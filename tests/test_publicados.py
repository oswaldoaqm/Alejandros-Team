"""Los eventos publicados: qué los identifica, en qué polos salen y cómo cambian la versión de datos."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from dreemgo.contrato import Evento, EventoNuevo
from dreemgo.motor import datos as artefactos
from dreemgo.publicados import (
    RADIO_KM,
    SIN_PUBLICADOS,
    Instantanea,
    Publicado,
    plegar,
    polos_cercanos,
)

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

AHORA = datetime(2026, 10, 2, 9, 30, 15, 123456, tzinfo=timezone(timedelta(hours=-5)))
FESTIVAL = {
    "nombre": "Festival del Café",
    "tipo": "Feria gastronómica",
    "fecha_inicio": date(2026, 11, 13),
    "fecha_fin": date(2026, 11, 15),
    "distrito": "Villa Rica",
    "provincia": "Oxapampa",
    "region": "Pasco",
    "lat": -10.7345,
    "lon": -75.2712,
    "descripcion": "Tres días de catas y visitas a fincas.",
    "url": "https://www.munivillarica.gob.pe/festival",
    "publicado_por": "Municipalidad Distrital de Villa Rica",
}


def publicado(ahora: datetime = AHORA, **cambios) -> Publicado:
    return Publicado.nuevo(EventoNuevo(**{**FESTIVAL, **cambios}), ahora)


# Un país de juguete: dos polos que duermen en el mismo pueblo y uno lejos. Un grado de
# latitud son 111 km, así que 0,05° son unos 5,6 km y 0,2° unos 22 km.
PAIS = SimpleNamespace(
    polos={
        1: SimpleNamespace(id=1, base={"lat": -10.0, "lon": -75.0}, regiones=("Pasco",)),
        2: SimpleNamespace(id=2, base={"lat": -10.0, "lon": -75.0}, regiones=("Pasco", "Junín")),
        3: SimpleNamespace(id=3, base={"lat": -12.0, "lon": -77.0}, regiones=("Lima",)),
    },
    recursos={
        "a": {"lat": -10.01, "lon": -75.0, "polo": 1},
        "b": {"lat": -10.5, "lon": -75.0, "polo": 2},
        "c": {"lat": -12.0, "lon": -77.01, "polo": 3},
        "sin-polo": {"lat": -11.0, "lon": -76.0, "polo": None},
    },
)


class TestIdentidad:
    def test_el_mismo_evento_da_el_mismo_id(self):
        assert publicado().id == publicado().id
        assert publicado().id.startswith("p-") and len(publicado().id) == 14

    def test_ni_las_mayusculas_ni_las_tildes_ni_los_espacios_lo_vuelven_otro(self):
        otro = publicado(
            nombre="  FESTIVAL   del cafe ", provincia="oxapampa", publicado_por="municipalidad distrital de villa rica"
        )
        assert otro.id == publicado().id
        assert otro.nombre == "FESTIVAL del cafe"

    def test_corregir_la_ubicacion_el_enlace_o_el_tipo_no_lo_vuelve_otro(self):
        assert publicado(lat=-10.74, lon=-75.27, url=None, tipo=None, descripcion=None).id == publicado().id

    @pytest.mark.parametrize(
        "cambio",
        [
            {"nombre": "Festival del Cacao"},
            {"fecha_inicio": date(2026, 11, 14)},
            {"fecha_fin": date(2026, 11, 16)},
            {"distrito": "Oxapampa"},
            {"provincia": "Chanchamayo"},
            {"region": "Junín"},
            {"publicado_por": "Cámara de Turismo de Villa Rica"},
        ],
    )
    def test_otro_nombre_otras_fechas_otro_lugar_u_otra_entidad_es_otro_evento(self, cambio):
        assert publicado(**cambio).id != publicado().id

    def test_la_hora_de_publicacion_se_guarda_sin_fracciones(self):
        assert publicado().publicado == "2026-10-02T09:30:15-05:00"

    def test_plegar(self):
        assert plegar("  Áncash ") == plegar("ANCASH") == "ancash"
        assert plegar("Madre De  Dios") == plegar("madre de dios")
        assert plegar("Cañete") == "canete"


class TestRegistro:
    def test_va_y_vuelve_igual(self):
        for p in (publicado(), publicado(lat=None, lon=None, tipo=None, descripcion=None, url=None)):
            assert Publicado.de_registro(p.registro()) == p

    def test_se_puede_guardar_como_json(self):
        registro = publicado().registro()
        assert json.loads(json.dumps(registro)) == registro
        assert registro["fecha_inicio"] == "2026-11-13"
        assert registro["url"] == "https://www.munivillarica.gob.pe/festival"

    def test_un_almacen_que_devuelve_enteros_no_cambia_el_evento(self):
        registro = {**publicado(lat=-10.0, lon=-75.0).registro(), "lat": -10, "lon": -75}
        assert Publicado.de_registro(registro) == publicado(lat=-10.0, lon=-75.0)

    @pytest.mark.parametrize(
        "roto",
        [
            {"nombre": None},
            {"id": ""},
            {"fecha_inicio": "mañana"},
            {"fecha_fin": None},
            {"lat": "norte"},
            {"region": 5},
        ],
    )
    def test_un_registro_roto_no_se_lee(self, roto):
        with pytest.raises((KeyError, TypeError, ValueError)):
            Publicado.de_registro({**publicado().registro(), **roto})

    def test_como_lo_ve_el_viajero(self):
        evento = publicado().evento()
        assert isinstance(evento, Evento)
        assert (evento.fuente, evento.precision_fecha) == ("publicado", "exacta")
        assert evento.publicado_por == "Municipalidad Distrital de Villa Rica"
        assert (evento.fecha_inicio, evento.fecha_fin) == (date(2026, 11, 13), date(2026, 11, 15))
        assert str(evento.url) == "https://www.munivillarica.gob.pe/festival"
        assert "descripcion" not in evento.model_dump()  # el contrato 1.2 todavía no la muestra


class TestPolos:
    def polos(self, lat: float | None, lon: float | None) -> frozenset[int]:
        return polos_cercanos([publicado(lat=lat, lon=lon)], PAIS)[0]

    def test_en_el_pueblo_donde_se_duerme_sale_en_todos_los_polos_que_duermen_ahi(self):
        assert self.polos(-10.0, -75.0) == {1, 2}
        assert self.polos(-10.05, -75.0) == {1, 2}

    def test_cerca_de_un_lugar_de_un_polo_sale_en_ese_polo(self):
        assert self.polos(-10.5, -75.0) == {2}
        assert self.polos(-12.0, -77.05) == {3}

    def test_lejos_de_todo_no_sale_en_ninguna_ruta(self):
        assert self.polos(-10.25, -75.0) == frozenset()  # a 27 km de la base y del lugar más cercano
        assert self.polos(-11.0, -76.0) == frozenset()  # junto a un recurso que no es de ningún polo

    def test_sin_coordenadas_no_sale_en_ninguna_ruta(self):
        assert self.polos(None, None) == frozenset()

    def test_el_radio_es_el_que_dice(self):
        justo_dentro = -10.0 - (RADIO_KM - 0.2) / 111.19
        justo_fuera = -10.0 - (RADIO_KM + 1.4) / 111.19  # el lugar «a» queda 1,1 km más cerca que la base
        assert self.polos(justo_dentro, -75.0) == {1, 2}
        assert self.polos(justo_fuera, -75.0) == frozenset()

    def test_sin_polos_no_falla(self):
        vacio = SimpleNamespace(polos={}, recursos={})
        assert polos_cercanos([publicado()], vacio) == [frozenset()]


class TestInstantanea:
    def test_sin_eventos_la_version_es_la_de_los_artefactos(self):
        assert Instantanea.de([], PAIS) == SIN_PUBLICADOS
        assert SIN_PUBLICADOS.version("2026.10.2") == "2026.10.2"
        assert SIN_PUBLICADOS.entre(date(2026, 1, 1), date(2027, 1, 1)) == []

    def test_con_eventos_la_version_lleva_su_huella(self):
        version = Instantanea.de([publicado()], PAIS).version("2026.10.2")
        assert version.startswith("2026.10.2-e") and len(version) == len("2026.10.2-e") + 7
        assert "+" not in version and " " not in version  # viaja en el enlace para compartir

    def test_la_huella_no_depende_del_orden_en_que_llegan(self):
        a, b = publicado(), publicado(nombre="Feria del Queso")
        assert Instantanea.de([a, b], PAIS) == Instantanea.de([b, a], PAIS)

    def test_la_huella_cambia_con_lo_que_cambia_una_respuesta(self):
        base = Instantanea.de([publicado()], PAIS).huella
        for cambio in ({"lat": -10.0, "lon": -75.0}, {"url": None}, {"tipo": "Feria"}):
            assert Instantanea.de([publicado(**cambio)], PAIS).huella != base
        assert Instantanea.de([publicado(), publicado(nombre="Feria del Queso")], PAIS).huella != base

    def test_la_huella_no_cambia_con_lo_que_no_se_muestra(self):
        base = Instantanea.de([publicado()], PAIS).huella
        mas_tarde = AHORA + timedelta(hours=3)
        assert Instantanea.de([publicado(mas_tarde)], PAIS).huella == base
        assert Instantanea.de([publicado(descripcion="Otra descripción.")], PAIS).huella == base

    def test_de_dos_con_el_mismo_id_vale_el_ultimo_publicado(self):
        primero = publicado(url=None)
        corregido = publicado(AHORA + timedelta(minutes=5))
        for orden in ([primero, corregido], [corregido, primero]):
            instantanea = Instantanea.de(orden, PAIS)
            assert instantanea.eventos == (corregido,)

    def test_entre_dos_fechas(self):
        instantanea = Instantanea.de([publicado()], PAIS)  # del 13 al 15 de noviembre
        dentro = [
            (date(2026, 11, 1), date(2026, 11, 30)),
            (date(2026, 11, 15), date(2026, 11, 20)),  # toca el último día
            (date(2026, 11, 10), date(2026, 11, 13)),  # toca el primero
            (date(2026, 11, 14), date(2026, 11, 14)),
        ]
        fuera = [(date(2026, 11, 16), date(2026, 11, 30)), (date(2026, 11, 1), date(2026, 11, 12))]
        for desde, hasta in dentro:
            assert [e.nombre for e in instantanea.entre(desde, hasta)] == ["Festival del Café"]
        for desde, hasta in fuera:
            assert instantanea.entre(desde, hasta) == []

    def test_de_un_polo_o_de_todos(self):
        en_la_base = publicado(nombre="Feria en el pueblo", lat=-10.0, lon=-75.0)
        en_lima = publicado(nombre="Feria en Lima", lat=-12.0, lon=-77.0)
        sin_lugar = publicado(nombre="Feria sin lugar", lat=None, lon=None)
        instantanea = Instantanea.de([en_la_base, en_lima, sin_lugar], PAIS)
        noviembre = (date(2026, 11, 1), date(2026, 11, 30))

        def nombres(polo=None):
            return [e.nombre for e in instantanea.entre(*noviembre, polo)]

        # En el calendario están todos, también el que no tiene lugar.
        assert sorted(nombres()) == ["Feria en Lima", "Feria en el pueblo", "Feria sin lugar"]
        assert nombres(1) == nombres(2) == ["Feria en el pueblo"]
        assert nombres(3) == ["Feria en Lima"]
        assert nombres(99) == []
        assert instantanea.polos_de(en_la_base.id) == {1, 2}
        assert instantanea.polos_de(sin_lugar.id) == frozenset()
        assert instantanea.polos_de("p-no-existe") == frozenset()

    def test_salen_en_el_orden_del_calendario(self):
        tarde = publicado(nombre="Segundo", fecha_inicio=date(2026, 11, 20), fecha_fin=date(2026, 11, 21))
        temprano = publicado(nombre="Primero", fecha_inicio=date(2026, 11, 2), fecha_fin=date(2026, 11, 2))
        instantanea = Instantanea.de([tarde, temprano], PAIS)
        assert [e.nombre for e in instantanea.entre(date(2026, 11, 1), date(2026, 11, 30))] == ["Primero", "Segundo"]


@con_datos
class TestConElInventario:
    def test_un_evento_en_huaraz_sale_en_los_polos_que_duermen_en_huaraz(self):
        datos = artefactos.cargar()
        duermen_en_huaraz = {p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz"}
        assert len(duermen_en_huaraz) > 1, "el caso que justifica mirar la base y no solo el lugar más cercano"
        plaza = next(p for p in datos.polos.values() if p.base["nombre"] == "Huaraz").base
        [polos] = polos_cercanos([publicado(lat=plaza["lat"], lon=plaza["lon"])], datos)
        assert duermen_en_huaraz <= polos

    def test_un_evento_en_medio_del_mar_no_sale_en_ninguna_ruta(self):
        assert polos_cercanos([publicado(lat=-12.0, lon=-80.5)], artefactos.cargar()) == [frozenset()]

"""Los eventos publicados: qué los identifica y cómo se guardan."""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone

import pytest

from dreemgo.contrato import Evento, EventoNuevo
from dreemgo.publicados import (
    Publicado,
    plegar,
)

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

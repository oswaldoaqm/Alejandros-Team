"""Lo publicado, a mano del API: cuándo se lee el almacén, qué pasa si falla y quién puede publicar."""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from types import SimpleNamespace

import pytest

from dreemgo.almacen import EnMemoria
from dreemgo.api import publicaciones as modulo
from dreemgo.api.publicaciones import (
    HORA_DEL_PERU,
    REINTENTO_S,
    VIGENCIA_S,
    CalendarioLleno,
    Publicaciones,
    ahora,
    clave_valida,
)
from dreemgo.contrato import EventoNuevo
from dreemgo.publicados import SIN_PUBLICADOS, Publicado

AHORA = datetime(2026, 10, 2, 10, 0, tzinfo=HORA_DEL_PERU)
HOY = AHORA.date()
PAIS = SimpleNamespace(
    polos={1: SimpleNamespace(id=1, base={"lat": -10.0, "lon": -75.0}, regiones=("Pasco",))},
    recursos={"a": {"lat": -10.01, "lon": -75.0, "polo": 1}},
)
OTRO_PAIS = SimpleNamespace(
    polos={7: SimpleNamespace(id=7, base={"lat": -10.0, "lon": -75.0}, regiones=("Pasco",))},
    recursos={},
)


def publicado(nombre: str = "Festival del Café", momento: datetime = AHORA, **cambios) -> Publicado:
    campos = {
        "nombre": nombre,
        "fecha_inicio": date(2026, 11, 13),
        "fecha_fin": date(2026, 11, 15),
        "distrito": "Villa Rica",
        "provincia": "Oxapampa",
        "region": "Pasco",
        "lat": -10.0,
        "lon": -75.0,
        "publicado_por": "Municipalidad Distrital de Villa Rica",
        **cambios,
    }
    return Publicado.nuevo(EventoNuevo(**campos), momento)


class Reloj:
    def __init__(self) -> None:
        self.segundos = 1_000_000.0

    def __call__(self) -> float:
        return self.segundos

    def pasan(self, segundos: float) -> None:
        self.segundos += segundos


class AlmacenDePrueba(EnMemoria):
    """En memoria, pero cuenta las lecturas y puede fallar cuando se le pide."""

    def __init__(self) -> None:
        super().__init__()
        self.lecturas = 0
        self.falla_al_leer = False
        self.falla_al_guardar = False

    def leer(self) -> list[dict]:
        self.lecturas += 1
        if self.falla_al_leer:
            raise OSError("la tabla no responde")
        return super().leer()

    def guardar(self, registro: dict) -> None:
        if self.falla_al_guardar:
            raise OSError("la tabla no responde")
        super().guardar(registro)


@pytest.fixture
def almacen() -> AlmacenDePrueba:
    return AlmacenDePrueba()


@pytest.fixture
def reloj() -> Reloj:
    return Reloj()


@pytest.fixture
def publicadas(almacen, reloj) -> Publicaciones:
    return Publicaciones(almacen, reloj=reloj)


def nombres(instantanea) -> list[str]:
    return sorted(p.nombre for p in instantanea.eventos)


class TestLeer:
    def test_sin_nada_publicado(self, publicadas):
        assert publicadas.instantanea(PAIS) == SIN_PUBLICADOS

    def test_lee_el_almacen_una_vez_y_lo_recuerda(self, publicadas, almacen, reloj):
        almacen.guardar(publicado().registro())
        primera = publicadas.instantanea(PAIS)
        reloj.pasan(VIGENCIA_S - 1)
        assert publicadas.instantanea(PAIS) is primera
        assert almacen.lecturas == 1
        assert nombres(primera) == ["Festival del Café"]

    def test_pasado_el_plazo_vuelve_a_leer(self, publicadas, almacen, reloj):
        publicadas.instantanea(PAIS)
        almacen.guardar(publicado().registro())  # lo publicó otro servidor
        reloj.pasan(VIGENCIA_S - 1)
        assert nombres(publicadas.instantanea(PAIS)) == []
        reloj.pasan(1)
        assert nombres(publicadas.instantanea(PAIS)) == ["Festival del Café"]
        assert almacen.lecturas == 2

    def test_si_el_reloj_retrocede_vuelve_a_leer(self, publicadas, almacen, reloj):
        publicadas.instantanea(PAIS)
        reloj.pasan(-3_600)
        publicadas.instantanea(PAIS)
        assert almacen.lecturas == 2

    def test_con_otros_artefactos_ubica_de_nuevo_sin_volver_a_leer(self, publicadas, almacen):
        almacen.guardar(publicado().registro())
        id_ = publicado().id
        assert publicadas.instantanea(PAIS).polos_de(id_) == {1}
        assert publicadas.instantanea(OTRO_PAIS).polos_de(id_) == {7}
        assert almacen.lecturas == 1


class TestSiElAlmacenFalla:
    def test_al_arrancar_se_sigue_sin_lo_publicado(self, publicadas, almacen, caplog):
        almacen.falla_al_leer = True
        with caplog.at_level(logging.ERROR, logger="dreemgo.publicaciones"):
            assert publicadas.instantanea(PAIS) == SIN_PUBLICADOS
        assert "No se pudieron leer los eventos publicados" in caplog.text

    def test_despues_se_sigue_con_lo_ultimo_que_se_leyo(self, publicadas, almacen, reloj):
        almacen.guardar(publicado().registro())
        buena = publicadas.instantanea(PAIS)
        almacen.falla_al_leer = True
        reloj.pasan(VIGENCIA_S)
        assert publicadas.instantanea(PAIS) == buena

    def test_reintenta_pronto_pero_no_en_cada_consulta(self, publicadas, almacen, reloj):
        almacen.guardar(publicado().registro())
        almacen.falla_al_leer = True
        publicadas.instantanea(PAIS)
        publicadas.instantanea(PAIS)
        assert almacen.lecturas == 1
        almacen.falla_al_leer = False
        reloj.pasan(REINTENTO_S)
        assert nombres(publicadas.instantanea(PAIS)) == ["Festival del Café"]
        assert almacen.lecturas == 2

    def test_un_registro_roto_no_tumba_a_los_demas(self, publicadas, almacen, caplog):
        almacen.guardar(publicado().registro())
        almacen.guardar({"id": "p-roto", "nombre": "Sin fechas"})
        almacen.guardar({"id": "p-peor"})
        with caplog.at_level(logging.WARNING, logger="dreemgo.publicaciones"):
            assert nombres(publicadas.instantanea(PAIS)) == ["Festival del Café"]
        assert caplog.text.count("Se salta un evento publicado") == 2


class TestGuardar:
    def test_queda_en_el_almacen_y_se_ve_enseguida_sin_volver_a_leer(self, publicadas, almacen):
        publicadas.instantanea(PAIS)
        instantanea = publicadas.guardar(publicado(), PAIS, HOY)
        assert nombres(instantanea) == ["Festival del Café"]
        assert publicadas.instantanea(PAIS) is instantanea
        assert [r["id"] for r in almacen.leer()] == [publicado().id]
        assert almacen.lecturas == 2  # la del arranque y la de esta misma prueba

    def test_no_pierde_lo_que_publico_otro_servidor(self, publicadas, almacen):
        almacen.guardar(publicado("Feria del Queso").registro())
        assert nombres(publicadas.guardar(publicado(), PAIS, HOY)) == ["Feria del Queso", "Festival del Café"]

    def test_publicar_el_mismo_otra_vez_lo_corrige(self, publicadas):
        publicadas.guardar(publicado(lat=None, lon=None), PAIS, HOY)
        corregido = publicado(momento=AHORA + timedelta(minutes=5))
        instantanea = publicadas.guardar(corregido, PAIS, HOY)
        assert instantanea.eventos == (corregido,)
        assert instantanea.polos_de(corregido.id) == {1}

    def test_si_no_se_pudo_guardar_falla_y_no_lo_muestra(self, publicadas, almacen):
        almacen.falla_al_guardar = True
        with pytest.raises(OSError):
            publicadas.guardar(publicado(), PAIS, HOY)
        assert publicadas.instantanea(PAIS) == SIN_PUBLICADOS

    def test_el_calendario_tiene_un_tope_de_eventos_por_venir(self, publicadas, monkeypatch):
        monkeypatch.setattr(modulo, "PUBLICADOS_MAX", 2)
        ayer = HOY - timedelta(days=1)
        publicadas.guardar(publicado("Ya pasó", fecha_inicio=ayer, fecha_fin=ayer), PAIS, HOY)
        publicadas.guardar(publicado("Uno"), PAIS, HOY)
        publicadas.guardar(publicado("Dos", fecha_inicio=HOY, fecha_fin=HOY), PAIS, HOY)  # el de hoy cuenta
        with pytest.raises(CalendarioLleno):
            publicadas.guardar(publicado("Tres"), PAIS, HOY)
        # Corregir uno que ya estaba siempre se puede.
        publicadas.guardar(publicado("Uno", url="https://www.munivillarica.gob.pe/"), PAIS, HOY)
        assert nombres(publicadas.instantanea(PAIS)) == ["Dos", "Uno", "Ya pasó"]


class TestClave:
    def test_sin_clave_configurada_nadie_publica(self, monkeypatch):
        monkeypatch.delenv("DREEMGO_CLAVE_PUBLICADOR", raising=False)
        assert not clave_valida("") and not clave_valida("cualquiera") and not clave_valida(None)
        monkeypatch.setenv("DREEMGO_CLAVE_PUBLICADOR", "")
        assert not clave_valida("")

    def test_solo_pasa_la_clave_exacta(self, monkeypatch):
        monkeypatch.setenv("DREEMGO_CLAVE_PUBLICADOR", "una-clave-larga")
        assert clave_valida("una-clave-larga")
        for otra in (None, "", "una-clave-larg", "una-clave-larga ", "UNA-CLAVE-LARGA", "ñandú"):
            assert not clave_valida(otra)


def test_la_hora_es_la_del_peru():
    assert ahora().utcoffset() == timedelta(hours=-5)

"""Los almacenes de eventos publicados guardan y devuelven lo mismo."""

from __future__ import annotations

import json
import logging

import pytest

from dreemgo.almacen import EnArchivo, EnMemoria


def registro(id_: str = "p-000000000001", **cambios) -> dict:
    return {
        "id": id_,
        "nombre": "Festival del Café",
        "tipo": None,
        "fecha_inicio": "2026-11-13",
        "fecha_fin": "2026-11-15",
        "distrito": "Villa Rica",
        "provincia": "Oxapampa",
        "region": "Pasco",
        "lat": -10.7345,
        "lon": -75.2712,
        "descripcion": None,
        "url": "https://www.munivillarica.gob.pe/festival",
        "publicado_por": "Municipalidad Distrital de Villa Rica",
        "publicado": "2026-10-02T09:30:15-05:00",
        **cambios,
    }


@pytest.fixture(params=["memoria", "archivo"])
def almacen(request, tmp_path):
    if request.param == "memoria":
        return EnMemoria()
    return EnArchivo(tmp_path / "datos" / "eventos.jsonl")


class TestCualquierAlmacen:
    def test_vacio(self, almacen):
        assert almacen.leer() == []

    def test_devuelve_lo_que_se_guardo(self, almacen):
        uno, otro = registro(), registro("p-000000000002", lat=None, lon=None, url=None, tipo="Feria")
        almacen.guardar(uno)
        almacen.guardar(otro)
        assert sorted(almacen.leer(), key=lambda r: r["id"]) == [uno, otro]

    def test_guardar_el_mismo_id_lo_reemplaza(self, almacen):
        almacen.guardar(registro())
        almacen.guardar(registro(lat=-10.74, nombre="Festival del Café de Altura"))
        [guardado] = almacen.leer()
        assert (guardado["lat"], guardado["nombre"]) == (-10.74, "Festival del Café de Altura")

    def test_lo_devuelto_no_es_lo_guardado(self, almacen):
        original = registro()
        almacen.guardar(original)
        original["nombre"] = "cambiado después de guardar"
        almacen.leer()[0]["nombre"] = "cambiado después de leer"
        assert almacen.leer()[0]["nombre"] == "Festival del Café"


class TestEnArchivo:
    def test_lo_guardado_sigue_ahi_al_reiniciar(self, tmp_path):
        ruta = tmp_path / "eventos.jsonl"
        EnArchivo(ruta).guardar(registro())
        assert EnArchivo(ruta).leer() == [registro()]

    def test_una_linea_por_evento_con_sus_tildes(self, tmp_path):
        ruta = tmp_path / "eventos.jsonl"
        EnArchivo(ruta).guardar(registro())
        [linea] = ruta.read_text(encoding="utf-8").splitlines()
        assert "Festival del Café" in linea and json.loads(linea) == registro()

    def test_una_linea_rota_no_tumba_a_las_demas(self, tmp_path, caplog):
        ruta = tmp_path / "eventos.jsonl"
        almacen = EnArchivo(ruta)
        almacen.guardar(registro())
        with ruta.open("a", encoding="utf-8") as fh:
            fh.write('{"id": "p-00000000000\n\n[1, 2]\n{"sin": "id"}\n')
        almacen.guardar(registro("p-000000000002"))
        with caplog.at_level(logging.WARNING, logger="dreemgo.almacen"):
            assert [r["id"] for r in almacen.leer()] == ["p-000000000001", "p-000000000002"]
        assert len(caplog.records) == 3

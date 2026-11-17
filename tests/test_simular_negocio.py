"""Coherencia del escenario comercial ficticio, sin modificar la telemetría."""

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

from evaluacion import simular_negocio


def test_embudo_y_alternativas_son_coherentes():
    datos = simular_negocio.generar()
    filas = datos["registros"]
    assert datos["meta"]["tipo"] == "simulacion_comercial"
    assert datos["meta"]["usuarios_ficticios"] == len(filas) == 300
    assert len({r["usuario_id"] for r in filas}) == 300
    assert len({r["sesion"] for r in filas}) == 300
    assert set(r["canal_simulado"] for r in filas) == set(simular_negocio.CANALES)
    assert all(r["visito"] for r in filas)

    for r in filas:
        assert not r["busco"] or r["interactuo"]
        assert not r["vio_propuestas"] or r["busco"]
        assert not r["abrio_propuesta"] or r["vio_propuestas"]
        assert not r["acepto_propuesta"] or r["abrio_propuesta"]
        assert not r["compra_simulada"] or r["acepto_propuesta"]
        assert r["propuestas_mostradas"] == (2 if r["vio_propuestas"] else 0)
        assert r["propuesta_abierta"] in ({"A", "B"} if r["abrio_propuesta"] else {None})
        assert r["propuesta_aceptada"] == (r["propuesta_abierta"] if r["acepto_propuesta"] else None)
        assert (r["polo_A"] is not None and r["polo_B"] is not None) == r["vio_propuestas"]
        assert r["importe_simulado"] == (20 if r["compra_simulada"] else 0)
        assert r["costo_variable_simulado"] == (5 if r["compra_simulada"] else 0)

    assert [
        sum(r[k] for r in filas)
        for k in (
            "visito",
            "interactuo",
            "busco",
            "vio_propuestas",
            "abrio_propuesta",
            "acepto_propuesta",
            "compra_simulada",
        )
    ] == [300, 283, 243, 213, 168, 95, 40]
    assert Counter(r["propuesta_aceptada"] for r in filas if r["acepto_propuesta"]) == {"A": 52, "B": 43}
    assert sum(r["importe_simulado"] for r in filas) == 800
    assert sum(r["costo_variable_simulado"] for r in filas) == 200
    assert sum(r["importe_simulado"] - r["costo_variable_simulado"] for r in filas) - 800 == -200


def test_regenerar_es_reproducible_y_conserva_archivos_previos(tmp_path: Path):
    antiguo = simular_negocio.RAIZ / "data/simulacion/actividad_300.json"
    antes = hashlib.sha256(antiguo.read_bytes()).hexdigest()
    primera = simular_negocio.generar()
    segunda = simular_negocio.generar()
    assert primera == segunda
    ruta, csv_ruta = simular_negocio.guardar(primera, tmp_path / "negocio_300.json")
    assert hashlib.sha256(antiguo.read_bytes()).hexdigest() == antes
    assert json.loads(ruta.read_text(encoding="utf-8")) == primera
    with csv_ruta.open(encoding="utf-8-sig", newline="") as archivo:
        csv_filas = list(csv.DictReader(archivo, delimiter=";"))
    assert len(csv_filas) == 300
    assert [r["usuario_id"] for r in csv_filas] == [r["usuario_id"] for r in primera["registros"]]
    assert [r["propuesta_aceptada"] for r in csv_filas] == [r["propuesta_aceptada"] or "" for r in primera["registros"]]
    assert sum(r["compra_simulada"] == "True" for r in csv_filas) == 40
    assert all("@" not in str(r) for r in csv_filas)

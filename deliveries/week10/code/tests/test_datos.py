"""Lo que tienen que cumplir los artefactos publicados en dreemgo/datos, además de cargar: que
un número de polo sea el mismo polo en todos los archivos y que ningún pueblo sea la base de dos."""

import pytest

from dreemgo.motor import datos as artefactos

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


def test_cada_recurso_y_cada_evento_es_de_un_polo_que_existe():
    datos = artefactos.cargar()
    assert {r["polo"] for r in datos.recursos.values()} <= set(datos.polos)
    assert {e["polo"] for e in datos.eventos.values()} <= set(datos.polos) | {-1}  # −1: sin polo


def test_lo_que_lista_cada_polo_es_suyo_y_no_falta_nada():
    datos = artefactos.cargar()
    recursos, paradas, eventos = {}, {}, {}
    for r in datos.recursos.values():
        recursos[r["polo"]] = recursos.get(r["polo"], 0) + 1
        if r["es_parada"]:
            paradas.setdefault(r["polo"], set()).add(r["codigo"])
    for e in datos.eventos.values():
        eventos.setdefault(e["polo"], set()).add(e["id"])
    for polo in datos.polos.values():
        assert polo.paradas and set(polo.paradas) == paradas[polo.id], polo.nombre
        assert set(polo.eventos) == eventos.get(polo.id, set()), polo.nombre
        assert polo.recursos == recursos[polo.id], polo.nombre
        n = len(polo.paradas)
        assert polo.entre_minutos.shape == (n, n) and polo.base_minutos.shape == (n,), polo.nombre
        assert len(polo.clima) == 12, polo.nombre


def test_cada_origen_tiene_el_camino_a_la_base_de_cada_polo():
    datos = artefactos.cargar()
    for origen in datos.origenes.values():
        assert set(origen.a_base) == set(datos.polos), origen.nombre


def test_ningun_pueblo_es_la_base_de_dos_polos():
    """Los grupos de TA-01 que duermen en el mismo pueblo son un solo polo (pipeline/tiempos.py)."""
    datos = artefactos.cargar()
    donde = [(p.base["nombre"], p.base["lat"], p.base["lon"]) for p in datos.polos.values()]
    assert len(set(donde)) == len(donde)
    # Huaraz eran cuatro polos, cada uno con uno de estos lugares.
    [huaraz] = [p for p in datos.polos.values() if p.base["nombre"] == "Huaraz"]
    de_cada_grupo = {
        "Parque Nacional Huascarán",
        "Quebrada Quilcayhuanca",
        "Quebrada Huantzan",
        "Museo Arqueológico de Áncash Augusto Soriano Infante",
    }
    assert de_cada_grupo <= {datos.recursos[c]["nombre"] for c in huaraz.paradas}

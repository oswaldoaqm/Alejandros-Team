"""La línea de base de la evaluación (decisión 0021): la guía cuenta solo lo que se pidió, propone zonas
que caben, con bases distintas, y el viaje a cada una es el que arma el motor."""

from types import SimpleNamespace

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from evaluacion import linea_base

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


def _recurso(jerarquia, intereses):
    return {"jerarquia": jerarquia, "intereses": intereses}


def test_la_fama_de_la_guia_cuenta_solo_los_lugares_de_lo_que_se_pidio():
    recursos = {"a": _recurso(4, ["historia"]), "b": _recurso(2, ["playa"]), "c": _recurso(1, ["playa", "naturaleza"])}
    datos = SimpleNamespace(recursos=recursos)
    polo = SimpleNamespace(paradas=["a", "b", "c"])
    assert linea_base.fama(polo, datos) == 24 + 2 + 1
    assert linea_base.fama(polo, datos, frozenset({"playa"})) == 2 + 1
    assert linea_base.fama(polo, datos, frozenset({"aventura"})) == 0


def test_la_vida_nocturna_no_cuenta_como_lugar_del_dia():
    consulta = Consulta(origen="lima", mes=10, dias=2, intereses=["gastronomia", "vida_nocturna"])
    assert linea_base.intereses_del_dia(consulta) == frozenset({"gastronomia"})


@con_datos
@pytest.mark.parametrize("con_intereses", [True, False])
def test_proponen_hasta_tres_zonas_que_caben_cada_una_con_su_base(con_intereses):
    datos = artefactos.cargar()
    consulta = Consulta(origen="lima", mes=5, dias=5, intereses=["playa"])
    zonas = linea_base.zonas(consulta, datos, con_intereses)
    assert 1 <= len(zonas) <= 3
    assert len({datos.polos[z].base["nombre"] for z in zonas}) == len(zonas)
    caben = {p.polo.id for p in linea_base.preparados(consulta, datos)}
    assert set(zonas) <= caben
    intereses = frozenset({"playa"}) if con_intereses else frozenset()
    famas = [linea_base.fama(datos.polos[z], datos, intereses) for z in zonas]
    assert famas == sorted(famas, reverse=True) and famas[-1] > 0


@con_datos
def test_el_viaje_a_una_zona_es_el_mismo_que_arma_el_motor():
    """Así una calificación vale para todos los sistemas que proponen esa zona."""
    datos = artefactos.cargar()
    consulta = Consulta(origen="lima", mes=7, dias=4, intereses=["historia"], presupuesto=900)
    for ruta in viaje.resolver(consulta, datos).rutas:
        otra = linea_base.viaje_a(ruta.polo.id, consulta, datos)
        assert otra.dias == ruta.dias and otra.costo == ruta.costo and otra.avisos == ruta.avisos


@con_datos
def test_una_zona_que_no_cabe_no_tiene_viaje():
    datos = artefactos.cargar()
    consulta = Consulta(origen="lima", mes=7, dias=2, altitud_max=2_000)
    huaraz = next(p.id for p in datos.polos.values() if p.base["nombre"] == "Huaraz")
    with pytest.raises(ValueError, match="no cabe"):
        linea_base.viaje_a(huaraz, consulta, datos)

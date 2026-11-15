"""Un lugar que se ve de noche (decisión 0030), como el Circuito Mágico del Agua, no es parada del día: va en la noche
del viaje. Se marca aquí sobre los artefactos, para que la prueba no dependa de la versión de los datos."""

import dataclasses
from datetime import date

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import noche, viaje

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
CIRCUITO = "4033"
DE_NOCHE = {"nombre": "Circuito Mágico del Agua", "funciones": ["19:15", "20:15", "21:30"]}


def _con_el_circuito_de_noche():
    datos = artefactos.cargar()
    recursos = dict(datos.recursos)
    recursos[CIRCUITO] = {**recursos[CIRCUITO], "de_noche": DE_NOCHE, "dias": ["mie", "jue", "vie", "sab", "dom"]}
    polo = next(p.id for p in datos.polos.values() if CIRCUITO in p.paradas)
    return dataclasses.replace(datos, recursos=recursos), polo


def test_los_dias_de_funcion_se_dicen_como_se_hablan():
    assert noche.dias_de_funcion(["mie", "jue", "vie", "sab", "dom"]) == "de miércoles a domingo"
    assert noche.dias_de_funcion(["lun", "jue"]) == "los lunes y jueves"
    assert noche.dias_de_funcion(list(noche.DIAS)) == "todos los días"


@con_datos
def test_sin_fecha_va_la_segunda_noche_y_no_es_parada_del_dia():
    datos, polo = _con_el_circuito_de_noche()
    [ruta] = viaje.resolver(Consulta(origen="cusco", mes=7, dias=4, destino=polo), datos).rutas
    assert CIRCUITO not in {p.recurso.codigo for d in ruta.dias for p in d.paradas}
    noches = {d.numero: d.noche for d in ruta.dias if d.noche is not None and d.noche.tipo == "espectaculo"}
    assert list(noches) == [2]
    assert noches[2].titulo == "Circuito Mágico del Agua de noche"
    assert noches[2].funciones == DE_NOCHE["funciones"]
    assert "de miércoles a domingo" in noches[2].nota


@con_datos
def test_con_fecha_va_la_primera_noche_con_funcion():
    datos, polo = _con_el_circuito_de_noche()
    # El 5 de julio de 2027 es lunes: la primera noche con función es la del miércoles 7, el día 3.
    consulta = Consulta(origen="cusco", mes=7, dias=4, destino=polo, fecha_inicio=date(2027, 7, 5))
    [ruta] = viaje.resolver(consulta, datos).rutas
    [dia] = [d for d in ruta.dias if d.noche is not None and d.noche.tipo == "espectaculo"]
    assert (dia.numero, dia.fecha) == (3, date(2027, 7, 7))
    assert "de miércoles a domingo" not in dia.noche.nota

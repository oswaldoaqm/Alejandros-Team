"""«Quiero ir a…» (contrato 1.4): con un destino, el motor arma solo el viaje a esa zona, el
mismo que arma cuando la elige él. Corre contra los artefactos de dreemgo/datos."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje

con_datos = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


def _zona(nombre: str) -> int:
    [polo] = [p.id for p in artefactos.cargar().polos.values() if p.nombre == nombre]
    return polo


@con_datos
def test_con_destino_sale_solo_el_viaje_a_esa_zona():
    cusco = _zona("Cuzco")
    respuesta = viaje.resolver(Consulta(origen="lima", mes=7, dias=6, destino=cusco), artefactos.cargar())
    assert [r.polo.id for r in respuesta.rutas] == [cusco]
    assert respuesta.consulta.destino == cusco and respuesta.sin_resultado is None


@con_datos
@pytest.mark.parametrize("origen, dias", [("lima", 4), ("cusco", 2), ("arequipa", 6), ("iquitos", 1)])
def test_es_el_mismo_viaje_que_arma_el_motor_cuando_elige_esa_zona(origen, dias):
    datos = artefactos.cargar()
    consulta = Consulta(origen=origen, mes=7, dias=dias, presupuesto=1500)
    rutas = viaje.resolver(consulta, datos).rutas
    assert rutas
    for ruta in rutas:
        [elegida] = viaje.resolver(consulta.model_copy(update={"destino": ruta.polo.id}), datos).rutas
        # Solo cambia el puntaje, que compara con las demás zonas.
        assert elegida.model_dump(exclude={"puntaje"}) == ruta.model_dump(exclude={"puntaje"})


@con_datos
def test_un_destino_que_no_existe():
    with pytest.raises(viaje.DestinoDesconocido):
        viaje.resolver(Consulta(origen="lima", mes=7, destino=9_999), artefactos.cargar())


@con_datos
def test_los_eventos_dicen_su_zona():
    datos = artefactos.cargar()
    rutas = viaje.resolver(Consulta(origen="lima", mes=6, dias=6), datos).rutas
    eventos = [(r.polo.id, e.polo) for r in rutas for e in r.eventos]
    assert eventos and all(zona == polo for polo, zona in eventos)

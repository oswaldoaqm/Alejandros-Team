"""Lo que cualquiera espera del motor: que proponga Machu Picchu y la Cordillera Blanca desde
donde y cuando se puede ir, y que no mande a nadie más días en el bus que de visita. Corre
contra los artefactos de dreemgo/datos: si un cambio en los datos o en el puntaje los saca de
las tres rutas, aquí se nota (decisiones 0013 a 0015)."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


def _duermen_en(**consulta) -> list[str]:
    return [r.polo.base.nombre for r in viaje.resolver(Consulta(**consulta), artefactos.cargar()).rutas]


def test_desde_el_cusco_un_fin_de_semana_de_temporada_seca_lleva_a_machu_picchu():
    assert "Machupicchu Pueblo" in _duermen_en(origen="cusco", mes=6, dias=2)


def test_desde_lima_seis_dias_de_julio_llevan_a_huaraz():
    assert "Huaraz" in _duermen_en(origen="lima", mes=7, dias=6)


def test_desde_lima_cuatro_dias_de_julio_tambien_llevan_a_huaraz():
    """Son 8 horas y 8 minutos de viaje: un día de ida, dos allá y un día de vuelta."""
    rutas = viaje.resolver(Consulta(origen="lima", mes=7, dias=4), artefactos.cargar()).rutas
    [huaraz] = [r for r in rutas if r.polo.base.nombre == "Huaraz"]
    assert [d.tipo for d in huaraz.dias] == ["ida", "visita", "visita", "vuelta"]
    assert huaraz.traslado.dias_de_viaje == 2 and 8.0 < huaraz.dias[0].horas <= 9.0


# El ejemplo de la guía del avance del 9 de octubre: desde Lima, cuatro días, para alguien a quien le
# gustan la naturaleza y las caminatas, con hasta S/ 1 000. Si deja de cumplirse, la guía miente.
NATURALEZA = {"origen": "lima", "dias": 4, "intereses": ["naturaleza", "caminatas"], "presupuesto": 1000}


def test_con_naturaleza_y_caminatas_julio_lleva_a_huaraz():
    assert "Huaraz" in _duermen_en(mes=7, **NATURALEZA)


def test_en_febrero_la_lluvia_de_la_sierra_saca_a_huaraz():
    rutas = viaje.resolver(Consulta(mes=2, **NATURALEZA), artefactos.cargar()).rutas
    assert rutas and "Huaraz" not in [r.polo.base.nombre for r in rutas]
    assert all(r.estacionalidad.veredicto != "desaconsejado" for r in rutas)


def test_ningun_viaje_pasa_mas_dias_en_el_camino_que_alla():
    """Sin vuelos, el Cusco desde Lima con nueve días eran seis en el bus y tres allá; y Tarapoto
    desde Iquitos, ocho días de río y uno allá."""
    for origen, mes, fuera in (("lima", 7, "Cuzco"), ("iquitos", 6, "Tarapoto")):
        rutas = viaje.resolver(Consulta(origen=origen, mes=mes, dias=9), artefactos.cargar()).rutas
        assert rutas and fuera not in [r.polo.base.nombre for r in rutas]
        for ruta in rutas:
            de_camino = sum(1 for d in ruta.dias if d.tipo in ("ida", "vuelta") and not d.paradas)
            assert de_camino <= len(ruta.dias) - de_camino, ruta.polo.nombre

"""Lo que cualquiera espera que el motor proponga: Machu Picchu y la Cordillera Blanca, desde
donde y cuando se puede ir. Corre contra los artefactos de dreemgo/datos: si un cambio en los
datos o en el puntaje los saca de las tres rutas, aquí se nota (decisión 0013)."""

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

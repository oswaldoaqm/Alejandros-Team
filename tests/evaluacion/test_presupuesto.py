"""Qué cambia si el presupuesto deja fuera lo que no cabe (semana 12): sin filtro da lo mismo que el motor, y
con filtro ningún viaje pasa el monto en ese percentil."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from evaluacion import presupuesto

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")

CONSULTAS = [
    Consulta(origen="lima", mes=7, dias=4, presupuesto=800),  # la de la revisión del profesor
    Consulta(origen="cusco", mes=5, dias=5, intereses=["historia"], presupuesto=1500),
    Consulta(origen="arequipa", mes=2, dias=3, intereses=["playa"], presupuesto=500),
]


@pytest.fixture(scope="module")
def datos():
    return artefactos.cargar()


@pytest.mark.parametrize("consulta", CONSULTAS)
def test_sin_filtro_elige_lo_mismo_que_el_motor(consulta, datos):
    hoy = presupuesto.elegir(consulta, datos, presupuesto.CRITERIOS["hoy"])
    assert [p.polo for p in hoy] == [r.polo.id for r in viaje.resolver(consulta, datos, sugerir=False).rutas]


@pytest.mark.parametrize("consulta", CONSULTAS)
def test_con_filtro_ningun_viaje_pasa_el_monto(consulta, datos):
    for percentil in ("p50", "p80"):
        elegidas = presupuesto.elegir(consulta, datos, presupuesto.CRITERIOS[f"filtro_{percentil}"])
        assert len(elegidas) <= 3 and len({p.polo for p in elegidas}) == len(elegidas)
        assert all(getattr(p, percentil) <= consulta.presupuesto for p in elegidas)

"""La variante de la evaluación (decisión 0021): la raíz de la calidad en el puntaje mientras dura el bloque, y
después el motor como estaba."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from evaluacion import variante


def test_la_variante_deja_el_motor_como_estaba_aunque_algo_falle():
    antes = viaje.CONCAVIDAD
    with pytest.raises(RuntimeError), variante.con_concavidad():
        assert viaje.CONCAVIDAD == variante.CONCAVIDAD == 0.5
        assert viaje._concava(0.25) == pytest.approx(0.5)
        raise RuntimeError
    assert viaje.CONCAVIDAD == antes == 1.0
    assert viaje._concava(0.25) == 0.25


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_la_variante_reparte_mas_los_viajes():
    """Lo que la motivó: el motor propone casi siempre las mismas zonas. En una rejilla chica, la variante
    propone más zonas distintas, y deja el motor como estaba."""
    datos = artefactos.cargar()
    consultas = [
        Consulta(origen=o, mes=m, dias=d)
        for o in ("lima", "arequipa", "cusco", "trujillo", "piura", "huancayo")
        for m in (2, 7)
        for d in (4, 6)
    ]
    motor = {r.polo.id for c in consultas for r in viaje.resolver(c, datos, sugerir=False).rutas}
    con_la_variante = {z for c in consultas for z in variante.zonas(c, datos)}
    assert len(con_la_variante) > len(motor)
    assert viaje.CONCAVIDAD == 1.0

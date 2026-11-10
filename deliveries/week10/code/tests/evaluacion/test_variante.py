"""La variante de la evaluación (decisión 0021): cambia el valor de lo no pedido mientras dura el bloque, y
después deja el motor como estaba."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from evaluacion import variante


def test_la_variante_deja_el_motor_como_estaba_aunque_algo_falle():
    antes = viaje.FACTOR_SIN_INTERES
    with pytest.raises(RuntimeError), variante.con_factor():
        assert viaje.FACTOR_SIN_INTERES == variante.FACTOR_SIN_INTERES
        raise RuntimeError
    assert viaje.FACTOR_SIN_INTERES == antes


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_para_un_fin_de_semana_de_playa_la_variante_no_propone_una_zona_sin_playas():
    """El caso que la motivó: desde Lima, un fin de semana de enero de playa (la consulta 15)."""
    datos = artefactos.cargar()
    consulta = Consulta(origen="lima", mes=1, dias=2, intereses=["playa"])

    def sin_playas(polo: int) -> bool:
        return not any("playa" in datos.recursos[c]["intereses"] for c in datos.polos[polo].paradas)

    assert any(sin_playas(r.polo.id) for r in viaje.resolver(consulta, datos).rutas)
    assert not any(sin_playas(z) for z in variante.zonas(consulta, datos))
    assert viaje.FACTOR_SIN_INTERES == 0.25

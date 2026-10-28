"""El presupuesto avisa y no esconde (decisión 0022): con el costo central dentro y el escenario caro fuera, el
viaje sale con un aviso; con los dos dentro, sin ninguno; y si el costo central lo pasa, con el de siempre."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


@pytest.fixture(scope="module")
def datos():
    return artefactos.cargar()


def _a_huaraz(datos, presupuesto):
    """Dos amigas de Lima, tres días de agosto para caminar (la consulta 2 de la evaluación): sale Huaraz."""
    consulta = Consulta(origen="lima", mes=8, dias=3, intereses=["naturaleza", "caminatas"], presupuesto=presupuesto)
    rutas = viaje.resolver(consulta, datos).rutas
    return next(r for r in rutas if r.polo.nombre == "Huaraz")


def test_con_el_costo_central_dentro_y_el_caro_fuera_avisa(datos):
    sin_tope = _a_huaraz(datos, None).costo
    presupuesto = (sin_tope.p50 + sin_tope.p80) // 2
    ruta = _a_huaraz(datos, presupuesto)
    assert ruta.costo.p50 <= presupuesto < ruta.costo.p80 and not ruta.costo.exceso
    (aviso,) = [a for a in ruta.avisos if a.tipo == "presupuesto"]
    assert aviso.nivel == "info"
    assert viaje.textos.soles(ruta.costo.p80) in aviso.mensaje
    assert viaje.textos.soles(ruta.costo.p80 - presupuesto) in aviso.mensaje


def test_con_los_dos_dentro_no_avisa_y_si_el_central_lo_pasa_avisa_como_siempre(datos):
    sin_tope = _a_huaraz(datos, None).costo
    holgado = _a_huaraz(datos, sin_tope.p80)
    assert not [a for a in holgado.avisos if a.tipo == "presupuesto"]
    corto = _a_huaraz(datos, sin_tope.p50 - 10)
    assert [a.nivel for a in corto.avisos if a.tipo == "presupuesto"] == ["advertencia"]

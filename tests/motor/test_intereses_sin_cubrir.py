"""El viajero debe saber cuándo una preferencia no tiene paradas en el plan propuesto."""

import pytest

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje

pytestmark = pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")


@pytest.fixture(scope="module")
def datos():
    return artefactos.cargar()


def _avisos_de_intereses(ruta):
    return [a for a in ruta.avisos if a.mensaje.startswith("Este itinerario no incluye paradas registradas")]


def test_huaraz_explica_que_no_cubre_playa_sin_eliminar_el_viaje(datos):
    consulta = Consulta(origen="lima", destino=14, mes=8, dias=3, intereses=["naturaleza", "playa"])
    respuesta = viaje.resolver(consulta, datos)
    assert len(respuesta.rutas) == 1
    ruta = respuesta.rutas[0]
    assert ruta.polo.nombre == "Huaraz"
    (aviso,) = _avisos_de_intereses(ruta)
    assert "playa" in aviso.mensaje
    assert "naturaleza" not in aviso.mensaje
    assert aviso.tipo == "datos" and aviso.nivel == "info"


def test_una_busqueda_de_playa_prioriza_viajes_con_paradas_de_playa(datos):
    consulta = Consulta(origen="lima", mes=7, dias=4, intereses=["playa"])
    respuesta = viaje.resolver(consulta, datos)

    assert respuesta.rutas
    assert all(
        any(
            "playa" in datos.recursos[parada.recurso.codigo]["intereses"] for dia in ruta.dias for parada in dia.paradas
        )
        for ruta in respuesta.rutas
    )


@pytest.mark.parametrize("intereses", [[], ["naturaleza"], ["vida_nocturna"]])
def test_no_avisa_por_intereses_cubiertos_ausentes_o_gestionados_por_la_noche(datos, intereses):
    consulta = Consulta(origen="lima", destino=14, mes=8, dias=3, intereses=intereses)
    ruta = viaje.resolver(consulta, datos).rutas[0]
    assert not _avisos_de_intereses(ruta)


def test_lo_que_no_cubre_lo_pedido_va_detras_sin_quitarlo(datos):
    """Desde Chachapoyas, con playa, en julio: Chiclayo tiene playa y va primero; las otras dos siguen, detrás y
    con su aviso (decisión 0034)."""
    consulta = Consulta(origen="chachapoyas", mes=7, dias=3, intereses=["playa"])
    rutas = viaje.resolver(consulta, datos).rutas
    assert len(rutas) == 3
    cubre = [not _avisos_de_intereses(r) for r in rutas]
    assert cubre[0] and cubre == sorted(cubre, reverse=True)
    assert not all(cubre)

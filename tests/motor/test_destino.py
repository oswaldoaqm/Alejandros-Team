"""«Quiero ir a…» (contrato 1.4): con un destino, el motor arma solo el viaje a esa zona, el
mismo que arma cuando la elige él; y si no cabe, dice por qué y qué cambiar. Corre contra los
artefactos de dreemgo/datos."""

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


SIN_VIAJE = [
    pytest.param(
        "lima",
        2,
        "Cuzco",
        {},
        "En 2 días no da para ir de Lima a Cuzco y volver: por carretera, solo la ida toma unas 22 horas, "
        "y en avión, ir y volver son unas 9 horas: demasiado para 2 días.",
        [("dias", 3, "sale el viaje, con vuelo")],
        id="pocos dias para volar",
    ),
    pytest.param(
        "lima",
        4,
        "Cuzco",
        {"solo_por_tierra": True},
        "En 4 días no da para ir de Lima a Cuzco y volver: por carretera, solo la ida toma unas 22 horas.",
        [("dias", 12, "sale el viaje, sin volar"), ("solo_por_tierra", False, "sale el viaje, con vuelo")],
        id="solo por tierra",
    ),
    pytest.param(
        "lima",
        9,
        "Cuzco",
        {"solo_por_tierra": True},
        "En 9 días se pasaría más tiempo en el camino que en Cuzco: por carretera, solo la ida toma unas 22 horas.",
        [("dias", 12, "sale el viaje, sin volar"), ("solo_por_tierra", False, "sale el viaje, con vuelo")],
        id="mas camino que visita",
    ),
    pytest.param(
        "iquitos",
        6,
        "Caballococha",
        {},
        "En 6 días no da para ir de Iquitos a Caballococha y volver: por carretera y en bote, solo la ida toma "
        "unas 21 horas.",
        [("dias", 12, "sale el viaje, sin volar")],
        id="por rio",
    ),
    pytest.param(
        "lima",
        3,
        "Lima",
        {},
        "Estás a menos de media hora de Lima: no hace falta dormir allá.",
        [("dias", 1, "sale el viaje, sin volar")],
        id="la misma ciudad",
    ),
    pytest.param(
        "lima",
        1,
        "Iquitos",
        {},
        "En un día no da para ir de Lima a Iquitos, visitar algo y volver.",
        [("dias", 4, "sale el viaje, con vuelo")],
        id="un dia",
    ),
    pytest.param(
        "lima",
        6,
        "Puno",
        {"altitud_max": 3000},
        "Puno está a 3 830 m, más arriba de tu límite de 3 000 m.",
        [("altitud_max", None, "sale el viaje, con vuelo")],
        id="la base muy alta",
    ),
    pytest.param(
        "lima",
        6,
        "Caraz",
        {"altitud_max": 2500},
        "En Caraz no encontramos lugares para visitar por debajo de 2 500 m.",
        [("altitud_max", None, "sale el viaje, sin volar")],
        id="los lugares muy altos",
    ),
    pytest.param(
        "arequipa",
        2,
        "Sangalle",
        {},
        "En 2 días, el camino a Sangalle deja muy poco tiempo allá: por carretera, solo la ida toma unas 6 horas.",
        [("dias", 3, "sale el viaje, sin volar")],
        id="poco tiempo alla",
    ),
    pytest.param(
        "lima",
        2,
        "Iquitos",
        {"solo_por_tierra": True},
        "En 2 días no da para ir de Lima a Iquitos y volver: por carretera y en bote, solo la ida toma unas 53 horas. "
        "Volando, cabe en 4 días.",
        [],
        id="volar y mas dias, juntos",
    ),
    pytest.param(
        "lima",
        4,
        "Machupicchu Pueblo",
        {"altitud_max": 1500},
        "Machupicchu Pueblo está a 2 047 m, más arriba de tu límite de 1 500 m. Sin el límite de altitud, "
        "cabe en 5 días.",
        [],
        id="sin limite y mas dias, juntos",
    ),
    pytest.param(
        "arequipa",
        9,
        "Queropalca",
        {},
        "En Queropalca no encontramos lugares que se puedan visitar en una jornada.",
        [],
        id="nada que quepa en una jornada",
    ),
]


@con_datos
@pytest.mark.parametrize("origen, dias, zona, extra, motivo, cambios", SIN_VIAJE)
def test_si_no_cabe_dice_por_que_y_que_cambiar(origen, dias, zona, extra, motivo, cambios):
    datos = artefactos.cargar()
    consulta = Consulta(origen=origen, mes=7, dias=dias, destino=_zona(zona), **extra)
    respuesta = viaje.resolver(consulta, datos)
    assert respuesta.rutas == []
    assert respuesta.sin_resultado.motivo == motivo
    # Y siempre, al final, buscar en todas las zonas, si eso da algo.
    sugerencias = [(s.campo, s.valor, s.efecto) for s in respuesta.sin_resultado.sugerencias]
    assert sugerencias == [*cambios, ("destino", None, "aparecen 3 viajes")]
    # Cada cambio, solo, hace salir el viaje: a esa zona, o los que dice en todas.
    for s in respuesta.sin_resultado.sugerencias:
        rutas = viaje.resolver(consulta.model_copy(update={s.campo: s.valor}), datos).rutas
        if s.campo == "destino":
            assert len(rutas) == 3
        else:
            assert [r.polo.id for r in rutas] == [consulta.destino]
            assert ("avion" in rutas[0].traslado.medios) == s.efecto.endswith("con vuelo")


@con_datos
def test_sin_sugerir_solo_dice_por_que():
    consulta = Consulta(origen="lima", mes=7, dias=2, destino=_zona("Cuzco"))
    sin = viaje.resolver(consulta, artefactos.cargar(), sugerir=False).sin_resultado
    assert sin.motivo.startswith("En 2 días no da para ir de Lima a Cuzco") and sin.sugerencias == []


@con_datos
def test_los_eventos_dicen_su_zona():
    datos = artefactos.cargar()
    rutas = viaje.resolver(Consulta(origen="lima", mes=6, dias=6), datos).rutas
    eventos = [(r.polo.id, e.polo) for r in rutas for e in r.eventos]
    assert eventos and all(zona == polo for polo, zona in eventos)

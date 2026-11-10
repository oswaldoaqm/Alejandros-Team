"""El almuerzo en el planificador, sobre polos de juguete (decisión 0019)."""

import numpy as np

from dreemgo.motor.planificador import ALMUERZO_MIN, Candidata, Jornada, Tiempos, horario

OCHO = 8 * 60


def _hora(h: int, m: int = 0) -> int:
    return h * 60 + m


def _linea(n: int, paso: float = 10.0) -> Tiempos:
    """n paradas en fila a ``paso`` minutos una de otra; el depósito, antes de la primera."""
    pos = np.arange(1, n + 1) * paso
    return Tiempos(pos, np.abs(pos[:, None] - pos[None, :]))


def _tiempos(desde: list[float], entre: list[list[float]]) -> Tiempos:
    return Tiempos(np.array(desde, dtype=float), np.array(entre, dtype=float))


def test_al_terminar_la_primera_visita_despues_de_las_doce_y_media_donde_hay_que_comer():
    # 8:10 a 12:10 la primera; 12:20 a 12:50 la segunda, que tiene dónde comer.
    a, b = Candidata(0, valor=1.0, visita=240), Candidata(1, valor=1.0, visita=30, comida=True)
    r = horario([a, b], Jornada(_hora(8), OCHO), _linea(2))
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en, r.almuerzo.dentro) == (2, _hora(12, 50), 1, True)
    # El almuerzo no cuenta: 10 + 240 + 10 + 30 + 20 de vuelta.
    assert r.minutos == 310 and r.vuelta == _hora(8) + 310 + ALMUERZO_MIN


def test_si_aqui_no_hay_donde_comer_y_en_el_siguiente_si_alla_al_llegar():
    # La primera termina a las 12:40, sin dónde comer; a la segunda se llega a las 12:50.
    a, b = Candidata(0, valor=1.0, visita=270), Candidata(1, valor=1.0, visita=30, comida=True)
    r = horario([a, b], Jornada(_hora(8), OCHO), _linea(2))
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en) == (1, _hora(12, 50), 1)
    # La hora de la parada es la de después del almuerzo.
    assert r.visitas[1].llegada == _hora(13, 50)


def test_si_al_siguiente_se_llega_tarde_se_almuerza_antes_desde_las_once_y_media():
    # La primera termina a las 11:50; la segunda queda a dos horas y media: se llegaría a las 14:20.
    t = _tiempos([10.0, 60.0], [[0.0, 150.0], [150.0, 0.0]])
    a, b = Candidata(0, valor=1.0, visita=220), Candidata(1, valor=1.0, visita=30, comida=True)
    r = horario([a, b], Jornada(_hora(8), OCHO), t)
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en) == (1, _hora(11, 50), 0)


def test_al_llegar_si_la_visita_terminaria_despues_de_las_dos():
    # A la segunda se llega a las 12:20 y su visita es de dos horas y media: se almuerza primero.
    a = Candidata(0, valor=1.0, visita=240)
    b = Candidata(1, valor=1.0, visita=150, cierra=_hora(16))
    r = horario([a, b], Jornada(_hora(8), OCHO), _linea(2))
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en) == (1, _hora(12, 20), 1)


def test_un_orden_que_deja_el_almuerzo_para_muy_tarde_no_va():
    # Si la segunda cierra a las 15:00, almorzar antes de ella no deja visitarla, y después serían
    # las 14:50: ese orden no va, y el planificador busca otro.
    a = Candidata(0, valor=1.0, visita=240)
    b = Candidata(1, valor=1.0, visita=150, cierra=_hora(15))
    assert horario([a, b], Jornada(_hora(8), OCHO), _linea(2)) is None
    assert horario([b, a], Jornada(_hora(8), OCHO), _linea(2)) is not None


def test_al_llegar_despues_de_las_dos():
    # De la primera (hasta las 9:10) a la segunda hay cinco horas: se llega a las 14:20.
    t = _tiempos([10.0, 60.0], [[0.0, 310.0], [310.0, 0.0]])
    a, b = Candidata(0, valor=1.0, visita=60), Candidata(1, valor=1.0, visita=30)
    r = horario([a, b], Jornada(_hora(8), OCHO), t)
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en) == (1, _hora(14, 20), 1)


def test_mientras_abre_el_lugar():
    # Se llega a las 11:50 a un lugar que abre a la 13:00: se almuerza mientras abre.
    a = Candidata(0, valor=1.0, visita=210)
    b = Candidata(1, valor=1.0, visita=30, abre=_hora(13))
    r = horario([a, b], Jornada(_hora(8), OCHO), _linea(2))
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en) == (1, _hora(11, 50), 1)
    assert (r.visitas[1].llegada, r.visitas[1].espera) == (_hora(12, 50), 10)


def test_antes_de_salir_si_la_jornada_empieza_despues_de_las_doce_y_media():
    a = Candidata(0, valor=1.0, visita=60)
    r = horario([a], Jornada(_hora(13), 240), _linea(1))
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en, r.almuerzo.dentro) == (0, _hora(13), None, False)
    assert r.salida == _hora(14) and r.minutos == 80


def test_al_volver_al_deposito_si_ahi_hay_donde_comer():
    # Termina a las 12:40, sin dónde comer, y se vuelve a la base a las 12:50.
    a = Candidata(0, valor=1.0, visita=270)
    r = horario([a], Jornada(_hora(8), OCHO), _linea(1))
    assert (r.almuerzo.despues_de, r.almuerzo.hora, r.almuerzo.en, r.almuerzo.dentro) == (1, _hora(12, 50), None, False)


def test_un_dia_que_termina_antes_de_las_doce_y_media_no_almuerza():
    a = Candidata(0, valor=1.0, visita=120)
    assert horario([a], Jornada(_hora(8), OCHO), _linea(1)).almuerzo is None

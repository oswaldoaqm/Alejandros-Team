"""El planificador sobre polos de juguete: valor, topes, horarios y orden."""

import numpy as np

from dreemgo.motor.planificador import (
    PARADAS_POR_DIA,
    Candidata,
    Jornada,
    Tiempos,
    horario,
    mejor_plan,
    planificar,
    valor_visitado,
)

OCHO = 8 * 60


def _linea(n: int, paso: float = 10.0) -> Tiempos:
    """n paradas en fila a ``paso`` minutos una de otra; el depósito, antes de la primera."""
    pos = np.arange(1, n + 1) * paso
    return Tiempos(pos, np.abs(pos[:, None] - pos[None, :]))


def test_cabe_lo_que_entra_en_la_jornada():
    t = _linea(3)
    c = [Candidata(i, valor=1.0, visita=60) for i in range(3)]
    (r,) = planificar(c, [Jornada(480, OCHO)], t)
    orden = [v.candidata.i for v in r.visitas]
    assert orden in ([0, 1, 2], [2, 1, 0])  # en fila, los dos sentidos cuestan lo mismo
    # 10 + 60 + 10 + 60 + 10 + 60 y 30 de vuelta (o al revés): 240 minutos.
    assert r.minutos == 240


def test_el_tope_deja_fuera_lo_que_no_cabe_y_prefiere_lo_que_vale_mas():
    # Cada una a 100 minutos de la base, en lados opuestos (200 entre ellas).
    t = Tiempos(np.array([100.0, 100.0]), np.array([[0.0, 200.0], [200.0, 0.0]]))
    barata, valiosa = Candidata(0, valor=1.0, visita=60), Candidata(1, valor=8.0, visita=60)
    (r,) = planificar([barata, valiosa], [Jornada(480, 300)], t)
    # Sola, cada una toma 260 minutos; las dos, 520: entra la que vale más.
    assert [v.candidata.i for v in r.visitas] == [1]


def test_respeta_el_horario_de_cada_lugar():
    t = _linea(2)
    temprano = Candidata(0, valor=1.0, visita=60, abre=0, cierra=10 * 60)
    tarde = Candidata(1, valor=1.0, visita=60, abre=14 * 60, cierra=18 * 60)
    (r,) = planificar([temprano, tarde], [Jornada(8 * 60, OCHO)], t)
    llegadas = {v.candidata.i: v for v in r.visitas}
    assert llegadas[0].llegada + 60 <= 10 * 60
    assert llegadas[1].llegada + llegadas[1].espera >= 14 * 60
    assert r.minutos <= OCHO


def test_sale_mas_tarde_si_el_primer_lugar_aun_no_abre():
    t = _linea(1)
    museo = Candidata(0, valor=1.0, visita=60, abre=10 * 60, cierra=17 * 60)
    r = horario([museo], Jornada(8 * 60, OCHO), t)
    assert r.salida == 10 * 60 - 10 and r.visitas[0].espera == 0


def test_dias_de_atencion():
    t = _linea(1)
    solo_domingo = Candidata(0, valor=1.0, visita=60, dias=frozenset({6}))
    assert horario([solo_domingo], Jornada(480, OCHO, dia_semana=0), t) is None
    assert horario([solo_domingo], Jornada(480, OCHO, dia_semana=6), t) is not None
    assert horario([solo_domingo], Jornada(480, OCHO, dia_semana=None), t) is not None  # sin fecha no se sabe


def test_sin_carretera_no_se_programa():
    t = Tiempos(np.array([10.0, np.nan]), np.array([[0.0, np.nan], [np.nan, 0.0]]))
    c = [Candidata(0, valor=1.0, visita=30), Candidata(1, valor=8.0, visita=30)]
    (r,) = planificar(c, [Jornada(480, OCHO)], t)
    assert [v.candidata.i for v in r.visitas] == [0]


def test_reparte_entre_jornadas_y_no_pasa_de_seis_por_dia():
    t = _linea(14, paso=2.0)
    c = [Candidata(i, valor=1.0, visita=30) for i in range(14)]
    rutas = planificar(c, [Jornada(480, OCHO), Jornada(480, OCHO)], t)
    assert all(len(r.visitas) <= PARADAS_POR_DIA for r in rutas)
    assert sum(len(r.visitas) for r in rutas) == 2 * PARADAS_POR_DIA


def test_un_subtipo_repetido_vale_menos():
    t = _linea(3)
    iglesias = [Candidata(i, valor=2.0, visita=30, subtipo="Iglesias") for i in range(3)]
    rutas = planificar(iglesias, [Jornada(480, OCHO)], t)
    assert valor_visitado(rutas) == 2.0 + 2.0 * 0.8 + 2.0 * 0.8**2


def test_determinista_y_el_mejor_arranque_no_empeora():
    rng = np.random.default_rng(3)
    xy = rng.uniform(0, 60, (25, 2))
    entre = np.hypot(*(xy[:, None, :] - xy[None, :, :]).transpose(2, 0, 1))
    t = Tiempos(np.hypot(*(xy - 30).T), entre)
    c = [Candidata(i, valor=float(2 ** rng.integers(0, 4)), visita=int(rng.integers(20, 120))) for i in range(25)]
    jornadas = [Jornada(480, OCHO), Jornada(480, OCHO)]
    uno = mejor_plan(c, jornadas, t)
    otro = mejor_plan(c, jornadas, t)
    assert [[v.candidata.i for v in r.visitas] for r in uno] == [[v.candidata.i for v in r.visitas] for r in otro]
    assert valor_visitado(uno) >= valor_visitado(planificar(c, jornadas, t))
    assert all(r.minutos <= OCHO for r in uno)

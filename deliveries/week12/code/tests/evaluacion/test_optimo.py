"""La búsqueda exacta del planificador (semana 12): da lo mismo que probar cada reparto en instancias de
juguete, nunca menos que la heurística, y lo que devuelve cabe con las reglas de ``horario``."""

import itertools
import math
import random

import numpy as np
import pytest

from dreemgo.motor import datos as artefactos
from dreemgo.motor.planificador import PARADAS_POR_DIA, Candidata, Jornada, Tiempos, admite, horario, mejor_plan
from evaluacion import optimo

OCHO = 8 * 60


def _en_fila(posiciones: list[float]) -> Tiempos:
    """Paradas sobre una recta, a esos minutos del depósito."""
    pos = np.array(posiciones, dtype=float)
    return Tiempos(np.abs(pos), np.abs(pos[:, None] - pos[None, :]))


def _plano(n: int, semilla: int, lado: float = 70.0) -> Tiempos:
    """n paradas al azar en un cuadrado de ``lado`` minutos, con el depósito al medio: en línea recta, los
    tiempos cumplen la desigualdad triangular, como los de camino más corto."""
    rng = np.random.default_rng(semilla)
    pos = rng.uniform(0, lado, size=(n, 2))
    desde = np.linalg.norm(pos - lado / 2, axis=1)
    return Tiempos(desde, np.linalg.norm(pos[:, None, :] - pos[None, :, :], axis=2))


def _candidatas(n: int, semilla: int) -> list[Candidata]:
    rng = random.Random(semilla)
    salida = []
    for i in range(n):
        abre = rng.choice([0, 8 * 60, 9 * 60, 10 * 60, 11 * 60, 14 * 60])
        cierra = rng.choice([12 * 60, 13 * 60, 17 * 60, 24 * 60]) if abre < 11 * 60 else 18 * 60
        salida.append(
            Candidata(
                i,
                valor=rng.choice([1.0, 2.0, 6.0, 24.0]),
                visita=rng.choice([45, 60, 90, 120]),
                abre=abre,
                cierra=cierra,
                subtipo=rng.choice(["iglesia", "museo", "mirador", None]),
                dias=rng.choice([None, None, frozenset({0, 1, 2, 3, 4})]),
                comida=rng.random() < 0.5,
                altura=rng.choice([2800, 3300, 3900]),
                exigente=rng.random() < 0.3,
            )
        )
    return salida


JORNADAS = [
    Jornada(9 * 60, 4 * 60, dia_semana=5, altura_max=3400, tranquila=True),  # sábado, día tranquilo
    Jornada(8 * 60, OCHO, dia_semana=6),
]


def _fuerza_bruta(cands: list[Candidata], jornadas: list[Jornada], t: Tiempos) -> float:
    """Cada reparto de las paradas entre las jornadas, con cada orden: lo que tiene que dar el óptimo."""
    memo: dict[tuple[frozenset[int], int], bool] = {}

    def cabe(paradas: list[Candidata], d: int) -> bool:
        clave = (frozenset(c.i for c in paradas), d)
        if clave not in memo:
            j = jornadas[d]
            memo[clave] = not paradas or (
                len(paradas) <= PARADAS_POR_DIA
                and all(admite(j, c) for c in paradas)
                and any(horario(list(orden), j, t) is not None for orden in itertools.permutations(paradas))
            )
        return memo[clave]

    mejor = 0.0
    for reparto in itertools.product(range(len(jornadas) + 1), repeat=len(cands)):
        dias = [[c for c, d in zip(cands, reparto, strict=True) if d == k] for k in range(len(jornadas))]
        if all(cabe(s, k) for k, s in enumerate(dias)):
            mejor = max(mejor, optimo.valor_del_conjunto([c for s in dias for c in s]))
    return mejor


def test_el_valor_de_un_conjunto_rebaja_el_subtipo_repetido_de_mayor_a_menor():
    iglesias = [
        Candidata(0, valor=2.0, visita=30, subtipo="iglesia"),
        Candidata(1, valor=6.0, visita=30, subtipo="iglesia"),
    ]
    assert optimo.valor_del_conjunto(iglesias) == pytest.approx(6 + 0.8 * 2)
    assert optimo.valor_del_conjunto(iglesias[::-1]) == pytest.approx(6 + 0.8 * 2)
    assert optimo.valor_del_conjunto([Candidata(2, valor=1.0, visita=30), *iglesias]) == pytest.approx(8.6)


def test_la_desigualdad_triangular():
    assert optimo.desigualdad_triangular(_candidatas(6, 1), _plano(6, 1)) < 1e-9
    entre = np.array([[0, 100, 5], [100, 0, 5], [5, 5, 0]], dtype=float)
    con_atajo = Tiempos(np.array([10.0, 10.0, 10.0]), entre)
    assert optimo.desigualdad_triangular([Candidata(i, 1.0, 30) for i in range(3)], con_atajo) == pytest.approx(90)
    entre[0, 1] = entre[1, 0] = np.inf
    sin_tramo = Tiempos(np.array([10.0, 10.0, 10.0]), entre)
    assert optimo.desigualdad_triangular([Candidata(i, 1.0, 30) for i in range(3)], sin_tramo) == math.inf


@pytest.mark.parametrize("semilla", range(5))
def test_da_lo_mismo_que_probar_cada_reparto(semilla):
    cands, t = _candidatas(6, semilla), _plano(6, semilla)
    opt = optimo.exacto(cands, JORNADAS, t)
    assert opt is not None and opt.valor == pytest.approx(_fuerza_bruta(cands, JORNADAS, t))


@pytest.mark.parametrize("semilla", range(5, 10))
def test_lo_que_devuelve_cabe_y_no_vale_menos_que_la_heuristica(semilla):
    cands, t = _candidatas(9, semilla), _plano(9, semilla)
    plan = mejor_plan(cands, JORNADAS, t)
    heuristica = optimo.valor_del_conjunto([v.candidata for r in plan for v in r.visitas])
    opt = optimo.exacto(cands, JORNADAS, t, piso=heuristica)
    assert opt is not None and opt.valor >= heuristica - 1e-9
    usadas = [k for r in opt.recorridos for k in r]
    assert len(usadas) == len(set(usadas))
    for r, j in zip(opt.recorridos, JORNADAS, strict=True):
        assert len(r) <= PARADAS_POR_DIA and all(admite(j, cands[k]) for k in r)
        assert not r or horario([cands[k] for k in r], j, t) is not None
    assert optimo.valor_del_conjunto([cands[k] for k in usadas]) == pytest.approx(opt.valor)


def test_sumar_una_parada_puede_hacer_que_quepan_las_que_solas_no_caben():
    """A cierra a las 10:00 y B abre a las 11:00: de A a B se esperaría 1 h 40 en la puerta, y de B a A, A ya
    cerró. Con C entre las dos, la espera baja a 40 minutos y caben las tres."""
    a = Candidata(0, valor=1.0, visita=60, abre=8 * 60, cierra=10 * 60)
    b = Candidata(1, valor=1.0, visita=60, abre=11 * 60)
    c = Candidata(2, valor=1.0, visita=60)
    t, jornada = _en_fila([10, 20, 15]), Jornada(8 * 60, OCHO)
    caben = optimo.conjuntos_que_caben([a, b, c], jornada, t, holgura=optimo.REDONDEO_MIN)
    assert 0b011 not in caben and 0b111 in caben
    opt = optimo.exacto([a, b, c], [jornada], t)
    assert opt.valor == pytest.approx(3) and opt.recorridos == [caben[0b111]]


def test_si_pasa_el_plazo_no_responde():
    """Doce paradas a cinco minutos una de otra: caben millones de órdenes."""
    cands = [Candidata(i, valor=1.0, visita=30) for i in range(12)]
    t = Tiempos(np.full(12, 5.0), np.where(np.eye(12) > 0, 0.0, 5.0))
    assert optimo.exacto(cands, [Jornada(8 * 60, OCHO)], t, plazo=0.0) is None


def test_si_la_heuristica_visita_todas_no_hace_falta_buscar():
    cands = [Candidata(i, valor=1.0, visita=30) for i in range(3)]
    inst = optimo.Instancia(
        1, 7, "Zona", cands, [Jornada(8 * 60, OCHO)], _en_fila([10, 20, 30]), {0: "a", 1: "b", 2: "c"}
    )
    fila = optimo.medir(inst)
    assert fila["estado"] == "visita_todas" and fila["brecha"] == 0 and fila["valor_optimo"] == 3


@pytest.mark.skipif(not artefactos.hay_datos(), reason="sin los artefactos del motor")
def test_un_viaje_de_verdad():
    datos = artefactos.cargar()
    inst = next(optimo.instancias(datos, 10))
    assert len(inst.candidatas) == 10 and inst.jornadas
    fila = optimo.medir(inst)
    assert fila["estado"] in ("visita_todas", "heuristica_optima", "mejorable")
    assert fila["valor_optimo"] >= fila["valor_heuristica"]

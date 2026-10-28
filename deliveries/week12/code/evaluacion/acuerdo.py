"""
Cuánto coinciden quienes califican (semana 12, decisión 0021).

- **El kappa de Fleiss** (Fleiss, 1971): cuánto más coinciden que si calificaran al azar, con la misma
  proporción de 2, 1 y 0. Trata las notas como categorías. Pide que cada viaje tenga todas sus notas.
- **El alfa de Krippendorff** (Krippendorff, 2011, «Computing Krippendorff's alpha-reliability»), con la
  distancia ordinal: un 2 frente a un 0 es más desacuerdo que un 2 frente a un 1. Acepta notas que faltan.

Los dos dan 1 si todos coinciden siempre y 0 si coinciden lo que se esperaría por azar.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from itertools import permutations

Nota = int | None


def kappa_de_fleiss(notas: Sequence[Sequence[int]], categorias: Sequence[int] = (0, 1, 2)) -> float:
    """Una fila por viaje con la nota de cada quien, todas con el mismo número de notas."""
    if not notas:
        raise ValueError("no hay viajes calificados")
    n = len(notas[0])
    if n < 2 or any(len(f) != n for f in notas):
        raise ValueError("el kappa de Fleiss pide dos notas o más por viaje, y las mismas en todos")
    cuentas = [Counter(f) for f in notas]
    acuerdo = sum(sum(c[k] * (c[k] - 1) for k in categorias) / (n * (n - 1)) for c in cuentas) / len(notas)
    total = len(notas) * n
    azar = sum((sum(c[k] for c in cuentas) / total) ** 2 for k in categorias)
    return (acuerdo - azar) / (1 - azar) if azar < 1 else 1.0


def _ordinal(marginales: dict[int, int], valores: list[int]):
    """La distancia ordinal al cuadrado entre dos valores, con las marginales de la matriz de coincidencias."""
    posicion = {v: k for k, v in enumerate(valores)}

    def distancia(c: int, k: int) -> float:
        a, b = sorted((posicion[c], posicion[k]))
        entre = sum(marginales[valores[g]] for g in range(a, b + 1))
        return (entre - (marginales[c] + marginales[k]) / 2) ** 2

    return distancia


def alfa_de_krippendorff(notas: Sequence[Sequence[Nota]], nivel: str = "ordinal") -> float:
    """Una fila por viaje con la nota de cada quien; None si alguien no lo calificó. ``nivel``: «nominal» u
    «ordinal». Un viaje con menos de dos notas no cuenta."""
    unidades = [[v for v in f if v is not None] for f in notas]
    unidades = [u for u in unidades if len(u) >= 2]
    if not unidades:
        raise ValueError("no hay viajes con dos notas o más")
    coincidencias: Counter[tuple[int, int]] = Counter()
    for u in unidades:
        for c, k in permutations(range(len(u)), 2):
            coincidencias[(u[c], u[k])] += 1 / (len(u) - 1)
    valores = sorted({v for u in unidades for v in u})
    marginales = {c: sum(coincidencias[(c, k)] for k in valores) for c in valores}
    total = sum(marginales.values())
    if nivel == "nominal":

        def distancia(c: int, k: int) -> float:
            return 0.0 if c == k else 1.0

    elif nivel == "ordinal":
        distancia = _ordinal(marginales, valores)
    else:
        raise ValueError(f"nivel desconocido: {nivel}")
    observado = sum(coincidencias[(c, k)] * distancia(c, k) for c in valores for k in valores)
    esperado = sum(marginales[c] * marginales[k] * distancia(c, k) for c in valores for k in valores)
    return 1.0 if esperado == 0 else 1 - (total - 1) * observado / esperado

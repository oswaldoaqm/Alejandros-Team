"""
Cuánto acierta cada sistema con sus tres viajes (semana 12, decisión 0021).

La nota de un viaje es la media de las de quienes lo calificaron, de 0 a 2. Por consulta, con los tres
viajes de un sistema en su orden:

- **nDCG@3:** la ganancia de cada viaje es su nota y pesa menos cuanto más abajo va (1, 1/log2 3, 1/2);
  se divide por la del mejor orden posible entre todos los viajes calificados de esa consulta, de cualquier
  sistema. 1 es que propuso los mejores, en el mejor orden.
- **P@3:** la parte de sus tres viajes que se recomendarían tal cual: una nota de 1,5 o más.
- **MRR:** 1 sobre el puesto del primero que se recomendaría tal cual; 0 si ninguno.
- **No encajan:** la parte de sus tres viajes con una nota menor que 0,5.

Para comparar dos sistemas se toma la diferencia consulta por consulta: su media, con un intervalo de 95 %
por bootstrap sobre las consultas, y la prueba de Wilcoxon de rangos con signo.
"""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

K = 3
RECOMENDABLE = 1.5
NO_ENCAJA = 0.5


def dcg(ganancias: Sequence[float], k: int = K) -> float:
    return sum(g / math.log2(r + 2) for r, g in enumerate(ganancias[:k]))


def ndcg(propuestos: Sequence[float], todos: Sequence[float], k: int = K) -> float:
    """``propuestos``: las notas de los viajes del sistema, en su orden. ``todos``: las de todos los viajes
    calificados de la consulta. Si ninguno tiene nota mayor que 0, es 0."""
    ideal = dcg(sorted(todos, reverse=True), k)
    return dcg(propuestos, k) / ideal if ideal > 0 else 0.0


def precision(propuestos: Sequence[float], k: int = K) -> float:
    return sum(1 for g in propuestos[:k] if g >= RECOMENDABLE) / k


def rango_reciproco(propuestos: Sequence[float], k: int = K) -> float:
    return next((1 / r for r, g in enumerate(propuestos[:k], 1) if g >= RECOMENDABLE), 0.0)


def no_encajan(propuestos: Sequence[float], k: int = K) -> float:
    return sum(1 for g in propuestos[:k] if g < NO_ENCAJA) / k


def intervalo(diferencias: Sequence[float], veces: int = 10_000, semilla: int = 12) -> tuple[float, float]:
    """El intervalo de 95 % de la media, por bootstrap: se remuestrean las consultas con reemplazo."""
    azar = random.Random(semilla)
    n = len(diferencias)
    medias = sorted(sum(azar.choices(diferencias, k=n)) / n for _ in range(veces))
    return medias[int(0.025 * veces)], medias[int(0.975 * veces) - 1]


def comparar(a: Sequence[float], b: Sequence[float]) -> dict:
    """Las cifras de un sistema frente a otro, consulta por consulta: a menos b."""
    from scipy.stats import wilcoxon

    diferencias = [x - y for x, y in zip(a, b, strict=True)]
    distintas = [d for d in diferencias if d != 0]
    p = float(wilcoxon(distintas).pvalue) if len(distintas) >= 6 else None
    bajo, alto = intervalo(diferencias)
    return {
        "media": sum(diferencias) / len(diferencias),
        "ic95": [bajo, alto],
        "gana": sum(1 for d in diferencias if d > 0),
        "pierde": sum(1 for d in diferencias if d < 0),
        "empata": sum(1 for d in diferencias if d == 0),
        "wilcoxon_p": p,
    }

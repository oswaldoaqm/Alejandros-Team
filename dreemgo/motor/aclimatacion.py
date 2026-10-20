"""
Cuándo pesa la altura: la regla de la noche de descanso (decisión 0018), en un solo lugar, para que lo
que dependa de ella no la repita ni la contradiga.

**Pesa la altura** si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, sea en bus, en
bus de noche o en avión: es la altura, no el medio. Desde la costa a Huaraz, al Cusco o a Puno, sí;
desde el Cusco a Puno, no, porque quien vive a 3 400 m ya está acostumbrado. El Yellow Book del CDC
(edición 2026, «High-Altitude Travel and Altitude Illness», de Peter H. Hackett y David R. Shlim) pone
el riesgo en dormir a 2 450 m o más sin estar aclimatado.

La altura del origen es la de la base de la zona de su misma ciudad: la más cercana, si queda a
menos de media hora. Cada una de las 24 ciudades de origen tiene una.
"""

from __future__ import annotations

import math

from dreemgo.motor.datos import Datos, Origen

ALTURA_QUE_PESA_M = 2_500
SUBIDA_QUE_PESA_M = 1_000
CASA_MIN = 30  # como en viaje.py: una base más cerca que esto del origen es la misma ciudad


def del_origen(origen: Origen, datos: Datos) -> int | None:
    """La altura de la base de la zona de la misma ciudad del origen: la más cercana, si queda a
    menos de media hora; None si no hay ninguna."""
    cerca = sorted((m, p) for p, (m, _) in origen.a_base.items() if math.isfinite(m) and m < CASA_MIN)
    if not cerca:
        return None
    return datos.polos[cerca[0][1]].base["altitud_m"]


def pesa(altura_base: int | None, de_origen: int | None) -> bool:
    """Si pesa la altura: se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo. Sin alguna de
    las dos alturas no se sabe, y no pesa."""
    return (
        altura_base is not None
        and de_origen is not None
        and altura_base >= ALTURA_QUE_PESA_M
        and altura_base - de_origen >= SUBIDA_QUE_PESA_M
    )

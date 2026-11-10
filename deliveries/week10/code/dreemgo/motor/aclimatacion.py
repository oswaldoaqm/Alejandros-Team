"""
Cuándo pesa la altura y cómo es el primer día en ella, en una sola regla para la noche de descanso
(decisión 0018) y para el primer día tranquilo (decisión 0020): así nunca se contradicen.

**Pesa la altura** si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, sea en bus, en
bus de noche o en avión: es la altura, no el medio. Desde la costa a Huaraz, al Cusco o a Puno, sí;
desde el Cusco a Puno, no, porque quien vive a 3 400 m ya está acostumbrado. El Yellow Book del CDC
(edición 2026, «High-Altitude Travel and Altitude Illness», de Peter H. Hackett y David R. Shlim) pone
el riesgo en dormir a 2 450 m o más sin estar aclimatado.

La altura del origen es la de la base de la zona de su misma ciudad: la más cercana, si queda a
menos de media hora. Cada una de las 24 ciudades de origen tiene una.

**El primer día en la base**, si pesa la altura, es tranquilo, porque el CDC pide solo ejercicio
suave en las primeras 48 horas:

- medio día de visitas como mucho: 4 horas, más el almuerzo;
- ninguna parada a más de 500 m sobre la base: el primer día no es para subir de golpe a 4 400 m,
  como al Huascarán desde Huaraz. Es la medida que el CDC usa para subir de una noche a la otra sobre
  los 3 000 m; para el día es un supuesto del producto;
- nada exigente: ni una caminata de acceso de más de 30 minutos ni una visita de más de 2 horas,
  como un parque nacional;
- y después de un bus de noche, desde las 9:00.

Es el primer día con jornada en la base: el de llegada, si queda tiempo para visitar, o el siguiente.
"""

from __future__ import annotations

import math

from dreemgo.motor.datos import Datos, Origen

ALTURA_QUE_PESA_M = 2_500
SUBIDA_QUE_PESA_M = 1_000
CASA_MIN = 30  # como en viaje.py: una base más cerca que esto del origen es la misma ciudad
TRANQUILO_MIN = 4 * 60
SUBIDA_TRANQUILA_M = 500
CAMINATA_EXIGENTE_MIN = 30
VISITA_EXIGENTE_MIN = 2 * 60
INICIO_TRAS_BUS_DE_NOCHE = 9 * 60


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


def exigente(recurso: dict) -> bool:
    """Si un lugar cansa: una caminata de acceso de más de 30 minutos, de ida, o una visita de más de 2 horas."""
    return (recurso["caminata_min"] or 0) > CAMINATA_EXIGENTE_MIN or (recurso["visita_min"] or 0) > VISITA_EXIGENTE_MIN


def altura_max_del_primer_dia(altura_base: int | None, de_origen: int | None) -> int | None:
    """Lo más alto que sube el primer día en la base: la base más 500 m, si pesa la altura; si no pesa, None."""
    return altura_base + SUBIDA_TRANQUILA_M if pesa(altura_base, de_origen) else None

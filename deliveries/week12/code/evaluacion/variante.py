"""
Una variante del motor para la evaluación (semana 12, decisión 0021): lo que se pidió pesa más.

Hoy, si la consulta trae intereses, un lugar que no atiende ninguno vale la cuarta parte (CONTRATO.md,
«Cómo decide el motor»). Con la escala 1, 2, 6 y 24, un lugar de jerarquía 4 que no es de lo que se pidió
vale 6, lo mismo que uno de jerarquía 3 que sí lo es, y el triple que una playa de jerarquía 2. Por eso,
para un fin de semana de playa desde Lima, el motor propone Nasca, que no tiene playas. La variante lo
baja a la décima parte: así vale 2,4, casi lo mismo que un lugar de jerarquía 2 que sí es de lo pedido.

No está desplegada: entra al kit para que las calificaciones digan si conviene el cambio. Aquí solo
cambia qué zonas se proponen y en qué orden; el viaje a cada zona es el del motor desplegado, igual para
todas las opciones (``linea_base.viaje_a``). Lo que la variante cambiaría dentro de cada viaje se mide
aparte, sin calificaciones.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from dreemgo.contrato import Consulta
from dreemgo.motor import viaje
from dreemgo.motor.datos import Datos

FACTOR_SIN_INTERES = 0.1


@contextmanager
def con_factor(factor: float = FACTOR_SIN_INTERES) -> Iterator[None]:
    """El motor con otro valor para lo que no es de lo que se pidió, mientras dure el bloque."""
    antes = viaje.FACTOR_SIN_INTERES
    viaje.FACTOR_SIN_INTERES = factor
    try:
        yield
    finally:
        viaje.FACTOR_SIN_INTERES = antes


def zonas(consulta: Consulta, datos: Datos) -> list[int]:
    """Las zonas que propondría el motor con la variante, en su orden."""
    with con_factor():
        return [r.polo.id for r in viaje.resolver(consulta, datos, sugerir=False).rutas]

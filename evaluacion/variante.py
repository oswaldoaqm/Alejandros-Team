"""
Una variante del motor para la evaluación (decisión 0021): menos de lo mismo.

El puntaje de cada zona suma su calidad, el valor que alcanza a visitarse frente a la mejor zona de la consulta, y
su novedad, con pesos 0,7 y 0,3. Con la escala 1, 2, 6 y 24, la calidad separa mucho a las zonas grandes de las
demás, y la novedad casi nunca alcanza: en la rejilla de 1 152 consultas de la semana 10, los diez polos más
propuestos se llevaban el 80 % de los viajes. La variante usa la raíz cuadrada de la calidad: una zona con la mitad
del valor de la mejor pasa de 0,5 a 0,71, y la novedad pesa más en el desempate.

No está desplegada: entra al kit para que las calificaciones digan si conviene el cambio. Aquí solo cambia qué
zonas se proponen y en qué orden; el viaje a cada zona es el del motor desplegado, igual para todas las opciones
(``linea_base.viaje_a``).

Hasta el 5 de noviembre la variante era otra: la décima parte, en vez de la cuarta, para lo que no es de lo pedido.
Coincidía con el motor en 110 de sus 120 propuestas, así que las calificaciones no iban a decir casi nada de ella.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

from dreemgo.contrato import Consulta
from dreemgo.motor import viaje
from dreemgo.motor.datos import Datos

CONCAVIDAD = 0.5


@contextmanager
def con_concavidad(concavidad: float = CONCAVIDAD) -> Iterator[None]:
    """El motor con la calidad elevada a ``concavidad`` en el puntaje, mientras dure el bloque."""
    antes = viaje.CONCAVIDAD
    viaje.CONCAVIDAD = concavidad
    try:
        yield
    finally:
        viaje.CONCAVIDAD = antes


def zonas(consulta: Consulta, datos: Datos) -> list[int]:
    """Las zonas que propondría el motor con la variante, en su orden."""
    with con_concavidad():
        return [r.polo.id for r in viaje.resolver(consulta, datos, sugerir=False).rutas]

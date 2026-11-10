"""
Las líneas de base de la evaluación (semana 12, decisión 0021): lo que propondría una guía de viajes.

Entre las zonas que caben en el viaje, con las mismas reglas del motor (los días, la ida y la vuelta, el
bus de noche, los vuelos, la altitud máxima, «Sorpréndeme» y el primer día en la altura), las tres más
conocidas, cada una con su propia base. Lo conocida que es una zona es la suma del valor de sus lugares
por su jerarquía, con la escala del motor (1, 2, 6 o 24 por lugar). Sin mirar el mes, el presupuesto, lo
que se alcanza a ver en los días que hay ni lo poco visitado de la zona:

- **La guía** cuenta solo los lugares de lo que la persona pidió: para quien quiere playa, las zonas con
  las playas más conocidas. Sin intereses, cuenta todos. Es la línea de base de la evaluación.
- **Lo más conocido** (``con_intereses=False``) cuenta todos, pida lo que pida: la recomendación sin
  personalizar. Se descartó como línea de base, porque para quien pide playa propone el Cusco, Puno y
  Huaraz, y ganarle no dice nada; queda para comparar sin calificaciones, como la cobertura.

El viaje a cada zona es el que arma el motor para esa consulta (``viaje``), así que lo único que cambia
entre el motor y una línea de base es qué zonas se proponen. Es lo que pedía la semana 6
(``deliveries/week06/ModelSelection.md``, §8.5): si el motor no le gana a una guía, su puntaje no aporta.
"""

from __future__ import annotations

from dreemgo.contrato import DE_NOCHE, RUTAS_MAX, Consulta, Ruta
from dreemgo.motor import aclimatacion, viaje
from dreemgo.motor.datos import Datos
from dreemgo.motor.datos import Polo as PoloDatos


def fama(polo: PoloDatos, datos: Datos, intereses: frozenset[str] = frozenset()) -> float:
    """Lo conocida que es una zona: la suma del valor de sus lugares por su jerarquía. Con intereses, solo
    la de los lugares que atienden alguno."""
    lugares = (datos.recursos[c] for c in polo.paradas)
    return sum(viaje.valor(r, set()) for r in lugares if not intereses or intereses & set(r["intereses"]))


def intereses_del_dia(consulta: Consulta) -> frozenset[str]:
    """Los intereses que piden lugares: la vida nocturna no cambia las paradas del día."""
    return frozenset(i.value for i in consulta.intereses if i not in DE_NOCHE)


def preparados(consulta: Consulta, datos: Datos) -> list[viaje.Preparado]:
    """Las zonas que caben en el viaje, con las reglas del motor, en el orden de su número."""
    origen = datos.origenes[consulta.origen]
    de_origen = aclimatacion.del_origen(origen, datos)
    return [p for polo in datos.polos.values() if (p := viaje.preparar(polo, consulta, origen, datos, de_origen))]


def zonas(consulta: Consulta, datos: Datos, con_intereses: bool = True) -> list[int]:
    """Hasta tres zonas, las más conocidas que caben y con un viaje que visita algo, cada una con su propia
    base: con ``con_intereses``, las de la guía; sin él, las más conocidas. Una zona sin ningún lugar de lo
    que se pidió no entra."""
    intereses = intereses_del_dia(consulta) if con_intereses else frozenset()
    candidatos = preparados(consulta, datos)
    famas = {p.polo.id: fama(p.polo, datos, intereses) for p in candidatos}
    salida, bases = [], set()
    for p in sorted(candidatos, key=lambda p: (-famas[p.polo.id], p.polo.id)):
        if famas[p.polo.id] <= 0:
            break
        if p.polo.base["nombre"] in bases or viaje.armar_itinerario(p) is None:
            continue
        bases.add(p.polo.base["nombre"])
        salida.append(p.polo.id)
        if len(salida) == RUTAS_MAX:
            break
    return salida


def viaje_a(polo: int, consulta: Consulta, datos: Datos) -> Ruta:
    """El viaje que arma el motor a una zona que cabe, como lo devolvería si la propusiera. Su puntaje es 0:
    aquí no se usa."""
    origen = datos.origenes[consulta.origen]
    p = viaje.preparar(datos.polos[polo], consulta, origen, datos, aclimatacion.del_origen(origen, datos))
    it = viaje.armar_itinerario(p) if p is not None else None
    if it is None:
        raise ValueError(f"la zona {polo} no cabe en la consulta o su viaje no visita nada")
    return viaje.armar_ruta(p, it, 0.0, consulta, origen, datos)

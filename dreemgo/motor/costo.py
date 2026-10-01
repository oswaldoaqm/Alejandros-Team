"""
Cuánto cuesta un viaje, por persona: una banda y no un precio.

    transporte   bus interprovincial de ida y vuelta (intercepto + soles por km) y la
                 movilidad local de cada paseo (soles por km recorrido)
    alojamiento  noches × tarifa por noche
    alimentación días × gasto diario
    entradas     la tarifa de adulto peruano que publica cada ficha; un boleto combinado
                 (Boleto Turístico del Cusco, un circuito) se paga una sola vez, y una
                 parada con boleto cuya ficha no da el monto se estima en su rango

Los precios de transporte, hospedaje y comida no están calibrados con tarifas de este año:
cada uno entra con su rango entero (pipeline/referencia/costos.csv) a 4 000 simulaciones
con semilla fija, y la banda va del percentil 20 al 80. Así el ancho de la banda dice cuánto
no sabemos, y la misma consulta da siempre el mismo número.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dreemgo.contrato import Costo
from dreemgo.motor import textos

SIMULACIONES = 4_000
SEMILLA = 20_261_001


@dataclass(frozen=True)
class Gastos:
    """Lo que el costo necesita saber del itinerario."""

    dias: int
    noches: int
    km_interprovincial: float  # ida, por carretera; 0 en un viaje de un día
    km_locales: float  # paseos desde la base, o todo el viaje de un día
    tarifas: tuple[float, ...]  # entradas con monto conocido, sin los boletos combinados
    combinados: tuple[float, ...]  # montos de boletos combinados: se paga el mayor, una vez
    sin_tarifa: int  # paradas con boleto cuyo monto no se conoce
    base: str


def _muestras(parametros: dict, rng: np.random.Generator) -> dict[str, np.ndarray]:
    nombres = sorted(parametros)  # orden fijo: la misma semilla da las mismas muestras
    return {n: rng.uniform(parametros[n]["minimo"], parametros[n]["maximo"], SIMULACIONES) for n in nombres}


def _componentes(p: dict, g: Gastos) -> dict[str, np.ndarray | float]:
    bus = 2 * (p["bus_intercepto"] + p["bus_soles_km"] * g.km_interprovincial) if g.km_interprovincial else 0.0
    return {
        "transporte": bus + p["movilidad_soles_km"] * g.km_locales,
        "alojamiento": g.noches * p["alojamiento_noche"],
        "alimentacion": g.dias * p["alimentacion_dia"],
        "entradas": sum(g.tarifas) + max(g.combinados, default=0.0) + g.sin_tarifa * p["entrada_sin_tarifa"],
    }


def estimar(parametros: dict, g: Gastos, presupuesto: int | None) -> Costo:
    rng = np.random.default_rng(SEMILLA)
    total = sum(np.broadcast_to(v, (SIMULACIONES,)) for v in _componentes(_muestras(parametros, rng), g).values())
    p20, p50, p80 = (int(round(x)) for x in np.percentile(total, [20, 50, 80]))

    # El desglose reparte el P50 en proporción a cada componente con los valores centrales.
    central = _componentes({n: v["valor"] for n, v in parametros.items()}, g)
    suma = sum(central.values()) or 1.0
    desglose = {k: int(round(p50 * v / suma)) for k, v in central.items()}
    mayor = max(sorted(desglose), key=desglose.get)
    desglose[mayor] += p50 - sum(desglose.values())  # lo que se pierde al redondear, al componente mayor

    supuestos = []
    if g.km_interprovincial:
        supuestos.append(f"Bus interprovincial de ida y vuelta: {textos.miles(2 * g.km_interprovincial)} km")
    if g.km_locales:
        supuestos.append(f"Movilidad local en colectivo o taxi: {textos.miles(g.km_locales)} km")
    if g.noches:
        supuestos.append(f"Hospedaje económico en {g.base}, {g.noches} {'noche' if g.noches == 1 else 'noches'}")
    supuestos.append("Entradas de adulto peruano según la ficha oficial de cada lugar")
    if g.sin_tarifa:
        cuantas = "una parada no publica" if g.sin_tarifa == 1 else f"{g.sin_tarifa} paradas no publican"
        supuestos.append(f"{cuantas[0].upper()}{cuantas[1:]} su tarifa: se estima entre S/ 5 y S/ 20")
    supuestos.append("Banda del percentil 20 al 80: transporte, hospedaje y comida en su rango, sin calibrar")

    exceso = None if presupuesto is None or p50 <= presupuesto else p50 - presupuesto
    return Costo(
        p20=p20,
        p50=p50,
        p80=p80,
        desglose=desglose,
        dentro_del_presupuesto=None if presupuesto is None else p50 <= presupuesto,
        exceso=exceso,
        supuestos=supuestos,
    )

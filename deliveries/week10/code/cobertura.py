"""
Qué propone el motor sobre una rejilla de consultas, y cuánto tarda.

Recorre las 24 ciudades de origen, cuatro duraciones (2, 4, 6 y 9 días) y los doce meses, sin
intereses ni presupuesto: 1 152 consultas. Con sus respuestas cuenta cuántos polos distintos
llega a proponer el motor, cuántas rutas van fuera del circuito de Lima y Cusco, qué polos no
aparecen nunca y cuánto tarda cada consulta. Son las cifras del informe del prototipo
(PrototypeReport.md, «Lo que el motor propone hoy»).

Desde la raíz del repositorio, con el paquete instalado (pip install -e .):

    python deliveries/week10/code/cobertura.py

Tarda unos siete minutos. Las rutas son deterministas: con la misma versión de datos salen
los mismos conteos. Los tiempos dependen de la máquina.
"""

from __future__ import annotations

import itertools
import statistics
import time
from collections import Counter

from dreemgo.contrato import Consulta
from dreemgo.motor.datos import cargar
from dreemgo.motor.viaje import resolver

DIAS = (2, 4, 6, 9)
MESES = range(1, 13)
# Polos por los que alguien va a preguntar: dónde duermen y con qué nombre salen en el informe.
CONOCIDOS = {
    "Machupicchu Pueblo": "Machu Picchu",
    "Huaraz": "Huaraz y el Huascarán",
    "Iquitos": "Iquitos",
    "Cuzco": "la ciudad del Cusco",
    "Chachapoyas": "Chachapoyas y Kuélap",
}


def main() -> None:
    datos = cargar()
    origenes = sorted(datos.origenes)
    rutas: list[tuple[str, int, int, str, bool]] = []  # origen, días, polo, base, fuera del circuito
    por_consulta: list[int] = []
    segundos: list[float] = []
    for origen, dias, mes in itertools.product(origenes, DIAS, MESES):
        inicio = time.perf_counter()
        respuesta = resolver(Consulta(origen=origen, dias=dias, mes=mes), datos)
        segundos.append(time.perf_counter() - inicio)
        por_consulta.append(len(respuesta.rutas))
        rutas += [(origen, dias, r.polo.id, r.polo.base.nombre, r.polo.fuera_del_circuito) for r in respuesta.rutas]

    propuestos = Counter(polo for _, _, polo, _, _ in rutas)
    por_base = Counter(base for _, _, _, base, _ in rutas)
    por_origen: dict[str, set[int]] = {}
    for origen, _, polo, _, _ in rutas:
        por_origen.setdefault(origen, set()).add(polo)
    ordenados = sorted(segundos)

    print(f"Datos {datos.version}: {len(datos.polos)} polos, {len(origenes)} orígenes.")
    print(f"Consultas: {len(segundos)} ({len(origenes)} orígenes × {len(DIAS)} duraciones × {len(MESES)} meses).")
    print(
        f"Con tres rutas: {por_consulta.count(3)}. Con dos: {por_consulta.count(2)}. "
        f"Con una: {por_consulta.count(1)}. Sin ninguna: {por_consulta.count(0)}."
    )
    print(f"Rutas propuestas: {len(rutas)}; fuera del circuito, {100 * sum(f for *_, f in rutas) / len(rutas):.0f} %.")
    print(f"Polos distintos que el motor propone al menos una vez: {len(propuestos)} de {len(datos.polos)}.")
    cuantos = sorted(len(polos) for polos in por_origen.values())
    print(f"Polos distintos por origen: mediana {statistics.median(cuantos):.0f}, de {cuantos[0]} a {cuantos[-1]}.")
    for base, nombre in CONOCIDOS.items():
        print(f"Rutas que duermen en {base} ({nombre}): {por_base[base]}.")
    print(
        f"Tiempo por consulta: mediana {1000 * statistics.median(ordenados):.0f} ms, "
        f"percentil 95 {1000 * ordenados[int(0.95 * len(ordenados))]:.0f} ms, máximo {1000 * ordenados[-1]:.0f} ms."
    )


if __name__ == "__main__":
    main()

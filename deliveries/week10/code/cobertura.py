"""
Qué propone el motor sobre una rejilla de consultas, y cuánto tarda.

Recorre las 24 ciudades de origen, cuatro duraciones (2, 4, 6 y 9 días) y los doce meses, sin
intereses ni presupuesto: 1 152 consultas. Con sus respuestas cuenta cuántos polos distintos
llega a proponer el motor, cuántas rutas van fuera del circuito de Lima y Cusco, cuántas vuelan,
van en bus de noche o tienen un primer día tranquilo, dónde se almuerza, qué polos no aparecen
nunca y cuánto tarda cada consulta. Son las cifras del informe del prototipo (PrototypeReport.md,
«Lo que el motor propone hoy»).

Desde la raíz del repositorio, con el paquete instalado (pip install -e .):

    python deliveries/week10/code/cobertura.py

Tarda unos diez minutos. Las rutas son deterministas: con la misma versión de datos salen
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


def por_ciento(parte: int, todo: int) -> str:
    return f"{100 * parte / todo:.0f} %" if todo else "-"


def main() -> None:
    datos = cargar()
    origenes = sorted(datos.origenes)
    rutas = []  # (origen, ruta)
    por_consulta: list[int] = []
    segundos: list[float] = []
    for origen, dias, mes in itertools.product(origenes, DIAS, MESES):
        inicio = time.perf_counter()
        respuesta = resolver(Consulta(origen=origen, dias=dias, mes=mes), datos)
        segundos.append(time.perf_counter() - inicio)
        por_consulta.append(len(respuesta.rutas))
        rutas += [(origen, r) for r in respuesta.rutas]

    n = len(rutas)
    propuestos = Counter(r.polo.id for _, r in rutas)
    por_base = Counter(r.polo.base.nombre for _, r in rutas)
    origenes_de: dict[str, set[str]] = {}
    por_origen: dict[str, set[int]] = {}
    for origen, r in rutas:
        origenes_de.setdefault(r.polo.base.nombre, set()).add(origen)
        por_origen.setdefault(origen, set()).add(r.polo.id)
    diez = sum(c for _, c in propuestos.most_common(10))
    fuera = sum(r.polo.fuera_del_circuito for _, r in rutas)
    con_aviso_de_dias = sum(any(a.tipo == "dias" and a.nivel == "advertencia" for a in r.avisos) for _, r in rutas)
    desaconsejadas = sum(r.estacionalidad.veredicto == "desaconsejado" for _, r in rutas)
    vuelan = [(o, r) for o, r in rutas if r.traslado.vuelos]
    de_noche = sum(r.traslado.bus_de_noche is not None for _, r in rutas)
    tranquilas = sum(any(d.tranquilo for d in r.dias) for _, r in rutas)
    con_visitas = [d for _, r in rutas for d in r.dias if d.paradas]
    almuerzos = [d.almuerzo for d in con_visitas if d.almuerzo]
    sin_donde = sum(a.hay_donde_comer is False for a in almuerzos)
    en_la_base = sum(a.en_la_base for a in almuerzos)
    ordenados = sorted(segundos)

    print(f"Datos {datos.version}: {len(datos.polos)} polos, {len(origenes)} orígenes.")
    print(f"Consultas: {len(segundos)} ({len(origenes)} orígenes × {len(DIAS)} duraciones × {len(MESES)} meses).")
    print(
        f"Con tres rutas: {por_consulta.count(3)}. Con dos: {por_consulta.count(2)}. "
        f"Con una: {por_consulta.count(1)}. Sin ninguna: {por_consulta.count(0)}."
    )
    print(f"Rutas propuestas: {n}; fuera del circuito, {por_ciento(fuera, n)}.")
    print(f"Polos distintos que el motor propone al menos una vez: {len(propuestos)} de {len(datos.polos)}.")
    cuantos = sorted(len(polos) for polos in por_origen.values())
    print(f"Polos distintos por origen: mediana {statistics.median(cuantos):.0f}, de {cuantos[0]} a {cuantos[-1]}.")
    print(f"Rutas que se llevan los diez polos más propuestos: {por_ciento(diez, n)}.")
    print(
        "Rutas con el aviso de que la ida y la vuelta se llevan buena parte del viaje: "
        f"{por_ciento(con_aviso_de_dias, n)}."
    )
    print(f"Rutas en un mes desaconsejado, siempre con su aviso: {desaconsejadas} de {n}.")
    for base, nombre in CONOCIDOS.items():
        desde = sorted(origenes_de.get(base, ()))
        print(f"Rutas que duermen en {base} ({nombre}): {por_base[base]}, desde {len(desde)}: {', '.join(desde)}.")
    print(
        f"Rutas que vuelan: {len(vuelan)} ({por_ciento(len(vuelan), n)}), "
        f"desde {len({o for o, _ in vuelan})} orígenes. En bus de noche: {de_noche} ({por_ciento(de_noche, n)})."
    )
    print(f"Rutas con un primer día tranquilo en la altura: {tranquilas} ({por_ciento(tranquilas, n)}).")
    print(
        f"Días con visitas: {len(con_visitas)}; con almuerzo, {len(almuerzos)}. De esos, en la base "
        f"{en_la_base}, y sin dónde comer registrado cerca, {sin_donde} ({por_ciento(sin_donde, len(almuerzos))})."
    )
    print(
        f"Tiempo por consulta: mediana {1000 * statistics.median(ordenados):.0f} ms, "
        f"percentil 95 {1000 * ordenados[int(0.95 * len(ordenados))]:.0f} ms, máximo {1000 * ordenados[-1]:.0f} ms."
    )


if __name__ == "__main__":
    main()

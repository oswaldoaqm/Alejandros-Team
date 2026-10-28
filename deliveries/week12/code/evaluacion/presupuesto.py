"""
Qué cambia si el presupuesto deja fuera lo que no cabe (semana 12). Lo dejó para decidir el informe de la
semana 10, después de la revisión del profesor del 20 de octubre, que filtraba con el P50 o con el P80.

Hoy el presupuesto se compara con el P50, el costo central: un viaje que lo pasa compite castigado por
(presupuesto / P50)² y sale con su aviso, pero no se esconde (propiedad 7 del contrato). Aquí se comparan,
sobre las mismas consultas, tres criterios:

- **hoy**, el del motor desplegado;
- **filtro P50**, que deja fuera lo que pasa el presupuesto en el P50;
- **filtro P80**, que deja fuera lo que lo pasa en el P80, el escenario conservador.

Un filtro deja fuera un viaje al elegir los tres, después del puntaje: entran los siguientes que caben,
cada uno con su base, como en la copia del profesor. Lo demás es el motor tal cual: ``elegir`` repite los
pasos de ``viaje.resolver`` hasta la elección, y ``medir`` revisa en cada consulta que, sin filtro, dé lo
mismo que el motor.

Las consultas son las 8 de las 40 de la evaluación que traen presupuesto, y las 40 con cuatro montos por
persona (S/ 500, 800, 1 200 y 2 000), para ver lo mismo con más casos. Escribe en
data/evaluacion/resultados/:

  presupuesto.csv    cada consulta y cada criterio: las zonas propuestas, su P50 y su P80
  presupuesto.json   por grupo y criterio: cuántas consultas cambian frente a hoy, cuántas quedan con menos
                     viajes que hoy o sin ninguno, y cuántos viajes de hoy pasan el monto en el P50 o en el P80

Uso:  python -m evaluacion.presupuesto
"""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

from dreemgo.contrato import RUTAS_MAX, Consulta, Costo
from dreemgo.motor import aclimatacion, viaje
from dreemgo.motor import datos as artefactos
from dreemgo.motor.datos import Datos
from evaluacion import consultas

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "evaluacion" / "resultados"
MONTOS = (500, 800, 1200, 2000)
CRITERIOS: dict[str, Callable[[Costo, int], bool]] = {
    "hoy": lambda costo, presupuesto: True,
    "filtro_p50": lambda costo, presupuesto: costo.p50 <= presupuesto,
    "filtro_p80": lambda costo, presupuesto: costo.p80 <= presupuesto,
}


@dataclass(frozen=True)
class Propuesta:
    polo: int
    zona: str
    p50: int
    p80: int


def elegir(consulta: Consulta, datos: Datos, cabe: Callable[[Costo, int], bool]) -> list[Propuesta]:
    """Los viajes que elige el motor para una consulta con presupuesto, dejando fuera los que no ``cabe``n.
    Son los pasos de ``viaje.resolver`` hasta la elección, sin armar las respuestas."""
    origen = datos.origenes[consulta.origen]
    lam = viaje.LAMBDA_SORPRESA if consulta.sorpresa else viaje.LAMBDA
    polos = datos.polos.values() if consulta.destino is None else [datos.polos[consulta.destino]]
    de_origen = aclimatacion.del_origen(origen, datos)
    preparados = [p for polo in polos if (p := viaje.preparar(polo, consulta, origen, datos, de_origen)) is not None]
    if preparados:
        tope = max(p.cota for p in preparados) or 1.0
        preparados.sort(
            key=lambda p: (
                -((1 - lam) * p.temporada * p.noche * p.bus * p.cota / tope + lam * p.polo.novedad),
                p.polo.id,
            )
        )
    itinerarios, bases_planificadas = [], set()
    for n, p in enumerate(preparados[: viaje.POLOS_A_PLANIFICAR_MAX]):
        if n >= viaje.POLOS_A_PLANIFICAR and len(bases_planificadas) >= RUTAS_MAX:
            break
        it = viaje.armar_itinerario(p)
        if it is not None:
            itinerarios.append((p, it))
            bases_planificadas.add(p.polo.base["nombre"])
    mejor = max((it.valor for _, it in itinerarios), default=1.0)
    puntuados = []
    for p, it in itinerarios:
        ocupacion = sum(1 for r in it.recorridos if r.visitas) / len(it.recorridos)
        calidad = it.valor / mejor * ocupacion * p.temporada * p.noche * p.bus
        dias = viaje.dias_del_viaje(it, consulta, origen, datos)
        costo = viaje.costo_del_viaje(it, consulta, datos, dias)
        puntaje = (1 - lam) * calidad * viaje.por_presupuesto(costo, consulta.presupuesto) + lam * it.polo.novedad
        puntuados.append((puntaje, p, costo))
    puntuados.sort(key=lambda x: (-x[0], x[1].polo.id))
    elegidas, bases = [], set()
    for puntaje, p, costo in puntuados:
        if p.polo.base["nombre"] in bases or not cabe(costo, consulta.presupuesto):
            continue
        bases.add(p.polo.base["nombre"])
        # Como en la respuesta: el puntaje redondeado ordena los tres, y si empatan, el número de la zona.
        elegidas.append((round(min(1.0, puntaje), 3), Propuesta(p.polo.id, p.polo.nombre, costo.p50, costo.p80)))
        if len(elegidas) == RUTAS_MAX:
            break
    elegidas.sort(key=lambda x: (-x[0], x[1].polo))
    return [e for _, e in elegidas]


def casos() -> Iterator[tuple[str, int, Consulta]]:
    """(grupo, consulta, la consulta con su presupuesto): las que lo traen, y las 40 con cada monto."""
    anotadas = consultas.leer()
    for a in anotadas:
        if a.consulta.presupuesto is not None:
            yield "con_presupuesto", a.id, a.consulta
    for monto in MONTOS:
        for a in anotadas:
            yield f"monto_{monto}", a.id, a.consulta.model_copy(update={"presupuesto": monto})


def medir(datos: Datos) -> tuple[list[dict], dict]:
    filas, por_grupo = [], {}
    for grupo, id_consulta, consulta in casos():
        propuestas = {nombre: elegir(consulta, datos, cabe) for nombre, cabe in CRITERIOS.items()}
        hoy = propuestas["hoy"]
        del_motor = [r.polo.id for r in viaje.resolver(consulta, datos, sugerir=False).rutas]
        if [p.polo for p in hoy] != del_motor:
            raise RuntimeError(f"consulta {id_consulta} con S/ {consulta.presupuesto}: elegir no da lo del motor")
        presupuesto = consulta.presupuesto
        g = por_grupo.setdefault(
            grupo,
            {"consultas": 0, "viajes_hoy": 0, "hoy_pasan_en_p50": 0, "hoy_pasan_en_p80": 0, "hoy_solo_en_p80": 0}
            | {c: {"cambian": 0, "menos_viajes": 0, "ninguno": 0} for c in CRITERIOS if c != "hoy"},
        )
        g["consultas"] += 1
        g["viajes_hoy"] += len(hoy)
        g["hoy_pasan_en_p50"] += sum(1 for p in hoy if p.p50 > presupuesto)
        g["hoy_pasan_en_p80"] += sum(1 for p in hoy if p.p80 > presupuesto)
        g["hoy_solo_en_p80"] += sum(1 for p in hoy if p.p50 <= presupuesto < p.p80)
        for criterio, elegidas in propuestas.items():
            if criterio != "hoy":
                g[criterio]["cambian"] += [p.polo for p in elegidas] != [p.polo for p in hoy]
                g[criterio]["menos_viajes"] += len(elegidas) < len(hoy)
                g[criterio]["ninguno"] += not elegidas and bool(hoy)
            filas.append(
                {
                    "grupo": grupo,
                    "consulta": id_consulta,
                    "presupuesto": presupuesto,
                    "criterio": criterio,
                    "zonas": " | ".join(p.zona for p in elegidas),
                    "p50": " | ".join(str(p.p50) for p in elegidas),
                    "p80": " | ".join(str(p.p80) for p in elegidas),
                }
            )
    return filas, {"version_datos": datos.version, "montos": list(MONTOS), "por_grupo": por_grupo}


def main() -> None:
    ap = argparse.ArgumentParser(description="Qué cambia si el presupuesto deja fuera lo que no cabe.")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    filas, resumen = medir(artefactos.cargar())
    a.salida.mkdir(parents=True, exist_ok=True)
    with open(a.salida / "presupuesto.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]), delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    texto = json.dumps(resumen, ensure_ascii=False, indent=2) + "\n"
    (a.salida / "presupuesto.json").write_text(texto, encoding="utf-8")
    for grupo, g in resumen["por_grupo"].items():
        p80 = g["filtro_p80"]
        print(
            f"{grupo}: {g['consultas']} consultas; hoy, {g['hoy_pasan_en_p80']} de {g['viajes_hoy']} viajes pasan"
            f" el monto en el P80; con el filtro P80 cambian {p80['cambian']} y {p80['ninguno']} quedan sin viaje."
        )


if __name__ == "__main__":
    main()

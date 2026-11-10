"""
Qué zonas propone cada sistema en las 40 consultas de la evaluación, y en cuántas coinciden (semana 12).

Los tres sistemas son los del kit (decisión 0021): el motor desplegado, la guía por intereses, que es la línea de
base, y la variante del motor con la décima parte para lo que no se pidió. La clave del kit
(data/evaluacion/clave.csv) dice qué zonas propone cada uno para cada consulta y en qué puesto. De ahí salen, sin
juzgar ningún viaje:

- la cobertura: cuántas zonas distintas propone cada uno, de las 194 del motor;
- cuántos de sus viajes van fuera del circuito de Lima y el Cusco, y la novedad media de lo que propone (la de
  ``Polo.novedad``, que usa el motor para elegir);
- en cuántas de sus propuestas coinciden dos sistemas, consulta por consulta, sin mirar el puesto.

Escribe en data/evaluacion/resultados/zonas.json.

Uso:  python -m evaluacion.zonas
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from itertools import combinations
from pathlib import Path

from dreemgo.motor import datos as artefactos
from dreemgo.motor.datos import Datos
from evaluacion.informe import CARPETA, Viaje, leer_clave


def propuestas(viajes: list[Viaje], sistemas: list[str]) -> dict[str, dict[int, set[int]]]:
    """Las zonas que propone cada sistema en cada consulta."""
    salida = {s: defaultdict(set) for s in sistemas}
    for v in viajes:
        for s in v.puestos:
            salida[s][v.consulta].add(v.polo)
    return salida


def cobertura(de_cada: dict[str, dict[int, set[int]]], datos: Datos) -> dict:
    """Por sistema: cuántos viajes propone, cuántas zonas distintas, qué parte va fuera del circuito y la
    novedad media."""
    salida = {}
    for s, por_consulta in de_cada.items():
        todas = [p for zonas in por_consulta.values() for p in zonas]
        salida[s] = {
            "viajes": len(todas),
            "zonas_distintas": len(set(todas)),
            "de": len(datos.polos),
            "fuera_del_circuito": round(sum(datos.polos[p].fuera_del_circuito for p in todas) / len(todas), 4),
            "novedad_media": round(sum(datos.polos[p].novedad for p in todas) / len(todas), 4),
        }
    return salida


def coinciden(de_cada: dict[str, dict[int, set[int]]]) -> dict:
    """Por par de sistemas: en cuántas propuestas coinciden, sumando las 40 consultas, y en cuántas consultas
    proponen las mismas zonas."""
    salida = {}
    for a, b in combinations(de_cada, 2):
        consultas = sorted(set(de_cada[a]) | set(de_cada[b]))
        comunes = sum(len(de_cada[a][n] & de_cada[b][n]) for n in consultas)
        iguales = sum(de_cada[a][n] == de_cada[b][n] for n in consultas)
        salida[f"{a}_y_{b}"] = {
            "propuestas_en_comun": comunes,
            "de": sum(len(de_cada[a][n]) for n in consultas),
            "consultas_con_las_mismas_zonas": iguales,
            "consultas": len(consultas),
        }
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="Qué zonas propone cada sistema y en cuántas coinciden.")
    ap.add_argument("--clave", type=Path, default=CARPETA / "clave.csv")
    ap.add_argument("--salida", type=Path, default=CARPETA / "resultados")
    a = ap.parse_args()
    viajes, sistemas = leer_clave(a.clave)
    datos = artefactos.cargar()
    de_cada = propuestas(viajes, sistemas)
    resumen = {
        "version_datos": datos.version,
        "consultas": len({v.consulta for v in viajes}),
        "cobertura": cobertura(de_cada, datos),
        "coinciden": coinciden(de_cada),
    }
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "zonas.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for s, c in resumen["cobertura"].items():
        print(
            f"{s}: {c['zonas_distintas']} zonas de {c['de']}, {c['fuera_del_circuito']:.0%} fuera del circuito,"
            f" novedad {c['novedad_media']:.3f}"
        )
    for par, c in resumen["coinciden"].items():
        print(f"{par}: {c['propuestas_en_comun']} de {c['de']} propuestas en común")


if __name__ == "__main__":
    main()

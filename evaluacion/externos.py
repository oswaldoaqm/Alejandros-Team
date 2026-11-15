"""
Lo que dicen los calificadores de fuera del equipo contra lo que dijo el equipo, en los mismos viajes (decisión
0033).

Lee las notas del kit corto (``data/evaluacion/externos/calificaciones/*.csv``, de ``kit_externo.py``) y las del
equipo (``data/evaluacion/calificaciones/``), solo en las consultas del kit corto, y escribe
``data/evaluacion/externos/resumen.json`` con:

- cuántas personas de fuera calificaron, y su acuerdo entre ellas (kappa de Fleiss);
- la diferencia de la nota media de cada viaje, equipo menos fuera, con su intervalo de 95 % por bootstrap sobre
  las consultas: si el equipo se califica mejor, sale positiva;
- el nDCG@3 del motor y de la guía con las notas de fuera y con las del equipo, en esas consultas.

Uso:  python -m evaluacion.externos
"""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from evaluacion import acuerdo, metricas
from evaluacion.informe import CARPETA, Viaje, _media, leer_calificaciones, leer_clave
from evaluacion.kit_externo import elegidas

EXTERNOS = CARPETA / "externos"


def calcular(clave: Path, del_equipo: Path, de_fuera: Path) -> dict:
    viajes, sistemas = leer_clave(clave)
    consultas = set(elegidas())
    mios = [v for v in viajes if v.consulta in consultas]
    fuera = leer_calificaciones(de_fuera, mios)
    equipo = {
        q: {k: n for k, n in notas.items() if k[0] in consultas}
        for q, notas in leer_calificaciones(del_equipo, viajes).items()
    }
    claves = [(v.consulta, v.opcion) for v in mios]
    media_fuera = {k: _media([fuera[q][k] for q in fuera]) for k in claves}
    media_equipo = {k: _media([equipo[q][k] for q in equipo]) for k in claves}
    completas = [[fuera[q][k] for q in sorted(fuera)] for k in claves]
    completas = [n for n in completas if all(x is not None for x in n)]

    # Equipo menos fuera, por consulta: la media de las diferencias de sus viajes.
    por_consulta = defaultdict(list)
    for k in claves:
        if media_fuera[k] is not None and media_equipo[k] is not None:
            por_consulta[k[0]].append(media_equipo[k] - media_fuera[k])
    diferencias = [sum(d) / len(d) for _, d in sorted(por_consulta.items())]

    def ndcg(media: dict) -> dict[str, float]:
        de_la_consulta: dict[int, list[Viaje]] = defaultdict(list)
        for v in mios:
            de_la_consulta[v.consulta].append(v)
        salida = {}
        for s in sistemas:
            valores = []
            for vs in de_la_consulta.values():
                todas = [media[(v.consulta, v.opcion)] or 0.0 for v in vs]
                orden = sorted((v for v in vs if s in v.puestos), key=lambda v: v.puestos[s])
                valores.append(metricas.ndcg([media[(v.consulta, v.opcion)] or 0.0 for v in orden], todas))
            salida[s] = sum(valores) / len(valores)
        return salida

    bajo, alto = metricas.intervalo(diferencias)
    return {
        "consultas": sorted(consultas),
        "viajes": len(claves),
        "de_fuera": len(fuera),
        "kappa_fleiss_de_fuera": acuerdo.kappa_de_fleiss(completas) if completas else None,
        "equipo_menos_fuera": {
            "media": sum(diferencias) / len(diferencias),
            "ic95": [bajo, alto],
            "consultas": len(diferencias),
        },
        "ndcg3_con_las_notas_de_fuera": ndcg(media_fuera),
        "ndcg3_con_las_notas_del_equipo": ndcg(media_equipo),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Las notas de fuera del equipo contra las del equipo.")
    ap.add_argument("--clave", type=Path, default=CARPETA / "clave.csv")
    ap.add_argument("--equipo", type=Path, default=CARPETA / "calificaciones")
    ap.add_argument("--fuera", type=Path, default=EXTERNOS / "calificaciones")
    a = ap.parse_args()
    resumen = calcular(a.clave, a.equipo, a.fuera)
    (EXTERNOS / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    d = resumen["equipo_menos_fuera"]
    print(
        f"{resumen['de_fuera']} de fuera · {resumen['viajes']} viajes · equipo menos fuera {d['media']:+.3f} "
        f"(IC 95 % {d['ic95'][0]:+.3f} a {d['ic95'][1]:+.3f})"
    )


if __name__ == "__main__":
    main()

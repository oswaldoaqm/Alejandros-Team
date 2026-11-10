"""
Las cifras de la evaluación de la semana 12, con las calificaciones del equipo (decisión 0021).

Lee la clave del kit (data/evaluacion/clave.csv) y las calificaciones de cada quien
(data/evaluacion/calificaciones/<INICIALES>.csv, como las descarga el cuadernillo o como queda la planilla),
revisa que sean de este kit y escribe en data/evaluacion/resultados/:

  notas.csv      cada viaje con la nota de cada quien, su media y el puesto que le da cada sistema
  metricas.csv   por consulta y por sistema: nDCG@3, P@3, el rango recíproco y cuántos no encajan
  resumen.json   el acuerdo, la media de cada métrica por sistema, las comparaciones, la cobertura y la
                 novedad, y lo mismo por interés

Uso:  python -m evaluacion.informe
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from dreemgo.motor import datos as artefactos
from evaluacion import acuerdo, consultas, metricas

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "data" / "evaluacion"
NOTAS = ("0", "1", "2")
COMPARACIONES = (("motor", "guia"), ("variante", "motor"))


@dataclass(frozen=True)
class Viaje:
    consulta: int
    opcion: str
    polo: int
    zona: str
    puestos: dict[str, int]


def _filas(ruta: Path) -> list[dict]:
    """Las filas de un CSV del kit. Acepta lo que deja Excel al guardar: «;» o «,», y UTF-8 o Windows-1252."""
    crudo = ruta.read_bytes()
    try:
        texto = crudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = crudo.decode("cp1252")
    primera = texto.split("\n", 1)[0]
    separador = ";" if primera.count(";") >= primera.count(",") else ","
    return list(csv.DictReader(texto.splitlines(), delimiter=separador))


def leer_clave(ruta: Path) -> tuple[list[Viaje], list[str]]:
    filas = _filas(ruta)
    sistemas = [c.removeprefix("puesto_") for c in filas[0] if c.startswith("puesto_")]
    viajes = [
        Viaje(
            int(f["consulta"]),
            f["opcion"],
            int(f["polo"]),
            f["zona"],
            {s: int(f[f"puesto_{s}"]) for s in sistemas if f[f"puesto_{s}"].strip()},
        )
        for f in filas
    ]
    return viajes, sistemas


def leer_calificaciones(carpeta: Path, viajes: list[Viaje]) -> dict[str, dict[tuple[int, str], int | None]]:
    """Las notas de cada quien, por (consulta, opción). Se niega si un archivo no es de este kit: le falta
    o le sobra un viaje, o la zona de una opción no es la de la clave."""
    zonas = {(v.consulta, v.opcion): v.zona for v in viajes}
    salida = {}
    for ruta in sorted(carpeta.glob("*.csv")):
        notas, problemas = {}, []
        for f in _filas(ruta):
            clave = (int(f["consulta"]), f["opcion"].strip())
            if zonas.get(clave) != f["zona"].strip():
                problemas.append(f"{clave[0]}{clave[1]}")
                continue
            nota = f["calificacion"].strip()
            if nota and nota not in NOTAS:
                problemas.append(f"{clave[0]}{clave[1]}: «{nota}»")
                continue
            notas[clave] = int(nota) if nota else None
        faltan = sorted(set(zonas) - set(notas))
        if problemas or faltan:
            raise ValueError(f"{ruta.name} no es de este kit: {problemas[:5]} distintas, {len(faltan)} faltan")
        salida[ruta.stem] = notas
    if len(salida) < 2:
        raise ValueError(f"hacen falta las calificaciones de dos personas o más en {carpeta}")
    return salida


def _media(valores: list[int | None]) -> float | None:
    hay = [v for v in valores if v is not None]
    return sum(hay) / len(hay) if hay else None


def calcular(clave: Path, calificaciones: Path) -> tuple[list[dict], list[dict], dict]:
    viajes, sistemas = leer_clave(clave)
    quienes = leer_calificaciones(calificaciones, viajes)
    nombres = sorted(quienes)
    por_viaje = {(v.consulta, v.opcion): [quienes[q][(v.consulta, v.opcion)] for q in nombres] for v in viajes}
    completas = [n for n in por_viaje.values() if all(x is not None for x in n)]
    resumen: dict = {
        "calificadores": len(nombres),
        "viajes": len(viajes),
        "acuerdo": {
            "viajes_con_todas_las_notas": len(completas),
            "kappa_fleiss": acuerdo.kappa_de_fleiss(completas) if completas else None,
            "alfa_krippendorff_ordinal": acuerdo.alfa_de_krippendorff(list(por_viaje.values())),
            "alfa_krippendorff_nominal": acuerdo.alfa_de_krippendorff(list(por_viaje.values()), "nominal"),
            "coinciden_todos": sum(1 for n in completas if len(set(n)) == 1) / len(completas) if completas else None,
            "notas_por_calificador": {
                q: {k: sum(1 for x in quienes[q].values() if x == int(k)) for k in NOTAS} for q in nombres
            },
        },
    }
    media = {k: _media(n) for k, n in por_viaje.items()}
    notas = []
    for v in viajes:
        clave_viaje = (v.consulta, v.opcion)
        de_cada = zip(nombres, por_viaje[clave_viaje], strict=True)
        notas.append(
            {
                "consulta": v.consulta,
                "opcion": v.opcion,
                "polo": v.polo,
                "zona": v.zona,
                **{f"puesto_{s}": v.puestos.get(s, "") for s in sistemas},
                **{f"nota_{q}": "" if x is None else x for q, x in de_cada},
                "media": "" if media[clave_viaje] is None else round(media[clave_viaje], 4),
            }
        )

    # Por consulta y por sistema, con la media de cada viaje (los que nadie calificó cuentan 0).
    de_la_consulta = defaultdict(list)
    for v in viajes:
        de_la_consulta[v.consulta].append(v)
    filas, por_sistema = [], {s: defaultdict(list) for s in sistemas}
    for n, vs in sorted(de_la_consulta.items()):
        todas = [media[(v.consulta, v.opcion)] or 0.0 for v in vs]
        for s in sistemas:
            orden = sorted((v for v in vs if s in v.puestos), key=lambda v: v.puestos[s])
            propuestas = [media[(v.consulta, v.opcion)] or 0.0 for v in orden]
            cifras = {
                "ndcg3": metricas.ndcg(propuestas, todas),
                "p3": metricas.precision(propuestas),
                "rr": metricas.rango_reciproco(propuestas),
                "no_encajan": metricas.no_encajan(propuestas),
            }
            filas.append({"consulta": n, "sistema": s, **{k: round(x, 4) for k, x in cifras.items()}})
            for k, x in cifras.items():
                por_sistema[s][k].append(x)
    resumen["por_sistema"] = {s: {k: sum(xs) / len(xs) for k, xs in m.items()} for s, m in por_sistema.items()}
    resumen["comparaciones"] = {
        f"{a}_menos_{b}": {k: metricas.comparar(por_sistema[a][k], por_sistema[b][k]) for k in ("ndcg3", "p3")}
        for a, b in COMPARACIONES
        if a in sistemas and b in sistemas
    }

    # La cobertura y la novedad: cuántas zonas distintas propone cada uno y cuántas fuera del circuito.
    datos = artefactos.cargar()
    resumen["cobertura"] = {}
    for s in sistemas:
        propuestas = [v.polo for v in viajes if s in v.puestos]
        fuera = sum(1 for p in propuestas if datos.polos[p].fuera_del_circuito)
        resumen["cobertura"][s] = {
            "zonas_distintas": len(set(propuestas)),
            "de": len(datos.polos),
            "fuera_del_circuito": fuera / len(propuestas),
            "novedad_media": sum(datos.polos[p].novedad for p in propuestas) / len(propuestas),
        }

    # Lo mismo por interés: cada consulta cuenta en cada uno de sus intereses, y las sin interés aparte.
    intereses = {c.id: [i.value for i in c.consulta.intereses] or ["sin_intereses"] for c in consultas.leer()}
    grupos = defaultdict(lambda: defaultdict(list))
    for f in filas:
        for i in intereses[f["consulta"]]:
            grupos[i][f["sistema"]].append(f["ndcg3"])
    resumen["ndcg3_por_interes"] = {
        i: {"consultas": len(next(iter(m.values()))), **{s: sum(xs) / len(xs) for s, xs in m.items()}}
        for i, m in sorted(grupos.items())
    }
    return notas, filas, resumen


def _escribir(ruta: Path, filas: list[dict]) -> None:
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]), delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def main() -> None:
    ap = argparse.ArgumentParser(description="Las cifras de la evaluación de la semana 12.")
    ap.add_argument("--clave", type=Path, default=CARPETA / "clave.csv")
    ap.add_argument("--calificaciones", type=Path, default=CARPETA / "calificaciones")
    ap.add_argument("--salida", type=Path, default=CARPETA / "resultados")
    a = ap.parse_args()
    notas, filas, resumen = calcular(a.clave, a.calificaciones)
    a.salida.mkdir(parents=True, exist_ok=True)
    _escribir(a.salida / "notas.csv", notas)
    _escribir(a.salida / "metricas.csv", filas)
    (a.salida / "resumen.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    kappa = resumen["acuerdo"]["kappa_fleiss"]
    print(f"{resumen['calificadores']} calificadores y {resumen['viajes']} viajes; kappa de Fleiss, {kappa:.3f}.")
    for s, m in resumen["por_sistema"].items():
        cifras = f"nDCG@3 {m['ndcg3']:.3f} · P@3 {m['p3']:.3f} · MRR {m['rr']:.3f} · no encajan {m['no_encajan']:.3f}"
        print(f"  {s}: {cifras}")


if __name__ == "__main__":
    main()

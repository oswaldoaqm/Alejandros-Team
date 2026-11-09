"""
La auditoría del motor (semana 13): lo que miraría un jurado que busca pruebas en contra, con su cifra
(docs/AUDITORIA.md). Corre la rejilla de la semana 10, sin intereses: los 24 orígenes, 2, 4, 6 y 9 días y los doce
meses, 1 152 consultas. De cada viaje guarda sus días y sus paradas, y de ahí salen:

- los tramos del día que empiezan y terminan en una misma ciudad grande o en Lima, con su velocidad de puerta a
  puerta, contra la que mide TomTom de día manejando (``pipeline/referencia/trafico_ciudades.csv``): Lima para la
  metrópoli y Arequipa para las grandes, las dos ciudades del ajuste (decisión 0025);
- qué tan llenos van los días: horas ocupadas y paradas por día, en todo el país y en Lima;
- el orden de las paradas: en los días de tres a siete, el camino en el orden elegido contra el mejor orden
  posible de esas mismas paradas, por fuerza bruta y sin mirar horarios, que es una cota de lo que el orden podría
  mejorar;
- cuánto dura la visita a los lugares de jerarquía 3 y 4;
- lo que se ve de noche, puesto de día, por su nombre;
- qué tan concentrados están los viajes en pocas zonas.

La ciudad de un punto es la mancha de la red (``pipeline.red_vial.manchas_urbanas``) en su vértice más cercano, así
que hace falta la red vial que arma el pipeline, en ``data/externos/osm/``.

Escribe data/evaluacion/resultados/auditoria.json con los datos que carga el motor. Con ``--datos`` usa otros
artefactos, por ejemplo los de una versión anterior sacados con ``git show``, y escribe auditoria_<versión>.json.
Con ``--variante``, la rejilla va con la variante del kit (``evaluacion.variante``) y escribe
auditoria_variante.json: así se ve si reparte más los viajes. Con ``--detalle`` guarda también cada viaje, unos
18 MB, y con ``--desde`` saca las cifras de un detalle guardado, sin volver a correr la rejilla.

Uso:  python -m evaluacion.auditoria [--red <red_vial.npz>] [--datos <carpeta>] [--variante] [--detalle <archivo>]
      python -m evaluacion.auditoria --desde <archivo.json> [--red <red_vial.npz>]
"""

from __future__ import annotations

import argparse
import itertools
import json
import statistics
from collections import Counter
from contextlib import nullcontext
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from dreemgo.contrato import Consulta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from dreemgo.motor.datos import Datos
from evaluacion import variante

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "evaluacion" / "resultados"
DIAS = (2, 4, 6, 9)
ORDEN_HASTA = 7  # paradas: con más, la fuerza bruta tarda demasiado
DE_NOCHE = ("circuito mágico", "espectáculo", "show", "observatorio", "planetario", "nocturn")
DE_NOCHE_AL_EMPEZAR = ("peña",)  # «Peña ...» sí; «Paseo Sáenz Peña», no

_DATOS: Datos | None = None
_VARIANTE = False


def _iniciar(carpeta: str | None, con_variante: bool = False) -> None:
    global _DATOS, _VARIANTE
    _DATOS = artefactos.cargar(Path(carpeta)) if carpeta else artefactos.cargar()
    _VARIANTE = con_variante


def rejilla(datos: Datos) -> list[tuple[str, int, int]]:
    """(origen, mes, días) de las 1 152 consultas, en un orden fijo."""
    return [(o, m, d) for o in sorted(datos.origenes) for d in DIAS for m in range(1, 13)]


def camino_y_mejor(base: np.ndarray, entre: np.ndarray, orden: list[int]) -> tuple[float, float] | None:
    """(minutos de camino en ``orden``, en el mejor orden de las mismas paradas), saliendo de la base y volviendo
    a ella; None si algún tramo no tiene camino."""

    def total(o) -> float:
        return float(base[o[0]] + base[o[-1]] + sum(entre[a, b] for a, b in itertools.pairwise(o)))

    dado = total(orden)
    if not np.isfinite(dado):
        return None
    return dado, min(total(p) for p in itertools.permutations(orden))


def correr(consulta: tuple[str, int, int]) -> dict:
    """Los viajes de una consulta, con lo que la auditoría mira de cada día y cada parada."""
    origen, mes, dias = consulta
    with variante.con_concavidad() if _VARIANTE else nullcontext():
        r = viaje.resolver(Consulta(origen=origen, mes=mes, dias=dias), _DATOS)
    rutas = []
    for ruta in r.rutas:
        polo = _DATOS.polos[ruta.polo.id]
        indice = polo.indice()
        dias_ = []
        for d in ruta.dias:
            codigos = [p.recurso.codigo for p in d.paradas]
            orden = None
            if d.tipo == "visita" and 3 <= len(codigos) <= ORDEN_HASTA and all(c in indice for c in codigos):
                orden = camino_y_mejor(polo.base_minutos, polo.entre_minutos, [indice[c] for c in codigos])
            dias_.append(
                {
                    "tipo": d.tipo,
                    "horas": d.horas,
                    "almuerzo": d.almuerzo.hora if d.almuerzo else None,
                    "orden": orden,
                    "paradas": [
                        {
                            "nombre": p.recurso.nombre,
                            "jerarquia": p.recurso.jerarquia,
                            "lat": p.recurso.lat,
                            "lon": p.recurso.lon,
                            "llegada": p.llegada,
                            "traslado": p.minutos_traslado,
                            "km": p.km_desde_anterior,
                            "visita": p.minutos_visita,
                        }
                        for p in d.paradas
                    ],
                }
            )
        rutas.append(
            {
                "polo": ruta.polo.id,
                "nombre": ruta.polo.nombre,
                "base": [polo.base["lat"], polo.base["lon"]],
                "dias": dias_,
            }
        )
    return {"origen": origen, "mes": mes, "dias": dias, "rutas": rutas}


def de_noche(nombre: str) -> bool:
    """Si el nombre dice que el lugar se ve de noche."""
    n = nombre.lower()
    return any(k in n for k in DE_NOCHE) or n.startswith(DE_NOCHE_AL_EMPEZAR)


def _parte(n: int, de: int) -> float:
    return round(n / de, 3) if de else 0.0


def cifras(corrida: list[dict], banda_de, tomtom_kmh: dict[str, float]) -> dict:
    """Las cifras de la auditoría. ``banda_de(lat, lon)`` da (mancha, banda) de un punto, con la banda como nombre
    (``pipeline.red_vial.BANDAS``); ``tomtom_kmh``, la velocidad de TomTom de día por banda."""
    viajes = [r for q in corrida for r in q["rutas"]]
    de_visita = [d for r in viajes for d in r["dias"] if d["tipo"] == "visita" and d["paradas"]]

    tramos: dict[str, list[tuple[float, float, float]]] = {b: [] for b in tomtom_kmh}
    for r in viajes:
        for d in r["dias"]:
            anterior = banda_de(*r["base"])
            for p in d["paradas"]:
                aqui = banda_de(p["lat"], p["lon"])
                if aqui[0] and aqui == anterior and aqui[1] in tramos and p["km"] >= 1 and p["traslado"] > 0:
                    tramos[aqui[1]].append((p["km"], p["traslado"], p["km"] / (p["traslado"] / 60)))
                anterior = aqui
    en_ciudad = {}
    for b, t in tramos.items():
        if t:
            en_ciudad[b] = {
                "tramos": len(t),
                "km_mediana": round(statistics.median(x[0] for x in t), 1),
                "minutos_mediana": round(statistics.median(x[1] for x in t), 1),
                "kmh_mediana": round(statistics.median(x[2] for x in t), 1),
                "tomtom_kmh": round(tomtom_kmh[b], 1),
                "mas_rapidos_que_tomtom": _parte(sum(x[2] > tomtom_kmh[b] for x in t), len(t)),
            }

    horas = [d["horas"] for d in de_visita]
    en_lima = [
        d
        for r in viajes
        if banda_de(*r["base"])[1] == "metropoli"
        for d in r["dias"]
        if d["tipo"] == "visita" and d["paradas"]
    ]
    dias = {
        "de_visita": len(de_visita),
        "con_7_5_horas_o_mas": _parte(sum(h >= 7.5 for h in horas), len(horas)),
        "con_7_horas_o_mas": _parte(sum(h >= 7 for h in horas), len(horas)),
        "con_6_paradas": _parte(sum(len(d["paradas"]) >= 6 for d in de_visita), len(de_visita)),
        "paradas_por_dia": dict(sorted(Counter(len(d["paradas"]) for d in de_visita).items())),
        "en_lima": {
            "dias": len(en_lima),
            "paradas_mediana": statistics.median(len(d["paradas"]) for d in en_lima) if en_lima else None,
            "con_6_paradas": _parte(sum(len(d["paradas"]) >= 6 for d in en_lima), len(en_lima)),
            "paradas_por_dia": dict(sorted(Counter(len(d["paradas"]) for d in en_lima).items())),
        },
    }

    brechas = [o[0] / o[1] - 1 for d in de_visita if (o := d.get("orden")) and o[1] > 0]
    orden = {
        "dias": len(brechas),
        "el_mejor": _parte(sum(x < 1e-6 for x in brechas), len(brechas)),
        "a_mas_de_5_por_ciento": _parte(sum(x > 0.05 for x in brechas), len(brechas)),
    }

    paradas = [p for d in de_visita for p in d["paradas"]]
    visitas = {}
    for j in (4, 3):
        pj = [p for p in paradas if p["jerarquia"] == j]
        cortas = [p for p in pj if p["visita"] <= 30]
        visitas[str(j)] = {
            "paradas": len(pj),
            "minutos_mediana": statistics.median(p["visita"] for p in pj) if pj else None,
            "de_30_o_menos": _parte(len(cortas), len(pj)),
            "las_mas_frecuentes_de_30_o_menos": Counter(p["nombre"] for p in cortas).most_common(6),
        }

    noche = [(p["nombre"], p["llegada"]) for p in paradas if de_noche(p["nombre"])]
    zonas = Counter(r["nombre"] for r in viajes)
    return {
        "consultas": len(corrida),
        "viajes": len(viajes),
        "tramos_en_ciudad": en_ciudad,
        "dias": dias,
        "orden": orden,
        "visitas_por_jerarquia": visitas,
        "de_noche_en_el_dia": {
            "paradas": len(noche),
            "las_mas_frecuentes": [[n, h, k] for (n, h), k in Counter(noche).most_common(6)],
        },
        "concentracion": {
            "zonas_distintas": len(zonas),
            "las_5_mas_propuestas": [[n, _parte(k, len(viajes))] for n, k in zonas.most_common(5)],
            "las_10_mas_propuestas": _parte(sum(k for _, k in zonas.most_common(10)), len(viajes)),
            "con_base_en_ciudad_grande_o_lima": _parte(
                sum(banda_de(*r["base"])[1] in ("grande", "metropoli") for r in viajes), len(viajes)
            ),
        },
    }


def bandas_de_la_red(npz: Path):
    """(mancha, banda) de un punto, por el vértice de la red más cercano."""
    from scipy.spatial import cKDTree

    from pipeline.red_vial import BANDAS, KM2_BANDAS, Red, manchas_urbanas

    red = Red.cargar(npz)
    mancha, km2 = manchas_urbanas(red)
    banda = np.searchsorted(KM2_BANDAS, km2, side="right")
    banda[0] = 0
    arbol = cKDTree(np.column_stack([red.lat, red.lon * np.cos(np.radians(red.lat))]))

    def banda_de(lat: float, lon: float) -> tuple[int, str]:
        _, v = arbol.query([lat, lon * np.cos(np.radians(lat))])
        m = int(mancha[v])
        return m, BANDAS[int(banda[m])]

    return banda_de


def tomtom_por_banda() -> dict[str, float]:
    """km/h de día de la ciudad del ajuste de cada banda con piso."""
    from pipeline.red_calibracion import trafico

    t = trafico()
    t = t[t["uso"] == "ajuste"]
    return {b: 600 / float(m) for b, m in zip(t["banda"], t["meta_min_10km"], strict=True)}


def _red_del_pipeline() -> Path:
    from pipeline.maestro import EXTERNOS
    from pipeline.tiempos import CACHE

    osm = EXTERNOS / "osm"
    md5 = json.loads((osm / "manifiesto.json").read_text(encoding="utf-8"))["md5"]
    return osm / f"red_vial_{md5[:8]}_v{CACHE}.npz"


def main() -> None:
    ap = argparse.ArgumentParser(description="La auditoría del motor sobre la rejilla de la semana 10.")
    ap.add_argument("--red", type=Path, default=None, help="la red vial del pipeline (por defecto, la de su caché)")
    ap.add_argument("--datos", type=Path, default=None, help="otra carpeta de artefactos")
    ap.add_argument("--detalle", type=Path, default=None, help="guarda aquí cada viaje")
    ap.add_argument("--desde", type=Path, default=None, help="las cifras de un detalle guardado, sin la rejilla")
    ap.add_argument("--variante", action="store_true", help="la rejilla con la variante del kit")
    ap.add_argument("--procesos", type=int, default=2)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    if a.desde:
        guardado = json.loads(a.desde.read_text(encoding="utf-8"))
        version, corrida = guardado["version_datos"], guardado["rejilla"]
        a.variante = guardado.get("variante", False)
    else:
        carpeta = str(a.datos) if a.datos else None
        _iniciar(carpeta, a.variante)
        with Pool(a.procesos, initializer=_iniciar, initargs=(carpeta, a.variante)) as pool:
            corrida = pool.map(correr, rejilla(_DATOS), chunksize=8)
        version = _DATOS.version
        if a.detalle:
            texto = json.dumps(
                {"version_datos": version, "variante": a.variante, "rejilla": corrida}, ensure_ascii=False
            )
            a.detalle.write_text(texto, encoding="utf-8")
    resumen = {
        "version_datos": version,
        "con": "la variante del kit" if a.variante else "el motor",
        **cifras(corrida, bandas_de_la_red(a.red or _red_del_pipeline()), tomtom_por_banda()),
    }
    a.salida.mkdir(parents=True, exist_ok=True)
    desplegada = json.loads((artefactos.DATOS / "manifiesto.json").read_text(encoding="utf-8"))["version_datos"]
    nombre = "auditoria.json" if version == desplegada else f"auditoria_{version}.json"
    if a.variante:
        nombre = nombre.replace("auditoria", "auditoria_variante")
    (a.salida / nombre).write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lima = resumen["tramos_en_ciudad"].get("metropoli", {})
    print(
        f"{resumen['consultas']} consultas, {resumen['viajes']} viajes (datos {resumen['version_datos']}). "
        f"En Lima, {lima.get('mas_rapidos_que_tomtom', 0):.0%} de los tramos va más rápido que TomTom; "
        f"{resumen['dias']['con_6_paradas']:.0%} de los días tiene 6 paradas; "
        f"las 10 zonas más propuestas se llevan {resumen['concentracion']['las_10_mas_propuestas']:.0%} de los viajes."
    )


if __name__ == "__main__":
    main()

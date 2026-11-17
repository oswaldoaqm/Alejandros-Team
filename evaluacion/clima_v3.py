"""El clima de los grupos de TA-01 v3 contra el de la v2 (decisión 0023).

Para cada parada que está en un grupo en las dos versiones, compara el veredicto de cada mes que da el clima de su
grupo v2 con el que da el de su grupo v3, con el mismo cálculo de ``pipeline/clima.py``. Los grupos v3 son los de
la corrida del 28 de octubre (``data/evaluacion/resultados/polos_v3_del_clima.csv``), que es para la que se bajó
el clima: 108 grupos con su punto propio, en ``data/externos/clima/crudo_v3/``, y 95 con el punto de un grupo v2 a
menos de 9 km de su centro, en ``data/externos/clima/crudo/``. Las descargas están fuera de git.

    python -m evaluacion.clima_v3

Escribe ``data/evaluacion/resultados/clima_v3.json``.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from pipeline import clima

RAIZ = Path(__file__).resolve().parents[1]
CLIMA = RAIZ / "data" / "externos" / "clima"
GRUPOS = RAIZ / "data" / "evaluacion" / "resultados" / "polos_v3_del_clima.csv"
MAESTRO = RAIZ / "data" / "procesados" / "maestro_v3.csv"
SALIDA = RAIZ / "data" / "evaluacion" / "resultados" / "clima_v3.json"
CERCA_KM = 9.0


def _km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    a, b, c, d = map(math.radians, (lat1, lon1, lat2, lon2))
    h = math.sin((c - a) / 2) ** 2 + math.cos(a) * math.cos(c) * math.sin((d - b) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(h))


def veredictos_de(ruta: Path) -> dict[int, str] | None:
    leido = clima.leer_crudo(ruta)
    if leido is None:
        return None
    m = clima.mensual(leido[0])
    _, v = clima.veredictos(m["lluvia_mm"])
    return {int(mes): str(x) for mes, x in zip(m["mes"], v, strict=True)}


def comparar(grupos: pd.DataFrame, carpeta: Path = CLIMA) -> dict:
    puntos_v2 = pd.read_csv(carpeta / "puntos_polos.csv", sep=";")
    propios = {int(str(p).split("_")[1]): str(p) for p in pd.read_csv(carpeta / "puntos_v3.csv", sep=";")["polo"]}
    v2 = {int(g): veredictos_de(carpeta / "crudo" / f"polo_{g}.json") for g in grupos["grupo_v2"].unique() if g >= 0}
    v3, lejos = {}, 0.0
    for g, sub in grupos[grupos["grupo_v3"] >= 0].groupby("grupo_v3"):
        if g in propios:
            v3[int(g)] = veredictos_de(carpeta / "crudo_v3" / f"polo_{propios[g]}.json")
            continue
        lat, lon = sub["lat"].mean(), sub["lon"].mean()
        d = puntos_v2.apply(lambda r, lat=lat, lon=lon: _km(lat, lon, r["lat"], r["lon"]), axis=1)
        lejos = max(lejos, float(d.min()))
        v3[int(g)] = veredictos_de(carpeta / "crudo" / f"polo_{int(puntos_v2.loc[d.idxmin(), 'polo'])}.json")
    if lejos > CERCA_KM:
        raise ValueError(f"un grupo v3 sin clima propio queda a {lejos:.1f} km del punto v2 más cercano")
    iguales = pares = cambian = 0
    cambios: dict[str, int] = {}
    en_las_dos = grupos[(grupos["grupo_v2"] >= 0) & (grupos["grupo_v3"] >= 0)]
    for g2, g3 in zip(en_las_dos["grupo_v2"], en_las_dos["grupo_v3"], strict=True):
        a, b = v2[int(g2)], v3[int(g3)]
        if a is None or b is None:
            continue
        distintos = [mes for mes in range(1, 13) if a[mes] != b[mes]]
        pares += 12
        iguales += 12 - len(distintos)
        cambian += bool(distintos)
        for mes in distintos:
            clave = f"{a[mes]} a {b[mes]}"
            cambios[clave] = cambios.get(clave, 0) + 1
    return {
        "grupos_v3": len(v3),
        "con_clima_propio": sum(g in propios for g in v3),
        "sin_clima": sum(v is None for v in v3.values()),
        "paradas_en_las_dos": len(en_las_dos),
        "pares_parada_mes": pares,
        "pares_con_el_mismo_veredicto": iguales,
        "paradas_con_algun_mes_distinto": cambian,
        "cambios": dict(sorted(cambios.items(), key=lambda x: -x[1])),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--clima", type=Path, default=CLIMA)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    grupos = pd.read_csv(GRUPOS, sep=";", dtype={"codigo": str})
    maestro = pd.read_csv(
        MAESTRO, sep=";", encoding="utf-8-sig", usecols=["codigo", "lat", "lon"], dtype={"codigo": str}
    )
    r = comparar(grupos.merge(maestro, on="codigo", how="left"), a.clima)
    a.salida.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"{r['grupos_v3']} grupos v3, {r['con_clima_propio']} con clima propio; de {r['pares_parada_mes']} pares "
        f"parada-mes, {r['pares_con_el_mismo_veredicto']} con el mismo veredicto; "
        f"{r['paradas_con_algun_mes_distinto']} de {r['paradas_en_las_dos']} paradas cambian algún mes."
    )


if __name__ == "__main__":
    main()

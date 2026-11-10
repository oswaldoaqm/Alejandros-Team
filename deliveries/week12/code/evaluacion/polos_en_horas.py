"""
TA-01 v3: los grupos de lugares con las horas de la red vial, y lo que cambia contra la v2 (semana 12).

La v2 de TA-01 (semana 6, ``deliveries/week06/ModelSelection.md``) agrupa los lugares por enlace completo sobre
una distancia en línea recta corregida por el desnivel, con un diámetro de 80 km efectivos que entonces se leían
como 3,9 horas de punta a punta: 1,6 de sinuosidad y 32,5 km/h, una fórmula que nunca se contrastó. Desde la
semana 7 el motor viaja por la red vial de OpenStreetMap, calibrada con 1 780 recorridos de las fichas
(decisiones 0007 y 0008). Aquí se miden los grupos con esa red, en dos partes:

1. **La v2 en horas**: el viaje más largo entre dos paradas de cada grupo, de puerta a puerta, con los minutos
   que usa el motor (``data/procesados/tiempos_polo.csv``).
2. **La v3**: el mismo enlace completo, ahora sobre esos minutos, con el diámetro máximo en horas. Una parada
   entra en un grupo solo si llega por la red a cada una de las otras en ese tiempo, así que ningún grupo de la
   v3 pasa de su umbral, por construcción. Como en la v2, un grupo de menos de cinco paradas no es un grupo, y
   ninguno junta paradas con más de 1 300 m de altura entre sí: la v2 lo lograba sumando el desnivel a su
   distancia, porque un grupo que va de 200 a 4 000 m le sirve a medias a quien declara una altura máxima, y aquí
   es una regla aparte. Sin esa regla, un grupo de cuatro horas puede ir de la costa a la puna; también se mide.

Para la v3, los minutos de puerta a puerta se calculan como en ``pipeline.tiempos``: el camino más rápido por la
red, lo que falta de cada punta a la red y los minutos fijos de cada traslado, ahora entre todas las paradas y
hasta el umbral más grande. Aquí se buscan en la red entera; ``pipeline.tiempos`` busca dentro del rectángulo de
cada polo, así que en algunos pares la red entera da un camino más corto. Esa diferencia se mide contra
``tiempos_polo.csv``, en los pares que trae.

Solo cuenta para el diámetro lo que es parada, como en el motor. Las que quedan a más de 5 km de la red no
tienen tiempos y no entran en ningún grupo.

Escribe en data/evaluacion/resultados/:

  polos_en_horas.json   la red, la comparación con los tiempos del motor, la v2 en horas, la v3 con cada
                        umbral y la comparación de la v3 elegida con la v2
  polos_v2_horas.csv    cada grupo de la v2: sus paradas, su diámetro en horas y si tiene paradas sin camino
                        entre sí
  polos_v3.csv          cada parada: su grupo de la v2 y el de la v3 con el umbral elegido (-1: ninguno)

Pide la red ya armada por ``python -m pipeline.tiempos`` en data/externos/osm/, que queda fuera de git: este
script no la rearma. Unos tres minutos, casi todos de calibrar la red como la calibra el pipeline.

Uso:  python -m evaluacion.polos_en_horas [--umbrales 180 240 300] [--elegido 240]
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import red_calibracion as calibracion
from pipeline.maestro import EXTERNOS, PROCESADOS
from pipeline.red_vial import Red, Ruteador, minutos_por_arista
from pipeline.tiempos import CACHE, LEJOS_DE_LA_RED_M, paradas_de, ritmos_fijos

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "evaluacion" / "resultados"
OSM = EXTERNOS / "osm"
UMBRALES = (180, 240, 300)  # minutos de punta a punta
ELEGIDO = 240  # cuatro horas: lo que la v2 prometía con su fórmula, 3,9 horas
PARADAS_MIN = 5  # como la v2: un grupo de menos no es un grupo
DESNIVEL_MAX = 1300  # metros entre la parada más baja y la más alta de un grupo: lo que buscaba la v2
LEJOS = 1e9  # minutos entre dos paradas sin camino: nunca quedan en el mismo grupo
FUENTES_POR_VUELTA = 32  # búsquedas a la vez: cada una ocupa una fila del tamaño de la red


# ── La red ──────────────────────────────────────────────────────────────────────────────────────────


def cargar_red(osm: Path = OSM) -> tuple[Red, pd.DataFrame, pd.DataFrame, dict]:
    """La red y las capitales y pueblos del extracto, del caché de ``pipeline.tiempos``."""
    manifiesto = json.loads((osm / "manifiesto.json").read_text(encoding="utf-8"))
    etiqueta = manifiesto["md5"][:8]
    archivos = {
        "red_vial": osm / f"red_vial_{etiqueta}_v{CACHE}.npz",
        "capitales": osm / f"capitales_{etiqueta}_v{CACHE}.csv",
        "lugares": osm / f"lugares_{etiqueta}_v{CACHE}.csv",
    }
    faltan = [str(r) for r in archivos.values() if not r.exists()]
    if faltan:
        raise SystemExit("Falta la red armada (corre primero python -m pipeline.tiempos): " + ", ".join(faltan))
    red = Red.cargar(archivos["red_vial"])
    return red, pd.read_csv(archivos["capitales"]), pd.read_csv(archivos["lugares"]), manifiesto


def ruteador_calibrado(red: Red, maestro: pd.DataFrame, capitales, lugares) -> tuple[Ruteador, dict]:
    """El ruteador con los parámetros que calibra ``pipeline.tiempos`` con las fichas."""
    pares, _ = calibracion.pares_de_calibracion(maestro, capitales, lugares)
    parametros, _ = calibracion.calibrar(red, pares)
    parametros = {**parametros, **ritmos_fijos()}
    return Ruteador(red, minutos_por_arista(red, parametros)), parametros


def minutos_entre_paradas(
    ruteador: Ruteador, parametros: dict, paradas: pd.DataFrame, limite: float
) -> tuple[np.ndarray, np.ndarray]:
    """(minutos, lejos). Los minutos de puerta a puerta entre cada par de paradas, como ``pipeline.tiempos``:
    ``inf`` si no hay camino, si una punta queda lejos de la red o si pasa de ``limite``; de las dos direcciones,
    la más larga. ``lejos`` marca las paradas a más de 5 km de la red."""
    from scipy.sparse.csgraph import dijkstra

    v, m, capa = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy(), paradas["acceso"].to_numpy())
    lejos = m > LEJOS_DE_LA_RED_M
    en_capa = (capa > 0).astype(np.float64)
    # Lo de cada punta, como en ``tiempos._puerta_a_puerta``: lo que falta hasta la red, por un camino sin mapear,
    # y bajarse del tren o del bote. Los minutos fijos del traslado van una vez por par.
    fuera_km = 1.3 * m / 1000
    puntas = fuera_km * parametros["trocha"] + en_capa * parametros.get("transbordo_min", 0.0)
    n = len(paradas)
    minutos = np.full((n, n), np.inf, dtype=np.float32)
    cerca = np.flatnonzero(~lejos)
    for inicio in range(0, len(cerca), FUENTES_POR_VUELTA):
        fuentes = cerca[inicio : inicio + FUENTES_POR_VUELTA]
        en_red = dijkstra(ruteador.grafo, directed=True, indices=v[fuentes], limit=limite)[:, v[cerca]]
        minutos[np.ix_(fuentes, cerca)] = en_red + parametros["por_viaje"] + puntas[fuentes][:, None] + puntas[cerca]
    minutos = np.maximum(minutos, minutos.T)
    minutos[minutos > limite] = np.inf
    np.fill_diagonal(minutos, 0.0)
    return minutos, lejos


# ── Las dos partes ──────────────────────────────────────────────────────────────────────────────────


def diametros_del_motor(tiempos_polo: pd.DataFrame, grupo_de: pd.Series) -> pd.DataFrame:
    """Lo mismo que ``diametros``, con los minutos de ``tiempos_polo.csv``: por grupo de TA-01 (``grupo_de``, el
    grupo de cada código de parada; -1 si no tiene), entre los pares de sus paradas. El archivo trae cada par en
    los dos sentidos, y vacío si no hay camino."""
    t = tiempos_polo.assign(g=tiempos_polo["desde"].map(grupo_de), g2=tiempos_polo["hasta"].map(grupo_de))
    t = t[(t["g"] == t["g2"]) & (t["g"] >= 0)]
    por_grupo = t.groupby("g")["minutos"]
    paradas = grupo_de[grupo_de >= 0].value_counts().sort_index()
    tabla = pd.DataFrame(
        {
            "grupo": paradas.index.astype(int),
            "paradas": paradas.to_numpy(int),
            "diametro_min": por_grupo.max().reindex(paradas.index).fillna(0.0).to_numpy(float),
            "pares_sin_camino": (por_grupo.apply(lambda m: int(m.isna().sum())) // 2)
            .reindex(paradas.index)
            .fillna(0)
            .to_numpy(int),
        }
    )
    return tabla


def diametros(minutos: np.ndarray, grupo: np.ndarray) -> pd.DataFrame:
    """Por grupo (``grupo`` ≥ 0): cuántas paradas tiene, su diámetro en minutos entre las que tienen camino
    y cuántos pares de sus paradas no tienen camino (o pasan del límite con que se buscó)."""
    filas = []
    for g in np.unique(grupo[grupo >= 0]):
        i = np.flatnonzero(grupo == g)
        sub = minutos[np.ix_(i, i)][np.triu_indices(len(i), 1)]
        con = np.isfinite(sub)
        filas.append(
            {
                "grupo": int(g),
                "paradas": len(i),
                "diametro_min": float(sub[con].max()) if con.any() else 0.0,
                "pares_sin_camino": int((~con).sum()),
            }
        )
    return pd.DataFrame(filas, columns=["grupo", "paradas", "diametro_min", "pares_sin_camino"])


def agrupar(
    minutos: np.ndarray,
    umbral: float,
    paradas_min: int = PARADAS_MIN,
    altitud: np.ndarray | None = None,
    desnivel_max: float | None = None,
) -> np.ndarray:
    """Enlace completo con diámetro máximo ``umbral``: el grupo de cada parada, o -1 si cae en uno de menos de
    ``paradas_min``. Con ``altitud`` y ``desnivel_max``, dos paradas a más de ese desnivel no quedan juntas (si a
    una le falta la altura, cuenta solo el tiempo, como en la v2). Los grupos van del más grande al más chico."""
    from scipy.cluster.hierarchy import fcluster, linkage
    from scipy.spatial.distance import squareform

    d = np.where(np.isfinite(minutos), minutos, LEJOS).astype(np.float64)
    if altitud is not None and desnivel_max is not None:
        with np.errstate(invalid="ignore"):
            d[np.abs(altitud[:, None] - altitud[None, :]) > desnivel_max] = LEJOS
    np.fill_diagonal(d, 0.0)
    if len(d) < 2:
        return np.full(len(d), -1, dtype=int)
    etiqueta = fcluster(linkage(squareform(d, checks=False), method="complete"), t=umbral, criterion="distance")
    tamano = pd.Series(etiqueta).value_counts()
    orden = [e for e in sorted(tamano.index, key=lambda e: (-tamano[e], e)) if tamano[e] >= paradas_min]
    nuevo = {e: k for k, e in enumerate(orden)}
    return np.array([nuevo.get(e, -1) for e in etiqueta], dtype=int)


def resumen_de_grupos(tabla: pd.DataFrame, total: int, altitud: np.ndarray, grupo: np.ndarray) -> dict:
    """Cuántos grupos, cuántas paradas cubren, cuánto miden en horas y cuánto suben de su parada más baja a la
    más alta."""
    horas = tabla["diametro_min"].to_numpy() / 60
    desnivel = []
    for g in tabla["grupo"]:
        alturas = altitud[grupo == g]
        if np.isfinite(alturas).any():
            desnivel.append(float(np.nanmax(alturas) - np.nanmin(alturas)))

    def cuantil(x, q):
        return round(float(np.quantile(x, q)), 2) if len(x) else None

    return {
        "grupos": len(tabla),
        "paradas": int(tabla["paradas"].sum()),
        "cobertura": round(float(tabla["paradas"].sum()) / total, 4),
        "paradas_por_grupo_mediana": cuantil(tabla["paradas"].to_numpy(), 0.5),
        "diametro_h": {"mediana": cuantil(horas, 0.5), "p90": cuantil(horas, 0.9), "maximo": cuantil(horas, 1)},
        "desnivel_m": {"mediana": cuantil(desnivel, 0.5), "maximo": cuantil(desnivel, 1)},
        "con_pares_sin_camino": int((tabla["pares_sin_camino"] > 0).sum()),
    }


def comparar(v2: np.ndarray, v3: np.ndarray) -> dict:
    """Cuánto se parecen dos particiones de las mismas paradas, entre las que están en un grupo en las dos."""
    from sklearn.metrics import adjusted_rand_score

    en_las_dos = (v2 >= 0) & (v3 >= 0)
    a, b = v2[en_las_dos], v3[en_las_dos]
    juntas_v2 = juntas_las_dos = juntas_v3 = 0
    for g in np.unique(a):
        i = np.flatnonzero(a == g)
        juntas_v2 += len(i) * (len(i) - 1) // 2
        _, cuantas = np.unique(b[i], return_counts=True)
        juntas_las_dos += int((cuantas * (cuantas - 1) // 2).sum())
    for g in np.unique(b):
        k = int((b == g).sum())
        juntas_v3 += k * (k - 1) // 2
    # Un grupo de la v2 se parte si sus paradas quedan en dos o más de la v3; uno de la v3 junta si recibe de dos
    # o más de la v2.
    partidos = sum(len(np.unique(b[a == g])) > 1 for g in np.unique(a))
    juntan = sum(len(np.unique(a[b == g])) > 1 for g in np.unique(b))
    return {
        "paradas_en_las_dos": int(en_las_dos.sum()),
        "ari": round(float(adjusted_rand_score(a, b)), 3),
        "pares_juntos_en_la_v2_que_siguen_juntos": round(juntas_las_dos / juntas_v2, 3) if juntas_v2 else None,
        "pares_juntos_en_la_v3_que_ya_lo_estaban": round(juntas_las_dos / juntas_v3, 3) if juntas_v3 else None,
        "grupos_de_la_v2_que_se_parten": int(partidos),
        "grupos_de_la_v3_que_juntan_dos_o_mas": int(juntan),
        "en_la_v2_y_sin_grupo_en_la_v3": int(((v2 >= 0) & (v3 < 0)).sum()),
        "sin_grupo_en_la_v2_y_en_la_v3": int(((v2 < 0) & (v3 >= 0)).sum()),
    }


def contra_el_motor(minutos: np.ndarray, paradas: pd.DataFrame, tiempos_polo: pd.DataFrame) -> dict:
    """Los minutos de aquí contra los de ``tiempos_polo.csv``, en los pares que trae ese archivo."""
    fila = pd.Series(np.arange(len(paradas)), index=paradas["codigo"].to_numpy())
    t = tiempos_polo.dropna(subset=["minutos"])
    t = t[t["desde"].isin(fila.index) & t["hasta"].isin(fila.index)]
    aqui = minutos[fila.loc[t["desde"]].to_numpy(), fila.loc[t["hasta"]].to_numpy()].astype(np.float64)
    motor = t["minutos"].to_numpy(float)
    con = np.isfinite(aqui)
    diferencia = aqui[con] - motor[con]
    return {
        "pares": len(t),
        "con_camino_aqui": int(con.sum()),
        "a_menos_de_un_minuto": round(float(np.mean(np.abs(diferencia) < 1.0)), 4),
        "mas_cortos_aqui_por_mas_de_5_min": int((diferencia < -5).sum()),
        "diferencia_mediana_min": round(float(np.median(diferencia)), 2),
    }


# ── Todo junto ──────────────────────────────────────────────────────────────────────────────────────


def medir(maestro, minutos, lejos, paradas: pd.DataFrame, tiempos_polo: pd.DataFrame, umbrales, elegido) -> tuple:
    """(resumen, tabla de la v2 en horas, tabla de cada parada con su grupo de la v2 y de la v3)."""
    v2 = paradas["polo"].to_numpy(int)
    altitud = paradas["codigo"].map(maestro.set_index("codigo")["altitud_m"]).to_numpy(float)
    tabla_v2 = diametros_del_motor(tiempos_polo, paradas.set_index("codigo")["polo"])
    horas_v2 = tabla_v2["diametro_min"].to_numpy() / 60
    resumen = {
        "paradas": len(paradas),
        "lejos_de_la_red": int(lejos.sum()),
        "v2": {
            **resumen_de_grupos(tabla_v2, len(paradas), altitud, v2),
            "pasan_de": {f"{h}_h": int((horas_v2 > h).sum()) for h in (3, 4, 5, 6, 8)},
        },
        "v3": {},
    }
    por_parada = None
    for umbral in umbrales:
        v3 = agrupar(minutos, umbral, altitud=altitud, desnivel_max=DESNIVEL_MAX)
        resumen["v3"][str(umbral)] = resumen_de_grupos(diametros(minutos, v3), len(paradas), altitud, v3)
        if umbral == elegido:
            resumen["elegido"] = {"umbral_min": umbral, "desnivel_max_m": DESNIVEL_MAX, **comparar(v2, v3)}
            por_parada = pd.DataFrame({"codigo": paradas["codigo"], "grupo_v2": v2, "grupo_v3": v3})
    sin_tope = agrupar(minutos, elegido)
    resumen["v3_sin_tope_de_desnivel"] = {
        str(elegido): resumen_de_grupos(diametros(minutos, sin_tope), len(paradas), altitud, sin_tope)
    }
    return resumen, tabla_v2, por_parada


def main() -> None:
    ap = argparse.ArgumentParser(description="TA-01 v3: los grupos con las horas de la red vial.")
    ap.add_argument("--umbrales", type=int, nargs="+", default=list(UMBRALES), help="minutos de punta a punta")
    ap.add_argument("--elegido", type=int, default=ELEGIDO)
    ap.add_argument("--osm", type=Path, default=OSM)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    if a.elegido not in a.umbrales:
        raise SystemExit("--elegido tiene que estar entre los --umbrales")
    inicio = time.time()
    maestro = pd.read_csv(PROCESADOS / "maestro_v3.csv", sep=";", encoding="utf-8-sig", dtype={"dias": str})
    red, capitales, lugares, manifiesto = cargar_red(a.osm)
    ruteador, parametros = ruteador_calibrado(red, maestro, capitales, lugares)
    paradas = paradas_de(maestro)
    minutos, lejos = minutos_entre_paradas(ruteador, parametros, paradas, limite=max(a.umbrales))
    tiempos_polo = pd.read_csv(PROCESADOS / "tiempos_polo.csv", sep=";", encoding="utf-8-sig")
    resumen, tabla_v2, por_parada = medir(maestro, minutos, lejos, paradas, tiempos_polo, a.umbrales, a.elegido)
    resumen = {
        "osm": {"md5": manifiesto["md5"], "datos": manifiesto.get("datos_last_modified")},
        "contra_los_tiempos_del_motor": contra_el_motor(minutos, paradas, tiempos_polo),
        **resumen,
    }
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "polos_en_horas.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    tabla_v2 = tabla_v2.assign(diametro_h=(tabla_v2["diametro_min"] / 60).round(2))
    tabla_v2["diametro_min"] = tabla_v2["diametro_min"].round(1)
    columnas = ["grupo", "paradas", "diametro_min", "diametro_h", "pares_sin_camino"]
    tabla_v2[columnas].to_csv(a.salida / "polos_v2_horas.csv", sep=";", index=False, quoting=csv.QUOTE_MINIMAL)
    por_parada.to_csv(a.salida / "polos_v3.csv", sep=";", index=False)
    v2, v3 = resumen["v2"], resumen["v3"][str(a.elegido)]
    print(
        f"v2: {v2['grupos']} grupos, diámetro mediano {v2['diametro_h']['mediana']} h y máximo"
        f" {v2['diametro_h']['maximo']} h; {v2['pasan_de']['4_h']} pasan de 4 h."
        f" v3 con {a.elegido} min: {v3['grupos']} grupos, {v3['cobertura']:.1%} de las paradas."
        f" ARI {resumen['elegido']['ari']}. En {time.time() - inicio:.0f} s."
    )


if __name__ == "__main__":
    main()

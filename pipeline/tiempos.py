"""
Tiempos de viaje por carretera que usa el motor, sobre la red vial de OpenStreetMap.

1. Arma la red desde el extracto de Geofabrik (``pipeline/red_vial.py``) o la toma del
   caché si el extracto no cambió.
2. Calibra las velocidades con los recorridos de las fichas (``pipeline/red_calibracion.py``).
3. Calcula, con la red calibrada:
   - de cada una de las 24 ciudades de origen a cada parada posible;
   - entre las paradas de cada polo, en los dos sentidos.

Cada tiempo es de puerta a puerta en auto o bus: el camino por la red, lo que falta de la
parada a la vía más cercana y los minutos fijos de cada traslado. La caminata final que
registra la ficha (``caminata_min`` del maestro) va aparte.

Escribe en data/procesados/:
  red_calibracion.json             parámetros y error medido por validación cruzada
  red_calibracion_recorridos.csv   cada recorrido de ficha usado, con el tiempo de la red
  tiempos_origen.csv               origen → parada: minutos y km (vacío si no hay carretera)
  tiempos_polo.csv                 parada → parada dentro de cada polo
  red_paradas.csv                  a cuántos metros de la red queda cada parada

Todo lo que sale de la red es obra derivada de OpenStreetMap: ODbL 1.0, © colaboradores de
OpenStreetMap.

Uso:  python -m pipeline.tiempos                    (después de python -m pipeline.maestro)
      python -m pipeline.tiempos --indice "sparse_file_array,nodos.idx"   con poca memoria
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import red_calibracion as calibracion
from pipeline.maestro import EXTERNOS, PROCESADOS, REFERENCIA
from pipeline.red_vial import Red, Ruteador, leer_capitales, leer_lugares, leer_red, minutos_por_arista

OSM = EXTERNOS / "osm"
LEJOS_DE_LA_RED_M = 5_000  # una parada más lejos que esto de cualquier vía no se rutea


def red_en_cache(pbf: Path, indice: str) -> tuple[Red, pd.DataFrame, pd.DataFrame, dict]:
    """La red, las capitales y los pueblos del extracto; se rehacen si cambia su MD5."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    etiqueta = manifiesto["md5"][:8]
    rutas = {
        n: pbf.parent / f"{n}_{etiqueta}.{e}"
        for n, e in (("red_vial", "npz"), ("capitales", "csv"), ("lugares", "csv"))
    }
    if not all(r.exists() for r in rutas.values()):
        inicio = time.time()
        red = leer_red(pbf, indice)
        red.fecha_osm = manifiesto["datos_last_modified"]
        red.guardar(rutas["red_vial"])
        leer_capitales(pbf).to_csv(rutas["capitales"], index=False)
        leer_lugares(pbf).to_csv(rutas["lugares"], index=False)
        print(f"Red armada en {time.time() - inicio:.0f} s: {red.vertices:,} vértices, {red.aristas:,} aristas")
    red = Red.cargar(rutas["red_vial"])
    return red, pd.read_csv(rutas["capitales"]), pd.read_csv(rutas["lugares"]), manifiesto


def _puerta_a_puerta(minutos, km, metros_a_la_red, parametros) -> tuple[np.ndarray, np.ndarray]:
    """Suma a cada camino lo que falta de cada punta a la vía y los minutos fijos del traslado."""
    fuera_km = 1.3 * metros_a_la_red / 1000  # por un camino sin mapear, como en la calibración
    minutos = minutos + parametros["por_viaje"] + fuera_km * parametros["trocha"]
    return minutos, km + fuera_km


def tiempos_desde_origenes(ruteador, parametros, origenes, paradas) -> pd.DataFrame:
    v_origen, m_origen = ruteador.ubicar(origenes["lat"].to_numpy(), origenes["lon"].to_numpy())
    v_parada, m_parada = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy())
    minutos, km = ruteador.entre(v_origen, v_parada, margen=None)
    filas = []
    for i, origen in enumerate(origenes["id"]):
        m, k = _puerta_a_puerta(minutos[i], km[i], m_origen[i] + m_parada, parametros)
        filas.append(pd.DataFrame({"origen": origen, "codigo": paradas["codigo"].to_numpy(), "minutos": m, "km": k}))
    tabla = pd.concat(filas, ignore_index=True)
    lejos = np.tile(m_parada > LEJOS_DE_LA_RED_M, len(origenes))
    tabla.loc[lejos | ~np.isfinite(tabla["minutos"].to_numpy()), ["minutos", "km"]] = np.nan
    return tabla


def tiempos_en_polos(ruteador, parametros, paradas) -> pd.DataFrame:
    v, m = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy())
    paradas = paradas.assign(_v=v, _m=m)
    filas = []
    for polo, grupo in paradas[paradas["polo"] >= 0].groupby("polo"):
        if len(grupo) < 2:
            continue
        minutos, km = ruteador.entre(grupo["_v"].to_numpy(), grupo["_v"].to_numpy())
        extra = grupo["_m"].to_numpy()
        for i, desde in enumerate(grupo["codigo"].to_numpy()):
            mi, ki = _puerta_a_puerta(minutos[i], km[i], extra[i] + extra, parametros)
            otros = np.arange(len(grupo)) != i
            filas.append(
                pd.DataFrame(
                    {
                        "polo": polo,
                        "desde": desde,
                        "hasta": grupo["codigo"].to_numpy()[otros],
                        "minutos": mi[otros],
                        "km": ki[otros],
                    }
                )
            )
    tabla = pd.concat(filas, ignore_index=True)
    lejos = set(paradas.loc[paradas["_m"] > LEJOS_DE_LA_RED_M, "codigo"])
    sin_ruta = tabla["desde"].isin(lejos) | tabla["hasta"].isin(lejos) | ~np.isfinite(tabla["minutos"].to_numpy())
    tabla.loc[sin_ruta, ["minutos", "km"]] = np.nan
    return tabla


def _escribir(tabla: pd.DataFrame, ruta: Path) -> None:
    tabla.to_csv(ruta, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n", float_format="%.1f")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibra la red vial y calcula los tiempos de viaje por carretera.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--maestro", type=Path, default=PROCESADOS / "maestro_v3.csv")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem", help="dónde guarda pyosmium los nodos al leer (ver leer_red)")
    a = ap.parse_args()

    red, capitales, lugares, manifiesto = red_en_cache(a.pbf, a.indice)
    maestro = pd.read_csv(a.maestro, sep=";", encoding="utf-8-sig", dtype={"dias": str})

    pares, cuentas = calibracion.pares_de_calibracion(maestro, capitales, lugares)
    parametros, recorridos = calibracion.calibrar(red, pares)
    informe = calibracion.informe(recorridos, parametros, cuentas)
    informe = {"osm": {"datos": manifiesto["datos_last_modified"], "md5": manifiesto["md5"]}, **informe}
    (a.salida / "red_calibracion.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    recorridos = recorridos.assign(
        minutos_red=calibracion.predecir(recorridos, parametros), misma_distancia=calibracion.coinciden(recorridos)
    )
    _escribir(
        recorridos[
            [
                "codigo",
                "acceso_desde",
                "acceso_km",
                "acceso_min",
                "ultimo_medio",
                "km_red",
                "minutos_red",
                "misma_distancia",
            ]
        ].rename(columns={"acceso_km": "km_ficha", "acceso_min": "minutos_ficha"}),
        a.salida / "red_calibracion_recorridos.csv",
    )
    cv = informe["validacion_cruzada"]
    error = f"error medio {cv['error_medio']:.0%}, mediano {cv['error_mediano']:.0%}"
    print(f"Calibración con {cv['recorridos']} recorridos de fichas · {error} (validación cruzada)")

    ruteador = Ruteador(red, minutos_por_arista(red, parametros))
    paradas = maestro.loc[maestro["es_parada"].astype(bool), ["codigo", "polo", "lat", "lon"]].reset_index(drop=True)
    origenes = pd.read_csv(REFERENCIA / "origenes.csv", sep=";")
    _escribir(tiempos_desde_origenes(ruteador, parametros, origenes, paradas), a.salida / "tiempos_origen.csv")
    _escribir(tiempos_en_polos(ruteador, parametros, paradas), a.salida / "tiempos_polo.csv")
    _, metros = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy())
    _escribir(
        paradas[["codigo", "polo"]].assign(
            metros_a_la_red=np.round(metros).astype(int), lejos_de_la_red=metros > LEJOS_DE_LA_RED_M
        ),
        a.salida / "red_paradas.csv",
    )
    print(f"Escrito en {a.salida}")


if __name__ == "__main__":
    main()

"""
El terminal de bus en cada punta de la ida por tierra (decisión 0030).

La ida en bus va de terminal a terminal: los ritmos del bus se ajustaron con los horarios de Cruz
del Sur, que son de terminal a terminal (decisión 0026). Lo que faltaba es llegar al terminal y
salir de él:

1. el taxi del centro de la ciudad de origen al terminal más cercano, por la misma red y con el
   tráfico de la ciudad (decisión 0025);
2. media hora antes de la salida, la que piden las empresas para embarcar;
3. el taxi del terminal más cercano a la base hasta la base. Si no hay un terminal a menos de
   ``BASE_TERMINAL_KM`` de la base, el bus deja en el pueblo y no se suma nada.

Los terminales salen de las estaciones de bus de OpenStreetMap (``amenity=bus_station``, o
``public_transport=station`` con ``bus=yes``), sin las de transporte urbano. En cada punta se elige el
terminal terrestre más cercano; si no hay, el más cercano que se llame terminal, y si no, el de una empresa.
Una ciudad de origen sin terminal a menos de ``ORIGEN_TERMINAL_KM`` de su centro no suma taxi. Todo esto
solo cuenta en una ida de ``IDA_EN_BUS_MIN`` o más: en las cortas se va en colectivo o en auto.

Escribe en data/procesados/:
  terminales.csv   para cada origen y cada base: el terminal, a cuántos km queda y los minutos del
                   taxi, puerta a puerta

Lo que sale de la red es obra derivada de OpenStreetMap: ODbL 1.0, © colaboradores de OpenStreetMap.

Uso:  python -m pipeline.terminales       (después de python -m pipeline.tiempos)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import red_calibracion as calibracion
from pipeline.maestro import PROCESADOS, REFERENCIA, haversine_km
from pipeline.red_vial import Ruteador, minutos_por_arista
from pipeline.tiempos import OSM, red_en_cache, ritmos_fijos
from pipeline.vuelos import por_tierra

CACHE = 1
ORIGEN_TERMINAL_KM = 15.0  # del centro de la ciudad de origen
BASE_TERMINAL_KM = 3.0  # de la base: más lejos, el bus deja en el pueblo
EMBARQUE_MIN = 30  # lo que piden las empresas antes de la salida
BASE_TAXI_MAX_MIN = 30  # si el taxi del terminal a la base pasa de esto, el bus deja en el pueblo
IDA_EN_BUS_MIN = 180  # desde aquí la ida es un bus interprovincial, que sale de un terminal
# Lo que OSM marca como estación de bus y no es un terminal interprovincial: el Metropolitano y los
# corredores de Lima, y los paraderos de colectivos, combis y mototaxis.
NO_ES_TERMINAL = re.compile(
    r"metropolitano|corredor|colectivo|collectivo|combi|paradero|mototaxi|hacia el|tren|aeropuerto|naranjal", re.I
)


def es_terminal(nombre: str) -> bool:
    """Un terminal con nombre que no es de transporte urbano."""
    return bool(nombre.strip()) and not NO_ES_TERMINAL.search(nombre)


def leer_osm(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """Las estaciones de bus de OSM: el nodo, o el promedio de los nodos del contorno."""
    import osmium

    filas = []
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.TagFilter(("amenity", "bus_station"), ("public_transport", "station")))
    )
    for objeto in procesador:
        etiquetas = dict(objeto.tags)
        if etiquetas.get("amenity") != "bus_station" and etiquetas.get("bus") != "yes":
            continue
        if objeto.is_node():
            if not objeto.location.valid():
                continue
            lat, lon = objeto.location.lat, objeto.location.lon
        else:
            puntos = [(nd.lat, nd.lon) for nd in objeto.nodes if nd.location.valid()]
            if len(puntos) > 1 and puntos[0] == puntos[-1]:
                puntos = puntos[:-1]
            if not puntos:
                continue
            lat, lon = (float(x) for x in np.mean(puntos, axis=0))
        tipo = "node" if objeto.is_node() else "way"
        filas.append((f"{tipo}/{objeto.id}", etiquetas.get("name", ""), lat, lon))
    return pd.DataFrame(filas, columns=["osm", "nombre", "lat", "lon"])


def osm_en_cache(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """``leer_osm``, guardado junto al extracto: se rehace si cambia su MD5."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    ruta = pbf.parent / f"terminales_{manifiesto['md5'][:8]}_v{CACHE}.csv"
    if not ruta.exists():
        leer_osm(pbf, indice).to_csv(ruta, index=False)
    return pd.read_csv(ruta, keep_default_na=False)


def mas_cercano(puntos: pd.DataFrame, terminales: pd.DataFrame, max_km: float) -> pd.DataFrame:
    """Para cada punto, su terminal a menos de ``max_km`` en línea recta: el terminal terrestre más cercano si hay
    uno, si no el más cercano que se llame terminal, y si no, el más cercano de una empresa. Las estaciones de
    transporte urbano no cuentan (``es_terminal``)."""
    terminales = terminales[terminales["nombre"].map(es_terminal)].reset_index(drop=True)
    nombres = terminales["nombre"].str.lower()
    rango = np.where(nombres.str.contains("terminal terrestre"), 0, np.where(nombres.str.contains("terminal"), 1, 2))
    filas = []
    for p in puntos.itertuples():
        km = np.asarray(haversine_km(p.lat, p.lon, terminales["lat"].to_numpy(), terminales["lon"].to_numpy()))
        cerca = np.flatnonzero(km <= max_km)
        if len(cerca) == 0:
            continue
        k = int(cerca[np.lexsort((km[cerca], rango[cerca]))[0]])
        t = terminales.iloc[k]
        filas.append({"id": p.id, "terminal": t["nombre"], "osm": t["osm"], "lat": t["lat"], "lon": t["lon"]})
    return pd.DataFrame(filas, columns=["id", "terminal", "osm", "lat", "lon"])


def en_taxi(ruteador: Ruteador, parametros: dict, puntos: pd.DataFrame, terminales: pd.DataFrame) -> pd.DataFrame:
    """Los minutos y km de cada punto a su terminal, por la red."""
    pares = puntos.merge(terminales, on="id", suffixes=("", "_terminal"))
    minutos, km = [], []
    for p in pares.itertuples():
        desde = pd.DataFrame({"lat": [p.lat], "lon": [p.lon]})
        hasta = pd.DataFrame({"lat": [p.lat_terminal], "lon": [p.lon_terminal]})
        t = por_tierra(ruteador, parametros, desde, hasta)
        minutos.append(float(t["minutos"][0, 0]))
        km.append(float(t["km"][0, 0]))
    return pares.assign(minutos=np.round(minutos, 1), km=np.round(km, 2))[
        ["id", "terminal", "osm", "lat_terminal", "lon_terminal", "minutos", "km"]
    ]


def sumar_terminales(tiempos_origen_base: pd.DataFrame, terminales: pd.DataFrame) -> pd.DataFrame:
    """La ida en bus con los terminales: a cada ida de ``IDA_EN_BUS_MIN`` o más le suma el taxi al terminal del
    origen, el embarque y el taxi del terminal a la base, en minutos y en km. Una base sin terminal cerca, o con
    uno a más de ``BASE_TAXI_MAX_MIN`` en taxi, no suma ese último tramo."""
    origen = terminales[terminales["punta"] == "origen"].set_index("id")
    base = terminales[(terminales["punta"] == "base") & (terminales["minutos"] <= BASE_TAXI_MAX_MIN)]
    base = base.assign(id=base["id"].astype(int)).set_index("id")
    t = tiempos_origen_base.copy()
    larga = t["minutos"] >= IDA_EN_BUS_MIN
    mas_min = t["origen"].map(origen["minutos"]).fillna(0) + EMBARQUE_MIN + t["polo"].map(base["minutos"]).fillna(0)
    mas_km = t["origen"].map(origen["km"]).fillna(0) + t["polo"].map(base["km"]).fillna(0)
    t.loc[larga, "minutos"] = (t.loc[larga, "minutos"] + mas_min[larga]).round(1)
    t.loc[larga, "km"] = (t.loc[larga, "km"] + mas_km[larga]).round(2)
    return t


def main() -> None:
    ap = argparse.ArgumentParser(description="El terminal de bus de cada origen y de cada base, y el taxi hasta él.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--maestro", type=Path, default=PROCESADOS / "maestro_v3.csv")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem", help="dónde guarda pyosmium los nodos al leer (ver leer_red)")
    a = ap.parse_args()

    red, osm, _ = red_en_cache(a.pbf, a.indice)
    maestro = pd.read_csv(a.maestro, sep=";", encoding="utf-8-sig", dtype={"dias": str})
    pares, _ = calibracion.pares_de_calibracion(maestro, osm.capitales, osm.lugares)
    parametros, _ = calibracion.calibrar(red, pares)
    parametros = {**parametros, **ritmos_fijos()}
    ruteador = Ruteador(red, minutos_por_arista(red, parametros))

    terminales = osm_en_cache(a.pbf, a.indice)
    origenes = pd.read_csv(REFERENCIA / "origenes.csv", sep=";")[["id", "lat", "lon"]]
    bases = pd.read_csv(a.salida / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    bases = bases.rename(columns={"polo": "id"})[["id", "lat", "lon"]]
    salida = pd.concat(
        [
            en_taxi(ruteador, parametros, origenes, mas_cercano(origenes, terminales, ORIGEN_TERMINAL_KM)).assign(
                punta="origen"
            ),
            en_taxi(ruteador, parametros, bases, mas_cercano(bases, terminales, BASE_TERMINAL_KM)).assign(punta="base"),
        ]
    )
    salida = salida[["punta", "id", "terminal", "osm", "lat_terminal", "lon_terminal", "minutos", "km"]]
    salida.to_csv(a.salida / "terminales.csv", sep=";", index=False, encoding="utf-8-sig")
    print(
        f"{len(terminales)} terminales en OSM · {int((salida.punta == 'origen').sum())} de {len(origenes)} orígenes "
        f"y {int((salida.punta == 'base').sum())} de {len(bases)} bases con uno cerca · escrito en {a.salida}"
    )


if __name__ == "__main__":
    main()

"""
Dónde dormir: los hospedajes con nombre más cercanos a la base de cada polo (decisión 0032).

De OpenStreetMap salen los hospedajes con nombre (``tourism`` = hotel, hostel, guest_house, motel o
apartment). Para cada base van hasta ``POR_BASE``, los más cercanos a menos de ``RADIO_KM`` en línea
recta. No hay precio ni categoría oficial: OSM no los trae de forma pareja, y cruzar el directorio de
prestadores de MINCETUR queda para después. Tampoco hay una fuente por distrito de qué tan seguro es.
Lo que se muestra es lo que existe cerca, para buscarlo. Si quien lo mapeó puso en el nombre un celular, un
correo o una web, el nombre se corta ahí: nada de contacto llega a los artefactos.

Escribe en data/procesados/:
  hospedajes_cerca.csv   polo, nombre, tipo, km a la base, lat, lon y el objeto de OSM

Lo que sale de OSM es obra derivada de OpenStreetMap: ODbL 1.0, © colaboradores de OpenStreetMap.

Uso:  python -m pipeline.hospedajes   (después de python -m pipeline.polos, unos 3 minutos con el extracto)
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.maestro import PROCESADOS, haversine_km
from pipeline.tiempos import OSM

CACHE = 1
TIPOS = {
    "hotel": "hotel",
    "hostel": "albergue",
    "guest_house": "hospedaje",
    "motel": "motel",
    "apartment": "departamento",
}
RADIO_KM = 2.0
POR_BASE = 3
# Desde donde empieza un contacto en el nombre: «Cel», «Telf.», WhatsApp, un +51, seis cifras seguidas, un
# correo o una web. Todo lo que sigue se descarta.
CONTACTO = re.compile(
    r"(?i)\b(cel|cell|celular|telf?|tel[eé]fono|fono|whats ?app|wsp|m[oó]vil)\b\.?|\+?51[\s-]?9\d|\d{6,}"
    r"|[\w.+-]+@[\w-]+\.\w+|https?://|www\."
)


def sin_contacto(nombre: str) -> str:
    """El nombre hasta donde empieza un contacto, sin la puntuación que quede al final."""
    corte = CONTACTO.search(nombre)
    return (nombre[: corte.start()] if corte else nombre).rstrip(" ,;:-/|(").strip()


def leer_osm(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """Los hospedajes con nombre de OSM: el nodo, o el promedio de los nodos del contorno."""
    import osmium

    filas = []
    procesador = (
        osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
        .with_locations(indice)
        .with_filter(osmium.filter.TagFilter(*(("tourism", t) for t in TIPOS)))
    )
    for objeto in procesador:
        etiquetas = dict(objeto.tags)
        nombre = etiquetas.get("name", "").strip()
        if not nombre:
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
        filas.append((f"{tipo}/{objeto.id}", nombre, TIPOS[etiquetas["tourism"]], lat, lon))
    return pd.DataFrame(filas, columns=["osm", "nombre", "tipo", "lat", "lon"])


def osm_en_cache(pbf: Path, indice: str = "flex_mem") -> pd.DataFrame:
    """``leer_osm``, guardado junto al extracto: se rehace si cambia su MD5."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    ruta = pbf.parent / f"hospedajes_con_nombre_{manifiesto['md5'][:8]}_v{CACHE}.csv"
    if not ruta.exists():
        leer_osm(pbf, indice).to_csv(ruta, index=False)
    return pd.read_csv(ruta, keep_default_na=False)


def cerca(bases: pd.DataFrame, hospedajes: pd.DataFrame, radio_km: float = RADIO_KM, cuantos: int = POR_BASE):
    """Para cada base, hasta ``cuantos`` hospedajes a menos de ``radio_km``, del más cercano al más lejano. Si dos
    se llaman igual, va el más cercano."""
    filas = []
    for b in bases.itertuples():
        km = np.asarray(haversine_km(b.lat, b.lon, hospedajes["lat"].to_numpy(), hospedajes["lon"].to_numpy()))
        orden = [int(i) for i in np.argsort(km, kind="stable") if km[i] <= radio_km]
        vistos: set[str] = set()
        for i in orden:
            h = hospedajes.iloc[i]
            nombre = sin_contacto(h["nombre"])
            clave = nombre.casefold()
            if not nombre or clave in vistos:
                continue
            vistos.add(clave)
            filas.append(
                {
                    "polo": b.polo,
                    "nombre": nombre,
                    "tipo": h["tipo"],
                    "km": round(float(km[i]), 2),
                    "lat": round(float(h["lat"]), 6),
                    "lon": round(float(h["lon"]), 6),
                    "osm": h["osm"],
                }
            )
            if len(vistos) == cuantos:
                break
    return pd.DataFrame(filas, columns=["polo", "nombre", "tipo", "km", "lat", "lon", "osm"])


def main() -> None:
    ap = argparse.ArgumentParser(description="Los hospedajes con nombre más cercanos a cada base.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem", help="dónde guarda pyosmium los nodos al leer (ver leer_red)")
    a = ap.parse_args()
    bases = pd.read_csv(a.salida / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    hospedajes = osm_en_cache(a.pbf, a.indice)
    salida = cerca(bases, hospedajes)
    salida.to_csv(a.salida / "hospedajes_cerca.csv", sep=";", index=False, encoding="utf-8-sig")
    con = salida["polo"].nunique()
    print(f"{len(hospedajes)} hospedajes con nombre en OSM · {con} de {len(bases)} bases con alguno cerca · {a.salida}")


if __name__ == "__main__":
    main()

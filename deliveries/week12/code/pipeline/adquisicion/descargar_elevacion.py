"""
La altura del terreno alrededor de cada base: pipeline/elevacion.py la usa para las bases que
OpenStreetMap y el inventario no traen, y para comprobar las demás (decisión 0020).

Qué baja    Terrain Tiles, en el registro de datos abiertos de AWS: las teselas «skadi» de 1° × 1°
            que tocan las bases de data/procesados/polos_bases.csv. Cada una es una grilla de
            enteros de 16 bits, en metros sobre el geoide EGM96, a un segundo de arco (unos 30 m),
            con -32768 donde no hay dato. De cada tesela guarda solo una ventana de 21 × 21 puntos
            (unos 600 m) alrededor de cada base: la tesela entera ocupa unos 25 MB, y las que
            hacen falta suman más de 1 000 MB comprimidas.
Dónde       data/externos/elevacion/ventanas_bases_v1.npz y manifiesto.json (fuera de git)
Licencia    Terrain Tiles junta modelos de elevación abiertos; en el Perú, SRTM y GMTED2010 del
            U.S. Geological Survey y ETOPO1 de NOAA, de dominio público. El USGS pide el crédito
            «SRTM and GMTED2010 terrain data courtesy of the U.S. Geological Survey»
            (https://github.com/tilezen/joerd/blob/master/docs/attribution.md).
Tarda       unos minutos: baja unos 1 300 MB y guarda menos de 1 MB.

Uso:  python pipeline/adquisicion/descargar_elevacion.py
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import math

import numpy as np
import requests

from _comun import AGENTE, EXTERNOS, RAIZ, ahora_utc, escribir_json, utf8_consola

CUBO = "https://s3.amazonaws.com/elevation-tiles-prod/skadi"
DIR = EXTERNOS / "elevacion"
VENTANAS = DIR / "ventanas_bases_v1.npz"
MANIFIESTO = DIR / "manifiesto.json"
BASES = RAIZ / "data" / "procesados" / "polos_bases.csv"
RADIO = 10  # puntos a cada lado de la base: una ventana de 21 × 21
SIN_DATO = -32768


def tesela(lat: float, lon: float) -> str:
    """El nombre de la tesela de 1° × 1° que contiene el punto, por su esquina suroeste: S16/S16W072."""
    la, lo = math.floor(lat), math.floor(lon)
    fila = f"{'N' if la >= 0 else 'S'}{abs(la):02d}"
    return f"{fila}/{fila}{'E' if lo >= 0 else 'W'}{abs(lo):03d}"


def grilla(comprimida: bytes) -> np.ndarray:
    """La tesela como matriz de metros, de norte a sur y de oeste a este. Tiene 3601 × 3601 puntos a un
    segundo de arco, o 1201 × 1201 a tres: el borde se repite en la tesela vecina."""
    crudo = gzip.decompress(comprimida)
    n = math.isqrt(len(crudo) // 2)
    if n * n * 2 != len(crudo):
        raise ValueError(f"una tesela de {len(crudo)} bytes no es cuadrada")
    return np.frombuffer(crudo, dtype=">i2").reshape(n, n).astype(np.int16)


def posicion(lat: float, lon: float, n: int) -> tuple[int, int]:
    """La fila y la columna del punto de la grilla más cercano: la fila 0 es el borde norte."""
    la, lo = math.floor(lat), math.floor(lon)
    paso = n - 1
    return int(round((la + 1 - lat) * paso)), int(round((lon - lo) * paso))


def ventana(m: np.ndarray, fila: int, columna: int, radio: int = RADIO) -> np.ndarray:
    """Los (2·radio + 1)² puntos alrededor de (fila, columna); lo que cae fuera de la tesela va sin dato."""
    lado = 2 * radio + 1
    salida = np.full((lado, lado), SIN_DATO, dtype=np.int16)
    n = m.shape[0]
    f0, f1 = max(0, fila - radio), min(n, fila + radio + 1)
    c0, c1 = max(0, columna - radio), min(n, columna + radio + 1)
    salida[f0 - (fila - radio) : f1 - (fila - radio), c0 - (columna - radio) : c1 - (columna - radio)] = m[f0:f1, c0:c1]
    return salida


def leer_bases() -> list[tuple[int, str, float, float]]:
    with open(BASES, encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    return [(int(f["polo"]), f["base"], float(f["lat"]), float(f["lon"])) for f in filas]


def main() -> None:
    utf8_consola()
    argparse.ArgumentParser(description="Baja la altura del terreno alrededor de cada base.").parse_args()
    bases = leer_bases()
    por_tesela: dict[str, list[int]] = {}
    for k, (_, _, lat, lon) in enumerate(bases):
        por_tesela.setdefault(tesela(lat, lon), []).append(k)
    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    ventanas = np.full((len(bases), 2 * RADIO + 1, 2 * RADIO + 1), SIN_DATO, dtype=np.int16)
    puntos = np.zeros(len(bases), dtype=np.int32)
    teselas = {}
    for nombre in sorted(por_tesela):
        url = f"{CUBO}/{nombre}.hgt.gz"
        r = sesion.get(url, timeout=300)
        r.raise_for_status()
        m = grilla(r.content)
        for k in por_tesela[nombre]:
            _, _, lat, lon = bases[k]
            fila, columna = posicion(lat, lon, m.shape[0])
            ventanas[k] = ventana(m, fila, columna)
        puntos[por_tesela[nombre]] = m.shape[0]
        teselas[nombre] = {"url": url, "sha256": hashlib.sha256(r.content).hexdigest(), "bytes": len(r.content)}
        print(f"{nombre}: {len(por_tesela[nombre])} bases", flush=True)
    DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        VENTANAS,
        polo=np.array([b[0] for b in bases], dtype=np.int32),
        lat=np.array([b[2] for b in bases]),
        lon=np.array([b[3] for b in bases]),
        tesela=np.array([tesela(b[2], b[3]) for b in bases]),
        puntos=puntos,
        ventana=ventanas,
    )
    escribir_json(
        MANIFIESTO,
        {
            "fuente": "Terrain Tiles (Mapzen y Linux Foundation), registro de datos abiertos de AWS, formato skadi",
            "registro": "https://registry.opendata.aws/terrain-tiles/",
            "bases": {"archivo": "data/procesados/polos_bases.csv", "cuantas": len(bases)},
            "radio": RADIO,
            "teselas": teselas,
            "descargado_utc": ahora_utc(),
            "licencia": "SRTM y GMTED2010 del USGS y ETOPO1 de NOAA, de dominio público; crédito: SRTM and GMTED2010 "
            "terrain data courtesy of the U.S. Geological Survey",
        },
    )
    megas = sum(t["bytes"] for t in teselas.values()) / 1e6
    print(f"Listo: {len(bases)} bases en {len(teselas)} teselas ({megas:.0f} MB bajados) en {VENTANAS}")


if __name__ == "__main__":
    main()

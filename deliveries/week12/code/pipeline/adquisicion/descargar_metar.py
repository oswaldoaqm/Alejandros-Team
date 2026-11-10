"""
Los METAR de los aeropuertos del Perú de 2022 a 2024: lo que el observador de cada aeropuerto vio
en el cielo, hora por hora. pipeline/cielo.py los usa para contar las noches despejadas en la
costa, donde de noche el satélite no ve las nubes bajas, y para comprobar al satélite en el resto
(decisión 0018).

Qué baja    NOAA Global Hourly (Integrated Surface Database), en su copia pública de AWS: el
            archivo de cada estación peruana (números 843xx a 848xx) y de cada año. De cada fila
            guarda solo la fecha, la estación, su nombre, su lugar y el texto METAR.
Dónde       data/externos/metar/AAAA/ESTACION.csv.gz y manifiesto.json (fuera de git)
Licencia    NOAA (Open Data Dissemination): abiertos al público. NOAA pide que se la cite y que
            lo que se calcula con ellos no se presente como dato original suyo. Los de estaciones
            fuera de Estados Unidos, como estas, están sujetos a la Resolución 40 de la OMM: NOAA
            advierte que no se redistribuyan. Por eso se quedan en data/externos/, y al
            repositorio solo llega lo que se calcula con ellos.
Tarda       un par de minutos.

Uso:  python pipeline/adquisicion/descargar_metar.py
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import re

import requests

from _comun import AGENTE, EXTERNOS, ahora_utc, escribir_json, utf8_consola

CUBO = "https://s3.amazonaws.com/noaa-global-hourly-pds"
DIR = EXTERNOS / "metar"
MANIFIESTO = DIR / "manifiesto.json"
ANIOS = (2022, 2023, 2024)
PERU = ("843", "844", "845", "846", "847", "848")  # los bloques de la OMM del Perú
MINIMO_BYTES = 300_000  # menos que esto son estaciones con pocas horas: no alcanzan para un mes
COLUMNAS = ("DATE", "STATION", "NAME", "LATITUDE", "LONGITUDE", "ELEVATION")


def estaciones(sesion: requests.Session, anio: int) -> list[tuple[str, int]]:
    r = sesion.get(f"{CUBO}/?list-type=2&max-keys=1000&prefix={anio}/84", timeout=60)
    r.raise_for_status()
    claves = re.findall(r"<Key>([^<]*)</Key>", r.text)
    tamanios = [int(s) for s in re.findall(r"<Size>([^<]*)</Size>", r.text)]
    return [(k, s) for k, s in zip(claves, tamanios, strict=True) if k.split("/")[1][:3] in PERU and s >= MINIMO_BYTES]


def main() -> None:
    utf8_consola()
    argparse.ArgumentParser(description="Baja los METAR de los aeropuertos del Perú.").parse_args()
    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    archivos = {}
    for anio in ANIOS:
        for clave, _ in estaciones(sesion, anio):
            estacion = clave.split("/")[1].removesuffix(".csv")
            salida = DIR / str(anio) / f"{estacion}.csv.gz"
            if not salida.exists():
                r = sesion.get(f"{CUBO}/{clave}", timeout=300)
                r.raise_for_status()
                filas = []
                for fila in csv.DictReader(io.StringIO(r.text)):
                    texto = fila.get("REM") or ""
                    inicio = min((i for i in (texto.find("METAR"), texto.find("SPECI")) if i >= 0), default=-1)
                    if inicio < 0:
                        continue
                    filas.append([fila[c] for c in COLUMNAS] + [texto[inicio:].rstrip("=")])
                salida.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(salida, "wt", encoding="utf-8", newline="") as fh:
                    w = csv.writer(fh)
                    w.writerow([*COLUMNAS, "METAR"])
                    w.writerows(filas)
                print(f"{anio} {estacion}: {len(filas)} METAR", flush=True)
            archivos[f"{anio}/{estacion}"] = {
                "url": f"{CUBO}/{clave}",
                "sha256": hashlib.sha256(salida.read_bytes()).hexdigest(),
            }
    escribir_json(
        MANIFIESTO,
        {
            "fuente": "NOAA Global Hourly (Integrated Surface Database), copia pública en AWS",
            "registro": "https://registry.opendata.aws/noaa-isd/",
            "anios": list(ANIOS),
            "archivos": archivos,
            "descargado_utc": ahora_utc(),
            "licencia": "NOAA Open Data Dissemination, con cita a NOAA; estaciones fuera de EE. UU.: Resolución 40 de"
            " la OMM, no se redistribuyen",
        },
    )
    print(f"Listo: {len(archivos)} archivos en {DIR}")


if __name__ == "__main__":
    main()

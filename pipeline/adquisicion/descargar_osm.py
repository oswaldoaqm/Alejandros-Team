"""
Descarga el extracto de OpenStreetMap del Perú para calcular tiempos de viaje
por carretera real.

Por qué
-------
Hoy el tiempo entre dos paradas sale de la distancia en línea recta por un
factor de sinuosidad de 1,6 que nunca se calibró, y el motor no sabe qué polos
no tienen carretera desde el origen. Con la red vial ambas cosas se miden.

Qué baja   https://download.geofabrik.de/south-america/peru-latest.osm.pbf
Dónde      data/externos/osm/peru-latest.osm.pbf  (fuera de git)
Licencia   ODbL 1.0 · © colaboradores de OpenStreetMap. Las tablas de tiempos
           que se deriven de este archivo se publican también bajo ODbL.

Reproducible: verifica el MD5 que publica Geofabrik y deja un manifiesto con la
fecha de los datos, el tamaño y el hash. Geofabrik publica un extracto nuevo
cada día; una vez bajado y verificado, el script no lo reemplaza salvo que se
le pida con --forzar, para que todos los cálculos usen el mismo archivo.

Si se corta, al volver a correrlo retoma. Si Geofabrik publicó una versión
nueva mientras tanto, empieza de cero en vez de mezclar dos archivos.

Uso:  python pipeline/adquisicion/descargar_osm.py
      python pipeline/adquisicion/descargar_osm.py --forzar   # versión del día
"""

from __future__ import annotations

import argparse
import json
import sys
import time

import requests

from _comun import AGENTE, EXTERNOS, ahora_utc, escribir_json, md5_archivo, miles, utf8_consola

URL = "https://download.geofabrik.de/south-america/peru-latest.osm.pbf"
DESTINO = EXTERNOS / "osm" / "peru-latest.osm.pbf"
PARCIAL = DESTINO.with_suffix(".pbf.part")
PARCIAL_META = DESTINO.with_suffix(".pbf.part.json")
MANIFIESTO = EXTERNOS / "osm" / "manifiesto.json"


def md5_publicado(sesion: requests.Session) -> str:
    r = sesion.get(URL + ".md5", timeout=30)
    r.raise_for_status()
    return r.text.split()[0].strip().lower()


def leer_json(ruta) -> dict:
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def bajar(sesion: requests.Session, intentos: int = 5) -> str:
    """Deja el archivo completo en PARCIAL y devuelve su Last-Modified."""
    PARCIAL.parent.mkdir(parents=True, exist_ok=True)
    for intento in range(1, intentos + 1):
        ya = PARCIAL.stat().st_size if PARCIAL.exists() else 0
        version = leer_json(PARCIAL_META).get("last_modified", "")
        cab = {}
        if ya and version:
            # If-Range: si el archivo cambió en el servidor, responde 200 con
            # el archivo entero en vez de 206 con el resto de otra versión
            cab = {"Range": f"bytes={ya}-", "If-Range": version}
        try:
            with sesion.get(URL, headers=cab, stream=True, timeout=(30, 120)) as r:
                if r.status_code == 416:  # ya estaba completo
                    return version
                r.raise_for_status()
                if r.status_code != 206:  # de cero: no hay parcial o cambió la versión
                    ya = 0
                version = r.headers.get("Last-Modified", "")
                escribir_json(PARCIAL_META, {"last_modified": version})
                total = ya + int(r.headers.get("Content-Length", 0))
                with open(PARCIAL, "ab" if ya else "wb") as fh:
                    hecho = ya
                    siguiente = (int(hecho / total * 10) + 1) / 10 if total else 1.0
                    if ya:
                        print(f"  retomando desde {miles(ya / 1e6)} MB", flush=True)
                    for trozo in r.iter_content(chunk_size=1 << 20):
                        fh.write(trozo)
                        hecho += len(trozo)
                        if total and hecho / total >= siguiente:
                            print(
                                f"  {hecho / total:4.0%}  {miles(hecho / 1e6)} de {miles(total / 1e6)} MB", flush=True
                            )
                            siguiente = (int(hecho / total * 10) + 1) / 10
            return version
        except (requests.ConnectionError, requests.Timeout, requests.exceptions.ChunkedEncodingError) as e:
            espera = 10 * intento
            print(
                f"  se cortó la conexión ({type(e).__name__}); reintento {intento}/{intentos} en {espera} s", flush=True
            )
            time.sleep(espera)
    sys.exit("No se pudo completar la descarga. Vuelve a correr el script: retoma donde quedó.")


def main() -> None:
    utf8_consola()
    ap = argparse.ArgumentParser(description="Descarga el extracto de OpenStreetMap del Perú.")
    ap.add_argument("--forzar", action="store_true", help="reemplaza el archivo ya verificado por la versión del día")
    a = ap.parse_args()

    previo = leer_json(MANIFIESTO)
    if DESTINO.exists() and not a.forzar and previo.get("md5") == md5_archivo(DESTINO):
        print(
            f"Ya está descargado y verificado: datos de OSM del {previo.get('datos_last_modified')}.\n"
            "Se conserva para que todo el cálculo use el mismo archivo. "
            "Para bajar la versión del día: --forzar"
        )
        return

    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    antes = md5_publicado(sesion)
    print(f"Descargando {URL}")
    version = bajar(sesion)

    real = md5_archivo(PARCIAL)
    if real not in (antes, md5_publicado(sesion)):  # el .md5 pudo cambiar durante la descarga
        PARCIAL.unlink(missing_ok=True)
        PARCIAL_META.unlink(missing_ok=True)
        sys.exit(
            f"El MD5 no coincide con el publicado (obtenido {real}). Se descartó la descarga; "
            "vuelve a correr el script."
        )
    PARCIAL.replace(DESTINO)
    PARCIAL_META.unlink(missing_ok=True)

    escribir_json(
        MANIFIESTO,
        {
            "fuente": "Geofabrik · extracto de OpenStreetMap",
            "url": URL,
            "descargado_utc": ahora_utc(),
            "datos_last_modified": version,
            "bytes": DESTINO.stat().st_size,
            "md5": real,
            "md5_verificado_contra": URL + ".md5",
            "licencia": "ODbL 1.0",
            "atribucion": "© colaboradores de OpenStreetMap",
        },
    )
    print(
        f"\nListo: {miles(DESTINO.stat().st_size / 1e6)} MB · MD5 verificado · "
        f"datos del {version} · manifiesto en {MANIFIESTO}"
    )


if __name__ == "__main__":
    main()

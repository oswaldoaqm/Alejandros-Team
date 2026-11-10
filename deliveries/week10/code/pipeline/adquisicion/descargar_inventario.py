"""
Descarga el Inventario Nacional de Recursos Turísticos de MINCETUR, el dataset
base de todo el producto.

Qué baja   https://www.mincetur.gob.pe/Datos_abiertos/DGET/Inventario_recursos_turisticos.csv
Dónde      data/externos/inventario/Inventario_recursos_turisticos.csv  (fuera de git)
Licencia   ODC-BY · Ministerio de Comercio Exterior y Turismo del Perú

Deja un manifiesto con la fecha, el tamaño, el MD5 y el número de registros, y
compara el contenido con deliveries/week04/data/sample.csv, la copia con la que
se construyó todo hasta la semana 7. Si MINCETUR publicó una versión nueva, dice
cuántos recursos entraron, salieron o cambiaron y en qué columnas, sin tocar la
copia del repositorio. La comparación es por registro y no por bytes (git guarda
sample.csv con otro fin de línea) y no cuenta FECHA_DE_CORTE, que cambia en cada
publicación aunque el recurso siga igual.

El archivo está en Windows-1252, no en Latin-1: la diferencia está en las comillas
“ ”, el apóstrofo ’ y la raya – de algunos nombres.

Uso:  python pipeline/adquisicion/descargar_inventario.py
"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from collections import Counter

import requests

from _comun import AGENTE, EXTERNOS, RAIZ, ahora_utc, escribir_json, md5_archivo, miles, utf8_consola

URL = "https://www.mincetur.gob.pe/Datos_abiertos/DGET/Inventario_recursos_turisticos.csv"
DESTINO = EXTERNOS / "inventario" / "Inventario_recursos_turisticos.csv"
MANIFIESTO = EXTERNOS / "inventario" / "manifiesto.json"
COPIA_REPO = RAIZ / "deliveries" / "week04" / "data" / "sample.csv"
CLAVE = "CODIGO DEL RECURSO"
# Cambia en cada publicación mensual aunque el recurso no cambie.
NO_COMPARAR = {"FECHA_DE_CORTE"}


def decodificar(contenido: bytes) -> tuple[str, str]:
    """El texto y su codificación. MINCETUR publica en Windows-1252; si algún día
    cambia a UTF-8, se nota aquí."""
    for codificacion in ("utf-8", "cp1252"):
        try:
            return contenido.decode(codificacion), codificacion
        except UnicodeDecodeError:
            pass
    return contenido.decode("latin-1"), "latin-1"


def registros(texto: str) -> dict[str, dict[str, str]]:
    """{código: {columna: valor}} de un CSV del inventario ya decodificado."""
    filas = csv.DictReader(io.StringIO(texto, newline=""), delimiter=";")
    if CLAVE not in (filas.fieldnames or []):
        sys.exit(f"El archivo no tiene la columna «{CLAVE}». Columnas: {filas.fieldnames}")
    return {f[CLAVE].strip(): {k: (v or "").strip() for k, v in f.items()} for f in filas}


def columnas_que_cambian(nuevo: dict[str, str], previo: dict[str, str]) -> list[str]:
    return [c for c in nuevo if c not in NO_COMPARAR and nuevo.get(c) != previo.get(c)]


def main() -> None:
    utf8_consola()
    argparse.ArgumentParser(description="Descarga el inventario de MINCETUR.").parse_args()

    print(f"Descargando {URL}")
    r = requests.get(URL, headers={"User-Agent": AGENTE}, timeout=(30, 120))
    r.raise_for_status()
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    tmp = DESTINO.with_suffix(".csv.tmp")
    tmp.write_bytes(r.content)
    tmp.replace(DESTINO)

    texto, codificacion = decodificar(r.content)
    nuevo = registros(texto)
    previo = registros(decodificar(COPIA_REPO.read_bytes())[0])

    entran = sorted(set(nuevo) - set(previo), key=lambda c: int(c) if c.isdigit() else 0)
    salen = sorted(set(previo) - set(nuevo), key=lambda c: int(c) if c.isdigit() else 0)
    por_columna: Counter[str] = Counter()
    cambian = []
    for codigo in set(nuevo) & set(previo):
        columnas = columnas_que_cambian(nuevo[codigo], previo[codigo])
        if columnas:
            cambian.append(codigo)
            por_columna.update(columnas)
    se_ubican = sum(1 for c in set(nuevo) & set(previo) if not previo[c].get("LATITUD") and nuevo[c].get("LATITUD"))

    escribir_json(
        MANIFIESTO,
        {
            "fuente": "Inventario Nacional de Recursos Turísticos · MINCETUR",
            "url": URL,
            "descargado_utc": ahora_utc(),
            "http_last_modified": r.headers.get("Last-Modified", ""),
            "bytes": DESTINO.stat().st_size,
            "md5": md5_archivo(DESTINO),
            "codificacion": codificacion,
            "registros": len(nuevo),
            "contra_week04_sample": {
                "entran": len(entran),
                "salen": len(salen),
                "cambian": len(cambian),
                "cambios_por_columna": dict(por_columna.most_common()),
                "recursos_que_ganan_coordenadas": se_ubican,
                "no_se_compara": sorted(NO_COMPARAR),
                "codigos_que_entran": entran[:50],
                "codigos_que_salen": salen[:50],
            },
            "licencia": "ODC-BY",
            "atribucion": (
                "Inventario Nacional de Recursos Turísticos, Ministerio de Comercio Exterior y Turismo del Perú"
            ),
        },
    )

    print(f"\n{miles(len(nuevo))} registros · {codificacion} · {miles(DESTINO.stat().st_size / 1e3)} KB")
    if not (entran or salen or cambian):
        print("Idéntico, registro por registro, a deliveries/week04/data/sample.csv.")
    else:
        print(f"Contra week04/data/sample.csv: entran {len(entran)} · salen {len(salen)} · cambian {len(cambian)}")
        for columna, n in por_columna.most_common():
            print(f"  {columna}: {miles(n)}")
        if se_ubican:
            print(f"  (de esos, {miles(se_ubican)} recursos que no tenían coordenadas ahora las tienen)")
        print("MINCETUR publicó una versión nueva. La copia del repositorio no se tocó: avisa al equipo.")
    print(f"Manifiesto: {MANIFIESTO}")


if __name__ == "__main__":
    main()

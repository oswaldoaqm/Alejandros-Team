"""
Los lugares que publica Overture Maps dentro del Perú. pipeline/noche.py elige de ahí los bares,
pubs, discotecas, karaokes y peñas que quedan cerca de donde se duerme (decisión 0018).

Qué baja    De una versión del tema «places» de Overture, en su copia pública de AWS, solo los
            grupos de filas cuya caja toca el Perú y solo las columnas que hacen falta: el
            identificador, el nombre, la categoría, la confianza, el estado, la caja y las
            fuentes. Nunca los teléfonos, los correos, las páginas web, las redes ni las
            direcciones.
Versión     La más reciente, salvo que se pida otra con --version. Overture conserva solo las
            últimas en AWS: la que se usó queda en el manifiesto.
Dónde       data/externos/overture/lugares_peru_<versión>.parquet y manifiesto.json (fuera de git)
Licencia    CDLA Permissive 2.0 lo que viene de Meta, Microsoft y otros; Apache 2.0 lo que viene
            de Foursquare, que pipeline/noche.py deja fuera.
Necesita    pyarrow y fsspec (pip install pyarrow fsspec aiohttp).
Tarda       un minuto: de los 11 GB del tema lee unos 100 MB.

Uso:  python pipeline/adquisicion/descargar_overture.py
      python pipeline/adquisicion/descargar_overture.py --version 2026-09-23.1
"""

from __future__ import annotations

import argparse
import hashlib
import re
import time

import requests

from _comun import AGENTE, EXTERNOS, ahora_utc, escribir_json, utf8_consola

CUBO = "https://overturemaps-us-west-2.s3.us-west-2.amazonaws.com"
DIR = EXTERNOS / "overture"
MANIFIESTO = DIR / "manifiesto.json"
OESTE, ESTE, SUR, NORTE = -81.45, -68.6, -18.4, 0.05  # el Perú
COLUMNAS = ["id", "confidence", "names", "basic_category", "taxonomy", "operating_status", "bbox", "sources"]


def _listar(sesion: requests.Session, prefijo: str, delimitador: bool = False) -> tuple[list[str], list[str]]:
    extra = "&delimiter=/" if delimitador else ""
    r = sesion.get(f"{CUBO}/?list-type=2&max-keys=1000&prefix={prefijo}{extra}", timeout=60)
    r.raise_for_status()
    return re.findall(r"<Key>([^<]*)</Key>", r.text), re.findall(r"<Prefix>([^<]*)</Prefix>", r.text)


def ultima_version(sesion: requests.Session) -> str:
    _, prefijos = _listar(sesion, "release/", delimitador=True)
    versiones = sorted(p.split("/")[1] for p in prefijos if p.count("/") == 2)
    return versiones[-1]


def main() -> None:
    utf8_consola()
    ap = argparse.ArgumentParser(description="Baja los lugares de Overture Maps dentro del Perú.")
    ap.add_argument("--version", help="la versión de Overture, como 2026-09-23.1; por defecto la última")
    a = ap.parse_args()

    import fsspec
    import pyarrow as pa
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    sesion = requests.Session()
    sesion.headers["User-Agent"] = AGENTE
    version = a.version or ultima_version(sesion)
    salida = DIR / f"lugares_peru_{version}.parquet"
    if salida.exists():
        print(f"Ya está: {salida}")
        return
    claves, _ = _listar(sesion, f"release/{version}/theme=places/type=place/")
    sistema = fsspec.filesystem("https", client_kwargs={"trust_env": True, "headers": {"User-Agent": AGENTE}})
    tablas = []
    for clave in claves:
        inicio = time.time()
        with sistema.open(f"{CUBO}/{clave}", block_size=4 << 20, cache_type="bytes") as fh:
            archivo = pq.ParquetFile(fh)
            meta = archivo.metadata
            columna = {meta.row_group(0).column(j).path_in_schema: j for j in range(meta.row_group(0).num_columns)}
            grupos = []
            for g in range(meta.num_row_groups):
                grupo = meta.row_group(g)
                caja = {n: grupo.column(columna[f"bbox.{n}"]).statistics for n in ("xmin", "xmax", "ymin", "ymax")}
                if (
                    caja["xmax"].max >= OESTE
                    and caja["xmin"].min <= ESTE
                    and caja["ymax"].max >= SUR
                    and caja["ymin"].min <= NORTE
                ):
                    grupos.append(g)
            if grupos:
                tabla = archivo.read_row_groups(grupos, columns=COLUMNAS)
                x = pc.struct_field(tabla["bbox"], "xmin")
                y = pc.struct_field(tabla["bbox"], "ymin")
                dentro = pc.and_(
                    pc.and_(pc.greater_equal(x, OESTE), pc.less_equal(x, ESTE)),
                    pc.and_(pc.greater_equal(y, SUR), pc.less_equal(y, NORTE)),
                )
                tablas.append(tabla.filter(dentro))
        print(f"{clave.split('/')[-1][:10]}: {len(grupos)} grupos de filas en {time.time() - inicio:.0f} s", flush=True)
    tabla = pa.concat_tables(tablas)
    DIR.mkdir(parents=True, exist_ok=True)
    temporal = salida.with_suffix(".parquet.tmp")
    pq.write_table(tabla, temporal, compression="zstd")
    temporal.replace(salida)
    escribir_json(
        MANIFIESTO,
        {
            "fuente": "Overture Maps Foundation, tema places",
            "version": version,
            "url": f"{CUBO}/release/{version}/theme=places/type=place/",
            "caja": {"oeste": OESTE, "este": ESTE, "sur": SUR, "norte": NORTE},
            "columnas": COLUMNAS,
            "lugares": tabla.num_rows,
            "archivo": salida.name,
            "sha256": hashlib.sha256(salida.read_bytes()).hexdigest(),
            "descargado_utc": ahora_utc(),
            "licencia": "CDLA Permissive 2.0 (Meta, Microsoft y otros); Apache 2.0 (Foursquare)",
        },
    )
    print(f"Listo: {tabla.num_rows} lugares de la versión {version} en {salida}")


if __name__ == "__main__":
    main()

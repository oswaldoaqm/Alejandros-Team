"""
Baja las luces nocturnas que ve el satélite VIIRS sobre el Perú, para estimar desde dónde se ven
las estrellas (pipeline/cielo.py, decisión 0018).

Qué baja    Los compuestos mensuales de la banda día-noche (DNB) de VIIRS, en el Suomi NPP, que
            arma el Earth Observation Group de la Colorado School of Mines. Son los de la copia
            del Banco Mundial en AWS, «Light Every Night». De cada mes, dos capas: la radiancia
            media sin nubes (avg_rade9, en nW/cm²/sr) y cuántas noches sin nubes la midieron
            (n_cf). La resolución es de 15 segundos de arco, unos 460 m.
            De cada archivo global, de unos 4 GB, lee por rangos solo la ventana del Perú con
            300 km alrededor: la luz de una ciudad se ve en el cielo hasta esa distancia, también
            la de Guayaquil, Arica o La Paz.
Meses       De enero de 2024 a junio de 2025, menos octubre de 2024, que falta en la copia: 17
            meses. pipeline/cielo.py usa la mediana, así que los barcos de pesca y los incendios,
            que no se repiten, no cuentan como luz fija.
Dónde       data/externos/luces/viirs_AAAAMM.npz (fuera de git), con la radiancia, las noches
            medidas y la transformación de la ventana; y manifiesto.json
Licencia    Dominio público: la Colorado School of Mines dice que sus productos no tienen
            derechos de autor ni restricciones de uso, y pide citar a Elvidge et al. (2021). La
            copia del Banco Mundial se cita también: «World Bank - Light Every Night, accedido el
            … desde https://registry.opendata.aws/wb-light-every-night».
Necesita    rasterio (pip install rasterio), que lee la ventana de un GeoTIFF remoto.
Tarda       unos 6 minutos. Si se corta, al volver a correrlo sigue con los meses que faltan.

Uso:  python pipeline/adquisicion/descargar_luces.py
"""

from __future__ import annotations

import argparse
import calendar
import hashlib
import io
import time

import numpy as np

from _comun import EXTERNOS, ahora_utc, escribir_json, utf8_consola

CUBO = "https://s3.amazonaws.com/globalnightlight/composites"
DIR = EXTERNOS / "luces"
MANIFIESTO = DIR / "manifiesto.json"
# El Perú con 300 km alrededor (3° de lado a lado alcanzan en estas latitudes).
OESTE, SUR, ESTE, NORTE = -84.5, -21.5, -65.5, 3.5
MESES = [(2024, m) for m in range(1, 13) if m != 10] + [(2025, m) for m in range(1, 7)]


def url(anio: int, mes: int, capa: str) -> str:
    fin = calendar.monthrange(anio, mes)[1]
    nombre = f"DNB_npp_{anio}{mes:02d}01-{anio}{mes:02d}{fin}_global_ecm-slcorr_v10_ops.{capa}.tif"
    return f"{CUBO}/npp_{anio}{mes:02d}_ops/{nombre}"


def ventana(ruta: str) -> tuple[np.ndarray, tuple[float, ...]]:
    """La ventana del Perú de un GeoTIFF remoto, y su transformación (a, b, c, d, e, f)."""
    import rasterio
    from rasterio.windows import from_bounds

    entorno = {
        "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
        "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
        "GDAL_HTTP_MULTIRANGE": "YES",
        "GDAL_HTTP_MERGE_CONSECUTIVE_RANGES": "YES",
        "GDAL_HTTP_MAX_RETRY": "4",
        "GDAL_HTTP_RETRY_DELAY": "5",
    }
    with rasterio.Env(**entorno), rasterio.open(f"/vsicurl/{ruta}") as ds:
        w = from_bounds(OESTE, SUR, ESTE, NORTE, ds.transform).round_offsets().round_lengths()
        return ds.read(1, window=w), tuple(ds.window_transform(w))[:6]


def main() -> None:
    utf8_consola()
    argparse.ArgumentParser(description="Baja las luces nocturnas de VIIRS sobre el Perú.").parse_args()
    DIR.mkdir(parents=True, exist_ok=True)
    meses = {}
    for anio, mes in MESES:
        salida = DIR / f"viirs_{anio}{mes:02d}.npz"
        if not salida.exists():
            inicio = time.time()
            rad, transformacion = ventana(url(anio, mes, "avg_rade9"))
            noches, _ = ventana(url(anio, mes, "n_cf"))
            buffer = io.BytesIO()
            np.savez_compressed(
                buffer,
                radiancia=rad.astype(np.float32),
                noches=noches.astype(np.uint16),
                transformacion=np.array(transformacion),
            )
            salida.write_bytes(buffer.getvalue())
            print(
                f"{anio}-{mes:02d}: {rad.shape[1]} × {rad.shape[0]} pixeles en {time.time() - inicio:.0f} s", flush=True
            )
        meses[f"{anio}-{mes:02d}"] = {
            "radiancia": url(anio, mes, "avg_rade9"),
            "noches": url(anio, mes, "n_cf"),
            "archivo": salida.name,
            "sha256": hashlib.sha256(salida.read_bytes()).hexdigest(),
        }
    escribir_json(
        MANIFIESTO,
        {
            "fuente": "VIIRS DNB, compuestos mensuales ecm-slcorr (con la luz parásita corregida) del Earth "
            "Observation Group (Colorado School of Mines), en la copia del Banco Mundial «Light Every Night» (AWS)",
            "registro": "https://registry.opendata.aws/wb-light-every-night/",
            "ventana": {"oeste": OESTE, "sur": SUR, "este": ESTE, "norte": NORTE},
            "descargado_utc": ahora_utc(),
            "meses": meses,
            "licencia": "Dominio público (EOG); la copia del Banco Mundial pide citarla",
            "cita": "Elvidge, C. D. et al. (2021). Annual time series of global VIIRS nighttime lights derived "
            "from monthly averages: 2012 to 2019. Remote Sensing 13(5), 922.",
        },
    )
    print(f"Listo: {len(meses)} meses en {DIR}")


if __name__ == "__main__":
    main()

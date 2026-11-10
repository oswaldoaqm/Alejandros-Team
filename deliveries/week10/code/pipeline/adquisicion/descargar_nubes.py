"""
Cuántas noches de cada mes se ve el cielo despejado sobre el Perú, según la máscara de nubes del
satélite GOES-16 (pipeline/cielo.py, decisión 0018).

Qué baja    El producto «Clear Sky Mask» de disco completo de GOES-16 (ABI-L2-ACMF), de NOAA, en
            su copia pública de AWS. De cada día de 2022 a 2024, la imagen de las 02:00 y la de
            las 06:00 UTC, que son las 21:00 y la 01:00 en el Perú. De cada archivo, de 23 MB,
            lee por rangos solo la ventana del Perú (unos 300 KB): la máscara binaria (BCM:
            despejado o nublado) y su calidad (DQF), a 2 km por pixel bajo el satélite.
Qué guarda  Por hora, por mes y por pixel, cuántas veces la medición fue buena y cuántas de esas
            el cielo estaba despejado. No guarda las imágenes.
            Ojo: de noche, sobre el desierto de la costa, esta máscara se equivoca (no ve las
            nubes bajas del invierno y marca nubes donde no las hay). pipeline/cielo.py usa ahí
            los METAR de los aeropuertos (descargar_metar.py).
Dónde       data/externos/nubes/meses/goes16_AAAAMM.npz, uno por mes, y al final
            data/externos/nubes/goes16_noches.npz y manifiesto.json (fuera de git)
Licencia    Dominio público (NOAA, Open Data Dissemination).
Necesita    h5py, fsspec y aiohttp (pip install h5py fsspec aiohttp).
Tarda       unos 20 minutos con seis meses a la vez. Si se corta, al volver a correrlo baja solo
            los meses que faltan.

Uso:  python pipeline/adquisicion/descargar_nubes.py
      python pipeline/adquisicion/descargar_nubes.py --procesos 2   # con una conexión lenta
"""

from __future__ import annotations

import argparse
import calendar
import re
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import date

import numpy as np

from _comun import EXTERNOS, ahora_utc, escribir_json, utf8_consola

CUBO = "https://s3.amazonaws.com/noaa-goes16"
PRODUCTO = "ABI-L2-ACMF"
DIR = EXTERNOS / "nubes"
MESES_DIR = DIR / "meses"
SALIDA = DIR / "goes16_noches.npz"
MANIFIESTO = DIR / "manifiesto.json"
HORAS_UTC = (2, 6)  # las 21:00 y la 01:00 en el Perú
ANIOS = (2022, 2023, 2024)
# La ventana del Perú en la rejilla fija de GOES-16 (5 424 × 5 424 pixeles de 56 µrad): filas y
# columnas que cubren de 0,5° N a 18,6° S y de 81,6° a 68,4° O. pipeline/cielo.py la usa para
# ubicar cada punto.
FILAS = (2681, 3711)
COLUMNAS = (2344, 3079)


def _sesion():
    import requests

    s = requests.Session()
    s.headers["User-Agent"] = (
        "DreemGO/1.0 (proyecto academico UTEC DS3022; https://github.com/oswaldoaqm/Alejandros-Team)"
    )
    return s


def _clave(sesion, dia: date, hora: int) -> str | None:
    """La primera imagen de esa hora: la de las hh:00."""
    prefijo = f"{PRODUCTO}/{dia.year}/{dia.timetuple().tm_yday:03d}/{hora:02d}/"
    for intento in range(4):
        try:
            r = sesion.get(f"{CUBO}/?list-type=2&max-keys=10&prefix={prefijo}", timeout=60)
            r.raise_for_status()
            claves = re.findall(r"<Key>([^<]*)</Key>", r.text)
            return claves[0] if claves else None
        except Exception:  # noqa: BLE001 — la red falla de muchas maneras; se reintenta
            time.sleep(5 * (intento + 1))
    return None


def _ventana(sistema, clave: str):
    import h5py

    f0, f1 = FILAS
    c0, c1 = COLUMNAS
    for intento in range(3):
        try:
            with (
                sistema.open(f"{CUBO}/{clave}", block_size=256 * 1024, cache_type="bytes") as fh,
                h5py.File(fh, "r") as f,
            ):
                return f["BCM"][f0:f1, c0:c1], f["DQF"][f0:f1, c0:c1]
        except Exception:  # noqa: BLE001
            time.sleep(5 * (intento + 1))
    return None


def un_mes(anio: int, mes: int) -> str:
    """Baja las imágenes de un mes y guarda sus cuentas en meses/goes16_AAAAMM.npz."""
    import fsspec

    sesion = _sesion()
    sistema = fsspec.filesystem("https", client_kwargs={"trust_env": True})
    forma = (len(HORAS_UTC), FILAS[1] - FILAS[0], COLUMNAS[1] - COLUMNAS[0])
    despejado, valido = np.zeros(forma, np.uint16), np.zeros(forma, np.uint16)
    imagenes, faltan = 0, []
    for d in range(1, calendar.monthrange(anio, mes)[1] + 1):
        dia = date(anio, mes, d)
        for i, hora in enumerate(HORAS_UTC):
            clave = _clave(sesion, dia, hora)
            leido = _ventana(sistema, clave) if clave else None
            if leido is None:
                faltan.append(f"{dia.isoformat()}T{hora:02d}")
                continue
            bcm, dqf = leido
            bueno = dqf == 0
            valido[i] += bueno
            despejado[i] += bueno & (bcm == 0)
            imagenes += 1
    salida = MESES_DIR / f"goes16_{anio}{mes:02d}.npz"
    temporal = salida.with_name(salida.stem + ".tmp.npz")
    np.savez_compressed(temporal, despejado=despejado, valido=valido, imagenes=imagenes, faltan=np.array(faltan))
    temporal.replace(salida)
    return f"{anio}-{mes:02d}: {imagenes} imágenes" + (f", faltan {len(faltan)}" if faltan else "")


def juntar() -> dict:
    """Suma los meses de todos los años: (hora, mes, fila, columna)."""
    forma = (len(HORAS_UTC), 12, FILAS[1] - FILAS[0], COLUMNAS[1] - COLUMNAS[0])
    despejado, valido = np.zeros(forma, np.uint32), np.zeros(forma, np.uint32)
    imagenes, faltan = 0, []
    for anio in ANIOS:
        for mes in range(1, 13):
            z = np.load(MESES_DIR / f"goes16_{anio}{mes:02d}.npz")
            despejado[:, mes - 1] += z["despejado"]
            valido[:, mes - 1] += z["valido"]
            imagenes += int(z["imagenes"])
            faltan += [str(x) for x in z["faltan"]]
    np.savez_compressed(
        SALIDA,
        despejado=despejado,
        valido=valido,
        horas_utc=np.array(HORAS_UTC),
        filas=np.array(FILAS),
        columnas=np.array(COLUMNAS),
    )
    return {"imagenes": imagenes, "faltan": faltan}


def main() -> None:
    utf8_consola()
    ap = argparse.ArgumentParser(description="Cuenta las noches despejadas sobre el Perú con GOES-16.")
    ap.add_argument("--procesos", type=int, default=6, help="meses que se bajan a la vez")
    a = ap.parse_args()
    MESES_DIR.mkdir(parents=True, exist_ok=True)
    pendientes = [(y, m) for y in ANIOS for m in range(1, 13) if not (MESES_DIR / f"goes16_{y}{m:02d}.npz").exists()]
    if pendientes:
        print(f"{len(pendientes)} meses por bajar, {a.procesos} a la vez", flush=True)
        with ProcessPoolExecutor(max_workers=a.procesos) as grupo:
            for futuro in as_completed([grupo.submit(un_mes, y, m) for y, m in pendientes]):
                print(futuro.result(), flush=True)
    resumen = juntar()
    escribir_json(
        MANIFIESTO,
        {
            "fuente": "GOES-16 ABI L2 Clear Sky Mask, disco completo (ABI-L2-ACMF), NOAA",
            "copia": "https://registry.opendata.aws/noaa-goes/",
            "horas_utc": list(HORAS_UTC),
            "anios": list(ANIOS),
            "ventana_en_la_rejilla_fija": {"filas": list(FILAS), "columnas": list(COLUMNAS)},
            "imagenes": resumen["imagenes"],
            "faltan": resumen["faltan"],
            "descargado_utc": ahora_utc(),
            "licencia": "Dominio público (NOAA)",
        },
    )
    print(f"Listo: {resumen['imagenes']} imágenes, faltan {len(resumen['faltan'])}; en {SALIDA}")


if __name__ == "__main__":
    main()

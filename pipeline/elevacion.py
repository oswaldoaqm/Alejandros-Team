"""
La altura de cada base según un modelo de elevación (decisión 0020).

``pipeline/bases.py`` le da a cada base la altura que declara su nodo de OpenStreetMap o, si no la
tiene, la mediana de los lugares del inventario a menos de 2 km. A 13 de las 194 no les llega
ninguna de las dos, y sin altura el motor no sabe si se duerme en la altura: no avisa, no arma el
primer día tranquilo y la altitud máxima de la consulta no la puede filtrar. Aquí sale la altura
del terreno:

- **El modelo:** Terrain Tiles, del registro de datos abiertos de AWS
  (``pipeline/adquisicion/descargar_elevacion.py``). En el Perú es SRTM, a un segundo de arco: unos
  30 m entre punto y punto.
- **La altura de un pueblo:** la mediana de los 5 × 5 puntos alrededor de la base, unos 150 m de
  lado. Un pueblo no está en un solo punto, y un punto puede caer en una quebrada o en un techo. Lo
  que no tiene dato no cuenta.

En las 170 bases con la altura de OSM, el modelo difiere en 1 m en la mediana y en 26 como mucho;
en las 11 que la sacaban de los lugares cercanos, en 28 m en la mediana y en 137 como mucho. Por
eso, en los artefactos (``pipeline/artefactos.py``), la de OSM se queda y en las demás manda el
modelo.

Escribe data/procesados/altitud_bases.csv y altitud_resumen.json.

Uso:  python -m pipeline.elevacion
      (después de tiempos.py, que elige las bases, y de descargar_elevacion.py)
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.maestro import EXTERNOS, PROCESADOS

VENTANAS = EXTERNOS / "elevacion" / "ventanas_bases_v1.npz"
RADIO = 2  # puntos a cada lado de la base: la mediana de 5 × 5
SIN_DATO = -32768
FUENTE = "terrain_tiles"
OSM = "osm"  # la fuente de bases.py que se queda: coincide con el modelo
MISMA_BASE_GRADOS = 1e-5  # unos 1,1 m: más que esto, la base se movió desde la descarga
DIFIERE_M = (100, 300)


def altura(ventana: np.ndarray, radio: int = RADIO) -> float | None:
    """La mediana de los puntos con dato a ``radio`` o menos del centro de la ventana; None si no hay."""
    centro = ventana.shape[0] // 2
    cerca = ventana[centro - radio : centro + radio + 1, centro - radio : centro + radio + 1]
    validos = cerca[cerca != SIN_DATO]
    return float(np.median(validos)) if validos.size else None


def leer_ventanas(ruta: Path = VENTANAS) -> pd.DataFrame:
    """polo, lat, lon y altitud_dem_m de cada base descargada."""
    with np.load(ruta) as z:
        return pd.DataFrame(
            {
                "polo": z["polo"].astype(int),
                "lat_dem": z["lat"],
                "lon_dem": z["lon"],
                "altitud_dem_m": [altura(v) for v in z["ventana"]],
            }
        )


def tabla(bases: pd.DataFrame, dem: pd.DataFrame) -> pd.DataFrame:
    """Cada base con su altura de antes, de dónde sale, la del modelo y cuánto difieren (la de antes menos
    la del modelo). Se niega si una base no está en la descarga o se movió desde entonces."""
    t = bases[["polo", "base", "lat", "lon", "altitud_m", "altitud_fuente"]].merge(dem, on="polo", how="left")
    falta = t["lat_dem"].isna()
    lejos = np.maximum((t["lat"] - t["lat_dem"]).abs(), (t["lon"] - t["lon_dem"]).abs())
    movida = lejos > MISMA_BASE_GRADOS
    if falta.any() or movida.any():
        polos = sorted(t.loc[falta | movida, "polo"].astype(int))
        raise ValueError(f"las bases {polos} no están en la descarga o se movieron: corre descargar_elevacion.py")
    t["altitud_dem_m"] = t["altitud_dem_m"].round()
    t["diferencia_m"] = t["altitud_m"] - t["altitud_dem_m"]
    columnas = ["polo", "base", "lat", "lon", "altitud_m", "altitud_fuente", "altitud_dem_m", "diferencia_m"]
    return t[columnas].sort_values("polo").reset_index(drop=True)


def completar(bases: pd.DataFrame, altitudes: pd.DataFrame) -> pd.DataFrame:
    """Las bases con la altura que va a los artefactos: la de OpenStreetMap si la tienen y, si no, la del
    modelo, con su fuente: ``terrain_tiles``. Sin ninguna de las dos, queda la que traían."""
    dem = bases["polo"].map(altitudes.set_index("polo")["altitud_dem_m"])
    manda = (bases["altitud_fuente"] != OSM) & dem.notna()
    return bases.assign(
        altitud_m=bases["altitud_m"].where(~manda, dem),
        altitud_fuente=bases["altitud_fuente"].astype(object).where(~manda, FUENTE),
    )


def _diferencias(filas: pd.DataFrame) -> dict:
    dif = filas["diferencia_m"].abs()
    return {
        "bases": len(filas),
        "mediana": float(dif.median()),
        "p90": float(dif.quantile(0.9)),
        "max": float(dif.max()),
        **{f"mas_de_{m}": int((dif > m).sum()) for m in DIFIERE_M},
    }


def resumen(t: pd.DataFrame) -> dict:
    """Cuántas bases toman la altura del modelo y cuánto difiere de la que tenían."""
    comparadas = t.dropna(subset=["altitud_m", "altitud_dem_m"])
    mas = comparadas.assign(_d=comparadas["diferencia_m"].abs())
    mas = mas.sort_values(["_d", "polo"], ascending=[False, True]).head(5)
    return {
        "fuente": "Terrain Tiles (registro de datos abiertos de AWS), formato skadi: SRTM a un segundo de arco",
        "radio_puntos": RADIO,
        "bases": len(t),
        "completadas": int((t["altitud_m"].isna() & t["altitud_dem_m"].notna()).sum()),
        "reemplazadas": int((t["altitud_m"].notna() & (t["altitud_fuente"] != OSM) & t["altitud_dem_m"].notna()).sum()),
        "sin_altura": int((t["altitud_m"].isna() & t["altitud_dem_m"].isna()).sum()),
        "diferencia_m": {
            fuente: _diferencias(comparadas[comparadas["altitud_fuente"] == fuente])
            for fuente in sorted(comparadas["altitud_fuente"].unique())
        },
        "las_que_mas_difieren": [
            {
                "polo": int(f.polo),
                "base": f.base,
                "altitud_m": int(f.altitud_m),
                "fuente": f.altitud_fuente,
                "altitud_dem_m": int(f.altitud_dem_m),
            }
            for f in mas.itertuples()
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="La altura de cada base según el modelo de elevación.")
    ap.add_argument("--ventanas", type=Path, default=VENTANAS)
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    a = ap.parse_args()
    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    t = tabla(bases, leer_ventanas(a.ventanas))
    for c in ("altitud_m", "altitud_dem_m", "diferencia_m"):
        t[c] = t[c].astype("Int64")
    t.to_csv(a.salida / "altitud_bases.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")
    r = resumen(t)
    (a.salida / "altitud_resumen.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        f"Con la altura del modelo: {r['completadas']} bases que no la tenían y {r['reemplazadas']} que la sacaban de "
        "los lugares cercanos. Cuánto difiere de la que tenían: "
        + "; ".join(
            f"{fuente}, {d['mediana']:.0f} m en la mediana y {d['max']:.0f} como mucho"
            for fuente, d in r["diferencia_m"].items()
        )
    )


if __name__ == "__main__":
    main()

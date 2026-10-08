"""
Clima de cada polo mes a mes y su veredicto de temporada (TA-05 v2).

Fuente: diez años (2016-2025) de clima diario de Open-Meteo en el centro de cada grupo de
TA-01, que baja ``pipeline/adquisicion/descargar_clima_polos.py`` (decisión 0006). Mientras
esa descarga no termina, un polo sin su archivo usa la capa regional de la semana 6
(``deliveries/week06/data/processed/estacionalidad_polo_mes.csv``) y lo dice en ``fuente``.

Un polo puede juntar varios grupos, los que duermen en el mismo pueblo (``grupos`` de
polos_bases.csv). Toma el clima de su grupo con más paradas que ya tenga archivo; si ninguno
lo tiene, la capa regional de su grupo con más paradas.

Por polo y mes, el promedio de los diez años de:
  lluvia_mm              lluvia del mes
  dias_con_lluvia        días con 1 mm o más, la definición de la OMM
  temp_min_c, temp_max_c promedio de las mínimas y de las máximas diarias, llevadas de la
                         altitud del punto de clima a la de la base del polo con el
                         gradiente estándar de la atmósfera (6,5 °C por km)

El veredicto es la regla de la semana 6, ahora con el clima del propio polo:
  absoluto · 150 mm o más en el mes: el cuartil más lluvioso del país;
  relativo · el mes es uno de los 3 más lluviosos del polo y pasa de 50 mm, la mediana
             nacional: por debajo, la lluvia no estorba un viaje en ninguna parte.
  desaconsejado si se cumplen los dos · advertencia si uno · viable si ninguno.

Lo que no se publica, y por qué:
  - Horas de sol. ERA5 no ve la neblina de la costa: da más de 9 horas de sol al día en la
    costa de Lima en julio, cuando el cielo pasa cubierto casi todo el mes.
  - Nieve. Cae en las cumbres, no donde duerme el viajero.

Lee data/externos/clima/crudo/polo_<id>.json y data/procesados/polos_bases.csv.
Escribe data/procesados/clima_polo_mes.csv.

Uso:  python -m pipeline.clima          (después de python -m pipeline.tiempos)
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.maestro import EXTERNOS, PROCESADOS, RAIZ

CRUDO = EXTERNOS / "clima" / "crudo"
REGIONAL = RAIZ / "deliveries" / "week06" / "data" / "processed" / "estacionalidad_polo_mes.csv"
INICIO, FIN = date(2016, 1, 1), date(2025, 12, 31)
DIAS = (FIN - INICIO).days + 1

UMBRAL_MM = 150.0
PISO_MM = 50.0
MESES_LLUVIOSOS = 3
DIA_CON_LLUVIA_MM = 1.0
GRADIENTE_C_POR_M = 0.0065

COLUMNAS = [
    "polo",
    "mes",
    "lluvia_mm",
    "dias_con_lluvia",
    "temp_min_c",
    "temp_max_c",
    "puesto_lluvia",
    "veredicto",
    "fuente",
    "altitud_clima_m",
    "altitud_base_m",
]


def leer_crudo(ruta: Path) -> tuple[pd.DataFrame, float] | None:
    """(clima diario, altitud del punto según Open-Meteo), o None si el archivo no trae
    los diez años completos."""
    if not ruta.exists():
        return None
    try:
        d = json.loads(ruta.read_text(encoding="utf-8"))["open_meteo"]
        diario = pd.DataFrame(d["daily"])
    except (ValueError, KeyError, TypeError):
        return None
    if (
        len(diario) != DIAS
        or diario["time"].iloc[0] != INICIO.isoformat()
        or diario["time"].iloc[-1] != FIN.isoformat()
    ):
        return None
    return diario, float(d["elevation"])


def mensual(diario: pd.DataFrame) -> pd.DataFrame:
    """Promedio de los diez años, mes por mes."""
    t = pd.to_datetime(diario["time"])
    d = diario.assign(anio=t.dt.year, mes=t.dt.month, con_lluvia=diario["precipitation_sum"] >= DIA_CON_LLUVIA_MM)
    por_anio = d.groupby(["anio", "mes"]).agg(
        lluvia_mm=("precipitation_sum", "sum"),
        dias_con_lluvia=("con_lluvia", "sum"),
        temp_min_c=("temperature_2m_min", "mean"),
        temp_max_c=("temperature_2m_max", "mean"),
    )
    return por_anio.groupby("mes").mean().reset_index()


def veredictos(lluvia_mm: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """(puesto de cada mes por lluvia, 1 el más lluvioso; veredicto) para los 12 meses de un polo."""
    puesto = lluvia_mm.rank(ascending=False, method="min").to_numpy().astype(int)
    absoluto = lluvia_mm.to_numpy() >= UMBRAL_MM
    relativo = (puesto <= MESES_LLUVIOSOS) & (lluvia_mm.to_numpy() >= PISO_MM)
    veredicto = np.select([absoluto & relativo, absoluto | relativo], ["desaconsejado", "advertencia"], "viable")
    return puesto, veredicto


def clima_de_polo(polo: int, diario: pd.DataFrame, altitud_clima: float, altitud_base: float | None) -> pd.DataFrame:
    m = mensual(diario)
    ajuste = (
        0.0 if altitud_base is None or np.isnan(altitud_base) else (altitud_clima - altitud_base) * GRADIENTE_C_POR_M
    )
    m["temp_min_c"] += ajuste
    m["temp_max_c"] += ajuste
    m["puesto_lluvia"], m["veredicto"] = veredictos(m["lluvia_mm"])
    return m.assign(polo=polo, fuente="open_meteo_polo", altitud_clima_m=altitud_clima, altitud_base_m=altitud_base)


def clima_regional(polo: int, semana6: pd.DataFrame, altitud_base: float | None) -> pd.DataFrame:
    """La capa de la semana 6 para un polo sin su descarga: lluvia ponderada por las regiones
    del polo y su veredicto; sin días de lluvia ni temperaturas extremas, que no tenía."""
    s = semana6[semana6["POLO"] == polo].sort_values("MES")
    m = pd.DataFrame({"mes": s["MES"].astype(int).to_numpy(), "lluvia_mm": s["precip_mm"].to_numpy()})
    m["puesto_lluvia"] = m["lluvia_mm"].rank(ascending=False, method="min").astype(int)
    return m.assign(
        polo=polo,
        dias_con_lluvia=np.nan,
        temp_min_c=np.nan,
        temp_max_c=np.nan,
        veredicto=s["veredicto"].to_numpy(),
        fuente="region_semana6",
        altitud_clima_m=np.nan,
        altitud_base_m=altitud_base,
    )


def grupos_de(base) -> list[int]:
    """Los grupos de TA-01 que junta un polo, del que tiene más paradas al que tiene menos. Una
    tabla de antes de juntar no los trae: ahí el polo es su único grupo."""
    grupos = getattr(base, "grupos", None)
    return [int(base.polo)] if grupos is None or pd.isna(grupos) else [int(g) for g in str(grupos).split("|")]


def construir(bases: pd.DataFrame, crudo: Path, semana6: pd.DataFrame) -> pd.DataFrame:
    filas = []
    for b in bases.itertuples():
        polo, grupos = int(b.polo), grupos_de(b)
        altitud_base = None if pd.isna(b.altitud_m) else float(b.altitud_m)
        leido = next((clima for g in grupos if (clima := leer_crudo(crudo / f"polo_{g}.json")) is not None), None)
        if leido is not None:
            filas.append(clima_de_polo(polo, *leido, altitud_base))
        else:
            filas.append(clima_regional(grupos[0], semana6, altitud_base).assign(polo=polo))
    return pd.concat(filas, ignore_index=True)[COLUMNAS].sort_values(["polo", "mes"], ignore_index=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Clima por polo y mes con su veredicto de temporada.")
    ap.add_argument("--crudo", type=Path, default=CRUDO)
    ap.add_argument("--bases", type=Path, default=PROCESADOS / "polos_bases.csv")
    ap.add_argument("--regional", type=Path, default=REGIONAL)
    ap.add_argument("--salida", type=Path, default=PROCESADOS / "clima_polo_mes.csv")
    a = ap.parse_args()

    bases = pd.read_csv(a.bases, sep=";", encoding="utf-8-sig")
    semana6 = pd.read_csv(a.regional, sep=";", encoding="utf-8-sig")
    clima = construir(bases, a.crudo, semana6)
    clima.to_csv(a.salida, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n", float_format="%.1f")
    propios = clima.loc[clima["fuente"] == "open_meteo_polo", "polo"].nunique()
    print(f"{clima['polo'].nunique()} polos · {propios} con su propio clima, el resto con el regional de la semana 6")
    print(clima["veredicto"].value_counts().to_string())


if __name__ == "__main__":
    main()

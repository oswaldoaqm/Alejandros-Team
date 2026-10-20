"""
El viaje en avión de cada ciudad de origen a cada polo, de puerta a puerta (decisión 0016).

Las rutas son los vuelos regulares que salen de Lima (``pipeline/referencia/rutas_aereas.csv``):
entre dos aeropuertos que no son Lima se vuela con escala en Lima. Las rutas interregionales sin
escala, como Arequipa–Cusco, todavía no entran: las fuentes que las nombran son de 2020 a 2022 y
no se pudo confirmar que sigan.

De puerta a puerta, la ida en avión suma:

1. el camino por tierra del origen a un aeropuerto, sobre la misma red que el resto del motor;
2. dos horas antes del vuelo, lo que piden los aeropuertos para un vuelo nacional;
3. la duración del vuelo o, con escala en Lima, la de los dos y dos horas entre ellos;
4. media hora para salir del aeropuerto, sin maleta en bodega;
5. el camino por tierra del aeropuerto de llegada a la base del polo.

Se prueban todos los aeropuertos en las dos puntas y queda el más rápido. La vuelta es la misma
al revés. Si conviene volar o ir por tierra lo decide el motor (``dreemgo/motor/viaje.py``).

El pasaje de cada ruta es una banda en soles: desde la tarifa más baja publicada hasta 2,2 veces
esa, con 1,5 veces como valor central. Esos factores salen de los rangos típicos de una sola vía
que publica Kayak para Lima–Cusco, Lima–Arequipa y Lima–Iquitos: el típico va de 1,1 a 2,3 veces
el más barato. Una ruta sin tarifa publicada que se pueda citar toma la mediana de las demás.

Escribe en data/procesados/:
  vuelos_rutas.csv          cada ruta: minutos de vuelo y la banda del pasaje por tramo, en soles
  vuelos_origen_base.csv    origen → base de cada polo en avión: minutos de puerta a puerta, km por
                            tierra (y cuántos de ellos en tren y en bote), los aeropuertos, los
                            minutos de vuelo, los de tierra en cada punta y los km hasta el
                            aeropuerto de salida

Los caminos por tierra son obra derivada de OpenStreetMap: ODbL 1.0, © colaboradores de
OpenStreetMap.

Uso:  python -m pipeline.vuelos       (después de python -m pipeline.tiempos)
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import red_calibracion as calibracion
from pipeline.maestro import PROCESADOS, REFERENCIA
from pipeline.red_vial import Ruteador, minutos_por_arista
from pipeline.tiempos import OSM, _escribir, _puerta_a_puerta, red_en_cache, ritmos_fijos

HUB = "LIM"
LLEGAR_ANTES_MIN = 120  # Lima Airport Partners: dos horas antes para un vuelo nacional
SALIR_DEL_AEROPUERTO_MIN = 30  # supuesto del equipo: bajar del avión y salir, sin maleta en bodega
ESCALA_MIN = 120  # supuesto del equipo: entre dos vuelos en Lima, con la espera
TIPO_DE_CAMBIO = 3.436  # soles por dólar, BCRP, cierre del 5 de octubre de 2026
TARIFA_CENTRAL = 1.5  # veces la tarifa más baja publicada
TARIFA_MAXIMA = 2.2


def leer_aeropuertos() -> pd.DataFrame:
    return pd.read_csv(REFERENCIA / "aeropuertos.csv", sep=";")


def rutas_en_soles(rutas: pd.DataFrame) -> pd.DataFrame:
    """La banda del pasaje por tramo, en soles. Una ruta sin tarifa publicada toma la mediana."""
    desde = rutas["tarifa_desde_usd"].astype(float)
    sin_tarifa = desde.isna()
    minima = desde.fillna(desde.median()) * TIPO_DE_CAMBIO
    return rutas[["desde", "hasta", "minutos"]].assign(
        tarifa_minima=minima.round(0),
        tarifa_central=(minima * TARIFA_CENTRAL).round(0),
        tarifa_maxima=(minima * TARIFA_MAXIMA).round(0),
        tarifa_publicada=~sin_tarifa,
        fuente=rutas["fuente_tarifa"],
    )


def vuelos_entre(rutas: pd.DataFrame, codigos: list[str]) -> tuple[np.ndarray, list[list[list[str]]]]:
    """(minutos de vuelo, aeropuertos del camino) entre cada par de aeropuertos: directo si una
    punta es Lima, con escala en Lima si las dos tienen ruta a Lima, infinito si no se puede o si
    son el mismo aeropuerto. Los minutos con escala cuentan los dos vuelos y la escala."""
    a_lima = dict(zip(rutas["hasta"], rutas["minutos"].astype(float), strict=True))
    a_lima[HUB] = 0.0
    n = len(codigos)
    minutos = np.full((n, n), np.inf)
    caminos: list[list[list[str]]] = [[[] for _ in range(n)] for _ in range(n)]
    for i, a in enumerate(codigos):
        for j, b in enumerate(codigos):
            if a == b or a not in a_lima or b not in a_lima:
                continue
            if HUB in (a, b):
                minutos[i, j] = a_lima[a] + a_lima[b]
                caminos[i][j] = [a, b]
            else:
                minutos[i, j] = a_lima[a] + ESCALA_MIN + a_lima[b]
                caminos[i][j] = [a, HUB, b]
    return minutos, caminos


def por_tierra(ruteador: Ruteador, parametros: dict, desde: pd.DataFrame, hacia: pd.DataFrame) -> dict[str, np.ndarray]:
    """Minutos y km de puerta a puerta por la red, y cuántos de esos km van en tren y en bote, de
    cada punto de ``desde`` a cada uno de ``hacia``; nan donde no hay camino."""
    v_desde, m_desde, c_desde = ruteador.ubicar(desde["lat"].to_numpy(), desde["lon"].to_numpy())
    v_hacia, m_hacia, c_hacia = ruteador.ubicar(hacia["lat"].to_numpy(), hacia["lon"].to_numpy())
    minutos, km, km_tren, km_bote = ruteador.entre(v_desde, v_hacia, margen=None, por_medio=True)
    puntas = (c_desde[:, None] > 0).astype(int) + (c_hacia[None, :] > 0)
    minutos, km = _puerta_a_puerta(minutos, km, m_desde[:, None] + m_hacia[None, :], parametros, puntas)
    sin_camino = ~np.isfinite(minutos)
    return {
        "minutos": np.where(sin_camino, np.nan, minutos),
        "km": np.where(sin_camino, np.nan, km),
        "km_tren": np.where(sin_camino, np.nan, km_tren),
        "km_bote": np.where(sin_camino, np.nan, km_bote),
    }


def mejores_vuelos(
    origenes: pd.DataFrame,
    bases: pd.DataFrame,
    aeropuertos: pd.DataFrame,
    rutas: pd.DataFrame,
    ida: dict[str, np.ndarray],
    llegada: dict[str, np.ndarray],
) -> pd.DataFrame:
    """El viaje en avión más rápido de cada origen a cada base. ``ida`` va del origen a cada
    aeropuerto y ``llegada`` de cada aeropuerto a cada base, los dos de puerta a puerta."""
    codigos = aeropuertos["iata"].tolist()
    vuelo, caminos = vuelos_entre(rutas, codigos)
    en_aeropuertos = vuelo + LLEGAR_ANTES_MIN + SALIR_DEL_AEROPUERTO_MIN
    g_ida = np.nan_to_num(ida["minutos"], nan=np.inf)
    g_llegada = np.nan_to_num(llegada["minutos"], nan=np.inf)
    filas = []
    for o, origen in enumerate(origenes["id"]):
        # total[a1, a2, b] = tierra hasta a1 + aeropuertos y vuelos + tierra desde a2 hasta b
        total = g_ida[o][:, None, None] + en_aeropuertos[:, :, None] + g_llegada[None, :, :]
        plano = total.reshape(-1, len(bases))
        mejor = np.argmin(plano, axis=0)
        for b, polo in enumerate(bases["polo"]):
            minutos = plano[mejor[b], b]
            if not np.isfinite(minutos):
                continue
            a1, a2 = divmod(int(mejor[b]), len(codigos))
            filas.append(
                {
                    "origen": origen,
                    "polo": int(polo),
                    "minutos": float(minutos),
                    "km": ida["km"][o, a1] + llegada["km"][a2, b],
                    "km_tren": ida["km_tren"][o, a1] + llegada["km_tren"][a2, b],
                    "km_bote": ida["km_bote"][o, a1] + llegada["km_bote"][a2, b],
                    "aeropuertos": "-".join(caminos[a1][a2]),
                    "minutos_vuelo": float(vuelo[a1, a2]),
                    "minutos_hasta_aeropuerto": float(ida["minutos"][o, a1]),
                    "km_hasta_aeropuerto": float(ida["km"][o, a1]),
                    "minutos_desde_aeropuerto": float(llegada["minutos"][a2, b]),
                }
            )
    return pd.DataFrame(filas)


def main() -> None:
    ap = argparse.ArgumentParser(description="Calcula el viaje en avión de cada origen a cada polo.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--maestro", type=Path, default=PROCESADOS / "maestro_v3.csv")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem", help="dónde guarda pyosmium los nodos al leer (ver leer_red)")
    a = ap.parse_args()

    # La misma red y la misma calibración que pipeline.tiempos: los caminos por tierra hasta y
    # desde los aeropuertos se miden igual que los demás.
    red, osm, _ = red_en_cache(a.pbf, a.indice)
    maestro = pd.read_csv(a.maestro, sep=";", encoding="utf-8-sig", dtype={"dias": str})
    pares, _ = calibracion.pares_de_calibracion(maestro, osm.capitales, osm.lugares)
    parametros, _ = calibracion.calibrar(red, pares)
    parametros = {**parametros, **ritmos_fijos()}
    ruteador = Ruteador(red, minutos_por_arista(red, parametros))

    origenes = pd.read_csv(REFERENCIA / "origenes.csv", sep=";")
    bases = pd.read_csv(a.salida / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    aeropuertos = leer_aeropuertos()
    rutas = pd.read_csv(REFERENCIA / "rutas_aereas.csv", sep=";")

    ida = por_tierra(ruteador, parametros, origenes, aeropuertos)
    llegada = por_tierra(ruteador, parametros, aeropuertos, bases)
    vuelos = mejores_vuelos(origenes, bases, aeropuertos, rutas, ida, llegada)
    _escribir(rutas_en_soles(rutas), a.salida / "vuelos_rutas.csv")
    _escribir(vuelos, a.salida / "vuelos_origen_base.csv")
    print(f"{len(vuelos)} viajes en avión de {len(origenes)} orígenes a {len(bases)} bases · escrito en {a.salida}")


if __name__ == "__main__":
    main()

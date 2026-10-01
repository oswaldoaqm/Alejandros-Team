"""
Dónde se duerme en cada polo: la base de la que salen los paseos de cada día.

El motor arma cada viaje como una estrella: el viajero llega a un pueblo, duerme ahí y
cada día sale a visitar paradas y vuelve. Ese pueblo es la base del polo. Se elige entre
los lugares poblados de OpenStreetMap (ciudades, pueblos, barrios y caseríos) por lo que
costaría salir de ahí cada día y por lo que se sabe de dónde dormir:

    costo = minutos por carretera a cada parada, en promedio pesado por su jerarquía
            − 5 minutos por cada vez que se duplica el hospedaje registrado a menos de
              3 km, hasta 25
            + un recargo si no hay ninguno registrado

- El peso de una parada es 1 + su jerarquía (2,5 si MINCETUR no la asignó, el medio de
  la escala): la base queda cerca de lo que más vale ver.
- El hospedaje es lo que OSM registra como hotel, hostal, casa de huéspedes, motel o
  alojamiento turístico. Con 5 minutos por duplicación, un pueblo con 31 hospedajes le
  gana a un caserío con uno si no queda más de 20 minutos más lejos, en promedio, de cada
  parada: dormir donde hay servicios vale más que ahorrar unos minutos por paseo. Sin esa
  preferencia, el polo de Machu Picchu dormía en un caserío y no en Machupicchu Pueblo.
  Pasados los 31, más hoteles ya no mueven la base: si no, una gran ciudad atraía la base
  de polos que quedan a más de dos horas de ella.
- Un lugar sin hospedaje registrado paga según su tamaño: en una ciudad el mapa omite
  hoteles que sí existen (nada), en un pueblo o un barrio puede que haya (15 minutos) y en
  un caserío lo normal es que no haya (45 minutos). Una capital de distrito paga como un
  pueblo aunque OSM la marque caserío.
- Un barrio o caserío a menos de 8 km de una ciudad, o de 4 km de un pueblo, es parte de
  ese lugar y no compite con él: la base se llama Cusco y no Wanchaq ni San Sebastián.

Los minutos, los recargos y los radios son supuestos del producto, no mediciones; por eso
están juntos aquí, a la vista.

Los minutos salen de la misma búsqueda que da los tiempos entre paradas
(``pipeline/tiempos.py``). Este módulo solo decide, así que se prueba sin la red.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from pipeline.red_vial import cercanos, haversine_m

LUGAR = {0: "ciudad", 1: "pueblo", 2: "barrio", 3: "caserío"}  # rango de red_vial.leer_lugares
RADIO_HOSPEDAJE_M = 3_000
BONO_POR_DUPLICAR_MIN = 5.0
BONO_MAX_MIN = 25.0  # 5 duplicaciones: con más de 31 hospedajes, más hoteles no mueven la base
RECARGO_SIN_HOSPEDAJE_MIN = {0: 0.0, 1: 15.0, 2: 15.0, 3: 45.0}
RECARGO_CAPITAL_MIN = 15.0
MISMO_LUGAR_M = {0: 8_000, 1: 4_000}  # alrededor de una ciudad y de un pueblo
JERARQUIA_SIN_ASIGNAR = 1.5  # solo para pesar: el recurso la sigue teniendo en null
SIN_CAMINO_MIN = 600.0  # una parada sin camino desde un candidato cuenta como diez horas
MINUTOS_POR_KM_EN_LINEA_RECTA = 2.0  # solo para un polo sin ninguna parada junto a la red
RADIO_ALTITUD_M = 2_000


def candidatos(lugares: pd.DataFrame, capitales: pd.DataFrame, hospedajes: pd.DataFrame) -> pd.DataFrame:
    """Los lugares de OSM que pueden ser base, con los minutos que suma o resta lo que se
    sabe de su hospedaje (``ajuste_min``).

    Columnas: nombre, lat, lon, rango, lugar, capital_de_distrito, hospedajes_osm (a menos
    de 3 km), ajuste_min y altitud_osm_m. En un orden estable (más grande, con más
    hospedaje, por nombre): entre dos con el mismo costo gana el primero."""
    c = lugares[lugares["rango"].isin(list(LUGAR))].reset_index(drop=True)
    absorbido = np.zeros(len(c), dtype=bool)
    for rango, radio in MISMO_LUGAR_M.items():
        grandes = c[c["rango"] == rango]
        absorbido |= np.array([len(v) > 0 for v in cercanos(c["lat"], c["lon"], grandes["lat"], grandes["lon"], radio)])
    c = c[(c["rango"] <= 1) | ~absorbido].copy()
    capital = set(zip(capitales["lat"].round(6), capitales["lon"].round(6), strict=True))
    c["capital_de_distrito"] = [
        (la, lo) in capital for la, lo in zip(c["lat"].round(6), c["lon"].round(6), strict=True)
    ]
    vecinos = cercanos(c["lat"], c["lon"], hospedajes["lat"], hospedajes["lon"], RADIO_HOSPEDAJE_M)
    c["hospedajes_osm"] = [len(v) for v in vecinos]
    recargo = c["rango"].map(RECARGO_SIN_HOSPEDAJE_MIN).to_numpy()
    recargo = np.where(c["capital_de_distrito"], np.minimum(recargo, RECARGO_CAPITAL_MIN), recargo)
    bono = np.minimum(BONO_POR_DUPLICAR_MIN * np.log2(1 + c["hospedajes_osm"].to_numpy()), BONO_MAX_MIN)
    c["ajuste_min"] = np.where(c["hospedajes_osm"] > 0, -bono, recargo)
    c["lugar"] = c["rango"].map(LUGAR)
    c = c.rename(columns={"altitud_m": "altitud_osm_m"}).sort_values(
        ["rango", "hospedajes_osm", "nombre", "lat", "lon"], ascending=[True, False, True, True, True]
    )
    columnas = ["nombre", "lat", "lon", "rango", "lugar", "capital_de_distrito", "hospedajes_osm", "ajuste_min"]
    return c[[*columnas, "altitud_osm_m"]].reset_index(drop=True)


def pesos(jerarquia: pd.Series) -> np.ndarray:
    """Cuánto pesa cada parada al elegir la base: 1 + su jerarquía."""
    return 1.0 + jerarquia.astype(float).fillna(JERARQUIA_SIN_ASIGNAR).to_numpy()


def costos(minutos: np.ndarray, peso: np.ndarray, ajuste: np.ndarray) -> np.ndarray:
    """El costo de cada candidato (ver el módulo), o ``inf`` si no llega a ninguna parada.

    ``minutos`` es paradas × candidatos, de puerta a puerta, con ``inf`` donde no hay camino."""
    hay_camino = np.isfinite(minutos)
    media = peso @ np.where(hay_camino, minutos, SIN_CAMINO_MIN) / peso.sum()
    return np.where(hay_camino.any(axis=0), media + ajuste, np.inf)


def elegir(minutos: np.ndarray, peso: np.ndarray, ajuste: np.ndarray) -> int | None:
    """Índice del candidato de menor costo; None si ninguno llega a alguna parada.
    Entre iguales, el primero."""
    c = costos(minutos, peso, ajuste)
    return int(np.argmin(c)) if np.isfinite(c).any() else None


def elegir_en_linea_recta(lat, lon, peso, cand_lat, cand_lon, ajuste) -> int:
    """Para un polo sin ninguna parada junto a la red: el mismo costo, con la distancia en
    línea recta en vez del camino."""
    km = haversine_m(np.asarray(lat)[:, None], np.asarray(lon)[:, None], cand_lat[None, :], cand_lon[None, :]) / 1000
    return int(np.argmin(peso @ (km * MINUTOS_POR_KM_EN_LINEA_RECTA) / peso.sum() + ajuste))


def altitud(bases: pd.DataFrame, recursos: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """(altitud en metros, de dónde sale) de cada base.

    La que declara el nodo de OSM (``ele``) o, si no la tiene, la mediana de los recursos
    del inventario a menos de 2 km: en un pueblo son su plaza, su iglesia y su fiesta, que
    están a su altura. Sin ninguna de las dos, null."""
    con = recursos.dropna(subset=["lat", "lon", "altitud_m"])
    vecinos = cercanos(
        bases["lat"].to_numpy(), bases["lon"].to_numpy(), con["lat"].to_numpy(), con["lon"].to_numpy(), RADIO_ALTITUD_M
    )
    alt = con["altitud_m"].to_numpy()
    mediana = pd.Series([float(np.median(alt[v])) if len(v) else np.nan for v in vecinos], index=bases.index)
    osm = bases["altitud_osm_m"]
    fuente = np.where(osm.notna(), "osm", np.where(mediana.notna(), "recursos_a_2_km", ""))
    return osm.fillna(mediana).round(), pd.Series(fuente, index=bases.index)

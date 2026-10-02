"""
Tiempos de viaje que usa el motor, sobre la red de OpenStreetMap: vías, tren y botes.

1. Arma la red desde el extracto de Geofabrik (``pipeline/red_vial.py``) o la toma del
   caché si el extracto no cambió.
2. Calibra las velocidades de las vías con los recorridos de las fichas
   (``pipeline/red_calibracion.py``) y les suma los ritmos del tren y del bote
   (``pipeline/referencia/ritmos_fijos.csv``).
3. Recorre cada polo con una sola búsqueda desde sus paradas, que da a la vez:
   - los tiempos entre sus paradas, en los dos sentidos;
   - el pueblo donde se duerme, la base (``pipeline/bases.py``);
   - los tiempos de la base a cada parada. Son los mismos de vuelta: en la red cada tramo
     cuesta lo mismo en los dos sentidos.
4. Calcula los tiempos de cada una de las 24 ciudades de origen a cada parada y a cada base.

Cada tiempo es de puerta a puerta: el camino más rápido por la red (vías, tren y botes),
lo que falta de cada punta a la red y los minutos fijos de cada traslado. La caminata
final que registra la ficha (``caminata_min`` del maestro) va aparte.

Escribe en data/procesados/:
  red_calibracion.json             parámetros y error medido por validación cruzada
  red_calibracion_recorridos.csv   cada recorrido de ficha usado, con el tiempo de la red
  tiempos_origen.csv               origen → parada: minutos y km (vacío si no hay camino)
  tiempos_polo.csv                 parada → parada dentro de cada polo
  polos_bases.csv                  la base de cada polo
  tiempos_base.csv                 base → cada parada de su polo
  tiempos_origen_base.csv          origen → base de cada polo
  red_paradas.csv                  a cuántos metros de la red queda cada parada

Todo lo que sale de la red es obra derivada de OpenStreetMap: ODbL 1.0, © colaboradores de
OpenStreetMap.

Uso:  python -m pipeline.tiempos                    (después de python -m pipeline.maestro)
      python -m pipeline.tiempos --indice "sparse_file_array,nodos.idx"   con poca memoria
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import bases as bases_
from pipeline import red_calibracion as calibracion
from pipeline.maestro import EXTERNOS, PROCESADOS, REFERENCIA
from pipeline.red_vial import (
    Red,
    Ruteador,
    leer_capitales,
    leer_hospedajes,
    leer_lugares,
    leer_red,
    minutos_por_arista,
)

OSM = EXTERNOS / "osm"
CACHE = 4  # sube cuando cambia lo que se guarda de la red, para no leer un caché viejo
LEJOS_DE_LA_RED_M = 5_000  # una parada más lejos que esto de la red no se rutea
CANDIDATOS_MARGEN_GRADOS = 1.0  # los pueblos que pueden ser base: a menos de ~110 km de las paradas


@dataclass
class Osm:
    """Lo que se lee del extracto, además de la red."""

    capitales: pd.DataFrame
    lugares: pd.DataFrame
    hospedajes: pd.DataFrame


def red_en_cache(pbf: Path, indice: str) -> tuple[Red, Osm, dict]:
    """La red, las capitales, los pueblos y los hospedajes del extracto; cada uno se rehace
    si cambia el MD5 del extracto o si falta su archivo."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    etiqueta = manifiesto["md5"][:8]

    def ruta(nombre: str, extension: str) -> Path:
        return pbf.parent / f"{nombre}_{etiqueta}_v{CACHE}.{extension}"

    if not ruta("red_vial", "npz").exists():
        inicio = time.time()
        red = leer_red(pbf, indice)
        red.fecha_osm = manifiesto["datos_last_modified"]
        red.guardar(ruta("red_vial", "npz"))
        print(f"Red armada en {time.time() - inicio:.0f} s: {red.vertices:,} vértices, {red.aristas:,} aristas")
    tablas = {}
    for nombre, leer in (
        ("capitales", leer_capitales),
        ("lugares", leer_lugares),
        ("hospedajes", lambda p: leer_hospedajes(p, indice)),
    ):
        if not ruta(nombre, "csv").exists():
            leer(pbf).to_csv(ruta(nombre, "csv"), index=False)
        tablas[nombre] = pd.read_csv(ruta(nombre, "csv"))
    return Red.cargar(ruta("red_vial", "npz")), Osm(**tablas), manifiesto


def ritmos_fijos() -> dict[str, float]:
    """Minutos por km del tren y del bote, y los del trasbordo (pipeline/referencia/ritmos_fijos.csv)."""
    tabla = pd.read_csv(REFERENCIA / "ritmos_fijos.csv", sep=";")
    return dict(zip(tabla["clase"], tabla["min_por_km"].astype(float), strict=True))


def _puerta_a_puerta(minutos, km, metros_a_la_red, parametros) -> tuple[np.ndarray, np.ndarray]:
    """Suma a cada camino lo que falta de cada punta a la red y los minutos fijos del traslado."""
    fuera_km = 1.3 * metros_a_la_red / 1000  # por un camino sin mapear, como en la calibración
    minutos = minutos + parametros["por_viaje"] + fuera_km * parametros["trocha"]
    return minutos, km + fuera_km


def _sin_ruta_a_nan(tabla: pd.DataFrame, lejos: np.ndarray) -> pd.DataFrame:
    """Vacía minutos y km donde no hay camino o una punta queda lejos de la red."""
    tabla.loc[lejos | ~np.isfinite(tabla["minutos"].to_numpy()), ["minutos", "km"]] = np.nan
    return tabla


def recorrer_polos(
    ruteador: Ruteador, parametros: dict, paradas: pd.DataFrame, candidatos: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(tiempos entre paradas, base de cada polo, tiempos de la base a cada parada).

    ``paradas``: codigo, polo, lat, lon y jerarquia. ``candidatos``: los de
    ``bases.candidatos``. Una sola búsqueda por polo, desde sus paradas hasta sus paradas
    y los candidatos cercanos; solo las paradas obligan a buscar en toda la red si dentro
    del rectángulo del polo no hay camino (ver ``Ruteador.entre``)."""
    v, m = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy())
    vc, mc = ruteador.ubicar(candidatos["lat"].to_numpy(), candidatos["lon"].to_numpy())
    clat, clon = candidatos["lat"].to_numpy(), candidatos["lon"].to_numpy()
    junto_a_la_red = mc <= LEJOS_DE_LA_RED_M
    pares, elegidas, desde_base = [], [], []
    for polo, grupo in paradas[paradas["polo"] >= 0].groupby("polo"):
        i = grupo.index.to_numpy()
        codigos, n = grupo["codigo"].to_numpy(), len(i)
        margen = CANDIDATOS_MARGEN_GRADOS
        cerca = np.flatnonzero(
            junto_a_la_red
            & (clat >= grupo["lat"].min() - margen)
            & (clat <= grupo["lat"].max() + margen)
            & (clon >= grupo["lon"].min() - margen)
            & (clon <= grupo["lon"].max() + margen)
        )
        obligatorio = np.r_[np.ones(n, dtype=bool), np.zeros(len(cerca), dtype=bool)]
        minutos, km = ruteador.entre(v[i], np.r_[v[i], vc[cerca]], obligatorios=obligatorio)

        # Entre paradas: cada fila es desde, cada columna hasta.
        if n >= 2:
            mp, kp = _puerta_a_puerta(minutos[:, :n], km[:, :n], m[i][:, None] + m[i][None, :], parametros)
            desde, hasta = np.nonzero(~np.eye(n, dtype=bool))
            pares.append(
                pd.DataFrame(
                    {
                        "polo": polo,
                        "desde": codigos[desde],
                        "hasta": codigos[hasta],
                        "minutos": mp[desde, hasta],
                        "km": kp[desde, hasta],
                    }
                )
            )

        # La base: entre los candidatos, la de menor costo vista desde las paradas junto a la red.
        mb, kb = _puerta_a_puerta(minutos[:, n:], km[:, n:], m[i][:, None] + mc[cerca][None, :], parametros)
        en_red = m[i] <= LEJOS_DE_LA_RED_M
        peso = bases_.pesos(grupo["jerarquia"])
        ajuste = candidatos["ajuste_min"].to_numpy()
        j = bases_.elegir(mb[en_red], peso[en_red], ajuste[cerca]) if en_red.any() else None
        if j is not None:
            elegido, criterio = cerca[j], "carretera"
            mbj, kbj = mb[:, j], kb[:, j]
        else:
            lat, lon = grupo["lat"].to_numpy(), grupo["lon"].to_numpy()
            elegido = bases_.elegir_en_linea_recta(lat, lon, peso, clat, clon, ajuste)
            criterio = "linea_recta"
            mbj, kbj = np.full(n, np.inf), np.full(n, np.inf)
        con_camino = np.isfinite(mbj) & en_red
        c = candidatos.iloc[elegido]
        elegidas.append(
            {
                "polo": polo,
                "base": c["nombre"],
                "lat": c["lat"],
                "lon": c["lon"],
                "lugar": c["lugar"],
                "capital_de_distrito": bool(c["capital_de_distrito"]),
                "hospedajes_osm": int(c["hospedajes_osm"]),
                "altitud_osm_m": c["altitud_osm_m"],
                "criterio": criterio,
                "paradas": n,
                "paradas_con_camino": int(con_camino.sum()),
                "minutos_medios": round(float(peso[con_camino] @ mbj[con_camino] / peso[con_camino].sum()), 1)
                if con_camino.any()
                else np.nan,
            }
        )
        desde_base.append(pd.DataFrame({"polo": polo, "codigo": codigos, "minutos": mbj, "km": kbj}))

    lejos = set(paradas.loc[m > LEJOS_DE_LA_RED_M, "codigo"])
    pares = (
        pd.concat(pares, ignore_index=True)
        if pares
        else pd.DataFrame(columns=["polo", "desde", "hasta", "minutos", "km"])
    )
    pares = _sin_ruta_a_nan(pares, (pares["desde"].isin(lejos) | pares["hasta"].isin(lejos)).to_numpy())
    desde_base = pd.concat(desde_base, ignore_index=True)
    desde_base = _sin_ruta_a_nan(desde_base, desde_base["codigo"].isin(lejos).to_numpy())
    return pares, pd.DataFrame(elegidas), desde_base


def tiempos_desde_origenes(ruteador, parametros, origenes, paradas, bases) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(origen → cada parada, origen → la base de cada polo): minutos y km de puerta a puerta,
    vacíos si no hay camino. Una búsqueda en toda la red por ciudad de origen."""
    v_origen, m_origen = ruteador.ubicar(origenes["lat"].to_numpy(), origenes["lon"].to_numpy())
    v_parada, m_parada = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy())
    v_base, m_base = ruteador.ubicar(bases["lat"].to_numpy(), bases["lon"].to_numpy())
    minutos, km = ruteador.entre(v_origen, np.r_[v_parada, v_base], margen=None)
    n = len(paradas)
    a_paradas, a_bases = [], []
    for i, origen in enumerate(origenes["id"]):
        mi, ki = _puerta_a_puerta(minutos[i, :n], km[i, :n], m_origen[i] + m_parada, parametros)
        a_paradas.append(
            pd.DataFrame({"origen": origen, "codigo": paradas["codigo"].to_numpy(), "minutos": mi, "km": ki})
        )
        mi, ki = _puerta_a_puerta(minutos[i, n:], km[i, n:], m_origen[i] + m_base, parametros)
        a_bases.append(pd.DataFrame({"origen": origen, "polo": bases["polo"].to_numpy(), "minutos": mi, "km": ki}))
    a_paradas = pd.concat(a_paradas, ignore_index=True)
    a_paradas = _sin_ruta_a_nan(a_paradas, np.tile(m_parada > LEJOS_DE_LA_RED_M, len(origenes)))
    a_bases = pd.concat(a_bases, ignore_index=True)
    sin_camino = np.tile((bases["criterio"] != "carretera").to_numpy(), len(origenes))
    return a_paradas, _sin_ruta_a_nan(a_bases, sin_camino)


def _escribir(tabla: pd.DataFrame, ruta: Path) -> None:
    """Minutos y km con un decimal; la latitud y la longitud con seis (unos 10 cm): con uno
    serían 11 km."""
    coordenadas = {c: tabla[c].map(lambda x: "" if pd.isna(x) else f"{x:.6f}") for c in ("lat", "lon") if c in tabla}
    tabla = tabla.assign(**coordenadas)
    tabla.to_csv(ruta, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n", float_format="%.1f")


def main() -> None:
    ap = argparse.ArgumentParser(description="Calibra la red y calcula los tiempos de viaje por vías, tren y botes.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--maestro", type=Path, default=PROCESADOS / "maestro_v3.csv")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem", help="dónde guarda pyosmium los nodos al leer (ver leer_red)")
    a = ap.parse_args()

    red, osm, manifiesto = red_en_cache(a.pbf, a.indice)
    maestro = pd.read_csv(a.maestro, sep=";", encoding="utf-8-sig", dtype={"dias": str})

    pares, cuentas = calibracion.pares_de_calibracion(maestro, osm.capitales, osm.lugares)
    parametros, recorridos = calibracion.calibrar(red, pares)
    informe = calibracion.informe(recorridos, parametros, cuentas)
    informe = {"osm": {"datos": manifiesto["datos_last_modified"], "md5": manifiesto["md5"]}, **informe}
    (a.salida / "red_calibracion.json").write_text(
        json.dumps(informe, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    recorridos = recorridos.assign(
        minutos_red=calibracion.predecir(recorridos, parametros), misma_distancia=calibracion.coinciden(recorridos)
    )
    _escribir(
        recorridos[
            [
                "codigo",
                "acceso_desde",
                "acceso_km",
                "acceso_min",
                "ultimo_medio",
                "km_red",
                "minutos_red",
                "misma_distancia",
            ]
        ].rename(columns={"acceso_km": "km_ficha", "acceso_min": "minutos_ficha"}),
        a.salida / "red_calibracion_recorridos.csv",
    )
    cv = informe["validacion_cruzada"]
    error = f"error medio {cv['error_medio']:.0%}, mediano {cv['error_mediano']:.0%}"
    print(f"Calibración con {cv['recorridos']} recorridos de fichas · {error} (validación cruzada)")

    parametros = {**parametros, **ritmos_fijos()}  # la calibración es solo de las vías
    ruteador = Ruteador(red, minutos_por_arista(red, parametros))
    paradas = maestro.loc[maestro["es_parada"].astype(bool), ["codigo", "polo", "lat", "lon", "jerarquia"]]
    paradas = paradas.reset_index(drop=True)
    candidatos = bases_.candidatos(osm.lugares, osm.capitales, osm.hospedajes)
    pares, bases, desde_base = recorrer_polos(ruteador, parametros, paradas, candidatos)
    bases["altitud_m"], bases["altitud_fuente"] = bases_.altitud(bases, maestro)
    origenes = pd.read_csv(REFERENCIA / "origenes.csv", sep=";")
    a_paradas, a_bases = tiempos_desde_origenes(ruteador, parametros, origenes, paradas, bases)

    _escribir(a_paradas, a.salida / "tiempos_origen.csv")
    _escribir(pares, a.salida / "tiempos_polo.csv")
    _escribir(bases.drop(columns="altitud_osm_m"), a.salida / "polos_bases.csv")
    _escribir(desde_base, a.salida / "tiempos_base.csv")
    _escribir(a_bases, a.salida / "tiempos_origen_base.csv")
    _, metros = ruteador.ubicar(paradas["lat"].to_numpy(), paradas["lon"].to_numpy())
    _escribir(
        paradas[["codigo", "polo"]].assign(
            metros_a_la_red=np.round(metros).astype(int), lejos_de_la_red=metros > LEJOS_DE_LA_RED_M
        ),
        a.salida / "red_paradas.csv",
    )
    print(f"Escrito en {a.salida}")


if __name__ == "__main__":
    main()

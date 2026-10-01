"""
Calibra las velocidades de la red vial con los recorridos que publican las fichas.

Cada ficha dice cómo se llega al recurso: desde qué distrito, cuántos kilómetros y
cuántos minutos (``acceso_*`` en el maestro). Cuando todo el recorrido es por carretera,
sin caminata, bote ni avión, esa fila es una medición de campo de un viaje real hecha por
quien conoce el lugar: hay unas 2 600.

Para cada una:

1. El inicio es la capital del distrito de partida según OpenStreetMap (el pueblo que el
   límite distrital marca como centro) y el final, la coordenada del recurso.
2. La ruta se calcula por la red con los ritmos del momento, y se anota cuántos km hace
   por cada clase de vía, cuántos sin asfaltar y cuántas curvas.
3. Se ajustan los ritmos (minutos por km de cada clase), los recargos por km sin asfaltar
   y por curvas, y los minutos fijos de cada traslado, para que el tiempo de la red se
   parezca al de la ficha. El ajuste es en escala logarítmica (un error de +20 % pesa lo
   mismo que uno de −20 %), con pérdida robusta para que una ficha con un tipeo no mueva
   todo, y con un ancla suave en valores de partida razonables para que una clase con
   pocos datos no se vaya a los extremos. Se repiten 2 y 3 hasta que las rutas no cambian.

Solo entran los recorridos en que la red y la ficha dan la misma distancia (±50 %): si no,
no describen el mismo camino. Casi siempre es la ficha: el tramo empieza en otra ciudad
aunque el campo "desde" diga el distrito del recurso.

El error se mide con validación cruzada por distrito de partida: se calibra sin un grupo
de distritos y se mide en ellos, así la cifra no sale de los mismos datos del ajuste.

Uso:  python -m pipeline.tiempos     (calibra y después calcula las tablas de tiempos)
"""

from __future__ import annotations

import re
import unicodedata

import numpy as np
import pandas as pd

from pipeline.red_vial import CLASES, CURVAS_TOPE, Red, Ruteador, haversine_m, minutos_por_arista

# Valores de partida, en minutos por km: una red rural de montaña, no una autopista europea.
RITMO_INICIAL = {
    "autopista": 60 / 80,
    "troncal": 60 / 60,
    "primaria": 60 / 50,
    "secundaria": 60 / 40,
    "terciaria": 60 / 35,
    "local": 60 / 25,
    "trocha": 60 / 20,
    "balsa": 6.0,  # 10 km/h; no se calibra: casi ninguna ruta la usa
}
INICIALES = {**RITMO_INICIAL, "sin_asfaltar": 0.6, "curvas": 0.15, "por_viaje": 5.0}
PARAMETROS = [*CLASES[:-1], "sin_asfaltar", "curvas", "por_viaje"]
ANCLA = 0.3  # peso del valor de partida frente a los datos, en escala logarítmica
ESCALA_ROBUSTA = 0.2  # error logarítmico desde el que una ficha empieza a pesar menos (±22 %)

KM_MIN, MINUTOS_MIN = 3.0, 5.0  # más corto que esto es casi solo ruido de ubicación y redondeo
VELOCIDAD_FICHA = (5.0, 110.0)  # km/h: fuera de esto, la ficha trae un error de tipeo
KM_COINCIDEN = (0.67, 1.5)  # km de la red / km de la ficha: describen el mismo camino
UBICACION_MAX_KM = 80.0  # la capital elegida no puede estar más lejos de su distrito
ITERACIONES = 3
PLIEGUES = 5
BANDAS_KM = (0, 10, 30, 100, 300, 2_000)


def clave(texto) -> str:
    """Nombre comparable: sin tildes, en minúsculas y sin "Distrito de"."""
    t = unicodedata.normalize("NFKD", str(texto).lower()).encode("ascii", "ignore").decode()
    t = " ".join(re.sub(r"[^a-z0-9]+", " ", t).split())
    return re.sub(r"^distrito (de )?", "", t)


# --- Recorridos de las fichas -------------------------------------------------------------


def recorridos_de_fichas(maestro: pd.DataFrame) -> pd.DataFrame:
    """Recursos con un acceso completo por carretera y la coordenada confiable."""
    m = maestro
    solo_carretera = (
        m["acceso_km"].notna()
        & m["acceso_min"].notna()
        & (m["caminata_min"].fillna(0) == 0)
        & ~m["acceso_acuatico"].astype(bool)
        & ~m["acceso_aereo"].astype(bool)
        & m["lat"].notna()
        & ~m["coordenada_revisar"].astype(bool)
    )
    r = m.loc[solo_carretera, ["codigo", "lat", "lon", "acceso_desde", "acceso_km", "acceso_min", "ultimo_medio"]]
    partes = r["acceso_desde"].str.split("/", expand=True).reindex(columns=range(3))
    r = r.assign(region_desde=partes[0].map(clave), distrito_desde=partes[2].map(clave))
    return r[partes[2].notna()].reset_index(drop=True)


def ubicar_distritos(recorridos, maestro, capitales, lugares) -> pd.DataFrame:
    """Coordenada de partida de cada (región, distrito): la capital de OSM con ese nombre
    más cercana a los recursos del inventario en ese distrito (o, si no tiene, en su
    región). Un pueblo con el mismo nombre solo cuenta si el distrito no tiene capital."""
    m = maestro.dropna(subset=["lat"])
    m = m.assign(k_region=m["region"].map(clave), k_dist=m["distrito"].map(clave))
    ref_distrito = m.groupby(["k_region", "k_dist"])[["lat", "lon"]].median()
    ref_region = m.groupby("k_region")[["lat", "lon"]].median()
    candidatos = pd.concat(
        [
            capitales.assign(k=capitales["distrito"].map(clave), fuente="capital_osm")[["k", "lat", "lon", "fuente"]],
            lugares[lugares["rango"] <= 3].assign(k=lugares["nombre"].map(clave), fuente="pueblo_osm")[
                ["k", "lat", "lon", "fuente"]
            ],
        ]
    )
    por_nombre = dict(tuple(candidatos.groupby("k")))
    filas = []
    for region, distrito in recorridos[["region_desde", "distrito_desde"]].drop_duplicates().itertuples(index=False):
        if (region, distrito) in ref_distrito.index:
            ref = ref_distrito.loc[(region, distrito)]
        elif region in ref_region.index:
            ref = ref_region.loc[region]
        else:
            continue
        c = por_nombre.get(distrito)
        if c is None:
            continue
        km = haversine_m(ref["lat"], ref["lon"], c["lat"].to_numpy(), c["lon"].to_numpy()) / 1000
        dentro = km <= UBICACION_MAX_KM
        capital = dentro & (c["fuente"] == "capital_osm").to_numpy()
        elegibles = np.flatnonzero(capital if capital.any() else dentro)
        if len(elegibles):
            mejor = elegibles[np.argmin(km[elegibles])]
            filas.append((region, distrito, c["lat"].iloc[mejor], c["lon"].iloc[mejor], c["fuente"].iloc[mejor]))
    return pd.DataFrame(filas, columns=["region_desde", "distrito_desde", "lat_desde", "lon_desde", "ubicado_con"])


def pares_de_calibracion(maestro, capitales, lugares) -> tuple[pd.DataFrame, dict[str, int]]:
    """Los recorridos ubicados y plausibles, y cuántos quedan en cada paso."""
    recorridos = recorridos_de_fichas(maestro)
    ubicados = ubicar_distritos(recorridos, maestro, capitales, lugares)
    pares = recorridos.merge(ubicados, on=["region_desde", "distrito_desde"])
    velocidad = pares["acceso_km"] / (pares["acceso_min"] / 60)
    plausibles = pares[
        (pares["acceso_km"] >= KM_MIN) & (pares["acceso_min"] >= MINUTOS_MIN) & velocidad.between(*VELOCIDAD_FICHA)
    ].reset_index(drop=True)
    cuentas = {
        "solo_por_carretera": len(recorridos),
        "distritos_de_partida": int(recorridos[["region_desde", "distrito_desde"]].drop_duplicates().shape[0]),
        "distritos_ubicados": len(ubicados),
        "con_partida_ubicada": len(pares),
        "plausibles": len(plausibles),
    }
    return plausibles, cuentas


# --- Rutas y su composición ---------------------------------------------------------------


def componer(red: Red, ritmos: dict, pares: pd.DataFrame) -> pd.DataFrame:
    """Para cada par (inicio, recurso), la ruta más rápida con ``ritmos`` y cuántos km hace
    por cada clase de vía, sin asfaltar y en curvas."""
    ruteador = Ruteador(red, minutos_por_arista(red, ritmos))
    v_ini, m_ini = ruteador.ubicar(pares["lat_desde"].to_numpy(), pares["lon_desde"].to_numpy())
    v_fin, m_fin = ruteador.ubicar(pares["lat"].to_numpy(), pares["lon"].to_numpy())
    km = red.metros.astype(np.float64) / 1000
    curvas_km = km * np.minimum(red.curvas, CURVAS_TOPE) / 100
    filas = np.full((len(pares), len(CLASES) + 2), np.nan)
    for fuente in np.unique(v_ini):
        cuales = np.flatnonzero(v_ini == fuente)
        limite = 4.0 * pares["acceso_min"].to_numpy()[cuales].max() + 60
        _, predecesor = ruteador.minutos_desde(int(fuente), limite=limite, predecesores=True)
        for i in cuales:
            if v_fin[i] != fuente and predecesor[v_fin[i]] < 0:
                continue  # no se llega por la red
            aristas = ruteador.aristas_del_camino(predecesor, int(v_fin[i]))
            filas[i, : len(CLASES)] = np.bincount(red.clase[aristas], weights=km[aristas], minlength=len(CLASES))
            filas[i, len(CLASES)] = km[aristas][red.sin_asfaltar[aristas]].sum()
            filas[i, len(CLASES) + 1] = curvas_km[aristas].sum()
    columnas = [f"km_{c}" for c in CLASES] + ["km_sin_asfaltar", "curvas"]
    tabla = pd.concat([pares.reset_index(drop=True), pd.DataFrame(filas, columns=columnas)], axis=1)
    tabla["km_fuera_de_red"] = (m_ini + m_fin) / 1000
    tabla["traslados"] = 1.0  # cada recorrido paga una vez los minutos fijos
    tabla["km_red"] = tabla[[f"km_{c}" for c in CLASES]].sum(axis=1, min_count=1) + tabla["km_fuera_de_red"]
    return tabla


def _matriz(tabla: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Una columna por parámetro, en el orden de PARAMETROS, y los minutos que no se calibran."""
    x = np.column_stack(
        [tabla[f"km_{c}"] for c in CLASES[:-1]] + [tabla["km_sin_asfaltar"], tabla["curvas"], tabla["traslados"]]
    )
    # Del punto a la vía más cercana, por un camino que OSM no tiene: como una trocha.
    x[:, CLASES.index("trocha")] += 1.3 * tabla["km_fuera_de_red"].to_numpy()
    return x, tabla["km_balsa"].to_numpy() * RITMO_INICIAL["balsa"]


def ajustar(tabla: pd.DataFrame, previo: dict[str, float] = INICIALES) -> dict[str, float]:
    """Parámetros que mejor explican los minutos de las fichas (ver el módulo)."""
    from scipy.optimize import least_squares

    x, fijo = _matriz(tabla)
    observado = tabla["acceso_min"].to_numpy()
    partida = np.array([INICIALES[p] for p in PARAMETROS])

    def residuos(q):
        predicho = np.maximum(x @ q + fijo, 1e-3)
        return np.r_[np.log(predicho / observado), ANCLA * np.log(np.maximum(q, 1e-6) / partida)]

    inicio = np.array([previo[p] for p in PARAMETROS])
    ajuste = least_squares(residuos, inicio, bounds=(1e-4, np.inf), loss="soft_l1", f_scale=ESCALA_ROBUSTA)
    return {**RITMO_INICIAL, **dict(zip(PARAMETROS, ajuste.x.tolist(), strict=True))}


def predecir(tabla: pd.DataFrame, parametros: dict[str, float]) -> np.ndarray:
    x, fijo = _matriz(tabla)
    return x @ np.array([parametros[p] for p in PARAMETROS]) + fijo


def coinciden(tabla: pd.DataFrame) -> pd.Series:
    """Si la red y la ficha describen el mismo camino (ver KM_COINCIDEN)."""
    return tabla["km_red"].notna() & (tabla["km_red"] / tabla["acceso_km"]).between(*KM_COINCIDEN)


def validar(tabla: pd.DataFrame, pliegues: int = PLIEGUES) -> np.ndarray:
    """Minutos predichos para cada recorrido por un ajuste que no lo vio: los distritos de
    partida se reparten en ``pliegues`` grupos y cada grupo se predice con los demás."""
    grupo = pd.factorize(tabla["region_desde"] + "/" + tabla["distrito_desde"])[0]
    pliegue = np.random.default_rng(0).permutation(grupo.max() + 1)[grupo] % pliegues
    predicho = np.empty(len(tabla))
    for k in range(pliegues):
        prueba = pliegue == k
        predicho[prueba] = predecir(tabla[prueba], ajustar(tabla[~prueba]))
    return predicho


def calibrar(red: Red, pares: pd.DataFrame) -> tuple[dict[str, float], pd.DataFrame]:
    """Ajusta y vuelve a rutear hasta que las rutas no cambian. (parámetros, recorridos)."""
    parametros = dict(INICIALES)
    for _ in range(ITERACIONES):
        tabla = componer(red, parametros, pares)
        parametros = ajustar(tabla[coinciden(tabla)], parametros)
    tabla = componer(red, parametros, pares)
    return parametros, tabla


def informe(tabla: pd.DataFrame, parametros: dict[str, float], cuentas: dict[str, int]) -> dict:
    """Cifras de la calibración, con el error medido por validación cruzada."""
    usadas = tabla[coinciden(tabla)].reset_index(drop=True)
    observado = usadas["acceso_min"].to_numpy()
    predicho = validar(usadas)
    error = predicho / observado - 1
    recta = haversine_m(usadas["lat_desde"], usadas["lon_desde"], usadas["lat"], usadas["lon"]) / 1000
    error_formula = recta * 1.6 / 32.5 * 60 / observado - 1

    def cifras(e, minutos):
        return {
            "recorridos": int(len(e)),
            "error_medio": round(float(np.mean(np.abs(e))), 3),
            "error_mediano": round(float(np.median(np.abs(e))), 3),
            "dentro_del_25": round(float(np.mean(np.abs(e) <= 0.25)), 3),
            "sesgo_mediano": round(float(np.median(e)), 3),
            "minutos_de_error_mediano": round(float(np.median(np.abs(minutos))), 1),
        }

    def sin(cambio) -> float:
        """Error medio de validación cruzada si el modelo no tuviera ese término."""
        variante = cambio(usadas.copy())
        return round(float(np.mean(np.abs(validar(variante) / observado - 1))), 3)

    def un_ritmo(t):
        t["km_primaria"] = t[[f"km_{c}" for c in CLASES[:-1]]].sum(axis=1)
        t[[f"km_{c}" for c in CLASES[:-1] if c != "primaria"]] = 0.0
        return t

    ablacion = {
        "sin_curvas": sin(lambda t: t.assign(curvas=0.0)),
        "sin_minutos_fijos": sin(lambda t: t.assign(traslados=0.0)),
        "sin_recargo_sin_asfaltar": sin(lambda t: t.assign(km_sin_asfaltar=0.0)),
        "un_solo_ritmo": sin(un_ritmo),
    }
    bandas = pd.cut(usadas["acceso_km"], BANDAS_KM)
    por_distancia = {
        f"{int(b.left)}-{int(b.right)} km": cifras(
            error[(bandas == b).to_numpy()], (predicho - observado)[(bandas == b).to_numpy()]
        )
        for b in bandas.cat.categories
    }
    return {
        "recorridos": {**cuentas, "con_ruta": int(tabla["km_red"].notna().sum()), "misma_distancia": len(usadas)},
        "ritmo_min_por_km": {c: round(parametros[c], 3) for c in CLASES},
        "velocidad_kmh": {c: round(60 / parametros[c], 1) for c in CLASES},
        "recargo_sin_asfaltar_min_por_km": round(parametros["sin_asfaltar"], 3),
        "recargo_curvas_min_por_km_cada_100_grados": round(parametros["curvas"], 3),
        "minutos_por_traslado": round(parametros["por_viaje"], 1),
        "validacion_cruzada": {**cifras(error, predicho - observado), "por_distancia": por_distancia},
        "error_medio_sin_cada_termino": ablacion,
        "formula_semana_6": cifras(error_formula, recta * 1.6 / 32.5 * 60 - observado),
    }

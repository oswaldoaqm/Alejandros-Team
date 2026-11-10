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

En las ciudades (decisión 0025) las fichas no alcanzan: casi todos sus recorridos salen a
la carretera, y los que no, dicen menos de lo que mide el tráfico. Por eso la red reconoce
sus ciudades (``red_vial.manchas_urbanas``) y las de más de 100 km² van al ritmo que mide
TomTom (``pipeline/referencia/trafico_ciudades.csv``): ``pisos_de_ciudad`` busca el ritmo
de las calles con que un recorrido de 7 a 13 km por la ciudad tarda, en la mediana, lo
que TomTom mide de día para 10 km, con la autopista a la velocidad que TomTom publica para
sus vías rápidas. Lima fija el de la metrópoli y Arequipa el de las grandes; Trujillo,
que no entra en el ajuste, sirve para validarlo. Las ciudades medianas, que TomTom no
mide, llevan un recargo por km que se ajusta con las fichas como los demás parámetros.

Uso:  python -m pipeline.tiempos     (calibra y después calcula las tablas de tiempos)
"""

from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline.red_vial import (
    CODIGO,
    CURVAS_TOPE,
    VIALES,
    Red,
    Ruteador,
    haversine_m,
    manchas_urbanas,
    minutos_por_arista,
)

CALIBRADAS = VIALES[:-1]  # todas las clases de vía menos la balsa

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
INICIALES = {**RITMO_INICIAL, "sin_asfaltar": 0.6, "curvas": 0.15, "por_viaje": 5.0, "recargo_mediana": 0.5}
PARAMETROS = [*CALIBRADAS, "sin_asfaltar", "curvas", "por_viaje", "recargo_mediana"]
ANCLA = 0.3  # peso del valor de partida frente a los datos, en escala logarítmica
ESCALA_ROBUSTA = 0.2  # error logarítmico desde el que una ficha empieza a pesar menos (±22 %)

KM_MIN, MINUTOS_MIN = 3.0, 5.0  # más corto que esto es casi solo ruido de ubicación y redondeo
VELOCIDAD_FICHA = (5.0, 110.0)  # km/h: fuera de esto, la ficha trae un error de tipeo
KM_COINCIDEN = (0.67, 1.5)  # km de la red / km de la ficha: describen el mismo camino
UBICACION_MAX_KM = 80.0  # la capital elegida no puede estar más lejos de su distrito
ITERACIONES = 3
PLIEGUES = 5
BANDAS_KM = (0, 10, 30, 100, 300, 2_000)

# Las ciudades (decisión 0025)
TRAFICO = Path(__file__).resolve().parent / "referencia" / "trafico_ciudades.csv"
CON_PISO = ("grande", "metropoli")  # bandas con una ciudad que mide TomTom: su ritmo sale de ahí
CON_RECARGO = ("mediana",)  # sin una ciudad medida: un recargo por km, ajustado con las fichas
PARES_POR_CIUDAD = 160
EN_LINEA_RECTA_KM = (5.0, 9.0)  # los pares que se sortean en cada ciudad
POR_LA_RED_KM = (7.0, 13.0)  # y los que se miden: los de unos 10 km por la red, como la cifra de TomTom
TOLERANCIA_CIUDAD = 0.01
VUELTAS_CIUDAD = 5


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
    por cada clase de vía, sin asfaltar y en curvas. Solo por las vías: los recorridos que
    se calibran no usan tren ni bote.

    Lo que la ruta hace en una ciudad con piso (``CON_PISO``) no entra en esos km: va en
    ``min_ciudad``, con los minutos de esas aristas, que no dependen de lo que se ajusta, y en
    ``km_ciudad``. Los km en una ciudad con recargo (``CON_RECARGO``) sí entran, y además
    se cuentan en ``km_<banda>``, para su recargo."""
    from pipeline.red_vial import BANDAS

    red = red.vial()
    minutos = minutos_por_arista(red, ritmos)
    ruteador = Ruteador(red, minutos)
    banda = red.bandas
    con_piso = np.isin(banda, [BANDAS.index(b) for b in CON_PISO])
    v_ini, m_ini, _ = ruteador.ubicar(pares["lat_desde"].to_numpy(), pares["lon_desde"].to_numpy())
    v_fin, m_fin, _ = ruteador.ubicar(pares["lat"].to_numpy(), pares["lon"].to_numpy())
    km = red.metros.astype(np.float64) / 1000
    curvas_km = km * np.minimum(red.curvas, CURVAS_TOPE) / 100
    extra = ["km_sin_asfaltar", "curvas", *(f"km_{b}" for b in CON_RECARGO), "min_ciudad", "km_ciudad"]
    columna = dict(zip(extra, range(len(VIALES), len(VIALES) + len(extra)), strict=True))
    filas = np.full((len(pares), len(VIALES) + len(extra)), np.nan)
    for fuente in np.unique(v_ini):
        cuales = np.flatnonzero(v_ini == fuente)
        limite = 4.0 * pares["acceso_min"].to_numpy()[cuales].max() + 60
        _, predecesor = ruteador.minutos_desde(int(fuente), limite=limite, predecesores=True)
        for i in cuales:
            if v_fin[i] != fuente and predecesor[v_fin[i]] < 0:
                continue  # no se llega por la red
            aristas = ruteador.aristas_del_camino(predecesor, int(v_fin[i]))
            fuera = aristas[~con_piso[aristas]]
            dentro = aristas[con_piso[aristas]]
            filas[i, : len(VIALES)] = np.bincount(red.clase[fuera], weights=km[fuera], minlength=len(VIALES))
            filas[i, columna["km_sin_asfaltar"]] = km[fuera][red.sin_asfaltar[fuera]].sum()
            filas[i, columna["curvas"]] = curvas_km[fuera].sum()
            for b in CON_RECARGO:
                filas[i, columna[f"km_{b}"]] = km[fuera][banda[fuera] == BANDAS.index(b)].sum()
            filas[i, columna["min_ciudad"]] = minutos[dentro].sum()
            filas[i, columna["km_ciudad"]] = km[dentro].sum()
    columnas = [f"km_{c}" for c in VIALES] + extra
    tabla = pd.concat([pares.reset_index(drop=True), pd.DataFrame(filas, columns=columnas)], axis=1)
    tabla["km_fuera_de_red"] = (m_ini + m_fin) / 1000
    tabla["traslados"] = 1.0  # cada recorrido paga una vez los minutos fijos
    en_red = tabla[[f"km_{c}" for c in VIALES] + ["km_ciudad"]].sum(axis=1, min_count=1)
    tabla["km_red"] = en_red + tabla["km_fuera_de_red"]
    return tabla


def _matriz(tabla: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Una columna por parámetro, en el orden de PARAMETROS, y los minutos que no se calibran: los de la
    balsa y los de las ciudades con piso. Una tabla sin las columnas de las ciudades las toma en cero."""

    def columna(nombre: str) -> np.ndarray:
        return tabla[nombre].to_numpy() if nombre in tabla else np.zeros(len(tabla))

    x = np.column_stack(
        [tabla[f"km_{c}"] for c in CALIBRADAS]
        + [tabla["km_sin_asfaltar"], tabla["curvas"], tabla["traslados"]]
        + [columna(f"km_{b}") for b in CON_RECARGO]
    )
    # Del punto a la vía más cercana, por un camino que OSM no tiene: como una trocha.
    x[:, CALIBRADAS.index("trocha")] += 1.3 * tabla["km_fuera_de_red"].to_numpy()
    return x, tabla["km_balsa"].to_numpy() * RITMO_INICIAL["balsa"] + columna("min_ciudad")


def ajustar(tabla: pd.DataFrame, previo: dict[str, float] = INICIALES) -> dict[str, float]:
    """Parámetros que mejor explican los minutos de las fichas (ver el módulo)."""
    from scipy.optimize import least_squares

    x, fijo = _matriz(tabla)
    observado = tabla["acceso_min"].to_numpy()
    partida = np.array([INICIALES[p] for p in PARAMETROS])

    def residuos(q):
        predicho = np.maximum(x @ q + fijo, 1e-3)
        return np.r_[np.log(predicho / observado), ANCLA * np.log(np.maximum(q, 1e-6) / partida)]

    inicio = np.array([previo.get(p, INICIALES[p]) for p in PARAMETROS])
    ajuste = least_squares(residuos, inicio, bounds=(1e-4, np.inf), loss="soft_l1", f_scale=ESCALA_ROBUSTA)
    pisos = {k: v for k, v in previo.items() if k.startswith("piso_")}  # no se ajustan con las fichas
    return {**RITMO_INICIAL, **pisos, **dict(zip(PARAMETROS, ajuste.x.tolist(), strict=True))}


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
    """Ajusta y vuelve a rutear hasta que las rutas no cambian. (parámetros, recorridos).

    Los pisos de las ciudades se buscan antes de la primera vuelta y otra vez al final, con los ritmos ya
    ajustados: solo cambian si alguna vía de la ciudad iba más lenta que su piso."""
    parametros = {**INICIALES, **pisos_de_ciudad(red, INICIALES)}
    for _ in range(ITERACIONES):
        tabla = componer(red, parametros, pares)
        parametros = ajustar(tabla[coinciden(tabla)], parametros)
    parametros = {**parametros, **pisos_de_ciudad(red, parametros)}
    tabla = componer(red, parametros, pares)
    return parametros, tabla


# --- Las ciudades -------------------------------------------------------------------------


def trafico() -> pd.DataFrame:
    """Lo que mide TomTom en cada ciudad (``TRAFICO``), con su meta: los minutos por 10 km de un miércoles,
    promedio de las 10, 12, 14 y 16 h, las horas en que se visita."""
    tabla = pd.read_csv(TRAFICO, sep=";")
    horas = [c for c in tabla.columns if c.startswith("min_10km_")]
    return tabla.assign(meta_min_10km=tabla[horas].mean(axis=1))


def _pares_de_la_mancha(red: Red, ruteador: Ruteador, mancha: np.ndarray, vertice: int) -> np.ndarray:
    """``PARES_POR_CIUDAD`` pares de vértices de la mancha de ``vertice``, a ``EN_LINEA_RECTA_KM`` en línea recta,
    sorteados con una semilla fija: los mismos en cada vuelta."""
    dentro = np.flatnonzero((mancha[: red.vertices] == mancha[vertice]) & ruteador.en_red_grande[: red.vertices])
    rng = np.random.default_rng(0)
    pares = []
    for _ in range(200 * PARES_POR_CIUDAD):
        if len(pares) == PARES_POR_CIUDAD:
            break
        a, b = rng.choice(dentro, 2, replace=False)
        km = haversine_m(red.lat[a], red.lon[a], red.lat[b], red.lon[b]) / 1000
        if EN_LINEA_RECTA_KM[0] <= km <= EN_LINEA_RECTA_KM[1]:
            pares.append((a, b))
    return np.array(pares, dtype=np.int64).reshape(-1, 2)


def ritmos_en_ciudades(red: Red, ritmos: dict, ciudades: pd.DataFrame) -> pd.DataFrame:
    """Por ciudad: la mancha y su banda, y con ``ritmos`` la mediana de minutos por 10 km de sus pares que por la
    red quedan a ``POR_LA_RED_KM``, cuánto de esos km va por autopista y cuántos pares se midieron."""
    from scipy.sparse.csgraph import dijkstra

    from pipeline.red_vial import BANDAS, KM2_BANDAS

    red = red.vial()
    minutos = minutos_por_arista(red, ritmos)
    ruteador = Ruteador(red, minutos)
    mancha, km2 = manchas_urbanas(red)
    km = red.metros.astype(np.float64) / 1000
    autopista = red.clase == CODIGO["autopista"]
    filas = []
    for c in ciudades.itertuples():
        vertice = int(ruteador.ubicar([c.lat], [c.lon])[0][0])
        pares = _pares_de_la_mancha(red, ruteador, mancha, vertice)
        ritmo, rapidas = [], []
        for inicio in range(0, len(pares), 20):
            lote = pares[inicio : inicio + 20]
            _, predecesor = dijkstra(ruteador.grafo, indices=lote[:, 0], limit=240.0, return_predecessors=True)
            for k, (_, b) in enumerate(lote):
                if predecesor[k][b] < 0:
                    continue
                aristas = ruteador.aristas_del_camino(predecesor[k], int(b))
                largo = km[aristas].sum()
                if POR_LA_RED_KM[0] <= largo <= POR_LA_RED_KM[1]:
                    ritmo.append(minutos[aristas].sum() / largo * 10)
                    rapidas.append(km[aristas][autopista[aristas]].sum() / largo)
        banda = int(np.searchsorted(KM2_BANDAS, km2[mancha[vertice]], side="right")) if mancha[vertice] else 0
        filas.append(
            {
                "ciudad": c.ciudad,
                "banda": BANDAS[banda],
                "km2": float(km2[mancha[vertice]]),
                "pares": len(ritmo),
                "min_10km": float(np.median(ritmo)) if ritmo else np.nan,
                "por_autopista": float(np.mean(rapidas)) if rapidas else np.nan,
            }
        )
    return pd.DataFrame(filas)


def pisos_de_ciudad(red: Red, ritmos: dict) -> dict[str, float]:
    """Los pisos de cada banda de ``CON_PISO``, con su ciudad de ajuste en ``TRAFICO``: la autopista, a la velocidad
    que TomTom publica para sus vías rápidas; las calles, al ritmo con que la mediana de sus recorridos de unos 10 km
    tarda lo que TomTom mide de día. Como la parte por autopista cambia poco, se corrige la de las calles por
    regla de tres y se vuelve a medir, hasta quedar a ``TOLERANCIA_CIUDAD``."""
    tabla = trafico()
    ajuste = tabla[tabla["uso"] == "ajuste"].reset_index(drop=True)
    pisos = {}
    for c in ajuste.itertuples():
        pisos[f"piso_{c.banda}_rapidas"] = 60.0 / c.autopista_kmh
        pisos[f"piso_{c.banda}_calles"] = c.meta_min_10km / 10
    for _ in range(VUELTAS_CIUDAD):
        medido = ritmos_en_ciudades(red, {**ritmos, **pisos}, ajuste)
        if (medido["banda"].to_numpy() != ajuste["banda"].to_numpy()).any():
            cuales = medido[["ciudad", "banda"]].to_dict("records")
            raise ValueError(f"Una ciudad de ajuste no cae en su banda: {cuales}")
        listo = True
        for c, m in zip(ajuste.itertuples(), medido.itertuples(), strict=True):
            if abs(m.min_10km / c.meta_min_10km - 1) <= TOLERANCIA_CIUDAD:
                continue
            listo = False
            rapidas = m.por_autopista * 10 * pisos[f"piso_{c.banda}_rapidas"]
            calles_hoy = (m.min_10km - rapidas) / max(1 - m.por_autopista, 1e-3)
            calles_meta = (c.meta_min_10km - rapidas) / max(1 - m.por_autopista, 1e-3)
            pisos[f"piso_{c.banda}_calles"] *= max(calles_meta, 1e-3) / max(calles_hoy, 1e-3)
        if listo:
            break
    return pisos


def informe(
    tabla: pd.DataFrame, parametros: dict[str, float], cuentas: dict[str, int], ciudades: pd.DataFrame | None = None
) -> dict:
    """Cifras de la calibración, con el error medido por validación cruzada. Con ``ciudades`` (lo que da
    ``ritmos_en_ciudades`` para la tabla de ``trafico``), también el ritmo de cada ciudad frente a TomTom."""
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
        t["km_primaria"] = t[[f"km_{c}" for c in CALIBRADAS]].sum(axis=1)
        t[[f"km_{c}" for c in CALIBRADAS if c != "primaria"]] = 0.0
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
        "ritmo_min_por_km": {c: round(parametros[c], 3) for c in VIALES},
        "velocidad_kmh": {c: round(60 / parametros[c], 1) for c in VIALES},
        "recargo_sin_asfaltar_min_por_km": round(parametros["sin_asfaltar"], 3),
        "recargo_curvas_min_por_km_cada_100_grados": round(parametros["curvas"], 3),
        "minutos_por_traslado": round(parametros["por_viaje"], 1),
        "validacion_cruzada": {**cifras(error, predicho - observado), "por_distancia": por_distancia},
        "error_medio_sin_cada_termino": ablacion,
        "formula_semana_6": cifras(error_formula, recta * 1.6 / 32.5 * 60 - observado),
        **({} if ciudades is None else {"ciudades": _ciudades(parametros, ciudades)}),
    }


def _ciudades(parametros: dict[str, float], medido: pd.DataFrame) -> dict:
    """La sección de las ciudades del informe: sus ritmos y, por ciudad de ``TRAFICO``, lo que mide TomTom de día
    y lo que da la red."""
    tabla = trafico()
    return {
        "velocidad_kmh": {
            k.removeprefix("piso_"): round(60 / v, 1) for k, v in sorted(parametros.items()) if k.startswith("piso_")
        },
        "recargo_min_por_km": {b: round(parametros[f"recargo_{b}"], 3) for b in CON_RECARGO},
        "medido": [
            {
                "ciudad": t.ciudad,
                "uso": t.uso,
                "banda": m.banda,
                "km2": round(m.km2),
                "tomtom_min_por_10_km": round(t.meta_min_10km, 1),
                "red_min_por_10_km": round(m.min_10km, 1),
                "por_autopista": round(m.por_autopista, 2),
                "pares": int(m.pares),
            }
            for t, m in zip(tabla.itertuples(), medido.itertuples(), strict=True)
        ],
    }

"""
Desde dónde y en qué meses se ven las estrellas en cada polo (decisión 0018).

1. **Cuánta luz hay en el cielo.** Con la mediana de 17 meses de luces de VIIRS
   (``descargar_luces.py``), el modelo de Duriscoe et al. (2018) estima en cada punto la luz
   artificial del cielo entero frente a la natural (ALR): suma la radiancia de cada pixel a menos
   de 300 km, pesada por d^−α con α = 2,3 · (d / 350)^0,28 (d en km), y divide por 562,72, la
   constante con que lo calibraron contra mediciones en 24 parques de Estados Unidos. Las
   radiancias de menos de 0,5 nW/cm²/sr cuentan como cero, como en el modelo: son el resplandor
   del aire. La cuenta va a 30″ (unos 900 m), con una convolución.
   Las clases son las del Servicio de Parques Nacionales de Estados Unidos: debajo de 0,3, el
   cielo es excelente; de 0,3 a 2, tiene algo de luz pero se ve lo principal; sobre 2, la noche
   natural ya no se ve. El modelo no corrige la altura: en el altiplano, con menos aire, el
   cielo suele ser más oscuro de lo que dice.
2. **Desde dónde.** Desde la base, si su cielo no pasa de 2. Si pasa, desde el observatorio o
   el planetario de OpenStreetMap con nombre más cercano a menos de 45 minutos por la red: tiene
   telescopios y quien los explique, aunque su cielo tenga luz. Si la base tiene luz, también el
   lugar con nombre más oscuro a menos de 45 minutos (un mirador, casi siempre), si no pasa de 2
   y tiene a lo más un tercio de la luz de la base: se muestra como dato en la página de la zona,
   pero no se propone para una noche. Un mirador en el cerro, de noche y sin nadie, no es un plan
   que una app deba armar por su cuenta.
3. **Cuántas noches despejadas.** Por mes, la parte de las mediciones de las 21:00 y la 01:00
   con el cielo despejado, en la base:
   - **En la costa**, a menos de 100 km del mar y por debajo de 1 500 m, con los METAR del
     aeropuerto de la costa más cercano, si está a menos de 150 km (``descargar_metar.py``).
     Despejado es sin nubes o con pocas (FEW). De noche, sobre el desierto de la costa, el
     satélite no sirve: no ve las nubes bajas del invierno y marca nubes donde no las hay. Si
     no hay un aeropuerto cerca, no se da el dato.
   - **En el resto**, con la máscara de nubes de GOES-16 (``descargar_nubes.py``), sumando los
     3 × 3 pixeles alrededor del lugar, unos 6 km de lado.
   ``cielo_validacion.csv`` compara las dos fuentes en cada aeropuerto, mes a mes.

Escribe data/procesados/cielo_polos.csv y data/procesados/cielo_validacion.csv.

Uso:  python -m pipeline.cielo     (después de pipeline/noche.py y de las tres descargas)
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import re
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from pipeline import red_calibracion as calibracion
from pipeline.maestro import EXTERNOS, PROCESADOS, REFERENCIA
from pipeline.noche import puntos_en_cache
from pipeline.red_vial import RADIO_TIERRA_M, Ruteador, cercanos, haversine_m, minutos_por_arista
from pipeline.tiempos import OSM, _puerta_a_puerta, red_en_cache, ritmos_fijos

LUCES = EXTERNOS / "luces"
NUBES = EXTERNOS / "nubes" / "goes16_noches.npz"
METAR = EXTERNOS / "metar"
CACHE = 1  # sube cuando cambia cómo se calcula el brillo

# El modelo de Duriscoe et al. (2018), «A simplified model of all-sky artificial sky glow derived
# from VIIRS Day/Night band data», JQSRT 214: 133-145.
RADIANCIA_MINIMA = 0.5  # nW/cm²/sr
ALCANCE_KM = 300.0
CONSTANTE = 562.72
CELDA_DEL_MODELO_KM2 = 0.45 * 0.45  # el modelo se calibró sumando celdas de 450 m
# Las clases del Servicio de Parques Nacionales de Estados Unidos para el ALR.
MUY_OSCURO, OSCURO = 0.3, 2.0
MAS_OSCURO = 3.0  # un lugar fuera de la base tiene que tener a lo más un tercio de su luz
LEJOS_MIN = 45  # un lugar para ver estrellas, a lo más a esto por la red desde la base
LEJOS_KM = 40.0  # se buscan candidatos a esta distancia en línea recta
COSTA_KM, COSTA_ALTITUD_M = 100.0, 1_500.0
AEROPUERTO_KM = 150.0
AEROPUERTO_ALTITUD_M = 600.0  # un aeropuerto de la costa
OBSERVACIONES_MINIMAS = 300  # las de un aeropuerto en tres años, a las dos horas

# La rejilla fija de GOES-16 (GOES-R Product User Guide, sección 4.2.8).
R_ECUADOR, R_POLO = 6_378_137.0, 6_356_752.31414
ALTURA_SATELITE = 35_786_023.0 + R_ECUADOR
LONGITUD_SATELITE = -75.0
PASO_RAD, ORIGEN_RAD = 5.6e-05, 0.151844


# ─────────────────────────────── el brillo ───────────────────────────────


def _mediana(meses: list[Path]) -> tuple[np.ndarray, np.ndarray]:
    """La mediana de la radiancia de los meses en que se midió, pixel por pixel, por bloques para
    no llenar la memoria; y la transformación de la ventana."""
    primero = np.load(meses[0])
    forma, transformacion = primero["radiancia"].shape, primero["transformacion"]
    mediana = np.zeros(forma, np.float32)
    for f0 in range(0, forma[0], 500):
        f1 = min(forma[0], f0 + 500)
        pila = []
        for mes in meses:
            z = np.load(mes)
            r = z["radiancia"][f0:f1].astype(np.float32)
            r[z["noches"][f0:f1] == 0] = np.nan
            pila.append(r)
        with warnings.catch_warnings():  # un pixel que ningún mes midió queda en cero, sin aviso
            warnings.simplefilter("ignore", RuntimeWarning)
            mediana[f0:f1] = np.nan_to_num(np.nanmedian(np.stack(pila), axis=0), nan=0.0)
    return mediana, transformacion


def nucleo(dx_km: float, dy_km: float) -> np.ndarray:
    """El peso de cada celda alrededor de un punto: d^−α(d) hasta ``ALCANCE_KM``, por el área de la
    celda frente a la del modelo."""
    nx, ny = int(ALCANCE_KM / dx_km) + 1, int(ALCANCE_KM / dy_km) + 1
    x = np.arange(-nx, nx + 1) * dx_km
    y = np.arange(-ny, ny + 1) * dy_km
    d = np.maximum(np.hypot(x[None, :], y[:, None]), dx_km / 4)
    peso = d ** -(2.3 * (d / 350.0) ** 0.28)
    peso[d > ALCANCE_KM] = 0.0
    return peso * (dx_km * dy_km) / CELDA_DEL_MODELO_KM2


def brillo_del_cielo(meses: list[Path]) -> tuple[np.ndarray, np.ndarray]:
    """(ALR a 30″, su transformación). Las celdas de 30″ son el promedio de cuatro de 15″; la
    distancia en este a oeste se toma a la latitud del centro del Perú, 9° S, y con eso se equivoca
    en menos del 5 % en todo el país."""
    from scipy.signal import fftconvolve

    mediana, t = _mediana(meses)
    mediana[mediana < RADIANCIA_MINIMA] = 0.0
    f, c = (mediana.shape[0] // 2) * 2, (mediana.shape[1] // 2) * 2
    gruesa = mediana[:f, :c].reshape(f // 2, 2, c // 2, 2).mean(axis=(1, 3))
    paso = float(t[0]) * 2
    dx = paso * 111.320 * math.cos(math.radians(-9.0))
    dy = paso * 110.574
    alr = fftconvolve(gruesa.astype(np.float64), nucleo(dx, dy), mode="same") / CONSTANTE
    return np.maximum(alr, 0.0).astype(np.float32), np.array([paso, 0.0, float(t[2]), 0.0, -paso, float(t[5])])


def brillo_en_cache(directorio: Path = LUCES) -> tuple[np.ndarray, np.ndarray]:
    """``brillo_del_cielo``, guardado junto a las luces: se rehace si cambia algún mes."""
    manifiesto = json.loads((directorio / "manifiesto.json").read_text(encoding="utf-8"))
    huella = hashlib.sha256("".join(m["sha256"] for _, m in sorted(manifiesto["meses"].items())).encode()).hexdigest()
    ruta = directorio / f"brillo_{huella[:8]}_v{CACHE}.npz"
    if not ruta.exists():
        meses = [directorio / m["archivo"] for _, m in sorted(manifiesto["meses"].items())]
        alr, transformacion = brillo_del_cielo(meses)
        np.savez_compressed(ruta, alr=alr, transformacion=transformacion)
    z = np.load(ruta)
    return z["alr"], z["transformacion"]


def brillo_en(alr: np.ndarray, transformacion: np.ndarray, lat, lon) -> np.ndarray:
    """El ALR de la celda donde cae cada punto."""
    columna = ((np.asarray(lon) - transformacion[2]) / transformacion[0]).astype(int)
    fila = ((np.asarray(lat) - transformacion[5]) / transformacion[4]).astype(int)
    return alr[np.clip(fila, 0, alr.shape[0] - 1), np.clip(columna, 0, alr.shape[1] - 1)]


def clase(alr: float) -> str:
    return "muy_oscuro" if alr < MUY_OSCURO else "oscuro" if alr < OSCURO else "con_luz"


# ─────────────────────────────── las nubes ───────────────────────────────


def en_la_rejilla_de_goes(lat: float, lon: float) -> tuple[float, float]:
    """(fila, columna) de un punto en la rejilla fija de disco completo de GOES-16."""
    phi, lam = math.radians(lat), math.radians(lon)
    e2 = (R_ECUADOR**2 - R_POLO**2) / R_ECUADOR**2
    phi_c = math.atan((R_POLO**2 / R_ECUADOR**2) * math.tan(phi))
    rc = R_POLO / math.sqrt(1 - e2 * math.cos(phi_c) ** 2)
    sx = ALTURA_SATELITE - rc * math.cos(phi_c) * math.cos(lam - math.radians(LONGITUD_SATELITE))
    sy = -rc * math.cos(phi_c) * math.sin(lam - math.radians(LONGITUD_SATELITE))
    sz = rc * math.sin(phi_c)
    y = math.atan(sz / sx)
    x = math.asin(-sy / math.sqrt(sx**2 + sy**2 + sz**2))
    return (ORIGEN_RAD - y) / PASO_RAD, (x + ORIGEN_RAD) / PASO_RAD


class Satelite:
    """Las noches despejadas de GOES-16, por mes, en cualquier punto del Perú."""

    def __init__(self, ruta: Path = NUBES):
        z = np.load(ruta)
        self.despejado = z["despejado"].astype(np.int64).sum(axis=0)  # (mes, fila, columna)
        self.valido = z["valido"].astype(np.int64).sum(axis=0)
        self.f0, self.c0 = int(z["filas"][0]), int(z["columnas"][0])

    def despejadas(self, lat: float, lon: float) -> list[float | None]:
        """La parte de las mediciones buenas con el cielo despejado, en los 3 × 3 pixeles
        alrededor del punto; None en un mes sin mediciones."""
        fila, columna = en_la_rejilla_de_goes(lat, lon)
        f, c = int(round(fila)) - self.f0, int(round(columna)) - self.c0
        if not (1 <= f < self.valido.shape[1] - 1 and 1 <= c < self.valido.shape[2] - 1):
            return [None] * 12
        d = self.despejado[:, f - 1 : f + 2, c - 1 : c + 2].sum(axis=(1, 2))
        v = self.valido[:, f - 1 : f + 2, c - 1 : c + 2].sum(axis=(1, 2))
        return [round(float(a) / b, 3) if b else None for a, b in zip(d, v, strict=True)]


CAPA = re.compile(r"\b(FEW|SCT|BKN|OVC|VV)(\d{3}|///)")
SIN_NUBES = re.compile(r"\b(CAVOK|SKC|CLR|NSC|NCD)\b")
HORAS_UTC = (2, 6)  # las mismas de GOES-16: 21:00 y 01:00 en el Perú


def leer_metar(directorio: Path = METAR) -> pd.DataFrame:
    """Las observaciones de las 02:00 y las 06:00 UTC de cada aeropuerto, una por día y hora (la
    más cercana a la hora en punto, con media hora de margen), con si el cielo estaba despejado:
    sin capas de nubes o solo con pocas (FEW). Las que no dicen nada de las nubes no cuentan."""
    filas = []
    for archivo in sorted(directorio.glob("*/*.csv.gz")):
        with gzip.open(archivo, "rt", encoding="utf-8", newline="") as fh:
            vistas: dict[tuple[str, int], tuple[int, bool]] = {}
            meta = None
            for r in csv.DictReader(fh):
                fecha = r["DATE"]
                hh, mm = int(fecha[11:13]), int(fecha[14:16])
                minutos = hh * 60 + mm
                for hora in HORAS_UTC:
                    lejos = abs(minutos - hora * 60)
                    if lejos > 30:
                        continue
                    capas = CAPA.findall(r["METAR"])
                    if not capas and not SIN_NUBES.search(r["METAR"]):
                        continue
                    despejado = all(c == "FEW" for c, _ in capas)
                    clave = (fecha[:10], hora)
                    if clave not in vistas or lejos < vistas[clave][0]:
                        vistas[clave] = (lejos, despejado)
                meta = meta or (
                    r["STATION"],
                    r["NAME"],
                    float(r["LATITUDE"]),
                    float(r["LONGITUDE"]),
                    float(r["ELEVATION"]),
                )
        if meta is None:
            continue
        for (dia, hora), (_, despejado) in vistas.items():
            filas.append((*meta, int(dia[5:7]), hora, despejado))
    return pd.DataFrame(filas, columns=["estacion", "nombre", "lat", "lon", "altitud_m", "mes", "hora", "despejado"])


def _ciudad(nombre: str, lat: float, lon: float, referencia: pd.DataFrame) -> str:
    """La ciudad del aeropuerto: la de referencia/aeropuertos.csv si está a menos de 5 km; si no, el
    nombre de la estación sin «International»."""
    km = haversine_m(lat, lon, referencia["lat"].to_numpy(), referencia["lon"].to_numpy()) / 1000
    if len(km) and km.min() <= 5:
        return str(referencia.iloc[int(np.argmin(km))]["ciudad"])
    return re.sub(r"\s+(international|intl)\b.*$", "", nombre.split(",")[0], flags=re.IGNORECASE).title()


def aeropuertos(metar: pd.DataFrame) -> pd.DataFrame:
    """Por aeropuerto con al menos ``OBSERVACIONES_MINIMAS``: dónde está, su ciudad y la parte de
    noches despejadas de cada mes (None si un mes tiene menos de 20)."""
    referencia = pd.read_csv(REFERENCIA / "aeropuertos.csv", sep=";")
    salida = []
    for (estacion, nombre, lat, lon, altitud), g in metar.groupby(["estacion", "nombre", "lat", "lon", "altitud_m"]):
        if len(g) < OBSERVACIONES_MINIMAS:
            continue
        por_mes = g.groupby("mes")["despejado"].agg(["sum", "count"]).reindex(range(1, 13), fill_value=0)
        fila = {
            "estacion": estacion,
            "nombre": _ciudad(nombre, lat, lon, referencia),
            "lat": lat,
            "lon": lon,
            "altitud_m": altitud,
            "observaciones": len(g),
        }
        for mes, (s, n) in por_mes.iterrows():
            fila[f"despejadas_{mes}"] = round(s / n, 3) if n >= 20 else None
        salida.append(fila)
    return pd.DataFrame(salida)


def costa_en_cache(pbf: Path) -> pd.DataFrame:
    """Los nodos de la línea de costa del mar (``natural=coastline``) del extracto, uno de cada
    cinco: con eso la distancia al mar se equivoca en menos de un km."""
    manifiesto = json.loads((pbf.parent / "manifiesto.json").read_text(encoding="utf-8"))
    ruta = pbf.parent / f"costa_{manifiesto['md5'][:8]}_v1.csv"
    if not ruta.exists():
        import osmium

        filas = []
        procesador = (
            osmium.FileProcessor(str(pbf), osmium.osm.NODE | osmium.osm.WAY)
            .with_locations("flex_mem")
            .with_filter(osmium.filter.TagFilter(("natural", "coastline")))
        )
        for objeto in procesador:
            if objeto.is_way():
                filas += [(nd.lat, nd.lon) for nd in objeto.nodes if nd.location.valid()][::5]
        pd.DataFrame(filas, columns=["lat", "lon"]).to_csv(ruta, index=False)
    return pd.read_csv(ruta)


def km_al_mar(costa: pd.DataFrame, lat, lon) -> np.ndarray:
    from scipy.spatial import cKDTree

    def unitarios(la, lo):
        p, q = np.radians(np.asarray(la, float)), np.radians(np.asarray(lo, float))
        return np.column_stack([np.cos(p) * np.cos(q), np.cos(p) * np.sin(q), np.sin(p)])

    cuerda, _ = cKDTree(unitarios(costa["lat"], costa["lon"])).query(unitarios(lat, lon))
    return 2 * RADIO_TIERRA_M * np.arcsin(np.clip(cuerda / 2, 0, 1)) / 1000


def despejadas(lat, lon, altitud_m, al_mar_km, satelite: Satelite, en_costa: pd.DataFrame) -> tuple[list, str, str]:
    """(la parte de noches despejadas de cada mes, de dónde sale, el aeropuerto si es de METAR)."""
    costero = al_mar_km <= COSTA_KM and (altitud_m is None or not np.isfinite(altitud_m) or altitud_m < COSTA_ALTITUD_M)
    if not costero:
        return satelite.despejadas(lat, lon), "goes", ""
    if len(en_costa):
        km = haversine_m(lat, lon, en_costa["lat"].to_numpy(), en_costa["lon"].to_numpy()) / 1000
        i = int(np.argmin(km))
        if km[i] <= AEROPUERTO_KM:
            a = en_costa.iloc[i]
            return [a[f"despejadas_{m}"] for m in range(1, 13)], "metar", a["nombre"]
    return [None] * 12, "", ""


# ─────────────────────────────── desde dónde ───────────────────────────────


TIPO_DE_LUGAR = {
    "viewpoint": "mirador",
    "observatory": "observatorio",
    "telescope": "observatorio",
    "planetarium": "planetario",
}


NO_ES_DE_ESTRELLAS = re.compile(r"vulcanol|sismol|meteorol|geof[ií]s|magn[eé]t", re.IGNORECASE)


def candidatos(puntos: pd.DataFrame) -> pd.DataFrame:
    """Los miradores, observatorios y planetarios de OSM con nombre. Un «observatorio» que se llama
    mirador es un mirador. ``astronomia`` dice si es un observatorio o un planetario para mirar el
    cielo: un observatorio vulcanológico, sismológico o meteorológico no lo es."""
    c = puntos[puntos["valor"].isin(TIPO_DE_LUGAR) & (puntos["nombre"] != "")].copy()
    c["tipo"] = c["valor"].map(TIPO_DE_LUGAR)
    c.loc[c["nombre"].str.lower().str.startswith("mirador"), "tipo"] = "mirador"
    c["astronomia"] = c["tipo"].isin(["observatorio", "planetario"]) & ~c["nombre"].str.contains(NO_ES_DE_ESTRELLAS)
    return c.reset_index(drop=True)


def minutos_desde_cada_base(ruteador, parametros, bases: pd.DataFrame, lugares: pd.DataFrame) -> list[dict[int, float]]:
    """Para cada base, los minutos de puerta a puerta por la red a los lugares a menos de
    ``LEJOS_KM`` en línea recta."""
    v_base, m_base, _ = ruteador.ubicar(bases["lat"].to_numpy(), bases["lon"].to_numpy())
    v_lugar, m_lugar, _ = ruteador.ubicar(lugares["lat"].to_numpy(), lugares["lon"].to_numpy())
    vecinos = cercanos(
        bases["lat"].to_numpy(),
        bases["lon"].to_numpy(),
        lugares["lat"].to_numpy(),
        lugares["lon"].to_numpy(),
        LEJOS_KM * 1000,
    )
    salida = []
    for i, cerca in enumerate(vecinos):
        cerca = sorted(cerca)
        if not cerca:
            salida.append({})
            continue
        minutos, km = ruteador.entre(v_base[i : i + 1], v_lugar[cerca], margen=0.5)
        minutos, _ = _puerta_a_puerta(minutos[0], km[0], m_base[i] + m_lugar[cerca], parametros)
        salida.append({j: float(m) for j, m in zip(cerca, minutos, strict=True) if np.isfinite(m)})
    return salida


def _lugar(prefijo: str, r, minutos: float, brillo: float) -> dict:
    return {
        f"{prefijo}_nombre": r["nombre"],
        f"{prefijo}_tipo": r["tipo"],
        f"{prefijo}_osm": r["osm"],
        f"{prefijo}_lat": r["lat"],
        f"{prefijo}_lon": r["lon"],
        f"{prefijo}_minutos": int(round(minutos)),
        f"{prefijo}_brillo": round(float(brillo), 3),
    }


def para_cada_polo(bases, lugares, minutos, alr, transformacion, satelite, en_costa, costa) -> pd.DataFrame:
    """Por polo: el brillo del cielo en la base y sus noches despejadas de cada mes; si la base
    tiene luz, el lugar con nombre más oscuro a menos de ``LEJOS_MIN`` (``oscuro_*``), que se
    muestra como dato y no se propone para una noche; y el observatorio o planetario más cercano
    a menos de ``LEJOS_MIN`` (``astro_*``)."""
    brillo_base = brillo_en(alr, transformacion, bases["lat"], bases["lon"])
    brillo_lugar = brillo_en(alr, transformacion, lugares["lat"], lugares["lon"])
    al_mar = km_al_mar(costa, bases["lat"], bases["lon"])
    filas = []
    for i, base in enumerate(bases.itertuples(index=False)):
        b = float(brillo_base[i])
        fila = {"polo": int(base.polo), "brillo_base": round(b, 3)}
        cerca = {j: m for j, m in minutos[i].items() if m <= LEJOS_MIN}
        if b >= OSCURO:
            mejores = [
                (round(float(brillo_lugar[j]), 2), m, lugares.at[j, "osm"], j)
                for j, m in cerca.items()
                if brillo_lugar[j] < OSCURO and brillo_lugar[j] <= b / MAS_OSCURO
            ]
            if mejores:
                _, m, _, j = min(mejores)
                fila |= _lugar("oscuro", lugares.iloc[j], m, brillo_lugar[j])
        astro = sorted((m, lugares.at[j, "osm"], j) for j, m in cerca.items() if lugares.at[j, "astronomia"])
        if astro:
            m, _, j = astro[0]
            fila |= _lugar("astro", lugares.iloc[j], m, brillo_lugar[j])
        altitud = float(base.altitud_m) if pd.notna(base.altitud_m) else None
        partes, fuente, estacion = despejadas(base.lat, base.lon, altitud, float(al_mar[i]), satelite, en_costa)
        fila |= {"km_al_mar": round(float(al_mar[i]), 1), "nubes": fuente, "nubes_aeropuerto": estacion}
        fila |= {f"despejadas_{m}": p for m, p in zip(range(1, 13), partes, strict=True)}
        filas.append(fila)
    columnas = ["polo", "brillo_base"]
    columnas += [
        f"{p}_{c}" for p in ("oscuro", "astro") for c in ("nombre", "tipo", "osm", "lat", "lon", "minutos", "brillo")
    ]
    columnas += ["km_al_mar", "nubes", "nubes_aeropuerto", *(f"despejadas_{m}" for m in range(1, 13))]
    return pd.DataFrame(filas).reindex(columns=columnas)


def validacion(en_costa_y_fuera: pd.DataFrame, satelite: Satelite, costa: pd.DataFrame) -> pd.DataFrame:
    """Cada aeropuerto, mes a mes: las noches despejadas según su METAR y según GOES-16, si está
    en la costa, y qué tanto se parecen las dos (correlación y diferencia media, en puntos)."""
    filas = []
    for a in en_costa_y_fuera.itertuples(index=False):
        metar = np.array([getattr(a, f"despejadas_{m}") for m in range(1, 13)], dtype=float)
        goes = np.array([np.nan if x is None else x for x in satelite.despejadas(a.lat, a.lon)], dtype=float)
        ok = np.isfinite(metar) & np.isfinite(goes)
        al_mar = float(km_al_mar(costa, [a.lat], [a.lon])[0])
        fila = {
            "estacion": a.estacion,
            "nombre": a.nombre,
            "lat": a.lat,
            "lon": a.lon,
            "altitud_m": a.altitud_m,
            "km_al_mar": round(al_mar, 1),
            "en_la_costa": al_mar <= COSTA_KM and a.altitud_m < COSTA_ALTITUD_M,
            "observaciones": a.observaciones,
            "r": round(float(np.corrcoef(metar[ok], goes[ok])[0, 1]), 2) if ok.sum() >= 6 else None,
            "diferencia_media": round(float(np.abs(metar[ok] - goes[ok]).mean()) * 100, 1) if ok.any() else None,
        }
        fila |= {f"metar_{m}": metar[m - 1] for m in range(1, 13)}
        fila |= {f"goes_{m}": goes[m - 1] for m in range(1, 13)}
        filas.append(fila)
    return pd.DataFrame(filas)


def _escribir(tabla: pd.DataFrame, ruta: Path) -> None:
    """Las coordenadas con seis decimales (unos 10 cm), el brillo y las partes con tres."""

    def numero(decimales):
        return lambda x: "" if x is None or pd.isna(x) else f"{float(x):.{decimales}f}"

    formato = {c: tabla[c].map(numero(6)) for c in tabla.columns if c.endswith(("lat", "lon"))}
    formato |= {c: tabla[c].map(numero(1)) for c in tabla.columns if c.endswith(("altitud_m", "km_al_mar"))}
    tabla.assign(**formato).to_csv(
        ruta, sep=";", index=False, encoding="utf-8-sig", lineterminator="\n", float_format="%.3f"
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Desde dónde y en qué meses se ven las estrellas en cada polo.")
    ap.add_argument("--pbf", type=Path, default=OSM / "peru-latest.osm.pbf")
    ap.add_argument("--maestro", type=Path, default=PROCESADOS / "maestro_v3.csv")
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    ap.add_argument("--indice", default="flex_mem")
    a = ap.parse_args()

    bases = pd.read_csv(PROCESADOS / "polos_bases.csv", sep=";", encoding="utf-8-sig")
    lugares = candidatos(puntos_en_cache(a.pbf, a.indice))
    alr, transformacion = brillo_en_cache()
    satelite = Satelite()
    todos = aeropuertos(leer_metar())
    costa = costa_en_cache(a.pbf)
    al_mar = km_al_mar(costa, todos["lat"], todos["lon"])
    en_costa = todos[(al_mar <= COSTA_KM) & (todos["altitud_m"] < AEROPUERTO_ALTITUD_M)].reset_index(drop=True)

    # La misma red y la misma calibración que pipeline.tiempos.
    red, osm, _ = red_en_cache(a.pbf, a.indice)
    maestro = pd.read_csv(a.maestro, sep=";", encoding="utf-8-sig", dtype={"dias": str})
    pares, _ = calibracion.pares_de_calibracion(maestro, osm.capitales, osm.lugares)
    parametros, _ = calibracion.calibrar(red, pares)
    parametros = {**parametros, **ritmos_fijos()}
    ruteador = Ruteador(red, minutos_por_arista(red, parametros))
    minutos = minutos_desde_cada_base(ruteador, parametros, bases, lugares)

    tabla = para_cada_polo(bases, lugares, minutos, alr, transformacion, satelite, en_costa, costa)
    comparacion = validacion(todos, satelite, costa)
    _escribir(tabla, a.salida / "cielo_polos.csv")
    _escribir(comparacion, a.salida / "cielo_validacion.csv")
    clases = tabla["brillo_base"].map(clase).value_counts()
    luces = json.loads((LUCES / "manifiesto.json").read_text(encoding="utf-8"))
    nubes = json.loads((NUBES.parent / "manifiesto.json").read_text(encoding="utf-8"))

    def comparadas(en_la_costa: bool) -> dict:
        filas = comparacion[comparacion["en_la_costa"] == en_la_costa]
        return {f.nombre: {"r": f.r, "diferencia_media": f.diferencia_media} for f in filas.itertuples()}

    resumen = {
        "viirs": {"meses": sorted(luces["meses"])},
        "goes16": {"anios": nubes["anios"], "horas_utc": nubes["horas_utc"], "imagenes": nubes["imagenes"]},
        "metar": {"aeropuertos": len(todos), "en_la_costa": len(en_costa)},
        "polos": {
            **{c: int(clases.get(c, 0)) for c in ("muy_oscuro", "oscuro", "con_luz")},
            "con_observatorio": int(tabla["astro_nombre"].notna().sum()),
            "nubes_de_goes": int((tabla["nubes"] == "goes").sum()),
            "nubes_de_metar": int((tabla["nubes"] == "metar").sum()),
            "sin_nubes": int(tabla["nubes"].isna().sum() + (tabla["nubes"] == "").sum()),
        },
        "goes_contra_metar": {"fuera_de_la_costa": comparadas(False), "en_la_costa": comparadas(True)},
    }
    (a.salida / "cielo_resumen.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    astro = int(tabla["astro_nombre"].notna().sum())
    goes, metar = (int((tabla["nubes"] == f).sum()) for f in ("goes", "metar"))
    print(
        f"{len(tabla)} polos: desde la base, {clases.get('muy_oscuro', 0)} con el cielo muy oscuro, "
        f"{clases.get('oscuro', 0)} oscuro y {clases.get('con_luz', 0)} con luz; {astro} con un observatorio o un "
        f"planetario cerca; noches despejadas de GOES en {goes} y de METAR en {metar}"
    )


if __name__ == "__main__":
    main()

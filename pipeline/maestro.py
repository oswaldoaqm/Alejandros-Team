"""
Maestro v3: una fila por recurso del inventario vigente, con lo que dice su ficha
oficial, su polo y las marcas de calidad que el motor necesita.

Entradas que bajan los scripts de pipeline/adquisicion (fuera de git):
    data/externos/inventario/Inventario_recursos_turisticos.csv
    data/externos/fichas_html/<codigo>.html.gz
Entradas del repositorio:
    deliveries/week06/data/processed/polos_asignados_v2.csv  (polos del modelo v2, TA-01)
    pipeline/referencia/intereses.csv y duracion_visita.csv
Salidas:
    data/procesados/maestro_v3.csv           una fila por recurso
    data/procesados/maestro_v3_resumen.json  cobertura de cada campo y de dónde sale

Cada campo que no se copia tal cual de una fuente dice de dónde sale en su columna
``*_fuente``. Lo que la fuente no trae queda vacío: nada se imputa.

Uso:  python -m pipeline.maestro
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from dataclasses import dataclass
from math import fsum
from pathlib import Path

import numpy as np
import pandas as pd

from dreemgo.contrato import Interes
from pipeline.fichas import URL_FICHA, Ficha, Tramo, leer_archivo
from pipeline.inventario import leer_inventario
from pipeline.texto import sin_tildes

RAIZ = Path(__file__).resolve().parents[1]
EXTERNOS = RAIZ / "data" / "externos"
PROCESADOS = RAIZ / "data" / "procesados"
REFERENCIA = Path(__file__).resolve().parent / "referencia"
POLOS_V2 = RAIZ / "deliveries" / "week06" / "data" / "processed" / "polos_asignados_v2.csv"

VERSION = "v3"

# ── Polos: las mismas reglas del modelo v2 (deliveries/week06/code/ta01_polos_acotados.py) ──
R_TIERRA_KM = 6371.0
K_DESNIVEL = 0.06  # km equivalentes por metro de desnivel
DIAMETRO_MAX = 80.0  # km de viaje efectivo: ningún par de recursos de un polo pasa de esto
SE_MOVIO_KM = 0.5  # una coordenada que cambió menos que esto se considera la misma

CATEGORIAS_LUGAR = (1, 2, 4)  # sitios naturales, manifestaciones culturales, realizaciones
MEDIOS_A_PIE = {"A pie", "A caballo", "Acémila"}
ACCESOS_POR_AGUA = {"Lacustre / Fluvial", "Marítimo"}
ALTITUD_CUMBRE_M = 5_000  # una cumbre más alta se contempla, no se visita
DISCREPANCIA_ALTITUD_M = 500
DESCRIPCION_CORTA = 280
INTERESES = tuple(i.value for i in Interes)  # los ocho chips del contrato
DIAS_CORTOS = ("lun", "mar", "mie", "jue", "vie", "sab", "dom")
# Columnas enteras que pueden venir vacías: se guardan como "4", no como "4.0".
ENTEROS = (
    "polo",
    "jerarquia",
    "altitud_m",
    "altitud_ficha_m",
    "altitud_ficha_max_m",
    "altitud_dem_m",
    "visita_min",
    "acceso_min",
    "caminata_min",
    "recorridos",
    "visitantes_anio",
    "visitantes_nacionales",
    "visitantes_extranjeros",
    "visitantes_locales",
)


# ── Lectura de las tablas de referencia ─────────────────────────────────────────────


def _referencia(nombre: str) -> list[dict[str, str]]:
    with open(REFERENCIA / nombre, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


@dataclass(frozen=True)
class ReglasIntereses:
    por_campo: dict[tuple[str, str], frozenset[str]]
    excluir_subtipo: dict[str, frozenset[str]]

    @classmethod
    def cargar(cls) -> ReglasIntereses:
        por_campo: dict[tuple[str, str], set[str]] = {}
        excluir: dict[str, set[str]] = {}
        for fila in _referencia("intereses.csv"):
            if fila["campo"] == "excluir_subtipo":
                excluir.setdefault(fila["valor"], set()).add(fila["interes"])
            else:
                por_campo.setdefault((fila["campo"], fila["valor"]), set()).add(fila["interes"])
        return cls(
            {k: frozenset(v) for k, v in por_campo.items()},
            {k: frozenset(v) for k, v in excluir.items()},
        )

    def de(self, categoria_num: int | None, tipo: str | None, subtipo: str | None, actividades: list[str]) -> list[str]:
        estructura: set[str] = set()
        for campo, valor in (("categoria", str(categoria_num)), ("tipo", tipo), ("subtipo", subtipo)):
            estructura |= self.por_campo.get((campo, valor or ""), frozenset())
        estructura -= self.excluir_subtipo.get(subtipo or "", frozenset())
        por_actividad = set().union(*(self.por_campo.get(("actividad", a), frozenset()) for a in actividades))
        return sorted(estructura | por_actividad)


@dataclass(frozen=True)
class ReglasDuracion:
    minutos: dict[tuple[str, str], int]

    @classmethod
    def cargar(cls) -> ReglasDuracion:
        return cls({(f["campo"], f["valor"]): int(f["minutos"]) for f in _referencia("duracion_visita.csv")})

    def de(self, categoria_num: int | None, tipo: str | None, subtipo: str | None) -> tuple[int | None, str | None]:
        """Minutos de visita y la regla que los dio, de la más específica a la más general."""
        for campo, valor in (("subtipo", subtipo), ("tipo", tipo), ("categoria", str(categoria_num))):
            if valor and (campo, valor) in self.minutos:
                return self.minutos[(campo, valor)], f"referencia:{campo}"
        return None, None


# ── Resumen de una ficha ────────────────────────────────────────────────────────────


def _recorridos(tramos: tuple[Tramo, ...]) -> list[list[Tramo]]:
    grupos: dict[int | None, list[Tramo]] = {}
    for t in tramos:
        grupos.setdefault(t.recorrido, []).append(t)
    return [_sin_alternativas(r) for r in grupos.values()]


def _sin_alternativas(recorrido: list[Tramo]) -> list[Tramo]:
    """Muchas fichas repiten un mismo tramo con otro medio: "Paracas – Reserva: 7 min en
    auto, 10 en bus, 52 a pie". Son alternativas, no tramos seguidos: sumarlas daría el
    triple de distancia y una caminata que nadie hace. Un tramo repetido tiene el mismo
    inicio y fin y la misma distancia o la misma descripción; queda el más rápido."""
    elegidos: list[Tramo] = []
    for t in recorrido:
        for i, e in enumerate(elegidos):
            mismo_tramo = (e.desde, e.hasta) == (t.desde, t.hasta) and (
                e.km == t.km or (_detalle(e) is not None and _detalle(e) == _detalle(t))
            )
            if mismo_tramo:
                if t.minutos is not None and (e.minutos is None or t.minutos < e.minutos):
                    elegidos[i] = t
                break
        else:
            elegidos.append(t)
    return elegidos


def _detalle(t: Tramo) -> str | None:
    """La descripción del tramo sin espacios, tildes ni signos: "Nasca- Museo" = "Nasca - Museo"."""
    texto = re.sub(r"[^a-z0-9]", "", sin_tildes(t.detalle or ""))
    return texto or None


def resumen_acceso(tramos: tuple[Tramo, ...]) -> dict[str, object]:
    """El recorrido más corto en tiempo entre los que tienen todos sus minutos.

    De él salen el tramo final (medio y vía), la caminata que queda al final (a pie,
    a caballo) y si hace falta un bote o una avioneta. Si ningún recorrido está
    completo, se usa el primero y los totales quedan vacíos.
    """
    vacio: dict[str, object] = {
        "acceso_km": None,
        "acceso_min": None,
        "acceso_desde": None,
        "caminata_min": None,
        "acceso_acuatico": None,
        "acceso_aereo": None,
        "ultimo_medio": None,
        "ultimo_via": None,
        "recorridos": 0,
    }
    recorridos = _recorridos(tramos)
    if not recorridos:
        return vacio
    completos = [r for r in recorridos if all(t.minutos is not None for t in r)]
    # math.fsum y no sum(): desde Python 3.12 sum() compensa el redondeo y el resultado
    # cambiaría según la versión con que se corra el pipeline.
    elegido = min(completos, key=lambda r: fsum(t.minutos for t in r)) if completos else recorridos[0]
    caminata = 0.0
    for t in reversed(elegido):
        if t.medio not in MEDIOS_A_PIE or t.minutos is None:
            break
        caminata += t.minutos
    desde = elegido[0].desde
    return {
        "acceso_km": round(fsum(t.km for t in elegido), 1) if all(t.km is not None for t in elegido) else None,
        "acceso_min": round(fsum(t.minutos for t in elegido)) if completos else None,
        "acceso_desde": "/".join(p for p in (desde.departamento, desde.provincia, desde.distrito) if p)
        if desde
        else None,
        "caminata_min": round(caminata) if completos else None,
        "acceso_acuatico": any(t.acceso in ACCESOS_POR_AGUA for t in elegido),
        "acceso_aereo": any(t.acceso == "Aéreo" for t in elegido),
        "ultimo_medio": elegido[-1].medio,
        "ultimo_via": elegido[-1].via,
        "recorridos": len(recorridos),
    }


def descripcion_corta(texto: str | None, limite: int = DESCRIPCION_CORTA) -> str | None:
    """Las primeras oraciones completas que caben en ``limite`` caracteres."""
    if not texto:
        return None
    parrafo = texto.split("\n")[0]
    if len(parrafo) <= limite:
        return parrafo
    oraciones = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑ¿¡“\"])", parrafo)
    corto = ""
    for o in oraciones:
        if len(corto) + len(o) + 1 > limite:
            break
        corto = f"{corto} {o}".strip()
    if corto:
        return corto
    return parrafo[: limite - 1].rsplit(" ", 1)[0] + "…"


def _tiene(servicios: tuple[str, ...], *prefijos: str) -> bool:
    return any(s.startswith(prefijos) for s in servicios)


def resumen_ficha(f: Ficha) -> dict[str, object]:
    """Los campos del maestro que salen de la ficha."""
    ingreso = next((i for i in f.ingresos if i.tipo == "boleto"), f.ingresos[0] if f.ingresos else None)
    epoca = f.epocas[0] if f.epocas else None
    # Visitantes del año más reciente que registra la ficha, para no mezclar años.
    anios = [v.anio for v in f.visitantes if v.anio]
    ultimo = max(anios) if anios else None
    visitantes = {v.tipo: v for v in f.visitantes if v.anio == ultimo}
    return {
        "nombre_ficha": f.nombre,
        "jerarquia": f.jerarquia,
        "jerarquia_texto": f.jerarquia_texto,
        "altitud_ficha_m": f.altitud_min_m,
        "altitud_ficha_max_m": f.altitud_max_m,
        "ingreso": ingreso.tipo if ingreso else None,
        "tarifa_soles": ingreso.tarifa.soles if ingreso and ingreso.tipo != "libre" else (0.0 if ingreso else None),
        "tarifa_regla": (ingreso.tarifa.regla if ingreso.tipo != "libre" else "ingreso_libre") if ingreso else None,
        "boleto_combinado": ingreso.tarifa.combinada if ingreso else None,
        "abre": epoca.abre if epoca else None,
        "cierra": epoca.cierra if epoca else None,
        "dias": "|".join(DIAS_CORTOS[d] for d in epoca.dias) if epoca and epoca.dias is not None else None,
        "epoca": epoca.epoca if epoca else None,
        "epoca_observaciones": epoca.observaciones if epoca else None,
        **resumen_acceso(f.tramos),
        "visitantes_anio": ultimo,
        "visitantes_nacionales": visitantes["nacionales"].cantidad if "nacionales" in visitantes else None,
        "visitantes_extranjeros": visitantes["extranjeros"].cantidad if "extranjeros" in visitantes else None,
        "visitantes_locales": visitantes["locales"].cantidad if "locales" in visitantes else None,
        "actividades": [a.actividad for a in f.actividades],
        "alimentacion_cerca": _tiene(f.servicios_dentro + f.servicios_fuera, "Alimentación"),
        "alojamiento_cerca": _tiene(f.servicios_fuera, "Alojamiento"),
        "accesible_silla_ruedas": any("discapacidad" in a.lower() for a in f.accesibilidad),
        "descripcion_corta": descripcion_corta(f.descripcion),
        "foto_url": f.foto_url,
    }


# ── Distancias ──────────────────────────────────────────────────────────────────────


def haversine_km(lat1, lon1, lat2, lon2) -> np.ndarray:
    la1, lo1, la2, lo2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = np.sin((la2 - la1) / 2) ** 2 + np.cos(la1) * np.cos(la2) * np.sin((lo2 - lo1) / 2) ** 2
    return 2 * R_TIERRA_KM * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def distancia_efectiva_km(lat, lon, alt, lat2, lon2, alt2) -> np.ndarray:
    """La distancia del modelo v2: haversine más el desnivel a 0,06 km por metro.
    Si falta una altitud, cuenta solo la distancia horizontal."""
    d = haversine_km(lat, lon, lat2, lon2)
    dz = np.abs(np.asarray(alt, float) - np.asarray(alt2, float)) * K_DESNIVEL
    return np.sqrt(d**2 + np.nan_to_num(dz, nan=0.0) ** 2)


def distancia_a_su_distrito(tabla: pd.DataFrame, minimo: int = 3) -> pd.Series:
    """Km de cada recurso a la mediana de los demás recursos de su mismo distrito.

    Un recurso a cientos de km de sus vecinos de distrito tiene la coordenada mal
    ("Ceviche De Camarón", de Cocachacra, cae a 772 km). Solo se calcula en distritos
    con al menos ``minimo`` recursos más, para que la mediana sea confiable.
    """
    distancia = pd.Series(np.nan, index=tabla.index)
    con_punto = tabla[tabla["lat"].notna()]
    for _, grupo in con_punto.groupby(["region", "provincia", "distrito"], sort=False):
        if len(grupo) <= minimo:
            continue
        lat, lon = grupo["lat"].to_numpy(), grupo["lon"].to_numpy()
        for posicion, indice in enumerate(grupo.index):
            otros = np.arange(len(grupo)) != posicion
            distancia[indice] = float(
                haversine_km(lat[posicion], lon[posicion], np.median(lat[otros]), np.median(lon[otros]))
            )
    return distancia


# ── Polos ───────────────────────────────────────────────────────────────────────────


def asignar_polos(tabla: pd.DataFrame, v2: pd.DataFrame) -> pd.DataFrame:
    """Polo de cada recurso: el del modelo v2 si sigue valiendo; si no, uno que lo acepte.

    ``tabla`` necesita codigo, categoria_num, lat, lon, altitud_m y coordenada_revisar.
    ``v2`` necesita codigo, lat_v2, lon_v2, alt_v2 y polo_v2 (−1 = sin polo en v2).

    - Un recurso de v2 conserva su polo si su coordenada no cambió, o si cambió pero
      sigue a menos de 80 km efectivos de todos los demás miembros.
    - Los recursos que no estaban en v2 (los 65 nuevos y los 1 245 que no tenían
      coordenadas) y los que tuvieron que salir de su polo se asignan uno por uno al
      polo cuyo miembro más lejano está más cerca, si está a 80 km o menos: así cada
      polo sigue cumpliendo el diámetro máximo del modelo v2.
    - Los lugares (categorías 1, 2 y 4) pasan a ser miembros del polo. El folclore y
      los acontecimientos se asocian al polo, pero no cuentan para el diámetro: no son
      paradas.
    - Un recurso con la coordenada a revisar no se asigna.
    """
    t = tabla.merge(v2, on="codigo", how="left")
    movido = haversine_km(t["lat"], t["lon"], t["lat_v2"], t["lon_v2"]) > SE_MOVIO_KM
    # Altitud para la distancia efectiva: la del modelo v2 si la coordenada es la misma.
    alt = np.where(t["polo_v2"].notna() & ~movido, t["alt_v2"], t["altitud_m"])
    lat, lon = t["lat"].to_numpy(float), t["lon"].to_numpy(float)
    lugar = t["categoria_num"].isin(CATEGORIAS_LUGAR).to_numpy()
    revisar = t["coordenada_revisar"].fillna(False).to_numpy(bool)

    polo = np.full(len(t), -1, dtype=int)
    fuente = np.array([None] * len(t), dtype=object)
    miembros: dict[int, list[int]] = {}
    for i, p in enumerate(t["polo_v2"]):
        if pd.notna(p) and p >= 0 and not np.isnan(lat[i]) and not revisar[i]:
            miembros.setdefault(int(p), []).append(i)

    def diametro_con(i: int, integrantes: list[int]) -> float:
        otros = [j for j in integrantes if j != i]
        if not otros:
            return 0.0
        return float(distancia_efectiva_km(lat[i], lon[i], alt[i], lat[otros], lon[otros], alt[otros]).max())

    pendientes = []
    for i in range(len(t)):
        p = t["polo_v2"].iloc[i]
        if pd.isna(p):
            if not np.isnan(lat[i]) and not revisar[i]:
                pendientes.append(i)
            else:
                fuente[i] = "sin_coordenada" if np.isnan(lat[i]) else "coordenada_revisar"
            continue
        if p < 0:
            fuente[i] = "v2_sin_polo"
            continue
        if revisar[i] or np.isnan(lat[i]):
            fuente[i] = "coordenada_revisar"
            continue
        if not movido[i] or diametro_con(i, miembros[int(p)]) <= DIAMETRO_MAX:
            polo[i], fuente[i] = int(p), "v2"
        else:
            miembros[int(p)].remove(i)
            pendientes.append(i)

    centro = {p: (lat[ix].mean(), lon[ix].mean()) for p, ix in miembros.items()}
    # Primero los lugares, que fijan el diámetro; luego acontecimientos y folclore.
    pendientes.sort(key=lambda i: (not lugar[i], int(t["categoria_num"].iloc[i] or 9), int(t["codigo"].iloc[i])))
    for i in pendientes:
        mejor, mejor_d = -1, np.inf
        for p, ix in miembros.items():
            if haversine_km(lat[i], lon[i], *centro[p]) > DIAMETRO_MAX * 1.5:
                continue
            d = diametro_con(i, ix)
            if d <= DIAMETRO_MAX and d < mejor_d:
                mejor, mejor_d = p, d
        estaba_en_v2 = pd.notna(t["polo_v2"].iloc[i])
        if mejor >= 0:
            polo[i] = mejor
            fuente[i] = "v2_revisado" if estaba_en_v2 else "asignado_v3"
            if lugar[i]:
                miembros[mejor].append(i)
        else:
            fuente[i] = "salio_de_su_polo" if estaba_en_v2 else "sin_polo_cercano"
    return pd.DataFrame({"codigo": t["codigo"], "polo": polo, "polo_fuente": fuente})


# ── Construcción ────────────────────────────────────────────────────────────────────

COLUMNAS = [
    "codigo",
    "nombre",
    "nombre_ficha",
    "region",
    "provincia",
    "distrito",
    "categoria_num",
    "categoria",
    "tipo",
    "subtipo",
    "url_ficha",
    "tiene_ficha",
    "lat",
    "lon",
    "coordenada",
    "distancia_distrito_km",
    "coordenada_revisar",
    "coordenada_motivo",
    "polo",
    "polo_fuente",
    "jerarquia",
    "jerarquia_texto",
    "altitud_m",
    "altitud_fuente",
    "altitud_ficha_m",
    "altitud_ficha_max_m",
    "altitud_dem_m",
    "altitud_revisar",
    "es_parada",
    "motivo_no_parada",
    "intereses",
    "actividades",
    "visita_min",
    "visita_min_fuente",
    "ingreso",
    "tarifa_soles",
    "tarifa_regla",
    "boleto_combinado",
    "abre",
    "cierra",
    "dias",
    "epoca",
    "epoca_observaciones",
    "acceso_km",
    "acceso_min",
    "acceso_desde",
    "caminata_min",
    "acceso_acuatico",
    "acceso_aereo",
    "ultimo_medio",
    "ultimo_via",
    "recorridos",
    "visitantes_anio",
    "visitantes_nacionales",
    "visitantes_extranjeros",
    "visitantes_locales",
    "alimentacion_cerca",
    "alojamiento_cerca",
    "accesible_silla_ruedas",
    "descripcion_corta",
    "foto_url",
    "fecha_corte",
]

DISTANCIA_DISTRITO_REVISAR_KM = 100.0
SUBTIPOS_COSTEROS = {"Playas", "Caletas", "Bahías", "Puntas", "Penínsulas", "Manglares", "Esteros", "Islas"}
ALTITUD_MAX_COSTA_M = 200.0


PREPOSICIONES = {"de", "del", "y", "e", "o", "u", "en", "a", "al", "con", "por", "para", "sin", "sobre"}
ARTICULOS = {"el", "la", "los", "las"}


def nombre_legible(nombre: str) -> str:
    """ "Festividad Del Señor De Los Temblores" → "Festividad del Señor de los Temblores".

    MINCETUR escribe cada palabra con mayúscula. Las preposiciones y conjunciones van en
    minúscula (salvo al inicio), y los artículos solo después de una preposición: en
    "Playa La Mina" el "La" es parte del nombre. Las siglas quedan como están.
    """
    palabras = nombre.split()
    legibles = []
    for i, palabra in enumerate(palabras):
        minuscula = palabra.lower()
        anterior = palabras[i - 1].lower() if i else ""
        es_menor = minuscula in PREPOSICIONES or (minuscula in ARTICULOS and anterior in PREPOSICIONES)
        sigla = palabra.isupper() and len(palabra) > 1
        legibles.append(minuscula if i and es_menor and not sigla else palabra)
    return " ".join(legibles)


def _motivo_no_parada(fila: pd.Series) -> str | None:
    """Por qué un recurso no puede ser una parada del itinerario; None si puede."""
    if fila["categoria_num"] not in CATEGORIAS_LUGAR:
        return "folclore" if fila["categoria_num"] == 3 else "acontecimiento"
    if pd.isna(fila["lat"]):
        return "sin_coordenada"
    if fila["coordenada_revisar"]:
        return "coordenada_revisar"
    if not fila["tiene_ficha"]:
        return "sin_ficha"
    if fila["tipo"] == "Montañas" and pd.notna(fila["altitud_m"]) and fila["altitud_m"] > ALTITUD_CUMBRE_M:
        return "cumbre"  # un nevado se contempla desde abajo; subirlo es una expedición
    return None


def construir(inventario: pd.DataFrame, fichas: dict[int, Ficha], v2: pd.DataFrame) -> pd.DataFrame:
    """El maestro v3. ``v2`` es polos_asignados_v2.csv con sus columnas originales."""
    intereses = ReglasIntereses.cargar()
    duracion = ReglasDuracion.cargar()

    tabla = inventario.copy()
    tabla["nombre"] = tabla["nombre"].map(nombre_legible)
    tabla["distrito"] = tabla["distrito"].map(lambda d: nombre_legible(d.title()) if isinstance(d, str) else d)
    tabla["url_ficha"] = tabla["codigo"].map(lambda c: URL_FICHA.format(codigo=c))
    tabla["tiene_ficha"] = tabla["codigo"].isin(fichas)
    de_fichas = pd.DataFrame([{"codigo": c, **resumen_ficha(f)} for c, f in fichas.items()])
    tabla = tabla.merge(de_fichas, on="codigo", how="left")

    v2 = v2.rename(
        columns={
            "CODIGO DEL RECURSO": "codigo",
            "latitud": "lat_v2",
            "longitud": "lon_v2",
            "ALTITUD": "alt_v2",
            "POLO": "polo_v2",
        }
    )[["codigo", "lat_v2", "lon_v2", "alt_v2", "polo_v2"]]
    con_v2 = tabla.merge(v2, on="codigo", how="left")
    misma_coordenada = haversine_km(con_v2["lat"], con_v2["lon"], con_v2["lat_v2"], con_v2["lon_v2"]) <= SE_MOVIO_KM
    tabla["altitud_dem_m"] = np.where(misma_coordenada, con_v2["alt_v2"], np.nan)

    # Coordenada a revisar:
    # - a más de 100 km de los demás recursos de su distrito, salvo que la altitud del
    #   modelo de elevación en ese punto coincida con la de la ficha: un parque nacional
    #   o un distrito amazónico enorme pueden estar lejos de la mediana y bien ubicados;
    # - una playa que la ficha pone a nivel del mar y el modelo de elevación en la sierra
    #   ("Playa Quita Calzón": 3 m en la ficha, 1 369 m en su coordenada). Las playas e
    #   islas del Titicaca y de los ríos de la selva también se llaman así, pero su ficha
    #   ya dice su altura.
    tabla["distancia_distrito_km"] = distancia_a_su_distrito(tabla).round(1)
    altura_confirma = (tabla["altitud_ficha_max_m"] - tabla["altitud_dem_m"]).abs() <= DISCREPANCIA_ALTITUD_M
    lejos = (tabla["distancia_distrito_km"] > DISTANCIA_DISTRITO_REVISAR_KM) & ~altura_confirma
    costa_en_altura = (
        tabla["subtipo"].isin(SUBTIPOS_COSTEROS)
        & (tabla["altitud_ficha_max_m"] < ALTITUD_MAX_COSTA_M)
        & (tabla["altitud_dem_m"] - tabla["altitud_ficha_max_m"] > DISCREPANCIA_ALTITUD_M)
    )
    tabla["coordenada_motivo"] = np.select([lejos, costa_en_altura], ["lejos_de_su_distrito", "costa_en_altura"], None)
    tabla["coordenada_revisar"] = tabla["coordenada_motivo"].notna()

    # Altitud: la de la ficha (la más alta si da un rango). Si la ficha y el modelo de
    # elevación (en la misma coordenada que usó v2) difieren en más de 500 m, manda el
    # modelo, salvo que la coordenada esté a revisar: "Cañón del Colca: 3" en la ficha
    # frente a 2 215 m en el modelo es un error de tipeo; un jardín botánico de la selva
    # a 4 096 m es una coordenada mal puesta.
    ficha, dem = tabla["altitud_ficha_max_m"], tabla["altitud_dem_m"]
    tabla["altitud_revisar"] = (ficha - dem).abs() > DISCREPANCIA_ALTITUD_M
    manda_dem = dem.notna() & (ficha.isna() | (tabla["altitud_revisar"] & ~tabla["coordenada_revisar"]))
    tabla["altitud_m"] = np.where(manda_dem, dem, ficha)
    tabla["altitud_fuente"] = np.select([manda_dem, ficha.notna()], ["dem_open_meteo", "ficha"], None)

    tabla = tabla.merge(asignar_polos(tabla, v2), on="codigo", how="left")

    actividades = tabla["actividades"].map(lambda a: a if isinstance(a, list) else [])
    tabla["intereses"] = [
        "|".join(intereses.de(c, t, s, a))
        for c, t, s, a in zip(tabla["categoria_num"], tabla["tipo"], tabla["subtipo"], actividades, strict=True)
    ]
    tabla["actividades"] = actividades.map("|".join)
    visita = [
        duracion.de(c, t, s) for c, t, s in zip(tabla["categoria_num"], tabla["tipo"], tabla["subtipo"], strict=True)
    ]
    tabla["visita_min"] = [m for m, _ in visita]
    tabla["visita_min_fuente"] = [f for _, f in visita]
    tabla["motivo_no_parada"] = tabla.apply(_motivo_no_parada, axis=1)
    tabla["es_parada"] = tabla["motivo_no_parada"].isna()
    for columna in ENTEROS:
        tabla[columna] = tabla[columna].round().astype("Int64")
    return tabla[COLUMNAS].sort_values("codigo", ignore_index=True)


def resumen(maestro: pd.DataFrame) -> dict[str, object]:
    """Cobertura de cada campo y de dónde sale: lo que la documentación cita."""
    lugares = maestro[maestro["categoria_num"].isin(CATEGORIAS_LUGAR)]

    def conteo(columna: str, tabla: pd.DataFrame = maestro) -> dict[str, int]:
        return {str(k): int(v) for k, v in Counter(tabla[columna].fillna("—")).most_common()}

    return {
        "version": VERSION,
        "recursos": len(maestro),
        "fecha_corte_inventario": sorted(maestro["fecha_corte"].dropna().unique().tolist()),
        "con_ficha": int(maestro["tiene_ficha"].sum()),
        "paradas_posibles": int(maestro["es_parada"].sum()),
        "motivo_no_parada": conteo("motivo_no_parada"),
        "coordenada": conteo("coordenada"),
        "coordenada_revisar": int(maestro["coordenada_revisar"].sum()),
        "coordenada_motivo": conteo("coordenada_motivo"),
        "polo_fuente": conteo("polo_fuente"),
        "polos": int(maestro.loc[maestro["polo"] >= 0, "polo"].nunique()),
        "altitud_fuente": conteo("altitud_fuente"),
        "altitud_revisar": int(maestro["altitud_revisar"].sum()),
        "lugares": {
            "total": len(lugares),
            "con_jerarquia": int(lugares["jerarquia"].notna().sum()),
            "con_tarifa": int(lugares["tarifa_soles"].notna().sum()),
            "con_horario": int(lugares["abre"].notna().sum()),
            "con_acceso": int(lugares["acceso_min"].notna().sum()),
            "con_visitantes": int(lugares["visitantes_anio"].notna().sum()),
            "con_intereses": int((lugares["intereses"] != "").sum()),
            "ingreso": conteo("ingreso", lugares),
        },
        "intereses": {
            i: int(maestro["intereses"].str.split("|").map(lambda xs, i=i: i in xs).sum()) for i in INTERESES
        },
    }


def leer_fichas(carpeta: Path, codigos: set[int] | None = None) -> dict[int, Ficha]:
    """Las fichas guardadas en ``carpeta``; solo las de ``codigos`` si se da."""
    fichas = {}
    for ruta in sorted(carpeta.glob("*.html.gz")):
        if codigos is not None and int(ruta.name.split(".")[0]) not in codigos:
            continue
        ficha = leer_archivo(ruta)
        fichas[ficha.codigo] = ficha
    return fichas


def main() -> None:
    ap = argparse.ArgumentParser(description="Construye el maestro v3 de recursos turísticos.")
    ap.add_argument("--inventario", type=Path, default=EXTERNOS / "inventario" / "Inventario_recursos_turisticos.csv")
    ap.add_argument("--fichas", type=Path, default=EXTERNOS / "fichas_html")
    ap.add_argument("--polos-v2", type=Path, default=POLOS_V2)
    ap.add_argument("--salida", type=Path, default=PROCESADOS)
    a = ap.parse_args()

    inventario = leer_inventario(a.inventario)
    fichas = leer_fichas(a.fichas)
    v2 = pd.read_csv(a.polos_v2, sep=";")
    maestro = construir(inventario, fichas, v2)

    a.salida.mkdir(parents=True, exist_ok=True)
    maestro.to_csv(a.salida / "maestro_v3.csv", sep=";", index=False, encoding="utf-8-sig", lineterminator="\n")
    datos = resumen(maestro)
    (a.salida / "maestro_v3_resumen.json").write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        f"{datos['recursos']} recursos · {datos['con_ficha']} con ficha · {datos['paradas_posibles']} paradas posibles"
    )
    print(f"polos: {datos['polos']} · {datos['polo_fuente']}")
    print(f"Escrito en {a.salida}")


if __name__ == "__main__":
    main()

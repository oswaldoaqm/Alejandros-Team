"""
Lectura del Inventario Nacional de Recursos Turísticos de MINCETUR (datos abiertos).

El archivo lo baja pipeline/adquisicion/descargar_inventario.py. Trae tres problemas que
este módulo corrige y deja a la vista en la columna ``coordenada``:

1. Está en Windows-1252, no en Latin-1: las comillas “ ”, el apóstrofo ’ y la raya –
   de nombres como "Puente Colgante De Q’Eswachaka" se pierden si se lee como Latin-1.
2. LATITUD y LONGITUD vienen intercambiadas (en el corte 20260929, en todas las filas).
   Se corrige fila por fila: el valor que cae en el rango de latitudes del Perú es la
   latitud. Si un corte futuro las trae bien, también se detecta.
3. Un punto decimal corrido, como -780558.0373798 por -78.0558037 (Tauca, Áncash). Se
   repara solo si al moverlo el valor cae dentro del Perú, y queda marcado.

    from pipeline.inventario import leer_inventario
    inventario = leer_inventario("data/externos/inventario/Inventario_recursos_turisticos.csv")
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from pipeline.texto import limpio

CODIFICACION = "cp1252"

# Caja que contiene al Perú, con margen para islas y fronteras.
LATITUD_PERU = (-18.4, 0.1)
LONGITUD_PERU = (-81.4, -68.6)

COLUMNAS = {
    "CODIGO DEL RECURSO": "codigo",
    "NOMBRE DEL RECURSO": "nombre",
    "REGIÓN": "region",
    "PROVINCIA": "provincia",
    "DISTRITO": "distrito",
    "CATEGORÍA": "categoria_texto",
    "TIPO DE CATEGORÍA": "tipo_texto",
    "SUB TIPO CATEGORÍA": "subtipo",
    "URL": "url",
    "LATITUD": "latitud_original",
    "LONGITUD": "longitud_original",
    "FECHA_DE_CORTE": "fecha_corte",
}


@dataclass(frozen=True, slots=True)
class Coordenada:
    lat: float | None
    lon: float | None
    estado: str  # correcta, intercambiada, reparada, sin_coordenada, invalida


def _en(valor: float, rango: tuple[float, float]) -> bool:
    return rango[0] <= valor <= rango[1]


def _numero(texto: str | None) -> float | None:
    t = limpio(texto)
    if t is None:
        return None
    try:
        return float(t.replace(",", "."))
    except ValueError:
        return None


def _con_punto_corrido(valor: float, rango: tuple[float, float]) -> float | None:
    """-780558.0373798 → -78.0558037: el único corrimiento del punto que cae en el rango."""
    digitos = re.sub(r"\D", "", f"{abs(valor):.10f}").lstrip("0")
    signo = -1 if valor < 0 else 1
    candidatos = []
    for enteros in (1, 2):
        if len(digitos) > enteros:
            candidato = signo * float(f"{digitos[:enteros]}.{digitos[enteros:]}")
            if _en(candidato, rango):
                candidatos.append(candidato)
    return candidatos[0] if len(candidatos) == 1 else None


def leer_coordenada(latitud: str | None, longitud: str | None) -> Coordenada:
    """La coordenada de una fila, corrigiendo el intercambio y el punto corrido."""
    a, b = _numero(latitud), _numero(longitud)
    if a is None or b is None:
        return Coordenada(None, None, "sin_coordenada")
    if _en(a, LATITUD_PERU) and _en(b, LONGITUD_PERU):
        return Coordenada(a, b, "correcta")
    if _en(a, LONGITUD_PERU) and _en(b, LATITUD_PERU):
        return Coordenada(b, a, "intercambiada")
    # Un solo valor fuera de rango: se intenta reparar con el otro como referencia.
    for lat_cruda, lon_cruda in ((a, b), (b, a)):
        if _en(lat_cruda, LATITUD_PERU) and not _en(lon_cruda, LONGITUD_PERU):
            lon = _con_punto_corrido(lon_cruda, LONGITUD_PERU)
            if lon is not None:
                return Coordenada(lat_cruda, lon, "reparada")
        if _en(lon_cruda, LONGITUD_PERU) and not _en(lat_cruda, LATITUD_PERU):
            lat = _con_punto_corrido(lat_cruda, LATITUD_PERU)
            if lat is not None:
                return Coordenada(lat, lon_cruda, "reparada")
    return Coordenada(None, None, "invalida")


def leer_inventario(ruta: str | Path) -> pd.DataFrame:
    """Una fila por recurso, con coordenadas corregidas y categoría separada en número y nombre.

    Columnas: codigo, nombre, region, provincia, distrito, categoria_num, categoria, tipo,
    subtipo, url, lat, lon, coordenada, latitud_original, longitud_original, fecha_corte.
    """
    texto = Path(ruta).read_bytes().decode(CODIFICACION)
    filas = list(csv.DictReader(io.StringIO(texto, newline=""), delimiter=";"))
    faltan = set(COLUMNAS) - set(filas[0] if filas else {})
    if faltan:
        raise ValueError(f"al inventario le faltan columnas: {sorted(faltan)}")
    registros = []
    for fila in filas:
        r = {nuevo: limpio(fila.get(original)) for original, nuevo in COLUMNAS.items()}
        coordenada = leer_coordenada(r["latitud_original"], r["longitud_original"])
        categoria = re.match(r"(\d)\.\s*(.+)", r["categoria_texto"] or "")
        r.update(
            codigo=int(r["codigo"]),
            categoria_num=int(categoria.group(1)) if categoria else None,
            categoria=categoria.group(2).capitalize() if categoria else r["categoria_texto"],
            tipo=re.sub(r"^[a-zñ]\.\s*", "", r["tipo_texto"]) if r["tipo_texto"] else None,
            lat=coordenada.lat,
            lon=coordenada.lon,
            coordenada=coordenada.estado,
        )
        registros.append(r)
    tabla = pd.DataFrame(registros)
    if tabla["codigo"].duplicated().any():
        repetidos = tabla.loc[tabla["codigo"].duplicated(), "codigo"].tolist()
        raise ValueError(f"códigos repetidos en el inventario: {repetidos[:10]}")
    columnas = [
        "codigo",
        "nombre",
        "region",
        "provincia",
        "distrito",
        "categoria_num",
        "categoria",
        "tipo",
        "subtipo",
        "url",
        "lat",
        "lon",
        "coordenada",
        "latitud_original",
        "longitud_original",
        "fecha_corte",
    ]
    return tabla[columnas].sort_values("codigo", ignore_index=True)

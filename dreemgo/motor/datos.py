"""
Los artefactos que arma ``pipeline/artefactos.py``, cargados una vez al arrancar.

Todo queda en memoria y de solo lectura: recursos y eventos en diccionarios, y los tiempos
de cada polo en matrices de numpy (minutos y km, con ``nan`` donde no hay camino; y cuántos
de esos km van en tren y en bote, con 0 donde no van).
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

import numpy as np

DATOS = Path(__file__).resolve().parents[1] / "datos"


@dataclass(frozen=True)
class Polo:
    id: int
    nombre: str
    region: str
    regiones: tuple[str, ...]
    recursos: int
    fuera_del_circuito: bool
    novedad: float
    base: dict
    paradas: tuple[str, ...]  # códigos, en el orden de las matrices
    base_minutos: np.ndarray  # base → parada, y de vuelta
    base_km: np.ndarray
    entre_minutos: np.ndarray  # parada → parada
    entre_km: np.ndarray
    clima: tuple[dict, ...]  # 12 meses, de enero a diciembre
    eventos: tuple[str, ...]
    base_km_tren: np.ndarray  # de los km de la base a cada parada, los que van en tren
    base_km_bote: np.ndarray
    entre_km_tren: np.ndarray
    entre_km_bote: np.ndarray

    def indice(self) -> dict[str, int]:
        return {c: i for i, c in enumerate(self.paradas)}


@dataclass(frozen=True)
class Origen:
    id: str
    nombre: str
    region: str
    lat: float
    lon: float
    a_base: dict[int, tuple[float, float]]  # polo → (minutos, km); nan si no hay camino
    a_parada: dict[str, tuple[float, float]]  # solo las paradas a menos de 4 horas
    a_base_en_capa: dict[int, tuple[float, float]]  # polo → (km en tren, km en bote)
    a_parada_en_capa: dict[str, tuple[float, float]]


@dataclass(frozen=True)
class Datos:
    version: str
    recursos: dict[str, dict]
    polos: dict[int, Polo]
    origenes: dict[str, Origen]
    eventos: dict[str, dict]
    costos: dict[str, dict]
    intereses: dict[str, dict]
    atribucion: tuple[str, ...]
    fuentes: dict = field(default_factory=dict)


def _gz(ruta: Path):
    with gzip.open(ruta, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def _arreglo(valores) -> np.ndarray:
    return np.array([np.nan if v is None else v for v in valores], dtype=float)


def _matriz(filas) -> np.ndarray:
    if not filas:
        return np.zeros((0, 0))
    return np.array([[np.nan if v is None else v for v in fila] for fila in filas], dtype=float)


def _en_capa(p: dict, clave: str, forma: tuple[int, ...]) -> np.ndarray:
    """Los km en tren o en bote de un polo; ceros si ningún camino suyo va en ellos."""
    if clave not in p:
        return np.zeros(forma)
    valores = p[clave]
    return _matriz(valores) if len(forma) == 2 else _arreglo(valores)


def _polo(p: dict) -> Polo:
    n = len(p["paradas"])
    return Polo(
        id=p["id"],
        nombre=p["nombre"],
        region=p["region"],
        regiones=tuple(p["regiones"]),
        recursos=p["recursos"],
        fuera_del_circuito=p["fuera_del_circuito"],
        novedad=p["novedad"],
        base=p["base"],
        paradas=tuple(p["paradas"]),
        base_minutos=_arreglo(p["base_minutos"]),
        base_km=_arreglo(p["base_km"]),
        entre_minutos=_matriz(p["entre_minutos"]),
        entre_km=_matriz(p["entre_km"]),
        clima=tuple(p["clima"]),
        eventos=tuple(p["eventos"]),
        base_km_tren=_en_capa(p, "base_km_tren", (n,)),
        base_km_bote=_en_capa(p, "base_km_bote", (n,)),
        entre_km_tren=_en_capa(p, "entre_km_tren", (n, n)),
        entre_km_bote=_en_capa(p, "entre_km_bote", (n, n)),
    )


def _origen(o: dict) -> Origen:
    def par(v):
        return (np.nan if v[0] is None else v[0], np.nan if v[1] is None else v[1])

    def en_capa(v):  # [minutos, km, km en tren, km en bote]; los de antes no traen los dos últimos
        return tuple(0.0 if len(v) <= k or v[k] is None else v[k] for k in (2, 3))

    return Origen(
        id=o["id"],
        nombre=o["nombre"],
        region=o["region"],
        lat=o["lat"],
        lon=o["lon"],
        a_base={int(k): par(v) for k, v in o["a_base"].items()},
        a_parada={k: par(v) for k, v in o["a_parada"].items()},
        a_base_en_capa={int(k): en_capa(v) for k, v in o["a_base"].items()},
        a_parada_en_capa={k: en_capa(v) for k, v in o["a_parada"].items()},
    )


@cache
def cargar(carpeta: Path = DATOS) -> Datos:
    """Los artefactos de ``carpeta``. Falla con FileNotFoundError si no están."""
    manifiesto = json.loads((carpeta / "manifiesto.json").read_text(encoding="utf-8"))
    return Datos(
        version=manifiesto["version_datos"],
        recursos={r["codigo"]: r for r in _gz(carpeta / "recursos.json.gz")},
        polos={p["id"]: _polo(p) for p in _gz(carpeta / "polos.json.gz")},
        origenes={o["id"]: _origen(o) for o in _gz(carpeta / "origenes.json.gz")},
        eventos={e["id"]: e for e in _gz(carpeta / "eventos.json.gz")},
        costos=json.loads((carpeta / "costos.json").read_text(encoding="utf-8")),
        intereses=manifiesto["intereses"],
        atribucion=tuple(manifiesto["atribucion"]),
        fuentes=manifiesto["fuentes"],
    )


def hay_datos(carpeta: Path = DATOS) -> bool:
    return (carpeta / "manifiesto.json").exists()

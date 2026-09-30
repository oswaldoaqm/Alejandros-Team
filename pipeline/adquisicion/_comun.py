"""
Utilidades compartidas por los scripts de adquisición.

Estos son los únicos scripts del proyecto que salen a internet. Se corren en la
máquina de un integrante (Git Bash o cualquier terminal con Python 3.11+),
porque los entornos automatizados donde se desarrolla el resto no alcanzan las
fuentes: MINCETUR, Open-Meteo y Geofabrik.

Todo lo que bajan va a data/externos/, que está fuera de git. Lo que sí entra
al repositorio son los artefactos que el pipeline construye a partir de ahí.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
EXTERNOS = RAIZ / "data" / "externos"

# Agente identificado: quien administra el servidor puede saber quién pide y
# dónde está el proyecto. Sin correo personal en el código.
AGENTE = "DreemGO/1.0 (proyecto academico UTEC DS3022; https://github.com/oswaldoaqm/Alejandros-Team)"


def utf8_consola() -> None:
    """Git Bash en Windows no siempre imprime en UTF-8; sin esto, una tilde
    puede tumbar el script a mitad de una descarga de horas."""
    for flujo in (sys.stdout, sys.stderr):
        try:
            flujo.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def ahora_utc() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def md5_archivo(ruta: Path, bloque: int = 1 << 20) -> str:
    h = hashlib.md5()
    with open(ruta, "rb") as fh:
        for trozo in iter(lambda: fh.read(bloque), b""):
            h.update(trozo)
    return h.hexdigest()


def escribir_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(ruta)  # escritura atómica: nunca queda un JSON a medias


def miles(n: float) -> str:
    """12345 -> '12 345', como en el resto de la documentación."""
    return f"{n:,.0f}".replace(",", " ")

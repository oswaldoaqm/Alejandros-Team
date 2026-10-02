"""
Dónde se guardan los eventos publicados: en memoria, que sirve para desarrollar y se pierde al
reiniciar, o en un archivo local, una línea de JSON por evento.

Un almacén guarda y devuelve registros: diccionarios de tipos simples con ``id`` (ver
``Publicado.registro``). Guardar dos veces el mismo ``id`` deja el último.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Protocol

bitacora = logging.getLogger("dreemgo.almacen")


class Almacen(Protocol):
    def leer(self) -> list[dict]:
        """Todos los registros guardados."""
        ...

    def guardar(self, registro: dict) -> None:
        """Guarda un registro; si ya había uno con ese ``id``, lo reemplaza."""
        ...


class EnMemoria:
    def __init__(self) -> None:
        self._registros: dict[str, dict] = {}

    def leer(self) -> list[dict]:
        return [dict(r) for r in self._registros.values()]

    def guardar(self, registro: dict) -> None:
        self._registros[registro["id"]] = dict(registro)


class EnArchivo:
    """Una línea de JSON por cada vez que se guarda; al leer, de cada ``id`` vale la última.

    El archivo solo crece. Alcanza para un servidor del curso; para algo que dure, DynamoDB.
    """

    def __init__(self, ruta: Path) -> None:
        self._ruta = Path(ruta)

    def leer(self) -> list[dict]:
        if not self._ruta.exists():
            return []
        registros: dict[str, dict] = {}
        for numero, linea in enumerate(self._ruta.read_text(encoding="utf-8").splitlines(), 1):
            if not linea.strip():
                continue
            try:
                registro = json.loads(linea)
                registros[registro["id"]] = registro
            except (ValueError, KeyError, TypeError):  # una línea a medio escribir no tumba a las demás
                bitacora.warning("%s: la línea %d no es un evento y se salta.", self._ruta, numero)
        return list(registros.values())

    def guardar(self, registro: dict) -> None:
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._ruta.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")

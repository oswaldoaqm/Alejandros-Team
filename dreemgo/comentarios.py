"""Buzón breve del sitio. Se guarda aparte de la analítica de uso."""

from __future__ import annotations

import os
import sqlite3
from contextlib import closing
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, field_validator

RAIZ = Path(__file__).resolve().parents[1]
BASE_POR_DEFECTO = (
    Path("/tmp/dreemgo/comentarios.sqlite3")
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    else Path.home() / ".dreemgo" / "comentarios.sqlite3"
)
MAX_COMENTARIOS_POR_HORA = 3
_PREPARAR_BASE = Lock()

Categoria = Literal["duda", "sugerencia", "problema"]


class ComentarioNuevo(BaseModel):
    """La sesión limita envíos repetidos; no se pide nombre ni correo."""

    model_config = ConfigDict(extra="forbid")

    sesion: UUID
    categoria: Categoria
    mensaje: str

    @field_validator("mensaje")
    @classmethod
    def mensaje_breve(cls, valor: str) -> str:
        limpio = valor.strip()
        if not 10 <= len(limpio) <= 1000:
            raise ValueError("Escribe un mensaje de 10 a 1000 caracteres.")
        return limpio


class ComentarioRecibido(BaseModel):
    id: UUID
    estado: Literal["recibido"] = "recibido"


class ComentarioEquipo(BaseModel):
    id: UUID
    categoria: Categoria
    mensaje: str
    instante: datetime


class Buzon(BaseModel):
    total: int
    comentarios: list[ComentarioEquipo]


class DemasiadosComentarios(Exception):
    """La misma sesión superó el límite de mensajes de la última hora."""


def _ruta_base() -> Path:
    configurada = os.environ.get("DREEMGO_COMENTARIOS_DB")
    if not configurada:
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
            return Path("/tmp/dreemgo/comentarios.sqlite3")
        return BASE_POR_DEFECTO
    ruta = Path(configurada).expanduser()
    return ruta if ruta.is_absolute() else RAIZ / ruta


def _abrir() -> sqlite3.Connection:
    ruta = _ruta_base()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta, timeout=5)
    conexion.execute("PRAGMA busy_timeout = 5000")
    try:
        with _PREPARAR_BASE:
            conexion.execute("PRAGMA journal_mode = WAL")
            conexion.execute(
                """CREATE TABLE IF NOT EXISTS comentarios (
                    id TEXT PRIMARY KEY,
                    instante TEXT NOT NULL,
                    sesion TEXT NOT NULL,
                    categoria TEXT NOT NULL,
                    mensaje TEXT NOT NULL
                )"""
            )
            conexion.execute("CREATE INDEX IF NOT EXISTS idx_comentarios_sesion_hora ON comentarios(sesion, instante)")
            conexion.execute("CREATE INDEX IF NOT EXISTS idx_comentarios_instante ON comentarios(instante)")
            conexion.commit()
    except sqlite3.Error:
        conexion.close()
        raise
    return conexion


def guardar(nuevo: ComentarioNuevo, instante: datetime | None = None) -> ComentarioRecibido:
    """Asigna hora e identificador en el servidor y limita la misma sesión."""

    ahora = (instante or datetime.now(UTC)).astimezone(UTC)
    desde = (ahora - timedelta(hours=1)).isoformat(timespec="microseconds")
    identificador = uuid4()
    with closing(_abrir()) as conexion, conexion:
        conexion.execute("BEGIN IMMEDIATE")
        cantidad = conexion.execute(
            "SELECT COUNT(*) FROM comentarios WHERE sesion = ? AND instante >= ?",
            (str(nuevo.sesion), desde),
        ).fetchone()[0]
        if cantidad >= MAX_COMENTARIOS_POR_HORA:
            raise DemasiadosComentarios
        conexion.execute(
            "INSERT INTO comentarios(id, instante, sesion, categoria, mensaje) VALUES (?, ?, ?, ?, ?)",
            (
                str(identificador),
                ahora.isoformat(timespec="microseconds"),
                str(nuevo.sesion),
                nuevo.categoria,
                nuevo.mensaje,
            ),
        )
    return ComentarioRecibido(id=identificador)


def leer(limite: int = 50) -> Buzon:
    """Solo el API debe exponer este resultado después de verificar la clave."""

    with closing(_abrir()) as conexion:
        total = conexion.execute("SELECT COUNT(*) FROM comentarios").fetchone()[0]
        filas = conexion.execute(
            "SELECT id, categoria, mensaje, instante FROM comentarios ORDER BY instante DESC, id DESC LIMIT ?",
            (limite,),
        ).fetchall()
    return Buzon(
        total=total,
        comentarios=[
            ComentarioEquipo(id=UUID(fila[0]), categoria=fila[1], mensaje=fila[2], instante=fila[3]) for fila in filas
        ],
    )

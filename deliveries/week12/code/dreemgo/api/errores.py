"""
Errores de validación en español, con el campo que falla.

FastAPI responde por defecto con los mensajes de pydantic en inglés («Input should be
less than or equal to 14»). La app los muestra junto al campo del formulario, así que
cada error sale como {"campo", "mensaje", "tipo"}, con el mensaje en español.
"""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PLANTILLAS: dict[str, str] = {
    "greater_than_equal": "Debe ser mayor o igual que {ge}.",
    "less_than_equal": "Debe ser menor o igual que {le}.",
    "greater_than": "Debe ser mayor que {gt}.",
    "less_than": "Debe ser menor que {lt}.",
    "int_parsing": "Debe ser un número entero.",
    "int_from_float": "Debe ser un número entero.",
    "float_parsing": "Debe ser un número.",
    "float_type": "Debe ser un número.",
    "string_type": "Debe ser un texto.",
    "bool_parsing": "Debe ser verdadero o falso.",
    "date_from_datetime_parsing": "Fecha no válida: se espera AAAA-MM-DD.",
    "date_parsing": "Fecha no válida: se espera AAAA-MM-DD.",
    "date_type": "Fecha no válida: se espera AAAA-MM-DD.",
    "enum": "Valor no válido. Opciones: {expected}.",
    "string_pattern_mismatch": "Formato no válido.",
    "string_too_short": "Debe tener al menos {min_length} caracteres.",
    "string_too_long": "Debe tener como máximo {max_length} caracteres.",
    "too_long": "Admite como máximo {max_length} elementos.",
    "missing": "Falta este campo.",
    "extra_forbidden": "Este parámetro no existe en el contrato.",
    "url_parsing": "URL no válida.",
    "url_scheme": "La dirección tiene que empezar con http:// o https://.",
    "url_too_long": "La dirección es demasiado larga.",
    "json_invalid": "El cuerpo de la petición no es JSON válido.",
    "model_attributes_type": "Se espera un objeto JSON con los campos del contrato.",
}
# Lo que se manda en el cuerpo (un evento) no son parámetros de la URL.
EN_EL_CUERPO = {"extra_forbidden": "Este campo no existe en el contrato."}


def _campo(loc: tuple[Any, ...]) -> str:
    """('query', 'intereses', 1) -> 'intereses'. Un error de todo el modelo -> 'consulta', o
    'evento' si lo que no vale es el cuerpo de la petición."""
    partes = [str(p) for p in loc if p not in ("query", "body", "path", "header") and not isinstance(p, int)]
    return ".".join(partes) or ("evento" if loc[:1] == ("body",) else "consulta")


def _mensaje(error: dict[str, Any]) -> str:
    tipo, ctx = error.get("type", ""), error.get("ctx") or {}
    if tipo == "value_error":  # validaciones propias: el mensaje ya está en español
        return str(ctx.get("error") or error.get("msg", "")).removeprefix("Value error, ")
    if tipo == "enum" and "expected" in ctx:  # pydantic une las opciones con «or»
        ctx = {**ctx, "expected": str(ctx["expected"]).replace(" or ", " o ")}
    en_el_cuerpo = tuple(error.get("loc", ()))[:1] == ("body",)
    plantilla = (EN_EL_CUERPO.get(tipo) if en_el_cuerpo else None) or PLANTILLAS.get(tipo)
    if plantilla:
        try:
            return plantilla.format(**ctx)
        except (KeyError, IndexError):
            pass
    return error.get("msg", "Valor no válido.")


async def validacion_en_espanol(_: Request, exc: RequestValidationError) -> JSONResponse:
    detalle = [
        {"campo": _campo(tuple(e.get("loc", ()))), "mensaje": _mensaje(e), "tipo": e.get("type", "")}
        for e in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": detalle})

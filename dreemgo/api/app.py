"""
API de DreemGO.

Una sola aplicación FastAPI que corre igual en local (uvicorn), en cualquier host de
contenedores y en AWS Lambda con Lambda Web Adapter: el contenedor no sabe dónde está.

Documentación interactiva en /v1/docs y esquema en /v1/openapi.json. El contrato de
cada campo está en dreemgo/contrato.py y se explica en docs/CONTRATO.md.
"""

from __future__ import annotations

import os
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from dreemgo import __version__
from dreemgo.api.errores import validacion_en_espanol
from dreemgo.contrato import Consulta, Respuesta, Salud

# Orígenes que pueden llamar a la API desde el navegador: la app en GitHub Pages y el
# servidor de desarrollo de Vite. Se amplía con la variable DREEMGO_CORS, separada por comas.
CORS_POR_DEFECTO = "https://oswaldoaqm.github.io,http://localhost:5173"
ORIGENES = [o.strip() for o in os.environ.get("DREEMGO_CORS", CORS_POR_DEFECTO).split(",") if o.strip()]

app = FastAPI(
    title="DreemGO API",
    version=__version__,
    summary="Itinerarios por polos turísticos del Perú, con estacionalidad, rutas y costo.",
    docs_url="/v1/docs",
    redoc_url=None,
    openapi_url="/v1/openapi.json",
)
app.add_exception_handler(RequestValidationError, validacion_en_espanol)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Clave-Publicador"],
    max_age=3600,
)


@app.get("/v1/salud", response_model=Salud, tags=["servicio"], summary="Estado del servicio")
def salud() -> Salud:
    return Salud(version=__version__, version_datos=None)


@app.get(
    "/v1/viajes",
    response_model=Respuesta,
    tags=["viajes"],
    summary="Hasta tres viajes para una consulta",
    responses={
        422: {
            "description": "La consulta no cumple el contrato. `detail` trae, por cada error, "
            "el `campo`, un `mensaje` en español y el `tipo`."
        },
        503: {"description": "El motor todavía no está conectado a la API."},
    },
)
def viajes(consulta: Annotated[Consulta, Query()]) -> Respuesta:
    """La consulta viaja en la URL, igual que en el enlace para compartir: el motor es
    determinista, así que la misma consulta con la misma versión de datos da el mismo viaje."""
    raise HTTPException(status_code=503, detail="El motor todavía no está conectado a la API.")

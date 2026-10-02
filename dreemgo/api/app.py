"""
API de DreemGO.

Una sola aplicación FastAPI que corre igual en local (uvicorn), en cualquier host de
contenedores y en AWS Lambda con Lambda Web Adapter: el contenedor no sabe dónde está.

Documentación interactiva en /v1/docs y esquema en /v1/openapi.json. El contrato de
cada campo está en dreemgo/contrato.py y se explica en docs/CONTRATO.md.

Los artefactos del motor (dreemgo/datos/) se cargan una vez, en la primera consulta que
los necesita; sin ellos el API responde, pero /v1/viajes y las demás consultas de datos
dan 503.

Los eventos que publican los municipios se guardan aparte, donde diga el
entorno (dreemgo/almacen.py), y se suman al calendario oficial. Cada consulta se responde con
una sola foto de lo publicado, y la versión de datos lleva su huella (dreemgo/publicados.py).
"""

from __future__ import annotations

import logging
import os
from datetime import date, timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from dreemgo import __version__
from dreemgo.api.errores import validacion_en_espanol
from dreemgo.api.publicaciones import (
    Publicaciones,
    publicaciones,
)
from dreemgo.contrato import (
    ALTITUD_MAX_M,
    ALTITUD_MIN_M,
    DIAS_DEFECTO,
    DIAS_MAX,
    DIAS_MIN,
    ETIQUETAS_INTERES,
    PRESUPUESTO_MAX,
    PRESUPUESTO_MIN,
    Consulta,
    Evento,
    Eventos,
    Interes,
    Opciones,
    OpcionInteres,
    OpcionOrigen,
    PoloDetalle,
    Rango,
    Respuesta,
    Salud,
)
from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje


def _anotar_en_la_salida() -> None:
    """Lo que el API anota (qué se publicó, si el almacén falló) sale junto a lo de uvicorn."""
    raiz = logging.getLogger("dreemgo")
    if not raiz.handlers:
        salida = logging.StreamHandler()
        salida.setFormatter(logging.Formatter("%(levelname)s:     %(name)s: %(message)s"))
        raiz.addHandler(salida)
        raiz.setLevel(logging.INFO)


_anotar_en_la_salida()

# Orígenes que pueden llamar a la API desde el navegador: la app en GitHub Pages y el
# servidor de desarrollo de Vite. Se amplía con la variable DREEMGO_CORS, separada por comas.
CORS_POR_DEFECTO = "https://oswaldoaqm.github.io,http://localhost:5173"
ORIGENES = [o.strip() for o in os.environ.get("DREEMGO_CORS", CORS_POR_DEFECTO).split(",") if o.strip()]
EVENTOS_RANGO_MAX_DIAS = 366

SIN_DATOS = {503: {"description": "El motor no tiene sus artefactos cargados."}}
VALIDACION = {
    422: {
        "description": "La consulta no cumple el contrato. `detail` trae, por cada error, "
        "el `campo`, un `mensaje` en español y el `tipo`."
    }
}

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


def _datos() -> artefactos.Datos:
    if not artefactos.hay_datos():
        raise HTTPException(status_code=503, detail="El motor no tiene sus artefactos cargados.")
    return artefactos.cargar()


def _error(campo: str, mensaje: str) -> HTTPException:
    return HTTPException(status_code=422, detail=[{"campo": campo, "mensaje": mensaje, "tipo": "value_error"}])


def _en_orden(eventos: list[Evento]) -> list[Evento]:
    return sorted(eventos, key=lambda e: (e.fecha_inicio, e.id))


Publicadas = Annotated[Publicaciones, Depends(publicaciones)]


@app.get("/v1/salud", response_model=Salud, tags=["servicio"], summary="Estado del servicio")
def salud(publicadas: Publicadas) -> Salud:
    if not artefactos.hay_datos():
        return Salud(version=__version__, version_datos=None)
    datos = artefactos.cargar()
    return Salud(version=__version__, version_datos=publicadas.instantanea(datos).version(datos.version))


@app.get(
    "/v1/viajes",
    response_model=Respuesta,
    tags=["viajes"],
    summary="Hasta tres viajes para una consulta",
    responses={**VALIDACION, **SIN_DATOS},
)
def viajes(consulta: Annotated[Consulta, Query()], publicadas: Publicadas) -> Respuesta:
    """La consulta viaja en la URL, igual que en el enlace para compartir: el motor es
    determinista, así que la misma consulta con la misma versión de datos da el mismo viaje."""
    datos = _datos()
    try:
        return viaje.resolver(consulta, datos, publicadas.instantanea(datos))
    except viaje.OrigenDesconocido as e:
        opciones = ", ".join(datos.origenes)
        raise _error("origen", f"Origen desconocido. Opciones: {opciones}.") from e


@app.get(
    "/v1/opciones",
    response_model=Opciones,
    tags=["viajes"],
    summary="Orígenes, intereses y rangos del formulario",
    responses=SIN_DATOS,
)
def opciones(publicadas: Publicadas) -> Opciones:
    datos = _datos()
    return Opciones(
        version_datos=publicadas.instantanea(datos).version(datos.version),
        origenes=[OpcionOrigen(id=o.id, nombre=o.nombre, region=o.region) for o in datos.origenes.values()],
        intereses=[
            OpcionInteres(id=i, etiqueta=ETIQUETAS_INTERES[i], paradas=datos.intereses[i.value]["paradas"])
            for i in Interes
        ],
        dias=Rango(minimo=DIAS_MIN, maximo=DIAS_MAX, defecto=DIAS_DEFECTO),
        presupuesto=Rango(minimo=PRESUPUESTO_MIN, maximo=PRESUPUESTO_MAX),
        altitud_max=Rango(minimo=ALTITUD_MIN_M, maximo=ALTITUD_MAX_M),
    )


@app.get(
    "/v1/polos/{polo_id}",
    response_model=PoloDetalle,
    tags=["polos"],
    summary="Ficha de un polo: recursos, clima mes a mes y eventos",
    responses={404: {"description": "No hay un polo con ese número."}, **SIN_DATOS},
)
def polo(polo_id: Annotated[int, Path(ge=0)], publicadas: Publicadas) -> PoloDetalle:
    datos = _datos()
    p = datos.polos.get(polo_id)
    if p is None:
        raise HTTPException(status_code=404, detail="No hay un polo con ese número.")
    publicados = publicadas.instantanea(datos)
    desde = date(*(int(x) for x in datos.version.split(".")[:2]), 1)
    hasta = date(desde.year + 1, desde.month, 1) - timedelta(days=1)
    paradas = sorted(
        (datos.recursos[c] for c in p.paradas),
        key=lambda r: (-(r["jerarquia"] or 0), r["nombre"], r["codigo"]),
    )
    return PoloDetalle(
        version_datos=publicados.version(datos.version),
        polo=viaje.polo_publico(p),
        recursos=[viaje.recurso(r) for r in paradas],
        clima=[viaje.estacionalidad(p, mes) for mes in range(1, 13)],
        eventos=_en_orden(viaje.eventos_del_polo(p, desde, hasta, datos) + publicados.entre(desde, hasta, p.id)),
        atribucion=list(datos.atribucion),
    )


@app.get(
    "/v1/eventos",
    response_model=Eventos,
    tags=["eventos"],
    summary="Eventos entre dos fechas, de un polo o de todos",
    responses={404: {"description": "No hay un polo con ese número."}, **VALIDACION, **SIN_DATOS},
)
def eventos(
    publicadas: Publicadas,
    desde: Annotated[date, Query(description="Primer día, AAAA-MM-DD.")],
    hasta: Annotated[date, Query(description="Último día, AAAA-MM-DD. Hasta un año después de `desde`.")],
    polo: Annotated[int | None, Query(ge=0, description="Solo los de este polo.")] = None,
) -> Eventos:
    """Los del calendario oficial y los que publicaron los municipios (`fuente: "publicado"`)."""
    datos = _datos()
    if hasta < desde:
        raise _error("hasta", "No puede ser anterior a desde.")
    if (hasta - desde).days > EVENTOS_RANGO_MAX_DIAS:
        raise _error("hasta", f"El rango admite como máximo {EVENTOS_RANGO_MAX_DIAS} días.")
    if polo is not None and polo not in datos.polos:
        raise HTTPException(status_code=404, detail="No hay un polo con ese número.")
    publicados = publicadas.instantanea(datos)
    polos = [datos.polos[polo]] if polo is not None else list(datos.polos.values())
    lista = [e for p in polos for e in viaje.eventos_del_polo(p, desde, hasta, datos)]
    lista += publicados.entre(desde, hasta, polo)
    return Eventos(version_datos=publicados.version(datos.version), desde=desde, hasta=hasta, eventos=_en_orden(lista))

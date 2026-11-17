"""
API de DreemGO.

Una sola aplicación FastAPI que corre igual en local (uvicorn), en cualquier host de
contenedores y en AWS Lambda con Lambda Web Adapter: el contenedor no sabe dónde está.

Documentación interactiva en /v1/docs y esquema en /v1/openapi.json. El contrato de
cada campo está en dreemgo/contrato.py y se explica en docs/CONTRATO.md.

Los artefactos del motor (dreemgo/datos/) se cargan una vez, en la primera consulta que
los necesita; sin ellos el API responde, pero /v1/viajes y las demás consultas de datos
dan 503.

Los eventos que publican los municipios (POST /v1/eventos) se guardan aparte, donde diga el
entorno (dreemgo/almacen.py), y se suman al calendario oficial. Cada consulta se responde con
una sola foto de lo publicado, y la versión de datos lleva su huella (dreemgo/publicados.py).
"""

from __future__ import annotations

import logging
import os
import secrets
import sqlite3
from datetime import date, datetime, timedelta
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, HTTPException, Path, Query, Response, Security
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader

from dreemgo import __version__, analitica, comentarios
from dreemgo.api.errores import validacion_en_espanol
from dreemgo.api.publicaciones import (
    CalendarioLleno,
    Publicaciones,
    ahora,
    clave_configurada,
    clave_valida,
    publicaciones,
)
from dreemgo.contrato import (
    ALTITUD_MAX_M,
    ALTITUD_MIN_M,
    DE_NOCHE,
    DIAS_DEFECTO,
    DIAS_MAX,
    DIAS_MIN,
    ETIQUETAS_INTERES,
    PRESUPUESTO_MAX,
    PRESUPUESTO_MIN,
    Consulta,
    Evento,
    EventoNuevo,
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
from dreemgo.motor import noche, textos, viaje
from dreemgo.publicados import Instantanea, Publicado, region_del_inventario, regiones

bitacora = logging.getLogger("dreemgo.api")


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
CORS_POR_DEFECTO = "https://oswaldoaqm.github.io,http://localhost:5173,http://127.0.0.1:5173"
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
    allow_headers=["Content-Type", "X-Clave-Publicador", "X-Clave-Analitica", "X-Clave-Comentarios"],
    max_age=3600,
)


def _datos() -> artefactos.Datos:
    if not artefactos.hay_datos():
        raise HTTPException(status_code=503, detail="El motor no tiene sus artefactos cargados.")
    return artefactos.cargar()


def _errores(*errores: tuple[str, str]) -> HTTPException:
    """Un 422 con la forma de los errores de validación: cada uno con su campo y su mensaje."""
    detalle = [{"campo": campo, "mensaje": mensaje, "tipo": "value_error"} for campo, mensaje in errores]
    return HTTPException(status_code=422, detail=detalle)


def _error(campo: str, mensaje: str) -> HTTPException:
    return _errores((campo, mensaje))


def _en_orden(eventos: list[Evento]) -> list[Evento]:
    return sorted(eventos, key=lambda e: (e.fecha_inicio, e.id))


def _ultimo_inicio_publicable(hoy: date) -> date:
    """Se publican los eventos de doce meses: el mes en curso y los once que siguen. Son los
    que caben en el calendario de la app, que muestra cada mes en su próxima vez."""
    return date(hoy.year + 1, hoy.month, 1) - timedelta(days=1)


Publicadas = Annotated[Publicaciones, Depends(publicaciones)]

clave_de_publicador = APIKeyHeader(
    name="X-Clave-Publicador",
    scheme_name="ClavePublicador",
    description="La clave que el equipo de DreemGO entrega a los municipios y oficinas de destino que publican.",
    auto_error=False,
)

clave_de_analitica = APIKeyHeader(
    name="X-Clave-Analitica",
    scheme_name="ClaveAnalitica",
    description="Clave del equipo para consultar la actividad real. La simulación no la necesita.",
    auto_error=False,
)

clave_de_comentarios = APIKeyHeader(
    name="X-Clave-Comentarios",
    scheme_name="ClaveComentarios",
    description="Clave del equipo para leer los mensajes recibidos. No se usa para enviarlos.",
    auto_error=False,
)


def _publicador(clave: Annotated[str | None, Security(clave_de_publicador)]) -> None:
    """Deja pasar solo a quien trae la clave. Sin clave configurada, no publica nadie."""
    if not clave_configurada():
        raise HTTPException(status_code=403, detail="Este servidor no acepta publicaciones.")
    if not clave_valida(clave):
        raise HTTPException(
            status_code=401,
            detail="Falta la clave de publicador o no es la correcta.",
            headers={"WWW-Authenticate": "APIKey"},  # un 401 tiene que decir cómo se entra
        )


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
    except viaje.DestinoDesconocido as e:
        raise _error("destino", "No hay una zona con ese número.") from e


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
            OpcionInteres(
                id=i,
                etiqueta=ETIQUETAS_INTERES[i],
                paradas=datos.intereses.get(i.value, {}).get("paradas", 0),
                de_noche=i in DE_NOCHE,
            )
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
    responses={404: {"description": "No hay una zona con ese número."}, **SIN_DATOS},
)
def polo(polo_id: Annotated[int, Path(ge=0)], publicadas: Publicadas) -> PoloDetalle:
    datos = _datos()
    p = datos.polos.get(polo_id)
    if p is None:
        raise HTTPException(status_code=404, detail="No hay una zona con ese número.")
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
        noche=noche.noche_de_la_zona(p),
        atribucion=list(datos.atribucion),
    )


@app.get(
    "/v1/eventos",
    response_model=Eventos,
    tags=["eventos"],
    summary="Eventos entre dos fechas, de un polo o de todos",
    responses={404: {"description": "No hay una zona con ese número."}, **VALIDACION, **SIN_DATOS},
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
        raise HTTPException(status_code=404, detail="No hay una zona con ese número.")
    publicados = publicadas.instantanea(datos)
    polos = [datos.polos[polo]] if polo is not None else list(datos.polos.values())
    lista = [e for p in polos for e in viaje.eventos_del_polo(p, desde, hasta, datos)]
    lista += publicados.entre(desde, hasta, polo)
    return Eventos(version_datos=publicados.version(datos.version), desde=desde, hasta=hasta, eventos=_en_orden(lista))


@app.post(
    "/v1/eventos",
    response_model=Evento,
    status_code=201,
    tags=["eventos"],
    summary="Publicar un evento",
    response_description="El evento, como lo verá el viajero.",
    dependencies=[Depends(_publicador)],
    responses={
        401: {"description": "Falta la cabecera `X-Clave-Publicador` o la clave no es la correcta."},
        403: {"description": "Este servidor no tiene una clave de publicador: no acepta publicaciones."},
        422: {
            "description": "El evento no cumple el contrato, su región no es una del país, ya terminó o "
            "falta más de un año para que empiece. `detail` trae, por cada error, el `campo`, un `mensaje` "
            "en español y el `tipo`."
        },
        503: {
            "description": "El motor no tiene sus artefactos cargados, el evento no se pudo guardar "
            "o el calendario publicado está lleno."
        },
    },
)
def publicar(
    nuevo: EventoNuevo,
    publicadas: Publicadas,
    momento: Annotated[datetime, Depends(ahora)],
) -> Evento:
    """Lo usan los municipios y las oficinas de destino. El evento se suma al calendario y, si
    trae coordenadas, a las rutas de los polos que duermen o tienen algún lugar a 10 km o menos.
    No cambia qué polos se proponen ni en qué orden.

    Publicar otra vez el mismo evento (mismo nombre, fechas, lugar y entidad) lo corrige: no lo
    duplica. La respuesta es el evento tal como lo verá el viajero.
    """
    datos = _datos()
    hoy = momento.date()
    # Lo que el modelo no puede validar solo: depende del inventario y de qué día es hoy.
    errores = []
    region = region_del_inventario(nuevo.region, datos)
    if region is None:
        errores.append(("region", f"Región desconocida. Opciones: {', '.join(regiones(datos))}."))
    if nuevo.fecha_fin < hoy:
        errores.append(("fecha_fin", "El evento ya terminó. Se publican los que están por venir."))
    limite = _ultimo_inicio_publicable(hoy)
    if nuevo.fecha_inicio > limite:
        hasta = f"{textos.fechas(limite, None)} de {limite.year}"
        errores.append(("fecha_inicio", f"Falta demasiado: se publican los eventos que empiezan hasta el {hasta}."))
    if errores:
        raise _errores(*errores)
    publicado = Publicado.nuevo(nuevo.model_copy(update={"region": region}), momento)
    try:
        instantanea: Instantanea = publicadas.guardar(publicado, datos, hoy)
    except CalendarioLleno as e:
        raise HTTPException(
            status_code=503, detail="El calendario de eventos publicados está lleno. Avisa al equipo de DreemGO."
        ) from e
    except Exception as e:  # el almacén no respondió: no se guardó nada
        bitacora.exception("No se pudo guardar el evento %s.", publicado.id)
        raise HTTPException(
            status_code=503, detail="No pudimos guardar el evento. Vuelve a intentarlo en un momento."
        ) from e
    bitacora.info(
        "Evento %s publicado; sale en los polos %s.", publicado.id, sorted(instantanea.polos_de(publicado.id))
    )
    return publicado.evento(instantanea.zona_de(publicado.id))


@app.post(
    "/v1/analitica/eventos",
    status_code=202,
    tags=["analítica"],
    summary="Anotar una acción anónima del planificador",
    responses={
        429: {"description": "La sesión envió demasiadas acciones en un minuto."},
        503: {"description": "No se pudo guardar la acción."},
    },
)
def anotar_uso(evento: analitica.EventoUso) -> dict[str, str]:
    """El navegador envía categorías, nunca nombres ni la URL del viaje."""
    try:
        nuevo = analitica.registrar(evento)
    except analitica.DemasiadasAcciones as e:
        raise HTTPException(
            status_code=429,
            detail="La sesión envió demasiadas acciones. Intenta nuevamente en un minuto.",
            headers={"Retry-After": "60"},
        ) from e
    except (OSError, sqlite3.Error) as e:
        bitacora.exception("No se pudo guardar una acción de uso.")
        raise HTTPException(status_code=503, detail="No se pudo registrar la actividad.") from e
    return {"estado": "registrado" if nuevo else "ya_registrado"}


@app.get(
    "/v1/analitica/resumen",
    response_model=analitica.Resumen,
    tags=["analítica"],
    summary="Indicadores de uso, reales o de simulación",
    responses={
        401: {"description": "Clave incorrecta para los datos reales."},
        403: {"description": "No se configuró la clave para los datos reales."},
        503: {"description": "No se pudieron leer los eventos."},
    },
)
def resumen_uso(
    response: Response,
    modo: Literal["simulacion", "real"] = "simulacion",
    desde: date | None = None,
    hasta: date | None = None,
    clave: Annotated[str | None, Security(clave_de_analitica)] = None,
) -> analitica.Resumen:
    response.headers["Cache-Control"] = "no-store"
    if desde and hasta and desde > hasta:
        raise _error("hasta", "No puede ser anterior a desde.")
    if modo == "real":
        esperada = os.environ.get("DREEMGO_CLAVE_ANALITICA", "")
        if not esperada:
            raise HTTPException(status_code=403, detail="No se configuró el acceso a la actividad real.")
        if not clave or not secrets.compare_digest(clave.encode("utf-8"), esperada.encode("utf-8")):
            raise HTTPException(status_code=401, detail="Falta la clave de analítica o no es correcta.")
        try:
            eventos_uso = analitica.leer_reales(desde, hasta)
        except (OSError, sqlite3.Error) as e:
            bitacora.exception("No se pudieron leer los indicadores reales.")
            raise HTTPException(status_code=503, detail="No se pudo leer la actividad.") from e
        fuente = "Acciones anónimas registradas por esta instalación de DreemGO."
    else:
        try:
            meta, eventos_uso = analitica.leer_simulacion()
        except (OSError, ValueError, KeyError) as e:
            bitacora.exception("No se pudo leer la simulación de actividad.")
            raise HTTPException(status_code=503, detail="No está disponible la simulación.") from e
        fuente = f"SIMULACIÓN: {meta.get('sesiones', 0)} sesiones generadas; no son usuarios ni compras reales."
    return analitica.resumir(eventos_uso, modo=modo, desde=desde, hasta=hasta, fuente=fuente)


@app.post(
    "/v1/comentarios",
    response_model=comentarios.ComentarioRecibido,
    status_code=201,
    tags=["comentarios"],
    summary="Recibir una duda, sugerencia o aviso de problema",
    responses={
        429: {"description": "Esta sesión ya envió tres mensajes durante la última hora."},
        503: {"description": "No se pudo guardar el mensaje."},
    },
)
def recibir_comentario(nuevo: comentarios.ComentarioNuevo) -> comentarios.ComentarioRecibido:
    """Guarda texto breve sin solicitar identidad ni mezclarlo con analítica."""
    try:
        return comentarios.guardar(nuevo)
    except comentarios.DemasiadosComentarios as e:
        raise HTTPException(
            status_code=429,
            detail="Esta sesión ya envió tres mensajes durante la última hora. Intenta más tarde.",
            headers={"Retry-After": "3600"},
        ) from e
    except (OSError, sqlite3.Error) as e:
        bitacora.exception("No se pudo guardar un comentario del sitio.")
        raise HTTPException(status_code=503, detail="No pudimos guardar tu mensaje. Inténtalo de nuevo.") from e


@app.get(
    "/v1/comentarios",
    response_model=comentarios.Buzon,
    tags=["comentarios"],
    summary="Leer mensajes recibidos por el equipo",
    responses={
        401: {"description": "Clave incorrecta o ausente."},
        403: {"description": "Este servidor no tiene configurada la lectura del buzón."},
        503: {"description": "No se pudieron leer los mensajes."},
    },
)
def listar_comentarios(
    response: Response,
    limite: Annotated[int, Query(ge=1, le=100)] = 50,
    clave: Annotated[str | None, Security(clave_de_comentarios)] = None,
) -> comentarios.Buzon:
    response.headers["Cache-Control"] = "no-store"
    esperada = os.environ.get("DREEMGO_CLAVE_COMENTARIOS", "")
    if not esperada:
        raise HTTPException(status_code=403, detail="Este servidor no tiene configurada la lectura del buzón.")
    if not clave or not secrets.compare_digest(clave.encode("utf-8"), esperada.encode("utf-8")):
        raise HTTPException(status_code=401, detail="Falta la clave de comentarios o no es correcta.")
    try:
        return comentarios.leer(limite)
    except (OSError, sqlite3.Error) as e:
        bitacora.exception("No se pudieron leer los comentarios del sitio.")
        raise HTTPException(status_code=503, detail="No se pudieron leer los mensajes.") from e

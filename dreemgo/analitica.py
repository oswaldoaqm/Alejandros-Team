"""Actividad anónima del planificador y resumen del panel.

La actividad real vive en SQLite. La simulación se lee de un archivo aparte y nunca se
inserta en esa base. No se reciben nombres, correos, direcciones IP ni texto libre.
"""

from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter, defaultdict
from contextlib import closing
from datetime import UTC, date, datetime, time, timedelta, timezone
from pathlib import Path
from statistics import mean, median
from threading import Lock
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from dreemgo.analitica_gerencial import AnalisisGerencial, analizar
from dreemgo.contrato import DIAS_MAX, DIAS_MIN, ETIQUETAS_INTERES, PRESUPUESTO_MAX, PRESUPUESTO_MIN, Interes
from dreemgo.motor import datos as artefactos

RAIZ = Path(__file__).resolve().parents[1]
BASE_POR_DEFECTO = (
    Path("/tmp/dreemgo/actividad.sqlite3")
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME")
    else Path.home() / ".dreemgo" / "actividad.sqlite3"
)
# El Dockerfile copia el paquete dreemgo, no data/. Esta copia viaja también en el wheel.
SIMULACION = Path(__file__).resolve().parent / "datos" / "actividad_200_simulacion.json"
# El producto opera en Perú. Sus días de actividad deben cerrar a medianoche de Lima.
HORA_PERU = timezone(timedelta(hours=-5), name="America/Lima")
MAX_EVENTOS_POR_MINUTO = 120
_PREPARAR_BASE = Lock()
ETIQUETAS_EVENTO = {
    "sesion_iniciada": "Se inició una sesión",
    "formulario_abierto": "Se abrió el planificador",
    "busqueda_iniciada": "Se solicitó una recomendación",
    "busqueda_resultado": "Se recibieron las recomendaciones",
    "itinerario_abierto": "Se abrió un itinerario",
    "viaje_guardado": "Se guardó un viaje",
    "viaje_compartido": "Se compartió un viaje",
    "viaje_impreso": "Se abrió la impresión de un viaje",
    "ayuda_consultada": "Se hizo una pregunta en la ayuda",
    "comentario_enviado": "Se envió un comentario al equipo",
    "error_consulta": "Una consulta encontró un error",
}

TipoEvento = Literal[
    "sesion_iniciada",
    "formulario_abierto",
    "busqueda_iniciada",
    "busqueda_resultado",
    "itinerario_abierto",
    "viaje_guardado",
    "viaje_compartido",
    "viaje_impreso",
    "ayuda_consultada",
    "comentario_enviado",
    "error_consulta",
]


class EventoUso(BaseModel):
    """Solo categorías del producto y un identificador aleatorio de sesión."""

    model_config = ConfigDict(extra="forbid")

    id_evento: UUID | None = None
    sesion: UUID
    tipo: TipoEvento
    origen: str | None = Field(default=None, pattern=r"^[a-z0-9_-]{1,64}$")
    polo: int | None = Field(default=None, ge=0)
    intereses: list[Interes] = Field(default_factory=list, max_length=len(Interes))
    dias: int | None = Field(default=None, ge=DIAS_MIN, le=DIAS_MAX)
    mes: int | None = Field(default=None, ge=1, le=12)
    presupuesto: int | None = Field(default=None, ge=PRESUPUESTO_MIN, le=PRESUPUESTO_MAX)
    resultados: int | None = Field(default=None, ge=0, le=3)
    duracion_ms: int | None = Field(default=None, ge=0, le=120_000)
    codigo_error: str | None = Field(default=None, pattern=r"^[a-z0-9_-]{1,24}$")

    @field_validator("intereses")
    @classmethod
    def intereses_sin_repetir(cls, valor: list[Interes]) -> list[Interes]:
        return list(dict.fromkeys(valor))

    @model_validator(mode="after")
    def resultado_completo(self) -> EventoUso:
        if self.tipo == "busqueda_resultado" and self.resultados is None:
            raise ValueError("Una respuesta debe indicar cuántos viajes devolvió.")
        return self


class Indicador(BaseModel):
    id: str
    etiqueta: str
    valor: int | float | None
    unidad: str = ""
    descripcion: str
    grupo: str


class PuntoSerie(BaseModel):
    fecha: date
    sesiones: int
    busquedas: int
    detalles: int
    guardados: int


class Puesto(BaseModel):
    nombre: str
    cantidad: int


class AccionReciente(BaseModel):
    instante: datetime
    tipo: str
    etiqueta: str


class Resumen(BaseModel):
    modo: Literal["simulacion", "real"]
    actualizado: datetime | None
    consultado: datetime
    zona_horaria: str = "America/Lima"
    total_eventos: int
    actividad_reciente: list[AccionReciente]
    periodo: dict[str, date | None]
    fuente: str
    indicadores: list[Indicador]
    serie: list[PuntoSerie]
    destinos: list[Puesto]
    intereses: list[Puesto]
    analisis: AnalisisGerencial


def _ruta_base() -> Path:
    configurada = os.environ.get("DREEMGO_ANALITICA_DB")
    if not configurada:
        return BASE_POR_DEFECTO
    ruta = Path(configurada).expanduser()
    return ruta if ruta.is_absolute() else RAIZ / ruta


def _abrir() -> sqlite3.Connection:
    ruta = _ruta_base()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta, timeout=5)
    conexion.execute("PRAGMA busy_timeout = 5000")
    try:
        # Los primeros visitantes pueden llegar a la vez. Serializamos la
        # preparación dentro de este proceso y SQLite protege la transacción.
        with _PREPARAR_BASE, conexion:
            if conexion.execute("PRAGMA journal_mode").fetchone()[0] != "wal":
                conexion.execute("PRAGMA journal_mode = WAL")
            conexion.execute("BEGIN IMMEDIATE")
            conexion.execute(
                """CREATE TABLE IF NOT EXISTS actividad (
                    id INTEGER PRIMARY KEY,
                    instante TEXT NOT NULL,
                    sesion TEXT NOT NULL,
                    tipo TEXT NOT NULL,
                    datos TEXT NOT NULL,
                    id_evento TEXT
                )"""
            )
            columnas = {fila[1] for fila in conexion.execute("PRAGMA table_info(actividad)")}
            if "id_evento" not in columnas:
                conexion.execute("ALTER TABLE actividad ADD COLUMN id_evento TEXT")
            conexion.execute("CREATE INDEX IF NOT EXISTS idx_actividad_instante ON actividad(instante)")
            conexion.execute("CREATE INDEX IF NOT EXISTS idx_actividad_sesion ON actividad(sesion, instante)")
            conexion.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_actividad_evento ON actividad(id_evento)")
    except sqlite3.Error:
        conexion.close()
        raise
    return conexion


class DemasiadasAcciones(Exception):
    """Una sesión envió más acciones de las que permite una interacción normal."""


def _iso_utc(momento: datetime) -> str:
    return momento.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def registrar(evento: EventoUso, instante: datetime | None = None) -> bool:
    """Guarda un evento real. La fecha de un POST siempre la asigna la API."""

    momento = (instante or datetime.now(UTC)).astimezone(UTC)
    registro = evento.model_dump(mode="json", exclude_none=True)
    registro["instante"] = _iso_utc(momento)
    id_evento = str(evento.id_evento) if evento.id_evento else None
    with closing(_abrir()) as conexion, conexion:
        conexion.execute("BEGIN IMMEDIATE")
        if id_evento and conexion.execute("SELECT 1 FROM actividad WHERE id_evento = ?", (id_evento,)).fetchone():
            return False
        recientes = conexion.execute(
            "SELECT COUNT(*) FROM actividad WHERE sesion = ? AND instante >= ?",
            (str(evento.sesion), _iso_utc(momento - timedelta(minutes=1))),
        ).fetchone()[0]
        if recientes >= MAX_EVENTOS_POR_MINUTO:
            raise DemasiadasAcciones
        conexion.execute(
            "INSERT INTO actividad(instante, sesion, tipo, datos, id_evento) VALUES (?, ?, ?, ?, ?)",
            (
                registro["instante"],
                str(evento.sesion),
                evento.tipo,
                json.dumps(registro, ensure_ascii=False),
                id_evento,
            ),
        )
    return True


def leer_reales(desde: date | None = None, hasta: date | None = None) -> list[dict]:
    condiciones, parametros = [], []
    if desde:
        condiciones.append("instante >= ?")
        parametros.append(_iso_utc(datetime.combine(desde, time.min, tzinfo=HORA_PERU)))
    if hasta and hasta < date.max:
        condiciones.append("instante < ?")
        parametros.append(_iso_utc(datetime.combine(hasta + timedelta(days=1), time.min, tzinfo=HORA_PERU)))
    where = " WHERE " + " AND ".join(condiciones) if condiciones else ""
    with closing(_abrir()) as conexion:
        registros = conexion.execute(
            "SELECT datos FROM actividad" + where + " ORDER BY instante, id", parametros
        ).fetchall()
    return [json.loads(registro[0]) for registro in registros]


def leer_simulacion() -> tuple[dict, list[dict]]:
    contenido = json.loads(SIMULACION.read_text(encoding="utf-8"))
    if contenido.get("meta", {}).get("tipo") != "simulacion" or not isinstance(contenido.get("eventos"), list):
        raise ValueError("El archivo de simulación no tiene el formato esperado.")
    return contenido["meta"], contenido["eventos"]


def _porcentaje(parte: int, total: int) -> float | None:
    return round(parte * 100 / total, 1) if total else None


def _momento(evento: dict) -> datetime:
    return datetime.fromisoformat(evento["instante"].replace("Z", "+00:00"))


def _fecha_peru(evento: dict) -> date:
    return _momento(evento).astimezone(HORA_PERU).date()


def _percentil(valores: list[int], fraccion: float) -> float | None:
    if not valores:
        return None
    ordenados = sorted(valores)
    posicion = (len(ordenados) - 1) * fraccion
    inferior = int(posicion)
    superior = min(inferior + 1, len(ordenados) - 1)
    return round(ordenados[inferior] + (ordenados[superior] - ordenados[inferior]) * (posicion - inferior), 1)


def _destinos(conteo: Counter[int]) -> list[Puesto]:
    nombres: dict[int, str] = {}
    if conteo and artefactos.hay_datos():
        nombres = {id_polo: polo.nombre for id_polo, polo in artefactos.cargar().polos.items()}
    return [
        Puesto(nombre=nombres.get(polo, f"Zona {polo}"), cantidad=cantidad) for polo, cantidad in conteo.most_common(8)
    ]


def resumir(
    eventos: list[dict],
    modo: Literal["simulacion", "real"],
    desde: date | None = None,
    hasta: date | None = None,
    fuente: str = "",
) -> Resumen:
    """Calcula los indicadores siempre con los mismos denominadores, también en la demo."""

    filtrados = [
        e for e in eventos if (desde is None or _fecha_peru(e) >= desde) and (hasta is None or _fecha_peru(e) <= hasta)
    ]
    tipos = Counter(e["tipo"] for e in filtrados)
    sesiones = {e["sesion"] for e in filtrados}

    def de_sesiones(tipo: str) -> set[str]:
        return {e["sesion"] for e in filtrados if e["tipo"] == tipo}

    con_formulario = de_sesiones("formulario_abierto")
    con_busqueda = de_sesiones("busqueda_iniciada")
    con_detalle = de_sesiones("itinerario_abierto")
    con_guardado = de_sesiones("viaje_guardado")
    con_compartido = de_sesiones("viaje_compartido")
    con_error = de_sesiones("error_consulta")
    respuestas = [e for e in filtrados if e["tipo"] == "busqueda_resultado"]
    exitosas = sum(e.get("resultados", 0) > 0 for e in respuestas)
    sin_resultado = sum(e.get("resultados", 0) == 0 for e in respuestas)
    latencias = [e["duracion_ms"] for e in respuestas if isinstance(e.get("duracion_ms"), int)]
    consultas = [e for e in filtrados if e["tipo"] == "busqueda_iniciada"]
    dias = [e["dias"] for e in consultas if isinstance(e.get("dias"), int)]
    presupuestos = [e["presupuesto"] for e in consultas if isinstance(e.get("presupuesto"), int)]

    def indicador(id: str, etiqueta: str, valor: int | float | None, grupo: str, descripcion: str, unidad: str = ""):
        return Indicador(id=id, etiqueta=etiqueta, valor=valor, grupo=grupo, descripcion=descripcion, unidad=unidad)

    indicadores = [
        indicador("sesiones", "Sesiones", len(sesiones), "Uso", "Sesiones anónimas con al menos una acción."),
        indicador(
            "formularios_abiertos",
            "Formularios abiertos",
            tipos["formulario_abierto"],
            "Uso",
            "Veces que se abrió el planificador.",
        ),
        indicador(
            "busquedas_iniciadas",
            "Búsquedas iniciadas",
            tipos["busqueda_iniciada"],
            "Búsqueda",
            "Envíos del formulario.",
        ),
        indicador(
            "busquedas_completadas",
            "Búsquedas completadas",
            len(respuestas),
            "Búsqueda",
            "Respuestas recibidas del motor, con o sin rutas.",
        ),
        indicador(
            "busquedas_con_resultados",
            "Búsquedas con viajes",
            exitosas,
            "Búsqueda",
            "Respuestas con al menos un viaje.",
        ),
        indicador(
            "busquedas_sin_resultados",
            "Búsquedas sin viajes",
            sin_resultado,
            "Búsqueda",
            "Respuestas válidas sin viajes posibles.",
        ),
        indicador(
            "tasa_resultados",
            "Tasa con viajes",
            _porcentaje(exitosas, len(respuestas)),
            "Búsqueda",
            "Búsquedas con viajes / búsquedas completadas.",
            "%",
        ),
        indicador(
            "tasa_abandono_formulario",
            "Formularios sin búsqueda",
            _porcentaje(len(con_formulario - con_busqueda), len(con_formulario)),
            "Búsqueda",
            "Sesiones con formulario y sin búsqueda en el periodo / sesiones con formulario. No confirma abandono.",
            "%",
        ),
        indicador(
            "itinerarios_abiertos",
            "Itinerarios abiertos",
            tipos["itinerario_abierto"],
            "Interacción",
            "Aperturas de un viaje propuesto.",
        ),
        indicador(
            "tasa_apertura",
            "Sesiones que abrieron ruta",
            _porcentaje(len(con_detalle), len(sesiones)),
            "Interacción",
            "Sesiones con itinerario abierto / sesiones con actividad.",
            "%",
        ),
        indicador(
            "viajes_guardados",
            "Viajes guardados",
            tipos["viaje_guardado"],
            "Interacción",
            "Acciones de guardar confirmadas por el navegador.",
        ),
        indicador(
            "tasa_guardado",
            "Guardado tras abrir",
            _porcentaje(len(con_guardado & con_detalle), len(con_detalle)),
            "Interacción",
            "Sesiones que guardaron y abrieron itinerario / sesiones que abrieron itinerario.",
            "%",
        ),
        indicador(
            "viajes_compartidos",
            "Viajes compartidos",
            tipos["viaje_compartido"],
            "Interacción",
            "Acciones de compartir un enlace.",
        ),
        indicador(
            "tasa_compartir",
            "Compartido tras abrir",
            _porcentaje(len(con_compartido & con_detalle), len(con_detalle)),
            "Interacción",
            "Sesiones que compartieron y abrieron itinerario / sesiones que abrieron itinerario.",
            "%",
        ),
        indicador(
            "impresiones",
            "PDF o impresión",
            tipos["viaje_impreso"],
            "Interacción",
            "Veces que se abrió la impresión del viaje.",
        ),
        indicador(
            "consultas_ayuda",
            "Preguntas en la ayuda",
            tipos["ayuda_consultada"],
            "Interacción",
            "Preguntas escritas o elegidas en la ayuda, sin almacenar su texto.",
        ),
        indicador(
            "comentarios_enviados",
            "Comentarios enviados",
            tipos["comentario_enviado"],
            "Interacción",
            "Mensajes que el buzón confirmó como recibidos; este panel no guarda su contenido.",
        ),
        indicador(
            "errores_consulta",
            "Errores de consulta",
            tipos["error_consulta"],
            "Calidad",
            "Errores comunicados por el navegador al consultar viajes.",
        ),
        indicador(
            "sesiones_con_error",
            "Sesiones con error",
            len(con_error),
            "Calidad",
            "Sesiones donde ocurrió al menos un error de consulta.",
        ),
        indicador(
            "tasa_sesiones_con_error",
            "Sesiones con error (%)",
            _porcentaje(len(con_error), len(sesiones)),
            "Calidad",
            "Sesiones con error / sesiones con actividad.",
            "%",
        ),
        indicador(
            "latencia_mediana_ms",
            "Respuesta mediana",
            _percentil(latencias, 0.5),
            "Calidad",
            "Mediana del tiempo observado en el navegador para consultas completadas.",
            "ms",
        ),
        indicador(
            "latencia_p95_ms",
            "Respuesta p95",
            _percentil(latencias, 0.95),
            "Calidad",
            "Percentil 95 del tiempo observado en el navegador para consultas completadas.",
            "ms",
        ),
        indicador(
            "dias_promedio",
            "Días solicitados",
            round(mean(dias), 1) if dias else None,
            "Preferencias",
            "Promedio de días en búsquedas iniciadas.",
            "días",
        ),
        indicador(
            "presupuesto_mediano_soles",
            "Presupuesto mediano",
            round(median(presupuestos)) if presupuestos else None,
            "Preferencias",
            "Mediana de presupuestos indicados; omite búsquedas sin presupuesto.",
            "S/",
        ),
    ]

    por_fecha: dict[str, list[dict]] = defaultdict(list)
    for evento in filtrados:
        por_fecha[_fecha_peru(evento).isoformat()].append(evento)
    # Los huecos dentro del tramo observado se cuentan como cero eventos recibidos.
    # No alargamos artificialmente la historia hasta fechas sin cobertura conocida.
    fechas = sorted(por_fecha)
    if fechas:
        inicio, fin = date.fromisoformat(fechas[0]), date.fromisoformat(fechas[-1])
        fechas = [(inicio + timedelta(days=i)).isoformat() for i in range((fin - inicio).days + 1)]
    serie = [
        PuntoSerie(
            fecha=date.fromisoformat(fecha),
            sesiones=len({e["sesion"] for e in por_fecha[fecha]}),
            busquedas=sum(e["tipo"] == "busqueda_iniciada" for e in por_fecha[fecha]),
            detalles=sum(e["tipo"] == "itinerario_abierto" for e in por_fecha[fecha]),
            guardados=sum(e["tipo"] == "viaje_guardado" for e in por_fecha[fecha]),
        )
        for fecha in fechas
    ]
    polos: Counter[int] = Counter(
        e["polo"] for e in filtrados if e["tipo"] == "itinerario_abierto" and isinstance(e.get("polo"), int)
    )
    intereses: Counter[str] = Counter(
        interes for e in consultas for interes in e.get("intereses", []) if interes in Interes._value2member_map_
    )
    ranking_intereses = [
        Puesto(nombre=ETIQUETAS_INTERES[Interes(interes)], cantidad=cantidad)
        for interes, cantidad in intereses.most_common(8)
    ]
    marcas = [_momento(e) for e in filtrados]
    recientes = sorted(filtrados, key=_momento, reverse=True)[:8]
    return Resumen(
        modo=modo,
        actualizado=max(marcas) if marcas else None,
        consultado=datetime.now(UTC),
        total_eventos=len(filtrados),
        actividad_reciente=[
            AccionReciente(instante=_momento(e), tipo=e["tipo"], etiqueta=ETIQUETAS_EVENTO[e["tipo"]])
            for e in recientes
        ],
        periodo={
            "desde": desde or (min(marcas).astimezone(HORA_PERU).date() if marcas else None),
            "hasta": hasta or (max(marcas).astimezone(HORA_PERU).date() if marcas else None),
        },
        fuente=fuente,
        indicadores=indicadores,
        serie=serie,
        destinos=_destinos(polos),
        intereses=ranking_intereses,
        analisis=analizar(filtrados, [p.model_dump() for p in serie], modo),
    )

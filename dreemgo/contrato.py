"""
Contrato de la API de DreemGO: qué entra al motor y qué sale.

Es la única definición. FastAPI genera de aquí el esquema OpenAPI (/v1/openapi.json)
y la app web genera sus tipos a partir de ese esquema, así que un campo que no
está aquí no existe. docs/CONTRATO.md explica cada campo, sus unidades y por qué
el formulario, el modelo de datos y la respuesta quedaron como quedaron.

Reglas de redacción que siguen todos los modelos:
- Unidades en el nombre del campo cuando no son obvias: `_m`, `_km`, `_mm`, `_c`.
- Montos en soles enteros, por persona, para todo el viaje.
- Nada se inventa: un dato que la fuente no trae viaja como null, nunca como 0.
"""

from __future__ import annotations

from datetime import date, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

VERSION_CONTRATO = "1.0"

DIAS_MIN, DIAS_MAX, DIAS_DEFECTO = 1, 14, 6
ALTITUD_MIN_M, ALTITUD_MAX_M = 0, 6_000
PRESUPUESTO_MIN, PRESUPUESTO_MAX = 100, 50_000
RUTAS_MAX = 3
EVENTO_DURACION_MAX_DIAS = 60


class _Modelo(BaseModel):
    """Base común: los campos que no están en el contrato se rechazan."""

    model_config = ConfigDict(extra="forbid")


# ─────────────────────────────── entrada ───────────────────────────────


class Interes(StrEnum):
    """Intereses del viajero, con su vocabulario y no con la taxonomía de MINCETUR.
    Cada uno se traduce a categorías, subtipos y actividades de la ficha oficial;
    la tabla de equivalencias es un artefacto del pipeline."""

    naturaleza = "naturaleza"
    historia = "historia"
    gastronomia = "gastronomia"
    caminatas = "caminatas"
    playa = "playa"
    fiestas = "fiestas"
    arquitectura = "arquitectura"
    aventura = "aventura"


ETIQUETAS_INTERES: dict[Interes, str] = {
    Interes.naturaleza: "Naturaleza",
    Interes.historia: "Historia y arqueología",
    Interes.gastronomia: "Gastronomía",
    Interes.caminatas: "Caminatas",
    Interes.playa: "Playa",
    Interes.fiestas: "Fiestas y cultura viva",
    Interes.arquitectura: "Arquitectura urbana",
    Interes.aventura: "Aventura",
}


class Consulta(_Modelo):
    """Lo que el viajero pide. Es también el enlace para compartir: el motor es
    determinista, así que la misma consulta con la misma versión de datos
    devuelve el mismo viaje."""

    origen: str = Field(
        "lima",
        min_length=2,
        max_length=40,
        pattern=r"^[a-z0-9-]+$",
        description="Ciudad de partida, por su identificador (la lista está en /v1/opciones).",
    )
    mes: int | None = Field(
        None,
        ge=1,
        le=12,
        description="Mes del viaje, 1 a 12. Obligatorio salvo que se dé fecha_inicio.",
    )
    fecha_inicio: date | None = Field(
        None,
        description="Día en que se sale del origen. Con ella los días del itinerario llevan fecha "
        "y los eventos se cruzan día a día; sin ella, se cruzan con el mes.",
    )
    dias: int = Field(
        DIAS_DEFECTO,
        ge=DIAS_MIN,
        le=DIAS_MAX,
        description="Días disponibles en total, contando la ida y la vuelta desde el origen.",
    )
    intereses: list[Interes] = Field(
        default_factory=list,
        max_length=len(Interes),
        description="Cero o más intereses. Sin intereses, el motor busca lo más valioso de cada polo.",
    )
    presupuesto: int | None = Field(
        None,
        ge=PRESUPUESTO_MIN,
        le=PRESUPUESTO_MAX,
        description="Soles por persona para todo el viaje. Ordena y advierte; no descarta rutas.",
    )
    altitud_max: int | None = Field(
        None,
        ge=ALTITUD_MIN_M,
        le=ALTITUD_MAX_M,
        description="Altitud máxima tolerada, en metros. Ninguna parada la supera.",
    )
    sorpresa: bool = Field(
        False,
        description="Prioriza polos fuera del circuito habitual (término de novedad al máximo).",
    )

    @field_validator("intereses")
    @classmethod
    def _sin_repetidos(cls, v: list[Interes]) -> list[Interes]:
        return list(dict.fromkeys(v))

    @model_validator(mode="after")
    def _mes_o_fecha(self) -> Consulta:
        if self.fecha_inicio is not None:
            if self.mes is not None and self.mes != self.fecha_inicio.month:
                raise ValueError("El mes no coincide con la fecha de inicio: basta con indicar la fecha.")
            self.mes = self.fecha_inicio.month
        elif self.mes is None:
            raise ValueError("Indica el mes de viaje o la fecha de inicio.")
        return self


# ─────────────────────────────── salida ───────────────────────────────


class Punto(_Modelo):
    nombre: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    altitud_m: int | None = None


class Recurso(_Modelo):
    """Un recurso turístico del inventario oficial, con lo que la ficha publica."""

    codigo: str = Field(description="Código del recurso en el inventario de MINCETUR.")
    nombre: str
    categoria: str
    tipo: str
    subtipo: str | None = None
    jerarquia: int | None = Field(
        None,
        ge=1,
        le=4,
        description="Jerarquía oficial de 1 a 4. null cuando MINCETUR no la asigna («No aplica», "
        "«POR JERARQUIZAR»): nunca se imputa.",
    )
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    altitud_m: int | None = None
    url_ficha: HttpUrl = Field(description="Ficha oficial: toda parada es verificable en la fuente (RNF-01).")
    descripcion: str | None = None
    ingreso: Literal["libre", "pagado", "desconocido"] = "desconocido"
    tarifa_soles: float | None = Field(None, ge=0)


class Parada(_Modelo):
    orden: int = Field(ge=1, description="Posición dentro del día.")
    recurso: Recurso
    llegada: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$", description="Hora estimada de llegada, HH:MM.")
    minutos_traslado: int = Field(ge=0, description="Desde la parada anterior o desde la base.")
    km_desde_anterior: float = Field(ge=0)
    minutos_visita: int = Field(ge=0)


class Dia(_Modelo):
    numero: int = Field(ge=1)
    fecha: date | None = None
    tipo: Literal["ida", "visita", "vuelta", "ida_y_visita", "visita_y_vuelta"]
    horas: float = Field(ge=0, description="Horas ocupadas entre traslados y visitas.")
    km: float = Field(ge=0)
    paradas: list[Parada] = Field(default_factory=list)
    nota: str | None = None


class Estacionalidad(_Modelo):
    mes: int = Field(ge=1, le=12)
    veredicto: Literal["viable", "advertencia", "desaconsejado"]
    lluvia_mm: float = Field(ge=0, description="Lluvia media del mes, diez años de datos.")
    dias_con_lluvia: float | None = Field(None, ge=0, le=31)
    horas_sol: float | None = Field(None, ge=0, le=24, description="Horas de sol por día, promedio del mes.")
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    explicacion: str
    mejores_meses: list[int] = Field(default_factory=list, description="Meses viables del polo, de mejor a peor.")


class Traslado(_Modelo):
    desde: str = Field(description="Nombre de la ciudad de origen.")
    horas: float | None = Field(None, ge=0, description="Horas por carretera, solo ida.")
    dias_de_viaje: int = Field(ge=0, description="Días del viaje que se van en la ida y la vuelta.")
    acceso: Literal["terrestre", "sin_acceso_terrestre", "desconocido"]
    fuente: Literal["red_vial", "estimado"] = Field(
        description="red_vial: calculado sobre OpenStreetMap. estimado: línea recta por un factor calibrado.",
    )


class Costo(_Modelo):
    """Una banda y no un precio: el motor estima, no vende."""

    moneda: Literal["PEN"] = "PEN"
    p20: int = Field(ge=0)
    p50: int = Field(ge=0)
    p80: int = Field(ge=0)
    desglose: dict[str, int] = Field(
        default_factory=dict,
        description="Componentes del P50: transporte, alojamiento, alimentación, entradas.",
    )
    dentro_del_presupuesto: bool | None = Field(None, description="null si la consulta no trae presupuesto.")
    exceso: int | None = Field(None, ge=0, description="Soles por encima del presupuesto, sobre el P50.")
    supuestos: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _banda_ordenada(self) -> Costo:
        if not self.p20 <= self.p50 <= self.p80:
            raise ValueError("La banda de costo debe cumplir p20 ≤ p50 ≤ p80.")
        return self


class Evento(_Modelo):
    id: str
    nombre: str
    tipo: str | None = None
    fecha_inicio: date | None = None
    fecha_fin: date | None = None
    precision_fecha: Literal["exacta", "aproximada", "por_confirmar"] = Field(
        description="exacta: la fuente la publica. aproximada: calculada (santoral, cómputo de Pascua). "
        "por_confirmar: sin fecha conocida.",
    )
    distrito: str
    provincia: str
    region: str
    fuente: Literal["mincetur", "publicado"]
    publicado_por: str | None = None
    url: HttpUrl | None = None


class Aviso(_Modelo):
    tipo: Literal["estacionalidad", "altitud", "aclimatacion", "presupuesto", "acceso", "dias", "datos"]
    nivel: Literal["info", "advertencia"]
    mensaje: str


class Polo(_Modelo):
    id: int
    nombre: str = Field(description="Nombre legible del polo, armado con su localidad principal.")
    region: str = Field(description="Región con más recursos del polo.")
    regiones: list[str]
    base: Punto = Field(description="Dónde se duerme: el punto de partida de cada día.")
    recursos: int = Field(ge=1, description="Recursos del inventario dentro del polo.")
    fuera_del_circuito: bool = Field(description="Ningún recurso del polo está en Lima ni en Cusco.")


class Indicadores(_Modelo):
    paradas: int = Field(ge=0)
    jerarquia_media: float | None = Field(None, ge=1, le=4)
    paradas_jerarquia_alta: int = Field(ge=0, description="Paradas de jerarquía 3 o 4.")
    altitud_max_m: int | None = None
    km_total: float = Field(ge=0)
    valor_capturado: float = Field(
        ge=0,
        le=1,
        description="Parte del valor alcanzable del polo que el itinerario visita.",
    )


class Ruta(_Modelo):
    polo: Polo
    puntaje: float = Field(ge=0, le=1)
    motivos: list[str] = Field(description="Por qué el motor propone este polo, en frases cortas.")
    estacionalidad: Estacionalidad
    traslado: Traslado
    dias: list[Dia]
    costo: Costo
    eventos: list[Evento] = Field(default_factory=list)
    avisos: list[Aviso] = Field(default_factory=list)
    indicadores: Indicadores


class Sugerencia(_Modelo):
    campo: Literal["origen", "mes", "fecha_inicio", "dias", "intereses", "presupuesto", "altitud_max"]
    valor: int | str | list[str] | None
    efecto: str = Field(description="Qué cambia si se acepta, por ejemplo «aparecen 5 rutas».")


class SinResultado(_Modelo):
    motivo: str
    sugerencias: list[Sugerencia] = Field(default_factory=list)


class Respuesta(_Modelo):
    version_contrato: str = VERSION_CONTRATO
    version_datos: str = Field(description="Versión de los artefactos con que se calculó; va en el enlace.")
    consulta: Consulta = Field(description="La consulta tal como la entendió el motor.")
    rutas: list[Ruta] = Field(max_length=RUTAS_MAX, description="Hasta tres polos distintos, del mejor al peor.")
    sin_resultado: SinResultado | None = Field(
        None,
        description="Presente solo si no hay ninguna ruta: por qué y qué relajar.",
    )
    atribucion: list[str] = Field(description="Fuentes y licencias que la app muestra junto al resultado.")

    @model_validator(mode="after")
    def _rutas_o_motivo(self) -> Respuesta:
        if not self.rutas and self.sin_resultado is None:
            raise ValueError("Sin rutas, la respuesta debe explicar por qué (sin_resultado).")
        if self.rutas and self.sin_resultado is not None:
            raise ValueError("sin_resultado solo va cuando no hay ninguna ruta.")
        return self


# ─────────────────────────────── eventos publicados ───────────────────────────────


class EventoNuevo(_Modelo):
    """Un evento que publica un municipio o una oficina de destino (RF-03)."""

    nombre: str = Field(min_length=3, max_length=120)
    tipo: str | None = Field(None, max_length=60)
    fecha_inicio: date
    fecha_fin: date
    distrito: str = Field(min_length=2, max_length=80)
    provincia: str = Field(min_length=2, max_length=80)
    region: str = Field(min_length=2, max_length=40)
    lat: float | None = Field(None, ge=-18.4, le=0.1, description="Dentro del Perú.")
    lon: float | None = Field(None, ge=-81.4, le=-68.6, description="Dentro del Perú.")
    descripcion: str | None = Field(None, max_length=1_000)
    url: HttpUrl | None = None
    publicado_por: str = Field(min_length=3, max_length=120, description="Entidad que publica.")

    @model_validator(mode="after")
    def _ventana_valida(self) -> EventoNuevo:
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")
        if self.fecha_fin - self.fecha_inicio > timedelta(days=EVENTO_DURACION_MAX_DIAS):
            raise ValueError(f"Un evento no puede durar más de {EVENTO_DURACION_MAX_DIAS} días.")
        if (self.lat is None) != (self.lon is None):
            raise ValueError("Latitud y longitud van juntas.")
        return self


# ─────────────────────────────── servicio ───────────────────────────────


class Salud(_Modelo):
    estado: Literal["ok"] = "ok"
    version: str
    version_contrato: str = VERSION_CONTRATO
    version_datos: str | None = Field(None, description="null mientras el motor no tiene artefactos cargados.")

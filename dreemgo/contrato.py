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

import unicodedata
from datetime import date, timedelta
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

VERSION_CONTRATO = "1.6"

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
    vida_nocturna = "vida_nocturna"


DE_NOCHE: frozenset[Interes] = frozenset({Interes.vida_nocturna})
"""Los intereses de la noche (desde 1.5): no atienden paradas del día, sino lo que se hace de
noche cerca de donde se duerme. Los demás son del día."""

ETIQUETAS_INTERES: dict[Interes, str] = {
    Interes.naturaleza: "Naturaleza",
    Interes.historia: "Historia y arqueología",
    Interes.gastronomia: "Gastronomía",
    Interes.caminatas: "Caminatas",
    Interes.playa: "Playa",
    Interes.fiestas: "Fiestas y cultura viva",
    Interes.arquitectura: "Arquitectura urbana",
    Interes.aventura: "Aventura",
    Interes.vida_nocturna: "Vida nocturna",
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
        description="El día 1 del viaje: el día en que se sale del origen o, con bus de noche (desde 1.6), el día "
        "en que se llega, porque el bus sale la noche anterior. Con ella los días del itinerario llevan fecha y los "
        "eventos se cruzan día a día; sin ella, se cruzan con el mes.",
    )
    dias: int = Field(
        DIAS_DEFECTO,
        ge=DIAS_MIN,
        le=DIAS_MAX,
        description="Días disponibles en total, contando la ida y la vuelta desde el origen. Con bus de noche "
        "(desde 1.6), las noches del bus van fuera: se sale la noche antes del día 1 y se vuelve la noche del último.",
    )
    intereses: list[Interes] = Field(
        default_factory=list,
        max_length=len(Interes),
        description="Cero o más intereses. Sin intereses, el motor busca lo más valioso de cada polo. "
        "vida_nocturna (desde 1.5) no cambia las paradas del día: trae los bares, pubs, discotecas y peñas "
        "cerca de donde se duerme, y pesa al elegir las zonas.",
    )
    presupuesto: int | None = Field(
        None,
        ge=PRESUPUESTO_MIN,
        le=PRESUPUESTO_MAX,
        description="Soles por persona para todo el viaje. Elige, ordena y advierte: una ruta que lo pasa "
        "sale solo si es mucho mejor que las que entran (desde 1.3; antes solo ordenaba).",
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
    solo_por_tierra: bool = Field(
        False,
        description="Sin vuelos: la ida y la vuelta van por carretera, en tren o en bote. Por defecto el "
        "motor vuela a lo que por tierra queda a más de 16 horas (desde 1.3).",
    )
    destino: int | None = Field(
        None,
        ge=0,
        description="La zona a la que el viajero quiere ir, por su número de polo. Con ella el motor arma "
        "solo ese viaje y, si no cabe, dice por qué y qué cambiar (desde 1.4). No va con sorpresa.",
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
        if self.destino is not None and self.sorpresa:
            raise ValueError("Con un destino elegido no hay sorpresa: quita uno de los dos.")
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


HORA = r"^([01]\d|2[0-3]):[0-5]\d$"


class Parada(_Modelo):
    orden: int = Field(ge=1, description="Posición dentro del día.")
    recurso: Recurso
    llegada: str = Field(
        pattern=HORA,
        description="Hora estimada de llegada, HH:MM. Si se almuerza al llegar (desde 1.6), la de después del "
        "almuerzo.",
    )
    minutos_traslado: int = Field(ge=0, description="Desde la parada anterior o desde la base.")
    km_desde_anterior: float = Field(ge=0)
    minutos_visita: int = Field(ge=0)


def _hora(descripcion: str):
    """Un campo con una hora HH:MM del Perú, o null."""
    return Field(None, pattern=HORA, description=descripcion)


class Almuerzo(_Modelo):
    """La hora de almuerzo de un día con visitas (desde 1.6). No cuenta en las horas del día."""

    hora: str = Field(pattern=HORA, description="Cuándo empieza, HH:MM. Dura una hora.")
    despues_de: int = Field(ge=0, description="Cuántas paradas del día van antes: 0, antes de la primera.")
    lugar: str = Field(description="Dónde: el nombre de la parada o de la base.")
    en_la_base: bool = Field(description="Si es en la base o, en un viaje de un día, en la ciudad de origen.")
    hay_donde_comer: bool | None = Field(
        None,
        description="Si OpenStreetMap u Overture registran restaurantes, cafés o comida rápida a menos de 1,5 km. "
        "false: no registran ninguno, y conviene llevar el almuerzo. En la base o en el origen, null si no "
        "registran ninguno: es un pueblo con hospedaje, y se da por hecho que hay.",
    )


class BusDeNoche(_Modelo):
    """La ida y la vuelta en bus de noche: las noches del bus van fuera de los días del viaje (desde 1.6)."""

    sale: str = Field(pattern=HORA, description="La salida del origen, la noche antes del día 1.")
    llega: str = Field(pattern=HORA, description="La llegada a la base, el día 1.")
    sale_vuelta: str = Field(pattern=HORA, description="La salida de la base, la noche del último día.")
    llega_vuelta: str = Field(pattern=HORA, description="La llegada al origen, la mañana siguiente.")


class LugarDeNoche(_Modelo):
    """Un lugar para salir de noche cerca de donde se duerme (desde 1.5)."""

    nombre: str
    tipo: Literal["bar", "pub", "discoteca", "karaoke", "pena", "musica", "comedia"] = Field(
        description="pub también es cervecería; pena, una peña, con música criolla o andina en vivo; musica, "
        "música en vivo; comedia, de pie."
    )
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    minutos_a_pie: int = Field(
        ge=1, description="Desde la base, con un 30 % más de camino que la línea recta y a 4,5 km/h."
    )
    fuente: Literal["openstreetmap", "overture"]
    url: HttpUrl = Field(
        description="Dónde verificarlo: su página en OpenStreetMap o, si solo está en Overture Maps, el mapa de "
        "OpenStreetMap en ese punto."
    )
    horario: str | None = Field(None, description="El que publica OpenStreetMap, tal cual (opening_hours).")


class LugarDeEstrellas(_Modelo):
    """Desde dónde se mira el cielo (desde 1.5)."""

    nombre: str
    tipo: Literal["base", "mirador", "observatorio", "planetario"]
    minutos: int = Field(ge=0, description="Desde la base por la red, de puerta a puerta; 0 si es la base.")
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    url: HttpUrl | None = Field(None, description="Su página en OpenStreetMap; null si es la base.")
    brillo: float = Field(
        ge=0,
        description="La luz artificial del cielo frente a la natural (ALR), estimada con las luces nocturnas de "
        "VIIRS y el modelo de Duriscoe et al. (2018).",
    )
    clase: Literal["muy_oscuro", "oscuro", "con_luz"] = Field(
        description="Las del Servicio de Parques Nacionales de EE. UU.: brillo menor que 0,3, excelente; de 0,3 a "
        "2, se ve lo principal; más de 2, la noche natural ya no se ve."
    )


class Luna(_Modelo):
    """La luna de una noche, en hora del Perú (desde 1.5)."""

    iluminada: float = Field(ge=0, le=1, description="La parte iluminada a medianoche.")
    creciente: bool
    sale: str | None = _hora("Si sale con la noche ya oscura.")
    se_pone: str | None = _hora("Si se pone con la noche ya oscura.")
    horas_sin_luna: float = Field(
        ge=0, description="Horas de noche oscura con la luna bajo el horizonte o casi sin luz."
    )


class Cielo(_Modelo):
    """Cómo se ve el cielo para mirar las estrellas (desde 1.5)."""

    desde: LugarDeEstrellas
    observatorio: LugarDeEstrellas | None = Field(
        None, description="Un observatorio o un planetario a menos de 45 minutos, aunque su cielo tenga luz."
    )
    noches_despejadas: float | None = Field(
        None,
        ge=0,
        le=1,
        description="La parte de las noches del mes con el cielo despejado, a las 21:00 y a la 01:00: según GOES-16 "
        "o, en la costa, según el METAR del aeropuerto más cercano. null si no hay un dato confiable.",
    )
    fuente_nubes: Literal["goes", "metar"] | None = None
    aeropuerto: str | None = Field(None, description="El aeropuerto del METAR, si de ahí sale el dato.")
    oscurece: str | None = _hora("Con fecha: cuando termina el crepúsculo, el Sol a 18° bajo el horizonte.")
    aclara: str | None = _hora("Con fecha: cuando empieza el crepúsculo de la mañana.")
    luna: Luna | None = Field(None, description="Con fecha: la luna de esa noche.")
    lunas_nuevas: list[date] = Field(
        default_factory=list, description="Sin fecha: los días de luna nueva del mes del viaje, los mejores."
    )
    temp_min_c: float | None = Field(None, description="La mínima media del mes donde se mira.")


class Noche(_Modelo):
    """Qué hacer una noche que se duerme en la base (desde 1.5). No cambia nada del día."""

    tipo: Literal["salir", "estrellas", "descanso"] = Field(
        description="salir: bares, pubs, discotecas y peñas cerca, con vida_nocturna. estrellas: con naturaleza o "
        "sin intereses, si se ven. descanso: la primera noche en la altura, con vida_nocturna."
    )
    titulo: str
    nota: str
    lugares: list[LugarDeNoche] = Field(default_factory=list, description="Con salir: los que se proponen esa noche.")
    cielo: Cielo | None = Field(None, description="Con estrellas.")


class Dia(_Modelo):
    numero: int = Field(ge=1)
    fecha: date | None = None
    tipo: Literal["ida", "visita", "vuelta", "ida_y_visita", "visita_y_vuelta", "ida_visita_y_vuelta"] = Field(
        description="ida_visita_y_vuelta (desde 1.1): un viaje de un día, que sale del origen y vuelve a él. Con "
        "bus de noche (desde 1.6), el día 1 es de ida y el último de vuelta aunque el bus vaya de noche: "
        "ida_y_visita y visita_y_vuelta, si tienen paradas.",
    )
    horas: float = Field(ge=0, description="Horas ocupadas entre traslados y visitas: el almuerzo no cuenta.")
    km: float = Field(ge=0)
    paradas: list[Parada] = Field(default_factory=list)
    nota: str | None = None
    almuerzo: Almuerzo | None = Field(
        None,
        description="Cuándo y dónde se almuerza, si el día tiene visitas y llega a la hora del almuerzo: null si "
        "las visitas terminan antes de las 12:30 (desde 1.6).",
    )
    noche: Noche | None = Field(
        None,
        description="Qué hacer esa noche, si se duerme en la base y la consulta lo pide: vida_nocturna o, para las "
        "estrellas, naturaleza o ningún interés (desde 1.5).",
    )


class Estacionalidad(_Modelo):
    mes: int = Field(ge=1, le=12)
    veredicto: Literal["viable", "advertencia", "desaconsejado"]
    lluvia_mm: float = Field(ge=0, description="Lluvia media del mes, diez años de datos.")
    dias_con_lluvia: float | None = Field(None, ge=0, le=31)
    horas_sol: float | None = Field(
        None,
        ge=0,
        le=24,
        description="Horas de sol por día, promedio del mes. null mientras no haya un dato confiable: "
        "el reanálisis no ve la neblina de la costa.",
    )
    temp_min_c: float | None = None
    temp_max_c: float | None = None
    explicacion: str
    mejores_meses: list[int] = Field(
        default_factory=list,
        description="Los meses con mejor veredicto del polo, de menos a más lluvia: los viables o, si no "
        "hay ninguno, los de advertencia.",
    )


Medio = Literal["avion", "carretera", "tren", "bote"]


class TramoAereo(_Modelo):
    """Un vuelo de la ida. La vuelta hace los mismos al revés."""

    desde: str = Field(description="Ciudad del aeropuerto de salida.")
    hasta: str = Field(description="Ciudad del aeropuerto de llegada.")
    codigo_desde: str = Field(min_length=3, max_length=3, description="Código IATA del aeropuerto de salida.")
    codigo_hasta: str = Field(min_length=3, max_length=3, description="Código IATA del aeropuerto de llegada.")
    horas: float | None = Field(None, ge=0, description="Duración publicada del vuelo.")


class Traslado(_Modelo):
    desde: str = Field(description="Nombre de la ciudad de origen.")
    horas: float | None = Field(
        None,
        ge=0,
        description="Horas de la ida, de puerta a puerta: por carretera, en tren o en bote y, si se vuela, "
        "con el tiempo en los aeropuertos y en el aire.",
    )
    dias_de_viaje: int = Field(
        ge=0,
        description="Días del viaje que se van en la ida y la vuelta. Con bus de noche (desde 1.6), 0: el bus va "
        "de noche, fuera de los días.",
    )
    medios: list[Medio] = Field(
        default_factory=lambda: ["carretera"],
        description="Con qué se hace la ida, en este orden: avión (desde 1.3), carretera, tren, bote (desde "
        "1.2). En un viaje de un día, con qué se recorre el día.",
    )
    vuelos: list[TramoAereo] = Field(
        default_factory=list,
        description="Los vuelos de la ida, en orden; vacío si no se vuela (desde 1.3).",
    )
    acceso: Literal["terrestre", "sin_acceso_terrestre", "desconocido"] = Field(
        description="El del camino por tierra, aunque se vuele. terrestre: se llega por carretera o en tren. "
        "sin_acceso_terrestre: hace falta bote.",
    )
    fuente: Literal["red_vial", "red_vial_y_vuelos", "estimado"] = Field(
        description="red_vial: calculado sobre la red de OpenStreetMap, con sus vías, trenes y botes. "
        "red_vial_y_vuelos: lo mismo hasta y desde los aeropuertos, más la duración publicada de cada vuelo "
        "(desde 1.3). estimado: línea recta por un factor calibrado.",
    )
    bus_de_noche: BusDeNoche | None = Field(
        None,
        description="Si la ida y la vuelta son en bus de noche, sus horas: por tierra de 7 a 16 horas, sin tren ni "
        "bote, en un viaje de dos días o más (desde 1.6).",
    )


class Costo(_Modelo):
    """Una banda y no un precio: el motor estima, no vende."""

    moneda: Literal["PEN"] = "PEN"
    p20: int = Field(ge=0)
    p50: int = Field(ge=0)
    p80: int = Field(ge=0)
    desglose: dict[str, int] = Field(
        default_factory=dict,
        description="Componentes del P50: transporte (con el tren y el bote), alojamiento, alimentación, entradas "
        "y, si se vuela, vuelos (desde 1.3).",
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
    polo: int | None = Field(
        None,
        ge=0,
        description="La zona donde cae, por su número de polo: la del inventario o, si lo publicó un municipio, "
        "la que duerme más cerca. null si no queda cerca de ninguna (desde 1.4).",
    )


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
    km_total: float = Field(
        ge=0, description="Los km por tierra de todos los días; con bus de noche (desde 1.6), más los del bus."
    )
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
    campo: Literal[
        "origen",
        "mes",
        "fecha_inicio",
        "dias",
        "intereses",
        "presupuesto",
        "altitud_max",
        "solo_por_tierra",
        "destino",
    ]
    valor: int | str | list[str] | bool | None
    efecto: str = Field(description="Qué cambia si se acepta, por ejemplo «aparecen 5 viajes».")


class SinResultado(_Modelo):
    motivo: str
    sugerencias: list[Sugerencia] = Field(default_factory=list)


class Respuesta(_Modelo):
    version_contrato: str = VERSION_CONTRATO
    version_datos: str = Field(description="Versión de los artefactos con que se calculó; va en el enlace.")
    consulta: Consulta = Field(description="La consulta tal como la entendió el motor.")
    rutas: list[Ruta] = Field(
        max_length=RUTAS_MAX,
        description="Hasta tres polos distintos, del mejor al peor; con destino, solo el de esa zona.",
    )
    sin_resultado: SinResultado | None = Field(
        None,
        description="Presente solo si no hay ninguna ruta: por qué y qué cambiar para que salga.",
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


def _en_una_linea(valor: object) -> object:
    """Un texto sin caracteres invisibles ni espacios de más. Lo que no es texto pasa igual,
    para que el error lo dé la validación del campo."""
    if not isinstance(valor, str):
        return valor
    visible = "".join(" " if c.isspace() else c for c in valor if c.isspace() or unicodedata.category(c)[0] != "C")
    return " ".join(visible.split())


class EventoNuevo(_Modelo):
    """Un evento que publica un municipio o una oficina de destino (RF-03).

    Los textos se limpian antes de validarse: lo que se mide es lo que se va a mostrar."""

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

    @field_validator("nombre", "tipo", "distrito", "provincia", "region", "publicado_por", mode="before")
    @classmethod
    def _sin_espacios_de_mas(cls, valor: object) -> object:
        return _en_una_linea(valor)

    @field_validator("tipo", "descripcion", "url", mode="before")
    @classmethod
    def _vacio_es_no_darlo(cls, valor: object) -> object:
        """Un formulario manda los campos que no se llenaron como textos vacíos."""
        if isinstance(valor, str):
            return valor.strip() or None
        return valor

    @model_validator(mode="after")
    def _ventana_valida(self) -> EventoNuevo:
        if self.fecha_fin < self.fecha_inicio:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio.")
        if self.fecha_fin - self.fecha_inicio > timedelta(days=EVENTO_DURACION_MAX_DIAS):
            raise ValueError(f"Un evento no puede durar más de {EVENTO_DURACION_MAX_DIAS} días.")
        if (self.lat is None) != (self.lon is None):
            raise ValueError("Latitud y longitud van juntas.")
        return self


# ─────────────────────────────── consultas de apoyo (desde 1.1) ───────────────────────────────


class Rango(_Modelo):
    minimo: int
    maximo: int
    defecto: int | None = None


class OpcionOrigen(_Modelo):
    id: str = Field(description="El valor que viaja en `origen`.")
    nombre: str
    region: str


class OpcionInteres(_Modelo):
    id: Interes
    etiqueta: str
    paradas: int = Field(ge=0, description="Paradas posibles que atiende el interés en todo el inventario.")
    de_noche: bool = Field(
        False,
        description="Si es de la noche: no atiende paradas, sino lo que se hace de noche cerca de donde se duerme "
        "(desde 1.5).",
    )


class Opciones(_Modelo):
    """Lo que la app necesita para armar el formulario sin fijar nada en su código."""

    version_contrato: str = VERSION_CONTRATO
    version_datos: str
    origenes: list[OpcionOrigen]
    intereses: list[OpcionInteres]
    dias: Rango
    presupuesto: Rango
    altitud_max: Rango


class CieloDeLaZona(_Modelo):
    """El cielo de una zona para mirar las estrellas, mes a mes (desde 1.5)."""

    desde: LugarDeEstrellas = Field(description="La base.")
    mas_oscuro: LugarDeEstrellas | None = Field(
        None,
        description="Si la base tiene luz: el mirador, observatorio o planetario con nombre más oscuro a menos de "
        "45 minutos, si su cielo es oscuro. Es un dato: el motor no propone ir de noche.",
    )
    observatorio: LugarDeEstrellas | None = None
    noches_despejadas: list[float | None] = Field(
        description="Enero a diciembre: la parte de las noches con el cielo despejado; null donde no hay dato."
    )
    fuente_nubes: Literal["goes", "metar"] | None = None
    aeropuerto: str | None = None


class NocheDeLaZona(_Modelo):
    """Lo que hay de noche en una zona (desde 1.5)."""

    lugares: list[LugarDeNoche] = Field(
        description="Para salir, a menos de 1,5 km de la base, del más al menos confiable."
    )
    cielo: CieloDeLaZona


class PoloDetalle(_Modelo):
    """Ficha de un polo: sus recursos, su clima mes a mes y sus eventos del año."""

    version_contrato: str = VERSION_CONTRATO
    version_datos: str
    polo: Polo
    recursos: list[Recurso] = Field(description="Las paradas posibles del polo, de mayor a menor jerarquía.")
    clima: list[Estacionalidad] = Field(description="Los doce meses, de enero a diciembre.")
    eventos: list[Evento] = Field(description="Los acontecimientos del polo en los próximos doce meses.")
    noche: NocheDeLaZona | None = Field(None, description="Para salir y para mirar las estrellas (desde 1.5).")
    atribucion: list[str]


class Eventos(_Modelo):
    version_contrato: str = VERSION_CONTRATO
    version_datos: str
    desde: date
    hasta: date
    eventos: list[Evento]


# ─────────────────────────────── servicio ───────────────────────────────


class Salud(_Modelo):
    estado: Literal["ok"] = "ok"
    version: str
    version_contrato: str = VERSION_CONTRATO
    version_datos: str | None = Field(None, description="null mientras el motor no tiene artefactos cargados.")

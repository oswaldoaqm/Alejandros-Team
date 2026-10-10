"""
Lectura de la ficha oficial de un recurso turístico de MINCETUR.

La ficha (consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha=N) tiene un
encabezado con los datos del recurso y un acordeón de secciones: descripción, ruta de
acceso, tipo de ingreso, época de visita, actividades, servicios. Este módulo convierte el
HTML que guarda pipeline/adquisicion/descargar_fichas_html.py en una ``Ficha``: los campos
tal como los escribió MINCETUR, más las cifras que pipeline/texto.py lee de ellos.

Dos secciones no se leen. "Datos del Responsable" trae nombre, correo y teléfono de quien
llenó la ficha, y "Saneamiento Físico Legal" trae partidas registrales; el producto no
necesita ninguna de las dos. En el texto libre que sí se lee, los teléfonos y correos se
reemplazan (``texto.sin_contactos``).

    from pipeline.fichas import leer_archivo
    ficha = leer_archivo("data/externos/fichas_html/1237.html.gz")
    ficha.nombre, ficha.jerarquia, ficha.tramos[0].km  # 'Ciudad Sagrada De Caral', 4, 186.0
"""

from __future__ import annotations

import gzip
import re
from dataclasses import dataclass
from pathlib import Path

import lxml.html

from pipeline.texto import (
    Tarifa,
    leer_altitud,
    leer_dias,
    leer_distancia_tiempo,
    leer_horario,
    leer_tarifa,
    limpio,
    normalizar,
    sin_contactos,
)

URL_FICHA = "https://consultasenlinea.mincetur.gob.pe/fichaInventario/index.aspx?cod_Ficha={codigo}"

# Secciones que se saltan a propósito, con la razón.
SECCIONES_OMITIDAS = {
    "Datos del Responsable": "datos personales de quien llenó la ficha",
    "Saneamiento Físico Legal": "partidas registrales que el producto no usa",
    "Galería de fotos": "la página la llena con JavaScript; el HTML guardado viene vacío",
}

TIPOS_INGRESO = {
    "libre": "libre",
    "previa presentación de boleto": "boleto",
    "semi-restringido": "permiso",
    "otros": "otro",
}
TIPOS_VISITANTE = {
    "turistas nacionales": "nacionales",
    "turistas extranjeros": "extranjeros",
    "visitantes locales": "locales",
}

_PARSER = lxml.html.HTMLParser(encoding="utf-8")


class FichaInvalida(ValueError):
    """El HTML no es una ficha de MINCETUR con datos (página de error o ficha vacía)."""


@dataclass(frozen=True, slots=True)
class Lugar:
    departamento: str | None
    provincia: str | None
    distrito: str | None

    @classmethod
    def leer(cls, texto: str | None) -> Lugar | None:
        """ "Lima/Barranca/Supe" → Lugar("Lima", "Barranca", "Supe")."""
        t = limpio(texto)
        if t is None:
            return None
        partes = [limpio(p) for p in t.split("/")]
        partes += [None] * (3 - len(partes))
        return cls(*partes[:3])


@dataclass(frozen=True, slots=True)
class Tramo:
    """Una fila de "Ruta de acceso al recurso". Las filas con el mismo ``recorrido``
    son tramos seguidos de una misma forma de llegar; recorridos distintos son
    alternativas (en bus público, en auto, a pie)."""

    recorrido: int | None
    desde: Lugar | None
    hasta: Lugar | None
    detalle: str | None
    acceso: str | None  # Terrestre, Lacustre / Fluvial, Marítimo, Aéreo
    medio: str | None  # Automóvil particular, Bus público, A pie, Bote…
    via: str | None  # Asfaltado, Afirmado, Trocha carrozable, Sendero, Camino de Herradura
    distancia_tiempo: str | None  # la celda tal como está
    km: float | None
    minutos: float | None
    ambigua: bool


@dataclass(frozen=True, slots=True)
class Visitantes:
    tipo: str  # nacionales, extranjeros, locales
    cantidad: int | None
    anio: int | None
    fuente: str | None


@dataclass(frozen=True, slots=True)
class Ingreso:
    tipo: str  # libre, boleto, permiso, otro
    observaciones: str | None
    tarifa: Tarifa


@dataclass(frozen=True, slots=True)
class Epoca:
    epoca: str | None  # Todo el Año, Esporádicamente - Algunos meses, Fines de semana…
    especificacion: str | None
    horario: str | None  # "10:00 a.m. - 04:00 p.m."
    abre: str | None  # "10:00"
    cierra: str | None  # "16:00"
    dias: tuple[int, ...] | None  # 0 = lunes; None si la ficha no lo dice
    observaciones: str | None


@dataclass(frozen=True, slots=True)
class Actividad:
    grupo: str | None  # Naturaleza, Cultura y Folclore, Deportes / Aventura…
    actividad: str
    observacion: str | None


@dataclass(frozen=True, slots=True)
class Ficha:
    codigo: int
    nombre: str
    departamento: str | None
    provincia: str | None
    distrito: str | None
    referencia: str | None
    otros: str | None
    toponimia: str | None
    categoria_num: int | None  # 1 sitios naturales … 5 acontecimientos programados
    categoria: str | None
    tipo: str | None
    subtipo: str | None
    jerarquia: int | None  # 1 a 4; None en folclore, eventos y recursos por jerarquizar
    jerarquia_texto: str | None
    altitud_texto: str | None
    altitud_min_m: float | None
    altitud_max_m: float | None
    foto_url: str | None
    descripcion: str | None
    particularidades: str | None
    reconocimientos: str | None
    estado_actual: str | None
    observaciones: str | None
    visitantes: tuple[Visitantes, ...]
    tramos: tuple[Tramo, ...]
    ingresos: tuple[Ingreso, ...]
    epocas: tuple[Epoca, ...]
    actividades: tuple[Actividad, ...]
    servicios_dentro: tuple[str, ...]
    servicios_fuera: tuple[str, ...]
    complementarios_dentro: tuple[str, ...]
    complementarios_fuera: tuple[str, ...]
    infraestructura_dentro: tuple[str, ...]
    infraestructura_fuera: tuple[str, ...]
    accesibilidad: tuple[str, ...]
    secciones: tuple[str, ...]  # títulos de sección presentes, en orden

    @property
    def url(self) -> str:
        return URL_FICHA.format(codigo=self.codigo)


# ── Extracción del HTML ──────────────────────────────────────────────────────────────


def _celda(elemento: lxml.html.HtmlElement) -> str | None:
    return limpio(elemento.text_content())


def _texto_largo(elemento: lxml.html.HtmlElement) -> str | None:
    """Texto de una sección con sus párrafos, sin contactos."""
    lineas = [normalizar(linea) for linea in elemento.text_content().splitlines()]
    t = "\n".join(linea for linea in lineas if linea)
    t = re.sub(r"(?<=[a-záéíóúñ])\.(?=[A-ZÁÉÍÓÚÑ][a-záéíóúñ])", ". ", t)  # "ciudad.La" → "ciudad. La"
    return limpio(sin_contactos(t)) if limpio(t) else None


def _tabla(elemento: lxml.html.HtmlElement) -> list[dict[str, str | None]]:
    """Filas de la primera tabla de una sección, con la fila de títulos como claves."""
    tablas = elemento.xpath(".//table")
    if not tablas:
        return []
    filas = [[_celda(c) or "" for c in tr.xpath("./td|./th")] for tr in tablas[0].xpath(".//tr")]
    if not filas:
        return []
    titulos = [t or f"columna_{i}" for i, t in enumerate(filas[0])]
    registros = []
    for fila in filas[1:]:
        valores = [limpio(v) for v in fila] + [None] * (len(titulos) - len(fila))
        if any(valores):
            registros.append(dict(zip(titulos, valores, strict=False)))
    return registros


def _entero(texto: str | None) -> int | None:
    t = limpio(texto)
    if t is None:
        return None
    t = re.sub(r"(?<=\d)[.,\s](?=\d{3}\b)", "", t)  # 41,463 · 41 463
    return int(t) if re.fullmatch(r"\d+", t) else None


def _anio(texto: str | None) -> int | None:
    m = re.search(r"\b(19[89]\d|20[0-4]\d)\b", texto or "")
    return int(m.group(1)) if m else None


def _encabezado(doc: lxml.html.HtmlElement) -> dict[str, str | None]:
    datos: dict[str, str | None] = {}
    for tr in doc.xpath('//div[contains(@class, "prop-section")]//tr'):
        celdas = tr.xpath("./td")
        if len(celdas) == 2:
            clave = normalizar(celdas[0].text_content()).rstrip(":").strip()
            if clave:
                datos[clave] = _celda(celdas[1])
    return datos


def _secciones(doc: lxml.html.HtmlElement) -> list[tuple[str, lxml.html.HtmlElement]]:
    secciones = []
    for h3 in doc.xpath('//div[@id="accordionContent"]/h3'):
        contenido = h3.getnext()
        while contenido is not None and contenido.tag != "div":
            contenido = contenido.getnext()
        if contenido is not None:
            secciones.append((normalizar(h3.text_content()), contenido))
    return secciones


def _tipo_de(texto: str | None, tabla: dict[str, str]) -> str | None:
    t = (limpio(texto) or "").lower()
    for prefijo, tipo in tabla.items():
        if t.startswith(prefijo):
            return tipo
    return None


def _tramos(filas: list[dict[str, str | None]]) -> tuple[Tramo, ...]:
    tramos = []
    for fila in filas:
        desde = hasta = None
        tramo = fila.get("Tramo")
        if tramo:
            partes = re.split(r"\s+-\s+", tramo, maxsplit=1)
            desde = Lugar.leer(partes[0])
            hasta = Lugar.leer(partes[1]) if len(partes) > 1 else None
        celda = fila.get("Distancia en kms./tiempo")
        lectura = leer_distancia_tiempo(celda)
        tramos.append(
            Tramo(
                recorrido=_entero(fila.get("Recorrido")),
                desde=desde,
                hasta=hasta,
                detalle=sin_contactos(fila.get("Detalle")),
                acceso=fila.get("Tipo de Acceso"),
                medio=fila.get("Medio de transporte"),
                via=fila.get("Tipo de Vía Terrestre"),
                distancia_tiempo=celda,
                km=lectura.km,
                minutos=lectura.minutos,
                ambigua=lectura.ambigua,
            )
        )
    return tuple(tramos)


def _nombres(filas: list[dict[str, str | None]], *columnas: str) -> tuple[str, ...]:
    """Los valores de una o dos columnas unidos con ": ", sin repetir, en orden."""
    vistos: dict[str, None] = {}
    for fila in filas:
        partes = [fila.get(c) for c in columnas]
        partes = [p for p in partes if p]
        if partes:
            vistos[": ".join(partes)] = None
    return tuple(vistos)


def leer_ficha(html: bytes | str, codigo: int | None = None) -> Ficha:
    """Lee una ficha. Si se da ``codigo``, verifica que la página sea de ese recurso."""
    if isinstance(html, str):
        html = html.encode("utf-8")
    doc = lxml.html.fromstring(html, parser=_PARSER)
    titulo = doc.xpath('//div[contains(@class, "TituloRecurso")]')
    datos = _encabezado(doc)
    codigo_leido = _entero(datos.get("Código"))
    if not titulo or codigo_leido is None:
        raise FichaInvalida(f"la página no trae el título o el código del recurso (código pedido: {codigo})")
    if codigo is not None and codigo_leido != codigo:
        raise FichaInvalida(f"se pidió la ficha {codigo} y la página es de la {codigo_leido}")

    categoria = datos.get("Categoría")
    m_categoria = re.match(r"(\d)\.\s*(.+)", categoria or "")
    jerarquia_texto = datos.get("Jerarquía")
    altitud_min, altitud_max = leer_altitud(datos.get("Altitud"))
    foto = doc.xpath('//div[contains(@class, "img-section")]//img/@src')

    textos: dict[str, str | None] = {}
    tablas: dict[str, list[dict[str, str | None]]] = {}
    presentes = []
    for nombre, contenido in _secciones(doc):
        presentes.append(nombre)
        if nombre in SECCIONES_OMITIDAS:
            continue
        if contenido.xpath(".//table"):
            tablas[nombre] = _tabla(contenido)
        else:
            textos[nombre] = _texto_largo(contenido)

    ingresos = tuple(
        Ingreso(
            tipo=_tipo_de(fila.get("Tipo de ingreso"), TIPOS_INGRESO) or "otro",
            observaciones=sin_contactos(fila.get("Observaciones"), aviso=True),
            tarifa=leer_tarifa(fila.get("Observaciones")),
        )
        for fila in tablas.get("Tipo de ingreso", [])
    )
    epocas = []
    for fila in tablas.get("Época propicia de visita al recurso", []):
        horario = fila.get("Hora de visita especificación")
        abre, cierra = leer_horario(horario)
        observaciones = sin_contactos(fila.get("Observaciones"), aviso=True)
        epocas.append(
            Epoca(
                epoca=fila.get("Época propicia de visita al recurso"),
                especificacion=fila.get("Especificación"),
                horario=horario,
                abre=abre,
                cierra=cierra,
                dias=leer_dias(observaciones),
                observaciones=observaciones,
            )
        )
    visitantes = tuple(
        Visitantes(
            tipo=_tipo_de(fila.get("Tipo de Visitante"), TIPOS_VISITANTE) or (fila.get("Tipo de Visitante") or ""),
            cantidad=_entero(fila.get("Cantidad")),
            anio=_anio(fila.get("Año")),
            fuente=sin_contactos(fila.get("Fuente de datos")),
        )
        for fila in tablas.get("Tipo de Visitante", [])
        if fila.get("Tipo de Visitante")
    )
    actividades = tuple(
        Actividad(
            grupo=fila.get("Actividad"), actividad=fila["Tipo"], observacion=sin_contactos(fila.get("Observación"))
        )
        for fila in tablas.get("Actividades desarrolladas dentro del recurso turístico", [])
        if fila.get("Tipo")
    )

    return Ficha(
        codigo=codigo_leido,
        nombre=normalizar(titulo[0].text_content()),
        departamento=datos.get("Departamento"),
        provincia=datos.get("Provincia"),
        distrito=datos.get("Distrito"),
        referencia=sin_contactos(datos.get("Referencia")),
        otros=sin_contactos(datos.get("Otros")),
        toponimia=datos.get("Toponimia"),
        categoria_num=int(m_categoria.group(1)) if m_categoria else None,
        categoria=m_categoria.group(2).capitalize() if m_categoria else categoria,
        tipo=re.sub(r"^[a-zñ]\.\s*", "", datos["Tipo"]) if datos.get("Tipo") else None,
        subtipo=datos.get("Subtipo"),
        jerarquia=int(jerarquia_texto) if jerarquia_texto and jerarquia_texto.isdigit() else None,
        jerarquia_texto=jerarquia_texto,
        altitud_texto=datos.get("Altitud"),
        altitud_min_m=altitud_min,
        altitud_max_m=altitud_max,
        foto_url=foto[0] if foto else None,
        descripcion=textos.get("Descripción"),
        particularidades=textos.get("Particularidades"),
        reconocimientos=textos.get("Reconocimientos"),
        estado_actual=textos.get("Estado actual"),
        observaciones=textos.get("Observaciones"),
        visitantes=visitantes,
        tramos=_tramos(tablas.get("Ruta de acceso al recurso", [])),
        ingresos=ingresos,
        epocas=tuple(epocas),
        actividades=actividades,
        servicios_dentro=_nombres(
            tablas.get("Servicios Turísticos actuales dentro del recurso", []), "Servicio", "Tipo de Servicio"
        ),
        servicios_fuera=_nombres(
            tablas.get("Servicios Turísticos actuales fuera del recurso", []), "Servicio", "Tipo de Servicio"
        ),
        complementarios_dentro=_nombres(
            tablas.get("Servicios Complementarios dentro del recurso", []), "Servicio Complementario"
        ),
        complementarios_fuera=_nombres(tablas.get("Servicios Complementarios fuera del recurso", []), "Servicio"),
        infraestructura_dentro=_nombres(tablas.get("Infraestructura básica dentro del recurso", []), "Infraestructura"),
        infraestructura_fuera=_nombres(tablas.get("Infraestructura básica fuera del recurso", []), "Infraestructura"),
        accesibilidad=_nombres(tablas.get("Condiciones de Accesibilidad al Visitante", []), "Visitante"),
        secciones=tuple(presentes),
    )


def leer_archivo(ruta: str | Path, codigo: int | None = None) -> Ficha:
    """Lee una ficha guardada como .html o .html.gz. El código sale del nombre si no se da."""
    ruta = Path(ruta)
    if codigo is None:
        m = re.match(r"(\d+)\.html", ruta.name)
        codigo = int(m.group(1)) if m else None
    abrir = gzip.open if ruta.suffix == ".gz" else open
    with abrir(ruta, "rb") as f:
        return leer_ficha(f.read(), codigo)

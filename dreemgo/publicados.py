"""
Los eventos que publican los municipios y las oficinas de destino (RF-03).

Se guarda lo que dijo quien publica y nada más. Publicar otra vez el mismo evento lo corrige
en vez de duplicarlo: su identificador sale de su nombre, sus fechas, su lugar y la entidad.

A qué polos toca un evento no se guarda: se calcula con los artefactos del momento. Si los
polos cambian con una versión nueva de los datos, lo publicado los sigue.

Se suman al calendario oficial sin tocar el orden de las rutas: aparecen en ``eventos[]`` con
``fuente: "publicado"`` y con quién los publicó. Como también son datos, la versión de datos
que informa el API lleva su huella: la misma consulta con la misma versión sigue dando la
misma respuesta (docs/CONTRATO.md §3 y docs/decisiones/0011).

Aquí no hay red ni disco: guardar y leer es cosa del almacén.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import date, datetime

import numpy as np

from dreemgo.contrato import Evento, EventoNuevo
from dreemgo.motor.datos import Datos

# Un evento sale en las rutas de un polo si queda a esta distancia, en línea recta, de donde
# se duerme en ese polo o de alguno de sus lugares del inventario.
RADIO_KM = 10.0
RADIO_TIERRA_KM = 6371.0

# Lo que identifica a un evento: publicarlo otra vez con esto igual lo corrige, no lo duplica.
IDENTIDAD = ("nombre", "fecha_inicio", "fecha_fin", "distrito", "provincia", "region", "publicado_por")
# Lo que puede cambiar una respuesta. La descripción todavía no se muestra, y la hora de
# publicación no cambia qué evento es.
EN_LA_HUELLA = (
    "id",
    "nombre",
    "tipo",
    "fecha_inicio",
    "fecha_fin",
    "distrito",
    "provincia",
    "region",
    "lat",
    "lon",
    "url",
    "publicado_por",
)


def plegar(texto: str) -> str:
    """Sin tildes ni mayúsculas, para comparar: «Áncash» y «ancash» son lo mismo."""
    sin_marcas = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
    return " ".join(sin_marcas.casefold().split())


@dataclass(frozen=True)
class Publicado:
    """Un evento publicado, como se guarda."""

    id: str
    nombre: str
    tipo: str | None
    fecha_inicio: date
    fecha_fin: date
    distrito: str
    provincia: str
    region: str
    lat: float | None  # sin coordenadas sale en el calendario, pero en ninguna ruta
    lon: float | None
    descripcion: str | None
    url: str | None
    publicado_por: str
    publicado: str  # cuándo se publicó, en ISO

    @classmethod
    def nuevo(cls, nuevo: EventoNuevo, ahora: datetime) -> Publicado:
        campos = {
            **nuevo.model_dump(),
            "url": str(nuevo.url) if nuevo.url else None,
        }
        identidad = json.dumps([plegar(str(campos[c])) for c in IDENTIDAD], ensure_ascii=False)
        return cls(
            id="p-" + hashlib.sha256(identidad.encode()).hexdigest()[:12],
            publicado=ahora.replace(microsecond=0).isoformat(),
            **campos,
        )

    def registro(self) -> dict:
        """Como diccionario de tipos simples, para guardarlo en cualquier almacén."""
        return {**asdict(self), "fecha_inicio": self.fecha_inicio.isoformat(), "fecha_fin": self.fecha_fin.isoformat()}

    @classmethod
    def de_registro(cls, r: dict) -> Publicado:
        """Falla con KeyError, TypeError o ValueError si al registro le falta algo o no es válido."""
        campos = {c: r.get(c) for c in cls.__dataclass_fields__}
        for obligatorio in ("id", "nombre", "distrito", "provincia", "region", "publicado_por"):
            if not isinstance(campos[obligatorio], str) or not campos[obligatorio]:
                raise ValueError(f"Falta «{obligatorio}».")
        campos["fecha_inicio"] = date.fromisoformat(r["fecha_inicio"])
        campos["fecha_fin"] = date.fromisoformat(r["fecha_fin"])
        for eje in ("lat", "lon"):  # un almacén puede devolver −12 donde se guardó −12.0
            campos[eje] = None if r.get(eje) is None else float(r[eje])
        campos["publicado"] = str(r.get("publicado") or "")
        return cls(**campos)

    def evento(self) -> Evento:
        """Como lo ve el viajero: con sus fechas, que son exactas porque las da quien lo organiza."""
        return Evento(
            id=self.id,
            nombre=self.nombre,
            tipo=self.tipo,
            fecha_inicio=self.fecha_inicio,
            fecha_fin=self.fecha_fin,
            precision_fecha="exacta",
            distrito=self.distrito,
            provincia=self.provincia,
            region=self.region,
            fuente="publicado",
            publicado_por=self.publicado_por,
            url=self.url,
        )


def _km(lat: float, lon: float, lats: np.ndarray, lons: np.ndarray) -> np.ndarray:
    """Distancia en línea recta sobre la esfera (haversine) de un punto a muchos, en radianes."""
    a = np.sin((lats - lat) / 2) ** 2 + np.cos(lat) * np.cos(lats) * np.sin((lons - lon) / 2) ** 2
    return 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(a))


def polos_cercanos(publicados: Iterable[Publicado], datos: Datos) -> list[frozenset[int]]:
    """Por cada evento, los polos en cuyas rutas sale: los que duermen o tienen algún lugar
    del inventario a ``RADIO_KM`` o menos. Sin coordenadas, ninguno."""
    puntos = [(r["lat"], r["lon"], r["polo"]) for r in datos.recursos.values() if r.get("polo") is not None]
    puntos += [(p.base["lat"], p.base["lon"], p.id) for p in datos.polos.values()]
    puntos = [(lat, lon, polo) for lat, lon, polo in puntos if lat is not None and lon is not None]
    if not puntos:
        return [frozenset() for _ in publicados]
    lats = np.radians(np.array([p[0] for p in puntos], dtype=float))
    lons = np.radians(np.array([p[1] for p in puntos], dtype=float))
    polos = np.array([p[2] for p in puntos], dtype=int)
    salida = []
    for p in publicados:
        if p.lat is None or p.lon is None:
            salida.append(frozenset())
            continue
        cerca = _km(float(np.radians(p.lat)), float(np.radians(p.lon)), lats, lons) <= RADIO_KM
        salida.append(frozenset(int(x) for x in polos[cerca]))
    return salida


@dataclass(frozen=True)
class Instantanea:
    """Los eventos publicados en un momento dado, ya ubicados en sus polos. No cambia: una
    consulta se resuelve entera con una sola. Se arma con ``Instantanea.de``."""

    eventos: tuple[Publicado, ...] = ()
    polos: tuple[frozenset[int], ...] = ()  # los de cada evento, en el mismo orden
    huella: str = ""

    @classmethod
    def de(cls, publicados: Iterable[Publicado], datos: Datos) -> Instantanea:
        # De dos con el mismo id vale el último publicado; y el orden no depende del almacén.
        por_id: dict[str, Publicado] = {}
        for p in sorted(publicados, key=lambda p: (p.publicado, json.dumps(p.registro(), sort_keys=True))):
            por_id[p.id] = p
        eventos = tuple(por_id[i] for i in sorted(por_id))
        if not eventos:
            return cls()
        contenido = [{c: r[c] for c in EN_LA_HUELLA} for r in (p.registro() for p in eventos)]
        texto = json.dumps(contenido, ensure_ascii=False, sort_keys=True)
        return cls(
            eventos=eventos,
            polos=tuple(polos_cercanos(eventos, datos)),
            huella=hashlib.sha256(texto.encode()).hexdigest()[:7],
        )

    def version(self, de_los_artefactos: str) -> str:
        """La versión de datos con lo publicado: «2026.10.2» sin eventos, «2026.10.2-e3f9a1c» con ellos.
        Un guion y no un «+»: la versión viaja en el enlace, y ahí un «+» se lee como un espacio."""
        return f"{de_los_artefactos}-e{self.huella}" if self.huella else de_los_artefactos

    def entre(self, desde: date, hasta: date, polo: int | None = None) -> list[Evento]:
        """Los que caen entre dos fechas, de un polo o de todos, en el orden del calendario."""
        salida = [
            p.evento()
            for p, polos in zip(self.eventos, self.polos, strict=True)
            if p.fecha_inicio <= hasta and p.fecha_fin >= desde and (polo is None or polo in polos)
        ]
        return sorted(salida, key=lambda e: (e.fecha_inicio, e.id))

    def polos_de(self, id_evento: str) -> frozenset[int]:
        for p, polos in zip(self.eventos, self.polos, strict=True):
            if p.id == id_evento:
                return polos
        return frozenset()


SIN_PUBLICADOS = Instantanea()

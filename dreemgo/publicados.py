"""
Los eventos que publican los municipios y las oficinas de destino (RF-03).

Se guarda lo que dijo quien publica y nada más. Publicar otra vez el mismo evento lo corrige
en vez de duplicarlo: su identificador sale de su nombre, sus fechas, su lugar y la entidad.

Aquí no hay red ni disco: guardar y leer es cosa del almacén.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import asdict, dataclass
from datetime import date, datetime

from dreemgo.contrato import Evento, EventoNuevo

# Lo que identifica a un evento: publicarlo otra vez con esto igual lo corrige, no lo duplica.
IDENTIDAD = ("nombre", "fecha_inicio", "fecha_fin", "distrito", "provincia", "region", "publicado_por")


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

"""
Dónde se guardan los eventos publicados: en memoria, que sirve para desarrollar y se pierde al
reiniciar; en un archivo local, una línea de JSON por evento; o en una tabla de DynamoDB, que
es lo que usa el despliegue en AWS (infra/template.yaml).

Un almacén guarda y devuelve registros: diccionarios de tipos simples con ``id`` (ver
``Publicado.registro``). Guardar dos veces el mismo ``id`` deja el último.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Protocol

bitacora = logging.getLogger("dreemgo.almacen")


class Almacen(Protocol):
    def leer(self) -> list[dict]:
        """Todos los registros guardados."""
        ...

    def guardar(self, registro: dict) -> None:
        """Guarda un registro; si ya había uno con ese ``id``, lo reemplaza."""
        ...


class EnMemoria:
    def __init__(self) -> None:
        self._registros: dict[str, dict] = {}

    def leer(self) -> list[dict]:
        return [dict(r) for r in self._registros.values()]

    def guardar(self, registro: dict) -> None:
        self._registros[registro["id"]] = dict(registro)


class EnArchivo:
    """Una línea de JSON por cada vez que se guarda; al leer, de cada ``id`` vale la última.

    El archivo solo crece. Alcanza para un servidor del curso; para algo que dure, DynamoDB.
    """

    def __init__(self, ruta: Path) -> None:
        self._ruta = Path(ruta)

    def leer(self) -> list[dict]:
        if not self._ruta.exists():
            return []
        registros: dict[str, dict] = {}
        for numero, linea in enumerate(self._ruta.read_text(encoding="utf-8").splitlines(), 1):
            if not linea.strip():
                continue
            try:
                registro = json.loads(linea)
                registros[registro["id"]] = registro
            except (ValueError, KeyError, TypeError):  # una línea a medio escribir no tumba a las demás
                bitacora.warning("%s: la línea %d no es un evento y se salta.", self._ruta, numero)
        return list(registros.values())

    def guardar(self, registro: dict) -> None:
        self._ruta.parent.mkdir(parents=True, exist_ok=True)
        with self._ruta.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(registro, ensure_ascii=False, sort_keys=True) + "\n")


def _a_dynamo(valor: Any) -> Any:
    """DynamoDB no acepta ``float``: los números van como ``Decimal``."""
    return Decimal(str(valor)) if isinstance(valor, float) else valor


def _de_dynamo(valor: Any) -> Any:
    if isinstance(valor, Decimal):
        return int(valor) if valor == valor.to_integral_value() else float(valor)
    return valor


class EnDynamo:
    """La tabla de ``infra/template.yaml``, con ``id`` de clave: guardar el mismo evento lo reemplaza.

    Se lee entera. Son pocos eventos (el API no deja pasar de ``PUBLICADOS_MAX``) y así cada
    consulta se resuelve con una sola foto del calendario, que es lo que lleva la versión de datos.

    ``tabla`` es un objeto con ``scan`` y ``put_item``, como ``boto3.resource("dynamodb").Table``;
    si no se pasa, se crea con boto3 la primera vez que hace falta.
    """

    def __init__(self, nombre: str, tabla: Any = None) -> None:
        self._nombre = nombre
        self._tabla = tabla

    def _la_tabla(self) -> Any:
        if self._tabla is None:
            # Solo en AWS: fuera de ahí no hace falta tener boto3 instalado.
            import boto3
            from botocore.config import Config

            # Si la tabla no responde, que se sepa pronto: las rutas siguen sin lo publicado.
            apuro = Config(connect_timeout=1, read_timeout=2, retries={"total_max_attempts": 2, "mode": "standard"})
            self._tabla = boto3.resource("dynamodb", config=apuro).Table(self._nombre)
        return self._tabla

    def leer(self) -> list[dict]:
        tabla, items, desde = self._la_tabla(), [], {}
        while True:
            # Lectura consistente: lo que se acaba de publicar ya está.
            pagina = tabla.scan(ConsistentRead=True, **desde)
            items.extend(pagina.get("Items", []))
            if "LastEvaluatedKey" not in pagina:
                break
            desde = {"ExclusiveStartKey": pagina["LastEvaluatedKey"]}
        return [{k: _de_dynamo(v) for k, v in item.items() if k != "expira"} for item in items]

    def guardar(self, registro: dict) -> None:
        item = {k: _a_dynamo(v) for k, v in registro.items()}
        # La tabla borra sola lo que ya pasó: «expira» es el fin del día siguiente al del evento.
        fin = date.fromisoformat(registro["fecha_fin"]) + timedelta(days=1)
        item["expira"] = int(datetime.combine(fin, time.max, tzinfo=UTC).timestamp())
        self._la_tabla().put_item(Item=item)

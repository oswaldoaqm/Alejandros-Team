"""
Dónde se guardan los eventos publicados.

El API no sabe dónde corre: pide un almacén y este módulo le da el que toca según el entorno.

- ``DREEMGO_TABLA_EVENTOS``: una tabla de DynamoDB (el despliegue en AWS, infra/template.yaml).
- ``DREEMGO_EVENTOS_ARCHIVO``: un archivo local, una línea de JSON por evento (un contenedor
  o una máquina cualquiera, con el archivo en un volumen que no se borre).
- Ninguna de las dos: en memoria. Sirve para desarrollar; se pierde al reiniciar.

Un almacén guarda y devuelve registros: diccionarios de tipos simples con ``id`` (ver
``Publicado.registro``). Guardar dos veces el mismo ``id`` deja el último.

También da una marca, que cambia cada vez que alguien guarda. Preguntarla cuesta poco, y con
ella un servidor se entera de lo que publicó otro sin leer todo cada vez.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from collections.abc import Mapping
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

    def marca(self) -> object:
        """Un valor que cambia cada vez que se guarda. Mientras sea igual, nadie guardó nada."""
        ...


class EnMemoria:
    def __init__(self) -> None:
        self._registros: dict[str, dict] = {}
        self._guardados = 0

    def leer(self) -> list[dict]:
        return [dict(r) for r in self._registros.values()]

    def guardar(self, registro: dict) -> None:
        self._registros[registro["id"]] = dict(registro)
        self._guardados += 1

    def marca(self) -> object:
        return self._guardados


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

    def marca(self) -> object:
        """El tamaño y la hora del archivo: cada línea que se suma los cambia."""
        try:
            estado = self._ruta.stat()
        except FileNotFoundError:
            return None
        return estado.st_size, estado.st_mtime_ns


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

    La marca es un ítem más de la tabla, con un ``id`` que ningún evento puede tener. Cada vez
    que se guarda un evento se le pone un valor nuevo, y leerla cuesta una unidad de lectura.

    ``tabla`` es un objeto con ``scan``, ``put_item`` y ``get_item``, como
    ``boto3.resource("dynamodb").Table``; si no se pasa, se crea con boto3 la primera vez que
    hace falta.
    """

    MARCA = "#marca"  # los eventos se llaman «p-…»

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
        return [
            {k: _de_dynamo(v) for k, v in item.items() if k != "expira"} for item in items if item["id"] != self.MARCA
        ]

    def guardar(self, registro: dict) -> None:
        item = {k: _a_dynamo(v) for k, v in registro.items()}
        # La tabla borra sola lo que ya pasó: «expira» es el fin del día siguiente al del evento.
        fin = date.fromisoformat(registro["fecha_fin"]) + timedelta(days=1)
        item["expira"] = int(datetime.combine(fin, time.max, tzinfo=UTC).timestamp())
        tabla = self._la_tabla()
        tabla.put_item(Item=item)
        try:
            tabla.put_item(Item={"id": self.MARCA, "marca": uuid.uuid4().hex})
        except Exception as error:  # el evento ya está guardado: que no se pierda por no poder avisar
            bitacora.warning("El evento se guardó, pero no su marca: otros servidores tardarán en verlo (%r).", error)

    def marca(self) -> object:
        # Lectura consistente, como la de la tabla: lo que se acaba de guardar ya cuenta.
        item = self._la_tabla().get_item(Key={"id": self.MARCA}, ConsistentRead=True).get("Item")
        return item.get("marca") if item else None


def del_entorno(entorno: Mapping[str, str] = os.environ) -> Almacen:
    """El almacén que corresponde a las variables de entorno."""
    if tabla := entorno.get("DREEMGO_TABLA_EVENTOS"):
        return EnDynamo(tabla)
    if archivo := entorno.get("DREEMGO_EVENTOS_ARCHIVO"):
        return EnArchivo(Path(archivo))
    return EnMemoria()

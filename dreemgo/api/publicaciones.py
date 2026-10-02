"""
Lo que el API necesita para los eventos publicados: tenerlos a mano sin ir al almacén en
cada consulta, guardar uno nuevo y comprobar la clave de quien publica.
"""

from __future__ import annotations

import hmac
import logging
import os
import threading
import time
from collections.abc import Callable
from datetime import date, datetime, timedelta, timezone
from functools import cache

from dreemgo.almacen import Almacen, del_entorno
from dreemgo.motor.datos import Datos
from dreemgo.publicados import SIN_PUBLICADOS, Instantanea, Publicado

bitacora = logging.getLogger("dreemgo.publicaciones")

VIGENCIA_S = 60.0  # cada cuánto se vuelve a leer el almacén
REINTENTO_S = 10.0  # y cuánto se espera si la lectura falló
PUBLICADOS_MAX = 500  # eventos por venir; con más, el calendario publicado está lleno
HORA_DEL_PERU = timezone(timedelta(hours=-5))  # todo el país, todo el año


def ahora() -> datetime:
    return datetime.now(HORA_DEL_PERU)


class CalendarioLleno(Exception):
    """Ya hay ``PUBLICADOS_MAX`` eventos por venir."""


class Publicaciones:
    """Los eventos publicados, leídos del almacén y recordados ``vigencia`` segundos.

    Si el almacén falla al leer, se sigue con lo último que se leyó (o con nada): las rutas
    no dependen de él. Cada consulta recibe una instantánea, y la versión de datos que el
    API informa es la de esa instantánea: siempre dice con qué se respondió.
    """

    def __init__(
        self,
        almacen: Almacen,
        vigencia: float = VIGENCIA_S,
        # El reloj de pared: un proceso que se congela entre peticiones, como en Lambda,
        # vuelve con la hora correcta.
        reloj: Callable[[], float] = time.time,
    ) -> None:
        self._almacen = almacen
        self._vigencia = vigencia
        self._reloj = reloj
        self._candado = threading.Lock()
        self._publicados: tuple[Publicado, ...] = ()
        self._leido: float | None = None  # cuándo se leyó el almacén por última vez
        self._espera = vigencia  # cuánto falta para volver a leerlo
        self._datos: Datos | None = None  # los artefactos con que se ubicó la instantánea
        self._instantanea = SIN_PUBLICADOS

    def instantanea(self, datos: Datos) -> Instantanea:
        """Lo publicado, ubicado en los polos de ``datos``."""
        with self._candado:
            if self._toca_leer():
                self._leer()
                self._armar(datos)
            elif datos is not self._datos:
                self._armar(datos)
            return self._instantanea

    def guardar(self, publicado: Publicado, datos: Datos, hoy: date) -> Instantanea:
        """Guarda un evento y devuelve la instantánea que ya lo trae. Si el almacén falla, falla.

        Con ``CalendarioLleno`` si el evento es nuevo y no queda sitio; corregir uno que ya
        estaba siempre se puede.
        """
        with self._candado:
            if self._toca_leer():
                self._leer()
            es_nuevo = all(p.id != publicado.id for p in self._publicados)
            if es_nuevo and sum(1 for p in self._publicados if p.fecha_fin >= hoy) >= PUBLICADOS_MAX:
                raise CalendarioLleno
            self._almacen.guardar(publicado.registro())
            # Ya está guardado: quien publica lo ve en su siguiente consulta, sin esperar a la próxima lectura.
            self._publicados = (*(p for p in self._publicados if p.id != publicado.id), publicado)
            self._armar(datos)
            return self._instantanea

    def _toca_leer(self) -> bool:
        if self._leido is None:
            return True
        pasaron = self._reloj() - self._leido
        return pasaron < 0 or pasaron >= self._espera  # menos de cero: alguien corrigió el reloj

    def _leer(self) -> None:
        try:
            registros = self._almacen.leer()
        except Exception:  # la tabla no responde, no hay permiso, el disco falla…: las rutas siguen
            bitacora.exception("No se pudieron leer los eventos publicados; se sigue con los que había.")
            self._espera = min(REINTENTO_S, self._vigencia)
        else:
            publicados = []
            for registro in registros:
                try:
                    publicados.append(Publicado.de_registro(registro))
                except (AttributeError, KeyError, TypeError, ValueError):  # uno mal guardado no tumba a los demás
                    cual = registro.get("id") if isinstance(registro, dict) else type(registro).__name__
                    bitacora.warning("Se salta un evento publicado que no se puede leer: %r", cual)
            self._publicados = tuple(publicados)
            self._espera = self._vigencia
        self._leido = self._reloj()

    def _armar(self, datos: Datos) -> None:
        self._instantanea = Instantanea.de(self._publicados, datos)
        self._datos = datos


@cache
def publicaciones() -> Publicaciones:
    """Las del proceso, con el almacén que digan las variables de entorno."""
    return Publicaciones(del_entorno())


def clave_configurada() -> str:
    return os.environ.get("DREEMGO_CLAVE_PUBLICADOR", "")


def clave_valida(recibida: str | None) -> bool:
    """Compara sin revelar, por el tiempo que tarda, cuánto de la clave se acertó."""
    esperada = clave_configurada()
    return bool(esperada) and recibida is not None and hmac.compare_digest(recibida.encode(), esperada.encode())

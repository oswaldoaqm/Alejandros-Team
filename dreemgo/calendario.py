"""
Fechas de los acontecimientos para un año dado.

El pipeline (pipeline/eventos.py) guarda para cada acontecimiento una **regla** y no una
fecha, porque muchas fiestas cambian de día cada año. Este módulo convierte la regla en
fechas concretas para el año del viaje. Es la única parte del calendario que corre en el
API, así que no depende de nada fuera de la biblioteca estándar.

Reglas (una por acontecimiento):

    fija 07-25              un día fijo (25 de julio)
    fija 07-24..07-30       un rango fijo; puede cruzar el año: fija 12-25..01-06
    pascua -7..0            días contados desde el Domingo de Pascua (Semana Santa)
    nesimo 04 2 dom         el segundo domingo de abril; -1 es el último
    nesimo 10 -1 dom 3      …y los tres días siguientes
    mes 07                  todo julio; mes 07..08, julio y agosto
"""

from __future__ import annotations

import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

DIAS = ("lun", "mar", "mie", "jue", "vie", "sab", "dom")


def pascua(anio: int) -> date:
    """Domingo de Pascua del calendario gregoriano (algoritmo anónimo de Meeus, Jones y Butcher)."""
    a, b, c = anio % 19, anio // 100, anio % 100
    d, e = b // 4, b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = c // 4, c % 4
    j = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * j) // 451
    mes = (h + j - 7 * m + 114) // 31
    dia = (h + j - 7 * m + 114) % 31 + 1
    return date(anio, mes, dia)


def _dia(anio: int, mes: int, dia: int) -> date:
    """La fecha, o el último día del mes si no existe (29 de febrero en un año común)."""
    return date(anio, mes, min(dia, calendar.monthrange(anio, mes)[1]))


def _nesimo(anio: int, mes: int, n: int, dia_semana: int) -> date:
    """El n-ésimo día de la semana del mes (n = −1 es el último)."""
    if n > 0:
        primero = date(anio, mes, 1)
        return primero + timedelta(days=(dia_semana - primero.weekday()) % 7 + 7 * (n - 1))
    ultimo = date(anio, mes, calendar.monthrange(anio, mes)[1])
    return ultimo - timedelta(days=(ultimo.weekday() - dia_semana) % 7 + 7 * (-n - 1))


@dataclass(frozen=True, slots=True)
class Regla:
    texto: str

    def __post_init__(self) -> None:
        if not REGLA.fullmatch(self.texto):
            raise ValueError(f"regla de fecha inválida: {self.texto!r}")

    def fechas(self, anio: int) -> tuple[date, date]:
        """(inicio, fin) de la edición que empieza en ``anio``."""
        tipo, _, resto = self.texto.partition(" ")
        if tipo == "fija":
            ini, _, fin = resto.partition("..")
            (m1, d1), (m2, d2) = map(int, ini.split("-")), map(int, (fin or ini).split("-"))
            inicio = _dia(anio, m1, d1)
            # 12-25..01-06: termina el año siguiente
            return inicio, _dia(anio + 1 if (m2, d2) < (m1, d1) else anio, m2, d2)
        if tipo == "pascua":
            ini, _, fin = resto.partition("..")
            domingo = pascua(anio)
            return domingo + timedelta(days=int(ini)), domingo + timedelta(days=int(fin or ini))
        if tipo == "nesimo":
            partes = resto.split()
            mes, n, dia = int(partes[0]), int(partes[1]), DIAS.index(partes[2])
            extra = int(partes[3]) if len(partes) > 3 else 0
            inicio = _nesimo(anio, mes, n, dia)
            return inicio, inicio + timedelta(days=extra)
        ini, _, fin = resto.partition("..")
        mes_ini, mes_fin = int(ini), int(fin or ini)
        anio_fin = anio + 1 if mes_fin < mes_ini else anio  # mes 11..02: noviembre a febrero
        return date(anio, mes_ini, 1), date(anio_fin, mes_fin, calendar.monthrange(anio_fin, mes_fin)[1])

    def cae_en(self, inicio: date, fin: date) -> tuple[date, date] | None:
        """La edición que se cruza con el viaje [inicio, fin], o None si ninguna se cruza."""
        for anio in (inicio.year - 1, inicio.year, fin.year):
            a, b = self.fechas(anio)
            if a <= fin and b >= inicio:
                return a, b
        return None


_MMDD = r"(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])"
REGLA = re.compile(
    rf"fija {_MMDD}(\.\.{_MMDD})?"
    r"|pascua -?\d{1,3}(\.\.-?\d{1,3})?"
    rf"|nesimo (0[1-9]|1[0-2]) (-1|[1-5]) ({'|'.join(DIAS)})( \d{{1,2}})?"
    r"|mes (0[1-9]|1[0-2])(\.\.(0[1-9]|1[0-2]))?"
)

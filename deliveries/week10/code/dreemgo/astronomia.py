"""
El Sol y la Luna en las noches del viaje: a qué hora oscurece del todo, cuánta luna hay y cuándo
sale o se pone (decisión 0018).

Usa las fórmulas de baja precisión del Astronomical Almanac. La posición de la Luna sale con
unos 0,3° de error, y eso da su salida y su puesta con unos minutos de error; la del Sol, con
menos. Para decir «la luna se pone hacia las 21:40» basta. Como el calendario, corre en el
API, así que solo usa la biblioteca estándar y no tiene azar.

Las horas son las del Perú: UTC−5 todo el año.
"""

from __future__ import annotations

import calendar
import math
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta, timezone

PERU = timezone(timedelta(hours=-5))
_J2000 = datetime(2000, 1, 1, 12, tzinfo=UTC)
OSCURO_GRADOS = -18.0  # el Sol más abajo que esto: ya no queda luz del crepúsculo
PASO_MIN = 5
# La noche se recorre de las 17:00 a las 8:00 del día siguiente: en el Perú oscurece del todo
# entre las 18:50 y las 20:00, y aclara entre las 4:20 y las 5:30.
DESDE = time(17, 0)
HORAS_DE_RECORRIDO = 15
LUNA_QUE_NO_ESTORBA = 0.05  # un hilo de luna no apaga ninguna estrella


def _siglos(t: datetime) -> float:
    return (t - _J2000).total_seconds() / 86_400 / 36_525


def _sen(grados: float) -> float:
    return math.sin(math.radians(grados))


def _cos(grados: float) -> float:
    return math.cos(math.radians(grados))


def _longitud_del_sol(siglos: float) -> float:
    media = 280.460 + 36_000.770 * siglos
    anomalia = 357.528 + 35_999.050 * siglos
    return (media + 1.915 * _sen(anomalia) + 0.020 * _sen(2 * anomalia)) % 360


def _luna_ecliptica(siglos: float) -> tuple[float, float, float]:
    """(longitud, latitud, paralaje horizontal) de la Luna, en grados."""
    t = siglos
    longitud = (
        218.32
        + 481_267.881 * t
        + 6.29 * _sen(135.0 + 477_198.87 * t)
        - 1.27 * _sen(259.3 - 413_335.36 * t)
        + 0.66 * _sen(235.7 + 890_534.22 * t)
        + 0.21 * _sen(269.9 + 954_397.74 * t)
        - 0.19 * _sen(357.5 + 35_999.05 * t)
        - 0.11 * _sen(186.5 + 966_404.03 * t)
    ) % 360
    latitud = (
        5.13 * _sen(93.3 + 483_202.02 * t)
        + 0.28 * _sen(228.2 + 960_400.89 * t)
        - 0.28 * _sen(318.3 + 6_003.15 * t)
        - 0.17 * _sen(217.6 - 407_332.21 * t)
    )
    paralaje = (
        0.9508
        + 0.0518 * _cos(135.0 + 477_198.87 * t)
        + 0.0095 * _cos(259.3 - 413_335.36 * t)
        + 0.0078 * _cos(235.7 + 890_534.22 * t)
        + 0.0028 * _cos(269.9 + 954_397.74 * t)
    )
    return longitud, latitud, paralaje


def _ecuatoriales(longitud: float, latitud: float, siglos: float) -> tuple[float, float]:
    """(ascensión recta, declinación) en grados, de coordenadas de la eclíptica."""
    e = math.radians(23.439 - 0.013 * siglos)
    lam, beta = math.radians(longitud), math.radians(latitud)
    x = math.cos(beta) * math.cos(lam)
    y = math.cos(e) * math.cos(beta) * math.sin(lam) - math.sin(e) * math.sin(beta)
    z = math.sin(e) * math.cos(beta) * math.sin(lam) + math.cos(e) * math.sin(beta)
    return math.degrees(math.atan2(y, x)) % 360, math.degrees(math.asin(z))


def _altura(ascension: float, declinacion: float, t: datetime, lat: float, lon: float) -> float:
    dias = (t - _J2000).total_seconds() / 86_400
    sidereo = (280.46061837 + 360.98564736629 * dias) % 360
    angulo = math.radians((sidereo + lon - ascension) % 360)
    phi, delta = math.radians(lat), math.radians(declinacion)
    return math.degrees(math.asin(math.sin(phi) * math.sin(delta) + math.cos(phi) * math.cos(delta) * math.cos(angulo)))


def altura_del_sol(t: datetime, lat: float, lon: float) -> float:
    siglos = _siglos(t)
    return _altura(*_ecuatoriales(_longitud_del_sol(siglos), 0.0, siglos), t, lat, lon)


def _luna(t: datetime, lat: float, lon: float) -> tuple[float, float]:
    """(altura de la Luna sobre el horizonte, menos la que tiene al salir), en grados: positiva
    si está a la vista. Al salir y al ponerse su centro está a 0,7275 de su paralaje menos 34′,
    por la paralaje y la refracción."""
    siglos = _siglos(t)
    longitud, latitud, paralaje = _luna_ecliptica(siglos)
    altura = _altura(*_ecuatoriales(longitud, latitud, siglos), t, lat, lon)
    return altura - (0.7275 * paralaje - 0.5667), paralaje


def iluminada(t: datetime) -> tuple[float, bool]:
    """(parte iluminada de la Luna, de 0 a 1; si está creciente) en el instante ``t``."""
    siglos = _siglos(t)
    longitud, latitud, _ = _luna_ecliptica(siglos)
    elongacion = (longitud - _longitud_del_sol(siglos)) % 360
    coseno = math.cos(math.radians(latitud)) * math.cos(math.radians(elongacion))
    return (1 - coseno) / 2, elongacion < 180


@dataclass(frozen=True, slots=True)
class Noche:
    """Lo que hace el cielo una noche en un lugar, en hora del Perú. La noche oscura va del fin
    del crepúsculo de la tarde (el Sol a 18° bajo el horizonte) al comienzo del de la mañana."""

    fecha: date  # el día en que empieza la noche
    oscurece: time
    aclara: time
    luna: float  # parte iluminada a medianoche, de 0 a 1
    creciente: bool
    luna_sale: time | None  # si sale durante la noche oscura
    luna_se_pone: time | None  # si se pone durante la noche oscura
    horas_oscuras: float  # entre que oscurece y aclara
    horas_sin_luna: float  # de esas, las que la Luna está bajo el horizonte o casi no alumbra


def _hora(t: datetime) -> time:
    """La hora del Perú, redondeada a los cinco minutos."""
    local = (t.astimezone(PERU) + timedelta(minutes=2, seconds=30)).replace(second=0, microsecond=0)
    return local.replace(minute=local.minute - local.minute % 5).time()


def _cruce(t0: datetime, a0: float, a1: float) -> datetime:
    """Cuándo, entre t0 y t0 + un paso, una altura que pasa de a0 a a1 cruza el cero."""
    return t0 + timedelta(minutes=PASO_MIN * a0 / (a0 - a1))


def noche(fecha: date, lat: float, lon: float) -> Noche:
    """La noche que empieza el día ``fecha`` en (lat, lon)."""
    inicio = datetime.combine(fecha, DESDE, tzinfo=PERU)
    pasos = HORAS_DE_RECORRIDO * 60 // PASO_MIN
    instantes = [inicio + timedelta(minutes=PASO_MIN * i) for i in range(pasos + 1)]
    sol = [altura_del_sol(t, lat, lon) - OSCURO_GRADOS for t in instantes]
    luna = [_luna(t, lat, lon)[0] for t in instantes]
    medianoche = datetime.combine(fecha + timedelta(days=1), time(0, 0), tzinfo=PERU)
    parte, creciente = iluminada(medianoche)

    oscurece = aclara = None
    for i in range(pasos):
        if oscurece is None and sol[i] >= 0 > sol[i + 1]:
            oscurece = _cruce(instantes[i], sol[i], sol[i + 1])
        elif oscurece is not None and sol[i] < 0 <= sol[i + 1]:
            aclara = _cruce(instantes[i], sol[i], sol[i + 1])
            break
    if oscurece is None or aclara is None:  # no pasa en el Perú; por si acaso, la noche entera
        oscurece, aclara = instantes[0], instantes[-1]

    sale = se_pone = None
    sin_luna = 0.0
    for i in range(pasos):
        t0, t1 = instantes[i], instantes[i + 1]
        if t1 <= oscurece or t0 >= aclara:
            continue
        if luna[i] < 0 <= luna[i + 1] and sale is None:
            sale = _cruce(t0, luna[i], luna[i + 1])
        if luna[i] >= 0 > luna[i + 1] and se_pone is None:
            se_pone = _cruce(t0, luna[i], luna[i + 1])
        dentro = (min(t1, aclara) - max(t0, oscurece)).total_seconds() / 3_600
        if parte < LUNA_QUE_NO_ESTORBA or (luna[i] < 0 and luna[i + 1] < 0):
            sin_luna += dentro
        elif luna[i] < 0 or luna[i + 1] < 0:
            sin_luna += dentro / 2
    return Noche(
        fecha=fecha,
        oscurece=_hora(oscurece),
        aclara=_hora(aclara),
        luna=round(parte, 3),
        creciente=creciente,
        luna_sale=None if sale is None or not oscurece < sale < aclara else _hora(sale),
        luna_se_pone=None if se_pone is None or not oscurece < se_pone < aclara else _hora(se_pone),
        horas_oscuras=round((aclara - oscurece).total_seconds() / 3_600, 1),
        horas_sin_luna=round(sin_luna, 1),
    )


def lunas_nuevas(anio: int, mes: int) -> list[date]:
    """Los días del mes en cuya noche la Luna está nueva: donde pasa de menguante a creciente,
    el de menos luna de los dos."""
    ultimo = calendar.monthrange(anio, mes)[1]
    dias = [date(anio, mes, 1) + timedelta(days=k) for k in range(-1, ultimo + 1)]
    medias = [iluminada(datetime.combine(d + timedelta(days=1), time(0, 0), tzinfo=PERU)) for d in dias]
    salida = []
    pares = list(zip(dias, medias, strict=True))
    for (d0, (p0, c0)), (d1, (p1, c1)) in zip(pares, pares[1:], strict=False):
        if not c0 and c1:
            nueva = d0 if p0 <= p1 else d1
            if nueva.month == mes and nueva not in salida:
                salida.append(nueva)
    return salida

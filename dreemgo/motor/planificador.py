"""
Qué visitar cada día y en qué orden: orientación por equipos (decisión 0004).

Cada jornada es un recorrido que sale de un depósito (la base del polo o, en un viaje de un
día, la ciudad de origen) y vuelve a él, con un tope de minutos entre traslados, esperas y
visitas. Cada parada vale algo; el objetivo es juntar el mayor valor posible en las
jornadas disponibles, visitando cada lugar dentro de su horario.

Heurística determinista:
0. Semilla: cada jornada vacía arranca con la parada de más valor que cabe sola en ella,
   para que un lugar de jerarquía 4 a una hora no pierda frente a cinco plazas cercanas.
1. Inserción voraz: en cada vuelta entra la parada, en la jornada y la posición, que da más
   valor por minuto agregado sin pasar el tope ni salirse de un horario. El valor de una
   parada baja un 20 % por cada otra del mismo subtipo ya elegida, para que tres iglesias
   seguidas no le ganen a una iglesia, un mirador y un museo.
2. 2-opt en cada jornada: se invierte un tramo mientras baje el tiempo total.
3. Otra vuelta de inserción con el tiempo que liberó el 2-opt.

Los empates se rompen por el orden de las candidatas, así que la misma entrada da siempre
el mismo itinerario.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

REPETIDO = 0.8  # el valor de una parada se multiplica por esto por cada otra de su subtipo
ALFA = 2.0  # orden de inserción: valor**ALFA por minuto agregado
# Arranques de la heurística (semilla, alfa): se queda el de más valor. En 705 polos de 60
# consultas al azar, el mejor de los tres junta 2,6 % más valor que el primero solo.
ARRANQUES = ((False, 2.0), (False, 1.0), (True, 1.0))
PARADAS_POR_DIA = 6  # más que esto en un día no se disfruta


@dataclass(frozen=True)
class Candidata:
    """Una parada posible. ``i`` es su posición en las matrices de tiempos."""

    i: int
    valor: float
    visita: int  # minutos en el lugar, con la caminata de ida y vuelta
    abre: int = 0  # minuto del día
    cierra: int = 24 * 60
    subtipo: str | None = None
    dias: frozenset[int] | None = None  # días de la semana en que atiende (0 = lunes)


@dataclass(frozen=True)
class Jornada:
    inicio: int  # minuto del día en que se sale del depósito
    tope: int  # minutos hasta estar de vuelta en el depósito
    dia_semana: int | None = None


@dataclass
class Visita:
    candidata: Candidata
    llegada: int  # minuto del día
    traslado: int  # minutos desde la parada anterior o desde el depósito
    espera: int


@dataclass
class Recorrido:
    jornada: Jornada
    visitas: list[Visita] = field(default_factory=list)
    salida: int = 0  # minuto en que conviene salir del depósito
    vuelta: int = 0  # minuto en que se está de regreso
    regreso: int = 0  # minutos de la última parada al depósito

    @property
    def minutos(self) -> int:
        return self.vuelta - self.salida if self.visitas else 0


class Tiempos:
    """Minutos de viaje entre el depósito (índice -1) y las paradas."""

    def __init__(self, desde_deposito: np.ndarray, entre: np.ndarray):
        n = len(desde_deposito)
        m = np.full((n + 1, n + 1), np.inf)
        m[:n, :n] = np.where(np.isfinite(entre), entre, np.inf)
        m[n, :n] = m[:n, n] = np.where(np.isfinite(desde_deposito), desde_deposito, np.inf)
        m[n, n] = 0.0
        self.m = m
        self.deposito = n

    def __call__(self, a: int, b: int) -> float:
        return self.m[self.deposito if a < 0 else a, self.deposito if b < 0 else b]


def horario(ruta: list[Candidata], jornada: Jornada, t: Tiempos) -> Recorrido | None:
    """El recorrido con sus horas, o None si no cabe en la jornada o en algún horario.

    Si la primera parada todavía no abre, se sale más tarde en vez de esperar en la puerta:
    la jornada se cuenta desde que se sale."""
    if not ruta:
        return Recorrido(jornada, salida=jornada.inicio, vuelta=jornada.inicio)
    primera = ruta[0]
    salida = max(jornada.inicio, primera.abre - int(round(t(-1, primera.i))))
    ahora, anterior, visitas = salida, -1, []
    for c in ruta:
        traslado = t(anterior, c.i)
        if not np.isfinite(traslado):
            return None
        if c.dias is not None and jornada.dia_semana is not None and jornada.dia_semana not in c.dias:
            return None
        llegada = ahora + int(round(traslado))
        espera = max(0, c.abre - llegada)
        if llegada + espera + c.visita > c.cierra:
            return None
        visitas.append(Visita(c, llegada, int(round(traslado)), espera))
        ahora = llegada + espera + c.visita
        anterior = c.i
    regreso = t(anterior, -1)
    if not np.isfinite(regreso):
        return None
    vuelta = ahora + int(round(regreso))
    if vuelta - salida > jornada.tope:
        return None
    return Recorrido(jornada, visitas, salida, vuelta, int(round(regreso)))


def _valor(c: Candidata, elegidas: dict[str | None, int]) -> float:
    return c.valor * REPETIDO ** elegidas.get(c.subtipo, 0) if c.subtipo else c.valor


def _insertar(
    rutas: list[list[Candidata]], jornadas: list[Jornada], pendientes: list[Candidata], t: Tiempos, alfa: float = ALFA
) -> None:
    """Inserción voraz (paso 1), en el lugar."""
    elegidas: dict[str | None, int] = {}
    for ruta in rutas:
        for c in ruta:
            elegidas[c.subtipo] = elegidas.get(c.subtipo, 0) + 1
    actuales = [horario(r, j, t) for r, j in zip(rutas, jornadas, strict=True)]
    while pendientes:
        opciones = []
        vistas_vacias = set()
        for k, (ruta, jornada) in enumerate(zip(rutas, jornadas, strict=True)):
            if not ruta:  # jornadas vacías iguales son intercambiables: basta probar la primera
                firma = (jornada.inicio, jornada.tope, jornada.dia_semana)
                if firma in vistas_vacias:
                    continue
                vistas_vacias.add(firma)
            if len(ruta) >= PARADAS_POR_DIA:
                continue
            usado = actuales[k].minutos
            nodos = [-1, *(c.i for c in ruta), -1]
            for pos in range(len(ruta) + 1):
                a, b = nodos[pos], nodos[pos + 1]
                quitar = t(a, b) if ruta else 0.0
                for orden, c in enumerate(pendientes):
                    extra = t(a, c.i) + t(c.i, b) - quitar + c.visita
                    if not np.isfinite(extra) or usado + extra > jornada.tope:
                        continue
                    opciones.append((-(_valor(c, elegidas) ** alfa) / max(extra, 1.0), k, pos, orden))
        if not opciones:
            return
        opciones.sort()
        for _, k, pos, orden in opciones:
            c = pendientes[orden]
            nueva = [*rutas[k][:pos], c, *rutas[k][pos:]]
            recorrido = horario(nueva, jornadas[k], t)
            if recorrido is not None:
                rutas[k], actuales[k] = nueva, recorrido
                pendientes.pop(orden)
                elegidas[c.subtipo] = elegidas.get(c.subtipo, 0) + 1
                break
        else:
            return


def _dos_opt(ruta: list[Candidata], jornada: Jornada, t: Tiempos) -> list[Candidata]:
    """Paso 2: invierte tramos mientras el recorrido termine antes."""
    mejor = horario(ruta, jornada, t)
    mejora = mejor is not None
    while mejora:
        mejora = False
        for i in range(len(ruta) - 1):
            for j in range(i + 1, len(ruta)):
                prueba = ruta[:i] + ruta[i : j + 1][::-1] + ruta[j + 1 :]
                r = horario(prueba, jornada, t)
                if r is not None and r.minutos < mejor.minutos:
                    ruta, mejor, mejora = prueba, r, True
    return ruta


def _sembrar(rutas: list[list[Candidata]], jornadas: list[Jornada], pendientes: list[Candidata], t: Tiempos) -> None:
    """Paso 0: la parada de más valor que cabe sola en cada jornada (la más cercana si empatan)."""
    for k, jornada in enumerate(jornadas):
        orden = sorted(range(len(pendientes)), key=lambda o: (-pendientes[o].valor, t(-1, pendientes[o].i), o))
        for o in orden:
            if horario([pendientes[o]], jornada, t) is not None:
                rutas[k] = [pendientes.pop(o)]
                break


def planificar(
    candidatas: list[Candidata], jornadas: list[Jornada], t: Tiempos, semilla: bool = False, alfa: float = ALFA
) -> list[Recorrido]:
    """Un recorrido por jornada, en el mismo orden. Una jornada puede quedar sin paradas."""
    rutas: list[list[Candidata]] = [[] for _ in jornadas]
    pendientes = list(candidatas)
    if semilla:
        _sembrar(rutas, jornadas, pendientes, t)
    _insertar(rutas, jornadas, pendientes, t, alfa)
    rutas = [_dos_opt(r, j, t) for r, j in zip(rutas, jornadas, strict=True)]
    _insertar(rutas, jornadas, pendientes, t, alfa)
    return [horario(r, j, t) for r, j in zip(rutas, jornadas, strict=True)]


def valor_visitado(recorridos: list[Recorrido]) -> float:
    """El valor visitado, con la misma rebaja por subtipo repetido que guía la inserción."""
    vistos: dict[str | None, int] = {}
    total = 0.0
    for r in recorridos:
        for v in r.visitas:
            c = v.candidata
            n = vistos.get(c.subtipo, 0) if c.subtipo else 0
            total += c.valor * REPETIDO**n
            if c.subtipo:
                vistos[c.subtipo] = n + 1
    return total


def mejor_plan(candidatas: list[Candidata], jornadas: list[Jornada], t: Tiempos) -> list[Recorrido]:
    """El de más valor entre los ``ARRANQUES``; si empatan, el primero."""
    mejor, valor = None, -1.0
    for semilla, alfa in ARRANQUES:
        plan = planificar(candidatas, jornadas, t, semilla=semilla, alfa=alfa)
        v = valor_visitado(plan)
        if v > valor + 1e-9:
            mejor, valor = plan, v
    return mejor

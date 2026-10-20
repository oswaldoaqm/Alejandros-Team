"""
Qué visitar cada día y en qué orden: orientación por equipos (decisión 0004).

Cada jornada es un recorrido que sale de un depósito (la base del polo o, en un viaje de un
día, la ciudad de origen) y vuelve a él, con un tope de minutos entre traslados, esperas y
visitas. Cada parada vale algo; el objetivo es juntar el mayor valor posible en las
jornadas disponibles, visitando cada lugar dentro de su horario. Si el primer lugar abre
tarde, se sale más tarde, pero la jornada no se corre: se vuelve, a más tardar, a su hora
de siempre, el final de su tope más la hora del almuerzo (las 17:00 en un día entero, desde
la decisión 0019). Antes, un día podía empezar a las 18:00 en un teatro y terminar de noche.
Y no se espera más de una hora en la puerta de un lugar a que abra, sin contar el almuerzo:
antes, un día podía llegar a las 8:53 a una casa museo que abre a las 15:00.

El almuerzo (decisión 0019) es una hora que no cuenta en el tope, pero corre el reloj: los
horarios de los lugares se miran con la hora real. Se almuerza en el primer momento que toca:

- antes de salir, en el depósito, si se sale después de las 12:30, o desde las 11:30 si al
  primer lugar se llega después de las 14:00. Si la salida espera a que abra el primer lugar y
  hay tiempo, a la hora (a las 12:30, o al empezar la jornada si es más tarde), sin atrasar la
  salida; si no, al salir, y se sale una hora después;
- al llegar a un lugar después de las 14:00; o desde las 11:30, si el lugar abre en una hora o
  más (mientras abre) o si su visita terminaría después de las 14:00 y, almorzando antes, cabe
  en su horario;
- al terminar una visita después de las 12:30, salvo que este lugar no tenga dónde comer, el
  siguiente sí y allá todavía se almuerce a la hora: entonces allá, al llegar si así cabe en su
  horario, o al terminar su visita;
- al terminar una visita desde las 11:30, si en lo que sigue ya no se almorzaría a la hora: se
  llega después de las 14:00, o su visita terminaría después de las 14:00 y almorzando antes no
  cabe en su horario;
- y si se vuelve al depósito sin almorzar después de las 12:30, en el depósito, fuera de la
  jornada.

Una jornada tranquila, el primer día en la altura (decisión 0020), no admite paradas exigentes ni
más altas que su altura máxima: se filtran al elegir en qué jornada puede ir cada una, antes de
armar un horario, que se arma unas 3 700 veces por consulta.

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
ALMUERZO_MIN = 60
ALMUERZO_DESDE = 12 * 60 + 30  # al terminar una visita desde esta hora, se almuerza
ALMUERZO_TEMPRANO = 11 * 60 + 30  # antes de un traslado que llega después de las 14:00, desde esta hora
ALMUERZO_HASTA = 14 * 60  # si un traslado llega después de esta hora sin almorzar, se almuerza al llegar
ESPERA_MAX = 60  # lo más que se espera a que un lugar abra, fuera del almuerzo


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
    comida: bool = False  # si hay dónde comer cerca (pipeline/comida.py)
    altura: int | None = None  # metros sobre el mar
    exigente: bool = False  # una caminata de acceso larga o una visita larga (aclimatacion.exigente)


@dataclass(frozen=True)
class Jornada:
    inicio: int  # minuto del día en que se sale del depósito
    tope: int  # minutos hasta estar de vuelta en el depósito, sin contar el almuerzo
    # Y se vuelve, a más tardar, en inicio + tope + la hora del almuerzo: la jornada no se corre.
    dia_semana: int | None = None
    comida_en_deposito: bool = True  # la base es un pueblo con hospedaje: se da por hecho que hay dónde comer
    # El primer día en la altura (decisión 0020): ninguna parada más alta que esto ni, si es tranquila, exigente.
    altura_max: int | None = None
    tranquila: bool = False


def admite(jornada: Jornada, c: Candidata) -> bool:
    """Si la parada puede ir en la jornada: en una tranquila, ninguna exigente; con altura máxima, ninguna
    más alta, ni una de la que no se sabe la altura."""
    if jornada.tranquila and c.exigente:
        return False
    return jornada.altura_max is None or (c.altura is not None and c.altura <= jornada.altura_max)


def _con_reglas(jornada: Jornada) -> bool:
    return jornada.tranquila or jornada.altura_max is not None


@dataclass(frozen=True)
class Almuerzo:
    despues_de: int  # cuántas visitas del día van antes
    hora: int  # minuto del día en que empieza
    en: int | None  # la parada (``Candidata.i``) donde se almuerza; None en el depósito
    dentro: bool  # si corre el reloj de la jornada: entre la salida y la vuelta


@dataclass
class Visita:
    candidata: Candidata
    llegada: int  # minuto del día; si se almuerza al llegar, el de después del almuerzo
    traslado: int  # minutos desde la parada anterior o desde el depósito
    espera: int


@dataclass
class Recorrido:
    jornada: Jornada
    visitas: list[Visita] = field(default_factory=list)
    salida: int = 0  # minuto en que conviene salir del depósito
    vuelta: int = 0  # minuto en que se está de regreso
    regreso: int = 0  # minutos de la última parada al depósito
    almuerzo: Almuerzo | None = None

    @property
    def minutos(self) -> int:
        """Los minutos de la jornada entre traslados, esperas y visitas: el almuerzo no cuenta."""
        if not self.visitas:
            return 0
        return self.vuelta - self.salida - (ALMUERZO_MIN if self.almuerzo is not None and self.almuerzo.dentro else 0)


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
    """El recorrido con sus horas y su almuerzo, o None si no cabe en la jornada o en algún horario.

    Si la primera parada todavía no abre, se sale más tarde en vez de esperar en la puerta:
    la jornada se cuenta desde que se sale, pero se vuelve a la hora de siempre. El almuerzo,
    como dice el comienzo del módulo."""
    if not ruta:
        return Recorrido(jornada, salida=jornada.inicio, vuelta=jornada.inicio)
    primera = ruta[0]
    salida = max(jornada.inicio, primera.abre - int(round(t(-1, primera.i))))
    almuerzo = None
    llega_a_la_primera = salida + t(-1, primera.i)
    if salida >= ALMUERZO_DESDE or (salida >= ALMUERZO_TEMPRANO and llega_a_la_primera > ALMUERZO_HASTA):
        # Antes de salir, en el depósito: a la hora, si antes de salir hay una hora libre; si no, al salir.
        a_la_hora = max(jornada.inicio, ALMUERZO_DESDE if salida >= ALMUERZO_DESDE else ALMUERZO_TEMPRANO)
        if a_la_hora + ALMUERZO_MIN <= salida:
            almuerzo = Almuerzo(0, a_la_hora, None, dentro=False)
        else:
            almuerzo = Almuerzo(0, salida, None, dentro=False)
            salida += ALMUERZO_MIN
    ahora, anterior, visitas, al_llegar = salida, -1, [], False
    for k, c in enumerate(ruta):
        traslado = t(anterior, c.i)
        if not np.isfinite(traslado):
            return None
        if c.dias is not None and jornada.dia_semana is not None and jornada.dia_semana not in c.dias:
            return None
        llegada = ahora + int(round(traslado))
        mientras_abre = c.abre - llegada >= ALMUERZO_MIN
        termina_tarde = max(llegada, c.abre) + c.visita > ALMUERZO_HASTA
        cabe_despues = max(llegada + ALMUERZO_MIN, c.abre) + c.visita <= c.cierra
        a_la_hora = llegada >= ALMUERZO_TEMPRANO and (mientras_abre or (termina_tarde and cabe_despues))
        if almuerzo is None and (al_llegar or llegada > ALMUERZO_HASTA or a_la_hora):
            almuerzo = Almuerzo(k, llegada, c.i, dentro=True)
            llegada_a_visitar = llegada + ALMUERZO_MIN  # la hora de la parada es la de después de almorzar
        else:
            llegada_a_visitar = llegada
        espera = max(0, c.abre - llegada_a_visitar)
        if espera > ESPERA_MAX or llegada_a_visitar + espera + c.visita > c.cierra:
            return None
        visitas.append(Visita(c, llegada_a_visitar, int(round(traslado)), espera))
        ahora = llegada_a_visitar + espera + c.visita
        anterior = c.i
        if almuerzo is None and ahora >= ALMUERZO_TEMPRANO:
            siguiente = ruta[k + 1] if k + 1 < len(ruta) else None
            hasta_siguiente = t(c.i, siguiente.i if siguiente is not None else -1)
            llega_alla = ahora + (int(round(hasta_siguiente)) if np.isfinite(hasta_siguiente) else 0)
            if siguiente is None:  # se vuelve al depósito
                alla, cabe_alla, termina_alla = jornada.comida_en_deposito, True, llega_alla
            else:
                alla = siguiente.comida
                cabe_alla = max(llega_alla + ALMUERZO_MIN, siguiente.abre) + siguiente.visita <= siguiente.cierra
                termina_alla = max(llega_alla, siguiente.abre) + siguiente.visita
            # Si allá ya no se almorzaría a la hora: se llega tarde, o su visita termina tarde y antes no cabe.
            tarde = llega_alla > ALMUERZO_HASTA or (termina_alla > ALMUERZO_HASTA and not cabe_alla)
            if ahora >= ALMUERZO_DESDE:
                if c.comida or not alla or tarde:
                    almuerzo = Almuerzo(k + 1, ahora, c.i, dentro=True)
                elif cabe_alla:  # allá hay dónde comer y se llega a la hora: al llegar
                    al_llegar = siguiente is not None
                # Y si no cabe al llegar, al terminar la visita de allá, que todavía es a la hora.
            elif tarde:
                almuerzo = Almuerzo(k + 1, ahora, c.i, dentro=True)
            if almuerzo is not None:
                ahora += ALMUERZO_MIN
    regreso = t(anterior, -1)
    if not np.isfinite(regreso):
        return None
    vuelta = ahora + int(round(regreso))
    if almuerzo is None and vuelta >= ALMUERZO_DESDE:  # se vuelve sin almorzar: en el depósito
        almuerzo = Almuerzo(len(ruta), vuelta, None, dentro=False)
    recorrido = Recorrido(jornada, visitas, salida, vuelta, int(round(regreso)), almuerzo)
    if recorrido.minutos > jornada.tope or vuelta > jornada.inicio + jornada.tope + ALMUERZO_MIN:
        return None
    return recorrido


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
                firma = (jornada.inicio, jornada.tope, jornada.dia_semana, jornada.altura_max, jornada.tranquila)
                if firma in vistas_vacias:
                    continue
                vistas_vacias.add(firma)
            if len(ruta) >= PARADAS_POR_DIA:
                continue
            usado = actuales[k].minutos
            nodos = [-1, *(c.i for c in ruta), -1]
            posibles = list(enumerate(pendientes))
            if _con_reglas(jornada):
                posibles = [(orden, c) for orden, c in posibles if admite(jornada, c)]
            for pos in range(len(ruta) + 1):
                a, b = nodos[pos], nodos[pos + 1]
                quitar = t(a, b) if ruta else 0.0
                for orden, c in posibles:
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
            if admite(jornada, pendientes[o]) and horario([pendientes[o]], jornada, t) is not None:
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

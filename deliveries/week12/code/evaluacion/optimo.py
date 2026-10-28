"""
La distancia del itinerario al óptimo exacto (semana 12). La dejó para esta semana la decisión 0009.

El planificador (``dreemgo/motor/planificador.py``) elige qué visitar cada día y en qué orden con una
heurística: inserción voraz, 2-opt y tres arranques. El problema exacto, con 40 candidatas y hasta 14 días,
no cabe en el segundo de respuesta. Aquí se resuelve exacto en instancias chicas sacadas de los viajes
reales, y se compara con lo que arma la heurística sobre la misma instancia.

Cada instancia es un viaje que propone el motor para una de las 40 consultas de la evaluación
(``consultas.csv``): sus jornadas tal cual y solo sus ``n`` mejores candidatas, las de más valor por minuto,
como las elige el motor (``viaje._mejores``). Las reglas son las mismas porque las decide la misma función,
``planificador.horario``: el horario de cada lugar, el almuerzo, una hora de espera como mucho, la jornada
que no se corre, el día tranquilo en la altura y, como en la heurística, seis paradas por día.

Lo que se compara es el valor de lo visitado, con la rebaja del 20 % por cada parada del mismo subtipo
contada de la de más valor a la de menos (``valor_del_conjunto``): así el valor de un plan no depende del
orden de sus visitas. ``planificador.valor_visitado`` las cuenta en su orden y puede dar un poco menos.

La búsqueda exacta tiene dos pasos:

1. Por cada tipo de jornada, todos los conjuntos de hasta seis paradas que caben en algún orden
   (``conjuntos_que_caben``). Es un recorrido en profundidad por los órdenes posibles, y ``horario`` decide
   cada uno. Una rama se corta solo si ninguna continuación puede caber: si una parada terminaría después
   de su cierre aun sin almorzar, o si los traslados y las visitas, más la vuelta directa al depósito, ya
   pasan el tope o la hora de volver. La vuelta directa es lo menos que puede tardar el resto del camino
   porque los tiempos son de camino más corto: cada instancia lo revisa (``desigualdad_triangular``), y la
   holgura suma el redondeo de cada tramo, que ``horario`` hace por separado.
2. Ramificación y acotamiento sobre las jornadas (``exacto``): un conjunto por jornada, sin repetir paradas.
   Las cotas valen porque el valor no baja al sumar paradas y lo que suma un conjunto nunca pasa de lo que
   vale solo. Las jornadas iguales seguidas eligen en orden, para no probar lo mismo permutado.

Si una búsqueda pasa de su plazo, la instancia se cuenta aparte, sin resolver.

Escribe en data/evaluacion/resultados/:

  optimo.csv    cada viaje y cada tamaño: sus jornadas y candidatas, cuántas paradas visitan la heurística
                y el óptimo, el valor de cada uno, la brecha, el tiempo y las paradas que cambian
  optimo.json   el resumen por tamaño: en cuántos viajes se visita todo, en cuántos la heurística da el
                óptimo, la brecha y el tiempo de la búsqueda

Con los mismos datos sale lo mismo, salvo los segundos, que dependen de la computadora y de la corrida.

Uso:  python -m evaluacion.optimo [--candidatas 10 12 15] [--plazo 120]
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from dreemgo.motor import aclimatacion, viaje
from dreemgo.motor import datos as artefactos
from dreemgo.motor.datos import Datos
from dreemgo.motor.planificador import (
    ALMUERZO_MIN,
    PARADAS_POR_DIA,
    REPETIDO,
    Candidata,
    Jornada,
    Tiempos,
    admite,
    horario,
    mejor_plan,
)
from evaluacion import consultas

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "evaluacion" / "resultados"
TAMANOS = (10, 12, 15)  # candidatas por instancia
PLAZO_S = 120.0
# ``horario`` redondea cada tramo por separado: en los seis o siete tramos que pueden quedar, la suma
# redondeada puede quedar hasta 3 minutos por debajo de la vuelta directa redondeada.
REDONDEO_MIN = 4
TOLERANCIA = 1e-6  # el mismo conjunto, sumado en otro orden, puede diferir en los últimos decimales


def valor_del_conjunto(paradas: Sequence[Candidata]) -> float:
    """El valor de lo visitado, con la rebaja por subtipo repetido de la de más valor a la de menos."""
    total, por_subtipo = 0.0, {}
    for c in paradas:
        if c.subtipo:
            por_subtipo.setdefault(c.subtipo, []).append(c.valor)
        else:
            total += c.valor
    for valores in por_subtipo.values():
        valores.sort(reverse=True)
        total += sum(v * REPETIDO**k for k, v in enumerate(valores))
    return total


def desigualdad_triangular(cands: Sequence[Candidata], t: Tiempos) -> float:
    """Lo más que un tramo directo tarda de más que ir pasando por otro lugar, entre el depósito y las
    candidatas. Con tiempos de camino más corto es 0; si un tramo directo no existe y pasando por otro
    sí, es infinito."""
    nodos = [-1, *(c.i for c in cands)]
    m = np.array([[t(a, b) for b in nodos] for a in nodos], dtype=float)
    peor = 0.0
    with np.errstate(invalid="ignore"):
        for b in range(len(nodos)):
            pasando = m[:, [b]] + m[[b], :]
            exceso = m - pasando
            if np.any(np.isinf(m) & np.isfinite(pasando)):
                return math.inf
            exceso = exceso[np.isfinite(exceso)]
            if exceso.size:
                peor = max(peor, float(exceso.max()))
    return peor


def _redondo(minutos: float) -> float:
    return float(int(round(minutos))) if np.isfinite(minutos) else math.inf


def conjuntos_que_caben(
    cands: Sequence[Candidata], jornada: Jornada, t: Tiempos, holgura: float, hasta: float = math.inf
) -> dict[int, tuple[int, ...]] | None:
    """Cada conjunto de paradas que cabe en la jornada en algún orden, como máscara sobre ``cands`` (el bit
    k es ``cands[k]``), con un orden en que cabe. Siempre está el vacío. None si pasa la hora ``hasta``
    (``time.monotonic``)."""
    usables = [
        k
        for k, c in enumerate(cands)
        if admite(jornada, c) and (c.dias is None or jornada.dia_semana is None or jornada.dia_semana in c.dias)
    ]
    ida = {k: _redondo(t(-1, cands[k].i)) for k in usables}
    entre = {(a, b): _redondo(t(cands[a].i, cands[b].i)) for a in usables for b in usables if a != b}
    # Lo menos que tarda volver desde cada parada, pasando por las que falten: la vuelta directa, si los
    # tiempos cumplen la desigualdad triangular; si no, nada.
    vuelta = {k: _redondo(t(cands[k].i, -1)) - holgura if math.isfinite(holgura) else 0.0 for k in usables}
    hora_de_volver = jornada.inicio + jornada.tope + ALMUERZO_MIN
    caben: dict[int, tuple[int, ...]] = {0: ()}
    pasos = 0

    def probar(orden: tuple[int, ...], mascara: int, k: int, traslados: float, visitas: int, termina: float) -> bool:
        """Suma la parada k al orden, si alguna continuación puede caber, y sigue en profundidad. False si
        se acabó el plazo."""
        nonlocal pasos
        c = cands[k]
        if termina > c.cierra:
            return True
        if traslados + visitas + vuelta[k] > jornada.tope or termina + vuelta[k] > hora_de_volver:
            return True
        pasos += 1
        if pasos % 4096 == 0 and time.monotonic() > hasta:
            return False
        nuevo, clave = (*orden, k), mascara | (1 << k)
        if clave not in caben and horario([cands[j] for j in nuevo], jornada, t) is not None:
            caben[clave] = nuevo
        if len(nuevo) == PARADAS_POR_DIA:
            return True
        for s in usables:
            if clave >> s & 1 or not math.isfinite(entre[(k, s)]):
                continue
            llega = termina + entre[(k, s)]
            sigue = max(llega, cands[s].abre) + cands[s].visita
            if not probar(nuevo, clave, s, traslados + entre[(k, s)], visitas + cands[s].visita, sigue):
                return False
        return True

    for k in usables:
        if not math.isfinite(ida[k]):
            continue
        c = cands[k]
        # Como en horario: si el primer lugar todavía no abre, se sale más tarde. Sin almorzar, que solo atrasa.
        salida = max(jornada.inicio, c.abre - ida[k])
        termina = max(salida + ida[k], c.abre) + c.visita
        if not probar((), 0, k, ida[k], c.visita, termina):
            return None
    return caben


def _firma(j: Jornada) -> tuple:
    return (j.inicio, j.tope, j.dia_semana, j.comida_en_deposito, j.altura_max, j.tranquila)


@dataclass(frozen=True)
class Optimo:
    valor: float
    recorridos: list[tuple[int, ...]]  # por jornada, las posiciones en ``cands`` en un orden que cabe
    desigualdad: float
    conjuntos: int  # cuántos conjuntos caben, sumando los tipos de jornada
    segundos: float


def exacto(
    cands: Sequence[Candidata], jornadas: Sequence[Jornada], t: Tiempos, piso: float = 0.0, plazo: float = PLAZO_S
) -> Optimo | None:
    """El plan de más valor (``valor_del_conjunto``), con las reglas de ``horario`` y seis paradas por día
    como mucho. ``piso`` es el valor de un plan que ya se tiene, como el de la heuristica: acota desde el
    comienzo, y el óptimo vale eso o más. None si no termina en ``plazo`` segundos."""
    inicio = time.monotonic()
    hasta = inicio + plazo
    desigualdad = desigualdad_triangular(cands, t)
    holgura = REDONDEO_MIN + PARADAS_POR_DIA * desigualdad
    por_tipo: dict[tuple, dict[int, tuple[int, ...]]] = {}
    for j in jornadas:
        if _firma(j) not in por_tipo:
            caben = conjuntos_que_caben(cands, j, t, holgura, hasta)
            if caben is None:
                return None
            por_tipo[_firma(j)] = caben
    valores: dict[int, float] = {}

    def valor(mascara: int) -> float:
        if mascara not in valores:
            valores[mascara] = valor_del_conjunto([c for k, c in enumerate(cands) if mascara >> k & 1])
        return valores[mascara]

    opciones = [sorted(por_tipo[_firma(j)], key=lambda m: (-valor(m), m)) for j in jornadas]
    n = len(jornadas)
    alcanzable = [0] * (n + 1)  # todas las paradas que todavía podrían entrar, desde cada jornada
    for d in range(n - 1, -1, -1):
        for m in opciones[d]:
            alcanzable[d] |= m
        alcanzable[d] |= alcanzable[d + 1]
    mejor_valor, mejores = piso - TOLERANCIA, None
    elegidas = [0] * n
    pasos = 0

    def cota(d: int, usadas: int) -> float:
        """Lo que pueden sumar las jornadas desde d: cada una, su mejor conjunto sin repetir paradas."""
        suma = 0.0
        for e in range(d, n):
            suma += next(valor(m) for m in opciones[e] if not m & usadas)
        return suma

    def ramificar(d: int, usadas: int, desde: int) -> bool:
        nonlocal mejor_valor, mejores, pasos
        pasos += 1
        if pasos % 2048 == 0 and time.monotonic() > hasta:
            return False
        actual = valor(usadas)
        if d == n:
            if actual > mejor_valor + TOLERANCIA / 10:
                mejor_valor, mejores = actual, list(elegidas)
            return True
        if min(actual + cota(d, usadas), valor(usadas | alcanzable[d])) <= mejor_valor + TOLERANCIA / 10:
            return True
        igual_a_la_siguiente = d + 1 < n and _firma(jornadas[d + 1]) == _firma(jornadas[d])
        for pos in range(desde, len(opciones[d])):
            m = opciones[d][pos]
            if m & usadas:
                continue
            elegidas[d] = m
            if not ramificar(d + 1, usadas | m, pos if igual_a_la_siguiente else 0):
                return False
        elegidas[d] = 0
        return True

    if not ramificar(0, 0, 0) or mejores is None:
        return None
    recorridos = [por_tipo[_firma(j)][m] for j, m in zip(jornadas, mejores, strict=True)]
    return Optimo(
        mejor_valor, recorridos, desigualdad, sum(len(c) for c in por_tipo.values()), time.monotonic() - inicio
    )


# ─────────────────────────────── los viajes de las 40 consultas ───────────────────────────────


@dataclass(frozen=True)
class Instancia:
    consulta: int
    polo: int
    zona: str
    candidatas: list[Candidata]
    jornadas: list[Jornada]
    tiempos: Tiempos
    nombres: dict[int, str]  # Candidata.i → nombre del lugar


def instancias(datos: Datos, n: int) -> Iterator[Instancia]:
    """Los viajes que propone el motor para las 40 consultas, cada uno con sus ``n`` mejores candidatas."""
    for anotada in consultas.leer():
        c = anotada.consulta
        origen = datos.origenes[c.origen]
        de_origen = aclimatacion.del_origen(origen, datos)
        for ruta in viaje.resolver(c, datos, sugerir=False).rutas:
            polo = datos.polos[ruta.polo.id]
            p = viaje.preparar(polo, c, origen, datos, de_origen)
            desde = p.tiempos.m[p.tiempos.deposito, : p.tiempos.deposito]
            cands = viaje._mejores(p.candidatas, desde, n)
            nombres = {x.i: datos.recursos[polo.paradas[x.i]]["nombre"] for x in cands}
            yield Instancia(anotada.id, polo.id, polo.nombre, cands, list(p.plan.jornadas), p.tiempos, nombres)


def medir(inst: Instancia, plazo: float = PLAZO_S) -> dict:
    """La heurística y el óptimo sobre la misma instancia. El estado es ``visita_todas`` (la heurística
    visita todas las candidatas: ningún plan junta más, porque el valor no baja al sumar paradas),
    ``heuristica_optima``, ``mejorable`` o ``sin_resolver``."""
    plan = mejor_plan(inst.candidatas, inst.jornadas, inst.tiempos)
    de_la_heuristica = [v.candidata for r in plan for v in r.visitas]
    valor_h = valor_del_conjunto(de_la_heuristica)
    del_optimo, valor_o, segundos = de_la_heuristica, valor_h, 0.0
    if len(de_la_heuristica) == len(inst.candidatas):
        estado = "visita_todas"
    else:
        opt = exacto(inst.candidatas, inst.jornadas, inst.tiempos, piso=valor_h, plazo=plazo)
        if opt is None:
            estado, del_optimo, valor_o, segundos = "sin_resolver", None, None, plazo
        else:
            del_optimo = [inst.candidatas[k] for r in opt.recorridos for k in r]
            valor_o, segundos = opt.valor, opt.segundos
            estado = "heuristica_optima" if valor_o - valor_h <= TOLERANCIA else "mejorable"
    resuelta = del_optimo is not None
    brecha = max(valor_o - valor_h, 0.0) / valor_o if resuelta and valor_o > 0 else 0.0
    h = {c.i for c in de_la_heuristica}
    o = {c.i for c in del_optimo} if resuelta else h
    return {
        "consulta": inst.consulta,
        "polo": inst.polo,
        "zona": inst.zona,
        "jornadas": len(inst.jornadas),
        "candidatas": len(inst.candidatas),
        "paradas_heuristica": len(de_la_heuristica),
        "paradas_optimo": len(del_optimo) if resuelta else "",
        "valor_heuristica": round(valor_h, 4),
        "valor_optimo": round(valor_o, 4) if resuelta else "",
        "brecha": round(brecha, 6) if resuelta else "",
        "estado": estado,
        "segundos": round(segundos, 2),
        "solo_heuristica": " | ".join(sorted(inst.nombres[i] for i in h - o)),
        "solo_optimo": " | ".join(sorted(inst.nombres[i] for i in o - h)),
    }


def resumir(filas: list[dict]) -> dict:
    """Las cifras de un tamaño de instancia."""
    estados = [f["estado"] for f in filas]
    resueltas = [f for f in filas if f["estado"] != "sin_resolver"]
    con_que_elegir = [f for f in resueltas if f["estado"] != "visita_todas"]
    brechas = sorted(f["brecha"] for f in con_que_elegir)
    tiempos = sorted(f["segundos"] for f in con_que_elegir)
    valor_h = sum(f["valor_heuristica"] for f in resueltas)
    valor_o = sum(f["valor_optimo"] for f in resueltas)

    def cuantil(xs: list[float], q: float) -> float | None:
        return xs[min(len(xs) - 1, int(math.ceil(q * len(xs))) - 1)] if xs else None

    return {
        "viajes": len(filas),
        "visita_todas": estados.count("visita_todas"),
        "con_que_elegir": len(con_que_elegir),
        "heuristica_optima": estados.count("heuristica_optima"),
        "mejorables": estados.count("mejorable"),
        "sin_resolver": estados.count("sin_resolver"),
        "brecha_con_que_elegir": {
            "media": statistics.fmean(brechas) if brechas else None,
            "mediana": statistics.median(brechas) if brechas else None,
            "p90": cuantil(brechas, 0.9),
            "maxima": brechas[-1] if brechas else None,
        },
        "valor_que_junta_la_heuristica": valor_h / valor_o if valor_o else None,
        "segundos": {"mediana": statistics.median(tiempos) if tiempos else None, "maximo": max(tiempos, default=None)},
    }


def _escribir(ruta: Path, filas: list[dict]) -> None:
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]), delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)


def main() -> None:
    ap = argparse.ArgumentParser(description="La brecha del itinerario contra el óptimo exacto.")
    ap.add_argument("--candidatas", type=int, nargs="+", default=list(TAMANOS))
    ap.add_argument("--plazo", type=float, default=PLAZO_S, help="segundos por búsqueda exacta")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    datos = artefactos.cargar()
    filas, resumen = [], {"version_datos": datos.version, "plazo_s": a.plazo, "por_tamano": {}}
    for n in a.candidatas:
        del_tamano = [{"tamano": n, **medir(inst, a.plazo)} for inst in instancias(datos, n)]
        filas += del_tamano
        r = resumen["por_tamano"][str(n)] = resumir(del_tamano)
        b = r["brecha_con_que_elegir"]
        texto = f"media {b['media']:.2%}, máxima {b['maxima']:.2%}" if b["media"] is not None else "sin casos"
        print(
            f"{n} candidatas: {r['viajes']} viajes, {r['visita_todas']} visitan todas; de los {r['con_que_elegir']}"
            f" con qué elegir, la heurística da el óptimo en {r['heuristica_optima']} ({texto});"
            f" {r['sin_resolver']} sin resolver."
        )
    a.salida.mkdir(parents=True, exist_ok=True)
    _escribir(a.salida / "optimo.csv", filas)
    (a.salida / "optimo.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

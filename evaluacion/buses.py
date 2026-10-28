"""
Los tiempos por tierra del motor contra lo que publica una empresa de buses (semana 12). Lo dejó pendiente
el informe de la semana 10, que dice entre sus límites que el bus de noche no conoce los horarios de los buses.

El motor calcula la ida por carretera sobre una red propia de OpenStreetMap (decisión 0007), calibrada con
1 780 recorridos de las fichas de MINCETUR (decisión 0008). Esos recorridos son cortos, de un pueblo a sus
lugares. Aquí se miden los largos contra un bus de verdad.

``buses.csv`` trae las 29 rutas de Cruz del Sur que unen un origen del motor con la base de una zona, de las 42
de su página de pasajes, con lo que dice la página de cada ruta, consultada el 26 de octubre de 2026: entre
cuántos minutos y cuántos toma el viaje, de su servicio más rápido al más lento, y sus kilómetros. Chimbote va
con Nuevo Chimbote, la base vecina. Son tiempos de terminal a terminal, con las paradas del bus; el motor mide
de centro a centro por el camino más rápido. Una ruta cae **dentro** si el tiempo del motor está en el rango de
la empresa, **debajo** si es más rápido que su bus más rápido, y **encima** si es más lento que el más lento.

Para las rutas de 7 a 16 horas, las que el motor hace en bus de noche, se calcula también a qué hora se
llegaría: el motor fija la salida para llegar a eso de las 6:00 (``viaje.bus_de_noche``), y con los tiempos de
la empresa, saliendo a esa hora, se llega entre el bus más rápido y el más lento. El atraso es cuánto después
de la hora que da la app llegan esos dos buses.

Escribe en data/evaluacion/resultados/:

  buses.csv    cada ruta: el tiempo y los kilómetros del motor y de la empresa, dónde cae y, si va de noche,
               a qué hora llega según el motor y según la empresa
  buses.json   el resumen: cuántas caen dentro, debajo y encima, la razón entre el motor y la mitad del rango de
               la empresa, lo mismo con los kilómetros, y en cuántas de noche el bus llega más tarde que la app

Uso:  python -m evaluacion.buses
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from dataclasses import dataclass
from pathlib import Path

from dreemgo.motor import datos as artefactos
from dreemgo.motor import viaje
from dreemgo.motor.datos import Datos

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO = Path(__file__).with_name("buses.csv")
SALIDA = RAIZ / "data" / "evaluacion" / "resultados"
ATRASO_QUE_PESA = 60  # minutos: con una hora más, el primer día ya no empieza como dice el plan


@dataclass(frozen=True)
class Ruta:
    origen: str
    destino: str
    origen_motor: str
    polo: int
    empresa_min: int
    empresa_max: int
    empresa_km: int
    fuente: str


def leer(ruta: Path = ARCHIVO) -> list[Ruta]:
    with open(ruta, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    return [
        Ruta(
            f["origen"],
            f["destino"],
            f["origen_motor"],
            int(f["polo"]),
            int(f["empresa_min"]),
            int(f["empresa_max"]),
            int(f["empresa_km"]),
            f["fuente"],
        )
        for f in filas
    ]


def donde(minutos: float, desde: int, hasta: int) -> str:
    """«dentro», «debajo» (más rápido que el bus más rápido) o «encima» (más lento que el más lento)."""
    return "debajo" if minutos < desde else "encima" if minutos > hasta else "dentro"


def _hora(minuto: int) -> str:
    m = minuto % (24 * 60)
    return f"{m // 60:02d}:{m % 60:02d}"


def comparar(r: Ruta, datos: Datos) -> dict:
    minutos, km = datos.origenes[r.origen_motor].a_base.get(r.polo, (math.nan, math.nan))
    if not math.isfinite(minutos):
        raise ValueError(f"{r.origen} → {r.destino}: el motor no tiene camino de {r.origen_motor} a la zona {r.polo}")
    mitad = (r.empresa_min + r.empresa_max) / 2
    fila = {
        "origen": r.origen,
        "destino": r.destino,
        "zona": datos.polos[r.polo].nombre,
        "motor_min": round(minutos),
        "empresa_min": r.empresa_min,
        "empresa_max": r.empresa_max,
        "donde": donde(minutos, r.empresa_min, r.empresa_max),
        "razon": round(minutos / mitad, 3),
        "motor_km": round(km),
        "empresa_km": r.empresa_km,
        "razon_km": round(km / r.empresa_km, 3),
        "de_noche": "",
        "sale": "",
        "llega_motor": "",
        "llega_bus": "",
        "atraso_min": "",
        "atraso_max": "",
        "fuente": r.fuente,
    }
    if viaje.NOCHE_MIN <= minutos <= viaje.LEJOS_PARA_VOLAR_MIN:
        sale, llega = viaje.bus_de_noche(minutos)
        viaje_motor = math.ceil(minutos)  # como lo cuenta bus_de_noche
        fila |= {
            "de_noche": "sí",
            "sale": _hora(sale),
            "llega_motor": _hora(llega),
            "llega_bus": f"{_hora(sale + r.empresa_min)} a {_hora(sale + r.empresa_max)}",
            "atraso_min": r.empresa_min - viaje_motor,
            "atraso_max": r.empresa_max - viaje_motor,
        }
    return fila


def resumir(filas: list[dict]) -> dict:
    de_noche = [f for f in filas if f["de_noche"]]
    return {
        "rutas": len(filas),
        **{d: sum(1 for f in filas if f["donde"] == d) for d in ("dentro", "debajo", "encima")},
        "razon_mediana": statistics.median(f["razon"] for f in filas),
        "razon_km_mediana": statistics.median(f["razon_km"] for f in filas),
        "de_noche": len(de_noche),
        "de_noche_el_mas_lento_llega_una_hora_despues": sum(1 for f in de_noche if f["atraso_max"] > ATRASO_QUE_PESA),
        "de_noche_ni_el_mas_rapido_llega_a_la_hora": sum(1 for f in de_noche if f["atraso_min"] > 0),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Los tiempos por tierra del motor contra los de una empresa de buses.")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    datos = artefactos.cargar()
    filas = [comparar(r, datos) for r in leer()]
    resumen = {"version_datos": datos.version, **resumir(filas)}
    a.salida.mkdir(parents=True, exist_ok=True)
    with open(a.salida / "buses.csv", "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]), delimiter=";", lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    texto = json.dumps(resumen, ensure_ascii=False, indent=2) + "\n"
    (a.salida / "buses.json").write_text(texto, encoding="utf-8")
    print(
        f"{resumen['rutas']} rutas: {resumen['dentro']} dentro del rango de la empresa, {resumen['debajo']} más"
        f" rápidas que su bus más rápido y {resumen['encima']} más lentas que el más lento; razón mediana"
        f" {resumen['razon_mediana']:.2f}. De las {resumen['de_noche']} de noche, en"
        f" {resumen['de_noche_el_mas_lento_llega_una_hora_despues']} el bus más lento llega más de una hora después"
        f" de lo que dice la app, y en {resumen['de_noche_ni_el_mas_rapido_llega_a_la_hora']} ni el más rápido"
        " llega a esa hora."
    )


if __name__ == "__main__":
    main()

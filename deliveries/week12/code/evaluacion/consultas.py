"""
Las 40 consultas cuyos viajes califica el equipo (semana 12, decisión 0021). Cada una es una persona con
un viaje en mente: de dónde sale, cuántos días tiene, cuándo, qué le gusta y, si lo dijo, cuánto puede
gastar o hasta qué altura puede subir. Están escritas a mano en ``consultas.csv`` para cubrir lo que el
producto promete:

- 15 orígenes, y 16 de las 40 consultas desde Lima, que es de donde sale la mayoría de los viajes;
- de 2 a 10 días, y 34 de las 40 de dos a cinco: sobre todo fines de semana, largos o no;
- los doce meses, con la temporada de lluvias de la sierra y el verano de la costa;
- cada interés al menos dos veces, y cinco consultas sin ninguno;
- presupuesto, altitud máxima, «Solo por tierra», «Sorpréndeme» y dos con fecha: Semana Santa y el
  Inti Raymi de 2027.

Es un conjunto chico, hecho a mano, y se declara como tal: sirve para comparar el motor con una línea de
base sobre las mismas consultas, no para estimar cómo le va con cualquier consulta.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dreemgo.contrato import Consulta

ARCHIVO = Path(__file__).with_name("consultas.csv")


@dataclass(frozen=True)
class ConsultaAnotada:
    id: int
    perfil: str
    consulta: Consulta


def _entero(texto: str) -> int | None:
    return int(texto) if texto.strip() else None


def leer(ruta: Path = ARCHIVO) -> list[ConsultaAnotada]:
    """Las consultas del archivo, en su orden, ya validadas por el contrato."""
    with open(ruta, encoding="utf-8", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    salida = []
    for f in filas:
        consulta = Consulta(
            origen=f["origen"],
            mes=_entero(f["mes"]),
            fecha_inicio=date.fromisoformat(f["fecha_inicio"]) if f["fecha_inicio"].strip() else None,
            dias=int(f["dias"]),
            intereses=[i for i in f["intereses"].split("|") if i],
            presupuesto=_entero(f["presupuesto"]),
            altitud_max=_entero(f["altitud_max"]),
            solo_por_tierra=f["solo_por_tierra"].strip() == "true",
            sorpresa=f["sorpresa"].strip() == "true",
        )
        salida.append(ConsultaAnotada(int(f["id"]), f["perfil"], consulta))
    return salida

"""
El kit corto para calificadores de fuera del equipo (punto 12 de la auditoría, decisión 0033).

Quienes calificaron el kit de la semana 12 hicieron el producto. Para medir ese sesgo, personas de fuera
califican una parte de los mismos viajes, con el mismo cuadernillo: 10 de las 40 consultas, elegidas al azar
con una semilla fija, de modo que sus notas se comparan con las del equipo viaje por viaje
(``evaluacion/externos.py``).

Lee data/evaluacion/cuadernillo.html, deja solo esas consultas, cambia la guía para alguien de fuera y la
clave del navegador, y escribe:

  data/evaluacion/externos/cuadernillo_externo.html

Lo mismo con el mismo cuadernillo da siempre el mismo archivo.

Uso:  python -m evaluacion.kit_externo
"""

from __future__ import annotations

import argparse
import random
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CUADERNILLO = RAIZ / "data" / "evaluacion" / "cuadernillo.html"
SALIDA = RAIZ / "data" / "evaluacion" / "externos"
SEMILLA = "calificadores de fuera"
CONSULTAS = 10

GUIA = (
    "<p>Gracias por ayudarnos. Somos un equipo de UTEC que arma viajes por el Perú. Abajo hay {n} personas con un "
    "viaje en mente y, para cada una, de 3 a 7 viajes posibles: {viajes} en total, unos 20 minutos. Lee quién viaja y "
    "lo que pidió, y califica cada viaje por separado, pensando en esa persona: <b>2</b> si se lo recomendarías tal "
    "cual, <b>1</b> si podría servirle pero con reparos, <b>0</b> si no encaja. No hay respuestas correctas: nos "
    "importa tu opinión.</p>\n<p>Califica por tu cuenta, sin buscar los lugares en internet. El avance se guarda en "
    "este navegador. Cuando termines, pon tus iniciales, descarga tus calificaciones y mándanos el archivo.</p>"
)


def elegidas(total: int = 40, cuantas: int = CONSULTAS) -> list[int]:
    """Las consultas del kit corto: al azar, con una semilla fija, en orden."""
    return sorted(random.Random(SEMILLA).sample(range(1, total + 1), cuantas))


def recortar(html: str, consultas: list[int]) -> str:
    """El cuadernillo con solo esas consultas, la guía para alguien de fuera y su propia clave en el navegador."""
    secciones = re.findall(r"<section class='consulta' id='c(\d+)'>.*?</section>\n?", html, flags=re.S)
    if len(secciones) != 40:
        raise ValueError(f"el cuadernillo tiene {len(secciones)} consultas, no 40")
    quedan = set(consultas)

    def quitar(m: re.Match) -> str:
        return m.group(0) if int(m.group(1)) in quedan else ""

    salida = re.sub(r"<section class='consulta' id='c(\d+)'>.*?</section>\n?", quitar, html, flags=re.S)
    viajes = len(re.findall(r"<fieldset[^>]*data-opcion", salida))
    salida = re.sub(
        r"<div class='guia'>\n<p>.*?</p>\n<p>.*?</p>\n",
        lambda _: "<div class='guia'>\n" + GUIA.format(n=len(consultas), viajes=viajes) + "\n",
        salida,
        count=1,
        flags=re.S,
    )
    salida = re.sub(r">0 de \d+ calificados<", f">0 de {viajes} calificados<", salida, count=1)
    salida = salida.replace('"dreemgo-calificaciones-" + kit.huella', '"dreemgo-externos-" + kit.huella', 1)
    salida = salida.replace('"calificaciones_" + quien() + ".csv"', '"externo_" + quien() + ".csv"', 1)
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description="El kit corto para calificadores de fuera del equipo.")
    ap.add_argument("--cuadernillo", type=Path, default=CUADERNILLO)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    consultas = elegidas()
    html = recortar(a.cuadernillo.read_text(encoding="utf-8"), consultas)
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "cuadernillo_externo.html").write_text(html, encoding="utf-8")
    viajes = len(re.findall(r"<fieldset[^>]*data-opcion", html))
    print(f"kit corto: consultas {', '.join(map(str, consultas))} · {viajes} viajes · {a.salida}")


if __name__ == "__main__":
    main()

"""
Las cifras de la prueba de usabilidad de la semana 12 (decisión 0021, ``docs/evaluacion/usabilidad.md``).

Lee lo que se anotó en data/evaluacion/usabilidad/, con un código por persona y sin datos de nadie:

  participantes.csv   el dispositivo, la fecha y cuántos viajes hace por el Perú al año
  tareas.csv          por persona y tarea: si la logró sola, con ayuda o no, en cuántos segundos y con
                      cuántos caminos equivocados
  sus.csv             las diez respuestas del SUS, del 1 al 5
  comentarios.csv     lo más útil y lo que cambiaría primero

y escribe en data/evaluacion/resultados/usabilidad.json el SUS de cada persona, su media, su mediana y su
rango; cada tarea con cuántas la lograron solas, con ayuda o no, y el tiempo de quienes la lograron; y los
comentarios, tal cual. Una fila sin llenar no cuenta: si todavía no se probó con nadie, lo dice.

El SUS es el de John Brooke (1996): a cada frase impar se le resta 1 a la respuesta y cada par se le resta a
5; la suma por 2,5 queda de 0 a 100. Para leerlo, 68 es la media de cientos de estudios (Sauro, 2011), y la
escala de adjetivos de Bangor, Kortum y Miller (2009, *Journal of Usability Studies* 4(3), tabla 3) da la
media de los puntajes que la gente describió con cada palabra. Con cinco personas el margen es grande: el
puntaje orienta, y lo que más sirve son los tropiezos de cada tarea.

Uso:  python -m evaluacion.usabilidad
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "data" / "evaluacion" / "usabilidad"
SALIDA = RAIZ / "data" / "evaluacion" / "resultados"
FRASES = [f"p{k}" for k in range(1, 11)]
RESULTADOS = ("sola", "con_ayuda", "no")
DISPOSITIVOS = ("celular", "computadora")
MEDIA_DE_REFERENCIA = 68  # Sauro (2011), sobre cientos de estudios
# Bangor, Kortum y Miller (2009), tabla 3: la media del SUS de quienes eligieron cada adjetivo.
ADJETIVOS = (
    ("Lo peor imaginable", 12.5),
    ("Horrible", 20.3),
    ("Mala", 35.7),
    ("Aceptable", 50.9),
    ("Buena", 71.4),
    ("Excelente", 85.5),
    ("Lo mejor imaginable", 90.9),
)


def _filas(ruta: Path) -> list[dict[str, str]]:
    """Las filas de una planilla, sin las que quedaron sin llenar (solo el código, o el código y la tarea)."""
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        filas = list(csv.DictReader(fh, delimiter=";"))
    claves = {"participante", "tarea"}
    return [
        {k: (v or "").strip() for k, v in f.items()}
        for f in filas
        if any((v or "").strip() for k, v in f.items() if k not in claves)
    ]


def puntaje_sus(respuestas: list[int]) -> float:
    """El SUS de una persona, de 0 a 100."""
    if len(respuestas) != 10 or any(r not in (1, 2, 3, 4, 5) for r in respuestas):
        raise ValueError(f"el SUS pide diez respuestas del 1 al 5, y llegaron {respuestas}")
    impares = sum(r - 1 for r in respuestas[0::2])
    pares = sum(5 - r for r in respuestas[1::2])
    return (impares + pares) * 2.5


def adjetivo(puntaje: float) -> str:
    """El adjetivo de Bangor y colegas cuya media queda más cerca del puntaje."""
    return min(ADJETIVOS, key=lambda a: (abs(a[1] - puntaje), a[1]))[0]


def _entero(texto: str, que: str) -> int:
    try:
        return int(texto)
    except ValueError:
        raise ValueError(f"{que}: «{texto}» no es un número entero") from None


def calcular(carpeta: Path = CARPETA) -> dict:
    participantes = {f["participante"]: f for f in _filas(carpeta / "participantes.csv")}
    for codigo, f in participantes.items():
        if f["dispositivo"] not in DISPOSITIVOS:
            raise ValueError(f"{codigo}: el dispositivo es «celular» o «computadora», no «{f['dispositivo']}»")

    sus = {}
    for f in _filas(carpeta / "sus.csv"):
        respuestas = [_entero(f[p], f"{f['participante']}, {p}") for p in FRASES if f[p]]
        sus[f["participante"]] = puntaje_sus(respuestas)

    tareas: dict[str, dict] = {}
    for f in _filas(carpeta / "tareas.csv"):
        quien = f"{f['participante']}, {f['tarea']}"
        if f["resultado"] not in RESULTADOS:
            raise ValueError(f"{quien}: el resultado es «sola», «con_ayuda» o «no», no «{f['resultado']}»")
        t = tareas.setdefault(f["tarea"], {r: 0 for r in RESULTADOS} | {"segundos": [], "errores": []})
        t[f["resultado"]] += 1
        if f["resultado"] != "no" and f["segundos"]:
            t["segundos"].append(_entero(f["segundos"], f"{quien}, segundos"))
        if f["errores"]:
            t["errores"].append(_entero(f["errores"], f"{quien}, errores"))

    puntajes = list(sus.values())
    resumen_sus = None
    if puntajes:
        media = statistics.fmean(puntajes)
        resumen_sus = {
            "personas": len(puntajes),
            "media": media,
            "mediana": statistics.median(puntajes),
            "minimo": min(puntajes),
            "maximo": max(puntajes),
            "adjetivo_de_la_media": adjetivo(media),
            "sobre_la_media_de_referencia": sum(1 for p in puntajes if p > MEDIA_DE_REFERENCIA),
        }
    por_tarea = {}
    for nombre, t in sorted(tareas.items()):
        intentos = sum(t[r] for r in RESULTADOS)
        por_tarea[nombre] = {
            "intentos": intentos,
            **{r: t[r] for r in RESULTADOS},
            "logradas": (t["sola"] + t["con_ayuda"]) / intentos,
            "segundos_mediana": statistics.median(t["segundos"]) if t["segundos"] else None,
            "errores_media": statistics.fmean(t["errores"]) if t["errores"] else None,
        }
    dispositivos = {d: sum(1 for f in participantes.values() if f["dispositivo"] == d) for d in DISPOSITIVOS}
    return {
        "participantes": len(participantes),
        "dispositivos": dispositivos,
        "sus_por_persona": dict(sorted(sus.items())),
        "sus": resumen_sus,
        "media_de_referencia": MEDIA_DE_REFERENCIA,
        "adjetivos": dict(ADJETIVOS),
        "tareas": por_tarea,
        "comentarios": _filas(carpeta / "comentarios.csv"),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Las cifras de la prueba de usabilidad de la semana 12.")
    ap.add_argument("--carpeta", type=Path, default=CARPETA)
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    resumen = calcular(a.carpeta)
    a.salida.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(resumen, ensure_ascii=False, indent=2) + "\n"
    (a.salida / "usabilidad.json").write_text(texto, encoding="utf-8")
    if resumen["sus"] is None:
        print("Todavía no hay respuestas del SUS en", a.carpeta)
        return
    s = resumen["sus"]
    print(
        f"{s['personas']} personas: SUS {s['media']:.1f} de media ({s['minimo']:.1f} a {s['maximo']:.1f}),"
        f" «{s['adjetivo_de_la_media']}»; {s['sobre_la_media_de_referencia']} sobre {MEDIA_DE_REFERENCIA}."
    )
    for nombre, t in resumen["tareas"].items():
        print(f"  {nombre}: {t['sola']} sola, {t['con_ayuda']} con ayuda, {t['no']} no")


if __name__ == "__main__":
    main()

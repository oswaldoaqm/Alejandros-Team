"""Actualiza la instantánea incrustada en el tablero independiente de DreemGO."""

from __future__ import annotations

import json
import re
from pathlib import Path

from dreemgo.analitica import leer_simulacion, resumir

RAIZ = Path(__file__).resolve().parents[1]
TABLERO = RAIZ / "app" / "public" / "tablero-gerencial.html"
MARCADOR = re.compile(r'(<script id="datos-iniciales" type="application/json">).*?(</script>)', re.DOTALL)


def exportar(ruta: Path = TABLERO) -> None:
    meta, eventos = leer_simulacion()
    resumen = resumir(eventos, modo="simulacion", fuente=f"SIMULACIÓN: {meta['sesiones']} sesiones ficticias.")
    # Escapar < impide que un texto de los datos cierre la etiqueta script.
    contenido = json.dumps(resumen.model_dump(mode="json"), ensure_ascii=False, separators=(",", ":"))
    contenido = contenido.replace("<", "\\u003c").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    original = ruta.read_text(encoding="utf-8")
    if len(MARCADOR.findall(original)) != 1:
        raise ValueError("El tablero debe contener un único bloque datos-iniciales.")
    actualizado = MARCADOR.sub(lambda m: m.group(1) + contenido + m.group(2), original)
    ruta.write_text(actualizado, encoding="utf-8")
    print(f"Tablero independiente actualizado: {ruta}")


if __name__ == "__main__":
    exportar()

"""
Prepara una ficha descargada para usarla como caso de prueba.

Vacía las secciones que el pipeline no lee porque traen datos de personas ("Datos del
Responsable", "Saneamiento Físico Legal") y reemplaza teléfonos y correos en el resto
del texto. El resultado sigue siendo una ficha que pipeline.fichas lee igual que la
original.

    python -m tests.fixtures.fichas.sanear data/externos/fichas_html/1237.html.gz tests/fixtures/fichas/
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import lxml.html

from pipeline.fichas import SECCIONES_OMITIDAS
from pipeline.texto import normalizar, sin_contactos

VACIADAS = {"Datos del Responsable", "Saneamiento Físico Legal"}
assert VACIADAS <= set(SECCIONES_OMITIDAS)


def sanear(html: bytes) -> bytes:
    doc = lxml.html.fromstring(html, parser=lxml.html.HTMLParser(encoding="utf-8"))
    for h3 in doc.xpath('//div[@id="accordionContent"]/h3'):
        if normalizar(h3.text_content()) in VACIADAS:
            contenido = h3.getnext()
            for hijo in list(contenido):
                contenido.remove(hijo)
            contenido.text = "Omitido en la copia de prueba."
    for elemento in doc.iter():
        if isinstance(elemento.tag, str):
            if elemento.text:
                elemento.text = sin_contactos(elemento.text)
            if elemento.tail:
                elemento.tail = sin_contactos(elemento.tail)
    return lxml.html.tostring(doc, encoding="utf-8", doctype="<!DOCTYPE html>")


if __name__ == "__main__":
    destino = Path(sys.argv[-1])
    for origen in map(Path, sys.argv[1:-1]):
        with gzip.open(origen, "rb") as f:
            limpio = sanear(f.read())
        with (
            open(destino / origen.name, "wb") as crudo,
            gzip.GzipFile(fileobj=crudo, mode="wb", filename="", mtime=0) as f,
        ):
            f.write(limpio)  # sin fecha ni nombre en la cabecera: el mismo HTML da el mismo archivo
        print(f"{origen.name}: {len(limpio):,} bytes")

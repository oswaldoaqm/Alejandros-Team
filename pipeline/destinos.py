"""
Las zonas a las que se puede pedir un viaje («Quiero ir a…»), con lo que la app necesita para
buscarlas: su nombre, sus regiones y los lugares que se visitan en ellas.

La app busca en el navegador, sin pedirle nada al API, así que la lista va con la app, como
las fotos: sirve aunque el API todavía esté despertando. Sale de los artefactos del motor
(``dreemgo/datos``) y lleva su versión de datos.

- **Qué zonas.** Las que tienen algún lugar que se visita en una jornada: con camino desde su
  base y una visita de 6 horas o menos, como las candidatas del motor. Las demás nunca darían
  un viaje: en Queropalca solo hay caminatas de más de un día.
- **Qué lugares.** Esos mismos, de mayor a menor jerarquía. Si dos se llaman igual, va uno.
- **El peso.** Lo que valen sus doce lugares más importantes, con la escala del motor (1, 2, 6
  o 24 según la jerarquía, y 2 si no la tiene): lo que se alcanza a ver en un viaje de unos
  días. Ordena la lista, y la app propone las primeras. Sumar todos los lugares ponía a un
  pueblo con cincuenta lugares corrientes antes que Machu Picchu.
- **La misma ciudad.** Los orígenes a menos de media hora de la base: desde ahí el motor no
  arma un viaje con noches a esa zona, así que la app no la propone.

Uso:     python -m pipeline.destinos        (después de pipeline/artefactos.py)
Salida:  app/public/destinos.json
"""

from __future__ import annotations

import argparse
import json
import unicodedata
from pathlib import Path

import numpy as np

from dreemgo.motor import datos as artefactos
from dreemgo.motor.datos import Datos, Polo
from dreemgo.motor.viaje import CASA_MIN, VISITA_MAX_MIN, minutos_de_visita, valor

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "app" / "public" / "destinos.json"
LUGARES_DEL_PESO = 12


def _plegado(texto: str) -> str:
    """Para ordenar sin que pesen las tildes ni las mayúsculas."""
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)).casefold()


def lugares_de_un_dia(polo: Polo, datos: Datos) -> list[dict]:
    """Los lugares de la zona que se visitan en una jornada desde su base."""
    return [
        datos.recursos[codigo]
        for i, codigo in enumerate(polo.paradas)
        if np.isfinite(polo.base_minutos[i]) and minutos_de_visita(datos.recursos[codigo]) <= VISITA_MAX_MIN
    ]


def zona(polo: Polo, datos: Datos) -> dict | None:
    """La zona como la busca la app, o None si no tiene nada que se visite en una jornada."""
    lugares = lugares_de_un_dia(polo, datos)
    if not lugares:
        return None
    jerarquias: dict[str, int | None] = {}
    for r in lugares:
        if (r["jerarquia"] or 0) >= (jerarquias.get(r["nombre"]) or 0):
            jerarquias[r["nombre"]] = r["jerarquia"]
    orden = sorted(jerarquias.items(), key=lambda x: (-(x[1] or 0), _plegado(x[0]), x[0]))
    return {
        "id": polo.id,
        "nombre": polo.nombre,
        "region": polo.region,
        "regiones": list(polo.regiones),
        "peso": round(sum(sorted((valor(r, set()) for r in lugares), reverse=True)[:LUGARES_DEL_PESO]), 1),
        "misma_ciudad": sorted(o.id for o in datos.origenes.values() if o.a_base.get(polo.id, (np.inf,))[0] < CASA_MIN),
        "lugares": [[nombre, jerarquia] for nombre, jerarquia in orden],
    }


def destinos(datos: Datos) -> dict:
    """Las zonas, de más a menos peso."""
    zonas = [z for polo in datos.polos.values() if (z := zona(polo, datos)) is not None]
    zonas.sort(key=lambda z: (-z["peso"], z["id"]))
    return {"version_datos": datos.version, "zonas": zonas}


def main() -> None:
    argparse.ArgumentParser(description=__doc__.split("\n\n")[0]).parse_args()
    lista = destinos(artefactos.cargar())
    SALIDA.write_text(json.dumps(lista, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    lugares = sum(len(z["lugares"]) for z in lista["zonas"])
    print(f"{SALIDA.relative_to(RAIZ)}: {len(lista['zonas'])} zonas y {lugares} lugares ({lista['version_datos']})")


if __name__ == "__main__":
    main()

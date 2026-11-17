"""Mide por qué las islas del Titicaca no aparecen en un viaje a Puno.

Usa los mismos artefactos y el mismo motor de la aplicación. No cambia el
orden de las recomendaciones ni inventa frecuencias u horarios de botes.

    python -m evaluacion.islas_puno
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import numpy as np

from dreemgo.contrato import Consulta
from dreemgo.motor import viaje
from dreemgo.motor.datos import cargar

POLO_PUNO = 11
# Códigos del inventario de MINCETUR que ya están en los artefactos del polo.
ISLAS = ("958", "959", "960", "13550")


@dataclass(frozen=True)
class Caso:
    nombre: str
    consulta: Consulta


CASOS = (
    Caso("Puno sin intereses, cuatro días", Consulta(origen="lima", mes=7, dias=4, destino=POLO_PUNO)),
    Caso(
        "Puno con naturaleza, cuatro días",
        Consulta(origen="lima", mes=7, dias=4, destino=POLO_PUNO, intereses=["naturaleza"]),
    ),
    Caso(
        "Puno con caminatas y gastronomía, cinco días",
        Consulta(origen="lima", mes=7, dias=5, destino=POLO_PUNO, intereses=["caminatas", "gastronomia"]),
    ),
)


def evaluar() -> dict:
    datos = cargar()
    polo = datos.polos[POLO_PUNO]
    casos = []
    for caso in CASOS:
        # Es el mismo criterio que usa preparar() antes del planificador.
        desde = polo.base_minutos
        candidatas = viaje.candidatas(polo, caso.consulta, datos, desde)
        orden = sorted(candidatas, key=lambda c: (-c.valor / (c.visita + 2 * desde[c.i]), c.i))
        rangos = {polo.paradas[c.i]: posicion for posicion, c in enumerate(orden, 1)}
        respuesta = viaje.resolver(caso.consulta, datos)
        visitadas = {parada.recurso.codigo for ruta in respuesta.rutas for dia in ruta.dias for parada in dia.paradas}
        islas = []
        for codigo in ISLAS:
            if codigo not in datos.recursos or codigo not in polo.paradas:
                continue
            i = polo.paradas.index(codigo)
            minutos = desde[i]
            islas.append(
                {
                    "codigo_mincetur": codigo,
                    "nombre": datos.recursos[codigo]["nombre"],
                    "minutos_desde_puno": round(float(minutos), 1) if np.isfinite(minutos) else None,
                    "km_en_bote_desde_puno": round(float(polo.base_km_bote[i]), 1),
                    "puesto_en_preseleccion": rangos.get(codigo),
                    "entra_entre_40_candidatas": rangos.get(codigo, float("inf")) <= viaje.CANDIDATAS_MAX,
                    "aparece_en_el_itinerario": codigo in visitadas,
                }
            )
        casos.append({"caso": caso.nombre, "consulta": caso.consulta.model_dump(mode="json"), "islas": islas})
    return {
        "version_datos": datos.version,
        "fuente_de_lugares": "Inventario Nacional de Recursos Turísticos de MINCETUR",
        "alcance": "Diagnóstico del motor actual; no verifica horarios ni disponibilidad de botes",
        "casos": casos,
    }


if __name__ == "__main__":
    print(json.dumps(evaluar(), ensure_ascii=False, indent=2))

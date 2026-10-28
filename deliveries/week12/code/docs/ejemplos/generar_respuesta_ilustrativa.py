"""
Genera docs/ejemplos/respuesta_ilustrativa.json: una respuesta del motor, tal cual, para la
consulta de abajo con los artefactos de dreemgo/datos.

Sirve para construir y probar la app contra una respuesta real sin levantar el API. Las
pruebas la validan contra dreemgo.contrato.Respuesta, así que si el contrato cambia y el
ejemplo no, CI falla. Se regenera cada vez que cambian el motor o los datos.

Uso:  python docs/ejemplos/generar_respuesta_ilustrativa.py
"""

from __future__ import annotations

from pathlib import Path

from dreemgo.contrato import Consulta
from dreemgo.motor.datos import cargar
from dreemgo.motor.viaje import resolver

SALIDA = Path(__file__).with_name("respuesta_ilustrativa.json")
CONSULTA = Consulta(
    origen="lima", mes=7, dias=4, intereses=["historia", "naturaleza"], presupuesto=700, altitud_max=3500
)


def main() -> None:
    respuesta = resolver(CONSULTA, cargar())
    SALIDA.write_text(respuesta.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(f"{SALIDA.name}: {len(respuesta.rutas)} rutas con los datos {respuesta.version_datos}")


if __name__ == "__main__":
    main()

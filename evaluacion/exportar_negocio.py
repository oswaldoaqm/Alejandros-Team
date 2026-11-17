"""Incluye la simulación comercial en el tablero HTML para abrirla sin servidor."""

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATOS = RAIZ / "data/simulacion/negocio_300.json"
TABLERO = RAIZ / "app/public/tablero-negocio.html"
PATRON = re.compile(r'(<script id="datos-negocio" type="application/json">)(.*?)(</script>)', re.S)


def exportar() -> None:
    datos = json.loads(DATOS.read_text(encoding="utf-8"))
    if datos.get("meta", {}).get("tipo") != "simulacion_comercial" or len(datos.get("registros", [])) != 300:
        raise ValueError("Se esperaban 300 perfiles de la simulación comercial.")
    contenido = TABLERO.read_text(encoding="utf-8")
    if len(PATRON.findall(contenido)) != 1:
        raise ValueError("No se encontró un único bloque de datos en el tablero.")
    instantanea = json.dumps(datos, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    actualizado = PATRON.sub(lambda m: m.group(1) + instantanea + m.group(3), contenido)
    TABLERO.write_text(actualizado, encoding="utf-8")
    print(f"Tablero actualizado con {len(datos['registros'])} perfiles ficticios.")


if __name__ == "__main__":
    exportar()

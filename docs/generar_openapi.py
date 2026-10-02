"""
Genera docs/openapi.json: el esquema OpenAPI del API, tal como lo sirve /v1/openapi.json.

De ese archivo salen los tipos de la app (app/src/api/esquema.d.ts, con `npm run tipos`), así
que la app se puede construir sin levantar el API. Las pruebas comparan sus modelos y campos
con los del contrato: si el contrato cambia y este archivo no, CI falla.

Uso:  python docs/generar_openapi.py && (cd app && npm run tipos)
"""

from __future__ import annotations

import json
from pathlib import Path

from dreemgo.api.app import app

SALIDA = Path(__file__).with_name("openapi.json")


def main() -> None:
    esquema = app.openapi()
    SALIDA.write_text(json.dumps(esquema, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{SALIDA.name}: {len(esquema['paths'])} rutas y {len(esquema['components']['schemas'])} modelos")


if __name__ == "__main__":
    main()

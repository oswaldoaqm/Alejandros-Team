# Código que no se ejecuta

| Script | Por qué está aquí |
|---|---|
| `fix_pricing_native.py` | Versión sin pandas de `../fix_pricing.py`, con la misma regla de distancia. Quedó duplicada |
| `verify_enriched_native.py` | Versión sin pandas de la verificación. Revisa `NIVEL_PRECIO_PROXY`, una columna que `../fix_pricing.py` elimina, así que sobre el CSV entregado se detiene con error |

El pipeline vigente y su orden están en [`../../README.md`](../../README.md).

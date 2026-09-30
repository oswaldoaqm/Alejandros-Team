# Código que no se ejecuta

Scripts que quedan como registro del desarrollo. Ninguno forma parte del pipeline de [`../../README.md`](../../README.md), y algunos dañan los datos si se corren.

| Script | Por qué está aquí |
|---|---|
| `build_master_dataset.py` | Genera `JERARQUIA_OFICIAL` y `TIPO_INGRESO` con `random.choices()` y escribe sobre el dataset maestro. Correrlo destruye la extracción real |
| `clean_impute_dataset.py` | Reemplaza `TIPO_INGRESO` y `EPOCA_PROPICIA` por reglas deterministas y manda a `1` toda jerarquía no reconocida ([`../../DataAnalysis.md`](../../DataAnalysis.md) §3.1) |
| `scraper_mincetur.py` | Primera versión del extractor de fichas: buscaba etiquetas por cercanía de texto y escribía sobre el dataset maestro. La reemplaza `../scraper_mincetur_v3.py`, que reconoce cada tabla por su encabezado |
| `generate_commerce_data.py` | Genera los 500 eventos simulados de `comercios_ferias_locales.csv`, sin semilla: cada corrida da otros. Los eventos reales son los 749 acontecimientos del inventario |
| `create_notebook.py`, `build_advanced_eda.py` | Generaron la primera versión de los dos notebooks. Correrlos hoy los reescribiría con los títulos y las rutas que se corrigieron |

Cuatro de ellos tienen rutas absolutas a la máquina de un integrante. Se dejan así a propósito: no deben correr en ninguna otra.

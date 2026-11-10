# Erratas · Semana 5

Lo entregado el 9 de septiembre está intacto en la etiqueta [`entrega/semana-05`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-05). Esta carpeta se corrigió el 30 de septiembre, en su sitio.

## Correcciones

| Dónde | Qué decía o hacía | Qué dice o hace ahora | Por qué |
|---|---|---|---|
| `README.md`, data enriquecida | `ZONA_CLIMATICA` con 6 categorías | 7 categorías | El CSV tiene siete pisos ecológicos: Costa, Yunga, Quechua, Suni, Puna, Janca y Selva |
| `README.md`, reproducir | enrich → add_climate → fix_altitudes → fix_pricing → build_features → verify | enrich → fix_altitudes → build_features → add_climate → fix_pricing → verify | En el orden anterior `build_features.py` corría al final y reemplazaba el índice de lejanía por otra regla (15 y 60 km, más un nivel por categoría cultural). El CSV entregado sigue la regla de `fix_pricing.py`: 20 y 80 km |
| `code/*.py` | Rutas relativas a carpetas distintas: `add_climate.py` a la raíz del repositorio, el resto a `code/` | Rutas relativas al propio script | Los comandos del README fallaban desde `week05/` |
| `code/fix_pricing.py`, `code/build_features.py` | Buscaban la capital regional con el nombre de la región en mayúsculas y con tilde | Quitan la tilde antes de buscar | Junín, Áncash, Huánuco, Apurímac y San Martín no encontraban su capital y 1 202 recursos quedaban sin distancia. El CSV entregado sí la tiene, así que salió de una versión del código que no llegó al repositorio |
| `code/verify_enriched.py` | Verificaba `NIVEL_PRECIO_PROXY` | Verifica el índice de lejanía y la zona climática | Esa columna se descartó en la misma semana; sobre el CSV entregado el script se detenía con `KeyError` |
| `code/fix_pricing_native.py`, `code/verify_enriched_native.py` | Junto al código vivo | En `code/legacy/` | Son variantes sin pandas de dos scripts; la segunda también se detenía con error |

Con estos cambios, los tres pasos sin red (`build_features.py`, `add_climate.py` y `fix_pricing.py`) reproducen exactamente las columnas derivadas del CSV entregado en las 6 160 filas. Los dos pasos con red no se pudieron volver a correr desde el entorno de verificación.

## Documentos que se dejan como se entregaron

El Canvas, la propuesta, la presentación y `Requirements.md` son la versión inicial que pedía la semana 5, y los PDF no se editan. La especificación final se entrega en la Delivery 2. Lo que cambió desde entonces:

| Dónde | Qué decía | Qué se sabe ahora |
|---|---|---|
| Canvas §5 | Modelo «Prescriptivo y Predictivo» | El producto es prescriptivo: recomienda polos y ordena la ruta sobre climatología histórica. No hay ningún modelo predictivo, y el enunciado no lo exige cuando un método más simple es el adecuado (`week06/ModelSelection.md` §12) |
| Canvas §7 | «Similitud del coseno > 75 % entre el input y el centroide» | Nunca se definió ni se implementó. Las métricas del modelo están en `week06/ModelSelection.md` §4 y §8.5 |
| Canvas §3 y §9 | «Matriz de Estacionalidad»; «Entrenar K-Means / HDBSCAN» | La matriz existe como TA-05 (`estacionalidad_polo_mes.csv`). El modelo elegido fue enlace completo con diámetro acotado |
| `Requirements.md`, supuesto 3 | La época propicia de la ficha oficial es una guía de estacionalidad | Falso. La ficha publica frecuencia de visita («Todo el año», «Fines de semana»), no una ventana climática. La estacionalidad sale del clima (TA-05), y la excepción de CU-01 que usaba la época de la ficha deja de aplicar |
| `Requirements.md`, restricción 1 | No hay datos de precio por recurso | Falso en parte: la ficha trae el tipo de ingreso en el 74,8 % de los recursos y la tarifa en soles en el 13 %. Ya calibran el modelo de costo |
| `Requirements.md` §6 | `INDICE_LEJANIA` «se renombró desde `INDICE_COSTO_LOGISTICO`» | El cambio de nombre nunca llegó al CSV ni al código: la columna sigue siendo `INDICE_COSTO_LOGISTICO`. Se publicará como `INDICE_LEJANIA` en el maestro v3 (semana 10) |
| `Requirements.md` §6 | Tres tareas analíticas | TA-04 (ruta) y TA-05 (estacionalidad) se numeraron en `week06/ModelSelection.md` §1. RF-03 (eventos con ventana temporal) se agregó en la Delivery 1 |

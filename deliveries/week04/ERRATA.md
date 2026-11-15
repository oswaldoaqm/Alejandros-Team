# Erratas · Semana 4

Lo entregado el 2 de septiembre está intacto en la etiqueta [`entrega/semana-04`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-04). Esta carpeta se corrigió después, en su sitio. Aquí está cada cambio y por qué.

| Dónde | Qué decía | Qué dice ahora | Por qué |
|---|---|---|---|
| `data/acquisition.md`, opción 2 | Ofrecía `python code/download_inventory.py`, con la nota «No hemos generado ese Script» | Apunta a `pipeline/adquisicion/descargar_inventario.py`, que baja el CSV, guarda su MD5 y lo compara con `data/sample.csv` | Un documento de adquisición no puede citar un script que no existe |
| `data/data_quality.md`, el impacto del intercambio | «todos los recursos caen en el océano Índico frente a Somalia» | «todos los recursos caerían al sur del círculo polar antártico (Machu Picchu, en 72,5° S y 13,2° O)» | Leídas como vienen, las latitudes del inventario van de −81,3 a −68,7 y las longitudes de −18,3 a −0,6: todas al sur del círculo polar, al oeste de Greenwich, lejos del océano Índico |

El hallazgo principal de esta entrega, la latitud y la longitud intercambiadas en la fuente, sigue vigente y se volvió a verificar en las semanas 5 y 6.

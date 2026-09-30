# Adquisición de datos

Los únicos scripts del proyecto que salen a internet. Se corren en la máquina de un integrante, porque los entornos automatizados donde se desarrolla el resto no alcanzan las fuentes. Todo lo que bajan queda en `data/externos/`, fuera de git; al repositorio entra lo que el pipeline construye a partir de ahí.

| Script | Qué baja | Tiempo | Licencia de la fuente |
|---|---|---|---|
| `descargar_inventario.py` | Inventario Nacional de Recursos Turísticos (el CSV base), con MD5, manifiesto y comparación contra `deliveries/week04/data/sample.csv` | segundos | ODC-BY |
| `descargar_osm.py` | Extracto de OpenStreetMap del Perú (Geofabrik), con MD5 verificado y manifiesto | 5-15 min, según la conexión | ODbL 1.0 |
| `descargar_fichas_html.py` | HTML crudo de la ficha de cada recurso del inventario vigente: primero los recursos nuevos y las 31 que fallaron en el scraper v3, luego los acontecimientos y al final el resto. Al volver a correrlo baja solo las que faltan | 2-3 h la primera vez | Datos abiertos de MINCETUR (ODC-BY) |
| `descargar_clima_polos.py` | Clima diario 2016-2025 en el centro de cada uno de los 222 polos: lluvia, horas de lluvia, nieve, horas de sol y temperaturas | ~6 días, limitado por la cuota gratuita de Open-Meteo | CC BY 4.0 |

Los tres retoman donde quedaron si se cortan: basta volver a correr el mismo comando.

## Cómo correrlos

Desde la raíz del repositorio, con Python 3.11 o más y `requests` instalado:

```bash
# ventana 1: se deja corriendo; si se apaga la PC, se vuelve a lanzar y sigue
python pipeline/adquisicion/descargar_clima_polos.py

# ventana 2: unas 3 horas en total
python pipeline/adquisicion/descargar_inventario.py
python pipeline/adquisicion/descargar_osm.py
python pipeline/adquisicion/descargar_fichas_html.py
```

Mientras corren, la PC tiene que estar enchufada y sin suspenderse. Si se suspende no se pierde nada, solo se atrasa.

## Por qué el clima tarda días

Open-Meteo es gratuito para uso no comercial con 10 000 llamadas al día y 5 000 por hora, y cuenta una petición de 10 años de datos diarios como unas 261 llamadas. El script se queda por debajo de ambos topes, anota lo gastado en `cuota.json` y espera solo cuando se acaba. Baja primero los polos que más se recomiendan, así un resultado parcial ya sirve.

## Por qué el HTML de todas las fichas

`fichas_mincetur.csv` salió de un scraper que no guardaba las páginas. Su parser tiene errores que no se arreglan sin volver a leerlas (31 fichas caídas por distancias como "1.200.5 km", accesos de hasta 67 406 km) y dejó fuera la descripción de cada lugar y la fecha de cada fiesta, que la app necesita. Con el HTML guardado, el parser nuevo se prueba sobre páginas reales y se corre las veces que haga falta sin volver a tocar el servidor.

## Buenas prácticas con las fuentes

- MINCETUR: una petición por segundo y un agente que identifica al proyecto. El inventario base se baja entero en una sola petición.
- Open-Meteo: siempre bajo la cuota gratuita, sin paralelizar.
- Geofabrik: una sola descarga del extracto, verificada por MD5, en vez de consultar servicios de ruteo públicos miles de veces. Geofabrik publica uno nuevo cada día; el script conserva el que ya bajó para que todo el cálculo use el mismo archivo.

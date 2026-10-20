# Adquisición de datos

Los únicos scripts del proyecto que salen a internet. Se corren en la máquina de un integrante, porque los entornos automatizados donde se desarrolla el resto no alcanzan las fuentes. Todo lo que bajan queda en `data/externos/`, fuera de git; al repositorio entra lo que el pipeline construye a partir de ahí.

| Script | Qué baja | Tiempo | Licencia de la fuente |
|---|---|---|---|
| `descargar_inventario.py` | Inventario Nacional de Recursos Turísticos (el CSV base), con MD5, manifiesto y comparación contra `deliveries/week04/data/sample.csv` | segundos | ODC-BY |
| `descargar_osm.py` | Extracto de OpenStreetMap del Perú (Geofabrik), con MD5 verificado y manifiesto | 5-15 min, según la conexión | ODbL 1.0 |
| `descargar_fichas_html.py` | HTML crudo de la ficha de cada recurso del inventario vigente: primero los recursos nuevos y las 31 que fallaron en el scraper v3, luego los acontecimientos y al final el resto. Al volver a correrlo baja solo las que faltan | 2-3 h la primera vez | Datos abiertos de MINCETUR (ODC-BY) |
| `descargar_clima_polos.py` | Clima diario 2016-2025 en el centro de cada uno de los 222 polos: lluvia, horas de lluvia, nieve, horas de sol y temperaturas | ~6 días, limitado por la cuota gratuita de Open-Meteo | CC BY 4.0 |
| `descargar_overture.py` | De Overture Maps, los lugares del Perú (tema *places*), leyendo del archivo remoto solo los bloques que caen en el país y solo las columnas que hacen falta: nombre, categoría, confianza, ubicación y fuentes. Nunca teléfonos, correos, páginas ni redes. De los 11 GB del tema lee unos 100 MB: 666 549 lugares, 42 MB | 1-10 min, según la conexión | CDLA Permissive 2.0; lo de Foursquare, Apache 2.0, y no se usa |
| `descargar_luces.py` | Las luces nocturnas de VIIRS de 17 meses (los compuestos mensuales del Earth Observation Group, en la copia del Banco Mundial en AWS), leyendo de cada archivo solo la ventana del Perú y sus alrededores. Si se corta, sigue con los meses que faltan. Unos 500 MB | 6-30 min, según la conexión | Dominio público; el Banco Mundial pide citar su copia |
| `descargar_nubes.py` | La máscara de nubes de GOES-16 a las 21:00 y a la 01:00 de cada noche de 2022 a 2024: 2 188 imágenes, de las que lee solo la ventana del Perú. Trabaja seis meses a la vez y, si se corta, baja solo los meses que faltan. Unos 30 MB | 20-60 min, según la conexión | Dominio público (NOAA) |
| `descargar_metar.py` | Los METAR de los aeropuertos peruanos de 2022 a 2024, de NOAA: de cada fila, solo la fecha, la estación con su nombre y su lugar, y el texto METAR. Unos 6 MB | un par de minutos | NOAA, con cita. Los de estaciones fuera de EE. UU. no se redistribuyen (Resolución 40 de la OMM): quedan en `data/externos/` |
| `descargar_fotos.py` | De Wikidata, lo que tiene coordenadas y foto cerca de las paradas y las bases, con sus nombres y sus tipos; de Wikimedia Commons, el autor, la licencia y el tamaño de cada una de esas fotos, y de las que la revisión puso a mano en `pipeline/referencia/fotos_revisadas.csv`. Las fotos no: la app las pide a Wikimedia | 10-20 min | Wikidata, CC0; cada foto, la suya |

Los que tardan retoman donde quedaron si se cortan: basta volver a correr el mismo comando.

## Cómo correrlos

Desde la raíz del repositorio, con Python 3.11 o más y `requests` instalado (para los cuatro de la noche, `pip install -e ".[adquisicion]"`):

```bash
# ventana 1: se deja corriendo; si se apaga la PC, se vuelve a lanzar y sigue
python pipeline/adquisicion/descargar_clima_polos.py

# ventana 2: unas 3 horas en total
python pipeline/adquisicion/descargar_inventario.py
python pipeline/adquisicion/descargar_osm.py
python pipeline/adquisicion/descargar_fichas_html.py
python pipeline/adquisicion/descargar_fotos.py   # después de los artefactos del motor: busca fotos para sus paradas y bases

# para la noche: en cualquier orden, antes de pipeline/noche.py y pipeline/cielo.py
python pipeline/adquisicion/descargar_overture.py
python pipeline/adquisicion/descargar_luces.py
python pipeline/adquisicion/descargar_nubes.py
python pipeline/adquisicion/descargar_metar.py
```

Mientras corren, la PC tiene que estar enchufada y sin suspenderse. Si se suspende no se pierde nada, solo se atrasa.

## Por qué el clima tarda días

Open-Meteo es gratuito para uso no comercial con 10 000 llamadas al día y 5 000 por hora, y cuenta una petición de 10 años de datos diarios como unas 261 llamadas. El script se queda por debajo de ambos topes, anota lo gastado en `cuota.json` y espera solo cuando se acaba. Baja primero los polos que más se recomiendan, así un resultado parcial ya sirve.

## Por qué el HTML de todas las fichas

`fichas_mincetur.csv` salió de un scraper que no guardaba las páginas. Su parser tiene errores que no se arreglan sin volver a leerlas (31 fichas caídas por distancias como "1.200.5 km", accesos de hasta 67 406 km) y dejó fuera la descripción de cada lugar y la fecha de cada fiesta, que la app necesita. Con el HTML guardado, el parser nuevo se prueba sobre páginas reales y se corre las veces que haga falta sin volver a tocar el servidor.

## Buenas prácticas con las fuentes

- MINCETUR: una petición por segundo y un agente que identifica al proyecto. El inventario base se baja entero en una sola petición.
- Open-Meteo: siempre bajo la cuota gratuita, sin paralelizar.
- Wikidata y Wikimedia Commons: de a un pedido, con pausa, un agente que identifica al proyecto y respetando el `Retry-After` cuando responden 429. A Commons, los archivos de a 50.
- Overture, VIIRS, GOES-16 y los METAR están en el programa de datos abiertos de AWS: se leen por rangos, solo lo que cae en el Perú, sin bajar los archivos enteros.
- Geofabrik: una sola descarga del extracto, verificada por MD5, en vez de consultar servicios de ruteo públicos miles de veces. Geofabrik publica uno nuevo cada día; el script conserva el que ya bajó para que todo el cálculo use el mismo archivo.

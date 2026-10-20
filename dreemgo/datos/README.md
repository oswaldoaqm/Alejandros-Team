# Artefactos del motor

Lo que `dreemgo/motor` carga al arrancar ([decisión 0003](../../docs/decisiones/0003-artefactos-precalculados.md)). Los arma `python -m pipeline.artefactos --version AAAA.MM.n` a partir de `data/procesados/`; no se editan a mano.

| Archivo | Qué tiene |
|---|---|
| `manifiesto.json` | `version_datos`, la fecha y la huella de cada fuente, cuántas paradas atiende cada interés, la atribución, el SHA-256 de cada archivo y, desde la `2026.10.5`, cada aeropuerto con su ciudad y los minutos de su vuelo a Lima. Desde la `2026.10.6`, el interés `vida_nocturna` con cuántos lugares para salir hay, y los resúmenes de la noche y del cielo; desde la `2026.10.7`, el de dónde comer |
| `recursos.json.gz` | Los recursos de cada polo con lo que la respuesta muestra y lo que el motor necesita para programarlos: valor, visita, caminata, horario, días de atención y tarifa. Desde la `2026.10.7`, `comida_m`: a cuántos metros queda el lugar de comida más cercano, o `null` si no hay ninguno a menos de 1,5 km ([decisión 0019](../../docs/decisiones/0019-plan-creible.md)) |
| `polos.json.gz` | Cada polo: nombre, regiones, novedad, base, sus paradas, los tiempos entre ellas y desde la base, su clima mes a mes y sus eventos. Donde algún camino va en tren o en bote, cuántos de sus km van en cada uno. Desde la `2026.10.6`, su noche: los lugares para salir y su cielo ([decisión 0018](../../docs/decisiones/0018-planes-de-noche.md)). Desde la `2026.10.7`, la base lleva `comida_m`, como cada recurso |
| `origenes.json.gz` | Las 24 ciudades de partida, con el camino a cada base y a las paradas a menos de 4 horas: minutos, km, km en tren y km en bote. Desde la `2026.10.5`, también la ida en avión a cada base ([decisión 0016](../../docs/decisiones/0016-vuelos.md)) |
| `eventos.json.gz` | Los acontecimientos con la regla de su fecha |
| `costos.json` | Los parámetros del costo, de [`pipeline/referencia/costos.csv`](../../pipeline/referencia/costos.csv), y el pasaje de cada ruta aérea por tramo (`vuelo_LIM_CUZ`…) |

Son deterministas: con las mismas tablas salen los mismos bytes, así que dos máquinas que corren el pipeline sobre las mismas descargas obtienen las mismas huellas. Combinan el inventario de MINCETUR (ODC-BY), el clima de Open-Meteo (CC BY 4.0), OpenStreetMap (ODbL) y, para la noche y la comida, Overture Maps (CDLA Permissive 2.0), las luces de VIIRS y las nubes de NOAA: ver [DATA_LICENSES.md](../../DATA_LICENSES.md).

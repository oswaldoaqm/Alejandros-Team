# Artefactos del motor

Lo que `dreemgo/motor` carga al arrancar ([decisión 0003](../../docs/decisiones/0003-artefactos-precalculados.md)). Los arma `python -m pipeline.artefactos --version AAAA.MM.n` a partir de `data/procesados/`; no se editan a mano.

| Archivo | Qué tiene |
|---|---|
| `manifiesto.json` | `version_datos`, la fecha y la huella de cada fuente, cuántas paradas atiende cada interés, la atribución y el SHA-256 de cada archivo |
| `recursos.json.gz` | Los recursos de cada polo con lo que la respuesta muestra y lo que el motor necesita para programarlos: valor, visita, caminata, horario, días de atención y tarifa |
| `polos.json.gz` | Cada polo: nombre, regiones, novedad, base, sus paradas, los tiempos entre ellas y desde la base, su clima mes a mes y sus eventos |
| `origenes.json.gz` | Las 24 ciudades de partida, con los tiempos a cada base y a las paradas a menos de 4 horas |
| `eventos.json.gz` | Los acontecimientos con la regla de su fecha |
| `costos.json` | Los parámetros del costo, de [`pipeline/referencia/costos.csv`](../../pipeline/referencia/costos.csv) |

Son deterministas: con las mismas tablas salen los mismos bytes, así que dos máquinas que corren el pipeline sobre las mismas descargas obtienen las mismas huellas. Combinan el inventario de MINCETUR (ODC-BY), el clima de Open-Meteo (CC BY 4.0) y OpenStreetMap (ODbL): ver [DATA_LICENSES.md](../../DATA_LICENSES.md).

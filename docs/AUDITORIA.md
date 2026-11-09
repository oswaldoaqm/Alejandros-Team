# Auditoría del motor: lo que un jurado podría objetar

El 5 de noviembre de 2026 revisamos el motor como lo haría un jurado que busca razones para bajarnos la nota: cada supuesto, con una prueba y su cifra. La rejilla es la del informe de la semana 10: los 24 orígenes; 2, 4, 6 y 9 días; los doce meses, sin intereses. Son 1 152 consultas y 3 444 viajes. Las cifras salen de `python -m evaluacion.auditoria`: «antes» es el motor con los datos `2026.10.8` ([`auditoria_2026.10.8.json`](../data/evaluacion/resultados/auditoria_2026.10.8.json)), y «después», con los `2026.11.1` ([`auditoria.json`](../data/evaluacion/resultados/auditoria.json)).

## Lo que se arregló

### En la ciudad se iba a velocidad de carretera

En Lima, el modelo hacía 10 km en 13 minutos de manejo, y TomTom (Traffic Index 2025) mide 37,6 un miércoles de día. En la rejilla, el 69 % de los tramos del día dentro de Lima iba más rápido que ese promedio, aun contando los minutos fijos de cada traslado, y el 94 % de los días en Lima tenía seis paradas. Las fichas de MINCETUR decían lo mismo: en sus 164 recorridos que salen de la provincia de Lima, el modelo daba una mediana de 54 minutos donde la ficha dice 95. Pesa porque Lima y las ciudades grandes, como Trujillo y Arequipa, son la base del 46 % de los viajes, y las medianas, como el Cusco y Puno, de otro 30 %.

Ahora la red reconoce sus ciudades y va en ellas al ritmo que mide TomTom ([decisión 0025](decisiones/0025-trafico-de-las-ciudades.md)). Trujillo no entra en el ajuste y sirve de prueba: la red da 35,0 minutos por 10 km donde TomTom mide 35,7. En la rejilla, los tramos de Lima más rápidos que el promedio de TomTom bajan al 30 %, y todos pasan por una vía rápida, porque por las calles la red no supera los 15,3 km/h. Los días en Lima con seis paradas bajan al 69 %. En las ciudades grandes, los tramos más rápidos que TomTom bajan del 46 % al 13 %.

### Salir de Lima en un tren que casi nunca sale

Este lo destapó el arreglo anterior. Con el tráfico en la red, salir de Lima en tren se volvía más rápido que cruzar la ciudad, y la ida a Huancayo, Jauja, Tarma, La Merced, Oxapampa o Tanta hacía sus primeros 28 km en el Ferrocarril Central. La app decía «por carretera y en tren», el viaje perdía el bus de noche y el costo sumaba un pasaje de tren. Ese tren salió tres veces en 2025, y en 2026 la venta de Semana Santa se suspendió sin fecha (Infobae).

La red ya no usa las líneas que OpenStreetMap trae como rutas de pasajeros y no tienen servicio regular ([`trenes_sin_servicio.csv`](../pipeline/referencia/trenes_sin_servicio.csv)): quedan 713 de los 1 042 km de tren. Con los datos `2026.10.8`, 32 idas de un origen a una base tenían algún tramo en tren; con el tráfico y el Ferrocarril Central, 77; ahora, 33, todas a Machupicchu Pueblo y a Santa Teresa. Por casos como este, la rejilla se vuelve a correr con cada versión de los datos.

### El bus a la sierra central llegaba antes que el bus de verdad

De las 29 rutas de Cruz del Sur, 16 caían en el rango de la empresa con los datos `2026.10.8`. De Lima a Huancayo, el motor daba 6 h 03, y el bus tarda de 7 h 30 a 8 h 55.

La ida en bus lleva ahora dos ritmos, ajustados con esas rutas y medidos dejando fuera cada corredor ([decisión 0026](decisiones/0026-ida-en-bus.md)). Fuera de la muestra caen 20 de 29 rutas en el rango, y 24 con todas en el ajuste. De Lima a Huancayo, 8 h 32, y ahora en bus de noche. Un modelo con un parámetro menos da casi lo mismo fuera de la muestra, y la decisión lo muestra con sus cifras.

Una cifra queda peor. El motor da una sola hora de llegada al bus de noche, y los buses de una misma ruta difieren hasta en 3 h 10. En 11 de las 18 rutas de noche, el más lento llega más de una hora después de lo que dice la app. Se resuelve con los horarios de cada empresa, el punto 1 de lo pendiente.

### «Siempre propone los mismos sitios»

Las diez zonas más propuestas se llevan el 80 % de los viajes, y Miraflores sola el 18 %. La variante del kit de evaluación pasa a ser la raíz de la calidad ([decisión 0021](decisiones/0021-evaluacion-semana-12.md)): la anterior coincidía con el motor en 110 de 120 propuestas, y calificarla no iba a decir casi nada. La nueva coincide en 100. En la rejilla, con ella, las diez zonas más propuestas se llevan el 76 % de los viajes, salen 66 zonas distintas en vez de 56 y Miraflores baja del 19 al 11 % ([`auditoria_variante.json`](../data/evaluacion/resultados/auditoria_variante.json)). Reparte algo más, pero tres de cada cuatro viajes siguen yendo a diez zonas: esta variante sola no resuelve la concentración. Si las calificaciones la favorecen, se despliega.

## Lo que no es un problema, con su prueba

El orden de las paradas de cada día: en el 55 % de los días es el mejor orden posible para el camino, y solo en el 1 % queda a más de 5 % del mejor, por fuerza bruta sobre las mismas paradas y sin mirar horarios. Lo que se veía mal era el tiempo de cada tramo, no el orden.

La heurística que elige qué visitar: en los 120 viajes que el motor propone para las 40 consultas del kit, reducidos a sus 15 mejores lugares, junta el 99,0 % del valor que junta el óptimo exacto ([`optimo.json`](../data/evaluacion/resultados/optimo.json)). Con los datos `2026.10.8` juntaba el 99,1 %.

## Pendiente, en orden

| # | Lo que objetaría el jurado | La prueba | Qué hacer | Cuándo |
|---|---|---|---|---|
| 1 | «Hay un vuelo, un bus o un tren justo cuando llegas» | A Mazamari hay 2 vuelos por semana, a las 11:20; a Andahuaylas 5, a las 5:55 o a las 6:00; a Huaraz 6, a las 7:10 (FlightConnections, 5 de noviembre). `rutas_aereas.csv` lo dice: «el motor supone que hay uno a la hora en que se llega al aeropuerto». El bus de noche sale a la hora que conviene para llegar a las 6:00 | Las frecuencias y la primera y última salida de las 22 rutas aéreas y de los buses de cada empresa; en las de pocas salidas, el horario de verdad. Y la llegada como un rango | w13e |
| 2 | El bus te deja en el centro, no en el terminal | La ida va de centro a centro y no cuenta llegar antes al terminal | Los terminales de OpenStreetMap en cada punta, el taxi hasta ellos con el tráfico de la ciudad y la media hora antes que piden las empresas | w13e |
| 3 | Lo que se ve de noche, puesto de día | El Circuito Mágico del Agua sale 390 veces en la rejilla, siempre a las 10:51, porque su ficha dice que abre de 7:00 a 22:30. Abre a las 15:00, y las fuentes con luces son a las 19:15, 20:15 y 21:30 (Andina, 2024; How to Peru, julio de 2026) | Su horario de verdad, con su fuente, y en la noche del viaje | w13d |
| 4 | Los horarios y los días de cierre | Sin fecha, que es lo normal en el formulario, el motor no revisa qué días cierra cada lugar, y la app no muestra el horario. Y la ficha puede estar mal, como en el 3 | Mostrar el horario y los días de cierre de cada parada, y avisar si alguna cierra algún día de la semana | w13d |
| 5 | Tiempos de visita sin fuente | Salen de una tabla por subtipo, «supuesto del equipo»: el Centro Histórico de Trujillo, 20 minutos; Moray, 30; las Líneas de Nasca, 30, sin la avioneta | Corregir los subtipos mal puestos y poner un mínimo por jerarquía, declarado como supuesto | w13d |
| 6 | Solo taxi | Los tramos del día suponen auto o taxi, y la app no lo dice | Decirlo en la app, y cuánto sería en transporte público, con una fuente | w13d |
| 7 | La hora del día | TomTom mide Lima 17 % más lenta a las 8 de la mañana que en el promedio del día, y el motor usa un solo tiempo por tramo | El ritmo de cada hora en las ciudades, con TomTom | semana 14 |
| 8 | Las colas | El motor no suma esperas en los lugares más visitados, como la fila del bus de Aguas Calientes a Machu Picchu en temporada alta, ni la espera del taxi. La del taxi la cubre el margen de la 0025, sin una fuente que la mida | Una espera por lugar y temporada donde haya una fuente que la mida; donde no la haya, decirlo en la app | semana 14 |
| 9 | Zonas peligrosas | Hay polos con paradas en el VRAEM (Satipo: Río Tambo, Mazamari, Pangoa; Kimbiri). No salen en la rejilla sin intereses, pero se pueden elegir como destino y el motor no avisa | Un aviso con las alertas oficiales de viaje | w13d |
| 10 | ¿Dónde duermo? | El motor elige el pueblo, no el hospedaje | Hospedajes del directorio de MINCETUR y de OpenStreetMap, con su categoría como banda de precio, y la seguridad del distrito (Observatorio de Seguridad Ciudadana del Mininter, INEI) | semana 14 |
| 11 | Costos viejos | El README de `pipeline/referencia/` dice que ninguno de transporte, hospedaje o comida está calibrado con tarifas de este año | Pasajes, entradas y hospedaje de 2026, con su fuente | semana 14 |
| 12 | Se califican ellos mismos | Quienes califican el kit hicieron el producto | Ya está declarado en la 0021; sumar calificadores de fuera del equipo | semana 14 |
| 13 | Entradas con cupo | Machu Picchu vende un número fijo de entradas por día, 5 600 en 2026 según el Ministerio de Cultura (El Peruano), y el motor no lo dice; del tren sí avisa | Un aviso en los polos con entradas con cupo | w13d |

## Sobre el aprendizaje automático

Lo que el jurado puede preguntar es qué se aprende de datos y qué no.

Agrupar los lugares en zonas (TA-01) es aprendizaje no supervisado: agrupamiento jerárquico con enlace completo sobre la distancia de viaje. El modelo de tiempos es aprendizaje supervisado: una regresión de 11 parámetros (el ritmo de cada tipo de vía, los recargos por trocha y por curvas, los minutos fijos de cada traslado y el recargo de las ciudades medianas), ajustada con 1 779 recorridos medidos en las fichas, con pérdida robusta y validación cruzada por distrito. Se equivoca en 22 % en promedio; la fórmula de la semana 6, en 48 %. Desde la 0025 se suma lo que las fichas no ven, el tráfico, con una fuente medida (TomTom) y una ciudad que queda fuera del ajuste para probarlo (Trujillo). La ida en bus son dos parámetros más, ajustados con 29 rutas de Cruz del Sur y comparados, dejando fuera cada corredor, con tres modelos más simples ([0026](decisiones/0026-ida-en-bus.md)). La estacionalidad (TA-05) es una regla declarada sobre diez años de clima, y el itinerario (TA-04) es optimización: un problema de orientación con horarios, que la heurística resuelve al 99 % del óptimo exacto.

No usamos aprendizaje profundo, y no por falta de tiempo. Una red neuronal aprende de muchos ejemplos con su respuesta. Para el itinerario no hay ninguno: nadie nos dijo todavía «este viaje estuvo bien». Para los tiempos hay 1 779 filas, que una red profunda memoriza y que una regresión de 11 parámetros explica, con su error medido y cada parámetro a la vista. El enunciado lo permite de forma explícita: no se exige un modelo complejo cuando uno más simple es el adecuado ([0004](decisiones/0004-sin-modelos-supervisados.md)).

Entra más aprendizaje cuando haya datos. Con las calificaciones del kit (196 viajes, cuatro personas) se pueden aprender los pesos del puntaje, la calidad, la novedad y los intereses, con un modelo de preferencias por pares y validación cruzada por consulta. Y si la app llega a tener viajes aceptados por usuarios, se puede sumar la capa de ordenamiento supervisado que la 0004 deja como trabajo futuro.

## Fuentes

Consultadas el 5 de noviembre de 2026, salvo donde se dice otra cosa.

- TomTom Traffic Index 2025, las páginas de [Lima](https://www.tomtom.com/traffic-index/city/lima/), [Arequipa](https://www.tomtom.com/traffic-index/city/arequipa) y [Trujillo](https://www.tomtom.com/traffic-index/city/trujillo).
- Cruz del Sur: la página de cada una de las 29 rutas, en [`evaluacion/buses.csv`](../evaluacion/buses.csv), consultadas el 26 de octubre.
- Infobae: [el último recorrido de 2025 del tren turístico Lima–Huancayo](https://www.infobae.com/peru/2025/08/06/tren-turistico-lima-huancayo-realizo-su-ultimo-recorrido-del-2025-evaluan-incrementar-sus-salidas-el-proximo-ano/), 6 de agosto de 2025, y [por qué no se venden pasajes para Semana Santa de 2026](https://www.infobae.com/peru/2026/03/18/tren-lima-huancayo-por-que-no-se-venden-boletos-para-el-viaje-de-semana-santa-2026/), 18 de marzo de 2026.
- Andina, [el horario del Circuito Mágico del Agua](https://andina.pe/agencia/noticia-circuito-magico-del-agua-te-espera-diversion-y-comida-el-feriado-largo-1007809.aspx), 2024, y How to Peru, [Magic Water Circuit in Lima](https://howtoperu.com/answers/magic-water-circuit-in-lima-worth-it-for-couples-families-or-first-time-visitors/), julio de 2026.
- El Peruano, [el aforo de Machu Picchu para 2026](https://elperuano.pe/noticia/282176-machu-picchu-ministerio-de-cultura-fija-aforo-maximo-de-5600-visitantes-diarios-para-2026).
- FlightConnections, las páginas de cada ruta desde Lima, como la de [Mazamari](https://www.flightconnections.com/flights-from-lim-to-mza).

# Auditoría del motor: lo que un jurado podría objetar

El 5 de noviembre de 2026 revisamos el motor como lo haría un jurado que busca razones para bajarnos la nota: cada supuesto, con una prueba y su cifra. La rejilla es la del informe de la semana 10: los 24 orígenes; 2, 4, 6 y 9 días; los doce meses, sin intereses. Son 1 152 consultas y 3 444 viajes. Las cifras salen de `python -m evaluacion.auditoria`: «antes» es el motor con los datos `2026.10.8` ([`auditoria_2026.10.8.json`](../data/evaluacion/resultados/auditoria_2026.10.8.json)), y «después», con los `2026.11.1` ([`auditoria_2026.11.1.json`](../data/evaluacion/resultados/auditoria_2026.11.1.json)).

El 12 de noviembre se arreglaron cuatro puntos de lo pendiente y la mitad de otros dos, con el contrato 1.8 y los datos `2026.11.2`, más dos cosas que salieron después: el tope del bus de noche y los Uros. Para esos, «antes» es el motor de `main` del 10 de noviembre con los datos `2026.11.1`, y «después», la `2026.11.2` ([`auditoria.json`](../data/evaluacion/resultados/auditoria.json)). Desde entonces, la auditoría mide también el bus de noche y los avisos de cada viaje.

El 15 de noviembre se arreglaron los tres puntos que quedaban para w13e, con el contrato 1.9 y los datos `2026.11.3` ([decisión 0030](decisiones/0030-a-su-hora-y-desde-el-terminal.md)). Para esos, «antes» es la `2026.11.2`, la de arriba, y «después», la `2026.11.3`.

El mismo día, con los datos `2026.11.4`, se sumó el tráfico de cada hora en Lima, Arequipa y Trujillo, y la app dice que no cuenta colas ([decisión 0031](decisiones/0031-la-hora-del-dia.md)). Para eso, «antes» es la `2026.11.3` ([`auditoria_2026.11.3.json`](../data/evaluacion/resultados/auditoria_2026.11.3.json)).

Y con los datos `2026.11.5` y el contrato 1.10, el techo del bus salió de las tarifas de Cruz del Sur, y cada base dice qué hospedajes tiene cerca ([decisión 0032](decisiones/0032-costo-del-bus-y-donde-dormir.md)).

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

Las diez zonas más propuestas se llevan el 80 % de los viajes, y Miraflores sola el 18 %. La variante del kit de evaluación pasa a ser la raíz de la calidad ([decisión 0021](decisiones/0021-evaluacion-semana-12.md)): la anterior coincidía con el motor en 110 de 120 propuestas, y calificarla no iba a decir casi nada. La nueva coincide en 100. En la rejilla, con ella, las diez zonas más propuestas se llevan el 76 % de los viajes, salen 66 zonas distintas en vez de 56 y Miraflores baja del 19 al 11 % ([`auditoria_variante.json`](../data/evaluacion/resultados/auditoria_variante.json)). Reparte algo más, pero tres de cada cuatro viajes siguen yendo a diez zonas: esta variante sola no resuelve la concentración. Se iba a desplegar si las calificaciones la favorecían, y no la favorecen: su nDCG@3 no se distingue del del motor ([`resultados.md`](evaluacion/resultados.md)). Con los datos `2026.11.2`, el motor ya reparte como ella, sin cambiar su puntaje: 67 zonas distintas, el 76 % de los viajes en las diez más propuestas y Miraflores en el 15 %.

### El bus de noche se llevaba hasta el 40 % del viaje

Con dos días, la mitad de los viajes iba en bus de noche, con un tope de 9 h 36 por tramo, y tres días desde el Cusco podían ser Ilo o Nasca, a 14 horas por tramo. Las calificaciones del kit dan menos nota cuanto más del viaje se lleva el bus: 1,25 con menos del 20 %, 0,97 del 20 al 30 % y 0,80 del 30 al 40 %. El tope baja al 30 % ([decisión 0027](decisiones/0027-tope-del-bus-de-noche.md)). En la rejilla, el bus de noche pasa del 50,2 al 6,7 % de los viajes de dos días, y el que más se lleva del viaje, del 39,5 al 29,9 %. Tiene un costo: lo que ya no va de noche va de día, y los viajes de dos días que avisan que el camino se lleva mucho del viaje pasan del 27,9 al 56,8 %.

### El Circuito Mágico, a la hora en que abre y después de noche

Salía 390 veces en la rejilla, siempre a las 10:51, porque su ficha dice que abre de 7:00 a 22:30. Abre de 15:00 a 22:00, de miércoles a domingo, y las fuentes con luces son a las 19:15, 20:15 y 21:30. Ese horario, con su fuente, manda ahora sobre el de la ficha ([decisión 0028](decisiones/0028-horarios-y-visitas-corregidos.md)): sale 277 veces, y se llega entre las 14:56 y las 15:30. Era la hora en que abre, pero todavía de día. Desde la `2026.11.3`, un lugar que se ve de noche no es parada del día: va en una noche del viaje, la primera con función si hay fecha ([decisión 0030](decisiones/0030-a-su-hora-y-desde-el-terminal.md)). En la rejilla, el Circuito ya no sale de día, y 447 de los 454 viajes que duermen en Miraflores llevan su noche.

### Visitas de 20 minutos a un centro histórico

El 23 % de las visitas a lugares de jerarquía 3, y el 24 % de las de jerarquía 4, duraban 30 minutos o menos: la Biblioteca Municipal Manuel Beingolea, Moray, el templo de Andahuaylillas y el Centro Histórico de Trujillo, este en 20 porque su ficha lo pone en el subtipo «Otros». Ahora las cinco zonas monumentales de «Otros» van con 90 minutos, y desde la jerarquía 3 la visita dura una hora como mínimo, un supuesto que queda escrito como tal (0028). En la rejilla ya no hay ninguna de 30 minutos o menos, y la mediana de la jerarquía 3 sube de 66 a 76 minutos. Tiene un efecto que no buscábamos: con la hora mínima, un lugar de jerarquía 3 rinde por minuto lo mismo que uno de jerarquía 2 de 20 minutos, y el día se llena de lugares menores. En Lima, los días con seis paradas suben del 69 al 87 %.

### Puno sin los Uros

Ningún viaje a Puno iba a los Uros: su ficha no les da jerarquía, y se visitan en lugar de la Reserva Nacional del Titicaca, de jerarquía 4, que no tiene camino. Ahora valen como ella (0028) y van en los viajes a Puno que tienen tiempo, como verifica una prueba de lo conocido. Puno pasa del 8,0 al 12,7 % de los viajes de la rejilla. Con el motor de ahora, Puno queda primero en 7 de las 40 consultas del kit, donde las calificaciones preferían lo que desplaza; esas notas eran de viajes sin los Uros ([`resultados.md`](evaluacion/resultados.md)).

### Los horarios y los días de cierre

El PR 52, de Miguel, llevó el horario de cada lugar al contrato y a su hoja en la app, y sumó un aviso: si el viaje no tiene fecha y alguna parada no abre todos los días, lo dice. Ahora el horario es el corregido cuando la ficha está mal, la fila del plan dice si el lugar cierra algún día de la semana y el plan impreso lo lleva también. Con fecha, el motor no pone una parada fuera de su horario ni un día que cierra: es la propiedad 16 del contrato 1.8, que se prueba con 1 000 consultas al azar. Sin fecha no puede saber el día, y por eso la app lo muestra siempre.

### El VRAEM y el cupo de Machu Picchu

Un viaje que duerme o para en uno de los 37 distritos del VRAEM que delimita el D.S. 133-2022-PCM lo avisa primero, con las alertas de Canadá y Estados Unidos. Hoy son 126 paradas en 9 polos, y 5 bases. Y cada parada con cupo dice cuántas personas entran al día y dónde se compran las entradas: Machu Picchu, 4 500 al día y 5 600 en temporada alta (el 5 de noviembre esta auditoría daba solo la segunda cifra), en tuboleto.cultura.pe y, solo 1 000 al día, en persona en Machu Picchu Pueblo ([decisión 0029](decisiones/0029-avisos-de-seguridad-y-de-entradas.md)). Lo verifican las propiedades 17 y 18. Reemplazan los dos avisos de `acceso` que el PR 52 había sumado para lo mismo (0029).

### Un vuelo cada día

El motor supone que hay un vuelo cuando se llega al aeropuerto, y a Mazamari hay unos 9 al mes. Cada ruta lleva ahora cuántos vuelos tiene al mes, de FlightConnections, y si alguna punta tiene menos de uno por día, el viaje lo avisa: cuántos hay por semana y que las fechas se fijen según el vuelo. En la rejilla, lo avisan 52 de 3 432 viajes. A qué hora sale cada vuelo sigue sin entrar: no hay una fuente que se pueda citar sin entrar a las páginas de venta.

### El bus, desde el terminal

La ida en bus iba de centro a centro. Ahora la de tres horas o más suma el taxi al terminal de la ciudad de origen, media hora de embarque y el taxi del terminal a la base, si el bus no deja en el pueblo. Los terminales salen de OpenStreetMap; en Lima, el taxi hasta el Terminal Terrestre Yerbateros es de 21 minutos. Cada ida suma de 35 a 71 minutos, 41 en la mediana, y la mediana del bus de noche en la rejilla pasa de 10,1 a 10,9 horas de puerta a puerta. Tres días desde Arequipa a Puno dejan de salir: el camino pesa más que la visita.

### La hora del día

El motor usaba el mismo tiempo para un tramo a cualquier hora, y TomTom mide Lima 18 % más lenta a las 8:00 que en el promedio de 10:00 a 16:00, al que se ajustó la red, y 37 % más a las 18:00. Desde la `2026.11.4`, las bases de Lima, Arequipa y Trujillo llevan el ritmo de cada hora, y el planificador cuenta cada tramo a la hora en que sale ([decisión 0031](decisiones/0031-la-hora-del-dia.md)). En la rejilla, la mediana de los tramos del día en Lima baja de 13,5 a 11,7 km/h. Los días con seis paradas casi no cambian (78,1 %): la mayoría de los tramos va a media jornada, cuando el factor es cercano a 1.

### Las colas

No hay una fuente que mida la espera por lugar y por temporada, ni la del bus de Aguas Calientes a Machu Picchu. El motor no inventa una: la app dice en la letra chica que no cuenta colas ni esperas.

### El bus, con tarifas de 2026

Ninguna tarifa de transporte, hospedaje o comida estaba calibrada con precios de este año. Para el bus, la tarifa más baja de Cruz del Sur en sus 18 rutas desde Lima, vista a mano en la página de cada una, queda 1,75 veces sobre el valor central del motor en la mediana, y en 11 de las 18 pasaba el máximo de la banda. Cruz del Sur es la empresa cara, así que esas tarifas fijan el techo: 84 soles por tramo más 0,10 por km, que las cubre a todas. El central y el mínimo siguen siendo los de las empresas más baratas. El hospedaje, la comida y la movilidad local siguen sin calibrar: quedan en lo pendiente.

### Dónde dormir

El motor elige el pueblo, no el hospedaje. Ahora cada base lleva hasta tres hospedajes con nombre de OpenStreetMap a 2 km o menos, y la app los muestra junto a dónde se duerme: 162 de las 194 bases tienen alguno. No llevan precio, ni categoría, ni la seguridad del distrito: eso queda en lo pendiente.

### En auto o taxi

La app dice ahora, en la hoja de cada lugar y en la letra chica, que entre un lugar y otro del día el plan cuenta en auto o taxi. La letra chica decía además que la visita sale de la ficha de cada lugar, y no es así: es el tiempo típico de cada clase de lugar, un supuesto nuestro. Ya no lo dice. Cuánto sería en transporte público queda en lo pendiente, en el punto 6.

## Lo que no es un problema, con su prueba

El orden de las paradas de cada día: en el 55 % de los días es el mejor orden posible para el camino, y solo en el 1 % queda a más de 5 % del mejor, por fuerza bruta sobre las mismas paradas y sin mirar horarios. Lo que se veía mal era el tiempo de cada tramo, no el orden.

La heurística que elige qué visitar: en los 120 viajes que el motor propone para las 40 consultas del kit, reducidos a sus 15 mejores lugares, junta el 99,1 % del valor que junta el óptimo exacto con los datos `2026.11.5` ([`optimo.json`](../data/evaluacion/resultados/optimo.json)). Con los `2026.11.1` juntaba el 99,0 %, y con los `2026.10.8`, el 99,1 %.

## Pendiente, en orden

Los números son los de la lista del 5 de noviembre, para que se puedan citar: los que faltan ya se arreglaron, arriba.

| # | Lo que objetaría el jurado | La prueba | Qué hacer | Cuándo |
|---|---|---|---|---|
| 6 | Solo taxi | Los tramos del día suponen auto o taxi. La app ya lo dice, pero no cuánto sería en transporte público | Cuánto sería en transporte público, con una fuente por ciudad | después de la entrega |
| 10 | La categoría del hospedaje y la seguridad del distrito | La app dice qué hospedajes hay cerca, pero no cuánto cuestan ni qué tan seguro es el distrito | El directorio de prestadores de MINCETUR, con su categoría como banda de precio, y el Observatorio de Seguridad Ciudadana del Mininter | después de la entrega |
| 11 | El hospedaje, la comida y la movilidad de 2026 | Solo el bus se calibró con tarifas de este año | Una fuente de 2026 por zona para cada uno | después de la entrega |
| 12 | Se califican ellos mismos | Quienes califican el kit hicieron el producto | Un kit corto de 10 consultas para 3 a 5 personas de fuera, y la comparación con el equipo en los mismos viajes ([decisión 0033](decisiones/0033-calificadores-de-fuera.md)) | antes del 17 de noviembre |

## Sobre el aprendizaje automático

Lo que el jurado puede preguntar es qué se aprende de datos y qué no.

Agrupar los lugares en zonas (TA-01) es aprendizaje no supervisado: agrupamiento jerárquico con enlace completo sobre la distancia de viaje. El modelo de tiempos es aprendizaje supervisado: una regresión de 11 parámetros (el ritmo de cada tipo de vía, los recargos por trocha y por curvas, los minutos fijos de cada traslado y el recargo de las ciudades medianas), ajustada con 1 779 recorridos medidos en las fichas, con pérdida robusta y validación cruzada por distrito. Se equivoca en 22 % en promedio; la fórmula de la semana 6, en 48 %. Desde la 0025 se suma lo que las fichas no ven, el tráfico, con una fuente medida (TomTom) y una ciudad que queda fuera del ajuste para probarlo (Trujillo). La ida en bus son dos parámetros más, ajustados con 29 rutas de Cruz del Sur y comparados, dejando fuera cada corredor, con tres modelos más simples ([0026](decisiones/0026-ida-en-bus.md)). La estacionalidad (TA-05) es una regla declarada sobre diez años de clima, y el itinerario (TA-04) es optimización: un problema de orientación con horarios, que la heurística resuelve al 99 % del óptimo exacto.

No usamos aprendizaje profundo, y no por falta de tiempo. Una red neuronal aprende de muchos ejemplos con su respuesta. Para el itinerario no hay ninguno: nadie nos dijo todavía «este viaje estuvo bien». Para los tiempos hay 1 779 filas, que una red profunda memoriza y que una regresión de 11 parámetros explica, con su error medido y cada parámetro a la vista. El enunciado lo permite de forma explícita: no se exige un modelo complejo cuando uno más simple es el adecuado ([0004](decisiones/0004-sin-modelos-supervisados.md)).

Entra más aprendizaje cuando haya datos. Con las calificaciones del kit (196 viajes, tres personas, con un acuerdo bajo) se pueden aprender los pesos del puntaje, la calidad, la novedad y los intereses, con un modelo de preferencias por pares y validación cruzada por consulta. Y si la app llega a tener viajes aceptados por usuarios, se puede sumar la capa de ordenamiento supervisado que la 0004 deja como trabajo futuro.

## Fuentes

Consultadas el 5 de noviembre de 2026, salvo donde se dice otra cosa.

- TomTom Traffic Index 2025, las páginas de [Lima](https://www.tomtom.com/traffic-index/city/lima/), [Arequipa](https://www.tomtom.com/traffic-index/city/arequipa) y [Trujillo](https://www.tomtom.com/traffic-index/city/trujillo).
- FlightConnections: [los vuelos desde Lima](https://www.flightconnections.com/flights-from-lima-lim), con cuántos tiene al mes cada ruta, consultada el 15 de noviembre, y la [ruta a Tingo María](https://www.flightconnections.com/flights-from-lim-to-tgi), que vuelve a tener vuelos en enero de 2027.
- Cruz del Sur: la página de cada una de las 29 rutas, en [`evaluacion/buses.csv`](../evaluacion/buses.csv), consultadas el 26 de octubre.
- Infobae: [el último recorrido de 2025 del tren turístico Lima–Huancayo](https://www.infobae.com/peru/2025/08/06/tren-turistico-lima-huancayo-realizo-su-ultimo-recorrido-del-2025-evaluan-incrementar-sus-salidas-el-proximo-ano/), 6 de agosto de 2025, y [por qué no se venden pasajes para Semana Santa de 2026](https://www.infobae.com/peru/2026/03/18/tren-lima-huancayo-por-que-no-se-venden-boletos-para-el-viaje-de-semana-santa-2026/), 18 de marzo de 2026.
- Andina, [el horario del Circuito Mágico del Agua](https://andina.pe/agencia/noticia-circuito-magico-del-agua-te-espera-diversion-y-comida-el-feriado-largo-1007809.aspx), 2024, y How to Peru, [Magic Water Circuit in Lima](https://howtoperu.com/answers/magic-water-circuit-in-lima-worth-it-for-couples-families-or-first-time-visitors/), julio de 2026.
- El Peruano, [el aforo de Machu Picchu para 2026](https://elperuano.pe/noticia/282176-machu-picchu-ministerio-de-cultura-fija-aforo-maximo-de-5600-visitantes-diarios-para-2026), 2 de noviembre de 2025; Andina, [lo que hay que saber para ir a Machu Picchu en 2026](https://andina.pe/agencia/noticia-iras-a-machu-picchu-2026-ten-cuenta-estas-medidas-para-una-optima-visita-1056293.aspx), 25 de diciembre de 2025, y La República, [el aforo de la temporada alta](https://larepublica.pe/sociedad/2026/06/17/machu-picchu-amplia-su-capacidad-para-la-temporada-alta-fechas-aforo-y-que-cambiara-para-los-visitantes-520693), 17 de junio de 2026, consultadas el 10 de noviembre.
- El Peruano, [el D.S. 133-2022-PCM](https://busquedas.elperuano.pe/normaslegales/decreto-supremo-que-modifica-el-articulo-1-del-decreto-supre-decreto-supremo-n-133-2022-pcm-2121215-1/), que delimita el VRAEM, y el [plan de trabajo 2025-2026 de la comisión del VRAEM del Congreso](https://www.congreso.gob.pe/Docs/comisiones2021/cem-vraem/files/plan_trabajo23_24/plan_de_trabajo_congre_olivos_2025-2026[r].pdf), que trae la lista de sus 37 distritos; las alertas de viaje de [Canadá](https://travel.gc.ca/destinations/peru), del 6 de noviembre de 2026, y de [Estados Unidos](https://travel.state.gov/content/travel/en/traveladvisories/traveladvisories/peru-travel-advisory.html), consultadas el 10 de noviembre.
- Los Uros: Andina, [la Reserva Nacional del Titicaca](https://andina.pe/agencia/noticia-la-excepcional-belleza-altoandina-de-reserva-nacional-del-titicaca-640674.aspx), noviembre de 2016, y las excursiones de [My Guide Peru](https://www.myguideperu.com/experiences/puno-3-hour-trip-to-the-floating-uros-islands) y [Civitatis](https://www.civitatis.com/puno/excursion-isla-uros/), consultadas el 10 de noviembre.
- FlightConnections, las páginas de cada ruta desde Lima, como la de [Mazamari](https://www.flightconnections.com/flights-from-lim-to-mza).

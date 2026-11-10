# 0025 · El tráfico de las ciudades

**Fecha:** 5 de noviembre de 2026 · **Estado:** vigente · Corrige la calibración de la [0008](./0008-calibrar-con-las-fichas.md) dentro de las ciudades

## Contexto

La red se calibraba con 1 780 recorridos de las fichas, casi todos de un pueblo a sus lugares, por carretera. Con un solo ritmo por tipo de vía para todo el país, en la ciudad se iba casi a la velocidad de la carretera. En Lima, el modelo hacía 10 km en 13 minutos de manejo; TomTom mide 37,6 un miércoles de día (Traffic Index 2025). En la rejilla de 1 152 consultas de la [auditoría](../AUDITORIA.md), el 69 % de los tramos del día dentro de Lima iba más rápido que ese promedio, aun contando los minutos fijos de cada traslado, y el 94 % de los días en Lima tenía seis paradas. Las mismas fichas lo decían: en sus 164 recorridos que salen de la provincia de Lima, el modelo daba una mediana de 54 minutos donde la ficha dice 95. Y pesa: Lima y las ciudades grandes, como Trujillo y Arequipa, son la base del 46 % de los viajes que propone el motor, y las medianas, como el Cusco y Puno, de otro 30 %.

## Decisión

- **La red reconoce sus ciudades** (`red_vial.manchas_urbanas`): celdas de unos 550 m con 40 cruces de calles o más por km², promediadas con sus vecinas y unidas. Sin datos de afuera: Lima y Callao salen como una mancha de 1 040 km², Arequipa de 303, Trujillo de 158 y el Cusco de 72. Son 31 manchas de 20 km² o más.
- **Por su tamaño, cada mancha va a un ritmo:**
  - **metrópoli** (500 km² o más: Lima y Callao) y **grandes** (100 a 500, como Arequipa, Trujillo, Huancayo, Piura o Chiclayo): ninguna vía va más rápido que lo que mide TomTom en Lima y en Arequipa. La autopista, a la velocidad de sus vías rápidas (33,5 y 33,2 km/h); las demás calles, al ritmo con que un recorrido de unos 10 km por la ciudad tarda lo que TomTom mide de día, el promedio de un miércoles a las 10, 12, 14 y 16 h (`pipeline/referencia/trafico_ciudades.csv`). Sale 15,3 km/h en Lima y 17,1 en las grandes;
  - **medianas** (20 a 100 km², como el Cusco o Puno): TomTom no mide ninguna, así que llevan un recargo por km que se ajusta con las fichas, como el resto de los parámetros. Sale 1 minuto más por km;
  - las de menos de 20 km² son pueblos y quedan como estaban.
- **Trujillo no entra en el ajuste:** es la prueba. Con el ritmo de Arequipa, la red da 35,0 minutos por 10 km donde TomTom mide 35,7. En Lima da 37,3 (TomTom, 37,6) y en Arequipa 35,0 (35,0).
- **El Ferrocarril Central sale de la red** (`pipeline/referencia/trenes_sin_servicio.csv`). Con el tráfico, salir de Lima en tren se volvía más rápido que cruzar la ciudad: la ida de Lima a Huancayo, Jauja, Tarma, La Merced, Oxapampa o Tanta hacía sus primeros 28 km en ese tren, y con eso perdía el bus de noche y sumaba un pasaje de tren al costo. Ese tren no tiene servicio regular: salió tres veces en 2025, en Semana Santa y Fiestas Patrias, y en marzo de 2026 la venta de Semana Santa se suspendió sin fecha (Infobae). OpenStreetMap lo trae como una ruta de pasajeros; ahora la red no usa sus tramos ni sube a sus estaciones.
- **Las bases se quedan donde estaban** (`bases.fijas`). Con el tráfico, dormir en una ciudad cuesta más, y al volver a elegir las bases el Cusco perdía Sacsayhuamán, Maras, Moray y Chinchero, que se iban a una zona con base en Anta; Puno perdía Taquile y Amantaní, que se iban a Chucuito, y Arequipa se partía con una zona en Chacahuayo, un caserío. Qué zonas hay y dónde duerme cada una se decide con la v3 de TA-01 ([0023](./0023-ta01-v3-horas-reales.md)), con estas cifras como dato. `python -m pipeline.tiempos --elegir-bases` las vuelve a elegir.

## Alternativas descartadas

- **Aprender el recargo de las ciudades solo con las fichas:** baja el error de validación cruzada de 22,3 a 20,3 %, pero deja a Lima en 22 minutos por 10 km. Las fichas que salen de Lima van casi todas por la Panamericana; sus recorridos cortos dicen menos de lo que mide el tráfico.
- **Un solo ritmo para todas las vías de la ciudad:** la Vía Expresa iría tan lenta como una calle, y la red dejaría de usarla.
- **El ritmo de cada hora del día:** TomTom lo publica, y a las 8 de la mañana Lima va 17 % más lenta que el promedio del día. El motor usa un solo tiempo por tramo; queda pendiente.
- **Sumar aparte la espera del taxi:** no hay una fuente que la mida. Los tiempos nuevos quedan por encima de lo que dicen las fichas en la ciudad, y ese margen la cubre.

## Consecuencias

En la rejilla de la auditoría, con las mismas bases y el mismo motor (`python -m evaluacion.auditoria`):

- **En Lima,** los tramos del día que van más rápido que el promedio de TomTom bajan del 69 % al 30 %. Todos esos pasan por una vía rápida, porque por las calles la red no supera los 15,3 km/h. El tramo típico, de 4 km, toma 16 minutos de puerta a puerta; antes, 12.
- **En las ciudades grandes,** bajan del 46 % al 13 %.
- **Los días en Lima con seis paradas** bajan del 94 % al 69 %; en todo el país, del 66 % al 63 %. Los días con 7 horas o más ocupadas suben del 41 % al 46 %: entre parada y parada se va más tiempo.
- **El orden de las paradas y la concentración de los viajes** casi no cambian: las diez zonas más propuestas se llevan el 80 % de los viajes, antes y después.

Y en la calibración:

- **El error de validación cruzada sobre las fichas** queda en 22,5 % (antes 22,3 %). Los 168 recorridos que salen de la provincia de Lima quedan, en la mediana, 10 % por encima de lo que dicen sus fichas; antes, 20 % por debajo. En la ciudad se prefiere lo que mide el tráfico.
- **Fuera de las ciudades, las carreteras asfaltadas van más rápido** que antes, porque lo lento de la ciudad ya no se reparte entre todas las vías: la autopista, de 48 a 87 km/h, y la troncal, de 58 a 63. La trocha va más lenta, de 32 a 25 km/h, y los minutos fijos de cada traslado bajan de 7,2 a 4.
- **Las bases no cambian:** de `polos_bases.csv` cambian solo los minutos medios de cada base a sus lugares.
- **Los datos pasan a la versión `2026.11.1`**, junto con la ida en bus de la [0026](./0026-ida-en-bus.md), y con ellos las cifras de la evaluación.

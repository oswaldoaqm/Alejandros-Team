# 0027 · El bus de noche se lleva como máximo el 30 % del viaje

**Fecha:** 12 de noviembre de 2026 · **Estado:** vigente · Cambia el tope del bus de noche de la [0019](./0019-plan-creible.md), del 40 al 30 %, y con él la propiedad 13 del [contrato](../CONTRATO.md) (versión 1.8)

## Contexto

La 0019 dejó ir en bus de noche si la ida y la vuelta no se llevaban el 40 % de las horas del viaje: en dos días, hasta 9 h 36 por tramo; en tres, hasta 14 h 24. Lo dejó escrito como un supuesto por calibrar. Con ese tope, tres días desde el Cusco podían ser Ilo o Nasca, a 14 horas: 28 de las 72 horas del viaje arriba de un bus. En la rejilla de la [auditoría](../AUDITORIA.md), la mitad de los viajes de dos días iba en bus de noche, y el que más se llevaba llegaba al 39,5 % del viaje.

Las calificaciones del kit, de tres de los cuatro, dan con qué calibrarlo ([`resultados.md`](../evaluacion/resultados.md)). El kit se armó con el tope del 40 %, y sus viajes en bus de noche sacan menos nota cuanto más se lleva el bus:

| Parte del viaje en el bus | Viajes | Nota media | No encajan |
|---|---|---|---|
| Menos del 20 % | 28 | 1,25 | 7 % |
| Del 20 al 30 % | 37 | 0,97 | 19 % |
| Del 30 al 40 % | 29 | 0,80 | 28 % |

## Decisión

- El bus de noche va si la ida y la vuelta se llevan menos del 30 % de las horas del viaje (`TOPE_BUS_DE_NOCHE`): hasta 7 h 12 por tramo en dos días, 10 h 48 en tres y 14 h 24 en cuatro.
- El 40 % sigue para lo demás en que pesa el camino (`CAMINO_QUE_PESA`): el aviso de que el viaje pasa mucho tiempo en el camino y la regla para volar de la [0016](./0016-vuelos.md).
- La propiedad 13 del contrato verifica el 30 %.
- Sigue siendo un supuesto del producto. Las notas apoyan bajar el tope, pero no fijan dónde: son pocos viajes, el acuerdo entre quienes califican es bajo, y los viajes con más bus van también más lejos.

## Alternativas descartadas

- El 35 %: en dos días deja tramos de hasta 8 h 24, con Puno desde el Cusco (7 h 21) pero no Huaraz desde Lima (8 h 26). En tres, de hasta 12 h 36, como Mollendo desde el Cusco (11 h 56) o Huacho desde Cajamarca (12 h 20).
- El 25 %: el tope de dos días, 6 horas, queda bajo las 7 que necesita un bus de noche, y en tres días saca Trujillo desde Lima y Arequipa desde el Cusco, ambos a 9 h 57.

## Consecuencias

- El fin de semana casi no va en bus de noche: en la rejilla, el 6,7 % de los viajes de dos días, con tramos de 7 h a 7 h 12. Es lo que la 0019 descartó porque sacaba a Huaraz de los fines de semana desde Lima. Ahora Huaraz sale desde tres días, y dos días desde Lima son Huacho, Paracas y Chincha.
- Lo que ya no va de noche va de día: los viajes de dos días que avisan que el camino se lleva mucho del viaje pasan del 27,9 al 56,8 %. Las notas no dicen si eso es mejor o peor, porque el kit no tiene esos viajes.
- Desde los cuatro días casi nada cambia: el bus de noche va en el 53,2 % de los viajes de cuatro días (antes, el 55,3 %), y el que más se lleva del viaje llega al 29,9 %.
- Las pruebas de lo conocido cambian con esto: el fin de semana desde el Cusco y desde Lima se queda cerca, y Puno y Huaraz van en bus de noche desde los tres días.
- La auditoría mide ahora cuántos viajes van en bus de noche según sus días, cuánto se lleva el bus y cuántos avisan del camino, y el informe de la evaluación, la nota según la parte del viaje en el bus.

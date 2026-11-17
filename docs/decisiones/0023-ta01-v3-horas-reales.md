# 0023 · TA-01 v3: los grupos de lugares con las horas de la red

**Fecha:** 28 de octubre de 2026 · **Estado:** medida y con su clima; no entra al producto antes de la entrega del 18 de noviembre · Mide con la red vial el modelo de la semana 6 ([`ModelSelection.md`](../../deliveries/week06/ModelSelection.md), §5.9 y §10) y propone su reemplazo

## Contexto

TA-01 agrupa los lugares en las zonas a las que se va a dormir. La v2 usa enlace completo sobre una distancia en línea recta que suma el desnivel, con un diámetro de 80 km efectivos, que en la semana 6 se leían como 3,9 horas de punta a punta con 1,6 de sinuosidad y 32,5 km/h. Esa fórmula nunca se contrastó: la red vial llegó en la semana 7 ([decisión 0007](./0007-red-vial-propia.md)), y la propia semana 6 dejó escrito que con red real el umbral habría que recalibrarlo.

[`evaluacion/polos_en_horas.py`](../../evaluacion/polos_en_horas.py) lo midió el 28 de octubre con los minutos de puerta a puerta que usa el motor:

| | v2 | v3, 4 horas y 1 300 m |
|---|---|---|
| Grupos | 222 | 203 |
| Paradas en un grupo, de 4 578 | 97,5 % | 93,2 % |
| Diámetro mediano | 3,4 h | 2,8 h |
| Grupos de más de 4 horas de punta a punta | 82 | 0 |
| Diámetro máximo | 9,8 h | 4,0 h |
| Desnivel máximo | 1 434 m | 1 300 m |

## Decisión

- **La v3 es el mismo enlace completo, sobre las horas de la red**, con cuatro horas de diámetro máximo y sin juntar paradas a más de 1 300 m de altura entre sí, lo que la v2 buscaba con su distancia. Sin ese tope, la v3 de cuatro horas junta la costa con paradas a más de 4 000 m.
- **Entra al producto en la semana 14**, con una versión nueva de los datos, después de calibrar los tiempos con los buses (semana 13): si cambian las horas, cambian los grupos.
- **Hasta entonces el producto sigue con la v2.** Lo entregado el 28 de octubre usa sus grupos.

## Alternativas descartadas

- **Dejar la v2:** el modelo promete un diámetro que 82 de sus 222 grupos no cumplen por la red. El motor no se equivoca por eso, porque arma cada día con los minutos de la red, pero un grupo de nueve horas tiene lugares que no se alcanzan a visitar en un día desde su base.
- **Cambiarla esta semana:** cambia las zonas, sus bases y el clima de cada una, y deja sin valor lo medido en la evaluación de la semana 12.
- **Tres o cinco horas:** con tres, 235 grupos y el 90,3 % de las paradas; con cinco, 180 grupos de hasta 5 horas. Cuatro es lo que la v2 prometía.

## Consecuencias

- 246 paradas que la v2 tenía en un grupo quedan sin él, y 49 que no lo tenían lo ganan: quedan fuera las que no tienen cuatro paradas más a cuatro horas.
- Cambian las zonas, sus bases, sus tiempos y su clima: hay que bajar el clima de las zonas nuevas, rehacer los artefactos y volver a correr las propiedades y la evaluación.
- Las horas de la v3 son las de la red, con su error: 22 % en recorridos cortos, y en la Carretera Central, más rápido que los buses.

## Con las horas de los datos `2026.11.1` (5 de noviembre)

Con el tráfico de las ciudades ([0025](./0025-trafico-de-las-ciudades.md)) y la red sin el Ferrocarril Central, las horas cambian, y con ellas los grupos. `polos_en_horas` da ahora 205 grupos con el 92,6 % de las paradas, cuando el 28 de octubre daba 203 con el 93,2 %; 83 grupos de la v2 pasan de las cuatro horas, y el más largo llega a 10,5. Con tres horas salen 237 grupos y con cinco, 176. La decisión no cambia: los grupos que entran en la semana 14 son los de esta corrida (`data/evaluacion/resultados/polos_v3.csv`). La ida en bus de la [0026](./0026-ida-en-bus.md) no entra aquí, porque dentro de un grupo se va en auto.

## El clima de la v3 (17 de noviembre)

El clima de los grupos v3 se bajó para la corrida del 28 de octubre, la de 203 grupos: 108 con su punto propio y 95 con el de un grupo de la v2 a menos de 9 km de su centro (`data/externos/clima/crudo_v3/` y `crudo/`). [`evaluacion/clima_v3.py`](../../evaluacion/clima_v3.py) compara, para cada parada que está en un grupo en las dos versiones, el veredicto de cada mes con el clima de su grupo v2 y con el de su grupo v3 ([`clima_v3.json`](../../data/evaluacion/resultados/clima_v3.json)).

De los 50 628 pares de parada y mes, 47 158 tienen el mismo veredicto, el 93,1 %. 1 404 de las 4 219 paradas cambian el de algún mes. Casi siempre es un paso: entre advertencia y viable (2 122 pares) o entre desaconsejado y advertencia (1 205). De desaconsejado a viable pasan 126 pares, y de viable a desaconsejado, 17.

La v3 no entra antes de la entrega, por tres razones:

- Los grupos de la corrida del 5 de noviembre, que son los que se iban a usar, no son los del clima bajado. 25 de sus 205 grupos no tienen un punto de clima a menos de 9 km, y bajarlos toma un día de cuota.
- Cambiar los grupos cambia las zonas, sus bases, los tiempos, las noches, la comida, los hospedajes y los terminales. Eso pide correr el pipeline con el extracto de OpenStreetMap y rehacer los artefactos, las propiedades y la evaluación.
- Las notas del kit son de zonas de la v2. Con zonas nuevas, ninguna nota se podría usar para el motor que se entrega.

Lo que queda para después de la entrega: bajar el clima de esos 25 grupos, armar los artefactos con la v3 en una versión nueva de los datos y medir qué cambia en las respuestas antes de publicarla.


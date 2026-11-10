# 0023 · TA-01 v3: los grupos de lugares con las horas de la red

**Fecha:** 28 de octubre de 2026 · **Estado:** propuesta, para la semana 14 · Mide con la red vial el modelo de la semana 6 ([`ModelSelection.md`](../../deliveries/week06/ModelSelection.md), §5.9 y §10) y propone su reemplazo

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

# 0031 · La hora del día en las ciudades, y las colas

**Fecha:** 15 de noviembre de 2026 · **Estado:** vigente · Cierra los puntos 7 y 8 de la [auditoría](../AUDITORIA.md), el 8 solo en lo que dice la app. No cambia el [contrato](../CONTRATO.md)

## Contexto

La red se ajustó a lo que mide TomTom en Lima, Arequipa y Trujillo un miércoles de 10:00 a 16:00 (0025), y el motor usaba ese tiempo a cualquier hora. TomTom mide Lima 18 % más lenta a las 8:00 que en ese promedio, y 37 % más a las 18:00. El motor tampoco suma colas, como la del bus de Aguas Calientes a Machu Picchu.

## Decisión

- `pipeline/referencia/trafico_por_hora.csv` trae, de la tabla por hora de TomTom Traffic Index 2025, cuánto se tarda en manejar 10 km un miércoles cada dos horas en las tres ciudades. Una base a menos de 20 km del centro de Lima, o de 8 km del de Arequipa o Trujillo, lleva su `ritmo`: a cada hora, esos minutos divididos por el promedio de 10:00 a 16:00.
- El planificador cuenta cada tramo del día a la hora en que sale, con el factor de esa hora y, entre dos horas medidas, en línea recta. Así, el horario y lo que cabe en el día se miden con el tráfico de la hora.
- Para las colas no hay una fuente que mida la espera por lugar y por temporada. La app lo dice en la letra chica, con la del bus a Machu Picchu como ejemplo, y no se suma ninguna espera inventada.

## Alternativas descartadas

- Un factor solo para la hora punta: el tramo de las 18:00 tarda casi el doble que el de las 6:00, y la hora punta de TomTom es una sola cifra.
- Aplicar el ritmo a la ida desde la ciudad de origen: el bus sale de noche, cuando la ciudad va más rápido que el promedio, y la ida ya se ajustó con los horarios de Cruz del Sur (0026).
- Una espera fija por lugar «muy visitado»: sin una fuente, sería un número nuestro presentado como medido.

## Consecuencias

- Cuatro polos llevan ritmo: Miraflores y Lima, Arequipa y Trujillo. En Trujillo, a las 8:00 se va 3 % más rápido que en el promedio.
- En la rejilla de la auditoría, la mediana de los tramos del día en Lima baja de 13,5 a 11,7 km/h, y los que van más rápido que el promedio de TomTom, del 23,3 al 21,9 %. Los días en Lima con seis paradas casi no cambian: del 78,2 al 78,1 %. La hora punta de la mañana toca solo el primer tramo del día, la mayoría de los tramos va entre las 10:00 y las 16:00, cuando el factor es cercano a 1, y el día termina a las 17:00, antes de lo peor de la tarde.
- El ejemplo del contrato, en Trujillo, cambia el orden y el número de sus paradas: 22 en vez de 24.
- Las colas siguen sin contarse. Si aparece una fuente que mida la espera de un lugar, sus minutos se suman a los de su visita.

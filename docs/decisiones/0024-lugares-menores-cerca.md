# 0024 · Por un lugar menor no se va lejos

**Fecha:** 3 de noviembre de 2026 · **Estado:** vigente · Ajusta el planificador de la [0004](./0004-sin-modelos-supervisados.md) y suma la propiedad 15 del [contrato](../CONTRATO.md)

## Contexto

En la rejilla del informe de la semana 10 (24 orígenes, 2, 4, 6 y 9 días, los 12 meses: 1 152 consultas), el 1,2 % de los días de visita tenía un tramo de más de hora y media, casi siempre hacia un lugar de jerarquía 1 o 2. Desde Chachapoyas, en nueve días en Íllimo, el día 8 iba 1 h 41 al Reservorio Tinajones y 2 h 42 más a la Cascada Dos Reinas, los dos de jerarquía 1: 5 h 34 de camino para 1 h 50 de visita. El planificador junta valor por minuto y nunca deja un día libre: cuando en la zona se acaba lo cercano, rellena con lo lejano.

## Decisión

- **Una parada de jerarquía 1 o 2, o sin jerarquía, no va a más de 90 minutos** de la anterior, de la siguiente ni de la base (`planificador.TRAMO_MENOR_MAX`). Se comprueba al armar el horario de cada día, así que vale en la semilla, en la inserción y en el 2-opt.
- **Lo de jerarquía 3 y 4 puede seguir quedando lejos:** por Kuélap o por las Islas Ballestas sí se maneja.
- **Si no queda nada cerca que valga el camino, el día queda libre,** con el aviso que ya existía.
- **La propiedad 15 del contrato** lo verifica en cada consulta al azar, con los tramos que trae la respuesta.

## Alternativas descartadas

- **Una regla por día, «no más camino que visita»:** dejaría fuera días razonables, como uno en el Colca con seis paradas a menos de una hora una de otra: 4 h 19 de camino y 3 h 17 de visita.
- **Contar también la jerarquía 3:** cortaría tramos como el de San Andrés a las Islas Ballestas, de 122 minutos, y por un lugar así sí se maneja dos horas.
- **Bajar la escala a 1, 2, 4 y 8:** los días con más camino que visita bajan del 6,6 al 4,7 %, pero los viajes con un imperdible, del 71 al 51 %, y vuelve lo que corrigió la [0013](./0013-un-polo-por-pueblo.md).

## Consecuencias

En la misma rejilla, con el motor de verdad:

- Los días con un tramo de más de 90 minutos bajan del 1,2 al 0,1 %, y los que quedan van a lugares de jerarquía 3 o 4. Los días con 4 horas de camino o más, del 1,7 al 1,1 %, y los que tienen más camino que visita, del 6,6 al 6,0 %.
- El día 8 en Íllimo queda en 2 h 54 de camino para 3 h de visita.
- El valor visitado por viaje (mediana 84) y las paradas por viaje (24) no cambian, y los polos propuestos casi tampoco: los diez más propuestos siguen llevándose el 80 % de los viajes.
- Los días libres pasan de 12 a 36, casi todos en viajes de nueve días a zonas chicas. Eso lo arreglan los viajes de varios polos, no esta regla.
- Las cifras de `data/evaluacion/resultados/` son del motor de antes; se vuelven a correr con la versión final.

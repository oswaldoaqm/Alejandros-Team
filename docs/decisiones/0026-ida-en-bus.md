# 0026 · La ida a la base va en bus

**Fecha:** 5 de noviembre de 2026 · **Estado:** vigente · Ajusta la ida por carretera de la [0009](./0009-viaje-en-estrella.md) con lo que mide la evaluación de buses de la semana 12

## Contexto

La red se calibra con autos: los recorridos de las fichas van casi todos en auto particular. Pero la ida del origen a la base, la que más pesa en un viaje, se hace en bus. En la semana 12 se midieron 29 rutas de Cruz del Sur ([`evaluacion/buses.py`](../../evaluacion/buses.py)): con los datos `2026.10.8` caían 16 en el rango de la empresa, 6 debajo y 7 encima. Con el tráfico de las ciudades ([0025](./0025-trafico-de-las-ciudades.md)), la autopista fuera de ellas ya no carga con lo lento de Lima, y en auto caen 20 dentro, 8 debajo y 1 encima. De las 8 que quedan debajo, 4 cruzan la Carretera Central, entre Chosica y La Oroya, donde el bus va mucho más lento que un auto. De Lima a Huancayo, la red daba 6 h 03 con los datos `2026.10.8` y da 7 h 29 en auto con el tráfico; el bus tarda de 7 h 30 a 8 h 55. A La Merced, 7 h 29 en auto, y el bus, de 8 h 30 a 10 h 05.

## Decisión

- **Dos ritmos para la ida en bus,** sobre el mismo camino que elige la red (`tiempos.correccion_del_bus`):
  - **en la autopista,** fuera de las ciudades con piso, el bus va a 78 km/h, donde el auto va a 87;
  - **entre Chosica y La Oroya,** tarda 1,37 veces lo que un auto.
- **Se ajustan con las 29 rutas** (`tiempos.ida_en_bus`), en escala logarítmica contra la mitad del rango de la empresa, y el error se mide dejando fuera cada corredor: la ida y la vuelta entre dos ciudades salen juntas del ajuste. Son 19 corredores.
- **Solo la ida a la base.** La ida a una parada, la del viaje de un día, sigue en auto, y los tramos de cada día también.

## Alternativas descartadas

Todas se probaron con las mismas rutas, la misma pérdida y dejando fuera cada corredor, y sus cifras están en `data/procesados/ida_en_bus.json`. El error es contra la mitad del rango de la empresa. La distancia al rango es cuánto queda fuera del rango, en proporción a su borde más cercano, y vale 0 para una ruta dentro:

| Modelo | Lo ajustado | Dentro del rango | Debajo | Encima | Error medio | Distancia media al rango |
|---|---|---|---|---|---|---|
| En auto, sin corregir | — | 20 | 8 | 1 | 6,4 % | 1,3 % |
| Un solo factor para todo el bus | × 1,05 | 23 | 2 | 4 | 5,6 % | 1,2 % |
| Solo la Carretera Central | × 1,37 | 21 | 6 | 2 | 5,8 % | 0,7 % |
| **La autopista y la Carretera Central** | 78 km/h y × 1,37 | 20 | 5 | 4 | 5,8 % | 0,6 % |

- **Un solo factor para todo el bus:** cae más veces en el rango y tiene el menor error, porque estira todas las rutas por igual y los rangos de la costa son anchos. Pero deja lejos la Carretera Central, donde el error era de un solo lado: La Merced en 7 h 47 y Oxapampa en 9 h 35, cuando el bus más rápido tarda 8 h 30 y 10 h 30.
- **Solo la Carretera Central:** con 29 rutas, da lo mismo que la elegida fuera de la muestra, con un parámetro menos. Se queda el de la autopista porque su signo no depende de qué corredor quede fuera: en las 19 corridas, el bus va de 75 a 81 km/h, siempre más lento que el auto. Con él, el bus de noche de la costa llega más cerca de la hora de los buses más lentos.
- **Frenar las aristas de la Carretera Central en la red:** el camino más rápido se iba por vías que ningún bus toma, y La Merced seguía por debajo del bus más rápido.
- **Los tiempos de la empresa para las 29 rutas, y la red para el resto:** dos varas distintas según la ruta, y las otras 4 000 idas seguirían igual de lejos.

## Consecuencias

- **En el rango de la empresa:** 20 de 29 rutas, dejando fuera cada corredor, con un error medio de 5,8 % contra la mitad del rango; con todas en el ajuste, 24. Antes, 16. De Lima a Huancayo, 8 h 32 (la empresa, de 7 h 30 a 8 h 55); a Jauja, 7 h 35 (de 6 h 35 a 7 h 35), y a La Merced, 8 h 32 (de 8 h 30 a 10 h 05).
- **Las que siguen fuera,** con todas en el ajuste: Oxapampa, 10 h 16 contra 10 h 30 del bus más rápido; de Ayacucho a Lima, 10 h 37 contra 10 h 55; de Arequipa al Cusco, debajo por menos de un minuto; y de Abancay y del Cusco a Lima, encima. El motor da el mismo tiempo de ida y de vuelta, y de esas dos ciudades a Lima el bus tarda menos que de ida.
- **El bus de noche:** con los tiempos nuevos, 18 de las 29 rutas toman de 7 a 16 horas y van de noche (antes, 14). El motor da una sola hora de llegada, y los buses de una misma ruta difieren hasta en 3 h 10 (de Trujillo a Lima): en 11 de las 18, el más lento llega más de una hora después de lo que dice la app (antes, 4 de 14), y en 2 ni el más rápido llega a esa hora (antes, 2). Lo resuelve mostrar el horario de cada empresa, que va con los terminales.
- **`evaluacion/buses.csv` sirve ahora para ajustar y para medir.** La cifra que cuenta es la que deja fuera cada corredor, en `data/procesados/ida_en_bus.json`; `python -m evaluacion.buses` da la de todas.
- **Faltan el terminal y la hora de salida:** el bus va de centro a centro y sale cuando hace falta. Es lo siguiente.

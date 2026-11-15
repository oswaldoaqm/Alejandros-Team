# 0030 · Los vuelos con su frecuencia, el bus desde el terminal y el Circuito Mágico de noche

**Fecha:** 15 de noviembre de 2026 · **Estado:** vigente · Suma la noche de `espectaculo` al [contrato](../CONTRATO.md) (versión 1.9), con la propiedad 19, y cierra los puntos 1, 2 y 3 de la [auditoría](../AUDITORIA.md)

## Contexto

La auditoría del 5 de noviembre dejó tres objeciones para w13e. El motor suponía que siempre hay un vuelo cuando se llega al aeropuerto: a Mazamari hay unos 9 vuelos al mes. La ida en bus iba de centro a centro, sin llegar al terminal ni embarcar. Y el Circuito Mágico del Agua, que se ve de noche, salía de día: con el horario corregido de la 0028 ya no a las 10:51, pero sí a las 15:00, antes de que se prendan las fuentes.

## Decisión

- Cada una de las 22 rutas aéreas lleva cuántos vuelos tiene al mes, de FlightConnections, con los vuelos programados de noviembre de 2026 (`pipeline/referencia/rutas_aereas.csv`). Si alguna punta del vuelo tiene menos de 30 al mes, menos de uno por día, el viaje lo avisa con un aviso de `acceso`, nivel `advertencia`: cuántos hay por semana y que las fechas se fijen según el vuelo. Tingo María no tiene vuelos en noviembre de 2026 y vuelve a tener 4 por semana desde enero de 2027: va con esos 4.
- La ida en bus de tres horas o más suma el taxi del centro de la ciudad de origen a su terminal, media hora de embarque y el taxi del terminal a la base (`pipeline/terminales.py`). Los terminales salen de OpenStreetMap, sin las estaciones de transporte urbano; en cada punta va el terminal terrestre más cercano, o el más cercano de una empresa. Si la base no tiene terminal a menos de 3 km, o el taxi pasa de media hora, el bus deja en el pueblo. Los ritmos del bus no cambian: se ajustaron con horarios de terminal a terminal (0026).
- Un lugar que se ve de noche (`pipeline/referencia/de_noche.csv`, hoy solo el Circuito, con funciones a las 19:15, 20:15 y 21:30, de miércoles a domingo) no es parada del día. Si el viaje duerme en una base a una hora o menos, una noche es de `espectaculo`: con fecha, la primera con función; sin fecha, la segunda, y dice qué días hay. Va antes que las estrellas y que salir.

## Alternativas descartadas

- El horario de cada vuelo: no hay una fuente que se pueda citar sin entrar a las páginas de venta, y las frecuencias cambian cada mes. El aviso dice cuántos hay, no a qué hora.
- Los horarios de cada empresa de buses: mismo problema. La salida del bus de noche sigue siendo la que conviene para llegar a las 6:00.
- El terminal de cada empresa: el motor no elige empresa. Va el terminal terrestre, que es donde salen la mayoría.
- Poner el Circuito como última parada del día: el día termina a las 17:00, y las funciones son de noche.

## Consecuencias

- En la rejilla de la auditoría, el Circuito ya no sale de día: 0 paradas, antes 277. 447 de los 454 viajes que duermen en Miraflores llevan su noche.
- 52 de los 3 432 viajes de la rejilla avisan que no hay un vuelo cada día.
- Cada ida de tres horas o más suma de 35 a 71 minutos, 41 en la mediana: el taxi en Lima, hasta el Terminal Terrestre Yerbateros, es de 21 minutos, y en Arequipa de 16. La mediana de los viajes en bus de noche de la rejilla pasa de 10,1 a 10,9 horas de puerta a puerta, y el bus sale antes: de Lima a Huaraz, a las 20:30 y no a las 21:30.
- Tres días desde Arequipa a Puno ya no salen: la ida pasa de 7 h 21 a 8 h 07, y el camino pesa más que la visita. Con cuatro, sí.
- Las cifras de FlightConnections son de noviembre de 2026; si cambian, se cambian en el CSV.

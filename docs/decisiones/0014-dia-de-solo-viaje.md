# 0014 · Un día de solo viaje puede durar nueve horas

**Fecha:** 7 de octubre de 2026 · **Estado:** vigente · Ajusta la [0009](./0009-viaje-en-estrella.md) y la propiedad 3 del [contrato](../CONTRATO.md)

## Contexto

La 0009 partía en dos días toda ida de más de 8 horas, que es el tope de una jornada. De Lima a Huaraz la red da 8 horas y 7 minutos, y a Nasca, 8 y 26. Un bus hace esos tramos de un tirón, pero el motor los partía: con cuatro días, el viaje a Huaraz se iba en ir y volver, con dos medias jornadas allá, y no salía entre las tres rutas.

## Decisión

- **Un día en el que solo se viaja puede durar hasta 9 horas.** Una ida más larga se sigue partiendo en partes iguales, ahora de hasta 9 horas, y se duerme a mitad de camino ([`dreemgo/motor/viaje.py`](../../dreemgo/motor/viaje.py), `SOLO_VIAJE_MAX_MIN`).
- **Un día con visitas sigue topado en 8 horas, con su viaje incluido.** El día de llegada y el de salida tienen visitas solo si de esas 8 horas sobran 90 minutos.
- **La propiedad 3 del contrato** dice ahora: «Ninguna jornada con visitas pasa de 8 horas entre traslados y visitas. Un día de solo viaje, sin visitas, puede llegar a 9». Las pruebas la verifican así.

## Alternativas descartadas

- **Dejar las 8 horas:** Huaraz solo salía desde Lima con seis días o más.
- **Diez horas:** el caso de Lima queda igual, y cambian otras 183 consultas hacia destinos todavía más lejanos.
- **Subir toda la jornada a 9 horas:** alarga también los días de visita, que es donde el viajero se cansa.
- **Viajar de noche**, que es como mucha gente hace esos tramos: pide horarios de buses, que no tenemos. Queda como límite conocido.

## Consecuencias

- **«Lima, cuatro días, julio» propone Huaraz, Huacho y Nasca.** A Huaraz: un día de ida, dos allá y uno de vuelta. El aviso lo dice: «La ida y la vuelta se llevan 16 h 16 de tus 4 días».
- **Cambia en cuántos días se hace el camino** en 1 557 de los 4 656 que van de una ciudad de origen a una base. 120 pasan de dos días a uno; los demás son más largos y se parten en menos días.
- **En la rejilla del informe** cambia el conjunto de rutas en 236 de 1 152 consultas, ninguna de dos días.
- **Huaraz pasa de 74 a 64 rutas.** Gana las consultas de Lima con cuatro días y pierde otras, de ciudades desde las que ahora caben destinos más lejanos: Trujillo, el Cusco, Nasca.
- **Con la 0013, más viajes se van en el camino:** las rutas con más días de camino que de visita llegan a 9 de cada 100, y las que llevan el aviso de la ida y la vuelta, a 43.
- Las 9 horas son un supuesto del producto, como las 8.

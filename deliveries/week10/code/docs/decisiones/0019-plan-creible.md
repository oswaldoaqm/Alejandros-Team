# 0019 · Un plan creíble: el almuerzo, el bus de noche y una jornada que no se corre

**Fecha:** 19 de octubre de 2026 · **Estado:** vigente · Amplía la [0009](./0009-viaje-en-estrella.md) y la [0014](./0014-dia-de-solo-viaje.md), precisa la [0016](./0016-vuelos.md), cierra lo que la [0017](./0017-quiero-ir-a.md) dejó abierto y suma `Dia.almuerzo` y `traslado.bus_de_noche` al [contrato](../CONTRATO.md) (versión 1.6)

## Contexto

El plan no almorzaba: ocho horas de paseo seguidas. A lo que por tierra queda a una noche, como Huaraz desde Lima, se iba en un día de ida y otro de vuelta, aunque la 0016 ya decía que eso se hace en bus de noche. Y la jornada se corría con el primer lugar: un día podía empezar a las 18:00 en el Gran Teatro Nacional y terminar a las 21:41 en un parque, o llegar a las 8:53 a una casa museo que abre a las 15:00 y esperar seis horas en la puerta.

## Decisión

- **Una hora de almuerzo, que no cuenta en las 8 horas:** un día entero va de 8:00 a 17:00. Se almuerza en el primer momento que toca ([`dreemgo/motor/planificador.py`](../../dreemgo/motor/planificador.py)):
  - al terminar la primera visita después de las 12:30, salvo que ese lugar no tenga dónde comer y el siguiente sí, y allá todavía se almuerce a la hora;
  - al llegar a un lugar después de las 14:00, o desde las 11:30 si abre en una hora o más, o si su visita terminaría después de las 14:00;
  - antes de un traslado que llega después de las 14:00, desde las 11:30;
  - en la base, antes de salir si se sale después de las 12:30, o al volver.
- **Dónde comer** sale de [`pipeline/comida.py`](../../pipeline/comida.py): restaurantes, cafés y comida rápida a menos de 1,5 km de cada lugar y de cada base, de OpenStreetMap y de Overture Maps (solo lo de licencia CDLA, con confianza de al menos 0,7). Si cerca de donde toca almorzar no registran nada, el plan dice que lleves el almuerzo. En la base se da por hecho que hay: es un pueblo con hospedaje.
- **La jornada no se corre.** Si el primer lugar abre tarde, se sale más tarde, pero se vuelve a la hora de siempre: el final del tope más la hora del almuerzo. Y no se espera más de una hora en la puerta de un lugar, sin contar el almuerzo.
- **El bus de noche.** Lo que por tierra toma de 7 a 16 horas, sin tren ni bote, en un viaje de dos días o más:
  - sale a las 19:00 o después, para llegar a eso de las 6:00, y la vuelta, a la misma hora;
  - sus noches van fuera de los días: se sale la noche antes del día 1 y se vuelve la noche del último. `dias` cuenta los días allá, y `fecha_inicio` es el día en que se llega;
  - el día 1 se visita desde una hora después de llegar, y nunca antes de las 8:00;
  - se cobra a la misma tarifa por km que el bus de día, y sus noches no pagan hospedaje.
- **Tope y peso, para que un viaje corto no salga siempre lejos.** No va en bus de noche si ida y vuelta se llevan el 40 % de las horas del viaje, con sus noches: en dos días, hasta unas 9 horas y media por tramo. Y en el puntaje sus dos noches pesan como un día más: un viaje de D días se multiplica por D / (D + 1). Es un supuesto del producto, por calibrar.
- **Con destino, se vuela aunque el viaje sea corto.** El 40 % de la 0016 sirve para elegir algo más cerca; con la zona ya elegida, no aplica. El viaje con destino sigue siendo el que arma el motor cuando elige él, salvo que puede volar donde él iría por tierra.

## Alternativas descartadas

- **El almuerzo dentro de las 8 horas.** Le quitaba a cada día una hora de visitas. El equipo eligió que se sume.
- **El bus de noche sin tope ni peso.** Dos días desde el Cusco eran Puno, Arequipa y Yanque; desde Lima, Trujillo (11 horas), Huaraz y Nasca; y cuatro días por tierra desde Lima incluían Íllimo, a 16 horas. Todo viaje corto se iba lejos.
- **El bus de noche solo desde tres días.** Dejaba el fin de semana como antes, con Machu Picchu desde el Cusco, pero sacaba el viaje de fin de semana más clásico desde Lima: Huaraz en bus de noche.
- **Un recargo por el bus cama.** Las tarifas de la semana 6 no distinguen el servicio, y en el Perú los buses largos van casi todos de noche. Calibrarlo es de los costos calibrados.
- **Buscar el mejor momento del almuerzo entre todos.** El planificador arma el horario de un día unas 3 700 veces por consulta; probar cada momento lo haría unas catorce veces más lento. Las reglas miran el lugar actual y el siguiente, y solo el 2 % de los almuerzos sin dónde comer tenía otro lugar con comida a la hora.

## Consecuencias

- **Datos `2026.10.7`:** hay dónde comer registrado a menos de 1,5 km de 2 954 de los 6 225 lugares (47 %) y de 154 de las 194 bases, con 16 648 puntos de OSM y 27 005 de Overture.
- **Dónde cae el almuerzo**, en 250 consultas al azar:
  - 64 %, en un lugar con dónde comer;
  - 20 %, en un lugar sin nada registrado, con el aviso de llevarlo;
  - 5 %, en la base;
  - en un 10 % de los días con visitas no hay almuerzo: las visitas terminan antes de las 12:30, como el día en que se vuelve en la mañana.

  Menos del 1 % empieza a las 15:00 o después: una visita larga que empieza antes, como la caminata a la Laguna Churup, de 9:00 a 15:00.
- **El bus de noche** lleva el 29 % de los viajes propuestos: el 48 % de los de dos días y el 60 % de los de tres o cuatro. Su mediana es de 9,7 horas.
- **Cambia lo que se propone.** Dos días desde el Cusco son Puno en bus de noche, Urubamba y Yanque: Machu Picchu sale con «Historia», no sin intereses. Dos días desde Lima son Huaraz en bus de noche, Huacho y Nasca. Las pruebas de lo conocido lo dicen así.
- **Con destino, desde Lima en julio:**
  - en avión, el Cusco, Arequipa, Chachapoyas, Puerto Maldonado, Tarapoto, Cajamarca, Puno e Iquitos salen en dos días; Máncora, en tres; Machu Picchu y el Colca, en cuatro;
  - en bus de noche, Huaraz y Nasca salen en dos días; Trujillo y Ayacucho, en tres.
- **El contrato pasa a la 1.6.** `Dia.almuerzo`, `traslado.bus_de_noche`, `dias_de_viaje` en 0 con bus de noche, la hora de una parada después del almuerzo y los km del bus en `indicadores.km_total`. Cambian dos cosas del sentido: `dias` y `fecha_inicio`, con bus de noche. Hay dos propiedades nuevas, la 12 (el almuerzo) y la 13 (el bus de noche), y la 9 tiene ahora la excepción del avión.
- **La consulta tarda lo mismo:** unos 340 ms en la mediana.
- **Lo que todavía no hace:**
  - no conoce los horarios de los buses, solo la hora que deja llegar a eso de las 6:00;
  - no sabe si el lugar donde se come está abierto;
  - una visita larga que empieza antes del almuerzo lo corre hasta que termina;
  - el bus de noche no se cobra aparte del de día.

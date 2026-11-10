# 0020 · Un primer día tranquilo en la altura

**Fecha:** 20 de octubre de 2026 · **Estado:** vigente · Amplía la [0009](./0009-viaje-en-estrella.md) y la [0019](./0019-plan-creible.md), comparte la regla de la [0018](./0018-planes-de-noche.md), completa la altura de las bases que usa la [0006](./0006-clima-por-polo.md) y suma `Dia.tranquilo` al [contrato](../CONTRATO.md) (versión 1.7)

## Contexto

El aviso de aclimatación decía «conviene un primer día tranquilo», y el plan no lo daba. De Lima a Huaraz, con tres días, el bus de noche llegaba a las 5:55 y el día 1 empezaba a las 8:53 en el Parque Nacional Huascarán: 4 453 m, 1 392 m sobre la base y tres horas de visita. En 300 consultas al azar, de 2 a 8 días, 196 viajes dormían a 2 500 m o más y llegaban desde 1 000 m o más abajo. Su primer día con visitas tenía 7,5 horas de jornada en la mediana, y 24 de ellos subían más de 500 m sobre la base.

Además, 13 de las 194 bases no tenían altura, y tres de ellas están sobre los 4 300 m. En ellas no había aviso ni regla, y la altitud máxima de la consulta no las filtraba.

## Decisión

- **Cuándo pesa la altura:** si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, en bus, en bus de noche o en avión. Es la regla de la noche de descanso de la 0018, ahora en un solo lugar ([`dreemgo/motor/aclimatacion.py`](../../dreemgo/motor/aclimatacion.py)), para que el día y la noche nunca se contradigan. Desde Puno no pesa nunca, y desde el Cusco, solo en tres bases sobre los 4 400 m: Imata, Marcapomacocha y Santa Inés.
- **El primer día en la base es tranquilo:** el de llegada, si queda tiempo para visitar, o el siguiente.
  - Medio día como mucho: 4 horas, más el almuerzo.
  - Ninguna parada a más de 500 m sobre la base.
  - Nada exigente: ni una caminata de acceso de más de 30 minutos ni una visita de más de 2 horas, como un parque nacional.
  - Después de un bus de noche, desde las 9:00.
- **La fuente** es el Yellow Book del CDC, edición 2026 (*High-Altitude Travel and Altitude Illness*, de Hackett y Shlim). Corre riesgo quien duerme a 2 450 m o más sin estar aclimatado. En las primeras 48 horas aconseja solo ejercicio suave y nada de alcohol, y sobre los 3 000 m, no subir más de 500 m por noche la altura donde se duerme. Los 500 m del día son un supuesto del producto, con esa misma medida.
- **En el planificador,** la jornada tranquila no admite paradas exigentes ni más altas que la base más 500 m. Se filtran al elegir a qué jornada puede ir cada una, antes de armar un horario.
- **El aviso dice lo que hace el plan:** «El día 1 es tranquilo: medio día de visitas como mucho, sin subir más de 500 m sobre Huaraz ni caminatas largas, para que el cuerpo se acostumbre». Si se llega desde la altura, sigue como estaba.
- **El contrato 1.7** suma `Dia.tranquilo`, y la app lo nombra en la lista de días, en el día y en el plan impreso. La propiedad 14 lo verifica. La propiedad 1 cuenta ahora también la base: con altitud máxima, una base sin altura no entra.
- **La altura de las bases:** donde OpenStreetMap no la trae, sale del modelo de elevación de Terrain Tiles, del registro de datos abiertos de AWS. En el Perú es SRTM, a un segundo de arco, y se toma la mediana de 5 × 5 puntos alrededor de la base ([`pipeline/elevacion.py`](../../pipeline/elevacion.py)). El clima usa esa misma altura para llevar sus temperaturas a la de la base.

## Alternativas descartadas

- **Un día entero suave,** con los mismos límites de altura y de caminata: seguía siendo un día entero.
- **Un día libre,** sin visitas: les quitaba un día entero a los viajes cortos.
- **Aplicarlo siempre que se duerma a 2 500 m o más,** venga de donde venga el viajero: le quitaba medio día a quien ya vive en la altura, como al ir del Cusco a Puno.
- **Decirlo solo en la nota del día:** la app no podía nombrar el día en la lista ni en el plan impreso.
- **Dejar sin altura las 13 bases,** con un aviso de que no se sabe: la regla no aplicaba en Imata, a 4 449 m, ni en Santa Inés, a 4 613.
- **La mediana de los lugares cercanos** en las 11 bases que la usaban: difiere del modelo en 28 m en la mediana y en 137 como mucho. La de OpenStreetMap, en 1 m y en 26, así que esa se queda.

## Consecuencias

- **El primer día en la altura,** en las mismas 300 consultas: 180 viajes duermen en la altura y llegan de abajo. Su primer día con visitas tiene 3,7 horas en la mediana, contando el camino del día de llegada. Ninguno sube más de 500 m sobre la base (antes, 24), lo más que sube son 350 m y la visita más larga dura 2 horas (antes, 3).
- **Cambia lo que se propone:**
  - en 21 de las 300 consultas (7 %) cambian las zonas, y en otras 24, solo su orden;
  - en 111, las mismas zonas salen con otro itinerario;
  - la que más deja de salir es Puno, en 10 consultas, y la que más entra, Arequipa, en 5, que queda a 2 347 m y no tiene día tranquilo: medio día menos de visitas le baja el puntaje a una zona en la altura cuando el viaje es corto;
  - Huaraz sigue saliendo un fin de semana desde Lima, y Machu Picchu desde el Cusco con «Historia».
- **Datos `2026.10.8`:** las 13 bases que no tenían altura la toman del modelo (siete quedan a 2 500 m o más), y otras 11 la cambian por la del modelo. Las temperaturas de 23 polos cambian, porque se llevan a la altura de su base. La que más, Villa Pampilla: su punto de clima está a 3 799 m y su base a 1 665 m, y sus temperaturas suben 13,9 °C. Los veredictos del mes no cambian.
- **La consulta tarda lo mismo:** 437 ms en la mediana, frente a 427 antes, en la misma máquina.
- **Lo que todavía no hace:**
  - el día tranquilo es uno solo, aunque el CDC habla de las primeras 48 horas;
  - de cada lugar sabe solo la caminata de acceso que dice su ficha, no cuánto se camina adentro;
  - la altura del origen es la de la base de su zona, no la de la ciudad;
  - en una ida larga por tierra no mira a qué altura se duerme en el camino.

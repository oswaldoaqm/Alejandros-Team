# Cómo calificar los viajes · semana 12

Con estas calificaciones medimos si DreemGO propone buenos viajes: si le gana a una guía de viajes y si un cambio que estamos pensando lo mejoraría ([decisión 0021](../decisiones/0021-evaluacion-semana-12.md)). Lo que importa es tu juicio honesto, como alguien que conoce el Perú y que le recomendaría un viaje a otra persona.

Son **40 personas** con un viaje en mente, escritas a mano para cubrir lo que el producto promete: de dónde salen, cuántos días tienen, cuándo, qué les gusta y, si lo dijeron, cuánto pueden gastar o hasta qué altura pueden subir. Para cada una hay **de 3 a 6 viajes**, 185 en total. Salen del motor y de otras maneras de elegir zonas; no se dice cuál es cuál, y el orden está mezclado, para que no influya.

## Lo que hay que hacer

1. Abre `data/evaluacion/cuadernillo.html` con doble clic: se abre en el navegador (Chrome, Edge o Firefox), sin internet. Escribe tus iniciales en el recuadro de arriba.
2. Para cada persona, lee quién es y lo que pidió. Después, cada viaje: dónde se duerme, cómo se llega, qué se hace cada día, cuánto cuesta, cómo es el mes y sus avisos.
3. Califica cada viaje con **2**, **1** o **0** (abajo, cómo decidir). Si quieres, deja un comentario.
4. Cuando termines, aprieta **Descargar** y mándale a Alejandro el archivo que baja, `calificaciones_TUS-INICIALES.csv`.

**Toma unas dos horas**, y no tiene que ser de una vez: el avance se guarda en ese navegador. «Siguiente» te lleva al primer viaje que te falta. Para seguir en otra computadora, descarga tus calificaciones y, allá, usa «Cargar un archivo». Si prefieres una hoja de cálculo, `data/evaluacion/planilla.csv` tiene las mismas filas: llena la columna `calificacion` y guárdala como CSV, con punto y coma.

## Las reglas

- **Por tu cuenta.** No lo comentes con el equipo hasta que los cuatro hayan terminado, ni para ponerse de acuerdo en un caso difícil. Medimos cuánto coinciden cuatro personas que califican por separado; si se ponen de acuerdo antes, esa medida no vale.
- **Sin la app y sin `data/evaluacion/clave.csv`.** La clave dice de dónde sale cada viaje: es para el análisis.
- **Para esa persona, no para ti.** Si a ti te encanta caminar pero ella quiere playa, piensa en ella.
- **Cada viaje por separado.** No es un ranking: pueden salir los seis con 2, o los seis con 0. No le bajes la nota a un viaje porque otro de la misma persona te gusta más.
- **Con lo que dice la tarjeta y lo que sepas del lugar.** Si dudas de un dato, como un horario o un costo, no lo investigues: califica con lo que hay y cuéntalo en el comentario.
- **Nada de datos personales en los comentarios**, ni tuyos ni de nadie.

## Cómo decidir

Mira tres cosas, en este orden:

1. **¿Encaja con lo que pidió?** Sus intereses, sus días, el mes, su presupuesto, su altura máxima y, si lo dijo, que no quiere volar.
2. **¿Vale la pena?** Que los lugares sean buenos para lo que quiere y que el camino no se coma el viaje.
3. **¿Se puede hacer así?** Que los horarios, los traslados y el costo sean creíbles.

| Nota | Quiere decir | Por ejemplo |
|---|---|---|
| **2** · Sí, tal cual | Se lo propondrías sin cambiarle nada importante. | Pidió playa en verano, cuatro días: el viaje tiene tres días de playa en una zona linda, se llega en una mañana y entra en su presupuesto. |
| **1** · Puede servirle, con reparos | Tiene cosas buenas, pero algo pesa: le das el viaje con un «pero». | El mismo viaje, pero con solo una playa entre seis lugares; o se pasa un poco del presupuesto; o el mes es de lluvias suaves; o el camino se lleva medio viaje. |
| **0** · No encaja | No se lo darías. | Pidió playa y no tiene ninguna; o es en plena temporada de lluvias para caminar; o cuesta el doble de lo que tiene; o algo lo arruina, como un día imposible. |

Los casos que más dudas dan:

- **Un lugar famoso que no es lo que pidió.** Si no tiene nada de lo que pidió, es 0 aunque sea Machu Picchu. Si tiene algo, 1 o 2 según cuánto.
- **Sin intereses marcados.** Juzga si es un buen viaje para esa persona, en esos días y en ese mes.
- **«Sorpréndeme».** Lo que pidió es salir de lo conocido: un viaje a lo de siempre no la sorprende.
- **El costo.** Es una estimación, en una banda: la cifra del medio es la más probable. Si entra en su presupuesto, la tarjeta lo dice.
- **Los avisos** (la altura, el día tranquilo, un camino largo) son parte del viaje: piensa si a esa persona le importan.
- **Un error en la tarjeta**, como un lugar que no está donde dice o un horario imposible: califica como lo vería esa persona y cuéntalo en el comentario. Esos comentarios son de lo más útil que puede salir de aquí.

## Lo que dice cada tarjeta

- **★** marca un imperdible: un lugar de jerarquía 3 o 4 en el inventario de MINCETUR, de lo más valioso del país.
- **Día tranquilo, por la altura:** el primer día en una base a 2 500 m o más, si se llega desde abajo. Medio día de visitas, sin subir mucho más ni caminatas largas ([decisión 0020](../decisiones/0020-primer-dia-tranquilo.md)).
- **Bus de noche:** la ida y la vuelta van de noche, fuera de los días del viaje.
- **De noche:** el plan de esa noche, si lo hay: salir o mirar las estrellas.

## Después

Alejandro guarda los cuatro archivos en `data/evaluacion/calificaciones/`, uno por persona, con sus iniciales como nombre (`AB.csv`). Con ellos sale el informe de la semana 12: cuánto coinciden los cuatro (kappa de Fleiss) y, con la nota de cada viaje, cuánto aciertan el motor, la guía y la variante en sus tres primeros (nDCG@3, P@3 y MRR).

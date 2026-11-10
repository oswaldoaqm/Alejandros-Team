# La prueba de usabilidad · semana 12

La lleva Chris. Cinco personas usan la app de verdad, con tareas de viajero, mientras alguien mira y anota, y al final llenan el cuestionario SUS. Lo que se busca son los tropiezos: dónde alguien se pierde, duda o hace algo distinto de lo que esperábamos. Con cinco personas salen la mayoría de los problemas grandes; no alcanza para cifras finas, y así se dice en el informe ([decisión 0021](../decisiones/0021-evaluacion-semana-12.md)).

## Quiénes

- **Cinco personas fuera del equipo**, mayores de edad, que hayan viajado por el Perú. Mejor si no son todas de la UTEC ni todas de Lima.
- **Al menos tres en celular**, que es como se usa sobre todo, y las otras en computadora.
- Cada sesión, de unos 25 minutos, con una persona a la vez.

## Antes de cada sesión

- La app es la desplegada: <https://oswaldoaqm.github.io/Alejandros-Team/>. Un minuto antes, abre <https://alejandros-team.onrender.com/v1/salud>: el API se duerme cuando nadie lo usa y la primera consulta tarda cerca de un minuto. Si `version_datos` no dice `2026.10.8`, avísale a Alejandro antes de empezar: la prueba es con lo que está desplegado.
- En el celular o la computadora de la prueba, abre la app en una ventana privada, para que no haya viajes guardados de antes.
- Ten a mano las tareas impresas o en otra pantalla, un cronómetro y `data/evaluacion/usabilidad/`, donde se anota.

## Lo que se le dice al empezar

> Gracias por ayudarnos. Vamos a probar DreemGO, una app para planear viajes por el Perú que hicimos para un curso de la UTEC. No te estamos evaluando a ti, sino a la app: si algo no te sale, es culpa de la app, y eso es justo lo que queremos encontrar. Te voy a pedir cinco cosas, como si fueras a viajar, y que pienses en voz alta mientras las haces: qué buscas, qué esperas que pase, qué te confunde. Al final hay diez preguntas cortas. Son unos 25 minutos. No guardamos tu nombre ni ningún dato tuyo: solo un código, lo que hiciste y tus respuestas. Puedes parar cuando quieras. ¿Empezamos?

Si dice que sí, empieza. No le expliques la app antes ni durante: lo que se mide es lo que entiende sola.

## Las tareas

Léelas tal cual, una por una, sin nombrar botones ni pantallas. El tiempo corre desde que terminas de leer hasta que da la respuesta o dice que terminó.

| Tarea | Lo que se lee | Se logra si |
|---|---|---|
| **T1** · Buscar | «Vives en Lima y tienes tres días libres en julio. Te gustan la historia y la naturaleza, y puedes gastar hasta 700 soles. Busca un viaje.» | Llega a los viajes propuestos con Lima, julio, 3 días, historia y naturaleza y S/ 700. |
| **T2** · Elegir | «De los viajes que te propone, ¿cuál te saldría más barato? ¿Y cuál tiene mejor clima en esa época?» | Las dos respuestas coinciden con lo que muestra la app. |
| **T3** · El plan | «Abre el viaje que más te guste. ¿Qué harías el segundo día? ¿A qué hora sales el primero?» | Nombra lugares del día 2 y da la hora de salida del día 1. |
| **T4** · Cambiar | «Tu abuela va contigo y el médico le dijo que no suba de 3 000 metros. Cambia la búsqueda para que la app lo tenga en cuenta.» | Pone la altura máxima en 3 000 m y vuelve a ver viajes. |
| **T5** · Compartir | «Quieres mandarle a una amiga el viaje que elegiste, para que lo vea en su celular. Hazlo.» | Copia o comparte el enlace del viaje. No hace falta mandarlo de verdad. |

Si sobra tiempo, una más: **T6** · «¿Hay alguna fiesta en la zona en las fechas de tu viaje?». Se logra si encuentra las fiestas del viaje o dice, con razón, que no hay.

**Si se atasca:** a los dos minutos sin avanzar, dale una pista corta («¿dónde crees que se cambia eso?») y anótalo «con ayuda». Si a los dos minutos más no sale, pasa a la siguiente y anótalo «no». No corrijas ni expliques: si da una respuesta equivocada, anótala así.

## Después de las tareas

1. **El SUS.** Que responda sola, en papel o en un formulario sin su nombre, cada frase del 1 (muy en desacuerdo) al 5 (muy de acuerdo). Que conteste todas, aunque dude: si no sabe, el 3.
2. **Dos preguntas abiertas:** «¿Qué fue lo más útil?» y «¿Qué cambiarías primero?». Anota sus palabras, cortas.
3. Agradécele. Si pregunta cómo le fue, la respuesta es que la que se probó fue la app.

### El cuestionario SUS

1. Creo que me gustaría usar esta app con frecuencia.
2. Encontré la app innecesariamente complicada.
3. Pensé que la app era fácil de usar.
4. Creo que necesitaría el apoyo de alguien que sepa de tecnología para poder usar esta app.
5. Encontré que las distintas partes de esta app estaban bien integradas.
6. Pensé que había demasiadas cosas inconsistentes en esta app.
7. Imagino que la mayoría de la gente aprendería a usar esta app muy rápido.
8. Encontré la app muy engorrosa de usar.
9. Me sentí muy segura o seguro usando la app.
10. Necesité aprender muchas cosas antes de poder arrancar con esta app.

Es el SUS de John Brooke (1996), con «la app» en vez de «el sistema». **La traducción es nuestra y no está validada.** Hay una versión en español validada, de Sevilla-Gonzalez y colegas (*JMIR Human Factors*, 2020, 7(4):e21161, [doi:10.2196/21161](https://doi.org/10.2196/21161)), con licencia CC BY 4.0: si puedes abrir su anexo, usa sus frases en vez de estas y avísale a Alejandro, para que el informe diga cuál se usó. Lo que no se cambia es el orden ni la escala: las frases impares son positivas y las pares, negativas, y así se calcula el puntaje.

## Dónde se anota

En `data/evaluacion/usabilidad/`, una fila por persona o por tarea, separadas por punto y coma. Ninguna lleva nombre, correo, teléfono ni nada que identifique a nadie: solo el código, de P1 a P5.

- `participantes.csv`: el código, el dispositivo (`celular` o `computadora`), la fecha y cuántos viajes hace por el Perú al año (`0-1`, `2-3` o `4+`).
- `tareas.csv`: por cada persona y tarea, el resultado (`sola`, `con_ayuda` o `no`), los segundos, cuántas veces tomó un camino equivocado y lo que viste o dijo.
- `sus.csv`: sus diez respuestas, del 1 al 5.
- `comentarios.csv`: sus respuestas a las dos preguntas abiertas.

No se graba ni la cara ni la voz. Si alguien prefiere que no anotes algo, no lo anotas.

## Cómo sale el puntaje

Por persona: a cada frase impar se le resta 1 a la respuesta; a cada par, la respuesta se le resta a 5; se suma todo y se multiplica por 2,5. Queda de 0 a 100. El informe da el de cada persona, la media y el rango, junto con 68, que es la media de cientos de estudios (Sauro, 2011), y con la escala de adjetivos de Bangor, Kortum y Miller (2009). Con cinco personas el margen es grande: el puntaje orienta, y lo que más sirve son los tropiezos de cada tarea.

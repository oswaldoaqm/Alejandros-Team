# 0028 · El horario y la visita, corregidos con su fuente

**Fecha:** 12 de noviembre de 2026 · **Estado:** vigente · Suma `abre`, `cierra` y `dias` a `Recurso` en el [contrato](../CONTRATO.md) (versión 1.8), con la propiedad 16, y responde a los puntos 3, 4 y 5 de la [auditoría](../AUDITORIA.md)

## Contexto

La auditoría del 5 de noviembre encontró casos en que la ficha, o la tabla del equipo, no dice lo que pasa allá:

- El Circuito Mágico del Agua salía 390 veces en la rejilla, siempre a las 10:51. Su ficha dice que abre de 7:00 a 22:30, y abre de 15:00 a 22:00, de miércoles a domingo.
- La visita sale de una tabla por subtipo, que es un supuesto del equipo. El 23 % de las visitas a lugares de jerarquía 3, y el 24 % de las de jerarquía 4, duraban 30 minutos o menos: Moray, 30; el Centro Histórico de Trujillo, 20, porque su ficha lo pone en el subtipo «Otros», con otras cuatro zonas monumentales, las del Callao, Pueblo Libre, Ancón y Yanahuara.
- Ningún viaje a Puno iba a los Uros. Su ficha no les da jerarquía, así que valían como un lugar de jerarquía 2, y se visitan en lugar de la Reserva Nacional del Titicaca, de jerarquía 4, que no tiene camino en la red.
- La app no mostraba el horario de ningún lugar, y sin fecha, que es lo normal en el formulario, el motor no revisa qué días cierra cada uno.

## Decisión

- Un horario corregido, con su fuente, manda sobre el de la ficha ([`horarios_corregidos.csv`](../../pipeline/referencia/horarios_corregidos.csv)), y el maestro dice de dónde sale cada horario (`horario_fuente`). Hoy hay uno: el del Circuito Mágico (How to Peru, julio de 2026).
- La visita puede tener una fila por recurso en [`duracion_visita.csv`](../../pipeline/referencia/duracion_visita.csv), que manda sobre la del subtipo: las cinco zonas monumentales del subtipo «Otros» van con los 90 minutos de los centros históricos. Y desde la jerarquía 3, la visita dura una hora como mínimo. Es un supuesto y así queda escrito: no hay una fuente oficial de tiempos de visita.
- Los Uros valen como la Reserva Nacional del Titicaca ([`valor_por_acceso.csv`](../../pipeline/referencia/valor_por_acceso.csv)), con 90 minutos de visita, como miden las excursiones desde Puno (My Guide Peru, Civitatis). Su jerarquía oficial no cambia: el motor usa `vale_como_jerarquia`.
- El contrato pasa a la 1.8. Cada parada trae su horario y los días que abre, y la propiedad 16 verifica que se visite dentro de su horario y, si hay fecha, un día que abre. La app muestra el horario en la hoja de cada lugar y, en su fila del plan, si cierra algún día de la semana.
- `python -m pipeline.maestro --solo-referencias` rehace lo que sale de las referencias sin volver a leer las fichas.

## Alternativas descartadas

- Corregir el horario o la visita a mano en el maestro: la próxima corrida del pipeline lo borraría, y no quedaría la fuente.
- Subirles la jerarquía a los Uros: la jerarquía es de MINCETUR.
- Valer los Uros como jerarquía 3 y no como la reserva. En una prueba a mano con el motor de ahora, Puno quedaba primero en 2 de las 40 consultas del kit y no en 7, y 24 de 28 viajes a Puno igual pasaban por los Uros. Se descartó para no inventar una jerarquía intermedia; ver las consecuencias.
- Revisar uno por uno los tiempos de visita de los lugares más propuestos: no alcanza el tiempo antes de la entrega. El mínimo por jerarquía arregla los casos que más se ven y queda a la vista como supuesto.

## Consecuencias

- Con los datos `2026.11.2`, 41 recursos cambian su tiempo de visita. En la rejilla ya no hay visitas de 30 minutos o menos a lugares de jerarquía 3 o 4, y la mediana de la jerarquía 3 sube de 66 a 76 minutos.
- El Circuito Mágico sale 277 veces, y se llega entre las 14:56 y las 15:30: a la hora en que abre, pero de día. Ponerlo en la noche del viaje, cuando se encienden las fuentes, queda pendiente.
- Los viajes a Puno van a los Uros, y Puno pasa del 8,0 al 12,7 % de los viajes de la rejilla. Con el motor de ahora, Puno queda primero en 7 de las 40 consultas del kit, donde antes iban otras zonas con nota media de 1,52; las notas de Puno en esas consultas promedian 0,83, aunque son de viajes que no iban a los Uros ([`resultados.md`](../evaluacion/resultados.md)). Los comentarios hablan del frío, la altura, la lluvia de febrero y de un viaje «contemplativo», que los Uros no cambian. Queda a la vista para la próxima calibración del puntaje.
- Con la hora mínima, un lugar de jerarquía 3 rinde por minuto lo mismo que uno de jerarquía 2 de 20 minutos, y el día se llena de lugares menores: en Lima, los días con seis paradas suben del 69 al 87 %.
- Sin fecha, el motor sigue sin revisar los días de cierre. Con fecha sí los revisa, y la app los muestra siempre.

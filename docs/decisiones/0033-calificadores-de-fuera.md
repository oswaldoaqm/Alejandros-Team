# 0033 · Calificadores de fuera del equipo

**Fecha:** 15 de noviembre de 2026 · **Estado:** en curso: faltan las notas · Responde al punto 12 de la [auditoría](../AUDITORIA.md)

## Contexto

Las 196 notas del kit las pusieron tres de los cuatro que hicieron el producto (0021). Un jurado puede decir que el equipo se califica a sí mismo: que el motor sale mejor que la guía porque quien lo hizo le pone mejores notas.

## Decisión

- Un kit corto con 10 de las 40 consultas, elegidas al azar con una semilla fija: la 3, 14, 15, 18, 21, 24, 29, 31, 33 y 39, con 50 viajes, unos 20 minutos (`python -m evaluacion.kit_externo`). Es el mismo cuadernillo, con la guía escrita para alguien de fuera, sin mencionar la app ni la clave, y con su propia memoria en el navegador.
- Lo califican de 3 a 5 personas que no son del equipo. Cada archivo va a `data/evaluacion/externos/calificaciones/`, con las iniciales de quien califica y nada más.
- `python -m evaluacion.externos` compara, viaje por viaje, la nota media de fuera con la del equipo, con un intervalo de 95 % por bootstrap sobre las consultas, y calcula el nDCG@3 del motor y de la guía con las notas de fuera.

## Cómo se lee

- Si la diferencia equipo menos fuera tiene un intervalo que no pasa por cero y es positiva, el equipo se calificó mejor que quien no hizo el producto, y las cifras de [`resultados.md`](../evaluacion/resultados.md) se leen con eso.
- Si el motor sigue por encima de la guía con las notas de fuera, la conclusión de la 0021 no depende de quién calificó.
- Con 10 consultas y pocas personas, el intervalo va a ser ancho. Se dice tal cual, sin estirar la conclusión.

## Alternativas descartadas

- Las 40 consultas: son unas dos horas, y nadie de fuera las califica bien antes de la entrega.
- Elegir las consultas en que el equipo no se puso de acuerdo: mediría otra cosa, y el kit dejaría de ser una muestra del total.

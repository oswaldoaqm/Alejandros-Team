# 0022 · El presupuesto avisa cuando el escenario caro lo pasa, y no deja fuera ningún viaje

**Fecha:** 27 de octubre de 2026 · **Estado:** vigente · Responde la pregunta que dejó el [informe de la semana 10](../../deliveries/week10/PrototypeReport.md) después de la revisión del profesor, y precisa la propiedad 7 del [contrato](../CONTRATO.md) sin cambiar sus campos

## Contexto

En su revisión del 20 de octubre, el profesor armó una copia del motor que deja fuera lo que no cabe en el presupuesto, comparándolo con el P50 o con el P80. Con Lima, julio, cuatro días y S/ 800, la lista cambiaba según el criterio: Huaraz, Huacho y Nasca con el P50; Trujillo, Huánuco y Pozuzo con el P80. El motor desplegado hace otra cosa: compara el presupuesto con el P50, castiga en el puntaje al viaje que lo pasa y lo muestra con su aviso, pero no lo esconde. El informe de la semana 10 dejó la decisión para la semana 12.

`evaluacion/presupuesto.py` midió qué cambia con cada filtro, con el mismo motor, en las 8 consultas de la evaluación que traen presupuesto y en las 40 con cuatro montos por persona:

| Consultas | Viajes de hoy que pasan el monto en el P50 | En el P80 | Sin ningún viaje con filtro P50 | Con filtro P80 |
|---|---|---|---|---|
| Las 8 con presupuesto | 6 de 24 | 8 de 24 | 2 de 8 | 2 de 8 |
| Las 40, con S/ 800 | 51 de 120 | 72 de 120 | 13 de 40 | 18 de 40 |
| Las 40, con S/ 1 200 | 18 de 120 | 34 de 120 | 3 de 40 | 6 de 40 |

Con S/ 800 por persona, el filtro P80 cambia las propuestas de 27 de las 40 consultas y deja 18 sin nada. Y el costo es una banda del percentil 20 al 80 sobre rangos de precios sin calibrar con viajes reales: el P80 es un escenario, no un precio.

## Decisión

- **El presupuesto no deja fuera ningún viaje.** Sigue como estaba: se compara con el P50, castiga en el puntaje al que lo pasa y le pone su aviso de nivel `advertencia`.
- **Si el costo central entra y el P80 no, el viaje sale con un aviso** de tipo `presupuesto` y nivel `info`: «El costo central (S/ 622) entra en tu presupuesto, pero si los precios salen altos el viaje llega a S/ 704: S/ 54 más. Lleva un margen.» Es el viaje a Huaraz de las dos amigas de la evaluación, con S/ 650.
- **La propiedad 7 lo verifica** sobre consultas al azar: con el P50 fuera, un aviso de `advertencia`; con el P50 dentro y el P80 fuera, uno de `info`; con los dos dentro, ninguno.

## Alternativas descartadas

- **Filtrar con el P80,** como la copia del profesor: deja sin viaje a casi la mitad de las consultas con S/ 800, por un escenario que no está calibrado.
- **Filtrar con el P50:** deja sin viaje a 13 de 40, y esconde viajes que pasan el monto por pocos soles.
- **Dejarlo como estaba:** con S/ 800, 21 de los 120 viajes entran en el P50 y pasan en el P80, y la app no lo decía.

## Consecuencias

- **No cambia qué zonas se proponen ni en qué orden.** El kit de la evaluación y las calificaciones del equipo siguen valiendo.
- **El aviso sale en «Antes de ir»,** con los demás avisos del viaje. La app no cambia.
- **Depende de un P80 sin calibrar.** Calibrar el costo con el camino real está en el plan de las tres semanas que quedan, en la entrega de la semana 12. Hasta entonces, el aviso dice «si los precios salen altos» y no lo presenta como un precio.

# 0015 · Un viaje no pasa más días en el camino que allá

**Fecha:** 8 de octubre de 2026 · **Estado:** vigente · Ajusta la [0009](./0009-viaje-en-estrella.md)

## Contexto

La calidad de un viaje es el valor de lo que visita frente al mejor de la consulta, y los días que se van en el camino no cuentan ni a favor ni en contra. Con el valor de la [0013](./0013-un-polo-por-pueblo.md) y el día de viaje de la [0014](./0014-dia-de-solo-viaje.md), un lugar lleno de imperdibles le ganaba a todo aunque quedara lejos. «Lima, 9 días» proponía el Cusco con seis días de bus y tres allá, y «Iquitos, 9 días», Tarapoto con ocho días de río y uno allá. En la rejilla del informe eran 307 de 3 408 rutas, el 9 %; antes de esas dos decisiones, el 2,6 %.

## Decisión

- **No se propone un viaje que pasaría más días solo viajando que días en que se puede visitar** ([`dreemgo/motor/viaje.py`](../../dreemgo/motor/viaje.py), `mas_camino_que_visita`). Un empate sí: a Huaraz con cuatro días, dos de viaje y dos allá.
- Es una regla y no un descuento: no cambia el orden de los viajes que sí caben.

## Alternativas descartadas

| Variante | Machu Picchu | Huaraz | Fuera del circuito | Más días de camino que de visita |
|---|---:|---:|---:|---:|
| Sin regla, con la 0013 y la 0014 | 9 | 64 | 74 % | 9 % |
| **Con la regla** | **9** | **70** | **77 %** | **0 %** |
| La calidad, por la parte de los días con visitas | 13 | 35 | 79 % | 1,3 % |
| La calidad, por la parte de las horas que no se van en ir y volver | 5 | 42 | 82 % | 1,9 % |

- **Descontar el camino en la calidad** cuenta dos veces el viaje: el valor ya baja cuando quedan menos días allá. Con cualquiera de los dos descuentos, Huaraz deja de salir primero desde Lima con cuatro y con seis días.

## Consecuencias

- «Lima, 9 días» propone Trujillo, Huaraz y Cajamarca. Por tierra, el Cusco desde Lima solo cabe con doce días o más; con menos, hacen falta vuelos, que son de la fase 4.
- 12 consultas de Iquitos con 9 días dan dos rutas en vez de tres: las que salen eran de ocho días de río y uno allá.
- El aviso «La ida y la vuelta se llevan…» sigue donde el camino pesa: lo llevan 36 de cada 100 rutas, frente a 43 sin la regla y 27 antes de la 0013.

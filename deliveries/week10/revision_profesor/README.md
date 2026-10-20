# La revisión del profesor · 20 de octubre de 2026

El profesor revisó lo que estaba en `main` hasta el 19 de octubre, con los datos `2026.10.4`, en una copia de trabajo aparte, sin tocar este repositorio. En esa copia, el presupuesto se compara con el costo central (P50) o con el escenario conservador (P80), y deja fuera lo que no cabe. Nos pidió:

1. comparar las dos listas para Lima, julio, cuatro días y S/ 800;
2. en P50, abrir Huacho, bajar su hoja de verificación y marcar dos filas de cobro desconocido como «Pendiente de confirmar», sin completar horarios, tarifas ni fechas;
3. explicar qué cambia entre los dos criterios y por qué el costo no es definitivo.

Todo sale de su demo sin instalar, con los ejemplos que trae. La hoja es la que baja su botón, byte por byte, con dos celdas de **Observaciones** llenas: [`dreemgo_verificar_70_revisada.csv`](./dreemgo_verificar_70_revisada.csv). Lo explica también la diapositiva 21 de la [presentación](../PresentationWeek10.pdf).

## Las dos listas

| Criterio | Destinos | Costo según el criterio |
|---|---|---|
| P50, costo central | Huaraz, Huacho y Nasca | S/ 706, S/ 773 y S/ 793 |
| P80, escenario conservador | Trujillo, Huánuco y Pozuzo | S/ 768, S/ 758 y S/ 730 |

**Qué cambia con P80.** El escenario conservador suma unos S/ 110 a cada viaje. Huaraz, Huacho y Nasca pasan los S/ 800 (S/ 816, S/ 887 y S/ 905), y entran los siguientes que caben: Trujillo, Huánuco y Pozuzo, que tienen menor puntaje (0,60, 0,56 y 0,42, contra 0,75, 0,72 y 0,70).

**Por qué el costo de Huacho no es definitivo.** De sus 18 paradas, 8 no tienen información de cobro, y el modelo no les suma nada: desconocido no significa gratis. P50 y P80 salen de 4 000 simulaciones con rangos de transporte, hospedaje y comida sin calibrar con viajes reales: son escenarios, no cotizaciones. Y ningún horario, tarifa ni apertura está confirmado.

## Las dos filas revisadas

| Lugar | ID MINCETUR | Llegada estimada | Cobro en catálogo | Observaciones |
|---|---|---|---|---|
| Zona Arqueológica Monumental de Peñico | 11873 | Día 3, 10:05 | desconocido | Pendiente de confirmar |
| Museo Municipal de Hualmay | 11211 | Día 2, 11:36 | desconocido | Pendiente de confirmar |

Elegimos un sitio arqueológico y un museo porque, en ese mismo viaje, cuatro de los cinco sitios arqueológicos y museos con dato en el catálogo cobran entrada, de S/ 5 a S/ 11 (Caral, Vichama, Paramonga y el Museo de Huaura). Las columnas de horario, tarifa, fecha y fuente confirmados quedan vacías: el catálogo no las verifica.

## Y en la app de hoy

La app de este repositorio, con los datos `2026.10.8`, hace otra cosa, a propósito: el presupuesto se compara con el P50 y entra a elegir, pero no esconde ningún viaje; el que pasa el monto sale con su aviso (propiedad 7 del [contrato](../../../docs/CONTRATO.md)). Con S/ 800 salen Trujillo, Huaraz y Huánuco, en bus de noche. Filtrar con P80, como en la copia, cambiaría esa propiedad: queda para decidirlo en la semana 12.

En la copia, el último día en Huacho esperaba hasta las 18:00, cuando abre su primera parada, y llegaba a la playa a las 19:30. Desde la [decisión 0019](../../../docs/decisiones/0019-plan-creible.md), la jornada no se corre y no se espera más de una hora en la puerta de un lugar.

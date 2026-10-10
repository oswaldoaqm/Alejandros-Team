# 0013 · Un polo por pueblo, y un valor que distingue lo imperdible

**Fecha:** 7 de octubre de 2026 · **Estado:** vigente · Ajusta la [0009](./0009-viaje-en-estrella.md). La [0015](./0015-mas-dias-alla-que-en-el-camino.md) corrige los viajes que se iban en el camino

## Contexto

En las 1 152 consultas con que el informe de la semana 10 mide al motor, ninguna ruta dormía en Machupicchu Pueblo ni en Huaraz. Se midió por qué, variante por variante, con el motor de verdad:

- **Huaraz era la base de cuatro grupos de TA-01.** Competían entre sí como destinos distintos y ninguno juntaba lo mejor de la Cordillera Blanca. Había 22 pueblos así, con 50 grupos.
- **Una parada valía 1, 2, 4 u 8 según su jerarquía.** Seis lugares de jerarquía 2, que caben en un día, valían más que Machu Picchu.
- **La novedad no era la causa**, aunque el informe lo decía: sin ella (λ = 0) tampoco salían.
- **Machu Picchu queda a 24,6 horas de Lima por tierra.** Desde la mayoría de las ciudades no cabe en los días del viaje, y eso no lo arregla el puntaje.

## Decisión

- **Un polo es lo que se visita desde un pueblo.** Los grupos de TA-01 que eligen la misma base son un solo polo, con el número del menor: de 222 grupos quedan 194 polos ([`pipeline/tiempos.py`](../../pipeline/tiempos.py)). La base no cambia, y los tiempos entre paradas de grupos distintos se calculan sobre la red, como los demás.
- **El agrupamiento de la semana 6 no se toca.** El maestro y los eventos siguen guardando el grupo de cada recurso; `grupos`, en `polos_bases.csv`, dice qué grupos junta cada polo.
- **El clima de un polo que junta grupos** es el de su grupo con más paradas que ya esté descargado.
- **Una parada vale 1, 2, 6 o 24 según su jerarquía:** de un nivel al siguiente se multiplica por 2, por 3 y por 4. Una de jerarquía 4 vale lo que doce de jerarquía 2, dos jornadas llenas. Sin jerarquía sigue valiendo 2.
- Los artefactos pasan a `2026.10.3`.

## Alternativas descartadas

De las 3 408 rutas de la rejilla, cuántas duermen en cada lugar, cuántas van fuera del circuito de Lima y Cusco, y en cuántas consultas cambia alguna de las tres rutas:

| Variante | Machu Picchu | Huaraz | Fuera del circuito | Consultas que cambian |
|---|---:|---:|---:|---:|
| Como estaba | 0 | 0 | 84 % | |
| Solo juntar los grupos | 0 | 11 | 79 % | 14 % |
| Solo cambiar el valor a 1, 2, 6, 24 | 9 | 0 | 77 % | 54 % |
| Juntar, con 1, 2, 4, 16 | 5 | 20 | 76 % | 37 % |
| **Juntar, con 1, 2, 6, 24** | **9** | **74** | **75 %** | **57 %** |
| Juntar, con 1, 2, 8, 32 | 9 | 91 | 74 % | 67 % |

- **Hacen falta las dos cosas:** juntar sin cambiar el valor casi no trae a Huaraz, y cambiar el valor sin juntar no lo trae nunca.
- **Una escala más empinada** trae más veces a Huaraz, pero cambia dos de cada tres consultas y deja menos polos a la vista: 68, frente a 74.
- **Rehacer el agrupamiento con la base como criterio:** TA-01 es una entrega ya defendida, con su diámetro acotado. Juntar después conserva las dos cosas.

## Consecuencias

- **Machu Picchu** sale desde el Cusco con dos días, de marzo a noviembre. Desde Lima sigue sin salir: hacen falta vuelos y viajes de varios polos (fase 4).
- **Huaraz** sale desde ocho ciudades, entre ellas Lima, Trujillo, Huánuco y Cajamarca, casi siempre entre mayo y setiembre.
- **Las propuestas se concentran:** los polos distintos que aparecen bajan de 83 a 74, y los diez más propuestos pasan de llevarse la mitad de las rutas al 59 %.
- **Los viajes quedan más lejos.** La calidad no descuenta el camino, así que un lugar con muchos imperdibles gana aunque quede lejos. Las rutas con más días de camino que de visita pasan de 3 a 7 de cada 100, y las que llevan el aviso de que la ida y la vuelta se comen el viaje, de 27 a 40.
- **Fuera del circuito:** de la baja de 84 a 75 %, una parte es de definición. Abancay y Cerro de Pasco, ya juntos, tienen algún recurso en las regiones de Cusco o de Lima y dejan de contar como fuera del circuito.
- **Clima:** nueve grupos cambian de veredicto en algún mes al tomar el clima de su polo.
- **El número de 28 grupos deja de ser un polo.** `/v1/polos/43` responde 404. No había API desplegada, así que no hay enlaces en uso.
- **La escala es un supuesto sin calibrar.** Se revisa en la evaluación de la semana 12, con las consultas anotadas por el equipo.
- [`tests/motor/test_lo_conocido.py`](../../tests/motor/test_lo_conocido.py) avisa si un cambio vuelve a sacar a Machu Picchu o a Huaraz de las tres rutas, y [`tests/test_datos.py`](../../tests/test_datos.py), si dos polos vuelven a dormir en el mismo pueblo.

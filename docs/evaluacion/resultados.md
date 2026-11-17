# Lo que dicen las calificaciones del kit

12 de noviembre de 2026. El kit es el de los datos `2026.11.1` y el contrato 1.7, con la huella `490ffe47ecb4`, y se evalúa como lo fijó la [decisión 0021](../decisiones/0021-evaluacion-semana-12.md) antes de calificar. Todas las cifras salen de `python -m evaluacion.informe`: [`resumen.json`](../../data/evaluacion/resultados/resumen.json), [`notas.csv`](../../data/evaluacion/resultados/notas.csv) y [`metricas.csv`](../../data/evaluacion/resultados/metricas.csv).

## Quién calificó

Tres de los cuatro: CP, ME y OAQM, los 196 viajes cada uno ([`calificaciones/`](../../data/evaluacion/calificaciones/)). DI calificó las consultas 1 a 9 y el equipo decidió cerrar sin esperar el resto, así que sus notas no entran.

En tres viajes, el comentario de CP habla de otro lugar que la zona calificada: el 25 D, Chachapoyas, dice «al sur de Lima»; el 25 E, Cajamarca, habla de los museos de Lima, y el 26 D, Los Órganos, del viento de Paracas. Sus notas quedan como están. Si se dejan en blanco, el nDCG@3 del motor pasa de 0,812 a 0,809, y su ventaja sobre la guía, de 0,098 a 0,097.

## El acuerdo

El kappa de Fleiss es 0,22, en los 196 viajes con las tres notas, y el alfa de Krippendorff ordinal, 0,41. Los tres ponen la misma nota en el 27 % de los viajes, y en 25 uno pone 0 y otro 2. OAQM es el más exigente: da 2 al 18 % de los viajes, contra el 40 % de CP y el 38 % de ME.

El kappa queda bajo 0,4. Como lo fijó la 0021 antes de calificar, las cifras que siguen se dan como no concluyentes, y los 25 viajes con un 0 y un 2 se revisan con el equipo: 3D Oxapampa, 3E Huaraz, 3G Trujillo, 4D Los Órganos, 4E Trujillo, 5D Puno, 6F Kimbiri, 11D Paracas, 16C Huaraz, 16D Puno, 17B Yunguyo, 17D Yanque, 19C Ilo, 19E Nasca, 20A Ilo, 21D Cuzco, 24E Huaraz, 26C Íllimo, 26D Los Órganos, 27D Miraflores, 30A Los Órganos, 31C Mazán, 37D Huacho, 38C La Merced y 39A Cerro de Pasco.

## Qué zonas aciertan

La nota de cada viaje es la media de las tres. Sobre las 40 consultas:

| Sistema | nDCG@3 | P@3 | MRR | No encajan |
|---|---|---|---|---|
| Motor | 0,812 | 0,317 | 0,592 | 14 % |
| Guía | 0,714 | 0,300 | 0,496 | 25 % |
| Variante | 0,821 | 0,317 | 0,558 | 13 % |

El motor ordena mejor que la guía: 0,098 más de nDCG@3, con un intervalo de 95 % de 0,020 a 0,176 y p = 0,019 en la prueba de Wilcoxon. Gana en 23 consultas, pierde en 14 y empata en 3. En P@3 la diferencia, 0,017, no se distingue de cero (p = 0,81): los dos aciertan pocas veces con un viaje que los tres recomendarían tal cual.

La variante no se distingue del motor: 0,009 más de nDCG@3, con un intervalo de −0,030 a 0,048 (p = 0,69), y gana en 11 consultas y pierde en 14. La 0021 la iba a desplegar si las calificaciones la favorecían, así que no se despliega.

Por interés, la ventaja del motor sobre la guía sale de las consultas sin interés (0,82 contra 0,49), de aventura (0,91 contra 0,73) y de naturaleza (0,82 contra 0,66). En arquitectura, caminatas y fiestas, la guía queda igual o algo arriba. En playa, la variante es la mejor de los tres: 0,83, contra 0,73 del motor, en seis consultas.

El motor propone 29 zonas distintas en las 40 consultas, la guía 36 y la variante 33. Fuera del circuito de Lima y el Cusco va el 75 % de los viajes del motor, el 60 % de los de la guía y el 80 % de los de la variante.

## El bus de noche

El kit se armó con el tope del 40 % de la [0019](../decisiones/0019-plan-creible.md). Según el cuadernillo que vio cada quien, sus viajes en bus de noche sacan menos nota cuanto más del viaje se lleva el bus, y eso sostiene la [0027](../decisiones/0027-tope-del-bus-de-noche.md):

| Parte del viaje en el bus | Viajes | Nota media | No encajan |
|---|---|---|---|
| Menos del 20 % | 28 | 1,25 | 7 % |
| Del 20 al 30 % | 37 | 0,97 | 19 % |
| Del 30 al 40 % | 29 | 0,80 | 28 % |
| Sin bus de noche | 102 | 1,10 | 25 % |

Son pocos viajes por tramo, y los que van más lejos difieren también en otras cosas.

## El motor de ahora

Las notas valen para el motor de los datos `2026.11.1`. El que se entrega es el de los `2026.11.5`. Para las mismas 40 consultas, cambia algo en 32, y 30 de sus 120 propuestas son zonas que el kit no tiene para esa consulta. Las que sí tiene promedian 1,26 de nota, y las que proponía el motor del kit, 1,17.

El primer puesto cambia en 18 consultas. En 14 la zona nueva tiene nota en el kit, y las dos medias quedan iguales, 1,19: mejora en 4, empeora en 7 y queda igual en 3. En 6 consultas pasa a ser Puno, que ahora va a los Uros ([0028](../decisiones/0028-horarios-y-visitas-corregidos.md)): las zonas que desplaza tenían 1,56 de media, y Puno, en las cinco con nota, 0,87, con notas puestas a viajes sin los Uros. Las que mejoran son Paracas en lugar de Huacho, Machu Picchu en lugar de Puno, Mollendo en lugar de Ilo y Los Órganos en lugar de Trujillo.

Casi todo eso entra con los datos `2026.11.3`, los de la [0030](../decisiones/0030-a-su-hora-y-desde-el-terminal.md): la ida en bus suma los terminales, los vuelos cuentan cuántos hay al mes y el Circuito Mágico del Agua se ve de noche. Con los `2026.11.2` el primer puesto cambiaba en 14 consultas. La hora del día, el techo del bus y los hospedajes, de los `2026.11.4` y `2026.11.5`, no cambian ningún primer puesto.

Con una de cada cuatro propuestas sin nota, las cifras de arriba describen al motor del kit y solo en parte al que se entrega. Calificar las 30 zonas nuevas pide otro kit (`python -m evaluacion.kit`) y otra ronda de notas.

## Lo que esto no dice

- Quienes califican hicieron el producto y pueden reconocer el estilo del motor, como dice la 0021.
- Son tres personas y no cuatro, con un acuerdo bajo. Sumar calificadores de fuera del equipo es el punto 12 de lo pendiente en la auditoría.
- Son 40 consultas escritas a mano para cubrir el producto. Sirven para comparar sistemas sobre las mismas consultas, no para estimar cómo le va al motor con cualquier consulta.

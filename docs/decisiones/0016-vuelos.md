# 0016 · Se vuela solo a lo lejano, y el presupuesto entra a elegir

**Fecha:** 15 de octubre de 2026 · **Estado:** vigente · Amplía la [0009](./0009-viaje-en-estrella.md) y cambia la propiedad 7 del [contrato](../CONTRATO.md) (versión 1.3)

## Contexto

Por tierra, el Cusco desde Lima solo cabía con doce días o más ([0015](./0015-mas-dias-alla-que-en-el-camino.md)), e Iquitos pedía más de dos días de río. La primera regla que se probó fue volar si así se llega al menos media jornada antes. Con ella vuelan 63 de cada 100 viajes de la rejilla, los que van fuera del circuito bajan del 77 % al 55 %, Huaraz deja de salir y el costo mediano sube 66 %. Con presupuesto, 95 de cada 100 viajes en avión lo pasan. Como el presupuesto no entraba a elegir las tres rutas, esos vuelos desplazaban a viajes en bus que sí entraban.

## Decisión

- **Rutas y tiempos:** las 22 rutas regulares que salen de Lima. Entre otros dos aeropuertos se vuela con escala en Lima. De puerta a puerta se suman:
  - el camino por tierra hasta el aeropuerto;
  - dos horas antes del vuelo;
  - el vuelo, con dos horas de escala si la hay;
  - media hora para salir;
  - el camino hasta la base.

  Está en [`pipeline/vuelos.py`](../../pipeline/vuelos.py) y en [`pipeline/README.md`](../../pipeline/README.md#los-vuelos).
- **Se vuela solo a lo lejano** (`conviene_volar`, en [`dreemgo/motor/viaje.py`](../../dreemgo/motor/viaje.py)). Se cumplen tres cosas:
  - por tierra, la ida pasa de 16 horas: lo que tarda menos se hace en un bus de noche;
  - en avión se llega al menos media jornada antes, con las noches del camino contadas;
  - la ida y la vuelta en avión no se llevan el 40 % de las horas del viaje, el umbral del aviso «dias».

  Nunca se vuela con `solo_por_tierra`.
- **Ningún día de viaje pasa de 9 horas, tampoco con vuelo.** Si no cabe en uno, se duerme junto al aeropuerto de llegada. Si llegar al de salida ya se lleva el día, también se duerme junto a ese.
- **El pasaje** se cobra por tramo, de ida y de vuelta. Va en una banda desde la tarifa más baja publicada hasta 2,2 veces esa.
- **El presupuesto entra a elegir las tres rutas.** Una que lo pasa compite castigada por (presupuesto / costo)². La propiedad 7 dice ahora tres cosas:
  - con presupuesto salen tantas rutas como sin él;
  - una que entra y salía sin él sigue saliendo;
  - la que lo pasa lleva su aviso.

## Alternativas descartadas

1 152 consultas sin presupuesto: 24 orígenes, 2, 4, 6 y 9 días, los doce meses. Los números de las columnas de Machu Picchu a Iquitos cuentan cuántas veces sale ese destino.

| Regla | Vuelan | Fuera del circuito | Machu Picchu | Cusco | Huaraz | Iquitos | Costo mediano |
|---|---:|---:|---:|---:|---:|---:|---:|
| Solo por tierra (hasta la 1.2) | 0 % | 77 % | 9 | 192 | 72 | 0 | S/ 997 |
| Llegar media jornada antes | 63 % | 55 % | 5 | 614 | 0 | 2 | S/ 1 658 |
| Lo lejano, con 12 horas | 41 % | 64 % | 9 | 446 | 19 | 4 | S/ 1 135 |
| **Lo lejano, con 16 horas** | **38 %** | **66 %** | **9** | **428** | **19** | **9** | **S/ 1 091** |
| Lo lejano, con 20 horas | 34 % | 69 % | 9 | 429 | 23 | 15 | S/ 1 068 |

Con 1 152 consultas con presupuesto (S/ 800, 1 000 y 1 500; 4 y 6 días; cuatro meses; con y sin naturaleza y caminatas):

| | Rutas que pasan el presupuesto | Consultas con las tres pasadas |
|---|---:|---:|
| Solo por tierra; el presupuesto solo ordena (1.2) | 35 % | 377 |
| Lo lejano; el presupuesto solo ordena | 52 % | 441 |
| **Lo lejano; el presupuesto elige** | **39 %** | **388** |

- **Doce o veinte horas en vez de dieciséis** dan casi lo mismo. Con veinte, Arequipa (19 horas por tierra) quedaría en bus desde Lima.
- **El interruptor apagado por defecto** dejaba el producto como estaba, pero el Cusco desde Lima no saldría si no se lo pide.

## Consecuencias

- Desde Lima con 4 o 6 días salen sobre todo el Cusco, Arequipa y Puno, en avión. Con 2 días salen Huacho, Chincha Alta y Paracas, como antes.
- Desde el Cusco, un fin de semana sigue siendo sobre todo Urubamba, Machu Picchu y Abancay.
- El ejemplo de la guía (Lima, 4 días, naturaleza y caminatas, S/ 1 000) da Huaraz, Huacho y Oxapampa, en bus y dentro del presupuesto.
- Sin presupuesto, «solo por tierra» da las mismas respuestas que la 1.2, byte a byte.
- `traslado.acceso` sigue hablando del camino por tierra: Iquitos sigue `sin_acceso_terrestre` aunque se vuele.
- **Lo que no se modela:**
  - los horarios y las frecuencias de los vuelos;
  - el traslado al aeropuerto, que se cobra como bus;
  - las tarifas, que no están calibradas;
  - los buses de noche. Cuando entren, las 16 horas pueden cambiarse por comparar el vuelo con el bus de noche.

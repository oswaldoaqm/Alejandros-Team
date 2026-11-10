# 0010 · El tren y los botes entran a la red; cada parada se ubica según su ficha

**Fecha:** 1 de octubre de 2026 · **Estado:** vigente · Amplía la [0007](./0007-red-vial-propia.md)

## Contexto

La red solo tenía carreteras. El motor no llegaba a Machu Picchu en tren ni a las islas del Titicaca, las Ballestas o los ríos de la Amazonía. Según sus fichas, a 168 paradas se llega en bote y a una en tren.

## Decisión

- **Dos capas sobre las vías** ([`pipeline/red_vial.py`](../../pipeline/red_vial.py)):
  - el tren de pasajeros: las rutas `route=train` de OSM sin ramales mineros, más los rieles de uso turístico aunque no tengan ruta, como el tramo Machu Picchu–Hidroeléctrica;
  - los botes: los ferris de más de 3 km.
- **Ritmos:** el tren a 2,14 min/km y el bote a 3,0 min/km, que son las medianas de los tramos de las fichas. Subir o bajar cuesta 15 minutos, un supuesto del equipo ([`ritmos_fijos.csv`](../../pipeline/referencia/ritmos_fijos.csv)).
- **Dónde se sube:**
  - al tren, en una estación, también en las que OSM dibuja al lado del riel;
  - a un bote, en cualquier punto de su ruta a menos de 1 km de una vía, como las lanchas que paran en cada pueblo de la orilla.
- **Cada parada se ubica según su ficha:** en la ruta de bote (a menos de 5 km) si se llega en bote, y en la vía si no. Los pueblos van en la vía mientras haya una a menos de 1 km.
- **La calibración no cambia:** se hace solo sobre las vías.

## Alternativas descartadas

- **Ubicar cada parada a la vez en la vía y en el bote, y dejar que elija el camino más corto:** a una isla cerca de la orilla se llegaba «manejando» sobre el agua.
- **Ampliar de 5 a 12 km el radio para ubicar una parada en el bote:** alcanzaba 14 paradas más, pero 8 con el doble o más del tiempo de su ficha.
- **Usar solo las rutas de tren de OSM:** sin el tramo Machu Picchu–Hidroeléctrica, el polo quedaba entre 1 y casi 4 horas más lejos desde el centro del país.

## Consecuencias

- **Machu Picchu:**
  - Cusco → Machupicchu Pueblo pasa de 5 h 38 a 3 h 17, en tren.
  - Desde las ocho ciudades que llegan por la Hidroeléctrica (el centro del país, Tarapoto y Chachapoyas), el polo queda 45 minutos más lejos que antes. Ese tramo ahora va en tren; antes la red lo cambiaba por 10 minutos de una trocha que no existe.
- **Lo que ahora se alcanza:**
  - Taquile a 2 h 33 de Puno y las Ballestas a 1 h 48 de Paracas.
  - Los pares origen–base sin camino bajan de 427 a 24.
- **Lo que sigue fuera:**
  - los recursos con su coordenada en medio del lago, como la Reserva Nacional del Titicaca;
  - Madre de Dios, que no tiene rutas de bote en OSM.
- **En la Amazonía**, cruzar un río cuesta 30 minutos, y donde OSM no registra la ruta local el tiempo sale mayor que el de la ficha.
- **La novedad de un polo no cambia de escala:** su lejanía se sigue midiendo hasta el polo más lejano por carretera, y uno a días de río vale 1, como cuando no tenía camino. Con la escala estirada hasta las 57 horas de río de Iquitos a Contamana, 116 de 576 consultas de prueba cambiaban de rutas o de orden solo por eso.
- **El contrato 1.2** dice con qué se viaja, y el costo cobra el tren y el bote, cada uno con su fuente.
- **Antes de publicar**, `python -m pipeline.comparar_tiempos` lista todo par que empeora y dice si es porque su base o su parada cambiaron de lugar en la red. Lo demás se mira a mano: esta vez, 14 pares, todos del tramo de la Hidroeléctrica.

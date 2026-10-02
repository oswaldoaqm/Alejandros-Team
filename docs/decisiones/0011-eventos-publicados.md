# 0011 · Los municipios publican eventos; lo publicado se suma sin mover las rutas

**Fecha:** 2 de octubre de 2026 · **Estado:** vigente · Amplía la [0003](./0003-artefactos-precalculados.md)

## Contexto

El calendario del motor son los 758 acontecimientos del inventario, con su fecha calculada. Pero la fecha y el lugar exactos de una feria solo los conoce quien la organiza ([DataAnalysis §6](../../deliveries/week06/DataAnalysis.md)): por eso el producto tiene un lado de la oferta, en el que un municipio o una oficina de destino anuncia lo suyo (RF-03). El contrato ya traía el modelo `EventoNuevo` y anunciaba `POST /v1/eventos`. Faltaba decidir dónde se guarda lo publicado, a qué rutas toca y cómo se sostiene que la misma consulta con los mismos datos dé la misma respuesta ([CONTRATO §3](../CONTRATO.md)) cuando los datos cambian con cada publicación.

## Decisión

- **Se suma, no ordena.** Un evento publicado aparece en `eventos[]` con `fuente: "publicado"`, sus fechas exactas y quién lo publicó. No entra al puntaje ni a los motivos: publicar no mueve ningún polo de su lugar. El orden no se vende.
- **A qué rutas toca:** a las de los polos que duermen o tienen algún lugar del inventario a 10 km o menos, en línea recta ([`dreemgo/publicados.py`](../../dreemgo/publicados.py)). Sin coordenadas, el evento sale en el calendario y en ninguna ruta.
- **Se guarda lo que dijo quien publica y nada más.** A qué polos toca se calcula al leer, con los artefactos del momento: si los polos cambian con una versión nueva de los datos, lo publicado los sigue.
- **La versión de datos lleva la huella de lo publicado:** `2026.10.2-e3f9a1c`. Cada consulta se resuelve con una sola foto del calendario publicado y la versión que informa es la de esa foto.
- **Dónde se guarda lo decide el entorno**, detrás de una interfaz de dos operaciones, leer todo y guardar uno ([`dreemgo/almacen.py`](../../dreemgo/almacen.py)): una tabla de DynamoDB en AWS, un archivo fuera de AWS y la memoria para desarrollar. ~~El API recuerda lo leído un minuto.~~ Ahora la interfaz tiene una tercera operación: ver la actualización.
- **La tabla tiene el `id` del evento como clave** y se lee entera. Publicar otra vez el mismo evento (mismo nombre, fechas, lugar y entidad) lo reemplaza, y DynamoDB borra sola los que ya pasaron.
- **Publica quien trae la clave** (`X-Clave-Publicador`). Sin clave configurada no publica nadie.
- **No se acepta** un evento que ya terminó, de más de 60 días, que empieza a más de doce meses, fuera del Perú o con una región que no es una de las 25. Caben 500 eventos por venir.

## Alternativas descartadas

- **Que un evento publicado sume al puntaje o sea un motivo:** quien más publica subiría su polo. Los motivos dicen por qué el motor propone un polo, y un anuncio no es una razón del motor.
- **Asociarlo solo al polo del lugar más cercano**, y usar ese polo como clave de la tabla, que es como estaba la plantilla: 22 pueblos sirven de base a más de un polo (Huaraz, a cuatro), y una feria en Huaraz salía en uno solo de los cuatro. Además, corregir la ubicación de un evento podía dejarlo dos veces en la tabla.
- **Un radio de 25 km:** un evento tocaba hasta a 7 polos. Con 10 km, medido donde están los 745 acontecimientos programados del inventario, toca a 2 en mediana y a 4 como mucho, y el 3 % no toca a ninguno.
- **No versionar lo publicado:** la misma consulta con la misma versión habría dado respuestas distintas.
- **Un contador o una fecha como versión:** dos servidores con el mismo calendario dirían versiones distintas. La huella sale del contenido.
- **Consultar la tabla en cada petición:** una lectura por consulta, y una respuesta armada con dos fotos si alguien publica a la mitad.
- **Cuentas por entidad:** fuera del alcance del curso ([0001](./0001-sin-login-y-enlace-compartible.md)). Una clave compartida alcanza para la demostración.

## Consecuencias

- ~~**Demora:** un evento se ve enseguida en el servidor que lo recibió y hasta un minuto después en los demás.~~ Ya son dos segundos: ver la actualización.
- **Si la tabla no responde, las rutas siguen:** se responde con lo último que se leyó, o sin lo publicado, y la versión de datos dice con qué.
- **Los enlaces compartidos** antes de una publicación abren con otra versión de datos. La app distingue los dos casos: si cambiaron los artefactos, avisa que las rutas pueden ser otras; si solo cambió la huella, las rutas son las mismas, no avisa y pone en el enlace la versión vigente. Avisar con cada publicación haría que nadie leyera el aviso que sí importa.
- **No hay moderación:** quien tiene la clave publica a nombre de la entidad que diga. Por eso lo publicado se muestra siempre con su «Publicado por…» y nunca como un motivo del motor.
- **Lo que el contrato 1.2 no tiene todavía:** retirar un evento por el API (hoy se borra de la tabla a mano), saber por la respuesta a qué polos tocó y mostrar la descripción. Corregirle el nombre o las fechas a un evento crea otro.
- **La imagen del API** suma boto3, que solo se usa en AWS.

## Actualización · 2 de octubre de 2026

Al preparar el despliegue, el minuto de demora resultó pesar más de lo previsto. En Lambda basta con que la app haga dos pedidos a la vez para que haya dos servidores despiertos, y quien acaba de publicar podía no ver su evento en la consulta siguiente, según cuál de los dos la atendiera. En un contenedor con dos procesos pasaba lo mismo.

Ahora el almacén tiene una tercera operación, **la marca**: un valor que cambia cada vez que alguien guarda. En la tabla es un ítem más, `#marca`; en el archivo, su tamaño y su hora; en memoria, un contador. Cada servidor la pregunta cada dos segundos como mucho, solo mientras atiende pedidos, y vuelve a leer todo cuando cambió. La lectura completa de cada minuto se queda, para lo que no mueve la marca: un evento borrado a mano, o uno guardado justo cuando la tabla no dejó escribir la marca.

- **Lo que cuesta:** en la tabla, una unidad de lectura por pregunta, y una escritura más por publicación.
- **Descartado, acortar el minuto:** leer la tabla entera cada pocos segundos pasa de su capacidad cuando el calendario se llena.
- **Descartado, preguntar la marca en cada consulta:** a diez consultas por segundo, que es el límite de la HTTP API, son el doble de las lecturas que la tabla da.

# Plan del producto

**El 14 de octubre DreemGO está desplegado y resuelve una consulta real de punta a punta; el 18 de noviembre es un producto que se puede presentar a cualquiera.** Este documento es el estado del plan dentro del repositorio: qué se hace, en qué orden, cuándo está terminado y quién lo defiende. Se actualiza al cerrar cada fase.

Estado al 2 de octubre de 2026: **fase 0** con CI en verde en `main`; falta que los cuatro revisen el contrato. **Fase 1** casi cerrada: el motor responde `/v1/viajes` con el [contrato 1.2](./CONTRATO.md) y cumple las diez propiedades en 1 000 consultas al azar, y la red ya tiene el tren a Machu Picchu y los botes del Titicaca, las Ballestas y la Amazonía ([decisión 0010](./decisiones/0010-tren-y-botes.md)); falta el clima propio de 186 polos, que baja hasta el 7 de octubre, y volver a armar con él los artefactos. De la **fase 2** ya está la [app](../app/), publicada en GitHub Pages: el formulario, tres rutas para comparar, el itinerario con su mapa, su costo, su mes y sus fiestas, la ficha de cada polo y el calendario, con sus pruebas en CI. Y el lado de la oferta: una municipalidad publica un evento (`POST /v1/eventos` y la página «Publicar un evento») y sale en el calendario y en las rutas que pasan cerca, sin mover ninguna ([decisión 0011](./decisiones/0011-eventos-publicados.md)). El despliegue está listo para ejecutarse ([`infra/README.md`](../infra/README.md)): en AWS, ensayado contra un simulador hasta donde este llega, o en un host gratuito como Render mientras no haya cuenta. Falta hacerlo: hasta entonces la app publicada no tiene a quién preguntarle. De la **fase 3** ya está el [informe del prototipo](../deliveries/week10/PrototypeReport.md), que mide qué propone hoy el motor sobre 1 152 consultas y deja escritos sus límites; faltan la presentación y las capturas.

Después, el 6 de octubre, la app se rediseñó: cada viaje se abre en su propia pantalla, con el plan día por día, un mapa de un pétalo por día y la hoja de cada lugar; hay fotos de Wikimedia Commons, con su autor y su licencia, y tema oscuro. Qué fotos van y cómo se revisaron está en [`pipeline/README.md`](../pipeline/README.md#fotos), y las pantallas, en [`app/README.md`](../app/README.md).

Entre el 7 y el 8 de octubre el motor empezó a proponer lo más conocido. Los grupos del agrupamiento que duermen en el mismo pueblo son un solo polo (194 en vez de 222), una parada de jerarquía alta vale más, un día de solo viaje puede durar 9 horas y ningún viaje pasa más días en el camino que allá. Con eso Huaraz sale desde Lima con cuatro días, y Machu Picchu, desde el Cusco. Desde Lima, Machu Picchu sigue sin salir: pide vuelos y viajes de varios polos, que son de la fase 4. Lo que se midió y lo que costó está en las decisiones [0013](./decisiones/0013-un-polo-por-pueblo.md), [0014](./decisiones/0014-dia-de-solo-viaje.md) y [0015](./decisiones/0015-mas-dias-alla-que-en-el-camino.md), y en el [informe del prototipo](../deliveries/week10/PrototypeReport.md).

El 8 de octubre la app publicada empezó a responder: le pregunta al API, que corre en Render desde `main` ([decisión 0012](./decisiones/0012-host-gratuito-render.md)). Render es gratis, pero se duerme sin uso y lo que publican los municipios no dura. AWS sigue siendo el destino, y la cuenta ya está.

El 10 de octubre entró el clima propio de los 194 polos, con los datos `2026.10.4`: ninguno usa ya el de su región. Cambió la respuesta de 156 de las 1 152 consultas; lo que se movió y por qué está en el [informe del prototipo](../deliveries/week10/PrototypeReport.md).

El 14 de octubre el profesor movió la entrega de la semana 10, con su exposición, al 21 de octubre. La carpeta [`deliveries/week10/`](../deliveries/week10/) ya tiene todo lo que pide el enunciado, con la presentación y las capturas.

Después de esa entrega entran los vuelos, con el [contrato 1.3](./CONTRATO.md) y los datos `2026.10.5`. Se vuela solo a lo que por tierra queda a más de 16 horas, y no en viajes cortos: desde Lima salen el Cusco, Arequipa y Puno en avión, y Huaraz y Trujillo siguen en bus. El presupuesto entra ahora a elegir las tres rutas. Quien no quiere volar apaga el interruptor «Vuelos». Lo que se midió está en la [decisión 0016](./decisiones/0016-vuelos.md).

Con los vuelos entra «Quiero ir a…», con el [contrato 1.4](./CONTRATO.md). Quien ya sabe a dónde quiere ir elige la zona en el formulario, desde la zona o desde una fiesta del calendario. El motor arma ese viaje o dice por qué no cabe y qué cambiar: desde Lima, el Cusco sale con tres días, Machu Picchu con cinco y Huaraz con cuatro. Está en la [decisión 0017](./decisiones/0017-quiero-ir-a.md), que deja abierta una pregunta para el equipo: si con destino se vuela también en viajes cortos.

Después entran los planes de noche, con el [contrato 1.5](./CONTRATO.md) y los datos `2026.10.6`. Cada noche que se duerme en la zona trae un plan, sin cambiar el día:

- con «Vida nocturna», hasta tres bares, pubs, discotecas, karaokes o peñas a pie de la base, otros cada noche, y un descanso la primera noche en la altura;
- con «Naturaleza», o sin intereses, una noche de estrellas: desde la base si su cielo es oscuro, o en un observatorio o planetario cercano. Con fecha, la de menos luna.

La página de cada zona muestra dónde salir y cuántas noches salen despejadas cada mes. Está en la [decisión 0018](./decisiones/0018-planes-de-noche.md).

Después, el plan creíble, con el [contrato 1.6](./CONTRATO.md) y los datos `2026.10.7`:

- **el almuerzo**: una hora más, que no cuenta en las 8 de paseo, en un lugar con dónde comer si lo hay a la hora, o con el aviso de llevarlo;
- **el bus de noche**: lo que por tierra toma de 7 a 16 horas va de noche, y sus noches quedan fuera de los días. Desde Lima, Huaraz y Nasca salen con dos días;
- **una jornada que no se corre**: se vuelve a las 17:00 aunque el primer lugar abra tarde, y no se espera más de una hora en una puerta;
- **con destino se vuela aunque el viaje sea corto**: el Cusco sale desde Lima con dos días. Así se cierra la pregunta que dejó la 0017.

Para que un fin de semana no salga siempre lejos, el bus no va si se lleva el 40 % del viaje, con sus noches, y sus dos noches pesan en el puntaje como un día más. Está en la [decisión 0019](./decisiones/0019-plan-creible.md).

Después, el primer día tranquilo en la altura, con el [contrato 1.7](./CONTRATO.md) y los datos `2026.10.8`. El aviso de aclimatación decía «conviene un primer día tranquilo», y ahora el plan lo da: si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, el primer día en la zona tiene medio día de visitas como mucho, sin subir más de 500 m sobre la base ni caminatas largas, y después de un bus de noche empieza a las 9:00. Es la misma regla de la noche de descanso, y sale del Yellow Book del CDC. Las 13 bases que no tenían altura la toman de un modelo de elevación, y con eso la altitud máxima también filtra dónde se duerme. Está en la [decisión 0020](./decisiones/0020-primer-dia-tranquilo.md).

## Qué promete el producto

El viajero dice desde dónde sale, cuántos días tiene, en qué mes viaja, qué le interesa, cuánto quiere gastar y hasta qué altura tolera. DreemGO le devuelve **tres viajes distintos, cada uno a un polo turístico, con el itinerario día por día**: qué visitar, en qué orden, a qué hora se llega, cuánto cuesta en una banda realista, qué fiestas caen en sus fechas y por qué ese mes conviene o no. Cada parada enlaza a su ficha oficial de MINCETUR. Si ya sabe a dónde quiere ir, le arma ese viaje o le dice qué cambiar para que quepa. Cada noche en la zona tiene su plan: dónde salir, desde dónde ver las estrellas o, en la altura, descansar. Y el plan se puede seguir: cada día almuerza, lo que queda a una noche de bus va de noche y el primer día en la altura va con calma.

## Calendario

| Fase | Fechas | Qué sale | Terminado cuando |
|---|---|---|---|
| 0 · Cimientos | 30 sep – 3 oct | Descargas de datos; erratas y etiquetas de las entregas 4 a 7; esqueleto del repositorio; [contrato de la API](./CONTRATO.md); CI; infraestructura lista para AWS | CI en verde y el contrato revisado por los cuatro |
| 1 · Datos v3 y motor | 3 – 9 oct | Maestro v3 con procedencia por campo; calendario de eventos real; clima por polo; tiempos de viaje por carretera, tren y bote; motor v2 detrás del API | `GET /v1/viajes` devuelve el contrato y las 10 propiedades de [CONTRATO §3](./CONTRATO.md) se cumplen en 1 000 consultas |
| 2 · App y despliegue | 6 – 12 oct | App web contra el contrato; eventos que publican los municipios; API desplegada | La app abre en un celular con datos móviles y resuelve una consulta |
| 3 · Entrega de la semana 10 | 12 – 21 oct | `PrototypeReport`, presentación, capturas y video, README con instalación y despliegue | Carpeta `deliveries/week10/` completa |
| **Semana 10 · prototipo** | **21 oct** | | |
| 4 · Refinar y evaluar | 15 – 27 oct | Viajes de varios polos; TA-01 v3 sobre horas reales; evaluación: brecha contra el óptimo, sensibilidad, consultas anotadas con acuerdo medido, prueba de usabilidad con cinco personas, tres casos de estudio | `EvaluationReport` con cada cifra reproducible |
| **Semana 12 · evaluación** | **28 oct** | | |
| 5 · Pulido y final | 29 oct – 17 nov | Informe final, presentación, video, página del proyecto, Canvas y requisitos finales, declaración de contribución y reflexión | Un ensayo completo con preguntas difíciles, sin tropiezos |
| **Delivery 2 · final** | **18 nov** | | |

Las fases 1 y 2 se solapan a propósito: la app se construye contra el contrato y el [ejemplo ilustrativo](./ejemplos/respuesta_ilustrativa.json) mientras el motor termina. Lo que no alcance para la entrega de la semana 10 pasa a la fase 4.

## Qué es cada pieza

| Pieza | Dónde | Qué hace |
|---|---|---|
| Adquisición | [`pipeline/adquisicion/`](../pipeline/adquisicion/) | Baja las fuentes: inventario, fichas oficiales, clima por polo, red vial, los datos de las fotos y, para la noche, los lugares de Overture, las luces de VIIRS, las nubes de GOES-16 y los METAR |
| Pipeline | [`pipeline/`](../pipeline/) | Convierte las descargas en artefactos versionados con procedencia, en [`data/procesados/`](../data/procesados/), y elige la foto de cada lugar |
| Motor y API | [`dreemgo/`](../dreemgo/) | Carga los artefactos y resuelve consultas, y recibe los eventos que publican los municipios: [contrato](./CONTRATO.md) |
| App | [`app/`](../app/) | React, Vite, TypeScript y MapLibre; en GitHub Pages |
| Infraestructura | [`infra/`](../infra/) | Imagen del API y despliegue en AWS con SAM, con la tabla de los eventos publicados; y las alternativas gratuitas mientras no haya cuenta |
| Pruebas | [`tests/`](../tests/) | Contrato, API y, con el motor, propiedades sobre miles de consultas |
| Evaluación | [`evaluacion/`](../evaluacion/) | Las 40 consultas que califica el equipo, la línea de base, el kit para calificar y las cifras del informe de la semana 12 ([decisión 0021](./decisiones/0021-evaluacion-semana-12.md)) |
| Decisiones | [`docs/decisiones/`](./decisiones/) | Por qué cada cosa es como es |
| Entregas | [`deliveries/`](../deliveries/) | Lo que pide cada semana del curso, con sus erratas |

## Quién defiende qué

Cada integrante tiene que poder explicar su parte frente al jurado. Antes de cada exposición hay una ronda de preguntas difíciles, y cada área tiene una guía de una página.

| Integrante | Rol | Defiende |
|---|---|---|
| Miguel | Data Engineer / Cloud Architect | Adquisición, pipeline y despliegue en AWS |
| Alejandro | Data Scientist / ML Engineer | Datos, modelo (polos, estacionalidad, rutas) y evaluación |
| Diego | Backend & Algorithms Engineer | Motor de rutas y API |
| Christopher | Frontend Developer & Product Owner | App, pruebas de usabilidad, Canvas y requisitos |

## Cómo se trabaja

- **Ramas**: una por fase o tarea, con prefijo del autor (`alejandro/fase0-cimientos`), y PR a `main`. Nadie hace push directo a `main`.
- **Commits**: atómicos, un cambio por commit, en español y con [Conventional Commits](https://www.conventionalcommits.org/es/v1.0.0/): `feat(motor): …`, `fix(week06): …`, `docs: …`.
- **CI**: lint, formato, pruebas, las dos imágenes del API (arrancan, publican un evento y no lo pierden) y la app (sus pruebas y una prueba de humo contra el API) en cada PR. Un PR en rojo no se fusiona.
- **Contrato primero**: un cambio en lo que el API recibe o devuelve empieza en `dreemgo/contrato.py` y [`CONTRATO.md`](./CONTRATO.md).
- **Datos**: nada se inventa. Un dato que la fuente no trae viaja como `null`, y cada campo derivado dice de dónde sale.
- **Entregas**: la carpeta de cada semana guarda sus documentos y una copia de su código. Desde la semana 10 el código es el del producto, que vive en la raíz; la carpeta guarda una copia congelada de ese código, de los datos procesados y de los artefactos, tal como se entregan, para que todo lo que pide el enunciado esté adentro. Lo entregado queda en su etiqueta y lo que se corrige después va en su `ERRATA.md` ([decisión 0005](./decisiones/0005-historial-y-erratas.md)).

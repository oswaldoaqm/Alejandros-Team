# Plan del producto

**El 14 de octubre DreemGO está desplegado y resuelve una consulta real de punta a punta; el 18 de noviembre es un producto que se puede presentar a cualquiera.** Este documento es el estado del plan dentro del repositorio: qué se hace, en qué orden, cuándo está terminado y quién lo defiende. Se actualiza al cerrar cada fase.

Estado al 2 de octubre de 2026: **fase 0** con CI en verde en `main`; falta que los cuatro revisen el contrato. **Fase 1** casi cerrada: el motor responde `/v1/viajes` con el [contrato 1.2](./CONTRATO.md) y cumple las diez propiedades en 1 000 consultas al azar, y la red ya tiene el tren a Machu Picchu y los botes del Titicaca, las Ballestas y la Amazonía ([decisión 0010](./decisiones/0010-tren-y-botes.md)); falta el clima propio de 186 polos, que baja hasta el 7 de octubre, y volver a armar con él los artefactos. De la **fase 2** ya está la [app](../app/), publicada en GitHub Pages: el formulario, tres rutas para comparar, el itinerario con su mapa, su costo, su mes y sus fiestas, la ficha de cada polo y el calendario, con sus pruebas en CI. Y el lado de la oferta: una municipalidad publica un evento (`POST /v1/eventos` y la página «Publicar un evento») y sale en el calendario y en las rutas que pasan cerca, sin mover ninguna ([decisión 0011](./decisiones/0011-eventos-publicados.md)). El despliegue está listo para ejecutarse ([`infra/README.md`](../infra/README.md)): en AWS, ensayado contra un simulador hasta donde este llega, o en un host gratuito como Render mientras no haya cuenta. Falta hacerlo: hasta entonces la app publicada no tiene a quién preguntarle. De la **fase 3** ya está el [informe del prototipo](../deliveries/week10/PrototypeReport.md), que mide qué propone hoy el motor sobre 1 152 consultas y deja escritos sus límites; faltan la presentación y las capturas.

## Qué promete el producto

El viajero dice desde dónde sale, cuántos días tiene, en qué mes viaja, qué le interesa, cuánto quiere gastar y hasta qué altura tolera. DreemGO le devuelve **tres viajes distintos, cada uno a un polo turístico, con el itinerario día por día**: qué visitar, en qué orden, a qué hora se llega, cuánto cuesta en una banda realista, qué fiestas caen en sus fechas y por qué ese mes conviene o no. Cada parada enlaza a su ficha oficial de MINCETUR.

## Calendario

| Fase | Fechas | Qué sale | Terminado cuando |
|---|---|---|---|
| 0 · Cimientos | 30 sep – 3 oct | Descargas de datos; erratas y etiquetas de las entregas 4 a 7; esqueleto del repositorio; [contrato de la API](./CONTRATO.md); CI; infraestructura lista para AWS | CI en verde y el contrato revisado por los cuatro |
| 1 · Datos v3 y motor | 3 – 9 oct | Maestro v3 con procedencia por campo; calendario de eventos real; clima por polo; tiempos de viaje por carretera, tren y bote; motor v2 detrás del API | `GET /v1/viajes` devuelve el contrato y las 10 propiedades de [CONTRATO §3](./CONTRATO.md) se cumplen en 1 000 consultas |
| 2 · App y despliegue | 6 – 12 oct | App web contra el contrato; eventos que publican los municipios; API desplegada | La app abre en un celular con datos móviles y resuelve una consulta |
| 3 · Entrega de la semana 10 | 12 – 14 oct | `PrototypeReport`, presentación, capturas y video, README con instalación y despliegue | Carpeta `deliveries/week10/` completa |
| **Semana 10 · prototipo** | **14 oct** | | |
| 4 · Refinar y evaluar | 15 – 27 oct | Viajes de varios polos; TA-01 v3 sobre horas reales; evaluación: brecha contra el óptimo, sensibilidad, consultas anotadas con acuerdo medido, prueba de usabilidad con cinco personas, tres casos de estudio | `EvaluationReport` con cada cifra reproducible |
| **Semana 12 · evaluación** | **28 oct** | | |
| 5 · Pulido y final | 29 oct – 17 nov | Informe final, presentación, video, página del proyecto, Canvas y requisitos finales, declaración de contribución y reflexión | Un ensayo completo con preguntas difíciles, sin tropiezos |
| **Delivery 2 · final** | **18 nov** | | |

Las fases 1 y 2 se solapan a propósito: la app se construye contra el contrato y el [ejemplo ilustrativo](./ejemplos/respuesta_ilustrativa.json) mientras el motor termina. Lo que no alcance para el 14 de octubre pasa a la fase 4; la fecha no se mueve.

## Qué es cada pieza

| Pieza | Dónde | Qué hace |
|---|---|---|
| Adquisición | [`pipeline/adquisicion/`](../pipeline/adquisicion/) | Baja las fuentes: inventario, fichas oficiales, clima por polo y red vial |
| Pipeline | [`pipeline/`](../pipeline/) | Convierte las descargas en artefactos versionados con procedencia, en [`data/procesados/`](../data/procesados/) |
| Motor y API | [`dreemgo/`](../dreemgo/) | Carga los artefactos y resuelve consultas, y recibe los eventos que publican los municipios: [contrato](./CONTRATO.md) |
| App | [`app/`](../app/) | React, Vite, TypeScript y MapLibre; en GitHub Pages |
| Infraestructura | [`infra/`](../infra/) | Imagen del API y despliegue en AWS con SAM, con la tabla de los eventos publicados; y las alternativas gratuitas mientras no haya cuenta |
| Pruebas | [`tests/`](../tests/) | Contrato, API y, con el motor, propiedades sobre miles de consultas |
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
- **Entregas**: la carpeta de cada semana guarda sus documentos. Hasta la semana 7 guarda también una copia de su código; desde la semana 10 el código es el del producto, que vive en la raíz, y la carpeta dice dónde está cada cosa. Lo entregado queda en su etiqueta y lo que se corrige después va en su `ERRATA.md` ([decisión 0005](./decisiones/0005-historial-y-erratas.md)).

# DreemGO — Semana 12 · Prototipo refinado, evaluación y casos de estudio

DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Carlos Abel Dominguez Bautista
Entrega: 28 de octubre de 2026

El producto vive en la raíz de este repositorio: un motor de itinerarios con su API, la app web que lo usa, el pipeline que arma sus datos y, desde esta semana, la evaluación que mide lo que propone. Esta carpeta guarda una copia congelada de su código, sus datos procesados, sus artefactos y las cifras de la evaluación, tal como se entregan el 28 de octubre (contrato 1.7, datos `2026.10.8`), para que todo lo que pide el enunciado esté aquí. La copia es para consultarla: el producto se instala y se corre desde la raíz, con los pasos de abajo. Dentro de la copia, los enlaces entre documentos siguen apuntando a la raíz, y algunos no abren desde aquí: el mismo documento está en la raíz.

Desde la semana 10 cambió esto: el frontend nuevo del equipo, las correcciones del 26 de octubre (la misma duración de la ida en la tarjeta y en el plan, un rojo propio para los avisos críticos, el tema oscuro con contraste suficiente y el tema del sistema), el aviso del presupuesto con el P80 ([decisión 0022](../../docs/decisiones/0022-presupuesto-con-margen.md)) y la evaluación, con una v3 de TA-01 medida con las horas de la red ([decisión 0023](../../docs/decisiones/0023-ta01-v3-horas-reales.md)). El detalle está en [`docs/ARQUITECTURA.md`](../../docs/ARQUITECTURA.md#lo-que-cambió-desde-la-semana-10).

## Qué pide el enunciado y dónde está

| Entregable | Dónde |
|---|---|
| Código fuente del producto refinado | [`code/`](./code/): el motor y el API (`dreemgo/`), la app web (`app/`), el pipeline de datos (`pipeline/`), la evaluación (`evaluacion/`), la imagen y el despliegue (`infra/`), las pruebas (`tests/`) y la documentación (`docs/`). Es la copia de lo que está en la raíz |
| URL del producto | La app: <https://oswaldoaqm.github.io/Alejandros-Team/>. El API que le responde: <https://alejandros-team.onrender.com>, con sus rutas en [`/v1/docs`](https://alejandros-team.onrender.com/v1/docs). Es un host gratuito que se duerme sin uso: la primera consulta después tarda cerca de un minuto |
| Datos procesados de la versión candidata | [`data/processed/`](./data/processed/), en CSV y JSON con su diccionario, copia de [`data/procesados/`](../../data/procesados/); y [`artifacts/`](./artifacts/), lo que el motor carga al arrancar, copia de [`dreemgo/datos/`](../../dreemgo/datos/). Son los datos `2026.10.8`, los mismos sobre los que se midió la evaluación |
| Cifras de la evaluación | [`resultados/`](./resultados/): lo que escribe cada script de la evaluación, de las zonas que propone cada sistema a los grupos en horas, en CSV y JSON. Es la copia de [`data/evaluacion/resultados/`](../../data/evaluacion/resultados/) |
| Scripts para reproducir | Los datos, con el pipeline ([`code/pipeline/`](./code/pipeline/)); cada cifra del informe, con un comando de [`code/evaluacion/`](./code/evaluacion/) (abajo, en [Evaluar](#evaluar)) |
| Informe de evaluación | [`EvaluationReport.md`](./EvaluationReport.md): la estrategia de validación, las métricas, la comparación con la línea de base, los resultados, los límites y tres casos de estudio |
| Presentación | [`PresentationWeek12.pptx`](./PresentationWeek12.pptx) y su versión en [PDF](./PresentationWeek12.pdf), con las mismas letras de las anteriores, Lexend y Quattrocento Sans; el PDF las lleva dentro |
| Arquitectura, flujos e interfaz | [`docs/ARQUITECTURA.md`](../../docs/ARQUITECTURA.md): las piezas, cómo viaja una consulta, cómo se arman los datos, cómo trabaja el equipo, las rutas del API y las pantallas de la app. Las pantallas en detalle, en [`app/README.md`](../../app/README.md); lo que recibe y devuelve el API, en el [contrato](../../docs/CONTRATO.md) |
| Evidencia de las pruebas | [`pruebas/`](./pruebas/): las salidas de cada revisión de la CI sobre el código de esta entrega, con las 1 000 consultas al azar de las propiedades del contrato, y cómo volver a correrlas. Las cifras de cada métrica, en `resultados/`; el análisis de dónde y por qué falla el motor, en el informe (4.2 a 4.4 y 5) |
| Caso de estudio | [`EvaluationReport.md`](./EvaluationReport.md#5--casos-de-estudio), con las capturas de [`capturas/`](./capturas/) |
| Plan de las tres semanas que quedan | [`PlanFinal.md`](./PlanFinal.md): cada tarea con su responsable y su criterio de terminado |
| README actualizado | Este archivo, y el de la raíz |

Lo entregado el 28 de octubre queda congelado en la etiqueta `entrega/semana-12`, en el último commit de `main` antes de la fecha ([decisión 0005](../../docs/decisiones/0005-historial-y-erratas.md)).

## Qué hace falta

| Para | Hace falta |
|---|---|
| El API y el motor | Python 3.11 o más nuevo. Instala `numpy`, `pydantic`, `fastapi` y `uvicorn` |
| La app | Node 22.12 o más nuevo. Instala React, Vite, TypeScript y MapLibre GL |
| La evaluación | Lo mismo que el API. Los grupos en horas piden además las dependencias del pipeline y la red vial que arma `pipeline.tiempos` |
| Rehacer los datos | Además, `pandas`, `scikit-learn`, `osmium`, `pyarrow`, `requests` y `lxml`, y las descargas de las fuentes. Las de la noche y la altura piden también `rasterio`, `h5py`, `fsspec` y `aiohttp` |
| Desplegar en AWS | Una cuenta, AWS CLI, SAM CLI y Docker |

Las versiones mínimas de cada paquete están en [`pyproject.toml`](../../pyproject.toml) y en [`app/package.json`](../../app/package.json). No hay base de datos que instalar: el motor responde desde los archivos de `dreemgo/datos/`, que ya vienen en el repositorio.

## Instalar y correr

Con el repositorio clonado, en dos terminales.

1. El API, desde la raíz:

```bash
pip install -e ".[api]"
python -m uvicorn dreemgo.api.app:app --port 8000
```

Queda en <http://localhost:8000>. <http://localhost:8000/v1/salud> responde `"estado": "ok"` con la versión de los datos, y <http://localhost:8000/v1/docs> muestra las rutas para probarlas a mano.

2. La app, en otra terminal:

```bash
cd app
npm ci
npm run dev
```

Queda en <http://localhost:5173> y le pregunta al API de la otra terminal. Para probar que un municipio publica un evento, el API arranca con una clave, que es la que después se escribe en el formulario de la app; los comandos para cada terminal están en [`app/README.md`](../../app/README.md#correrla-en-tu-máquina).

## Probar

```bash
pip install -e ".[api,dev,pipeline]"
pytest                                            # el motor, el API, el pipeline y la evaluación
DREEMGO_PROPIEDADES=1000 pytest tests/test_propiedades.py   # las garantías del contrato, con 1 000 consultas

cd app
npm test                    # la app, con un API de mentira
npx playwright install chromium
npm run e2e                 # la app en un navegador, contra el API de verdad
```

Lo mismo corre en cada pull request, junto con la construcción de las imágenes del API ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)). Las salidas de esta entrega y el script que las produjo están en [`pruebas/`](./pruebas/).

## Evaluar

Desde la raíz, con el entorno de las pruebas. Cada comando escribe en `data/evaluacion/resultados/`, y con los mismos datos sale lo mismo, salvo los segundos que tarda la búsqueda exacta.

```bash
python -m evaluacion.zonas            # qué zonas propone cada sistema y en cuántas coinciden
python -m evaluacion.optimo           # la heurística del itinerario contra el óptimo exacto, unos 10 minutos
python -m evaluacion.buses            # los tiempos por tierra contra los de Cruz del Sur
python -m evaluacion.polos_en_horas   # TA-01 con las horas de la red: la v2 medida y la v3, unos 4 minutos
python -m evaluacion.presupuesto      # qué cambia si el presupuesto deja fuera lo que no cabe, unos 5 minutos
```

`evaluacion.polos_en_horas` lee la red vial que `python -m pipeline.tiempos` deja en `data/externos/osm/`, fuera de git: se arma con los pasos de [Rehacer los datos](#rehacer-los-datos).

## Desplegar

- La app se publica sola en GitHub Pages con cada cambio de `main` ([`app/README.md`](../../app/README.md#publicarla)). La dirección del API la toma de la variable `API_URL` del repositorio.
- El API corre en Render, gratis, y se vuelve a desplegar solo con cada cambio de `main`. Se duerme a los 15 minutos sin uso, y lo que publican los municipios vive en un archivo del contenedor que se pierde cuando se reinicia. Los pasos están en [`infra/README.md`](../../infra/README.md#en-render-gratis-y-sin-tarjeta), y el porqué, en la [decisión 0012](../../docs/decisiones/0012-host-gratuito-render.md).
- El destino es AWS: una función Lambda con imagen de contenedor detrás de una HTTP API, con una tabla de DynamoDB donde lo publicado sí dura. Son cuatro comandos, descritos en [`infra/README.md`](../../infra/README.md), y desplegarlo es parte del [plan de las tres semanas](./PlanFinal.md).

## Rehacer los datos

Los datos del motor salen del pipeline, que parte de las descargas de las fuentes: el inventario y las fichas de MINCETUR, OpenStreetMap, Overture Maps, Open-Meteo, las nubes de GOES-16 y los METAR de NOAA, las luces de VIIRS, la altura del terreno de Terrain Tiles y las rutas aéreas que salen de Lima. El orden y lo que tarda cada paso están en el [`README.md`](../../README.md#reproducir) de la raíz y en [`pipeline/README.md`](../../pipeline/README.md); las licencias de cada fuente, en [`DATA_LICENSES.md`](../../DATA_LICENSES.md).

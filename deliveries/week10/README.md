# DreemGO — Semana 10 · Prototipo funcional

**Primera versión funcional del producto**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Carlos Abel Dominguez Bautista
Entrega: 21 de octubre de 2026 · Actualizada el 25 de octubre, con el frontend nuevo

El prototipo es el producto que vive en este repositorio: un motor de itinerarios con su API, la app web que lo usa y el pipeline que arma sus datos. Esta carpeta guarda una copia congelada de su código, sus datos procesados y sus artefactos tal como se entregan, al 25 de octubre (contrato 1.7, datos `2026.10.8`), para que todo lo que pide el enunciado esté aquí. La copia es para consultarla: el producto se instala y se corre desde la raíz del repositorio, con los pasos de abajo. Dentro de la copia, los enlaces entre documentos siguen apuntando a la raíz, y algunos no abren desde aquí: el mismo documento está en la raíz.

## Qué pide el enunciado y dónde está

| Entregable | Dónde |
|---|---|
| Código completo del prototipo | [`code/`](./code/): el motor y el API (`dreemgo/`), la app web (`app/`), el pipeline de datos (`pipeline/`), la evaluación de la semana 12 (`evaluacion/`), la imagen y el despliegue (`infra/`), las pruebas (`tests/`) y el contrato del API (`docs/`). Es la copia de lo que está en la raíz del repositorio |
| Datos procesados, en CSV y JSON | [`data/processed/`](./data/processed/), con su diccionario (`README.md`). Es la copia de [`data/procesados/`](../../data/procesados/) |
| Artefactos analíticos | [`artifacts/`](./artifacts/): lo que el motor carga al arrancar, con su manifiesto y la huella de cada archivo. Es la copia de [`dreemgo/datos/`](../../dreemgo/datos/) |
| El notebook | [`code/DreemGO_prototipo.ipynb`](./code/DreemGO_prototipo.ipynb), ya ejecutado: carga los artefactos, resuelve consultas reales (con vuelos, bus de noche y «Quiero ir a…») y mide las cifras del informe con el mismo código del API |
| Informe del prototipo | [`PrototypeReport.md`](./PrototypeReport.md). Las cifras de lo que propone el motor salen de [`code/cobertura.py`](./code/cobertura.py) |
| Presentación | [`PresentationWeek10.pptx`](./PresentationWeek10.pptx) y su versión en [PDF](./PresentationWeek10.pdf). Usa Lexend y Quattrocento Sans, de Google Fonts, como la de la semana 7; el PDF las lleva dentro |
| Capturas y video de la demostración | [`capturas/`](./capturas/): 25 pantallas en celular y en escritorio, con el frontend nuevo, y lo que muestra cada una. [`DemoWeek10.mp4`](./DemoWeek10.mp4): la demo del guion de la presentación en 3 minutos y 20 segundos, sin sonido y con un rótulo en cada paso |
| La revisión del profesor del 20 de octubre | [`revision_profesor/`](./revision_profesor/): la comparación de P50 y P80 con S/ 800 y la hoja de verificación de Huacho, con dos filas revisadas |
| URL del prototipo | La app: <https://oswaldoaqm.github.io/Alejandros-Team/>. El API que le responde: <https://alejandros-team.onrender.com>, con sus endpoints en [`/v1/docs`](https://alejandros-team.onrender.com/v1/docs) |
| Instalación, ejecución, dependencias y despliegue | Este archivo |

Lo entregado el 21 de octubre quedó congelado en la etiqueta `entrega/semana-10`, en el último commit de `main` antes de la fecha ([decisión 0005](../../docs/decisiones/0005-historial-y-erratas.md)). Lo que cambió después, con el frontend nuevo, está en [`ERRATA.md`](./ERRATA.md).

## Qué hace falta

| Para | Hace falta |
|---|---|
| El API y el motor | Python 3.11 o más nuevo. Instala `numpy`, `pydantic`, `fastapi` y `uvicorn` |
| La app | Node 22.12 o más nuevo. Instala React, Vite, TypeScript y MapLibre GL |
| Rehacer los datos | Además, `pandas`, `scipy`, `scikit-learn`, `osmium`, `pyarrow`, `requests` y `lxml`, y las descargas de las fuentes. Las de la noche y la altura piden también `rasterio`, `h5py`, `fsspec` y `aiohttp` |
| Desplegar en AWS | Una cuenta, AWS CLI, SAM CLI y Docker |

Las versiones mínimas de cada paquete están en [`pyproject.toml`](../../pyproject.toml) y en [`app/package.json`](../../app/package.json). No hay base de datos que instalar: el motor responde desde los archivos de `dreemgo/datos/`, que ya vienen en el repositorio.

## Instalar y correr

Con el repositorio clonado, en dos terminales.

**1. El API**, desde la raíz:

```bash
pip install -e ".[api]"
python -m uvicorn dreemgo.api.app:app --port 8000
```

Queda en <http://localhost:8000>. Para comprobarlo: <http://localhost:8000/v1/salud> responde `"estado": "ok"` con la versión de los datos, y <http://localhost:8000/v1/docs> muestra los endpoints para probarlos a mano.

**2. La app**, en otra terminal:

```bash
cd app
npm ci
npm run dev
```

Queda en <http://localhost:5173> y le pregunta al API de la otra terminal.

**Para probar que un municipio publica un evento**, el API tiene que arrancar con una clave, que es la que después se escribe en el formulario de la app:

```bash
# Git Bash, macOS o Linux
DREEMGO_CLAVE_PUBLICADOR=una-clave-para-probar python -m uvicorn dreemgo.api.app:app --port 8000
```

```powershell
# PowerShell
$env:DREEMGO_CLAVE_PUBLICADOR = "una-clave-para-probar"
python -m uvicorn dreemgo.api.app:app --port 8000
```

Las pantallas de la app y cómo verla en un celular antes de desplegar están en [`app/README.md`](../../app/README.md).

## Probar

```bash
pip install -e ".[api,dev,pipeline]"
pytest                      # el motor, el API, el pipeline y la evaluación

cd app
npm test                    # la app, con un API de mentira
npx playwright install chromium
npm run e2e                 # la app en un navegador, contra el API de verdad
```

Lo mismo corre en cada pull request, junto con la construcción de las imágenes del API ([`.github/workflows/ci.yml`](../../.github/workflows/ci.yml)).

## Desplegar

- **La app** se publica sola en GitHub Pages con cada cambio de `main` ([`app/README.md`](../../app/README.md#publicarla)). La dirección del API la toma de la variable `API_URL` del repositorio.
- **El API corre hoy en Render**, gratis, en <https://alejandros-team.onrender.com>, y se vuelve a desplegar solo con cada cambio de `main`. Se duerme a los 15 minutos sin uso, y la primera consulta después tarda cerca de un minuto. Lo que publican los municipios vive ahí en un archivo del contenedor y se pierde cuando se reinicia. Los pasos están en [`infra/README.md`](../../infra/README.md#en-render-gratis-y-sin-tarjeta), y el porqué, en la [decisión 0012](../../docs/decisiones/0012-host-gratuito-render.md).
- **El destino es AWS**: una función Lambda con imagen de contenedor detrás de una HTTP API, con una tabla de DynamoDB donde lo publicado sí dura. Son cuatro comandos, descritos en [`infra/README.md`](../../infra/README.md). Un Space de Hugging Face ya no sirve: Hugging Face pasó los Spaces de Docker a plan de pago.

## Rehacer los datos

Los datos del motor salen del pipeline, que parte de las descargas de las fuentes: el inventario y las fichas de MINCETUR, OpenStreetMap, Overture Maps, Open-Meteo, las nubes de GOES-16 y los METAR de NOAA, las luces de VIIRS, la altura del terreno de Terrain Tiles y las rutas aéreas que salen de Lima. La lista de fotos que muestra la app sale del mismo pipeline, con Wikidata y Wikimedia Commons. El orden y lo que tarda cada paso están en [`pipeline/README.md`](../../pipeline/README.md); las licencias de cada fuente, en [`DATA_LICENSES.md`](../../DATA_LICENSES.md).

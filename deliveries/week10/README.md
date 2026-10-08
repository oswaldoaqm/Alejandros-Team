# DreemGO — Semana 10 · Prototipo funcional

**Primera versión funcional del producto**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Entrega: 14 de octubre de 2026

El prototipo es el producto que vive en este repositorio: un motor de itinerarios con su API, la app web que lo usa y el pipeline que arma sus datos. Esta carpeta trae el informe y dice dónde está cada cosa que pide el enunciado, en vez de guardar una segunda copia del código y de los datos.

## Qué pide el enunciado y dónde está

| Entregable | Dónde |
|---|---|
| Código completo del prototipo | [`dreemgo/`](../../dreemgo/) (motor y API), [`app/`](../../app/) (app web), [`pipeline/`](../../pipeline/) (datos), [`infra/`](../../infra/) (imagen y despliegue) y [`tests/`](../../tests/) |
| Datos procesados, en CSV y JSON | [`data/procesados/`](../../data/procesados/), con su diccionario |
| Artefactos analíticos | [`dreemgo/datos/`](../../dreemgo/datos/): lo que el motor carga al arrancar, con su manifiesto y la huella de cada archivo |
| Informe del prototipo | [`PrototypeReport.md`](./PrototypeReport.md). Las cifras de lo que propone el motor salen de [`code/cobertura.py`](./code/cobertura.py) |
| URL del prototipo | La app: <https://oswaldoaqm.github.io/Alejandros-Team/>. El API que le responde: <https://alejandros-team.onrender.com>, con sus endpoints en [`/v1/docs`](https://alejandros-team.onrender.com/v1/docs) |
| Instalación, ejecución, dependencias y despliegue | Este archivo |

Lo que se entrega queda congelado en la etiqueta `entrega/semana-10`, que se pone en el último commit de `main` antes de la fecha ([decisión 0005](../../docs/decisiones/0005-historial-y-erratas.md)).

## Falta en esta carpeta

- `PresentationWeek10`, la presentación.
- Las capturas o el video corto de la demostración.

## Qué hace falta

| Para | Hace falta |
|---|---|
| El API y el motor | Python 3.11 o más nuevo. Instala `numpy`, `pydantic`, `fastapi` y `uvicorn` |
| La app | Node 22.12 o más nuevo. Instala React, Vite, TypeScript y MapLibre GL |
| Rehacer los datos | Además, `pandas`, `scipy`, `scikit-learn`, `osmium`, `requests` y `lxml`, y las descargas de las fuentes |
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
pytest                      # el motor, el API y el pipeline

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

Los datos del motor salen del pipeline, que parte de las descargas de las fuentes (inventario y fichas de MINCETUR, OpenStreetMap y Open-Meteo). La lista de fotos que muestra la app sale del mismo pipeline, con Wikidata y Wikimedia Commons. El orden y lo que tarda cada paso están en [`pipeline/README.md`](../../pipeline/README.md); las licencias de cada fuente, en [`DATA_LICENSES.md`](../../DATA_LICENSES.md).

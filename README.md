# DreemGO

**Inteligencia de rutas en Perú**

Plataforma que convierte intereses, temporada y presupuesto en un itinerario de viaje optimizado dentro del
Perú. Combina el inventario turístico oficial de MINCETUR con datos climáticos y algoritmos de clustering y
optimización de rutas, para entregar en segundos lo que hoy toma días de búsqueda dispersa.

> Proyecto final del curso **DS3022 — Desarrollo de Producto de Datos**
> Universidad de Ingeniería y Tecnología (UTEC) · Prof. Germain Garcia-Zanabria · Ciclo 2026-2

| | |
|---|---|
| **La app** | <https://oswaldoaqm.github.io/Alejandros-Team/> |
| **El API** | <https://alejandros-team.onrender.com/v1/docs>, en un host gratuito que se duerme sin uso: la primera consulta después tarda cerca de un minuto |
| **Correrlo en tu máquina** | [Probarlo](#probarlo), más abajo |
| **La entrega en curso** | [`deliveries/week10/`](./deliveries/week10/): el prototipo funcional y su [informe](./deliveries/week10/PrototypeReport.md) |
| **Qué recibe y qué devuelve el API** | [`docs/CONTRATO.md`](./docs/CONTRATO.md) |
| **El plan, con fechas y estado** | [`docs/PLAN.md`](./docs/PLAN.md) |
| **Por qué cada cosa es como es** | [`docs/decisiones/`](./docs/decisiones/) |

---

## Probarlo

La app publicada ya responde: le pregunta al API, desplegado en Render. El producto completo corre también en una computadora con Python 3.11 o más nuevo y Node 22.12 o más nuevo, en dos terminales:

```bash
# 1. El API, desde la raíz del repositorio
pip install -e ".[api]"
python -m uvicorn dreemgo.api.app:app --port 8000     # http://localhost:8000/v1/docs
```

```bash
# 2. La app, en otra terminal
cd app
npm ci
npm run dev                                           # http://localhost:5173
```

Las pantallas de la app, sus pruebas y cómo se publica están en [`app/README.md`](./app/README.md); cómo se despliega el API, en [`infra/README.md`](./infra/README.md).

Una municipalidad o una oficina de destino puede publicar un evento desde la app («Para municipios: publicar
un evento») o con `POST /v1/eventos` y la clave que le da el equipo. Lo publicado sale en el calendario y en
las rutas que pasan cerca en esas fechas, con el nombre de quien lo publicó, y no cambia qué rutas se proponen
ni en qué orden. El porqué está en la [decisión 0011](./docs/decisiones/0011-eventos-publicados.md), y cómo se
guarda en cada entorno, en [`infra/README.md`](./infra/README.md).

---

## El problema

Planificar un viaje dentro del Perú obliga a resolver a mano una ecuación de tres variables que ninguna
herramienta existente resuelve junta: **qué ver** según los intereses propios, **cuándo ir** según el clima y la
temporada de cada destino, y **cuánto cuesta** encadenar esos destinos en una ruta viable. La información está
fragmentada entre inventarios oficiales, reseñas subjetivas y reportes climáticos aislados, y el viajero termina
comparando pestañas en vez de decidir.

La gran mayoría de los viajeros internos peruanos organiza sus viajes por cuenta propia, sin paquetes de
agencia. Es un público numeroso que hoy hace manualmente un trabajo de optimización que un producto de datos
puede automatizar.

| | |
|---|---|
| **Entrada del usuario** | Intereses, temporada, presupuesto y días disponibles |
| **Salida del producto** | Itinerario ordenado con secuencia geográfica coherente, ventana temporal recomendada y costo estimado |
| **Alcance** | Destinos dentro del territorio peruano |

En el inventario oficial, Lima y Cusco concentran 1 605 recursos (25,8 %). Los **4 620 restantes — el 74,2 %**
están repartidos en las otras 23 regiones y quedan fuera del circuito que absorbe el grueso de la demanda.

---

## Equipo

| Integrante | Rol | Responsabilidades |
|---|---|---|
| **Miguel** | Data Engineer / Cloud Architect | Pipeline de ingesta, transformación a formatos ligeros, infraestructura cloud y contenedores |
| **Alejandro** | Data Scientist / ML Engineer | Análisis exploratorio, calidad de datos, clustering de destinos por perfil de interés, selección y validación de modelos |
| **Diego** | Backend & Algorithms Engineer | Microservicios, estructuras de datos y cálculo de rutas geográficas |
| **Christopher** | Frontend Developer & Product Owner | Interfaz interactiva, Data Product Canvas, requisitos funcionales y de negocio |

---

## Estructura del repositorio

```
Alejandros-Team/
├── README.md
├── pyproject.toml                  el paquete de Python: dependencias, ruff y pytest
├── LICENSE                         licencia del código (MIT)
├── DATA_LICENSES.md                licencia de cada fuente de datos y qué exige
├── .github/workflows/              integración continua y publicación de la app
├── dreemgo/                        motor y API (FastAPI); el contrato está en dreemgo/contrato.py. Los eventos
│                                   que publican los municipios: publicados.py y almacen.py
│   ├── motor/                      del pedido al viaje: valor, días, itinerario, costo y avisos
│   └── datos/                      los artefactos que carga el motor, con su manifiesto
├── pipeline/                       convierte las descargas en los datos del motor: fichas, maestro, eventos,
│                                   red vial, bases, clima y artefactos; y elige las fotos que muestra la app
│   ├── adquisicion/                descargas de las fuentes: inventario, OpenStreetMap, clima, fichas y fotos
│   └── referencia/                 tablas escritas a mano: ciudades de origen, intereses, santoral, fotos
│                                   revisadas…
├── data/procesados/                maestro v3, eventos, tiempos de viaje, bases y clima, con su diccionario
├── app/                            la app web: React, Vite, TypeScript y MapLibre
├── infra/                          imagen del API y cómo desplegarlo: en AWS con SAM, con la tabla de eventos
│                                   publicados, o gratis en Render
├── tests/                          pruebas del contrato, del API y del pipeline
├── docs/                           plan, contrato de la API (con su esquema OpenAPI) y registro de decisiones
└── deliveries/                     lo que pide cada hito del curso, una carpeta por semana
    ├── week04/                     tema, equipo y selección de dataset
    ├── week05/                     propuesta, Data Product Canvas y requerimientos
    ├── week06/                     análisis exploratorio y selección de modelo
    ├── week07/                     Delivery 1: definición integrada del proyecto
    └── week10/                     prototipo funcional: el informe y dónde está cada cosa
```

El plan del producto, con fechas y criterios de terminado, está en [`docs/PLAN.md`](./docs/PLAN.md); lo que recibe y devuelve el API, en [`docs/CONTRATO.md`](./docs/CONTRATO.md); y el porqué de cada decisión, en [`docs/decisiones/`](./docs/decisiones/).

Cada hito del curso vive en su propia carpeta bajo `deliveries/weekXX/`, y el `README.md` de cada una dice qué trae. Lo entregado en cada fecha queda intacto en las etiquetas `entrega/semana-XX`, y lo que se corrigió después está en el `ERRATA.md` de cada carpeta.

---

## Datos

**Inventario Nacional de Recursos Turísticos** — Ministerio de Comercio Exterior y Turismo (MINCETUR)
Licencia [ODC-BY](https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos) · 6 225 registros · 25 regiones · fecha de corte 2026-09-29

> **Advertencia para quien use esta fuente:** las columnas `LATITUD` y `LONGITUD` vienen **intercambiadas desde
> el origen**. Con las etiquetas originales, el 0 % de los recursos cae dentro del territorio peruano; al
> intercambiarlas, el 100 %. Sin corregirlo, cualquier análisis espacial falla en silencio, sin lanzar error.
> El análisis completo está en [`deliveries/week04/data/data_quality.md`](./deliveries/week04/data/data_quality.md).
> En el corte del 29 de septiembre, además, el recurso 14707 trae corrido el punto decimal;
> [`pipeline/inventario.py`](./pipeline/inventario.py) corrige las dos cosas y deja marcada cada coordenada.

El dataset enriquecido de la Semana 5 añade `ALTITUD`, `DISTANCIA_CAPITAL_KM`, el índice de lejanía
(`INDICE_COSTO_LOGISTICO` en el CSV) y `ZONA_CLIMATICA` sobre el inventario base ([`deliveries/week05/data/`](./deliveries/week05/data/)).

La Semana 6 suma las **6 129 fichas oficiales** de MINCETUR, con la jerarquía de cada recurso verificada
fila a fila: la columna del dataset maestro solo coincide con la ficha en el 59,7 %
([`deliveries/week06/docs/Data_Dictionary.md`](./deliveries/week06/docs/Data_Dictionary.md)), y **diez años de
climatología mensual** (2014-2023) de [Open-Meteo Archive](https://open-meteo.com/) para las 24 regiones.

La fase 1 rehace los datos sobre el corte del 29 de septiembre. [`pipeline/`](./pipeline/) lee las 6 225 fichas
oficiales y deja en [`data/procesados/`](./data/procesados/) el **maestro v3**, una fila por recurso con la
fuente de cada campo; el **calendario de los 758 acontecimientos**, con la regla de su fecha y una precisión
medida sobre una muestra anotada a mano; los **tiempos de viaje** sobre la red vial de OpenStreetMap,
calibrada con los recorridos de las fichas (22 % de error medio), con el tren a Machu Picchu y los botes del
Titicaca, las Ballestas y la Amazonía; **dónde se duerme en cada polo**, y el **clima de cada polo mes a
mes**. El motor ([`dreemgo/motor/`](./dreemgo/motor/)) carga todo eso y responde `/v1/viajes` según el
[contrato](./docs/CONTRATO.md).

Fuentes complementarias en uso: [Open-Meteo](https://open-meteo.com/) (clima diario por polo),
[OpenStreetMap](https://www.openstreetmap.org/) (vías, trenes, botes, pueblos y hospedajes) y
[Wikimedia Commons](https://commons.wikimedia.org/) (una foto de licencia libre para los lugares y los pueblos
que la tienen, elegida con [Wikidata](https://www.wikidata.org/)). Prevista:
[datosTurismo](https://datosturismo.mincetur.gob.pe/) (flujos y gasto).

Este repositorio contiene únicamente datos abiertos con licencia que permite su redistribución. De las fotos
guarda la lista, con el autor y la licencia de cada una, y ninguna imagen: la app se las pide a Wikimedia. La
licencia de cada fuente y lo que exige están en [`DATA_LICENSES.md`](./DATA_LICENSES.md).

---

## El modelo

**TA-01 · Agrupamiento espacio-temporal.** Enlace completo sobre una distancia de viaje que combina haversine
y desnivel. El algoritmo **acota el diámetro del polo por construcción**: ningún par de recursos del mismo polo
supera el umbral de 80 km de viaje efectivo.

| | v1 · HDBSCAN | **v2 · enlace completo** |
|---|---:|---:|
| Polos | 81 | **222** |
| Recursos utilizables | 3 760 (61,0 %) | **4 786 (77,7 %)** |
| Diámetro máximo | 427,9 km · **21,1 h** | 79,4 km · **3,9 h** |
| Desnivel máximo | 4 667 m | **1 296 m** |

La partición por departamento obtiene **silueta negativa**: el recurso promedio queda más cerca de los recursos
de otro departamento que de los de su propio departamento. La división política del Perú no describe la
geografía turística, y ese es el motivo de que el producto agrupe.

El detalle —barridos, ablación, la auditoría de la propia comparación y por qué la silueta no puede decidir
entre los dos modelos— está en
[`deliveries/week06/ModelSelection.md`](./deliveries/week06/ModelSelection.md).

Esos 222 grupos son el agrupamiento. El motor propone entre **194 polos**: cuando varios grupos duermen en el
mismo pueblo, como los cuatro de Huaraz, son un solo lugar al que ir y se juntan en uno
([decisión 0013](./docs/decisiones/0013-un-polo-por-pueblo.md)).

---

## Entregas y cronograma

| Semana | Fecha | Hito | Carpeta | Estado |
|---|---|---|---|---|
| 4 | 2 sep 2026 | Tema, equipo y selección de dataset | [`week04/`](./deliveries/week04/) | Entregado |
| 5 | 9 sep 2026 | Propuesta, Data Product Canvas y requisitos | [`week05/`](./deliveries/week05/) | Entregado |
| 6 | 16 sep 2026 | Análisis exploratorio y selección de modelo | [`week06/`](./deliveries/week06/) | Entregado |
| 7 | 23 sep 2026 | **Delivery 1** — definición integrada del proyecto | [`week07/`](./deliveries/week07/) | Entregado |
| 10 | 14 oct 2026 | Prototipo funcional | [`week10/`](./deliveries/week10/) | En curso |
| 12 | 28 oct 2026 | Prototipo refinado, evaluación y casos de estudio | | Pendiente |
| 15 | 18 nov 2026 | Presentación final y **Delivery 2** | | Pendiente |

Los documentos de cada una:

| Documento | Ruta |
|---|---|
| Nota de calidad de datos | [`week04/data/data_quality.md`](./deliveries/week04/data/data_quality.md) |
| Propuesta de proyecto | [`week05/ProjectProposal.pdf`](./deliveries/week05/ProjectProposal.pdf) |
| Data Product Canvas | [`week05/DataProductCanvas.pdf`](./deliveries/week05/DataProductCanvas.pdf) |
| Requerimientos y diseño | [`week05/Requirements.md`](./deliveries/week05/Requirements.md) |
| Análisis exploratorio | [`week06/DataAnalysis.md`](./deliveries/week06/DataAnalysis.md) |
| Selección de modelo | [`week06/ModelSelection.md`](./deliveries/week06/ModelSelection.md) |
| Diccionario de datos | [`week06/docs/Data_Dictionary.md`](./deliveries/week06/docs/Data_Dictionary.md) |
| Presentación de la Delivery 1 | [`week07/PresentationWeek07.pdf`](./deliveries/week07/PresentationWeek07.pdf) |
| Informe del prototipo | [`week10/PrototypeReport.md`](./deliveries/week10/PrototypeReport.md) |

---

## Reproducir

Las entregas de las semanas 4 a 7 se reproducen con el código de su carpeta:

```bash
git clone https://github.com/oswaldoaqm/Alejandros-Team.git
cd Alejandros-Team
pip install pandas scikit-learn matplotlib scipy requests beautifulsoup4

# Semana 4 — verificación de calidad del inventario base
python deliveries/week04/code/data_quality_check.py deliveries/week04/data/sample.csv

# Semana 6 — modelo elegido, puntaje, estacionalidad, ruta y consulta (no requiere red, ~1 min)
cd deliveries/week06/code
python ta01_polos_acotados.py  ../data/processed/dreemgo_master_dataset.csv
python ta03_score_polo.py      ../data/processed/polos_asignados_v2.csv 0.30
python ta05_estacionalidad.py
python ta04_evaluacion.py 6
python consulta.py --mes 7 --dias 6 --altitud-max 3500
```

El primero regenera las cifras de la nota de calidad. Los de la semana 6 regeneran los archivos de `data/processed/` que usa la consulta, y la consulta verifica en cada corrida los criterios de aceptación de RF-01, RF-02 y RNF-01.
Las instrucciones completas, incluida la parte que sí necesita red, están en
[`deliveries/week06/README.md`](./deliveries/week06/README.md).

Los datos v3 salen del pipeline. Primero se bajan las fuentes con los scripts de
[`pipeline/adquisicion/`](./pipeline/adquisicion/), que las dejan fuera de git (las fichas tardan unas horas la
primera vez):

```bash
pip install -e ".[api,pipeline,dev]"
python pipeline/adquisicion/descargar_inventario.py
python pipeline/adquisicion/descargar_fichas_html.py
python pipeline/adquisicion/descargar_osm.py
python pipeline/adquisicion/descargar_clima_polos.py   # días: respeta la cuota gratuita de Open-Meteo
python -m pipeline.maestro     # data/procesados/maestro_v3.csv
python -m pipeline.eventos     # data/procesados/eventos_v3.csv
python -m pipeline.tiempos     # tiempos de viaje (carretera, tren y bote) y bases, unos 9 minutos
python -m pipeline.clima       # clima por polo y mes
python -m pipeline.artefactos --version 2026.10.3   # dreemgo/datos/
python pipeline/adquisicion/descargar_fotos.py         # qué fotos hay en Wikidata y Wikimedia Commons, unos 15 minutos
python -m pipeline.fotos       # app/public/fotos.json: qué foto va con cada lugar
pytest
```

Con eso quedan los datos que usa el motor, y el producto se corre como dice [Probarlo](#probarlo).

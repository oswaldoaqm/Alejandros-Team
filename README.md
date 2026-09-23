# DreemGO

**Inteligencia de rutas en Perú**

Plataforma que convierte intereses, temporada y presupuesto en un itinerario de viaje optimizado dentro del
Perú. Combina el inventario turístico oficial de MINCETUR con datos climáticos y algoritmos de clustering y
optimización de rutas, para entregar en segundos lo que hoy toma días de búsqueda dispersa.

> Proyecto final del curso **DS3022 — Desarrollo de Producto de Datos**
> Universidad de Ingeniería y Tecnología (UTEC) · Prof. Germain Garcia-Zanabria · Ciclo 2026-2

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

En el inventario oficial, Lima y Cusco concentran 1 585 recursos (25,7 %). Los **4 575 restantes — el 74,3 %**
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

## Datos

**Inventario Nacional de Recursos Turísticos** — Ministerio de Comercio Exterior y Turismo (MINCETUR)
Licencia [ODC-BY](https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos) · 6 160 registros · 25 regiones · fecha de corte 2026-08-31

> **Advertencia para quien use esta fuente:** las columnas `LATITUD` y `LONGITUD` vienen **intercambiadas desde
> el origen**. Con las etiquetas originales, el 0 % de los recursos cae dentro del territorio peruano; al
> intercambiarlas, el 100 %. Sin corregirlo, cualquier análisis espacial falla en silencio, sin lanzar error.
> El análisis completo está en [`deliveries/week04/data/data_quality.md`](./deliveries/week04/data/data_quality.md).

El dataset enriquecido de la Semana 5 añade `ALTITUD`, `DISTANCIA_CAPITAL_KM`, `INDICE_LEJANIA` y
`ZONA_CLIMATICA` sobre el inventario base ([`deliveries/week05/data/`](./deliveries/week05/data/)).

La Semana 6 suma la **jerarquía oficial** de cada recurso, extraída de las fichas de MINCETUR y verificada
([`deliveries/week06/docs/Data_Dictionary.md`](./deliveries/week06/docs/Data_Dictionary.md)), y **diez años de
climatología mensual** (2014-2023) de [Open-Meteo Archive](https://open-meteo.com/) para las 24 regiones.

Fuentes complementarias previstas: [datosTurismo](https://datosturismo.mincetur.gob.pe/) (flujos y gasto),
[Open-Meteo](https://open-meteo.com/) (climatología histórica y modelo de elevación) y
[OpenStreetMap](https://www.openstreetmap.org/) (geometría vial).

Este repositorio contiene únicamente datos abiertos con licencia que permite su redistribución.

---

## Estructura del repositorio

```
Alejandros-Team/
├── README.md
└── deliveries/
    ├── week04/                     Tema, equipo y selección de dataset
    │   ├── README.md
    │   ├── DreemGO_pitch.pdf
    │   ├── code/data_quality_check.py
    │   └── data/                   sample.csv · data_dictionary.csv
    │                               acquisition.md · data_quality.md
    ├── week05/                     Propuesta, Data Product Canvas y requerimientos
    │   ├── README.md
    │   ├── ProjectProposal.pdf · .docx
    │   ├── DataProductCanvas.pdf · .md
    │   ├── Requirements.md
    │   ├── PresentationWeek05.pdf
    │   ├── assets/                 wireframes, storyboards y diagrama UML
    │   ├── code/                   enriquecimiento, clima, altitud y features
    │   └── data/                   dataset_enriched.csv · data_dictionary_v2.csv
    ├── week06/                     Análisis exploratorio y selección de modelo
    │   ├── README.md
    │   ├── DataAnalysis.md         EDA, hallazgos y limitaciones
    │   ├── ModelSelection.md       baselines, métricas y modelo elegido
    │   ├── code/                   scraping, clima y los scripts de TA-01
    │   ├── data/raw/ · data/processed/
    │   └── docs/                   diccionario, figura y métricas
    └── week07/                     Delivery 1 — Definición Integrada
        ├── README.md
        ├── DataProductCanvas.pdf   Lienzo de producto actualizado
        ├── Requirements.md         Requisitos funcionales y de negocio
        ├── E-R.png                 Diagrama Entidad-Relación de la App
        ├── Cloud_Architecture.drawio.png Diagrama de Arquitectura Cloud
        ├── code/                   Modelos TA-01, TA-02, TA-03, TA-04
        ├── data/raw/ · data/processed/ (Dataset final de modelos)
        └── docs/                   Data_Dictionary.md actualizado (V3)
```

Cada hito del curso vive en su propia carpeta bajo `deliveries/weekXX/`.

---

## El modelo

**TA-01 · Agrupamiento espacio-temporal.** Enlace completo sobre una distancia de viaje que combina haversine
y desnivel. El algoritmo **acota el diámetro del polo por construcción**: ningún par de recursos del mismo polo
supera el umbral de 80 km de viaje efectivo.

| | v1 · HDBSCAN | **v2 · enlace completo** |
|---|---:|---:|
| Polos | 81 | **222** |
| Recursos utilizables | 3 760 (61,0 %) | **4 786 (77,7 %)** |
| Diámetro máximo | 427,9 km · **17,1 h** | 79,4 km · **3,2 h** |
| Desnivel máximo | 4 667 m | **1 296 m** |

La partición por departamento obtiene **silueta negativa**: el recurso promedio queda más cerca de los recursos
de otro departamento que de los de su propio departamento. La división política del Perú no describe la
geografía turística, y ese es el motivo de que el producto agrupe.

El detalle —barridos, ablación, la auditoría de la propia comparación y por qué la silueta no puede decidir
entre los dos modelos— está en
[`deliveries/week06/ModelSelection.md`](./deliveries/week06/ModelSelection.md).

---

## Enlaces de las entregas

| Documento | Ruta |
|---|---|
| Data Product Canvas | [`week07/DataProductCanvas.pdf`](./deliveries/week07/DataProductCanvas.pdf) |
| Requerimientos y diseño | [`week07/Requirements.md`](./deliveries/week07/Requirements.md) |
| Diagrama Entidad-Relación | [`week07/E-R.png`](./deliveries/week07/E-R.png) |
| Arquitectura Cloud | [`week07/Cloud_Architecture.drawio.png`](./deliveries/week07/Cloud_Architecture.drawio.png) |
| Diccionario de datos (Final) | [`week07/docs/Data_Dictionary.md`](./deliveries/week07/docs/Data_Dictionary.md) |
| Análisis exploratorio | [`week06/DataAnalysis.md`](./deliveries/week06/DataAnalysis.md) |
| Selección de modelo (TA-01) | [`week06/ModelSelection.md`](./deliveries/week06/ModelSelection.md) |
| Nota de calidad de datos | [`week04/data/data_quality.md`](./deliveries/week04/data/data_quality.md) |

---

## Reproducir

```bash
git clone https://github.com/oswaldoaqm/Alejandros-Team.git
cd Alejandros-Team
pip install pandas scikit-learn matplotlib scipy requests beautifulsoup4

# Ejecución de Modelos Predictivos y de Recomendación (Semana 7)
cd deliveries/week07/code
# TA-01: Clustering espacial de Polos
python ta01_modelo_final.py ../data/processed/dreemgo_master_dataset.csv
# TA-02: Forecasting de Clima y Estacionalidad
python ta02_estacionalidad.py
# TA-03: Scoring B2B para Comercios y Ferias Locales
python ta03_score_polo.py
# TA-04: Motor de Enrutamiento Geográfico (Evaluación)
python ta04_evaluacion.py
```

Las instrucciones completas, incluida la generación de la data sintética y los scripts ETL de Mincetur, están documentadas en
[`deliveries/week07/README.md`](./deliveries/week07/README.md).

---

## Cronograma

| Semana | Fecha | Hito | Estado |
|---|---|---|---|
| 4 | 2 sep 2026 | Tema, equipo y selección de dataset | Entregado |
| 5 | 9 sep 2026 | Propuesta, Data Product Canvas y requisitos | Entregado |
| 6 | 16 sep 2026 | Análisis exploratorio y selección de modelo | Entregado |
| 7 | 23 sep 2026 | **Delivery 1** — definición integrada del proyecto | Entregado |
| 10 | 14 oct 2026 | Prototipo funcional | Pendiente |
| 12 | 28 oct 2026 | Prototipo refinado, evaluación y casos de estudio | Pendiente |
| 15 | 18 nov 2026 | Presentación final y **Delivery 2** | Pendiente |

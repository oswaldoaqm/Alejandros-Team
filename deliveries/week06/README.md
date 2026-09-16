# DreemGO — Semana 6

**Análisis exploratorio y selección de modelo**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Entrega: 16 de septiembre de 2026

---

## Qué se hizo esta semana

1. Se extrajo de las fichas oficiales de MINCETUR la **jerarquía oficial** de cada recurso, el campo que el CSV de datos abiertos no publica y del que depende poder ordenar destinos por importancia.
2. Se descargaron **diez años de climatología mensual** (2014–2023) de Open-Meteo Archive para las 24 regiones, con lo que la estacionalidad deja de ser una regla inventada y pasa a ser un dato.
3. Se implementó y evaluó **TA-01**, el agrupamiento espacio-temporal, contra dos baselines y con métricas reproducibles.
4. Se prototipó el **componente de eventos con ventana temporal** — el lado de la oferta del producto — sobre un dataset simulado.

---

## Contenido

```
week06/
├── README.md                       este archivo
├── DataAnalysis.md                 comprensión de datos, EDA, hallazgos y limitaciones
├── ModelSelection.md               modelos, baselines, métricas y modelo elegido
├── code/
│   ├── scraper_mincetur.py         extracción de la ficha oficial (jerarquía)
│   ├── clean_impute_dataset.py     imputación posterior  ⚠ ver nota abajo
│   ├── build_master_dataset.py     ⚠ SUPERADO — genera datos al azar, no ejecutar
│   ├── fetch_climate_history.py    10 años de clima mensual desde Open-Meteo
│   ├── discretize_climate.py       discretización de lluvia y temperatura
│   ├── generate_commerce_data.py   generador del dataset SIMULADO de eventos
│   ├── ta01_comparativa_modelos.py baselines + barrido de k y de min_cluster_size
│   ├── ta01_modelo_final.py        modelo elegido, perfiles y cobertura
│   ├── ta01_auditoria_comparacion.py  verificación de que la comparación es justa
│   ├── ta01_figura.py              figura de selección de modelo
│   ├── DreemGO_Advanced_EDA.ipynb
│   └── DreemGO_Predictive_Engine.ipynb
├── data/
│   ├── raw/
│   │   └── dataset_enriched.csv            entrada: salida de la semana 5
│   └── processed/
│       ├── dreemgo_master_dataset.csv      6 160 × 19 · dimensión de recursos
│       ├── historial_clima_regiones.csv    2 880 filas · hechos de clima
│       ├── comercios_ferias_locales.csv    500 filas · SIMULADO
│       └── clusters_asignados.csv          etiqueta de polo por recurso
└── docs/
    ├── Data_Dictionary.md          diccionario de las tres tablas
    ├── ta01_seleccion_modelo.png   figura de la comparación de modelos
    ├── comparativa_modelos.csv     métricas de cada modelo
    ├── barrido_k.csv               barrido completo de K-Means
    └── perfil_clusters_hdbscan.csv perfil de los 81 polos
```

---

## Reproducir

```bash
pip install pandas scikit-learn matplotlib scipy requests beautifulsoup4
```

El pipeline tiene dos mitades independientes. Los scripts leen rutas relativas desde `code/`.

### 1 · Datos

```bash
cd deliveries/week06/code

python scraper_mincetur.py        # ~2 h · una petición por segundo a MINCETUR
python clean_impute_dataset.py    # ver la nota de abajo antes de correrlo
python fetch_climate_history.py   # ~2 min · Open-Meteo Archive
python discretize_climate.py
python generate_commerce_data.py  # genera el dataset SIMULADO de eventos
```

### 2 · Modelo

```bash
python ta01_comparativa_modelos.py  ../data/processed/dreemgo_master_dataset.csv
python ta01_modelo_final.py         ../data/processed/dreemgo_master_dataset.csv
python ta01_auditoria_comparacion.py ../data/processed/dreemgo_master_dataset.csv
python ta01_figura.py               ../data/processed/dreemgo_master_dataset.csv
```

Semilla fija (`random_state=42`). Estos cuatro scripts regeneran **todas** las cifras de `ModelSelection.md` en menos de un minuto, sin volver a tocar la red.

### Cómo leer los CSV

Todos usan separador `;` y codificación UTF-8:

```python
import pandas as pd
df = pd.read_csv("../data/processed/dreemgo_master_dataset.csv", sep=";")
```

---

## Advertencias sobre el código

**`build_master_dataset.py` no debe ejecutarse.** Genera `JERARQUIA_OFICIAL` y `TIPO_INGRESO` con `random.choices()` y escribe sobre el mismo archivo que produce el scraper real. Está marcado en su encabezado y queda solo como registro de un paso intermedio del desarrollo.

**`clean_impute_dataset.py` sobrescribe dos columnas.** Se ejecuta después del scraper y reemplaza `TIPO_INGRESO` y `EPOCA_PROPICIA` por reglas deterministas, con lo que se pierde lo que el scraper había extraído de la ficha. La jerarquía sí sobrevive. El detalle está en `DataAnalysis.md` §3.1 y la corrección está prevista para la Semana 7.

**`comercios_ferias_locales.csv` es simulado.** No contiene comercios ni ferias reales y no admite ninguna afirmación empírica sobre el comercio local peruano.

---

## Resultados principales

### Datos

| | |
|---|---:|
| Inventario total | 6 160 recursos |
| Geolocalizables | 4 915 (79,8 %) |
| Sin coordenadas (folclore y eventos) | 1 245 (20,2 %) |
| Clima histórico | 2 880 filas · 24 regiones × 10 años × 12 meses |

La estacionalidad resultó ser de primer orden: la precipitación media de Cusco pasa de **228 mm en enero a 8 mm en junio**, un factor de 28.

### Modelo — TA-01

**Elegido: HDBSCAN con `min_cluster_size = 15`** sobre latitud, longitud, altitud e índice de lejanía estandarizados.

Comparación controlada, sobre los mismos 3 760 recursos y con número de grupos comparable:

| Modelo | Grupos | Silueta ↑ | Davies-Bouldin ↓ | Radio medio ↓ |
|---|---:|---:|---:|---:|
| **HDBSCAN mcs=15** | 81 | **0,657** | **0,419** | **30,2 km** |
| K-Means k=81 | 74 | 0,626 | 0,570 | 39,3 km |
| Baseline · REGIÓN | 25 | −0,029 | 2,868 | 68,6 km |

La partición por departamento obtiene **silueta negativa**: el recurso promedio está más cerca de los recursos de otro departamento que de los de su propio departamento. La división política no describe la geografía turística.

### Alcance real del producto

| | Recursos | % |
|---|---:|---:|
| Sin coordenadas — no ruteables | 1 245 | 20,2 % |
| Aislados por el modelo | 1 155 | 18,8 % |
| **No encadenables en una ruta** | **2 400** | **39,0 %** |
| Entran a un polo | 3 760 | 61,0 % |

### Dispersión

64 de los 81 polos (75 % de los recursos agrupados) no contienen ningún recurso de Lima ni de Cusco. Y con la jerarquía oficial ya verificada: **hay 451 recursos de jerarquía 3 o 4 fuera del circuito saturado, frente a 203 dentro.**

---

## Lo que queda pendiente

| Pendiente | Semana |
|---|---|
| Re-extraer `TIPO_INGRESO` y `EPOCA_PROPICIA` con columna `ORIGEN_JERARQUIA` | 7 |
| Cruzar la climatología por `REGIÓN × ZONA_CLIMATICA` en vez de solo por región | 7 |
| Perfilamiento semántico por intereses sobre los 187 subtipos | 7 |
| Sembrar el dataset de eventos con los 749 acontecimientos reales del inventario | 7 |
| Ordenamiento de la ruta (TTDP) con baseline de vecino más cercano | 10 |
| Red vial de OpenStreetMap para distancias reales | 10 |

---

## Nota sobre datos restringidos

La extracción de las fichas oficiales se hace con una petición por segundo, agente identificado y caché local. No se incluyen fuentes cuyos términos de servicio restrinjan la redistribución (TripAdvisor, Google Places API).

# DreemGO — Semana 6

**Análisis exploratorio y selección de modelo**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Entrega: 16 de septiembre de 2026

---

## Qué se hizo esta semana

1. Se extrajo de las fichas oficiales de MINCETUR la **jerarquía oficial** de cada recurso, el campo que el CSV de datos abiertos no publica y del que depende poder ordenar destinos por importancia.
2. Se descargaron **diez años de climatología mensual** (2014–2023) de Open-Meteo Archive para las 24 regiones, con lo que la estacionalidad deja de ser una regla inventada y pasa a ser un dato.
3. Se implementó y evaluó **TA-01**, el agrupamiento espacio-temporal, contra dos baselines. Una auditoría posterior detectó que el modelo elegido producía polos de hasta doce horas de punta a punta, y se rehízo con un algoritmo que acota el diámetro por construcción.
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
│   ├── ta01_comparativa_modelos.py v1 · baselines y barridos
│   ├── ta01_modelo_final.py        v1 · HDBSCAN, perfiles y cobertura
│   ├── ta01_auditoria_comparacion.py  auditoría de la comparación
│   ├── ta01_polos_acotados.py      v2 · MODELO ELEGIDO, diámetro acotado
│   ├── ta03_score_polo.py          puntaje del polo con término de novedad
│   ├── fetch_climate_v2.py         clima por región × zona climática (pendiente)
│   ├── ta01_figura.py              figura v1
│   ├── ta01_figura_v2.py           figura v2
│   ├── DreemGO_Advanced_EDA.ipynb
│   └── DreemGO_Predictive_Engine.ipynb
├── data/
│   ├── raw/
│   │   └── dataset_enriched.csv            entrada: salida de la semana 5
│   └── processed/
│       ├── dreemgo_master_dataset.csv      6 160 × 19 · dimensión de recursos
│       ├── historial_clima_regiones.csv    2 880 filas · hechos de clima
│       ├── comercios_ferias_locales.csv    500 filas · SIMULADO
│       ├── clusters_asignados.csv          v1 · etiqueta de polo por recurso
│       ├── polos_asignados_v2.csv          v2 · etiqueta de polo por recurso
│       └── puntos_clima_v2.csv             88 puntos región × zona climática
└── docs/
    ├── Data_Dictionary.md             diccionario de las tres tablas
    ├── ta01_seleccion_modelo.png      figura v1
    ├── ta01_seleccion_modelo_v2.png   figura v2 · la que va en la entrega
    ├── comparativa_modelos.csv        v1 · métricas de cada modelo
    ├── barrido_k.csv                  v1 · barrido de K-Means
    ├── perfil_clusters_hdbscan.csv    v1 · perfil de los 81 polos
    ├── comparativa_polos_v2.csv       v2 · comparativa de modelos
    ├── perfil_polos_v2.csv            v2 · perfil de los 222 polos
    └── puntaje_polos.csv              v2 · puntaje con término de novedad
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
# v1 · baselines, barridos y auditoría de la comparación
python ta01_comparativa_modelos.py   ../data/processed/dreemgo_master_dataset.csv
python ta01_modelo_final.py          ../data/processed/dreemgo_master_dataset.csv
python ta01_auditoria_comparacion.py ../data/processed/dreemgo_master_dataset.csv

# v2 · modelo elegido, puntaje y figura
python ta01_polos_acotados.py        ../data/processed/dreemgo_master_dataset.csv
python ta03_score_polo.py            ../data/processed/polos_asignados_v2.csv 0.30
python ta01_figura_v2.py             ../data/processed/dreemgo_master_dataset.csv
```

Semilla fija (`random_state=42`); el enlace completo es determinista. Regeneran **todas** las cifras de `ModelSelection.md` en un par de minutos, sin volver a tocar la red. El paso de v2 construye una matriz de distancias de 4 915 × 4 915 (97 MB en memoria).

### 3 · Pendiente de ejecutar

```bash
python fetch_climate_v2.py        # ~15 min · 88 puntos región × zona climática
```

Reemplaza la climatología por región (24 puntos) por una por piso ecológico (88 puntos), que cubre el 99,3 % de los recursos. Ver `DataAnalysis.md` §5.3.

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

**Elegido: enlace completo sobre distancia de viaje, umbral 80 km.** El enlace completo acota el diámetro del polo por construcción: ningún par de recursos del mismo polo supera el umbral.

| | v1 · HDBSCAN | **v2 · enlace completo** |
|---|---:|---:|
| Polos | 81 | **222** |
| Recursos utilizables | 3 760 (61,0 %) | **4 786 (77,7 %)** |
| Diámetro máximo | 427,9 km · **17,1 h** | 79,4 km · **3,2 h** |
| Desnivel máximo | 4 667 m | **1 296 m** |
| Polos de más de 4 h | ~15 | **0** |

La partición por departamento obtiene **silueta negativa** en cualquier configuración: el recurso promedio está más cerca de los recursos de otro departamento que de los de su propio departamento. La división política no describe la geografía turística.

Y un hallazgo de método: **la silueta no es un árbitro neutral.** HDBSCAN gana en el espacio estandarizado (0,657 contra 0,160) y el enlace completo gana en la métrica de viaje (0,462 contra 0,366). Cada modelo gana en el espacio que optimiza, así que la elección se decide por criterios de producto.

### Alcance real del producto

| | Recursos | % |
|---|---:|---:|
| Sin coordenadas — no ruteables | 1 245 | 20,2 % |
| Sin polo (no alcanzan el mínimo) | 129 | 2,1 % |
| **No encadenables en una ruta** | **1 374** | **22,3 %** |
| Entran a un polo | 4 786 | 77,7 % |

### Dispersión

172 de los 222 polos (73 % de los recursos agrupados) no contienen ningún recurso de Lima ni de Cusco. Y con la jerarquía oficial ya verificada: **hay 451 recursos de jerarquía 3 o 4 fuera del circuito saturado, frente a 203 dentro.**

Ordenar solo por jerarquía concentraba: el top 10 salía con 60 % de polos con Lima o Cusco sobre una base del 23 %. Con el término de novedad a λ = 0,3 baja a 30 % perdiendo menos del 2 % de jerarquía media.

---

## Lo que queda pendiente

| Pendiente | Semana |
|---|---|
| Re-extraer `TIPO_INGRESO` y `EPOCA_PROPICIA` con columna `ORIGEN_JERARQUIA` | 7 |
| Ejecutar `fetch_climate_v2.py`: clima por `REGIÓN × ZONA_CLIMATICA`, 88 puntos en vez de 24 | 7 |
| Decidir qué se hace con el presupuesto: no hay ninguna columna monetaria en el dataset | 7 |
| Perfilamiento semántico por intereses sobre los 187 subtipos | 7 |
| Sembrar el dataset de eventos con los 749 acontecimientos reales del inventario | 7 |
| Ordenamiento de la ruta (TTDP) con baseline de vecino más cercano | 10 |
| Red vial de OpenStreetMap para distancias reales | 10 |

---

## Nota sobre datos restringidos

La extracción de las fichas oficiales se hace con una petición por segundo, agente identificado y caché local. No se incluyen fuentes cuyos términos de servicio restrinjan la redistribución (TripAdvisor, Google Places API).

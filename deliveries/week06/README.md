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
5. Se implementó **TA-04**, el ordenamiento de la ruta dentro del polo, con dos baselines y evaluación sobre los 222 polos. La velocidad de traslado dejó de ser un supuesto: sale de 3 094 tramos de acceso reales de la ficha.
6. Se implementó **TA-05**, la viabilidad estacional del polo mes a mes, que es lo que hace que el mes de viaje del usuario cambie la recomendación.
7. Se unió todo en `code/consulta.py`, que resuelve una consulta de punta a punta y **verifica en cada ejecución los criterios de aceptación** de RF-01, RF-02 y RNF-01.

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
│   ├── scraper_mincetur_v3.py      extracción por firma de cabecera · la buena
│   ├── diagnostico_ficha.py        volcado de la estructura real de la ficha
│   ├── verificar_fichas.py         verificación de jerarquía y cobertura
│   ├── costo_itinerario.py         presupuesto con banda P20-P80
│   ├── ta03_score_polo.py          puntaje del polo con término de novedad
│   ├── ta04_ordenar_ruta.py        TA-04 · secuencia de paradas por día
│   ├── ta04_evaluacion.py          TA-04 · evaluación sobre los 222 polos
│   ├── ta05_estacionalidad.py      TA-05 · viabilidad del polo mes a mes
│   ├── consulta.py                 consulta de punta a punta
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
│       ├── fichas_mincetur.csv             6 129 fichas oficiales extraídas
│       ├── puntaje_polos.csv              v2 · puntaje con cobertura de jerarquía
│       ├── estacionalidad_polo_mes.csv     TA-05 · 222 polos × 12 meses
│       ├── evaluacion_ta04.csv             TA-04 · comparativa contra baseline
│       ├── ingreso_por_polo.csv            fracción de paradas pagadas por polo
│       ├── parametros_costo.csv            parámetros del modelo de costo
│       └── puntos_clima_v2.csv             88 puntos región × zona climática
└── docs/
    ├── Data_Dictionary.md             diccionario de las tres tablas
    ├── ta01_seleccion_modelo.png      figura v1
    ├── ta01_seleccion_modelo_v2.png   figura v2 · la que va en la entrega
    ├── comparativa_modelos.csv        v1 · métricas de cada modelo
    ├── barrido_k.csv                  v1 · barrido de K-Means
    ├── perfil_clusters_hdbscan.csv    v1 · perfil de los 81 polos
    ├── comparativa_polos_v2.csv       v2 · comparativa de modelos
    └── perfil_polos_v2.csv            v2 · perfil de los 222 polos
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

# TA-04 · ordenamiento y evaluación
python ta04_ordenar_ruta.py 201 6
python ta04_evaluacion.py 6

# TA-05 · estacionalidad
python ta05_estacionalidad.py

# consulta de punta a punta
python consulta.py --mes 7 --dias 6 --altitud-max 3500
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

**`clean_impute_dataset.py` sobrescribe dos columnas.** Se ejecuta después del scraper y reemplaza `TIPO_INGRESO` y `EPOCA_PROPICIA` por reglas deterministas, con lo que se pierde lo que el scraper había extraído de la ficha. El detalle está en `DataAnalysis.md` §3.1.

**`JERARQUIA_OFICIAL` del dataset maestro solo es fiable en el 59,7 %.** Coincide exactamente con la ficha oficial en los 3 660 recursos que MINCETUR jerarquiza, y asigna un número a los 2 469 que la ficha marca «No aplica» o «POR JERARQUIZAR». Para cualquier análisis nuevo, usar `FICHA_JERARQUIA_NUM` de `fichas_mincetur.csv`, que trae el dato o lo deja vacío. `code/verificar_fichas.py` reproduce la comprobación.

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

172 de los 222 polos (73 % de los recursos agrupados) no contienen ningún recurso de Lima ni de Cusco. Y con la jerarquía verificada fila a fila contra la ficha oficial: **hay 115 recursos de jerarquía 3 o 4 fuera del circuito saturado, frente a 49 dentro.**

En todo el inventario hay **172 recursos de jerarquía 3 o 4**. El patrimonio de primer nivel del país es mucho más escaso de lo que este documento afirmaba hasta ahora, y está repartido 70/30 a favor del resto del país. La cifra anterior (451 contra 203) venía del 40 % de jerarquías sin respaldo en la ficha oficial; el detalle está en `DataAnalysis.md` §3.1.

Ordenar solo por jerarquía concentra: el top 10 sale con 30 % de polos con Lima o Cusco sobre una base del 21 %. Con el término de novedad a λ = 0,3 baja a 10 % perdiendo 1,7 % de jerarquía media.

### Ordenamiento — TA-04

**El mismo viajero, los mismos seis días, 42 % más lugares.** Evaluado sobre los 222 polos:

| Método | Paradas | Kilómetros |
|---|---:|---:|
| Orden por jerarquía | 1 736 | 49 064 km |
| Vecino más cercano | 2 466 (**+42,1 %**) | 42 271 km (−13,8 %) |
| Vecino + 2-opt | 2 466 (+42,1 %) | 42 227 km (−13,9 %) |

Y un resultado negativo que también se reporta: **el 2-opt no aporta nada** — 0 paradas
extra y 0,1 % de kilómetros. Con jornadas de 8 h los tours tienen 3 a 6 paradas y el
vecino más cercano ya está cerca del óptimo.

La velocidad de traslado se calibró con 3 094 tramos de acceso de la ficha: **32,5 km/h**
sobre carretera, contra los 40 km/h que suponíamos. Cruzar un polo cuesta 23 % más tiempo
del que este documento afirmaba, y las horas de `ModelSelection.md` ya están corregidas.

### Estacionalidad — TA-05

222 polos × 12 meses desde diez años de clima. A dónde manda el producto cada mes:

```
enero      → SAN MARTÍN        abril–noviembre → PASCO
feb–marzo  → LA LIBERTAD       diciembre       → AREQUIPA
```

En temporada de lluvias recomienda la costa; en seca, sierra y selva alta. Nadie escribió
esa regla.

---

## Lo que queda pendiente

| Pendiente | Semana |
|---|---|
| Integrar `fichas_mincetur.csv` al maestro con columna `ORIGEN_JERARQUIA` | 7 |
| Alinear la numeración TA-04 y TA-05 en `week05/Requirements.md` | 7 |
| Usar el origen real del usuario en vez de `dist_origen_km = 450` | 7 |
| Perfil de intereses de verdad sobre las 63 actividades, no un filtro de texto | 10 |
| Armado de días no miope: orientación por equipos con presupuesto | 10 |
| Reemplazar el supuesto de 40 km/h por los tiempos reales de `ACCESO_MIN` | 7 |
| Llevar `TARIFA_SOLES` al modelo de costo y calibrar los seis parámetros | 7 |
| Corregir dos fallos menores del extractor: `TABLAS_RECONOCIDAS` vacía y los 31 errores guardados como `ValueError` | 7 |
| Ejecutar `fetch_climate_v2.py`: clima por `REGIÓN × ZONA_CLIMATICA`, 88 puntos en vez de 24 | 7 |
| Decidir qué se hace con el presupuesto: no hay ninguna columna monetaria en el dataset | 7 |
| Perfilamiento semántico por intereses sobre los 187 subtipos | 7 |
| Sembrar el dataset de eventos con los 749 acontecimientos reales del inventario | 7 |
| Ordenamiento de la ruta (TTDP) con baseline de vecino más cercano | 10 |
| Red vial de OpenStreetMap para distancias reales | 10 |

---

## Nota sobre datos restringidos

La extracción de las fichas oficiales se hace con una petición por segundo, agente identificado y caché local. No se incluyen fuentes cuyos términos de servicio restrinjan la redistribución (TripAdvisor, Google Places API).

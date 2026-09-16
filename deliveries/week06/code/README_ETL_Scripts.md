# Justificación de los scripts

Por qué existe cada script de esta carpeta y qué produce. Las instrucciones de ejecución están en [`../README.md`](../README.md).

---

## Datos

### `scraper_mincetur.py`
Extrae de las fichas públicas de MINCETUR la **jerarquía oficial** del recurso (1 a 4), que es la señal de importancia que el CSV de datos abiertos no publica y sin la cual el recomendador no puede ordenar: un mirador local y Machu Picchu pesarían igual. Una petición por segundo, agente identificado.

La extracción de la jerarquía funcionó y está verificada en [`../DataAnalysis.md`](../DataAnalysis.md) §3.1. Los otros dos campos que intenta leer —tipo de ingreso y época propicia— se pierden en el paso siguiente.

### `clean_impute_dataset.py`
Rellena los valores que el scraper no pudo parsear. **Tiene un efecto no deseado que hay que conocer antes de ejecutarlo:** sobrescribe `TIPO_INGRESO` y `EPOCA_PROPICIA` con reglas deterministas, borrando lo que el scraper había extraído. Hoy `TIPO_INGRESO` es una función exacta de la jerarquía y `EPOCA_PROPICIA` una función exacta de la zona climática.

Además convierte en `1` toda jerarquía no reconocida, con lo que los fallos del scraper quedan mezclados con la jerarquía 1 legítima. La corrección —columna `ORIGEN_JERARQUIA` con valores `scrapeado` / `imputado`— está prevista para la Semana 7.

### `build_master_dataset.py` — **superado, no ejecutar**
Genera jerarquía y tipo de ingreso con `random.choices()` y escribe sobre el mismo archivo que produce el scraper real. Ejecutarlo destruye la extracción. Se conserva solo como registro de un paso intermedio del desarrollo y está marcado en su encabezado.

### `fetch_climate_history.py`
Descarga de Open-Meteo Archive diez años de clima mensual (2014–2023) para la capital de cada una de las 24 regiones: 2 880 observaciones de temperatura media y precipitación total. Es lo que convierte la estacionalidad de una regla inventada en un dato medido, y lo que sostiene el cruce entre el mes de viaje y la viabilidad del destino.

### `discretize_climate.py`
Convierte precipitación y temperatura en categorías (`1_Seguro`, `2_Precaucion`, `3_Peligro` y `Frio`, `Templado`, `Calido`). Los umbrales están documentados en [`../docs/Data_Dictionary.md`](../docs/Data_Dictionary.md).

Es **climatología, no pronóstico**: describe el comportamiento medio observado en diez años. No predice un mes concreto y no modela eventos extremos — no hay ninguna fuente de huaicos ni de deslizamientos en este pipeline.

### `generate_commerce_data.py`
Genera un dataset **simulado** de 500 eventos con ventana temporal, para prototipar el lado de la oferta del producto: un municipio publica una feria con su fecha y su ubicación, y ese evento pasa a ser un nodo del itinerario mientras está vigente.

No contiene ningún comercio ni feria real. La fuente real prevista son los **749 Acontecimientos Programados** del inventario oficial, cuya fecha MINCETUR no publica y que solo conoce el municipio que los organiza.

---

## Modelo · TA-01

### `ta01_comparativa_modelos.py`
Evalúa dos baselines (partición por región y por región × categoría) contra K-Means con barrido de k de 4 a 30 y HDBSCAN con barrido de `min_cluster_size`. Métricas: silueta, Davies-Bouldin, Calinski-Harabasz y el radio medio en kilómetros del conglomerado, que es la métrica de producto.

### `ta01_modelo_final.py`
Ajusta el modelo elegido (HDBSCAN, `min_cluster_size=15`), perfila los 81 polos y calcula la cobertura de catálogo. Escribe `clusters_asignados.csv` y `perfil_clusters_hdbscan.csv`.

### `ta01_auditoria_comparacion.py`
Revisa que la comparación anterior sea justa. Existe porque la primera versión no lo era: comparaba HDBSCAN con 81 grupos evaluado sobre 3 760 recursos contra K-Means con 29 grupos evaluado sobre 4 915, dos ventajas que no dependen del algoritmo.

Comprueba si el radio medio mejora solo por tener más grupos, rehace la comparación sobre el mismo subconjunto y con el mismo número de grupos, mide la estabilidad de `min_cluster_size` y hace la ablación de las variables de TA-02. Los resultados están en [`../ModelSelection.md`](../ModelSelection.md) §5.

### `ta01_figura.py`
Genera `../docs/ta01_seleccion_modelo.png` con la comparación controlada, la curva de radio contra número de grupos y el mapa de los 81 polos.

---

## Notebooks

### `DreemGO_Advanced_EDA.ipynb`
Análisis exploratorio de las tres tablas: inventario geolocalizado por jerarquía, curvas de estacionalidad y distribución de los eventos simulados.

### `DreemGO_Predictive_Engine.ipynb`
Las dos funciones del motor. `calcular_score_viabilidad` devuelve la viabilidad climática histórica de una región en un mes. `recomendar_eventos_locales` selecciona los eventos vigentes durante el viaje y los ordena **por compatibilidad con la consulta** —afinidad de categoría, cercanía y encaje de fechas—, dejando `RELEVANCIA_PUBLICIDAD` únicamente como desempate entre eventos que ya empataron.

El municipio aporta datos; no compra posición. Un recomendador cuyo orden se puede comprar deja de servirle al viajero.

### `create_notebook.py` y `build_advanced_eda.py`
Andamiaje: generaron la primera versión de los notebooks. No forman parte del pipeline reproducible.

# Scripts de esta carpeta

Qué hace cada script, qué produce y si sigue vigente. Esta carpeta es una copia de `week06/code/` (ver [`../ERRATA.md`](../ERRATA.md)): cómo correrlos y en qué orden, en [`../../week06/README.md`](../../week06/README.md), y las secciones de `ModelSelection.md` que se citan son las de `week06/`. Aquí además está `arquitectura_dreemgo.py`, que dibuja el diagrama por capas. Los que no se ejecutan, con su porqué, están en [`legacy/`](./legacy/).

## Datos

| Script | Qué hace | Produce | Estado |
|---|---|---|---|
| `scraper_mincetur_v3.py` | Lee las 6 160 fichas oficiales de MINCETUR y reconoce cada tabla por su fila de encabezado, no por cercanía de texto | `../data/processed/fichas_mincetur.csv` | Vigente. En la semana 10 lo reemplaza un parser sobre el HTML guardado, que corrige `ACCESO_KM` y lee la descripción y la fecha de cada evento |
| `diagnostico_ficha.py` | Vuelca la estructura real de una ficha: el mapa con el que se escribió el scraper v3 | salida en consola | Herramienta |
| `verificar_fichas.py` | Compara la jerarquía del maestro con la de la ficha y mide la cobertura de cada campo | salida en consola | Vigente |
| `fetch_climate_history.py` | Descarga diez años de clima mensual (2014-2023) en la capital de cada una de las 24 regiones | `../data/processed/historial_clima_regiones.csv` | Vigente hasta que llegue el clima por polo |
| `discretize_climate.py` | Agrega los niveles de lluvia (hasta 30 mm, hasta 100 mm, más) y de temperatura | columnas nuevas en el mismo CSV | Vigente |
| `fetch_climate_v2.py` | Clima en 88 puntos región × zona climática | `../data/processed/puntos_clima_v2.csv` | Nunca se ejecutó. Lo reemplazó un punto por polo: `pipeline/adquisicion/descargar_clima_polos.py` |

## Modelo · TA-01

| Script | Qué hace | Produce | Estado |
|---|---|---|---|
| `ta01_comparativa_modelos.py` | Baselines por región y por región × categoría contra K-Means y HDBSCAN, con barridos | `../docs/comparativa_modelos.csv`, `../docs/barrido_k.csv`, `../docs/perfil_clusters.csv` | v1 |
| `ta01_modelo_final.py` | HDBSCAN con `min_cluster_size=15`: perfiles, cobertura y figura | `../data/processed/clusters_asignados.csv`, `../docs/perfil_clusters_hdbscan.csv`, `../docs/ta01_seleccion_modelo.png` | v1 |
| `ta01_auditoria_comparacion.py` | Revisa que la comparación sea justa: mismo subconjunto, mismo número de grupos, estabilidad y ablación | salida en consola | v1 |
| `ta01_figura.py` | Figura v1 con la comparación controlada | `../docs/ta01_seleccion_modelo.png` | v1 |
| `ta01_polos_acotados.py` | **Modelo elegido**: enlace completo sobre distancia de viaje, umbral de 80 km | `../data/processed/polos_asignados_v2.csv`, `../docs/perfil_polos_v2.csv`, `../docs/comparativa_polos_v2.csv` | Vigente |
| `ta01_figura_v2.py` | Figura del modelo elegido | `../docs/ta01_seleccion_modelo_v2.png` | Vigente |

Las cifras de v1 dependen de la versión de scikit-learn: las publicadas salen de la 1.8.0 (`../ModelSelection.md` §11).

## Puntaje, ruta y estacionalidad

| Script | Qué hace | Produce | Estado |
|---|---|---|---|
| `ta03_score_polo.py` | Puntaje del polo: jerarquía de la ficha más un término de novedad (`../ModelSelection.md` §6.4). El nombre es histórico: TA-03 es la extracción de fichas | `../data/processed/puntaje_polos.csv` | Vigente |
| `ta04_ordenar_ruta.py` | TA-04: secuencia de paradas por día desde el punto base, con tres métodos | salida en consola | Vigente; la versión 2 llega en la semana 10 |
| `ta04_evaluacion.py` | TA-04 evaluado sobre los 222 polos | `../data/processed/evaluacion_ta04.csv` | Vigente |
| `ta05_estacionalidad.py` | TA-05: viable, advertencia o desaconsejado por polo y mes | `../data/processed/estacionalidad_polo_mes.csv` | Vigente |

## Consulta y costo

| Script | Qué hace | Produce | Estado |
|---|---|---|---|
| `consulta.py` | Resuelve una consulta de punta a punta y verifica en cada corrida los criterios de RF-01, RF-02 y RNF-01 | salida en consola | Vigente |
| `costo_itinerario.py` | Presupuesto con banda P20-P80 por Monte Carlo sobre los parámetros sin calibrar | salida en consola | Vigente |

## Notebooks

| Notebook | Qué contiene | Estado |
|---|---|---|
| `DreemGO_Advanced_EDA.ipynb` | Análisis exploratorio del inventario, del clima y de los eventos simulados | Corre completo desde esta carpeta |
| `DreemGO_Predictive_Engine.ipynb` | Prototipo de viabilidad climática por región y de eventos con ventana temporal. El nombre del archivo es histórico: no hay ningún modelo predictivo | Corre completo; lo reemplazan TA-05 y, en la semana 10, los eventos reales (RF-03) |

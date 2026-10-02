# Erratas · Semana 6

Lo entregado el 16 de septiembre está intacto en la etiqueta [`entrega/semana-06`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-06). Después de esa fecha la carpeta siguió creciendo hasta el 20 de septiembre con TA-04, TA-05, las fichas oficiales, el modelo de costo y la consulta de punta a punta, que se presentaron en la Delivery 1. Lo que sigue son correcciones de errores, hechas el 30 de septiembre en su sitio.

## Correcciones

| Dónde | Qué decía o hacía | Qué dice o hace ahora | Por qué |
|---|---|---|---|
| `ModelSelection.md`, final | Marcadores de un merge sin resolver (`<<<<<<< HEAD`) y una segunda sección 11 | Una sola sección 11 | El merge del 20 de septiembre dejó el conflicto dentro del documento |
| `ModelSelection.md` §12 (antes, la segunda §11) | «El sistema integra dos modelos adicionales de Machine Learning»: Random Forest para riesgo climático y TF-IDF para comercio local | «Propuestas evaluadas y no adoptadas», con la razón de cada una | Ninguno se implementó. El primero solo puede reaprender la climatología de región y mes; el segundo se entrenaría sobre datos simulados y ordenaría por lo que paga cada negocio |
| `ModelSelection.md` §4, §5.9 y §6; `README.md` | Diámetro máximo de 17,1 h (v1) y 3,2 h (v2); polos «de cuatro horas» a 100 km y «de dos horas y media» a 60 km | 21,1 h y 3,9 h; casi cinco horas; unas tres horas | Salían de 40 km/h. La velocidad calibrada con 3 094 tramos de la ficha es 32,5 km/h (§8.2). §5.7 y §6.3 ya estaban corregidas; §5.9 y la tabla de §6 no, aunque §8.2 decía que sí |
| `ModelSelection.md` §6; `README.md` | Polos de v1 de más de 4 h: ~15 | 37 | Recontado sobre `clusters_asignados.csv`: 30 polos pasan de 100 km (4 h a la velocidad vieja) y 37 de 81 km (4 h a la calibrada) |
| `ModelSelection.md` §5.9 | «Subir a 100 gana 0,9 puntos de cobertura» | 1,0 punto | La misma tabla dice 77,7 % y 78,7 % |
| `ModelSelection.md` §2 | «`JERARQUIA_OFICIAL`, que sí es un dato real y verificado» | Real en la ficha; la columna del maestro coincide en el 59,7 % | `DataAnalysis.md` §3.1 lo demostró el 20 de septiembre y esta línea quedó sin actualizar |
| `ModelSelection.md` §8.3; `README.md` | «42 % más lugares» como resultado de TA-04 | Nota: la métrica cuenta paradas y no valor; en viajes de 6 días el ordenamiento omite 67 de los 157 recursos de jerarquía 3-4 de los polos | Contar paradas premia las pequeñas y cercanas. TA-04 v2 optimiza valor |
| `ModelSelection.md` §9.2 | Tabla de veredictos sin la fila de advertencia | Advertencia: 362 celdas (13,6 %) | Las tres filas suman las 2 664 celdas polo × mes |
| `ModelSelection.md` §7; `docs/Data_Dictionary.md`; `code/ta04_ordenar_ruta.py` | «TA-03» para el puntaje del polo | «Puntaje, §6.4» | TA-03 es la extracción de fichas (§1). El script `ta03_score_polo.py` conserva su nombre para no romper referencias |
| `ModelSelection.md` §11; `DataAnalysis.md` §9; `README.md` | Comandos con rutas que no existían (`python code/x.py ../data/...`), y `DataAnalysis.md` mandaba correr `build_master_dataset.py`, que genera jerarquías al azar | Comandos que se corren desde `code/`, en el orden que regenera los artefactos | Verificado el 30 de septiembre: el modelo elegido, el puntaje, TA-05 y TA-04 regeneran exactamente los CSV de `data/processed/` |
| `code/ta01_*.py` | Escribían sus salidas en la carpeta desde donde se corrían | Escriben en `data/processed/` y `docs/`, donde están los archivos entregados | Reproducir no actualizaba lo que leen los scripts siguientes |
| `ModelSelection.md` §11; `README.md` | Sin versión de scikit-learn | Las cifras de HDBSCAN (v1) se obtuvieron con scikit-learn 1.8.0 | Con 1.4 a 1.7 el mismo código da 80 polos y 315 km de diámetro máximo, no 81 y 427,9 km. El modelo elegido no cambia con la versión |
| `docs/Data_Dictionary.md` §1 | Nota de verificación: «La columna es real, extraída de la ficha oficial» | Real en el 59,7 %; para analizar, `FICHA_JERARQUIA_NUM` | Esa verificación con cuatro pruebas agregadas fue prematura (`DataAnalysis.md` §3.1) |
| `docs/Data_Dictionary.md` §4; `README.md`, pendientes | `TABLAS_RECONOCIDAS`: «columna vacía, bug conocido» | Tablas reconocidas por ficha, llena al 100 % | El error estaba en `verificar_fichas.py`, que leía la columna como número. Una ficha completa trae siete tablas; las incompletas, menos de dos en promedio, lo que confirma que el faltante es de la fuente |
| `docs/Data_Dictionary.md` §4; `DataAnalysis.md` §7 | 31 fichas que «fallaron», con el bug de guardar el texto del error | La página respondió; el parser se detuvo leyendo una distancia como «1.200.5 km» | No fueron errores de red |
| `docs/Data_Dictionary.md` §4 | Relleno de altitud y toponimia 96 %; de ingreso 74 % · 12 % | 97,8 % · 20,2 %; 74,8 % · 35,9 % · 13,0 % | Recontado sobre las 6 129 fichas leídas |
| `docs/Data_Dictionary.md`, encabezado; `README.md` | «Tres tablas» | Diez tablas | El diccionario documenta diez desde el 20 de septiembre |
| Notebooks | «Motor Predictivo», «Forecasting Espacial», «Análisis Predictivo»; rutas a `../data/` | Viabilidad climática histórica y eventos; rutas a `../data/processed/` | No hay pronóstico (`DataAnalysis.md` §5.4). Con las rutas anteriores no corrían desde `code/`; ahora corren completos |
| `code/discretize_climate.py`, `code/fetch_climate_history.py` | Ruta absoluta a la máquina de un integrante; salida en `../data/` | Rutas relativas al script, en `data/processed/` | No corrían en otra máquina, y el segundo escribía donde el primero no leía |
| `code/ta05_estacionalidad.py`, `code/consulta.py` | «TA-02» en un encabezado impreso y en la documentación | TA-05 | La renumeración del 20 de septiembre dejó dos restos |
| `code/` | `build_master_dataset.py`, `clean_impute_dataset.py`, `scraper_mincetur.py`, `generate_commerce_data.py`, `create_notebook.py` y `build_advanced_eda.py` junto al código vivo | En `code/legacy/`, con un README que explica por qué no se corren | Generan datos al azar, sobrescriben columnas, reescriben los notebooks o fueron reemplazados |

## Correcciones del 2 de octubre

| Dónde | Qué decía o hacía | Qué dice o hace ahora | Por qué |
|---|---|---|---|
| `data/processed/fichas_mincetur.csv`, columna `INGRESO_OBS` | Las observaciones de ingreso tal como las escribe cada ficha, con los teléfonos, los correos y los nombres de quienes atienden el lugar | Los mismos textos con `[contacto en la ficha oficial]` y `[encargado]` en su lugar, en 699 celdas, y en una de `HORA_VISITA`. Esas celdas quedan en una sola línea | Son datos de personas. El pipeline del producto los quita al leer la ficha ([`pipeline/README.md`](../../pipeline/README.md#datos-personales)) y esta tabla es anterior a esa regla. Ningún script lee la columna: el scraper sacó de ella `TARIFA_SOLES` al escribirla |

## Hallazgos que siguen abiertos

- **`ACCESO_KM` de `fichas_mincetur.csv` no es confiable.** El parser lee la coma como separador de miles y suma todas las filas de la tabla de accesos: 38 fichas pasan de 1 000 km y una llega a 67 406 km. La velocidad calibrada usa la mediana y resiste esos casos, pero se recalcula cuando las fichas se vuelvan a leer desde el HTML guardado (semana 10).
- **`DreemGO_week06.pdf` y `PresentationWeek06.pdf` son la misma presentación**; solo cambia el nombre del profesor en la portada. La que pide el enunciado es `PresentationWeek06.pdf`.

## Qué pasó con los pendientes del README (al 30 de septiembre)

| Pendiente | Estado |
|---|---|
| Reemplazar los 40 km/h por los tiempos de acceso de la ficha | Hecho: 32,5 km/h (`ModelSelection.md` §8.2) |
| Ordenamiento de la ruta con baseline de vecino más cercano | Hecho (`ModelSelection.md` §8) |
| Decidir qué hacer con el presupuesto | Decidido: una banda P20-P80 que ordena y advierte, no restringe |
| Llevar `TARIFA_SOLES` al modelo de costo | En parte: las entradas se calibraron con 782 tarifas reales; transporte, alojamiento y alimentación, en la semana 10 |
| Re-leer las fichas: las 31 que fallaron y `ACCESO_KM` | El HTML de las 6 160 fichas se descarga desde el 30 de septiembre; el parser nuevo, en la semana 10 |
| Clima por región × zona climática (`fetch_climate_v2.py`) | Reemplazado por un punto por polo (`pipeline/adquisicion/descargar_clima_polos.py`), en descarga |
| Integrar las fichas al maestro con el origen de cada jerarquía | Maestro v3, semana 10 |
| Usar el origen real del usuario | Motor v2, semana 10 |
| Perfil de intereses sobre las actividades de la ficha | Semana 10 |
| Armado de días no miope (orientación por equipos) | TA-04 v2, semana 10 |
| Sembrar los eventos con los 749 acontecimientos reales | RF-03, semana 10 |
| Red vial de OpenStreetMap | Extracto en descarga; tiempos por carretera en la semana 10 |
| Alinear la numeración TA-04 y TA-05 en `week05/Requirements.md` | Anotado en `week05/ERRATA.md`; requisitos finales en la Delivery 2 |
| Validación con usuarios (`ModelSelection.md` §10, «comprometida para la Delivery 1») | No se hizo. Pasa a la semana 12: prueba de usabilidad con cinco usuarios y un conjunto de consultas anotado por el equipo |

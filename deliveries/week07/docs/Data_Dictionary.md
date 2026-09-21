# DreemGO — Diccionario de Datos Extendido (Semana 7)

Este documento centraliza la metadata de todas las tablas que componen el Data Lake del proyecto DreemGO, incluyendo las salidas de los modelos predictivos y de agrupamiento (TA-01 a TA-04).

Todas las tablas utilizan delimitador punto y coma (`;`) y codificación `UTF-8-SIG` para preservar caracteres especiales del español.

---

## 1. Tablas Maestras (Fuentes de Verdad)

### 1.1 `dreemgo_master_dataset.csv`
*Dimensión central de los recursos turísticos del Perú, filtrada y enriquecida.*
- `CODIGO DEL RECURSO`: (PK) Identificador único oficial de MINCETUR.
- `NOMBRE DEL RECURSO`: Nombre oficial del destino.
- `REGIÓN` a `DISTRITO`: Jerarquía política peruana.
- `CATEGORÍA` / `SUB TIPO CATEGORÍA`: Clasificación oficial (Ej: Sitios Naturales).
- `latitud` / `longitud`: Coordenadas WGS84 corregidas. **[Nota: 1,245 registros nulos corresponden a intangibles como danzas y ferias].**
- `ALTITUD`: Elevación en m.s.n.m extraída de Open-Meteo DEM.
- `ZONA_CLIMATICA`: Piso ecológico inferido a partir de altitud y región (Chala, Yunga, Quechua, Suni, Puna, Janca, Selva).
- `DISTANCIA_CAPITAL_KM` / `INDICE_COSTO_LOGISTICO`: Variables de lejanía (Haversine) para el modelo de ruteo.
- `JERARQUIA_OFICIAL`: Nivel de importancia turística (1 a 4).

### 1.2 `fichas_mincetur.csv`
*Capa cruda extraída directamente del portal web del gobierno (Web Scraping Oficial).*
- `URL`: Enlace directo a la ficha del recurso.
- `FICHA_JERARQUIA_NUM`: Jerarquía oficial extraída del DOM de la página.
- `TARIFA_SOLES`: Precio base de entrada extraído del HTML.
- `EPOCA_PROPICIA`: Texto crudo indicando la mejor temporada (Ej: "Abril a Noviembre").
- `VISITANTES_NAC` / `VISITANTES_EXT`: Estadísticas de afluencia si están disponibles.

### 1.3 `historial_clima_regiones.csv`
*Tabla de hechos (Fact Table) climática con 10 años de historia mensual (Open-Meteo Archive).*
- `REGION`: (FK) Llave de cruce geográfico.
- `año` / `mes`: Ventana temporal (2014-2023).
- `PRECIPITACION_TOTAL_MM`: Lluvia mensual acumulada.
- `TEMPERATURA_MEDIA_C`: Promedio térmico mensual.
- `NIVEL_RIESGO_CLIMATICO`: Binning paramétrico de la lluvia (`1_Seguro`, `2_Precaucion`, `3_Peligro`).
- `SENSACION_TERMICA`: Binning de la temperatura (`Frio`, `Templado`, `Calido`).

### 1.4 `comercios_ferias_locales.csv`
*Catálogo B2B para el Motor de Recomendación (TA-03).*
- `id_comercio`: (PK) Identificador del evento o negocio.
- `CATEGORIA`: Clasificación comercial (Cultura, Gastronomía, Aventura).
- `FECHA_INICIO` / `FECHA_FIN`: Ventana de viabilidad del evento.
- `RELEVANCIA_PUBLICIDAD`: Score publicitario para priorización de anuncios en el itinerario.

---

## 2. Salidas del Modelado (Resultados de TA-01 a TA-04)

### 2.1 `polos_asignados_v2.csv` (Salida TA-01)
*Mapeo final de los recursos hacia su "Polo Turístico" urente a la optimización de clústeres espaciales (HDBSCAN/K-Means).*
- `CODIGO DEL RECURSO`: (FK) Llave de conexión con el Master Dataset.
- `POLO`: Identificador del clúster geográfico asignado. Actúa como el "Destino Macroeconómico" al que viajará el turista.

### 2.2 `puntaje_polos.csv` (Salida TA-03)
*Score comercial de cada polo para priorizar recomendaciones macro.*
- `POLO`: (PK) Identificador del clúster.
- `recursos`: Densidad (número de paradas dentro del polo).
- `jerarquia`: Promedio de importancia oficial.
- `saturacion`: Penalización por pertenecer a circuitos sobresaturados (Ej: Lima/Cusco).
- `novedad` / `puntaje`: Métrica final calculada que equilibra valor patrimonial y descentralización económica.

### 2.3 `estacionalidad_polo_mes.csv` (Salida TA-02)
*Predicción de viabilidad climática cruzada (Polo x Mes).*
- `POLO`: (FK) Identificador del clúster.
- `MES`: (FK) Mes de viaje (1 a 12).
- `precip_mm` / `temp_c`: Proyección de variables meteorológicas.
- `veredicto`: Predicción del modelo de Machine Learning (`Viable`, `Peligro`).
- `puesto_mes`: Ranking del mes para ese polo específico.

### 2.4 `ingreso_por_polo.csv` / `parametros_costo.csv`
*Derivadas de costo para el turista.*
- `frac_paradas_pagadas`: Proporción de atractivos que cobran entrada.
- `tarifa_mediana_soles`: Estimación de ticket promedio derivada de `fichas_mincetur.csv`.

### 2.5 `evaluacion_ta04.csv` (Salida TA-04)
*Resultados de la evaluación del modelo de Secuenciación y Enrutamiento de Rutas (VRP).*
- `POLO`: (FK) Clúster evaluado.
- `n`: Nodos visitados.
- `par_jer` / `par_vec` / `par_2opt`: Número de paradas optimizadas según tres estrategias distintas (Heurística Jerárquica, Vecino Cercano, y Opt-2).
- `km_jer` / `km_vec` / `km_2opt`: Distancia logística medida bajo los mismos tres algoritmos.

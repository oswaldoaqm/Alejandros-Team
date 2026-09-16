# DreemGO: Diccionario de Datos y Arquitectura
**Fase de Abstracción Finalizada - Semana 6**

## Arquitectura de Tablas (Data Lake)
Los datos han sido procesados y estructurados bajo un modelo relacional en la carpeta `/data/processed/`.

### 1. `dreemgo_master_dataset.csv` (Dimensión: Ubicaciones)
**Descripción:** Inventario geográfico y turístico oficial de MINCETUR, enriquecido con topología, feature engineering matemático y variables extraídas.
*   **ID_RECURSO** *(Primary Key)*: Identificador único del recurso turístico.
*   **NOMBRE DEL RECURSO**: Nombre oficial.
*   **REGION** *(Foreign Key)*: Región política, usada para cruzar con datos climáticos y comerciales.
*   **LATITUD / LONGITUD**: Coordenadas espaciales.
*   **ALTITUD**: Elevación en m.s.n.m (API Open-Meteo).
*   **ZONA_CLIMATICA**: Piso ecológico inferido (Discretización de la altitud).
*   **DISTANCIA_CAPITAL_KM**: Distancia Haversine al nodo logístico.
*   **INDICE_COSTO_LOGISTICO**: Nivel de costo de transporte del 1 al 3 (Discretización de la distancia).
*   **TIPO_INGRESO**: Libre o Pagado (Imputación lógica / Scraping).
*   **JERARQUIA_OFICIAL**: Importancia del destino del 1 al 4 (Web Scraping).

### 2. `historial_clima_regiones.csv` (Tabla de Hechos: Clima)
**Descripción:** Serie de tiempo histórica (2014-2023) descargada de Open-Meteo Archive para alimentar el modelo de *Forecasting* de viabilidad climática.
*   **REGION** *(Foreign Key)*: Llave de cruce con la tabla principal.
*   **AÑO**: Año del registro.
*   **MES**: Mes del registro.
*   **TEMPERATURA_MEDIA_C**: Temperatura promedio mensual (Continua).
*   **PRECIPITACION_TOTAL_MM**: Milímetros de lluvia total (Continua).
*   **NIVEL_RIESGO_CLIMATICO**: Variable predictiva (1_Seguro, 2_Precaucion, 3_Peligro). Creada mediante discretización paramétrica de las precipitaciones.
*   **SENSACION_TERMICA**: Variable categórica (Frio, Templado, Calido). Creada mediante discretización.

### 3. `comercios_ferias_locales.csv` (Tabla de Hechos: Eventos Dinámicos)
**Descripción:** Dataset comercial que representa el modelo de monetización (Two-Sided Market). Eventos y ferias locales inyectables en la ruta óptima.
*   **ID_EVENTO** *(Primary Key)*: Identificador del comercio/feria.
*   **REGION** *(Foreign Key)*: Llave de cruce.
*   **CATEGORIA**: Gastronomía, Cultura, Aventura, etc.
*   **FECHA_INICIO / FECHA_FIN**: Ventana de vigencia del evento.
*   **COSTO_PEN**: Costo estimado del evento.
*   **RELEVANCIA_PUBLICIDAD**: Score (1-5) para priorizar en el recomendador (Proxy de CTR).

## Relaciones del Modelo Predictivo
El Algoritmo de DreemGO consulta el `master_dataset` filtrando por las restricciones del usuario. Posteriormente, extrae la `REGION` resultante y consulta `historial_clima_regiones` para predecir la seguridad de la ruta, y `comercios_ferias_locales` para inyectar publicidad geolocalizada en el itinerario.

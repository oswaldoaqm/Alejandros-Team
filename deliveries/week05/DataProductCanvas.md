# Data Product Canvas: DreemGO

## 1. Problema
*   **¿Cuál es el problema?** La planificación de viajes internos en Perú exige resolver manualmente una ecuación compleja de tres variables: qué ver (intereses), dónde es geográficamente viable (altitud/clima), y cómo conectar los puntos (logística).
*   **¿Por qué es un problema?** Porque la información turística está fragmentada. El turista sufre de "parálisis por análisis" comparando múltiples pestañas sin poder optimizar su ruta.

## 2. Usuario
*   **¿Quiénes tienen este problema?** Turistas independientes (nacionales y extranjeros) que viajan por cuenta propia.
*   **¿A quiénes va a impactar?** Viajeros con restricciones de tiempo o de presupuesto que necesitan maximizar su experiencia sin gastar de más en logística ineficiente.

## 3. Data
*   **Data Interna/Externa:** Inventario Nacional de Recursos Turísticos de MINCETUR (6,160 registros). API de Open-Meteo.
*   **Data nueva creada:** Se creó el `INDICE_COSTO_LOGISTICO` (Cálculo Haversine) y la variable base `ZONA_CLIMATICA` (Macro-clima estático inferido por geografía). 
*   **Data futura (Fase 2):** Matriz de Estacionalidad (para penalizar lluvias o fenómenos por mes).

## 4. Hipótesis
*   **¿Cuáles son las posibles causas del problema?**
    1. Las plataformas actuales son buscadores aislados, no optimizadores de itinerarios.
    2. La geografía del Perú engaña al turista: subestiman los tiempos de traslado, los efectos de la altitud y las temporadas de lluvias, creando rutas imposibles de ejecutar.

## 5. Solución
*   **Solución Priorizada:** "DreemGO". Plataforma interactiva que recibe restricciones (categoría, presupuesto, mes de viaje) y asigna un "Polo Turístico Latente" optimizado.
*   **Output esperado:** Mapa interactivo con el clúster recomendado y un itinerario secuencial diario.
*   **¿Cuál es el tipo de modelo?** **Prescriptivo y Predictivo**. (Predictivo: agrupa lugares y cruza la temporada dinámica. Prescriptivo: traza la ruta más eficiente).

## 6. Actores
*   **Stakeholders:** Turistas independientes, Negocios locales (impactados indirectamente), MINCETUR.
*   **Sponsor:** Universidad de Ingeniería y Tecnología (Curso DS3022) / Prof. Germain Garcia-Zanabria.

## 7. Métricas claves
*   **Métricas de Modelo (ML):** Coeficiente de Silueta para la calidad de los polos. Similitud del Coseno > 75% entre el input y el centroide del cluster.
*   **Métricas de Negocio/Producto:** Distancia total optimizada. Latencia del sistema (< 5 segundos).

## 8. Impacto
*   **¿Cuál es el impacto?** Descentralización del turismo (recomendará corredores turísticos ocultos en lugar de enviar a todos a Cusco). Reducción del gasto logístico para el usuario.

## 9. Acciones
*   **Siguientes pasos:** 
    1. Ejecutar el EDA sobre la data enriquecida (Semana 6).
    2. Construir la Matriz de Estacionalidad para cruzar mes de viaje vs clima.
    3. Entrenar el modelo de Machine Learning (K-Means / HDBSCAN) ponderando distancias y clima.

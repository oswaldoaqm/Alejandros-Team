# Requirements & Product Design (Semana 5)

**Producto:** DreemGO — Inteligencia de rutas en Perú
**Equipo:** Alejandro, Miguel, Diego, Christopher

---

## 1. Producto y Requerimientos (2 pts)
*   **Requerimiento Funcional 1 (Motor de Clustering Dinámico):** El sistema debe procesar inputs del usuario (categoría, presupuesto, **mes de viaje**) y ejecutar un modelo de Aprendizaje No Supervisado. El modelo debe cruzar el macro-clima del destino con una "Matriz de Estacionalidad" para penalizar polos con clima adverso (ej. temporada de lluvias en la sierra) antes de retornar el resultado.
*   **Requerimiento No Funcional 1 (Integridad Analítica):** El pipeline de datos debe mantener el desacoplamiento entre las variables estáticas del inventario (Latitud, Altitud, Zona Climática Base) y las reglas dinámicas de tiempo (mes del viaje), asegurando que el dataset core no sea alterado estructuralmente por cambios estacionales.

---

## 2. Casos de Uso (3 pts)

*   **Caso de Uso 1: El Mochilero en Temporada de Lluvias**
    *   **Actor:** Turista joven, viaja en Febrero.
    *   **Flujo principal:**
        1. Selecciona *tags*: "Aventura", Presupuesto "Bajo", Viaje en "Febrero".
        2. El motor identifica polos andinos de aventura pero la Matriz de Estacionalidad los penaliza por alto riesgo de lluvias/huaicos.
        3. El sistema redirige y sugiere un clúster de aventura en la costa sur (Ica/Arequipa costa).

*   **Caso de Uso 2: Familia en Vacaciones de Invierno**
    *   **Actor:** Familia, viaja en Julio (Temporada seca andina).
    *   **Flujo principal:**
        1. Selecciona *tags*: "Cultura", Presupuesto "Medio", Viaje en "Julio".
        2. La Matriz de Estacionalidad avala la sierra sur (ausencia de lluvias, clima seguro).
        3. El sistema agrupa y sugiere el polo cultural del Cusco/Valle Sagrado y traza ruta minimizando distancias.

---

## 3. Wireframes (2 pts)
*   **Wireframe 1 (Onboarding):** Formulario con slider de presupuesto, botones de Categorías, y un selector obligatorio de **Mes de Viaje**.
*   **Wireframe 2 (Dashboard):** Pantalla dividida con el Mapa interactivo a la izquierda (Cluster ganador) y el Itinerario a la derecha con alertas climáticas dinámicas.

---

## 4. Storyboards (3 pts)
*   **Storyboard 1: La Paradoja de la Elección:** Un turista europeo confundido con mapas en su laptop -> Ingresa sus datos en DreemGO -> El modelo analiza distancias y temporada -> Recibe una ruta andina perfectamente conectada.
*   **Storyboard 2: Salvados del clima:** Un viajero limeño quiere ir a Huaraz en Febrero -> DreemGO le alerta que es temporada crítica de lluvias y le re-calcula un cluster costero alternativo -> Termina disfrutando el viaje a salvo en el sur chico.

---

## 5. User Stories - Diagramas (5 pts)

*   **US1 (Perfilamiento Espacio-Temporal):** Como turista, *quiero* ingresar mis intereses y mi mes de viaje, *para que* el sistema me asigne un polo turístico evitando zonas con clima adverso en esa temporada.
    *   *Criterio de Aceptación:* El motor de ML debe castigar el Score del cluster si la Zona Climática Base cruzada con el mes cae en la "Matriz de Lluvias/Fenómenos".
*   **US2 (Trazado de Ruta Óptima):** Como turista, *quiero* recibir un itinerario ordenado geográficamente, *para* evitar cruces redundantes y gastos logísticos extra.
    *   *Criterio de Aceptación:* Aplicación exitosa de algoritmo de grafos sobre el cluster ganador, limitando visitas diarias por distancia.

---

## 6. Tareas Analíticas (5 pts)
*   **Tarea Analítica 1 (Machine Learning Espacio-Temporal):** Aplicar K-Means/HDBSCAN sobre el dataset usando `Latitud`, `Altitud` y `Costo Logístico`. Post-procesar los clústeres cruzando la `ZONA_CLIMATICA` con una matriz estacional dinámica (mes de viaje) para ponderar qué clúster es el ganador definitivo de la recomendación.
*   **Tarea Analítica 2 (Feature Engineering Determinista):** Resolver la carencia de costos y clima en los datos abiertos gubernamentales mediante cálculo geoespacial (Fórmula de Haversine hacia capitales para el `INDICE_COSTO_LOGISTICO`) y pisos ecológicos peruanos (Altitud + Región para la `ZONA_CLIMATICA`).

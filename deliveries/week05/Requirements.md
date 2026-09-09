# Requirements & Product Design (Semana 5)

**Producto:** DreemGO — Inteligencia de rutas en Perú
**Equipo:** Alejandro, Miguel, Diego, Christopher

---

## 1. Producto y Requerimientos (2 pts)
Se han definido los requerimientos core que habilitan el motor de recomendación y ruteo de DreemGO.

*   **Requerimiento Funcional 1 (Motor de Clustering):** El sistema debe procesar un mínimo de 3 inputs del usuario (categoría preferida, presupuesto y tolerancia a la altitud) y ejecutar un algoritmo de Machine Learning No Supervisado (Ej. K-Means / HDBSCAN) para asignar al usuario a un "Polo Turístico Latente" geográficamente viable, retornando el resultado en un tiempo no mayor a 5 segundos.
*   **Requerimiento No Funcional 1 (Integridad y Enriquecimiento de Datos):** La base de datos analítica del sistema debe enriquecer el inventario oficial de MINCETUR (6,160 registros) conectándose a la API de *Open-Meteo* para resolver la ausencia de datos topológicos (Altitud). El pipeline de datos debe ser capaz de procesar lotes y asegurar que el 100% de los 4,915 registros geolocalizables tengan una variable `ALTITUD` válida antes de que el modelo pueda consumirlos.

---

## 2. Casos de Uso (3 pts)

*   **Caso de Uso 1: El Mochilero de Alta Montaña**
    *   **Actor:** Turista joven, presupuesto ajustado, alta condición física.
    *   **Precondición:** El usuario accede a la plataforma desde su móvil buscando un destino de aventura de 3 días.
    *   **Flujo principal:**
        1. El usuario selecciona los *tags*: "Aventura", "Naturaleza", Presupuesto "Bajo".
        2. El sistema detecta su tolerancia a destinos extremos e ingiere sus inputs.
        3. El algoritmo de clustering lo empareja con un clúster que agrupa recursos naturales a más de 3,000 msnm (ej. Callejón de Huaylas).
        4. El optimizador de rutas traza una secuencia de 3 días minimizando traslados geográficos.
    *   **Postcondición:** El usuario guarda el itinerario optimizado con tiempos estimados entre los nevados y lagunas.

*   **Caso de Uso 2: Vacaciones Familiares Culturales**
    *   **Actor:** Padre/Madre de familia, presupuesto medio, viajando con niños pequeños.
    *   **Precondición:** El usuario necesita evitar climas extremos y altitudes riesgosas.
    *   **Flujo principal:**
        1. El usuario selecciona *tags*: "Museos", "Folclore", Presupuesto "Medio", y Altitud "Baja/Costa".
        2. El sistema descarta inmediatamente clusters andinos o de selva profunda.
        3. El algoritmo agrupa y sugiere un polo cultural costero (ej. Ruta Moche en Lambayeque/La Libertad).
        4. El sistema prioriza distancias cortas en el ruteo diario para no fatigar a los niños.
    *   **Postcondición:** El usuario reserva los museos basados en la ruta generada y exporta el mapa familiar.

---

## 3. Wireframes (2 pts)
*(Nota para el equipo: Christopher debe diseñar esto visualmente en Figma guiándose de esta estructura).*

*   **Wireframe 1 (Onboarding / Recolección de Inputs):**
    *   **Estructura:** Pantalla limpia tipo formulario interactivo.
    *   **Componentes:** 
        *   Un *slider* para el presupuesto (Bajo, Medio, Alto).
        *   Un grupo de botones de selección múltiple (Pills) para Categorías (Naturaleza, Historia, Festividades).
        *   Un selector de fechas (Calendario) para identificar la temporada climática.
        *   Un botón principal de CTA: "Generar mi Ruta Óptima".

*   **Wireframe 2 (Dashboard de Resultados / Itinerario):**
    *   **Estructura:** Pantalla dividida (Split Screen).
    *   **Componentes (Izquierda):** Mapa interactivo del Perú centrado en el "Polo Turístico" (Cluster) ganador, mostrando la red de recursos con pines conectados por una línea de ruta.
    *   **Componentes (Derecha):** Un *Timeline* vertical con los días del viaje. Cada día muestra 2-3 tarjetas de recursos a visitar con su respectiva información extraída (nombre, categoría, altitud, clima).

---

## 4. Storyboards (3 pts)
*(Narrativa visual del viaje del usuario).*

*   **Storyboard 1: La Paradoja de la Elección**
    *   *Viñeta 1:* Un turista europeo frente a una laptop con 15 pestañas abiertas de blogs, confundido porque el Perú es demasiado grande y no sabe cómo conectar Arequipa con Cusco.
    *   *Viñeta 2:* Encuentra DreemGO. Ingresa que tiene 10 días, le gusta la arqueología y tiene presupuesto alto.
    *   *Viñeta 3:* La pantalla le muestra una animación mientras el "Modelo de Clustering" piensa.
    *   *Viñeta 4:* Aparece una ruta perfecta "Sur Andino Premium" conectando sitios arqueológicos sin rutas redundantes. El turista sonríe aliviado.

*   **Storyboard 2: El Viajero Local de Fin de Semana**
    *   *Viñeta 1:* Un limeño aburrido un viernes en la tarde, quiere salir de la ciudad pero solo tiene 2 días.
    *   *Viñeta 2:* Abre DreemGO en su celular. Selecciona "Escapada Rápida", "Comida/Folclore".
    *   *Viñeta 3:* El sistema agrupa los recursos turísticos que están a un máximo de 3 horas de su latitud/longitud actual.
    *   *Viñeta 4:* Recibe una ruta gastronómica hacia el sur chico (Azpitia/Lunahuaná) lista para arrancar en su auto.

---

## 5. User Stories - Diagramas (5 pts)

*   **User Story 1: Asignación a Polo Turístico (Clustering)**
    *   **Descripción:** Como turista sin destino fijo, *quiero* ingresar mis intereses temáticos y restricciones climáticas, *para que* el sistema me sugiera una zona del país (Cluster) altamente compatible con mi perfil.
    *   **Criterios de Aceptación:**
        *   El sistema debe requerir al menos la selección de 1 categoría y 1 restricción de presupuesto.
        *   El motor de Machine Learning debe retornar al menos un Cluster con un índice de similitud mínimo del 75%.
        *   Si no hay clusters que cumplan las restricciones exactas, el sistema debe ofrecer el cluster más cercano matemáticamente e informar la desviación.

*   **User Story 2: Trazado de Ruta Óptima (Routing)**
    *   **Descripción:** Como turista con tiempo limitado, *quiero* recibir mis recomendaciones ordenadas geográficamente como un itinerario, *para* evitar perder tiempo desplazándome de un punto a otro de manera desordenada.
    *   **Criterios de Aceptación:**
        *   La ruta generada no debe contener cruces sobre sí misma (debe ser el camino más corto o "TSP" resuelto).
        *   La ruta debe limitar la cantidad de recursos por día a un máximo de 4 para ser humanamente realizable.
        *   Se debe proveer una estimación base de la distancia total del cluster seleccionado.

---

## 6. Tareas Analíticas (5 pts)
Las tareas analíticas justifican la presencia de Inteligencia Artificial / Machine Learning y Data Engineering en el producto, superando los filtros de bases de datos tradicionales.

*   **Tarea Analítica 1 (Machine Learning - Clustering Multidimensional):**
    *   **Justificación:** El turismo no respeta fronteras políticas (distritos). Para recomendar, necesitamos descubrir "Polos Turísticos Latentes". 
    *   **Acción:** Aplicar un algoritmo de Aprendizaje No Supervisado (como *K-Means* usando distancia Gower para datos mixtos) utilizando `Latitud`, `Longitud`, `Altitud` y `Categoría` (One-Hot Encoded). Esto agrupará los 4,915 recursos geolocalizados en zonas de alta densidad afín. En base a las distancias de los centroides de cada cluster respecto al perfil vectorial del usuario, se elige el destino ideal.

*   **Tarea Analítica 2 (Data Engineering - Enriquecimiento Topográfico y Costo Logístico Geoespacial):**
    *   **Justificación:** MINCETUR carece de datos críticos de negocio para un recomendador: elevación y precios.
    *   **Acción:** Desarrollar un pipeline que extraiga las coordenadas válidas y consulte por lotes la API de *Open-Meteo* para inyectar la variable `ALTITUD` al dataset base. Simultáneamente, generar un modelo heurístico base que asigne un `INDICE_COSTO_LOGISTICO` usando cálculo de distancias Haversine respecto a las capitales regionales, cumpliendo con la exigencia de presentar "los datos en su totalidad" listos para que el modelo predictivo los consuma.

# DreemGO: revisión y punto de continuación

Fecha de revisión: 11 de noviembre de 2026.

Esta revisión se hizo sobre la copia de trabajo de la entrega del equipo. El criterio fue conservar la base que ya funciona: frontend, backend, fotografías, mapas, identidad roja y dorada y motor de itinerarios. Los cambios se concentran en explicar mejor las recomendaciones, corregir su evaluación y hacer más confiable el panel de uso. No se sustituyó el proyecto por una aplicación nueva.

## 1. Qué se revisó y qué se encontró

Se revisaron el contrato de la API, el motor de viajes, los scripts de evaluación, las decisiones técnicas del equipo, la captura de actividad y la pantalla de indicadores. La revisión distingue lo comprobado en el código de las decisiones que todavía necesitan datos de usuarios.

| Parte | Hallazgo | Qué se hizo |
|---|---|---|
| Evaluación de recomendaciones | Una opción sin calificación se convertía en cero. Esto podía perjudicar a un sistema sin que nadie hubiera juzgado esa opción. | La consulta queda pendiente si alguna de sus opciones no tiene ninguna nota. Los sistemas se comparan sobre las mismas consultas completas. |
| Archivos de evaluación | Las planillas sin notas podían detener el informe. Una fila duplicada podía sobrescribir otra. | Se admite el informe sin resultados suficientes, se rechazan duplicados y se explica una clave vacía. |
| Explicación del itinerario | El plan podía no cubrir uno de los intereses solicitados y no indicarlo expresamente. | Se añadió un aviso con el interés que no tiene paradas registradas en ese itinerario. No se cambia su puntaje ni se elimina el viaje. |
| Captura de actividad | Reenvíos de una misma acción podían producir conteos duplicados. | Cada acción puede llevar un UUID; el backend evita registrar dos veces el mismo identificador dentro de una transacción. |
| Lectura del panel | Un error de conexión podía dar una impresión incorrecta sobre la actualidad de las cifras. | El panel conserva el último dato válido, lo identifica como desactualizado y permite volver a intentar. |
| Interpretación de indicadores | Abrir un formulario sin buscar no demuestra que la persona abandonó el producto. | Se usa el nombre «Formularios sin búsqueda», que describe lo observado. Las tasas sin denominador se muestran sin datos. |

## 2. Cómo queda la web

Se conservan las imágenes, mapas y pantallas de viaje del equipo, así como sus colores. No se reemplazó su diseño ni se añadió un chatbot que simule conocer datos que el proyecto no tiene.

El panel mantiene los 22 indicadores existentes y añade cuatro resúmenes destacados, una lista de actividad reciente y dos momentos diferentes: cuándo se leyó el panel y cuándo ocurrió el último evento. Las fechas se presentan en hora de Perú.

Con la actualización activa y la pestaña visible, la pantalla consulta al servidor cada tres segundos. Se puede actualizar manualmente o pausar. Una pestaña oculta deja de consultar hasta volver a mostrarse. Es actualización periódica: el cambio aparece después de la siguiente lectura y del tiempo de respuesta del servidor; no es una transmisión instantánea por WebSocket o SSE.

Si la clave de lectura no es válida, se vuelve a pedir. Si se corta la conexión, se conservan las últimas cifras recibidas con un aviso. La pantalla de indicadores no se cuenta a sí misma como una visita al planificador.

La explicación del recomendador en la web describe lo que realmente hace: agrupar lugares, estimar tiempos, aplicar restricciones y ordenar itinerarios. El botón para ajustar preferencias permite continuar desde la consulta del viajero.

## 3. Qué cambió en el backend

- Se conserva FastAPI y el contrato de los itinerarios. El identificador de evento es una ampliación opcional de la analítica.
- SQLite mantiene los registros anteriores mediante una migración de esquema. Se añadió control de concurrencia, transacciones e índices para consultar intervalos.
- El modo WAL permite coordinar mejor lecturas y escrituras. Esto no convierte SQLite en una base distribuida.
- Las fechas del panel se agrupan y filtran con el día de Perú, UTC−05.
- Los resúmenes usan `Cache-Control: no-store` para evitar servir cifras antiguas desde una caché.
- Se limitan ráfagas a 120 eventos por minuto y sesión. Al superar el límite se responde 429 con `Retry-After: 60`.
- El resumen incluye el total de eventos, la hora de consulta y los últimos ocho eventos sin exponer identificadores de sesión.

La medición sigue siendo anónima y opcional. Un fallo al enviar estadísticas no debe impedir que el viajero reciba su itinerario.

## 4. Qué modelo hay realmente

El proyecto combina varios métodos. No corresponde presentar todo como una red neuronal ni como un modelo de clasificación.

| Componente | Método que existe en el proyecto | Qué significa |
|---|---|---|
| Agrupación de lugares | Agrupamiento de enlace completo y restricciones geográficas | Forma zonas que se pueden explorar como parte de un viaje. |
| Tiempo de traslado | Regresión calibrada con recorridos de las fichas; ajuste robusto con `scipy.optimize.least_squares` | Aprende parámetros de tiempo a partir de observaciones. Se valida separando distritos. |
| Ida en bus | Calibración con 29 rutas y evaluación dejando fuera cada corredor | Ajusta diferencias entre el recorrido en auto y en bus. Son 19 corredores en la entrega del equipo. |
| Temporada | Reglas sobre los datos climáticos históricos | Describe estacionalidad; no es un pronóstico meteorológico para un día concreto. |
| Plan diario | Optimización heurística con restricciones de tiempo y acceso | Elige las visitas y su orden dentro de la jornada disponible. |
| Orden de propuestas | Puntaje de calidad, temporada, preferencias, presupuesto y novedad | Ordena alternativas mediante reglas y pesos declarados por el equipo. |

La decisión `0004-sin-modelos-supervisados.md` incluye una actualización del 9 de noviembre que reconoce el modelo supervisado de tiempos. Lo que sigue descartado es entrenar un clasificador de clima que copie umbrales y un recomendador de preferencias sin calificaciones reales.

Esta revisión no reentrenó el modelo de tiempos ni atribuye mejoras de precisión a los cambios hechos ahora. Se corrigió cómo se evalúan las recomendaciones y cómo se explican. Los tiempos y las métricas históricas de calibración pertenecen al trabajo previo del equipo.

## 5. Qué se mantuvo

- La estructura React del frontend y FastAPI del backend.
- Las fotografías, los mapas, la identidad visual y las pantallas originales de viaje.
- El contrato de itinerarios, los identificadores de rutas, sus puntajes y el optimizador.
- La regresión de tiempos y los artefactos de datos del motor.
- La separación entre actividad registrada y simulación.
- El kit de evaluación existente, sin regenerarlo. Sirve para evaluar el ordenamiento que se mantuvo; el nuevo aviso de intereses se comprueba aparte en la web.

La comparación con el ZIP original confirmó que no se borró ninguno de sus 476 archivos ni se reemplazaron o añadieron medios visuales. `fotos.json` conserva sus 103 fotos de base y 494 lugares; siguen intactos los diez PNG de capturas y las URLs existentes del frontend. También se conservaron los 46 archivos originales de `data/` y los siete de `dreemgo/datos/`. No se añadió otra tecnología al `package.json`; el archivo de bloqueo sí actualizó parches de Vite y dependencias transitivas. Esta comprobación distingue conservar los recursos del equipo de conservar cada línea del código: los cambios funcionales descritos arriba sí modifican los archivos correspondientes.

## 6. Qué se comprobó

Estas son pruebas efectivamente ejecutadas durante la revisión. No equivalen a una validación con viajeros reales ni a una certificación de producción.

| Área | Verificación | Resultado |
|---|---|---|
| Evaluación y avisos del motor | `python -m pytest tests/evaluacion tests/motor/test_intereses_sin_cubrir.py tests/motor/test_aviso_de_presupuesto.py` | 89 pruebas aprobadas. |
| Estilo de los cambios del motor | Ruff sobre `evaluacion/informe.py`, `dreemgo/motor/viaje.py` y sus dos archivos de pruebas | Sin errores. |
| Backend y analítica | `python -m pytest tests/test_analitica.py tests/test_simulacion_actividad.py tests/test_api.py -q` | 44 pruebas aprobadas. |
| Frontend | Suite de Vitest | 274 pruebas aprobadas en 30 archivos. |
| Revisión de frontend | `npm run revisar` | Biome sobre 124 archivos y dos proyectos TypeScript: aprobado. |
| Compilación web | Compilación de producción | Aprobada. |
| Suite Python completa | `python -m pytest -o addopts= -q` | 1016 pruebas aprobadas en 143,19 segundos. |
| Estilo Python completo | `ruff check .` | Sin errores. |
| Recorrido en navegador | Entrada consentida, búsqueda, apertura de Arequipa y guardado | El panel pasó de cero a dos sesiones, dos búsquedas completadas, un itinerario abierto y un guardado sin pulsar Actualizar. Fueron acciones de prueba local. |

Las pruebas cubren, entre otros casos, notas ausentes y duplicadas, el aviso de playa no cubierta en Huaraz, el presupuesto, la actualización periódica del panel, la recuperación después de errores, la clave incorrecta, la pausa en pestañas ocultas y la prevención de búsquedas duplicadas en React StrictMode.

## 7. Límites que conviene explicar al presentar

1. **Las 300 sesiones de ejemplo son simuladas.** Enseñan cómo se ven las gráficas; no son 300 personas reales ni una prueba de 300 usuarios simultáneos.
2. **Una sesión no equivale a una persona.** La recepción pública y anónima de eventos tampoco garantiza datos de negocio auditados. El límite por sesión reduce ráfagas, pero no es un sistema completo contra bots.
3. **No hay ventas ni reservas en este alcance.** El precio del viaje es un estimado para el viajero, no el ingreso de DreemGO. No se calculan ganancias, pérdidas ni inasistencias sin una operación y registros que las respalden.
4. **La actualización depende de la conexión.** El panel consulta cada tres segundos mientras está visible y activo. Un corte de red retrasa los cambios.
5. **SQLite requiere almacenamiento persistente.** Esta implementación está orientada a una instancia con disco durable. Compartir cifras entre varias instancias requiere una decisión de despliegue adicional.
6. **La calidad de la recomendación todavía debe juzgarse.** Los clics y los guardados describen uso; no demuestran por sí solos que el itinerario sea bueno. Tampoco se deben convertir automáticamente en etiquetas para reentrenar.
7. **El presupuesto es una preferencia con avisos.** El motor puede mostrar una alternativa que lo supera y debe explicar el exceso. Se mantuvo esta decisión del equipo.

## 8. Lo que les toca completar: un ejercicio pequeño

No necesitan rehacer el proyecto ni entrenar otro modelo para esta entrega. El cierre propuesto es comprobar tres consultas con dos integrantes y mostrar un recorrido real por la interfaz.

### A. Preparar la evaluación

Desde la carpeta que contiene `pyproject.toml`, se necesita Python 3.11 o posterior. El informe usa NumPy y Pydantic, que instala el proyecto, y SciPy para comparar sistemas. Instalar solo la API no añade SciPy.

Si ya existe el entorno `.venv` del proyecto, usar:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[api]" "scipy>=1.13"
```

Si se prepara un entorno por primera vez:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[api]" "scipy>=1.13"
```

Para ejecutar solamente el informe, basta instalar el proyecto con `-e .` y `"scipy>=1.13"`; FastAPI no necesita estar encendido. El informe no requiere Jupyter, pandas, scikit-learn, una clave de IA ni volver a descargar las fuentes.

También deben conservarse `evaluacion/consultas.csv`, `data/evaluacion/clave.csv` y los seis artefactos del motor en `dreemgo/datos/`: `manifiesto.json`, `recursos.json.gz`, `polos.json.gz`, `origenes.json.gz`, `eventos.json.gz` y `costos.json`.

### B. Calificar tres consultas

1. Dos integrantes abren `data/evaluacion/cuadernillo.html` en sus propios navegadores. Acuerdan evaluar las consultas 1, 2 y 3.
2. Cada integrante califica **todas las opciones** de esas tres consultas por separado: 2 si lo recomendaría tal cual, 1 si tiene reparos y 0 si no encaja. No deben acordar las notas ni mirar `clave.csv` antes.
3. Las otras consultas se dejan sin nota. **No borren sus filas.** El archivo debe conservar todas las opciones del kit, aunque solo tres consultas estén calificadas.
4. Cada integrante descarga su CSV. Guardan ambos archivos en `data/evaluacion/calificaciones/`, con nombres diferentes, por ejemplo `AB.csv` y `CD.csv`. Solo debe haber una planilla por persona y ambas deben pertenecer al mismo kit.
5. Desde la raíz del proyecto ejecutan:

```powershell
.\.venv\Scripts\python.exe -m evaluacion.informe
```

El resultado se guarda en `data/evaluacion/resultados/`: `notas.csv`, `metricas.csv` y `resumen.json`. Deben revisar que aparezcan tres consultas evaluadas y las demás pendientes. Una nota vacía no cuenta como cero. Si una opción no tiene ninguna nota, su consulta completa queda pendiente para que ambos sistemas se comparen en igualdad de condiciones.

El código acepta una consulta cuando cada opción tiene al menos una nota; en este ejercicio se pide que ambas personas completen las tres para poder revisar también sus desacuerdos. Tres consultas son una comprobación inicial: no permiten afirmar que un sistema sea mejor para todos los viajeros. El informe no calcula una prueba de Wilcoxon si no tiene al menos seis diferencias no nulas.

### C. Mostrar el producto funcionando

1. En la web, solicitar Lima → Huaraz, agosto, tres días, con naturaleza y playa. Revisar el aviso que explica que el plan no incluye playa; después quitar playa y comparar.
2. En otra pestaña, abrir el panel. Activar las estadísticas anónimas en la pestaña del viajero, hacer una búsqueda y abrir un itinerario. Usar «Actividad registrada» en el panel con la clave configurada por el equipo.
3. Comprobar que las acciones aparecen después de la siguiente actualización. Distinguirlas del ejemplo de 300 sesiones.
4. Entregar una captura del itinerario, otra del panel y un párrafo: qué entendieron, qué desacuerdo apareció al calificar y qué ajuste pequeño proponen.

## 9. Fuentes que orientan la revisión

Estas fuentes respaldan criterios de diseño y evaluación. No prueban que DreemGO haya obtenido una precisión determinada.

- **Vansteenwegen y colaboradores, City Trip Planner (2011).** Describe planificación turística a partir de preferencias y restricciones mediante optimización. Es coherente con conservar el enfoque del equipo. [Artículo original](https://www.sciencedirect.com/science/article/abs/pii/S0957417410013230), DOI: 10.1016/j.eswa.2010.11.085.
- **Shani y Gunawardana, Evaluating Recommender Systems.** Distingue evaluación fuera de línea, estudios con usuarios y evaluación en uso. Orienta la separación entre el cuadernillo de calidad y el panel de actividad. [Publicación de Microsoft Research](https://www.microsoft.com/en-us/research/publication/evaluating-recommender-systems/).
- **Joachims, Swaminathan y Schnabel, Unbiased Learning-to-Rank with Biased Feedback.** Explica por qué los clics están condicionados por cómo se presentan los resultados y no son etiquetas limpias de relevancia. [Trabajo original](https://arxiv.org/abs/1608.04468).
- **SQLite, Write-Ahead Logging.** Referencia oficial para el modo WAL y sus condiciones de operación. [Documentación](https://www.sqlite.org/wal.html).
- **React, useEffect.** Referencia para sincronización con servicios externos y limpieza de efectos. [Documentación](https://react.dev/reference/react/useEffect).
- **MDN, Page Visibility API.** Referencia para suspender trabajo de una pestaña oculta. [Documentación](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).

La política de dejar pendientes las consultas incompletas es una corrección conservadora de esta revisión. No se atribuye a un artículo una regla exacta que el artículo no prescribe.

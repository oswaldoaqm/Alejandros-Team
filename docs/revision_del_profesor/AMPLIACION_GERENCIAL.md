# DreemGO y el dashboard para gerencia

Revisión del 11 de noviembre de 2026.

Equipo, esta copia amplía el panel de DreemGO para que puedan explicar el uso de la plataforma con indicadores y gráficos desde el primer inicio. La demostración trae **200 usuarios ficticios, una sesión por usuario, 932 acciones y 28 días completos**, del 14 de octubre al 10 de noviembre de 2026, en hora de Perú. Es un ejercicio reproducible para aprender a leer los datos; no representa 200 personas que hayan probado el producto ni una prueba de 200 conexiones simultáneas.

La página y el recomendador del equipo siguen siendo la base del proyecto. La ampliación se hizo en otra copia, conservando la entrega anterior. La [auditoría previa](AUDITORIA_Y_CAMBIOS.md) queda disponible como historial; este documento describe lo añadido después de esa revisión.

## Qué se añadió

- Una simulación inicial de 200 usuarios, con archivos separados de eventos y usuarios ficticios. Los destinos y perfiles de viaje proceden del kit existente del equipo; los comportamientos y tiempos son supuestos del ejercicio.
- Cuatro vistas en el dashboard integrado: **Resumen ejecutivo, Comportamiento, Estadística y Proyección**. Los 22 indicadores anteriores siguen disponibles, con su fórmula y la actividad reciente.
- Gráficos de barras y líneas combinadas, distribución circular de sesiones, embudo, Pareto, mapa de calor, histograma, matriz de correlación, dispersión y proyección de sesiones.
- Un diagrama de causa y efecto que organiza **hipótesis para investigar**, junto con una comprobación sencilla para cada una. No afirma haber identificado causas.
- Descarga de los indicadores en CSV para revisar los valores fuera de la pantalla.
- Un archivo independiente, `app/public/tablero-gerencial.html`, con una instantánea de los agregados de la simulación. Puede abrirse sin instalar el servidor para explorar ese ejemplo. Su lectura de actividad real requiere servirlo por HTTP, conectar la API y usar la clave del equipo.
- En ese archivo independiente hay un escenario financiero ilustrativo con supuestos editables. Se calcula aparte de la actividad registrada y no convierte guardados o búsquedas en ventas verificadas.

## Qué se corrigió o aclaró

Los nuevos gráficos utilizan denominadores explícitos. Una sesión puede generar varias acciones; por eso 932 eventos no se presentan como 932 usuarios. La distribución circular asigna cada sesión una sola vez a su etapa más avanzada observada, dando prioridad a guardar. El embudo es más estricto: exige observar las etapas en orden dentro del periodo seleccionado.

La serie diaria incluye ceros en los huecos entre la primera y la última fecha observadas. Esto permite leer un eje temporal continuo. Un cero significa que no llegaron eventos ese día; por sí solo no demuestra que el servicio estuviera disponible ni que nadie lo usara sin compartir estadísticas.

Los cálculos estadísticos mantienen los datos ausentes como ausentes. No muestran una correlación con menos de cinco pares completos ni cuando una variable es constante. La desviación estándar no se calcula con una sola respuesta. Si faltan días para proyectar, el panel explica qué información falta en lugar de presentar una cifra sin base.

El contrato de la API y los tipos de la interfaz se actualizaron para incluir `analisis`. El esquema OpenAPI conserva las siete rutas y describe 57 modelos. La ampliación no modifica el contrato de los itinerarios ni sus recomendaciones.

## Qué se mantuvo

- La estructura React del frontend y FastAPI del backend.
- Las imágenes, los catálogos turísticos, las pantallas de planificación, los mapas y la identidad visual del equipo.
- El agrupamiento geográfico, la regresión de tiempos y el optimizador de itinerarios. Esta ampliación no reentrena el recomendador ni atribuye una mejora de precisión a los gráficos.
- La medición opcional y anónima, el acceso protegido al resumen real y la separación entre simulación y actividad registrada.
- Las correcciones de la auditoría anterior, como la prevención de duplicados y la evaluación que deja pendientes las calificaciones vacías.
- Los archivos históricos de 300 sesiones. El dashboard nuevo utiliza los de 200; no suma ambos ejemplos.

## Cómo interpretar cada vista

| Vista o gráfico | Qué calcula | Qué decisión permite preparar |
|---|---|---|
| Combinado por día | Sesiones y búsquedas registradas en la misma escala temporal | Identificar días con mayor uso y revisar cambios en el recorrido |
| Distribución circular | Grupos exclusivos según la etapa más avanzada de cada sesión | Entender hasta dónde llegaron las sesiones sin contarlas dos veces |
| Embudo | Sesiones que completan las etapas en orden, como proporción del total de sesiones del periodo | Revisar la continuidad desde el formulario hasta guardar |
| Pareto | Frecuencia de estados entre las sesiones sin guardado, ordenada de mayor a menor, y porcentaje acumulado | Priorizar un grupo para investigar; no descubrir una causa automáticamente |
| Mapa de calor | Número de acciones por día de la semana y hora de Perú | Comparar horarios y preparar una observación del uso |
| Histograma | Distribución de la duración de las respuestas completadas | Ver dispersión, concentración y respuestas lentas |
| Correlación | Coeficiente de Pearson por pares completos de variables de sesión | Formular preguntas sobre asociaciones, sin atribuir causalidad |
| Dispersión | Días y presupuesto de la última consulta de cada sesión, cuando ambos existen | Ver cómo se distribuyen las preferencias enviadas |
| Proyección | Comparación de dos métodos sencillos para estimar las siguientes siete jornadas | Practicar evaluación temporal y explicar los límites de una predicción |
| Causa y efecto | Preguntas sobre interacción, respuestas, conexión y tiempos | Diseñar comprobaciones con personas y registros concretos |

El Pareto utiliza como base las sesiones **sin guardado**. No debe interpretarse su porcentaje como porcentaje de todos los usuarios. El diagrama tampoco presupone que se cumpla una regla 80/20: la concentración depende de los datos seleccionados.

## Las cifras del ejemplo inicial

Antes de aplicar filtros, deben aparecer estas cantidades:

| Medida | Valor simulado |
|---|---:|
| Usuarios ficticios y sesiones | 200 |
| Acciones totales | 932 |
| Formularios abiertos | 190 |
| Búsquedas iniciadas | 160 |
| Respuestas completadas | 154 |
| Respuestas con viajes | 143 |
| Respuestas sin viajes | 11 |
| Itinerarios abiertos | 115 |
| Viajes guardados | 60 |
| Viajes compartidos | 30 |
| Aperturas de impresión | 17 |
| Errores de consulta | 6 |

Las 143 respuestas con viajes y las 11 sin viajes ya están incluidas en las 154 respuestas completadas. No deben sumarse otra vez al total de eventos.

La distribución exclusiva es: 60 sesiones con guardado, 55 que abrieron una ruta sin guardar, 28 que recibieron viajes sin abrirlos, 11 sin viajes, 6 con error, 30 con formulario sin búsqueda y 10 con solo una visita. Estas cantidades sí suman 200. El Pareto excluye las 60 con guardado y trabaja con una base de 140 sesiones.

La mediana de la latencia simulada es 730 ms y el percentil 95 es aproximadamente 3513,8 ms. Son tiempos generados para la demostración, no una medición de rendimiento del servidor. Los detalles de las probabilidades y de los archivos están en [SIMULACION_200.md](SIMULACION_200.md).

## Las fórmulas estadísticas

La latencia se calcula sobre eventos `busqueda_resultado` que incluyen `duracion_ms`. Media, mediana, mínimo, máximo, percentiles 25, 75 y 95 describen esas respuestas completadas. Los percentiles usan interpolación lineal entre valores ordenados. La desviación es **muestral**, con denominador `n − 1`, y requiere al menos dos observaciones. El histograma utiliza seis intervalos de igual amplitud cuando hay variación; el último incluye el máximo. Si todos los tiempos son iguales, se muestra una sola barra.

La correlación se calcula por sesión, con estas variables:

- Días y presupuesto de la consulta más reciente enviada en el periodo.
- Mediana de la latencia de sus respuestas completadas.
- Cantidad de acciones de abrir, guardar, compartir o imprimir viajes.

Cada par utiliza solo las sesiones que tienen ambos valores y muestra su propio `n`. El coeficiente es la suma de los productos de las desviaciones respecto de las medias, dividida entre la raíz del producto de las sumas de cuadrados. Se muestra sin datos cuando hay menos de cinco pares o una variable no varía. El umbral es una regla prudente de presentación, no una garantía de significación estadística. No se calculan pruebas de causalidad ni se afirma que una asociación sea significativa por su color o magnitud.

## Cómo se calcula la proyección

Se requieren al menos 21 días completos del periodo seleccionado. En actividad real se excluye el día actual, porque todavía está en curso. La simulación inicial aporta 28 días completos.

1. Se separan los últimos siete días para evaluar; esos valores no participan en el ajuste inicial.
2. Con los días anteriores se ajustan dos candidatos: el promedio de los últimos siete días disponibles y una tendencia lineal por mínimos cuadrados.
3. Cada candidato estima la semana reservada. Se calcula su **error absoluto medio**, en sesiones por día.
4. Se elige el menor error; en un empate queda el promedio, que es el método más sencillo.
5. El método elegido se reajusta usando toda la historia disponible y genera siete valores futuros. Los valores negativos de una tendencia se limitan a cero.

Con la semilla 42 del ejemplo inicial, el promedio obtiene un error de 1,39 sesiones por día y la tendencia lineal, 1,44. Se selecciona el promedio y se proyectan aproximadamente 7,43 sesiones por día para el 11 al 17 de noviembre de 2026. Las fracciones son valores esperados del método, no personas fraccionadas ni registros que se incorporen a la base.

Esta comparación utiliza **una partición temporal**, no validación cruzada. La semana reservada sirve para elegir el método, por lo que sería necesario otro periodo posterior para evaluar de forma independiente la opción ya elegida. No se presenta un intervalo de confianza. Al partir de datos simulados, ni el error ni la proyección demuestran capacidad predictiva sobre viajeros reales.

## Actividad real y ejemplo inicial

El dashboard integrado inicia en Simulación para que tengan datos visibles al presentar. La simulación se lee de un JSON separado y nunca se inserta en SQLite. Volver al modo real no debe arrastrar los 200 usuarios ficticios.

La página envía acciones únicamente después de que el visitante acepta compartir estadísticas. La API las conserva en SQLite; el panel consulta los agregados cada tres segundos mientras está visible y la lectura está activa. Se puede pausar y reanudar. Es actualización periódica y depende de la conexión, no una promesa de respuesta instantánea.

El resumen real exige la clave del equipo. Abrir el panel no genera una visita al planificador. Una sesión anónima puede corresponder a una pestaña o recorrido y no equivale necesariamente a una persona única. La medición tampoco incluye a quienes no aceptan compartir estadísticas.

El archivo independiente conserva una instantánea para demostración sin conexión. No recalcula el historial por sí solo si se edita un CSV. Después de regenerar el ejemplo con `python -m evaluacion.simular_actividad`, ejecuten `python -m evaluacion.exportar_tablero` para actualizar su bloque de datos. Para actividad real, sí necesita la API; abrirlo con `file://` mantiene disponible únicamente el ejemplo incluido.

## Escenario económico y límites comerciales

DreemGO todavía no confirma compras ni reservas. El presupuesto que el viajero escribe y el costo estimado del itinerario no son ingresos de la plataforma. Por eso la analítica de eventos no informa ganancias, pérdidas ni ausencias comprobadas.

El archivo independiente permite ensayar otro cálculo: sesiones por conversión comercial supuesta da operaciones esperadas; operaciones por ingreso unitario da ingresos ilustrativos; los costos incluyen el componente variable y los supuestos fijos y de publicidad. El resultado es la diferencia entre ingresos y costos. Cambiar esos campos modifica el escenario, no los eventos, el recomendador ni las cifras comerciales observadas. Para usarlo ante gerencia, presenten los supuestos junto con el resultado y mantengan la palabra **escenario**.

## Dónde continuar en el código

| Archivo | Responsabilidad |
|---|---|
| `app/src/vistas/Indicadores.tsx` | Fuente, fechas, lectura automática, indicadores y exportación CSV |
| `app/src/vistas/AnalisisGerencial.tsx` | Gráficos, tablas de valores, vistas gerenciales e hipótesis |
| `app/src/estilos/indicadores.css` | Presentación del panel sobre la identidad visual existente |
| `dreemgo/analitica.py` | Recepción, almacenamiento y resumen de las acciones |
| `dreemgo/analitica_gerencial.py` | Distribuciones, embudo, Pareto, estadísticas y proyección |
| `evaluacion/simular_actividad.py` | Ejemplo reproducible de los 200 usuarios ficticios |
| `evaluacion/exportar_tablero.py` | Actualización de los agregados del HTML independiente |
| `app/public/tablero-gerencial.html` | Demostración independiente y conexión opcional con la API |
| `data/simulacion/actividad_200.csv` | Una fila por evento simulado |
| `data/simulacion/usuarios_200.csv` | Una fila por usuario ficticio |
| `docs/openapi.json` | Contrato actualizado de las respuestas de la API |

Las instrucciones de instalación y ejecución están en `00_COMIENZA_AQUI.txt` y en las guías Word de esta entrega. No hace falta añadir otro framework ni entrenar un modelo diferente para demostrar la ampliación.

## Qué se comprobó

| Comprobación | Resultado |
|---|---|
| Suite Python completa tras integrar la analítica y la simulación | **1045 pruebas aprobadas** en 145,19 segundos |
| Comprobación posterior del exportador del HTML independiente | **3 casos adicionales aprobados**, ejecutados por separado |
| Suite completa de la interfaz React | **282 pruebas aprobadas** en 31 archivos |
| Revisión de la interfaz | Biome sobre 126 archivos y comprobación de los dos proyectos TypeScript aprobados |
| Compilación de producción | Aprobada |
| Estilo Python de la copia | Ruff aprobado |

Los tres casos del exportador se añadieron después de aquella ejecución completa. Por eso se registran aparte y no se afirma que se haya ejecutado una única suite completa de 1048 pruebas. Tras pequeños ajustes de presentación de la interfaz se repitieron las 13 pruebas focales correspondientes, la revisión y la compilación.

Las pruebas estadísticas comprueban, entre otros casos, que los grupos no cuenten una sesión dos veces, que el Pareto termine en 100 %, que el embudo exija orden, que los días y horas correspondan a Perú, que se conserven los valores ausentes y que la semana de validación no se use para ajustar los candidatos. Estas comprobaciones verifican el código; no sustituyen una evaluación con usuarios reales.

## Qué les toca completar

La continuidad puede resolverse con tres ejercicios pequeños sobre esta misma copia:

1. Abran el ejemplo de 200 y comprueben una cifra contra su CSV. Expliquen el numerador y el denominador de un porcentaje.
2. Elijan un gráfico, describan lo que observan y propongan una comprobación. En Pareto y correlación, eviten atribuir un motivo que los datos no midieron.
3. Prueben la web con estadísticas activadas y observen una búsqueda y un guardado en Actividad registrada. Entreguen una captura antes y otra después, indicando que esa prueba está separada de la simulación.

Pueden añadir un cambio pequeño de texto que ayude a entender un gráfico. La evaluación completa del recomendador, una medición con viajeros reales y el despliegue con almacenamiento persistente siguen como pasos posteriores. SQLite requiere conservar el archivo en disco; un despliegue con varias instancias necesita una base compartida. Ninguna de estas tareas exige rehacer ahora la página del equipo.

## Referencias para interpretar el análisis

- [Forecasting Principles and Practice — evaluación de pronósticos](https://otexts.com/fpp3/toolbox.html#evaluating-point-forecast-accuracy): separación temporal y evaluación fuera de los datos usados para ajustar.
- [NIST — Scatter Plot](https://www.itl.nist.gov/div898/handbook/eda/section3/eda33q.htm): relaciones entre variables y límite de la interpretación causal.
- [ASQ — Pareto Chart](https://asq.org/quality-resources/pareto): orden por frecuencia y lectura del porcentaje acumulado.

Estas referencias orientan la interpretación. La elección de umbrales y del ejercicio de simulación está documentada como decisión de esta copia, no como un resultado demostrado por esos textos.

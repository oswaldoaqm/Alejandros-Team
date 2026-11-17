# Cómo practicar con los 200 usuarios de ejemplo

La nueva vista de gerencia empieza con **200 usuarios ficticios, una sesión por usuario y 932 acciones**. El ejemplo cubre 28 días completos, del 14 de octubre al 10 de noviembre de 2026, en hora de Perú. Se preparó para probar indicadores y gráficos desde el primer inicio, aunque todavía no haya visitantes reales.

Estos registros son una simulación reproducible. No son personas que probaron la aplicación, no son una prueba de carga y no permiten afirmar resultados comerciales. La actividad real conserva su base separada.

## De dónde sale cada parte

Los perfiles de viaje se toman de las 40 consultas del equipo en `evaluacion/consultas.csv`. Los identificadores de los destinos abiertos se toman de las tres propuestas guardadas por consulta en `data/evaluacion/clave.csv`, el ranking del kit al momento de crear esta simulación. La regla de intereses de la copia actual cambia tres de esos órdenes: el archivo simulado se conserva como escenario histórico, no como reproducción exacta del ranking vigente. No se añadieron destinos ficticios ni se cambiaron los artefactos turísticos.

Lo inventado para este ejercicio es el comportamiento: cuándo entra cada usuario, si abre el formulario, si busca, si aparece un error y si abre o guarda un viaje. La duración de las respuestas también es simulada. Una respuesta con cero viajes representa un escenario de prueba; no significa que el motor haya fallado al resolver esa consulta. El generador no ejecuta 200 consultas de rendimiento contra el servidor.

Cada usuario recibe un identificador como `U0001` y un UUID de sesión. Son etiquetas ficticias, no identificadores de alumnos ni de visitantes. No se generan nombres, correos, teléfonos, compras, pagos o reservas.

## Archivos que pueden abrir

| Archivo | Qué contiene | Para qué usarlo |
|---|---|---|
| `data/simulacion/actividad_200.json` | Metadatos, eventos y una ficha agregada por usuario ficticio | Revisar el ejemplo completo y sus supuestos |
| `data/simulacion/actividad_200.csv` | Una fila por acción, 932 filas | Construir tablas dinámicas, gráficas y conteos |
| `data/simulacion/usuarios_200.csv` | Una fila por usuario ficticio, 200 filas | Comparar grupos sin contar varias veces a la misma sesión |
| `dreemgo/datos/actividad_200_simulacion.json` | Copia idéntica del JSON | Alimentar el modo Simulación de la API |
| `evaluacion/simular_actividad.py` | Generador con semilla y probabilidades explícitas | Repetir el ejercicio sin editar datos a mano |

Los CSV usan punto y coma como separador y UTF-8 con marca BOM. Pueden abrirlos en Excel o importarlos en un notebook. Una celda vacía significa que no hay un valor, no que ese valor sea cero.

Los archivos anteriores `actividad_300.json`, `actividad_300.csv` y `actividad_300_simulacion.json` se conservaron como referencia. El panel nuevo usa el ejemplo de 200; no suma ambos conjuntos.

## Cómo se construye el ejemplo

La semilla es 42. Hay al menos una sesión en cada día del periodo; el resto se distribuye al azar, sin imponer crecimiento para favorecer una predicción. Las horas van de 08:00 a 22:59, con mayor peso al mediodía y al anochecer. Las acciones de una sesión avanzan entre 4 y 37 segundos y conservan el orden del recorrido.

Las probabilidades siguientes son decisiones del ejercicio, **no tasas medidas en DreemGO**. Se aplican solo cuando se llegó al paso indicado; la proporción que resulta de una muestra de 200 puede ser diferente.

| Decisión de la simulación | Probabilidad supuesta |
|---|---:|
| Abrir el formulario después de entrar | 92 % |
| Buscar después de abrir el formulario | 86 % |
| Error después de iniciar una búsqueda | 6 % |
| Cero viajes en una respuesta sin error | 8 % |
| Abrir un itinerario después de recibir viajes | 79 % |
| Guardar después de abrir un itinerario | 42 % |
| Compartir después de abrir un itinerario | 24 % |
| Imprimir después de abrir un itinerario | 11 % |

La latencia de una respuesta usa una distribución lognormal con parámetros `mu=6.5` y `sigma=0.55`, expresada en milisegundos. Un 8 % de las respuestas añade entre 1.800 y 4.500 ms; el resultado se limita a 100–10.000 ms. Esto produce dispersión y algunos casos lentos para practicar con histogramas, mediana y percentiles. No es una medición del rendimiento de la aplicación.

## Qué cifras deberían aparecer al comenzar

| Acción | Cantidad |
|---|---:|
| Sesiones iniciadas | 200 |
| Formularios abiertos | 190 |
| Búsquedas iniciadas | 160 |
| Respuestas completadas | 154 |
| Respuestas con viajes | 143 |
| Respuestas sin viajes | 11 |
| Errores de consulta | 6 |
| Itinerarios abiertos | 115 |
| Viajes guardados | 60 |
| Viajes compartidos | 30 |
| Aperturas de impresión | 17 |

Las acciones suman 932 si se cuenta cada respuesta una sola vez. Las filas «con viajes» y «sin viajes» desglosan las 154 respuestas completadas. Un mismo usuario puede buscar, abrir, guardar y compartir; por eso no se deben sumar acciones para calcular usuarios.

En `usuarios_200.csv`, la etapa final forma grupos exclusivos: 10 solo visitaron, 30 abrieron el formulario sin buscar, 6 tuvieron un error, 11 recibieron cero viajes, 28 recibieron viajes sin abrirlos, 55 abrieron un itinerario sin guardarlo y 60 guardaron. Esas siete cantidades sí suman 200. Compartir e imprimir quedan en columnas independientes. La última acción cronológica puede ser compartir o imprimir, aunque la etapa principal ya sea guardado.

## Regenerar exactamente los archivos

Desde la raíz del proyecto y con el entorno Python preparado:

```powershell
.\.venv\Scripts\python.exe -m evaluacion.simular_actividad
```

El comando equivalente con parámetros explícitos es:

```powershell
.\.venv\Scripts\python.exe -m evaluacion.simular_actividad --sesiones 200 --semilla 42 --fecha-base 2026-11-10 --dias-historia 28
```

Esto actualiza el ejemplo de 200, su CSV de eventos, su CSV de usuarios y la copia que lee la API. No escribe en SQLite ni en los archivos históricos de 300. Reinicien la API si la instalación conserva una copia del ejemplo en memoria.

Para comprobar el generador, después de instalar las dependencias de desarrollo:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests/test_simulacion_actividad.py -q
```

## Diccionario de los eventos

| Campo | Significado |
|---|---|
| `sesion` | UUID ficticio que agrupa las acciones del mismo usuario de ejemplo |
| `tipo` | Entrada, formulario, búsqueda, respuesta, apertura, guardado, compartido, impresión o error |
| `instante` | Fecha y hora ISO 8601 con desfase `-05:00` de Perú |
| `origen` | Identificador de origen de una consulta del kit |
| `polo` | Identificador de un destino propuesto en el kit, cuando se usa un itinerario |
| `intereses` | Intereses de la consulta, separados por `|` en el CSV |
| `dias` | Duración solicitada del viaje |
| `mes` | Mes solicitado para el viaje; no es el mes en que se usó la aplicación |
| `presupuesto` | Presupuesto solicitado en soles, si el perfil lo indica; no es una venta ni ingreso |
| `resultados` | Cantidad simulada de viajes en la respuesta: 0 o 3 |
| `duracion_ms` | Latencia simulada de una respuesta completada |
| `codigo_error` | Escenario ficticio `503`, `red` o `tiempo_agotado`, solo en eventos de error |

## Diccionario de los usuarios ficticios

El CSV por usuario incluye el UUID y los campos de la consulta, además de:

| Campo | Significado |
|---|---|
| `usuario_ficticio` | Código secuencial sin relación con una persona real |
| `consulta_kit` | ID de la consulta original asignada, entre 1 y 40 |
| `fecha_local`, `hora_local` | Día y hora de inicio de la sesión en Perú |
| `etapa_final` | Etapa principal alcanzada; guardar tiene prioridad sobre compartir o imprimir |
| `ultima_accion` | Última acción cronológica registrada en esa sesión |
| `acciones` | Número total de eventos de la sesión |
| `guardo`, `compartio`, `imprimio` | `True` o `False`, según las acciones del usuario ficticio |

El perfil asignado aparece en este CSV aunque el usuario ficticio no llegue a enviarlo. Para medir preferencias efectivamente enviadas en la simulación, usen los eventos `busqueda_iniciada`. El dashboard trabaja con los eventos, no con preferencias que nunca se enviaron.

## Una tarea sencilla para el equipo

1. Abran el panel en Simulación y comprueben que tiene 200 sesiones.
2. Elijan una fecha y expliquen por qué los conteos cambian al filtrar.
3. Comparen el gráfico de estados con `usuarios_200.csv`; su suma debe coincidir con 200 antes de filtrar.
4. Expliquen un gráfico de Pareto y una correlación. Describan lo observado sin decir que una variable causó la otra.
5. Prueben una búsqueda en Actividad registrada y verifiquen que no altera el ejemplo sintético.

La proyección calculada sobre este historial sigue siendo una demostración sobre datos ficticios. Su error de validación, aunque se calcule correctamente, no representa capacidad predictiva demostrada sobre visitantes reales.

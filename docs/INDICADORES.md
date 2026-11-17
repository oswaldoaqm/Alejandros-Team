# Indicadores de uso de DreemGO

Este panel acompaña al planificador que ya construyó el equipo. Mide cómo se usa la web y si las consultas llegan a un resultado. No cambia el motor, las rutas ni el costo estimado de un viaje.

La [decisión original de funcionar sin cuentas](./decisiones/0001-sin-login-y-enlace-compartible.md) se mantiene. La medición anónima y opcional es una ampliación de esta copia; el equipo debe decidir si la incorpora a su producto y ajustar su aviso de privacidad antes de publicarla.

## Dos fuentes que no se mezclan

- **Simulación:** 200 usuarios ficticios, con una sesión por usuario, generados con las consultas y destinos del kit de evaluación del equipo. Sirve para enseñar el recorrido del usuario y probar las gráficas. No representa visitantes reales ni una prueba de 300 personas conectadas simultáneamente. Se regenera con `python -m evaluacion.simular_actividad`.
- **Actividad registrada:** acciones anónimas enviadas únicamente por visitantes que activaron «Compartir estadísticas anónimas». La web conserva los viajes guardados en el navegador; el panel solo recibe el tipo de acción y categorías del viaje. No recibe nombres, correos, la URL completa ni pagos.

El archivo de simulación legible y su CSV están en `data/simulacion/`. Una copia idéntica del JSON viaja dentro del paquete del API para que el ejemplo se vea también en un contenedor.

## Cómo se conectan las partes

1. `app/src/` muestra el formulario, los resultados y la vista separada `/#/indicadores`.
2. Con consentimiento activo, la web envía acciones a `POST /v1/analitica/eventos`. Una entrada al sitio inicia una sesión de uso; abrir solamente el panel de indicadores no añade una visita. Preguntar en la ayuda o enviar un comentario agrega solo el tipo de acción, nunca el texto. Si este envío falla, la web sigue funcionando.
3. `dreemgo/analitica.py` valida las categorías y guarda la actividad real en SQLite. La fecha la pone el servidor. Cada acción nueva lleva `id_evento`: si el navegador vuelve a enviar el mismo identificador, el servidor reconoce el reintento y no suma otra acción.
4. `GET /v1/analitica/resumen?modo=simulacion` calcula los indicadores desde el archivo de ejemplo. `modo=real` los calcula desde SQLite y exige la clave de lectura en la cabecera `X-Clave-Analitica`.
5. En «Actividad registrada», el panel consulta los datos cada tres segundos mientras está visible. «Pausar» detiene esas lecturas y «Reanudar» las activa de nuevo. También se pausa automáticamente al dejar la pestaña en segundo plano. «Actualizar ahora» permite pedir una lectura manual. El modo simulado mantiene su archivo de ejemplo; no aumenta cuando alguien utiliza la web.

Esta actualización es una consulta periódica, no una transmisión instantánea. Normalmente se verá una acción en la siguiente lectura, más el tiempo que tarde la red y el servidor. Si la conexión falla, el panel conserva las últimas cifras recibidas y avisa que no logró actualizarlas.

La pantalla distingue dos momentos: **última lectura**, entregada como `consultado`, indica cuándo se calculó la respuesta; **última acción**, entregada como `actualizado`, indica cuándo ocurrió el evento más reciente del periodo. Una lectura puede ser reciente aunque no haya entrado ninguna acción nueva.

La sección de actividad reciente muestra las últimas ocho acciones de la fuente y del periodo elegidos, con su hora y una descripción breve. No muestra identificadores de sesión ni permite identificar a una persona. Los filtros y la gráfica diaria usan días de Perú, de medianoche a medianoche en UTC−05:00; el contrato lo señala como `America/Lima`.

## Qué significan los 24 indicadores

| Grupo | Indicadores | Cómo leerlos |
|---|---|---|
| Uso | Sesiones; formularios abiertos | Sesiones anónimas con actividad y veces que se abrió el planificador. Una persona puede iniciar más de una sesión. |
| Búsqueda | Búsquedas iniciadas; completadas; con viajes; sin viajes; tasa con viajes; formularios sin búsqueda | La tasa con viajes divide respuestas con al menos una ruta entre respuestas completadas. Formularios sin búsqueda cuenta sesiones que abrieron el formulario sin enviar una búsqueda dentro del periodo. No confirma abandono: alguien podría estar completándolo. |
| Interacción | Itinerarios abiertos; sesiones que abrieron ruta; viajes guardados; guardado tras abrir; viajes compartidos; compartido tras abrir; PDF o impresión; preguntas en la ayuda; comentarios enviados | Guardados cuenta acciones confirmadas por el navegador. Las tasas de guardar y compartir usan como base las sesiones que abrieron un itinerario. La ayuda cuenta preguntas escritas o elegidas y los comentarios solo después de que el buzón los confirma. No se copia su contenido a la analítica. |
| Calidad | Errores de consulta; sesiones con error; porcentaje de sesiones con error; respuesta mediana; respuesta p95 | Las duraciones salen del navegador al recibir una búsqueda. Si no hay respuestas con tiempo medido, aparecen como «Sin datos». |
| Preferencias | Días solicitados; presupuesto mediano | Se calculan con búsquedas iniciadas. La mediana de presupuesto omite consultas sin ese filtro. |

El gráfico diario muestra sesiones, búsquedas, itinerarios abiertos o guardados. En «Comparar con» se puede superponer una segunda serie del mismo período y consultar ambas cifras en la tabla bajo el gráfico. Los dos rankings muestran destinos abiertos e intereses elegidos. Un filtro de fechas cambia todos los cálculos; al dejar las fechas vacías se ve el período completo de la fuente seleccionada.

Cuando una tasa no tiene denominador, se muestra «Sin datos». Por ejemplo, todavía no se puede calcular la tasa de búsquedas con viajes si no se completó ninguna búsqueda. Tampoco se interpreta la cantidad de sesiones como usuarios únicos o personas conectadas en este instante: una persona puede abrir varias sesiones y solo se cuentan las que aceptaron compartir estadísticas. Una sesión que solo usa la ayuda aparece como «Usó la ayuda sin planear un viaje» en la distribución, sin atribuirle una compra ni una causa de abandono.

## Ejecución local

Desde la raíz del proyecto, en Windows, con Python 3.11 o posterior y Node 22.12 o posterior:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[api]"
$env:DREEMGO_CLAVE_ANALITICA = "una-clave-local-que-solo-conozca-el-equipo"
.\.venv\Scripts\python.exe -m uvicorn dreemgo.api.app:app --port 8000
```

En una segunda terminal:

```powershell
cd app
npm ci
npm run dev
```

Abrir `http://localhost:5173/#/indicadores`. La simulación se ve sin clave. Para ver «Actividad registrada», ingresar en la pantalla la misma clave que se configuró en la terminal del API. La clave permanece en memoria de esa pantalla y no se añade al enlace.

El archivo SQLite se guarda por defecto en el directorio personal del servidor (`~/.dreemgo/actividad.sqlite3`). `DREEMGO_ANALITICA_DB` permite elegir otro archivo. En un contenedor, ese archivo debe ubicarse en un volumen persistente para sobrevivir a una reconstrucción; en AWS Lambda el almacenamiento local es temporal. La simulación no se inserta en SQLite.

## Cómo comprobar que el panel cambia

1. Abran el panel en una ventana y entren a «Actividad registrada» con la clave del equipo. Anoten las cifras de sesiones, búsquedas e itinerarios abiertos.
2. Abran la página de DreemGO en otra ventana privada y activen el permiso «Compartir estadísticas anónimas» del pie de página. La ventana privada permite probar una sesión distinta.
3. Vuelvan al panel, manténganlo visible y comprueben que la siguiente lectura registra la nueva sesión.
4. En la ventana del visitante, hagan una búsqueda y abran uno de los viajes. Al volver al panel deberán aparecer la búsqueda iniciada, la completada y la apertura del itinerario, además de las acciones recientes. Pueden usar «Actualizar ahora» si pausaron la lectura automática.
5. Abran «¿Te ayudamos?», escriban una pregunta y envíen un comentario de ejemplo. Con el permiso activo, la siguiente lectura debe sumar una pregunta y un comentario; el texto solo podrá verse en el buzón del equipo. Si revocan el permiso, nuevas consultas no aumentarán esas cifras.
6. Recarguen el sitio del visitante dentro de la misma sesión. La sesión no debe contarse de nuevo. Una búsqueda nueva sí constituye otra acción.

## Cuidado de la medición

La base conserva los registros de la versión anterior y añade automáticamente el campo necesario para reconocer reintentos. SQLite usa WAL para permitir que las lecturas convivan con las escrituras; las inserciones se protegen con una transacción y las consultas por fechas aprovechan un índice. El resumen se entrega con `Cache-Control: no-store` para que la pantalla no reutilice cifras antiguas desde una caché.

Para frenar un bucle accidental del navegador, la API acepta como máximo 120 acciones por minuto y sesión. Si se supera ese límite, responde `429` y pide esperar un minuto. Esta protección no identifica robots ni demuestra que las acciones correspondan a personas: el registro es anónimo y su entrada es pública.

La solución está pensada para una instancia del API y una base local persistente. Varios servidores con archivos SQLite separados producirían historiales distintos. Antes de ampliar el despliegue, el equipo debe elegir una base compartida y comprobar la carga esperada; los datos simulados incluidos no prueban esa capacidad.

Las decisiones técnicas se apoyan en la [documentación de WAL de SQLite](https://www.sqlite.org/wal.html) y en el manejo de [cabeceras de respuesta de FastAPI](https://fastapi.tiangolo.com/advanced/response-headers/).

## Límite comercial y siguiente trabajo del equipo

DreemGO todavía no vende ni reserva. El costo que muestra es un cálculo para el viajero, no un ingreso de la plataforma. Por eso este panel no afirma cuántas personas compraron, cuánto ganó o perdió el negocio ni quién faltó a una reserva. Para medirlo harían falta un proceso de transacción y datos comprobables, que hoy no forman parte del proyecto.

El equipo puede continuar con tres tareas pequeñas: comprobar con personas ajenas al equipo si entienden la diferencia entre simulación y actividad real; revisar si los nombres y las fórmulas de las tarjetas responden a sus preguntas; y documentar dónde se almacenaría la base al desplegar su propia copia. Sus calificaciones del cuadernillo de viajes siguen siendo una evaluación distinta de esta analítica de uso.


## Ampliación para gerencia

El escenario inicial contiene 200 usuarios ficticios con una sesión por usuario,
distribuidos en 28 días completos. Sus supuestos y archivos se describen en
[SIMULACION_200.md](./SIMULACION_200.md). Los antiguos archivos de 300 sesiones
quedan como historial; la API carga el archivo nuevo de 200.

El panel conserva sus indicadores anteriores y añade dos conteos de uso de la ayuda. Permite estudiar el recorrido, su
distribución, los tiempos de respuesta, las asociaciones entre variables y una
proyección didáctica. Todos los gráficos respetan el modo y periodo elegidos.
Los conteos son observaciones del archivo simulado o de la base real: no se
completan con cifras comerciales inexistentes.

El Pareto organiza situaciones observadas; el diagrama de causa y efecto
presenta hipótesis para investigar. Ninguno demuestra por sí solo por qué una
persona dejó de interactuar. Una correlación tampoco prueba causalidad.
La proyección usa una validación temporal y muestra su error; en modo simulado
solo explica el procedimiento, sin predecir la demanda real de DreemGO.

Referencias: [NIST](https://www.itl.nist.gov/div898/handbook/eda/section3/eda33q.htm),
[Pareto de ASQ](https://asq.org/quality-resources/pareto),
[Ishikawa de ASQ](https://asq.org/quality-resources/fishbone),
[Forecasting Principles and Practice](https://otexts.com/fpp3/toolbox.html).

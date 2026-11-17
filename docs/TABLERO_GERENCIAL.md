# Cómo usar el tablero de control independiente

El archivo **`app/public/tablero-gerencial.html`** reúne indicadores de uso, estrategia, calidad y tecnología, marketing y un escenario financiero. Es una página aparte: conserva la tipografía y los colores de DreemGO y no reemplaza la web del equipo ni su recomendador. Los términos y cifras destacados aparecen en **_negrita y cursiva_**.

## 1. Abrir el ejemplo sin instalar nada

1. Extrae el ZIP del proyecto.
2. Abre `app`, después `public` y haz doble clic en `tablero-gerencial.html`.
3. Elige una sección del menú: Visión general, Estrategia, Calidad y TI, Marketing o Finanzas.
4. Abre las tablas de los gráficos y pulsa una celda del mapa de calor para leer su detalle.
5. En Finanzas, cambia un supuesto y observa cómo se recalculan las cifras.

El HTML ya contiene una instantánea de **200 usuarios ficticios, una sesión por usuario y 932 eventos**, repartidos en 28 días completos, del **14 de octubre al 10 de noviembre de 2026**. No necesita consultar un archivo JSON ni un servidor para mostrar ese ejemplo. Se puede compartir el HTML solo para explorar la simulación. Las fuentes tipográficas se solicitan a Google Fonts si hay conexión; sin Internet se usan las familias de respaldo del proyecto.

Esta instantánea no se anima ni agrega visitas por sí sola. Sirve para estudiar un conjunto reproducible de datos. Los tiempos y comportamientos son supuestos de simulación; no representan una prueba de carga de 200 personas, usuarios reales, ventas ni resultados comerciales. El detalle está en [SIMULACION_200.md](SIMULACION_200.md).

## 2. Ver los cambios producidos por la página de viajes

Sigue primero los pasos de instalación de [00_COMIENZA_AQUI.txt](./revision_del_profesor/00_COMIENZA_AQUI.txt), en la raíz. Mantén abiertos el API y la web de esta copia. Configura `DREEMGO_CLAVE_ANALITICA` antes de iniciar el API.

1. Abre `http://localhost:5173/tablero-gerencial.html`. Si Vite usa otro puerto, utiliza el que muestre la terminal; por ejemplo, `http://localhost:5174/tablero-gerencial.html`.
2. Selecciona **Actividad real**. Introduce la dirección del API, normalmente `http://localhost:8000`, y la clave que configuró el equipo. Pulsa **Conectar**.
3. Abre la página de viajes con el enlace del tablero. El enlace conserva el mismo servidor y puerto cuando el tablero está servido por la web.
4. En la página de viajes, activa el permiso opcional para registrar actividad. Realiza una búsqueda, abre una propuesta y guarda un viaje.
5. Vuelve al tablero: consulta el API cada **tres segundos mientras la pestaña está visible**. También puedes actualizar o pausar la consulta desde sus controles.

La sesión anónima no identifica a una persona única. Un contador de búsquedas o guardados puede incluir varias acciones de una misma sesión. El embudo, en cambio, cuenta sesiones que recorrieron sus pasos en orden. No todos los visitantes aceptarán el registro, por lo que la actividad no equivale al tráfico total del sitio.

El modo real no suma las 200 sesiones ficticias. Consulta el almacenamiento de actividad del API. El modo simulación vuelve a la instantánea incrustada. En ambos modos las finanzas siguen siendo un escenario hipotético.

Al abrir el archivo mediante `file://`, se mantiene disponible la simulación y se bloquea la conexión real. Para usar el API, abre el tablero mediante la web local. La clave se envía en la cabecera `X-Clave-Analitica`, queda solo en memoria y no se escribe en archivos, URL, CSV ni almacenamiento del navegador. Al recargar hay que volver a introducirla. Cambiar el campo de dirección o clave no modifica una conexión ya iniciada hasta pulsar Conectar.

## 3. Qué explica cada sección

| Sección | Qué permite revisar | Cómo interpretarlo |
|---|---|---|
| Visión general | Sesiones, búsquedas, aperturas, guardados, actividad diaria y distribución de estados | Los 22 indicadores de base tienen una definición desplegable. El gráfico circular asigna una sola etapa a cada sesión. |
| Estrategia | Activación de búsqueda, recorrido hasta guardar, cobertura de respuestas, embudo, Pareto y proyección | Guardar no demuestra compra. El Pareto ordena estados observados, no causas. La proyección compara métodos sencillos con un bloque final de validación; no garantiza demanda futura. |
| Calidad y TI | Respuestas, errores, búsquedas sin viajes, mediana y p95 de respuesta, histograma, calor y correlaciones | La tasa de respuestas no mide disponibilidad del servidor. Una respuesta sin viajes es válida. Los tiempos requieren tamaño de muestra; las asociaciones no demuestran causalidad. |
| Marketing | Sesiones, guardados, compartidos, intereses y destinos abiertos | Compartir un enlace no demuestra su alcance posterior. El presupuesto por sesión o guardado es un ejercicio de planificación, no CAC ni atribución de ventas. |
| Finanzas | Operaciones supuestas, ingresos, costos, resultado, margen, equilibrio y ROI operativo del escenario | Todo depende de supuestos editables. No hay una integración comercial que confirme compras, ingresos o ganancias. |

La cobertura del recomendador indica cuántas respuestas contienen alguna ruta. No equivale a satisfacción ni a precisión del ranking. El cuadernillo del equipo sigue siendo necesario para evaluar la calidad de las propuestas con personas.

## 4. Entender el escenario financiero

Los valores iniciales son **ilustrativos**: ingreso por operación S/ 20; costo variable por operación S/ 5; costo fijo del periodo S/ 500; presupuesto de marketing del periodo S/ 300; conversión comercial hipotética 10%. Los costos fijos y el presupuesto corresponden al periodo completo mostrado, no a cada día. Cambiarlos no altera los datos del API ni el modelo.

| Cálculo | Fórmula | Con 200 sesiones y los supuestos iniciales |
|---|---|---|
| Operaciones estimadas | Sesiones × conversión / 100 | 20 |
| Ingresos | Operaciones × ingreso por operación | S/ 400 |
| Costo variable total | Operaciones × costo variable unitario | S/ 100 |
| Costos totales | Costo variable total + costo fijo + marketing | S/ 900 |
| Resultado | Ingresos − costos totales | −S/ 500 |
| Margen | Resultado / ingresos × 100 | −125% |
| Punto de equilibrio | Redondeo hacia arriba de (costo fijo + marketing) / (ingreso unitario − costo variable unitario) | 54 operaciones |
| ROI operativo supuesto | Resultado / costos totales × 100 | −55,56% |
| Presupuesto por sesión | Marketing / sesiones | S/ 1,50 |
| Presupuesto por acción de guardar | Marketing / acciones de guardar | S/ 5,00 |

Las operaciones son un valor esperado: pueden resultar decimales. El punto de equilibrio sí se expresa en operaciones enteras. Si ingreso unitario no supera costo variable unitario, se indica que no se alcanza equilibrio mediante más operaciones bajo esos supuestos. Si un denominador es cero, se muestra **Sin datos**. El formulario rechaza campos vacíos, números negativos y conversiones mayores que 100%.

Un resultado negativo es parte del ejercicio. Por ejemplo, cambiar la conversión de 10% a 20% genera 40 operaciones, S/ 800 de ingresos, S/ 1 000 de costos y −S/ 200 de resultado con los demás supuestos iniciales intactos. Los gráficos muestran magnitudes y conservan el signo en la cifra del resultado.

## 5. Descargar y comprobar los indicadores

**Descargar indicadores CSV** genera `DreemGO_indicadores_simulacion.csv` o `DreemGO_indicadores_actividad.csv`, según la fuente seleccionada. Incluye una cabecera, **22 filas de indicadores de uso** y **14 filas del escenario financiero vigente**, con fuente, fecha inicial, fecha final, ID, nombre, valor, unidad y definición. Exporta los valores sin redondearlos de nuevo.

Las filas financieras llevan la fuente **Escenario hipotético**, identifican si su base corresponde a simulación o actividad e incluyen la base de sesiones, los cinco supuestos editables y ocho resultados. Al modificar la conversión u otro supuesto y descargar de nuevo, el CSV refleja el nuevo cálculo. No es una cuenta financiera real. Si algún campo financiero está vacío o es inválido, el archivo incluye únicamente los 22 indicadores de uso: corrige primero ese campo para exportar también el escenario. Los cocientes sin denominador se exportan vacíos. No se incluye el detalle de los gráficos ni claves. Se usa UTF-8 con BOM y separador de punto y coma; si Excel abre todo en una columna, importa el archivo como texto UTF-8 y selecciona `;` como delimitador.

Para revisar datos de la simulación al nivel de eventos o usuarios, utiliza `data/simulacion/actividad_200.csv` y `data/simulacion/usuarios_200.csv`. Son archivos diferentes de la exportación agregada del tablero. El diccionario y sus relaciones están en [SIMULACION_200.md](SIMULACION_200.md).

## 6. Regenerar la instantánea

Desde la raíz del proyecto, con el entorno Python instalado:

```powershell
# Solo si quieren regenerar los datos ficticios con los parámetros por defecto:
.\.venv\Scripts\python.exe -m evaluacion.simular_actividad

# Copiar sus agregados al HTML independiente:
.\.venv\Scripts\python.exe -m evaluacion.exportar_tablero
```

Después vuelve a abrir o recarga el HTML. El segundo comando es necesario porque el archivo independiente lleva una copia de los agregados; no lee automáticamente un JSON que cambió en disco. El exportador utiliza `leer_simulacion()` y `resumir()`, igual que la analítica del proyecto. No consulta ni modifica SQLite ni agrega actividad real.

## 7. Dónde está el código y cómo comprobarlo

| Archivo | Responsabilidad |
|---|---|
| `app/public/tablero-gerencial.html` | Estilos, controles, gráficos SVG y funciones de cálculo. El bloque `datos-iniciales` contiene la instantánea. |
| `evaluacion/exportar_tablero.py` | Sustituye únicamente ese bloque JSON por el resumen de simulación actualizado. |
| `tests/tablero_finanzas.test.cjs` | Comprueba fórmulas, divisiones, CSV, textos por fuente, enlaces y sintaxis con Node, sin bibliotecas adicionales. |
| `tests/test_exportar_tablero.py` | Comprueba la inclusión de 200 sesiones y que el exportador conserve el resto de la plantilla. |

```powershell
node --test tests/tablero_finanzas.test.cjs
.\.venv\Scripts\python.exe -m pytest tests/test_exportar_tablero.py -q
```

## 8. Qué les toca completar

Cada grupo puede cerrar esta parte con tres acciones sencillas: **comprobar un indicador contra el CSV**, **explicar un gráfico sin confundir asociación con causa** y **cambiar un supuesto financiero, escribir el resultado esperado y compararlo con la pantalla**. Después hagan una búsqueda real con el permiso de actividad y confirmen que aparece en el modo correspondiente. No necesitan rehacer el frontend ni el recomendador.

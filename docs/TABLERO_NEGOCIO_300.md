# Tablero de negocio de DreemGO

Este manual acompaña `app/public/tablero-negocio.html`. El tablero permite ensayar cómo seguir el recorrido comercial de DreemGO, desde la visita hasta una **compra simulada**, con 300 usuarios ficticios. Sirve para explicar indicadores y tomar decisiones dentro de ese escenario. Los alumnos pueden seguir trabajando desde la web y el recomendador que ya construyeron.

La aplicación actual ayuda a planear viajes; no cobra, reserva ni registra una aceptación comercial. Por eso el tablero declara la simulación en el título, en los datos y en las cifras económicas. Las interacciones, elecciones A/B, compras, canales e importes del conjunto de 300 se generaron para la demostración. El [documento de datos](SIMULACION_NEGOCIO_300.md) explica exactamente cómo.

## Abrirlo y reconocer cada parte

Para ver la simulación, extraigan el ZIP y abran `app/public/tablero-negocio.html` con el navegador. La instantánea de los 300 registros viaja dentro del archivo. También pueden ejecutar la web con `cd app`, `npm ci`, `npm run dev` y abrir `http://localhost:5173/tablero-negocio.html` (usen el puerto que muestre Vite). En la página de viajes encontrarán el enlace **Tablero de negocio (simulación)**.

La barra lateral organiza Resumen, Recorrido, Propuestas A y B, Economía y Cómo leerlo. Arriba aparecen controles para **reproducir los 300 registros**, pausarlos, avanzar de 25 en 25 y elegir velocidad. El control deslizante permite volver a cualquier tamaño de muestra entre 0 y 300. La reproducción enseña cómo cambian los indicadores cuando se incorporan registros del mismo conjunto; no crea visitantes nuevos ni modifica la API.

Los filtros de fechas, canal, interés principal, alternativa abierta, día de la semana y franja horaria actúan sobre **los mismos registros** de las tarjetas y los gráficos. Comiencen con los 300 visibles, cambien un filtro, observen el contador de registros seleccionados y revisen los gráficos juntos. El mapa de calor mantiene visibles las otras celdas al elegir día y hora para poder comparar y cambiar de selección; las tarjetas y los demás gráficos sí quedan filtrados. **Limpiar filtros** quita todas esas selecciones; conserva el número de usuarios incorporados. Para regresar a toda la cohorte, lleven también el control deslizante a 300. El botón **Descargar CSV** permite llevar la selección actual a una tabla para revisar un cálculo.

## Qué se ve al empezar

| Paso del recorrido | Usuarios ficticios |
|---|---:|
| Visitaron | 300 |
| Interactuaron con el formulario | 283 |
| Enviaron una búsqueda | 243 |
| Recibieron las propuestas A y B | 213 |
| Abrieron una de ellas | 168 |
| Aceptaron una propuesta en la simulación | 95 |
| Compraron en la simulación | 40 |

El embudo cuenta **personas ficticias únicas**, una vez por etapa. La tasa de aceptación entre quienes abrieron una propuesta es 95/168 = 56,5 %. La conversión comercial del ejemplo es 40/300 = 13,3 % de las visitas. Indiquen siempre el denominador y el filtro activo antes de comparar tasas. Los guardados y compartidos que aparecen en el archivo son acciones del escenario de uso y no equivalen a compras.

La serie diaria superpone visitas, interacciones y compras simuladas. El embudo deja ver en qué paso disminuye la cohorte. La distribución de resultados muestra la última etapa alcanzada por cada usuario ficticio. Son tres lecturas del mismo conjunto, no tres fuentes que deban sumarse.

## Dos gráficos para explorar el recorrido

**Último paso antes de la compra simulada** ordena los perfiles que no llegaron a comprar según `etapa_final`. Cada perfil aparece una sola vez. La barra indica cuántos quedaron en ese estado y la línea dorada muestra el porcentaje acumulado. La tabla debajo del gráfico ofrece los mismos conteos y porcentajes. El orden ayuda a elegir qué paso investigar primero; no demuestra la causa de que una persona se detuviera.

**Visitas por día y hora** cuenta los perfiles por día de la semana de `fecha_local` y por franjas de seis horas de `hora_local`. Cada celda muestra su cantidad exacta y el tono rojo permite localizar las más pobladas. Pulsen una celda para filtrar tarjetas, otros gráficos y CSV; púlsenla otra vez para quitar ese filtro. El mapa conserva los conteos de las otras celdas para que puedan comparar y elegir otra. También pueden elegir día y franja desde la barra de filtros. La tabla debajo del mapa contiene los conteos para revisarlos sin depender del color. Las horas y las visitas proceden del conjunto ficticio, no del tráfico público de la web.

Ambos gráficos cambian al reproducir de 0 a 300 y al usar fechas, canal, interés o alternativa. Si esos filtros dejan cero perfiles, muestran un estado vacío. Para comprobar que parten de la misma base, sumen las celdas del mapa de calor: con toda la cohorte visible, deben dar **300**. Sumen las barras del gráfico de último paso: deben dar **260**, es decir, 300 perfiles menos las 40 compras simuladas.

## Cómo leer las propuestas A y B

El motor del proyecto puede ofrecer hasta tres rutas ordenadas. En este ejercicio, **A representa la primera y B la segunda**. Se registraron 93 aperturas de A y 75 de B; de ellas, 52 y 43 terminaron en aceptación simulada. Entre las compras ficticias hubo 24 de A y 16 de B.

La barra comparativa permite contrastar aperturas, aceptaciones y compras por alternativa. Para una tasa de aceptación de A utilicen 52/93; para B, 43/75. Una mayor cantidad o tasa en esta muestra no demuestra que una opción sea mejor: las alternativas proceden del orden del motor y los usuarios no se asignaron al azar. Tampoco se ha medido satisfacción real.

El gráfico de canales presenta Directo, Redes sociales, Búsqueda y Referidos. Esos canales se asignaron artificialmente. Sus diferencias ayudan a practicar segmentación; no miden una campaña real ni permiten atribuir compras a marketing.

## Cómo leer la economía

Los supuestos iniciales son S/ 20 de ingreso por compra ficticia, S/ 5 de costo variable por compra, S/ 500 de costo fijo del periodo y S/ 300 de presupuesto de marketing. Con las 40 compras simuladas de la muestra completa, los ingresos son **S/ 800**, los costos variables **S/ 200**, los costos totales **S/ 1 000** y el resultado **−S/ 200**. El presupuesto de viaje que una persona introduce para recibir recomendaciones es una preferencia de gasto; no es ingreso para DreemGO.

Cuando se aplica un filtro, se suman los importes y costos variables de las filas visibles. Los S/ 500 de costo fijo y S/ 300 de marketing se mantienen **completos** para el periodo, incluso si se muestra un solo canal o una alternativa. Así, el resultado filtrado responde a «¿qué ocurriría con estos ingresos y los costos completos del periodo?». No es la ganancia atribuible al segmento. Por ejemplo, Redes sociales reúne 92 usuarios y 15 compras ficticias: S/ 300 de ingresos menos S/ 75 variables y S/ 800 de costos del periodo da **−S/ 575**. No sumen resultados de varios filtros: volverían a contar los mismos costos fijos y de marketing. El botón CSV permite revisar las filas que alimentan los importes variables.

La conversión por interés usa las compras ficticias de cada interés principal sobre sus usuarios seleccionados. Si un grupo es pequeño, la tasa puede cambiar mucho con pocos casos; lean primero los conteos.

## Relación con la web y con el modelo

El tablero comercial funciona con `data/simulacion/negocio_300.json` y su CSV. El generador `evaluacion/simular_negocio.py` utiliza el kit de consultas y las dos primeras alternativas del motor, pero **simula** las decisiones posteriores. La web de viajes y el motor siguen ejecutándose normalmente; no se instalaron pagos ni se reentrenó el recomendador para producir los gráficos.

El panel `/#/indicadores` es **Actividad del sitio**: allí se estudia otra simulación de 200 sesiones y, con permiso del visitante y la API local, se puede ver actividad registrada. Sus cifras no deben sumarse a las 300 del tablero comercial. Para interpretar o verificar compras reales en el futuro, el equipo tendría que diseñar un paso de aceptación verificable y un registro de transacciones, definir permiso y evaluar esos datos antes de llamar venta a un resultado.

## Trabajo breve para los alumnos

1. Reproduzcan de 0 a 300. Pausen en un tamaño intermedio y expliquen qué cambió en el embudo y por qué el denominador ya no es 300.
2. Filtren un canal o una alternativa. Descarguen el CSV y comprueben una cantidad y una tasa del tablero con las filas visibles.
3. Presenten una captura del gráfico A/B y otra del resultado económico. Expliquen en un párrafo qué datos son simulados y qué paso medirían después en la web real.

Los archivos que conviene abrir para continuar son `app/public/tablero-negocio.html` para la vista, `evaluacion/simular_negocio.py` para los datos, `data/simulacion/negocio_300.csv` para comprobar cifras y [SIMULACION_NEGOCIO_300.md](SIMULACION_NEGOCIO_300.md) para el diccionario y los supuestos. Las guías anteriores del sitio, el modelo y la actividad permanecen disponibles en `docs/revision_del_profesor/guias/` y `docs/`.

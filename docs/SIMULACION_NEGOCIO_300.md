# Seguimiento comercial con 300 usuarios ficticios

Este archivo explica la simulación comercial que alimenta el tablero de negocio. **Los 300 usuarios, sus canales, aceptaciones, compras y montos son ficticios.** DreemGO actualmente recomienda itinerarios, pero no registra la aceptación formal de una propuesta, procesa pagos ni confirma ventas. La simulación permite practicar cómo se leería un embudo comercial si el equipo añadiera esos pasos en el futuro.

El proyecto conserva los archivos anteriores `actividad_200.*` y `actividad_300.*`, que describen solo actividad de la web. El nuevo escenario está en `data/simulacion/negocio_300.json` y `data/simulacion/negocio_300.csv`. Tiene una fila por usuario ficticio y por sesión, durante 28 días completos, del 14 de octubre al 10 de noviembre de 2026, en hora de Perú. Ninguna fila corresponde a un alumno o viajero real.

## Cómo se formó el recorrido

El generador `evaluacion/simular_negocio.py` parte del kit de 40 consultas que usa el equipo y de la función de simulación de actividad, con semilla 42. Ese kit aporta origen, días e intereses; el comportamiento que se muestra sigue siendo supuesto. El canal de llegada es una asignación ficticia adicional, con pesos de 38 % para Directo, 32 % para Redes sociales, 20 % para Búsqueda y 10 % para Referidos. Las diferencias entre canales en los gráficos no demuestran cuál funciona mejor en una campaña real.

El kit de evaluación guardó tres alternativas por consulta. En este ejercicio, **A y B son las dos primeras alternativas del ranking guardado en ese kit al generar la simulación**. La nueva regla de intereses de esta copia cambia el orden en tres de las cuarenta consultas del kit; por eso A y B no siempre coinciden con las dos primeras rutas que devuelve hoy la web. El archivo se conserva como escenario histórico reproducible, sin reescribir el kit ni las evaluaciones del equipo. La tercera alternativa del kit sigue existiendo, pero el ejercicio comercial practica una decisión entre las primeras dos. A/B **no es un experimento aleatorizado** ni una comparación de modelos. Una persona ficticia puede abrir A o B, aceptar solo la que abrió o ninguna. Aceptar es una decisión afirmativa simulada; un guardado en la web no se interpreta como aceptación.

La simulación comercial usa semilla 73 para tres pasos adicionales. Entre quienes abrieron una alternativa, la probabilidad supuesta de abrir A es 55 %; entre quienes la abrieron, la de aceptar es 55 %; entre quienes aceptaron, la de comprar es 42 %. Son parámetros didácticos. La compra se crea únicamente después de la aceptación y **no ejecuta una transacción**. Los archivos no se insertan en la base SQLite de actividad real.

## Cifras de control del archivo entregado

| Etapa | Usuarios ficticios | Lectura |
|---|---:|---|
| Visitó la web | 300 | Inicio de cada sesión ficticia |
| Interactuó | 283 | Abrió el formulario |
| Buscó | 243 | Envió una consulta |
| Vio A y B | 213 | Recibió rutas del motor |
| Abrió A o B | 168 | Revisó una alternativa |
| Aceptó A o B | 95 | Decisión afirmativa simulada |
| Compró | 40 | Compra totalmente simulada |

De las 95 aceptaciones ficticias, 52 corresponden a A y 43 a B. De las 40 compras ficticias, 24 se asocian a A y 16 a B. Los 300 se reparten además por el canal supuesto: 127 Directo, 92 Redes sociales, 59 Búsqueda y 22 Referidos. El archivo de actividad aporta 86 guardados, 38 acciones de compartir y 13 errores de consulta; guardar y compartir siguen siendo señales de uso, no compras.

Cada tasa debe indicar su denominador. Por ejemplo, **aceptación de alternativas abiertas** es 95/168 = 56,5 %, mientras que **conversión de visita a compra simulada** es 40/300 = 13,3 %. Para comparar A y B, dividan las aceptaciones o compras por la cantidad de personas que abrió cada alternativa. Contar solo compras de A y B no prueba que una sea mejor, porque no hubo asignación experimental ni control de preferencias.

## Economía ficticia

Se reutilizan los valores ilustrativos del tablero anterior: S/ 20 de ingreso por compra simulada, S/ 5 de costo variable por compra, S/ 500 de costo fijo del periodo y S/ 300 de presupuesto de marketing del mismo periodo. Por tanto:

- Ingresos simulados: 40 × S/ 20 = **S/ 800**.
- Costo variable simulado: 40 × S/ 5 = **S/ 200**.
- Costos totales supuestos: S/ 200 + S/ 500 + S/ 300 = **S/ 1 000**.
- Resultado del escenario: S/ 800 − S/ 1 000 = **−S/ 200**.

El presupuesto de viaje que una persona escribe para recibir rutas no es un ingreso de DreemGO. La venta del escenario representa una posible operación futura y no una reserva o compra ocurrida. Si se calcula costo por compra simulada, debe etiquetarse como **presupuesto supuesto dividido por compras ficticias**, nunca como costo real de adquisición.

## Campos y reglas para continuar

`usuario_id` y `sesion` son identificadores inventados. `fecha_local`, `hora_local`, `canal_simulado`, `origen`, `intereses`, `dias` y `presupuesto_viaje` sirven para filtrar. `visito`, `interactuo`, `busco`, `vio_propuestas`, `abrio_propuesta`, `acepto_propuesta` y `compra_simulada` forman un embudo de condiciones anidadas. `propuestas_mostradas` vale 2 solo si aparecieron rutas. `propuesta_abierta` y `propuesta_aceptada` son A, B o vacías; `polo_A` y `polo_B` enlazan esas letras con las dos primeras opciones del kit. `importe_simulado` y `costo_variable_simulado` son cero para quienes no compraron. `guardo`, `compartio`, `error_consulta` y `duracion_ms` describen acciones o respuestas del escenario de uso; `etapa_final` agrupa cada sesión en un único estado.

Para reproducir los datos desde la raíz del ZIP:

```powershell
.\.venv\Scripts\python.exe -m evaluacion.simular_negocio
```

Para comprobar la coherencia del archivo:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_simular_negocio.py -q
```

El tablero debe comenzar con los 300 registros y permitir filtrar sin cambiar el archivo. La reproducción progresiva ordena por fecha, hora e identificador y muestra los primeros N registros; se detiene en 300. El panel de actividad real permanece separado. Para avanzar como equipo, contrasten una cifra del dashboard con el CSV, expliquen un denominador y planteen qué dato real deberían registrar —con permiso del usuario— antes de poder afirmar una compra o una preferencia comprobada entre A y B.

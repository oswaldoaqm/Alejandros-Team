# Plan de las tres semanas que quedan

Del 29 de octubre al 18 de noviembre de 2026, el día de la presentación final y la Delivery 2. Cada tarea tiene un responsable, que es quien la defiende frente al jurado, y un criterio de terminado que se puede revisar. Los roles son los del [plan del producto](../../docs/PLAN.md#quién-defiende-qué): Miguel, datos y nube; Alejandro, datos, modelo y evaluación; Diego, motor y API; Christopher, app, usabilidad y requisitos. Alejandro coordina y revisa cada pull request antes de fusionarlo.

Dos reglas valen para las tres semanas. Lo que cambie el motor o los datos entra con una versión nueva de los datos y con lo que cambió en las respuestas medido, como en las decisiones 0013 a 0022. Y las calificaciones del equipo se hacen con el kit de los datos `2026.10.8`: el informe final las reporta para esa versión, y lo que se mide sin ellas (las propiedades, el óptimo, los buses, los grupos en horas) se vuelve a correr con la versión final.

## Semana 13 · del 29 de octubre al 4 de noviembre

| Tarea | Quién | Terminada cuando |
|---|---|---|
| Calificar los 185 viajes del kit de la evaluación ([`docs/evaluacion/anotar.md`](../../docs/evaluacion/anotar.md)) | Los cuatro | Las cuatro calificaciones están en `data/evaluacion/calificaciones/` y `python -m evaluacion.informe` da el acuerdo y las métricas de cada sistema |
| La prueba de usabilidad, con cinco personas fuera del equipo ([`docs/evaluacion/usabilidad.md`](../../docs/evaluacion/usabilidad.md)) | Christopher | Las planillas de `data/evaluacion/usabilidad/` están llenas y `python -m evaluacion.usabilidad` da el SUS y el resumen de las tareas |
| Que la heurística meta la parada que le falta: en 34 de los 47 viajes en que no da el óptimo, le faltan una o dos paradas que sí caben ([`EvaluationReport.md` §4.2](./EvaluationReport.md#42--el-itinerario-contra-el-óptimo-exacto)) | Diego | `python -m evaluacion.optimo` da una brecha menor con 15 candidatas, sin pasar del segundo por consulta |
| Calibrar los tiempos por tierra con los de los buses: en la Carretera Central el motor tarda entre 18 y 26 % menos que el bus más rápido, y de Lima a Paracas y de Ica a Lima, más que el más lento | Alejandro | Las 29 rutas de Cruz del Sur caen en su rango o tienen su explicación, con datos `2026.11.1` |
| Desplegar el API en AWS y medir su arranque en frío | Miguel | La app publicada responde desde AWS y el informe final dice cuánto tarda la primera consulta |
| Los imperdibles con foto y texto en la app | Christopher y Alejandro | Cada imperdible que sale en un viaje tiene foto con su autor y su licencia, o dice por qué no |

## Semana 14 · del 5 al 11 de noviembre

| Tarea | Quién | Terminada cuando |
|---|---|---|
| Arreglar los tropiezos de la prueba de usabilidad | Christopher | Cada tropiezo anotado tiene su arreglo en un pull request o su razón para no hacerlo en el informe final |
| Pasar los grupos de lugares a la v3 de TA-01, con cuatro horas y 1 300 m como topes ([decisión 0023](../../docs/decisiones/0023-ta01-v3-horas-reales.md)) | Alejandro y Miguel | El pipeline arma los grupos con `evaluacion/polos_en_horas.py`, el clima de los grupos nuevos está bajado y los artefactos salen con una versión nueva de los datos, con lo que cambió en las respuestas medido |
| Viajes de varios polos, que pasaron de la semana 12 a la final | Diego | Desde Lima, un viaje puede ir al Cusco y a Machu Picchu en el mismo viaje, y las propiedades se cumplen en 1 000 consultas |
| El costo con el camino real del mapa | Alejandro y Miguel | El transporte del costo sale de los kilómetros del camino que dibuja el mapa |
| La página del proyecto | Christopher | Una página pública con el problema, la demo, el equipo y los enlaces al repositorio y a la app |
| El Data Product Canvas y los requisitos finales | Christopher | Cada requisito de la semana 5 dice si se cumplió, con su evidencia o su porqué |
| Volver a correr la evaluación con la versión final | Alejandro | Las propiedades con 1 000 consultas, las zonas, el óptimo, los buses y los grupos en horas, con los datos finales |

## Semana 15 · del 12 al 18 de noviembre

| Tarea | Quién | Terminada cuando |
|---|---|---|
| El informe final (Delivery 2) | Alejandro, con una sección de cada uno | `FinalReport.pdf` y su fuente editable están en `deliveries/week15/`, cada cifra sale de un script del repositorio y cada sección la revisa quien la defiende |
| La presentación final y el video de la demo | Los cuatro | La presentación está en pptx y en PDF, y cada uno presenta su parte en el tiempo que fije el profesor. El video dura de 5 a 7 minutos, muestra la app publicada, está en YouTube o en otra plataforma abierta, y su enlace va en el informe, en la página del proyecto y en el repositorio |
| La declaración de contribución y las reflexiones | Cada uno la suya | El informe final dice lo que hizo cada uno y trae una reflexión breve sobre cómo se hizo el producto; la reflexión de cada uno sobre el trabajo en equipo está en Canvas |
| El ensayo con preguntas difíciles, el lunes 16 | Los cuatro | Cada uno responde las preguntas de su parte sin ayuda |
| El PDF de los puntos bonus | Alejandro | Subido a Canvas antes del viernes de la semana 15 |

## Lo que no entra

- **Cuentas de usuario.** El enlace es el viaje guardado ([decisión 0001](../../docs/decisiones/0001-sin-login-y-enlace-compartible.md)), y nada de lo que pide el curso necesita cuentas.
- **Horarios y tarifas confirmados de cada lugar.** Las fichas no los traen para todos y verificarlos a mano no cabe en tres semanas. Los viajes siguen diciendo que son estimados.
- **Calificar dos veces.** Las calificaciones valen para los datos `2026.10.8`; una segunda ronda con la versión final no cabe en el calendario, y el informe final lo dice.

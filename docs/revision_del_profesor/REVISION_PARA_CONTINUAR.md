# DreemGO: revisión y continuidad

Esta copia parte de la entrega del 10 de noviembre de 2026 y se revisó de nuevo el 11 de noviembre. La entrega original y su PDF se guardan intactos fuera de esta carpeta. El equipo ya había construido una aplicación React, un API FastAPI, un pipeline de datos, modelos de tiempos y un sistema de evaluación. Las entregas anteriores del repositorio se conservan en `deliveries/` tal como llegaron; no se modificó GitHub.

## Qué encontré

| Parte | Estado comprobado en la copia | Límite que queda |
|---|---|---|
| Datos | Artefactos `2026.11.1`, inventario de 6 225 recursos y procedencia en `DATA_LICENSES.md`. | Los horarios, cierres, tarifas actuales y disponibilidad no están completos en fuentes abiertas. |
| Modelo | Agrupamiento de lugares, regresión para tiempos, reglas de temporada y optimización del itinerario. | Las recomendaciones necesitan calificaciones y pruebas con viajeros externos. |
| Aplicación | Web con formulario, tres resultados, plan diario, mapa, costo, clima y eventos; consume el API local. | El usuario puede interpretar horas estimadas como horarios confirmados si el aviso está lejos del plan. |
| Evaluación | Scripts, resultados y plantillas del equipo. | Faltan las calificaciones restantes y la prueba con cinco personas externas. |

## Qué cambié en esta copia

1. **Coherencia entre rutas y evaluación.** Restablecí exactamente la regla de bus y las rutas que entregó el equipo. Un tope de 12 horas que yo había añadido en una copia anterior modificaba 13 de las 40 consultas del kit sin cambiar `version_datos`: el motor generaba 187 viajes y el kit seguía en 196. Regeneré el kit solo en una carpeta temporal: volvió a producir 40 consultas y 196 viajes. `clave.csv` y `planilla.csv` coinciden byte por byte con los archivos entregados y conservan la huella `490ffe47ecb4`. Así, los enlaces, la versión `2026.11.1` y la evaluación siguen refiriéndose a las mismas rutas. El viaje largo que motivó aquella regla queda como limitación para que el equipo la estudie con evidencia.
2. **Aviso donde se toma la decisión.** El detalle de cada viaje recuerda confirmar horarios, cierres, entradas y transporte. Sale en «Antes de ir», junto al itinerario y los otros avisos. Archivo: `app/src/piezas/DetalleRuta.tsx`.
3. **Apertura local de la web.** El API acepta por defecto tanto `http://localhost:5173` como `http://127.0.0.1:5173`. Antes, al abrir la segunda dirección, el navegador mostraba que no había conexión. Archivos: `dreemgo/api/app.py`, `tests/test_api.py` y `app/README.md`.
4. **Instalación de la interfaz.** Se actualizó `app/package-lock.json` dentro de las versiones permitidas por `package.json`. Una instalación limpia con Node 24.22.1 incluyó la dependencia nativa de Windows y la auditoría de npm no reportó vulnerabilidades. El requisito del proyecto sigue siendo Node 22.12 o posterior.
5. **Laguna de Puno medida.** `evaluacion/islas_puno.py` reproduce tres consultas a Puno y deja el resultado en `data/evaluacion/resultados/islas_puno.json`. Las islas están en los datos, pero ninguna aparece en esos tres itinerarios. `evaluacion/ISLAS_PUNO.md` explica por qué no conviene forzarlas sin revisar el trayecto de bote y las preferencias de usuarios.
6. **Resultados de la búsqueda correcta.** Si alguien cambia de consulta antes de que responda el API, la web espera la respuesta nueva y descarta la tardía. Ya no muestra tarjetas de una búsqueda anterior bajo parámetros nuevos. Archivos: `app/src/estado/pedido.ts`, `app/src/vistas/Resultados.tsx` y su prueba.
7. **Borrado de guardados.** Si el navegador impide escribir en `localStorage`, la web conserva el viaje y avisa del error. Antes decía que lo había borrado aunque aún seguía guardado. Archivo: `app/src/vistas/MisViajes.tsx`.
8. **Datos incompletos.** El API comprueba sus seis artefactos antes de anunciar el motor. Una copia a medio descomprimir responde 503 en lugar de fallar internamente. Archivos: `dreemgo/motor/datos.py` y `tests/test_datos_incompletos.py`.
9. **Fechas fuera del calendario.** Una fecha extrema que antes desbordaba el calendario ahora recibe un 422 comprensible. Una fecha válida cercana al límite sigue funcionando. Archivos: `dreemgo/contrato.py` y `tests/test_api.py`.

## Qué mantuve

El inventario, los artefactos `2026.11.1`, los modelos y la selección de rutas, los colores, imágenes, mapas y pantallas de la web, los enlaces compartibles, el contrato de campos del API, el código de las entregas anteriores y la autoría del equipo. No añadí datos sintéticos ni declaré horarios o tarifas como si fueran actuales.

## Comprobaciones

- La web compiló y sus 264 pruebas de componentes y lógica pasaron. `npm run revisar` pasó con las versiones fijadas por `package-lock.json`.
- Una instalación limpia del paquete web con Node 24.22.1 terminó con auditoría npm sin vulnerabilidades conocidas.
- La prueba de CORS para `127.0.0.1:5173` pasó y la web local cargó sus opciones desde el API.
- `ruff check .` y `ruff format --check .` pasaron. Las 39 pruebas focalizadas del API y datos, y la suite Python completa, terminaron sin errores.
- En la revisión anterior, el navegador mostró el caso Lima, julio, cuatro días, naturaleza e historia, S/ 700 y 3 500 m; se abrió Trujillo y se vio el aviso en «Antes de ir». La integración local de esta copia se volvió a comprobar antes de compartirla.
- La evaluación de Puno se ejecutó con los datos incluidos: tres consultas, cuatro islas revisadas y cero visitas a esas islas.

## Qué falta y quién debe hacerlo

1. **Completar la evaluación humana.** Abran `data/evaluacion/cuadernillo.html`, sigan `docs/evaluacion/anotar.md` y descarguen un CSV por integrante. Guárdenlos en `data/evaluacion/calificaciones/` y ejecuten `python -m evaluacion.informe`. No mezclen calificaciones de kits con huellas distintas. Sin esas planillas no se puede decir si los viajes propuestos gustan más que la línea de base.
2. **Probar la usabilidad.** El equipo debe invitar a cinco personas ajenas al grupo, completar las plantillas de `data/evaluacion/usabilidad/` y resumir dónde se trabaron. No se deben inventar participantes ni resultados.
3. **Resolver Puno con evidencia.** Revisar primero Uros: su ruta de bote existe en los datos. Confirmar, si es posible, salidas y regresos con una fuente; preguntar en la prueba de usuarios si esperan un día en el lago. Después comparar una variante del ranking con el actual. El trayecto de Tikonata marca cero kilómetros en bote y requiere revisión antes de recomendarlo.
4. **Preparar la presentación final.** Mostrar una consulta completa, un viaje guardado y una limitación que sigue abierta, como el tiempo de traslado de un viaje corto. Es importante distinguir la estimación del motor de un horario o precio confirmado.

Los horarios de buses y vuelos, los cierres de lugares, las tarifas de 2026, el despliegue AWS y la persistencia de eventos publicados siguen pendientes según el avance del propio equipo. Este paquete no los presenta como resueltos.

# Consulta y comparación de viajes

Esta copia parte de la entrega `DreemGO_tableros_y_consultas.zip` del 11 de noviembre de 2026.
El ZIP original, el repositorio del equipo y sus archivos en Drive no se modificaron.

## Qué se mejoró

| Parte | Cambio | Para qué sirve |
|---|---|---|
| Ayuda | `app/src/ayuda/recomendacion.ts` interpreta únicamente campos que ya admite el formulario. `app/src/piezas/AyudaViaje.tsx` consulta `GET /v1/viajes` y muestra rutas, banda de costo, motivos, avisos y enlaces. | Pedir una recomendación concreta sin abandonar la página. El motor existente sigue decidiendo. |
| Resultados | `app/src/piezas/CompararViajes.tsx` presenta hasta tres rutas lado a lado, usando la respuesta del API. | Comparar puntaje interno, costo P50/P80 y horas de ida antes de abrir el itinerario. |
| Motor | `dreemgo/motor/viaje.py` prioriza itinerarios que contienen alguna parada del interés diurno pedido cuando el destino está abierto y existen coincidencias. Conserva la fórmula y la escala del puntaje. | Evitar que una ruta sin playas quede por delante de rutas con playas al pedir playa. |
| Navegación | `app/src/estado/navegacion.ts` y `app/src/piezas/Enlace.tsx` solo retroceden en el historial cuando la página anterior coincide con el enlace «volver». | «Tus viajes» lleva a la lista de la consulta incluso si se abrió el detalle desde la portada o la ayuda. |
| Dependencias de prueba | `app/package.json` y `app/package-lock.json` fijan `playwright-core` a la versión de `@playwright/test`. | Evitar tipos incompatibles al revisar las pruebas de accesibilidad. |

Se conservaron el diseño rojo y dorado, las fotografías y créditos del equipo, el formulario, las tarjetas, el plan diario, la lógica de clima y costos, las preguntas frecuentes, el buzón y los dos tableros existentes.

## Cómo comprobarlo

1. Ejecutar el API y la web con las instrucciones de `00_COMIENZA_AQUI.txt`.
2. Abrir «¿Te ayudamos?» y escribir «Quiero playa desde Lima en julio, 4 días». La ayuda envía al API los campos reconocidos, nunca el texto completo a la analítica. Debe ofrecer rutas con paradas de playa, costos y enlaces.
3. Abrir una ruta desde la ayuda y pulsar «Tus viajes». En la lista aparece «Compara antes de elegir» encima de las tarjetas originales.
4. Probar un destino fijado en Planear: el motor debe conservarlo aunque no cubra un interés y explicar la limitación en un aviso.
5. Abrir `/#/indicadores` para la simulación de 200 sesiones o la actividad consentida. Abrir `/tablero-negocio.html` para el escenario comercial fijo de 300 perfiles; las compras de ese tablero no son reales.

## Límites que deben explicarse

- La ayuda reconoce origen, mes, días, presupuesto e intereses del catálogo. Para fijar un destino concreto se usa el formulario. No es un modelo de lenguaje generativo ni una reserva.
- Si alguna ruta planificada cubre un interés pedido, las rutas sin ninguna coincidencia quedan fuera de esa búsqueda y pueden aparecer menos de tres propuestas. Si no hay coincidencias, se conserva el comportamiento anterior y sus avisos.
- Los costos y tiempos son estimaciones. El puntaje solo ordena rutas de la misma consulta; no es una probabilidad.
- Los escenarios de 200 y 300 sesiones son distintos. Sus destinos A/B se tomaron del ranking guardado en el kit de evaluación, antes de la nueva regla de intereses. El orden cambia en 3 de las 40 consultas del kit, así que el escenario no reproduce exactamente esas respuestas actuales. Se conservó el kit para no alterar las evaluaciones del equipo. El tablero de 300 reproduce compras ficticias y no crece con visitas reales. La actividad consentida se consulta en el panel de indicadores cada tres segundos cuando está visible.
- Los enlaces publicados por el equipo y su GitHub mantienen la versión previa hasta que el propio equipo decida integrar esta copia.

## Verificación de esta copia

- `npm ci`: instalación limpia del frontend.
- `npm test`: 304 pruebas de React aprobadas.
- `npm run build`: compilación de producción aprobada.
- `npm run revisar`: formato, tipos de la app y tipos de herramientas aprobados.
- `pytest tests -q`: 1 060 pruebas del motor, API, datos y simuladores aprobadas.
- Pruebas del tablero comercial: 19 comprobaciones aprobadas.
- Recorrido visual local: consulta desde la ayuda, apertura de itinerario, comparación y tablero de indicadores comprobados en el navegador.

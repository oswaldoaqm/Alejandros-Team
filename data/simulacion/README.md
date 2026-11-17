# Datos para practicar con el dashboard

El ejemplo inicial contiene **200 usuarios ficticios, una sesión por usuario, 932 acciones y 28 días completos**. Periodo: 14 de octubre al 10 de noviembre de 2026, hora de Perú. Es una simulación; no es tráfico real ni una prueba de 200 personas simultáneas.

- `actividad_200.json`: metadatos, supuestos, eventos y resumen por usuario.
- `actividad_200.csv`: una fila por acción, separador `;`, UTF-8 con BOM.
- `usuarios_200.csv`: una fila por usuario ficticio, sin datos personales.
- `actividad_300.json` y `actividad_300.csv`: ejemplo anterior conservado como historial. El panel no lo suma al nuevo.

La copia que lee la API está en `dreemgo/datos/actividad_200_simulacion.json`. Es idéntica al JSON de esta carpeta. Las consultas y los destinos proceden del kit del equipo; las decisiones de uso, errores, respuestas vacías y tiempos son escenarios inventados y documentados.

Para regenerar el ejemplo de 200 desde la raíz:

```powershell
.\.venv\Scripts\python.exe -m evaluacion.simular_actividad --sesiones 200 --semilla 42 --fecha-base 2026-11-10 --dias-historia 28
```

Este comando actualiza los cuatro archivos de 200 y no modifica SQLite ni los archivos anteriores de 300. Una celda vacía significa ausencia del dato, no cero. Los campos `mes` y `dias` describen el viaje solicitado, mientras que `instante` describe el momento de uso de la aplicación.

El [manual de la simulación](../../docs/SIMULACION_200.md) explica el diccionario, las probabilidades, las cifras esperadas y un ejercicio sencillo para el equipo. No hay compras, reservas, ingresos o ganancias porque esos procesos no existen en el alcance actual de DreemGO.

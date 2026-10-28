# La evaluación de la semana 12

Lo que califica el equipo, lo que sale de esas calificaciones y lo que se mide sin ellas ([decisión 0021](../../docs/decisiones/0021-evaluacion-semana-12.md)). Todo lo de aquí se arma con un script y no lleva datos de nadie: ni nombres, ni correos, ni teléfonos.

| Archivo | Qué es | De dónde sale |
|---|---|---|
| `cuadernillo.html` | Las 40 consultas con sus 185 viajes, para calificar en el navegador. Guarda el avance y descarga las calificaciones en un CSV | `python -m evaluacion.kit` |
| `planilla.csv` | Las mismas filas, para calificar en una hoja de cálculo | `python -m evaluacion.kit` |
| `clave.csv` | De dónde sale cada viaje: el puesto que le dan el motor, la guía y la variante. **Quien califica no la abre** | `python -m evaluacion.kit` |
| `calificaciones/` | Las calificaciones de cada quien, una planilla por persona con sus iniciales como nombre (`AB.csv`) | El cuadernillo, al descargar |
| `resultados/notas.csv`, `metricas.csv` y `resumen.json` | Cada viaje con sus notas, las métricas por consulta y el resumen | `python -m evaluacion.informe` |
| `resultados/optimo.csv` y `optimo.json` | Lo que junta la heurística del itinerario contra el óptimo exacto, en los 120 viajes que propone el motor | `python -m evaluacion.optimo`, unos 10 minutos |
| `resultados/buses.csv` y `buses.json` | Los tiempos por tierra del motor contra los de Cruz del Sur, en 29 rutas | `python -m evaluacion.buses` |
| `resultados/presupuesto.csv` y `presupuesto.json` | Qué cambia si el presupuesto deja fuera lo que no cabe en el P50 o en el P80 | `python -m evaluacion.presupuesto`, unos 5 minutos |
| `resultados/usabilidad.json` | El SUS y las tareas de la prueba de usabilidad | `python -m evaluacion.usabilidad` |
| `resultados/zonas.json` | Qué zonas propone cada sistema en las 40 consultas y en cuántas coinciden | `python -m evaluacion.zonas` |
| `resultados/polos_en_horas.json`, `polos_v2_horas.csv` y `polos_v3.csv` | TA-01 con las horas de la red: cuánto mide cada grupo de la v2 y la v3 con cada umbral, contra la v2 | `python -m evaluacion.polos_en_horas`, unos 4 minutos, con la red que arma `pipeline.tiempos` |
| `usabilidad/` | Lo que se anota en la prueba de usabilidad: participantes, tareas, el SUS y los comentarios, con un código por persona | A mano ([`usabilidad.md`](../../docs/evaluacion/usabilidad.md)) |

El kit es de los datos `2026.10.8` y del contrato 1.7, y su huella está en `clave.csv`: si el motor o los datos cambian, `python -m evaluacion.kit` da otro kit, y las calificaciones de este siguen valiendo para esta versión. Cómo se califica está en [`anotar.md`](../../docs/evaluacion/anotar.md).

Lo que no depende de las calificaciones sale de los datos `2026.10.8` y se rehace igual, salvo los segundos que tarda cada búsqueda exacta, que cambian de una corrida a otra. Los grupos en horas dependen además de la red vial armada del extracto de OpenStreetMap del 30 de septiembre, que queda fuera de git.

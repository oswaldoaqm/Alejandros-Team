# Las islas de Puno: diagnóstico para continuar

Con los datos `2026.11.5` los Uros ya aparecen en los tres casos: la [decisión 0028](../docs/decisiones/0028-horarios-y-visitas-corregidos.md) les dio el valor de la Reserva Nacional del Titicaca, que se visita a través de ellos, y 90 minutos de visita, y `data/evaluacion/resultados/islas_puno.json` es la corrida con esos datos. Taquile, Amantaní y Tikonata siguen sin entrar. Lo que sigue es el diagnóstico del profesor con los datos `2026.11.1`.

El avance del 10 de noviembre señala que el viaje a Puno todavía no incluye las islas del Titicaca. Los lugares **sí figuran en el inventario y en los artefactos del motor**: Amantaní (código 958), Taquile (959), Uros (960) y Tikonata (13550). La ausencia está en la selección del itinerario.

Se puede repetir la comprobación, sin descargar datos ni cambiar el producto:

```bash
python -m evaluacion.islas_puno > data/evaluacion/resultados/islas_puno.json
```

Con la versión de datos `2026.11.1`, el resultado fue este. Se probaron tres viajes desde Lima a Puno en julio: cuatro días sin intereses, cuatro días con naturaleza y cinco días con caminatas y gastronomía. Ninguno incluyó las cuatro islas. En el primer caso, Uros quedó en el puesto 57 de la preselección de 40 lugares; con naturaleza subió al 29, pero el planificador tampoco la eligió. Aumentar temporalmente el límite a 80 en una prueba local no cambió la selección. El problema no se arregla simplemente ampliando el límite.

| Lugar | Minutos desde la base de Puno según el motor | Km en bote registrados desde la base |
|---|---:|---:|
| Islas Flotantes de los Uros | 56,2 | 5,0 |
| Isla Taquile | 152,8 | 36,7 |
| Isla Amantaní | 177,7 | 39,1 |
| Isla Tikonata | 96,3 | 0,0 |

Estas cifras son **estimaciones del motor**, no horarios de una empresa de botes. Tikonata tiene cero kilómetros en bote en el artefacto actual; hay que revisar ese trayecto antes de recomendarla. Tampoco contamos con frecuencia, salida, regreso o disponibilidad de embarcaciones. Dar más puntos a una isla o imponerla como visita sin confirmar esos datos haría que la app parezca más completa, pero podría producir un viaje impracticable.

## Qué puede hacer el equipo

1. Elegir **Uros** como primer caso de revisión: ya tiene ruta en bote y, al pedir naturaleza, entra en las 40 candidatas. Anotar una fuente verificable de horarios de ida y regreso, si se consigue; si no, mantener el aviso de que el horario no está confirmado.
2. Probar con personas ajenas al equipo si, al elegir Puno, esperan un día en el lago aun cuando haya menos paradas. Registrar sus respuestas en las planillas de usabilidad existentes.
3. Solo después de esas dos comprobaciones, ajustar la selección como **variante** y compararla con la versión actual usando el mismo caso y las pruebas del contrato. Mantener la versión original hasta que la variante pase las pruebas y tenga una razón explicable.

Así la mejora continúa el trabajo del equipo sin cambiar a ciegas el valor de los lugares ni inventar una ruta de bote.

# Evidencia de las pruebas

Las mismas revisiones de la CI, más las mil consultas al azar de las propiedades del contrato, que la CI corre con cien. Corrieron la noche del 27 de octubre en un clon de prueba, en Linux, con el código del commit «docs(week10): las erratas despues del 25 de octubre» de esta entrega. `00_entorno.txt` anota el árbol de ese clon, `cbcdfd94`. En GitHub el mismo commit tiene otro árbol, porque allí ocho CSV de las semanas 6 y 7 guardan fines de línea de Windows; es la única diferencia, y ni las pruebas ni la app leen esos archivos. Lo que viene después en la rama solo agrega esta carpeta y el README de la raíz: el código no cambia.

Cada prueba se llama por lo que revisa, así que las listas de `02_pytest.txt` y `06_app_vitest.txt` son también la de los casos de prueba.

| Archivo | Qué revisa | Resultado |
|---|---|---|
| `salidas/00_entorno.txt` | El árbol, la fecha y las versiones de Python, ruff, pytest, hypothesis, Node, npm y Playwright | |
| `salidas/01_ruff.txt` | El estilo y el formato del Python | Sin observaciones |
| `salidas/02_pytest.txt` | Las pruebas del motor, el API, el pipeline y la evaluación, una por línea | 968 pasan |
| `salidas/03_propiedades_1000.txt` | Las catorce propiedades del contrato sobre 1 000 consultas al azar, y lo que publica un municipio sobre 250, con lo que ejercitó cada prueba | Pasan las dos |
| `salidas/04_app_estilo_y_tipos.txt` | Biome y TypeScript, en la app y en sus herramientas | Sin observaciones |
| `salidas/05_app_tipos_del_contrato.txt` | Que los tipos de la app sean los que salen del contrato | Iguales |
| `salidas/06_app_vitest.txt` | Cada pieza de la app, con un API de mentira | 243 pasan |
| `salidas/07_app_construir.txt` | La app compilada, como la publica GitHub Pages | Se construye |
| `salidas/08_humo_app_contra_api.txt` | La app compilada en un navegador, en celular y en escritorio, contra el API de verdad: una consulta, un viaje, «A dónde», publicar un evento, y el analizador de accesibilidad en las nueve pantallas, en claro y en oscuro | 60 pasan |

Las cifras de la evaluación están en [`../resultados/`](../resultados/), y el análisis de dónde falla el motor, en el [informe](../EvaluationReport.md).

## Volver a correrlas

Desde la raíz del repositorio, con el entorno de Python del proyecto (`pip install -e ".[api,dev,pipeline]"`) y `npm ci` hecho en `app/`:

```bash
bash deliveries/week12/pruebas/correr.sh deliveries/week12/pruebas/salidas
```

Unos 35 minutos; las mil consultas de las propiedades se llevan casi 25. Las salidas son `.txt` y no `.log` porque el repositorio ignora los `.log`. La prueba de humo levanta el API y la app si no están corriendo, y necesita el Chromium de Playwright (`npx playwright install chromium`).

Lo que no está aquí: las dos imágenes del API, que la CI construye en cada pull request, arranca, y con las que publica un evento y comprueba que no se pierde. Aquí no hubo Docker.

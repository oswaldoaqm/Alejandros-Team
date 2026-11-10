# 0004 · Sin modelos supervisados: agrupamiento, reglas de clima y optimización

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente

## Contexto

En la semana 6 se propusieron un clasificador de riesgo climático (Random Forest o XGBoost) y un recomendador de comercio local con TF-IDF. El producto arranca sin usuarios: no hay clics, valoraciones ni itinerarios aceptados que aprender.

## Decisión

El motor combina tres métodos que no necesitan etiquetas:

1. **Agrupamiento** (TA-01): enlace completo sobre distancia de viaje, que acota el diámetro de cada polo por construcción.
2. **Estacionalidad** (TA-05): una regla declarada de dos ejes sobre diez años de clima observado de cada polo.
3. **Optimización** (TA-04): orientación por equipos, que elige qué visitar y en qué orden para capturar el mayor valor dentro de la jornada.

## Alternativas descartadas

El detalle está en [`week06/ModelSelection.md` §12](../../deliveries/week06/ModelSelection.md). En corto: la etiqueta del clasificador climático es un umbral fijo sobre la lluvia, así que el modelo solo reaprendería la climatología que TA-05 ya usa. El recomendador de comercio se entrenaría sobre datos simulados y ordenaría por lo que paga cada negocio.

## Consecuencias

- El enunciado lo permite de forma explícita: no se exige un modelo complejo cuando un método más simple es el adecuado.
- La evaluación no puede apoyarse en métricas de clasificación. Se evalúa con cobertura del valor, brecha contra el óptimo exacto, un conjunto de consultas anotado por el equipo con acuerdo medido (kappa de Fleiss) y pruebas de usabilidad (semana 12).
- Si el prototipo genera uso real, una capa supervisada de ordenamiento sobre itinerarios aceptados queda como trabajo futuro, con datos reales.

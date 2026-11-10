# 0003 · El motor carga artefactos precalculados; no hay base relacional

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente

## Contexto

El modelo entidad-relación de la Delivery 1 ponía recursos, polos y clima en Amazon RDS. Esos datos no cambian cuando alguien usa la app: cambian cuando el equipo recalcula el modelo o cuando una fuente publica una versión nueva. La consulta de la semana 6 tardaba 2,5 s porque leía los CSV en cada llamada.

## Decisión

El pipeline (`pipeline/`) genera **artefactos versionados**: recursos con su ficha, polos, clima por polo y mes, tiempos de viaje y equivalencias de intereses. El motor los carga una vez al arrancar y responde desde memoria. Cada respuesta dice con qué `version_datos` se calculó. Solo los eventos que publican los municipios, que sí cambian con el uso, van a DynamoDB.

## Alternativas descartadas

- **RDS**: sin capa gratuita permanente, y una base relacional para datos de solo lectura suma latencia y operación.
- **Leer los CSV en cada consulta**, como en la semana 6: 2,5 s por respuesta.

## Consecuencias

- Los artefactos entran a la imagen del contenedor y al repositorio; tienen que ser pequeños (meta: menos de 30 MB).
- Reproducir el producto es correr el pipeline sobre las mismas descargas, que quedan descritas con su fecha y su hash en `data/externos/*/manifiesto.json`.

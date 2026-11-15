# 0032 · El techo del bus con tarifas de 2026, y dónde dormir

**Fecha:** 15 de noviembre de 2026 · **Estado:** vigente · Suma los hospedajes cerca de la base al [contrato](../CONTRATO.md) (versión 1.10), con la propiedad 20, y cierra en parte los puntos 10 y 11 de la [auditoría](../AUDITORIA.md)

## Contexto

La auditoría dejó dos objeciones sobre el dinero y la noche. Ninguna tarifa de transporte, hospedaje o comida estaba calibrada con precios de este año. Y el motor elegía el pueblo donde se duerme, pero no decía dónde.

## Decisión

- El techo del bus sale de la tarifa más baja de Cruz del Sur en sus 18 rutas desde Lima, vista a mano en la página de cada ruta, con la fecha en que la empresa dice haberla verificado, el 27 de octubre de 2026, y una el 19 (`pipeline/referencia/tarifas_bus.csv`). Cruz del Sur es la empresa cara, así que esas tarifas van al máximo de la banda: 84 soles por tramo más 0,10 por km, que las cubre a todas. El valor central y el mínimo quedan como estaban, con las tarifas de las empresas más baratas de la semana 6.
- Cada base lleva hasta tres hospedajes con nombre de OpenStreetMap a 2 km o menos, del más cercano al más lejano (`pipeline/hospedajes.py`). La 1.10 los lleva en `polo.hospedajes`, y la app los muestra junto a dónde se duerme.

## Alternativas descartadas

- Calibrar el valor central con Cruz del Sur: su tarifa más baja es 1,75 veces el central en la mediana de las 18 rutas. Las empresas económicas cobran menos: Lima–Huancayo costaba de 25 a 30 soles antes de la subida de Fiestas Patrias, según RPP el 25 de julio de 2026, contra los 110 de Cruz del Sur.
- Bajar las tarifas con un script: el equipo acordó no hacer scraping de páginas de venta. Las 18 se vieron una por una.
- Una banda de precio por hospedaje: OpenStreetMap no trae la categoría de forma pareja. El directorio de prestadores de MINCETUR sí la trae, pero hay que bajarlo y cruzarlo con OSM, y queda para después de la entrega.
- La seguridad del distrito: no hay una fuente por distrito que se pueda citar con la misma fecha para todo el país.

## Consecuencias

- La banda del costo se abre hacia arriba en los viajes en bus. En el ejemplo del contrato, el viaje a Trujillo pasa de 744 a 783 soles en el P20, de 859 a 906 en el P50 y de 973 a 1 019 en el P80.
- 162 de las 194 bases tienen algún hospedaje con nombre a 2 km o menos, y 115 tienen tres. La mediana de la distancia es 120 metros.
- El hospedaje, la comida y la movilidad local siguen con las cifras de la semana 6, sin calibrar: no hay una fuente de 2026 por zona que se pueda citar.
- La tarifa de Cruz del Sur cambia según la fecha y la anticipación. Si cambia, se cambia en el CSV, y una prueba revisa que la banda la siga cubriendo.

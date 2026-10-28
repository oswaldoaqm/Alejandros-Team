# 0008 · Calibrar la red vial con los recorridos de las fichas

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente · Precisa la calibración de la [0007](./0007-red-vial-propia.md)

## Contexto

La 0007 planeaba calibrar la red contra horarios de bus publicados. Esos horarios cubren unas decenas de pares de ciudades, todos lejanos, y nada de los tramos cortos entre paradas de un polo, que son la mayoría de los traslados. Las fichas oficiales publican cómo se llega a cada recurso: desde qué distrito, cuántos km y cuántos minutos. 2 588 de esos recorridos van enteros por carretera y los escribió quien conoce el lugar.

## Decisión

Se calibra con los 1 780 recorridos en que la red y la ficha dan casi la misma distancia: ritmo por clase de vía, recargos por km sin asfaltar y por curvas, y minutos fijos por traslado. El error se mide por validación cruzada por distrito de partida y se informa por distancia, porque la meta de la 0007 (20 % de error medio) no significa lo mismo en 5 km que en 500.

Resultado: 15 % en los viajes de más de 100 km, que son los traslados desde la ciudad de origen, y 21 % entre 30 y 100 km. En menos de 30 km el error relativo es de 27 a 31 %, pero son 4 a 8 minutos de mediana, en fichas que redondean a 5 o 10. La fórmula anterior se equivocaba en 48 %.

## Alternativas descartadas

- **Horarios de empresas de bus**: pocos pares, y solo largos.
- **Todos los recorridos**: en uno de cada cinco, la ficha pone como partida el distrito del recurso aunque el tramo empiece en otra ciudad.

## Consecuencias

- Las cifras quedan en `data/procesados/red_calibracion.json`, y cada recorrido usado, con su tiempo en la ficha y en la red, en `red_calibracion_recorridos.csv`.
- La calibración se rehace sola con `python -m pipeline.tiempos` si cambian las fichas o el extracto.

# 0007 · Tiempos de viaje sobre un extracto propio de OpenStreetMap

**Fecha:** 30 de septiembre de 2026 · **Estado:** vigente. Su calibración la precisa la [0008](./0008-calibrar-con-las-fichas.md)

## Contexto

Los tiempos de viaje salían de la distancia en línea recta por un factor de sinuosidad de 1,6 que nunca se calibró, a 32,5 km/h. El motor no podía saber qué polos no tienen carretera desde el origen, como los de Iquitos.

## Decisión

Se descarga una vez el extracto del Perú de OpenStreetMap (Geofabrik, verificado por MD5) y se calculan los tiempos por carretera con velocidades por tipo de vía: entre las paradas de cada polo y desde cada una de las 24 ciudades de origen hasta cada polo. El resultado se calibra contra duraciones de bus publicadas; la meta es un error medio de 20 % o menos.

## Alternativas descartadas

- **Servicios públicos de ruteo** (el servidor de demostración de OSRM): sus condiciones no permiten decenas de miles de consultas, y el resultado dependería de un servicio ajeno.
- **Seguir con la fórmula**: no detecta la falta de acceso terrestre y su error no se conoce.

## Consecuencias

- Las tablas de tiempos son obra derivada de OpenStreetMap y se publican bajo ODbL, con su atribución.
- Si la calibración no llega a la meta, se usa la fórmula calibrada y la limitación queda escrita.

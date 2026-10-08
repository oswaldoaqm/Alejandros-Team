# 0009 · El viaje es una estrella desde la base de un polo

**Fecha:** 1 de octubre de 2026 · **Estado:** vigente. La [0013](./0013-un-polo-por-pueblo.md) junta en un polo los grupos que duermen en el mismo pueblo y cambia el valor de una parada, y la [0014](./0014-dia-de-solo-viaje.md) deja que un día de solo viaje llegue a 9 horas

## Contexto

TA-04 (semana 6) armaba los días desde un «punto base» que era el recurso con menor tiempo de acceso de su ficha: un museo o una laguna, no un lugar donde dormir. Con la red vial ya se puede medir cuánto cuesta salir de cada pueblo a cada parada, y OpenStreetMap registra unos 8 000 hoteles, hostales y casas de huéspedes en el Perú. Hacía falta decidir dónde se duerme, cómo se reparten los días y cómo se ordenan los polos.

## Decisión

- **Una base por polo**, un pueblo real de OSM: el que deja las paradas más cerca en minutos por carretera (promedio pesado por jerarquía), con 5 minutos a favor por cada vez que se duplica el hospedaje registrado a menos de 3 km, hasta 25, y un recargo si no hay ninguno ([`pipeline/bases.py`](../../pipeline/bases.py)). Así el polo de Machu Picchu duerme en Machupicchu Pueblo y no en un caserío mejor centrado.
- **El viaje es una estrella:** ida, días de paseo que salen de la base y vuelven, y vuelta. Más de 8 horas de carretera se parten en partes iguales y se duerme a mitad de camino. Ninguna jornada pasa de 8 horas ni de seis paradas.
- **Qué visitar y en qué orden** es orientación por equipos: inserción voraz por valor por minuto, 2-opt y tres arranques, de los que queda el de más valor.
- **El puntaje** es el de la semana 6 con la calidad medida sobre el itinerario y el presupuesto como factor: (1 − λ) · calidad · temporada · presupuesto + λ · novedad, λ = 0,3. La lejanía de la novedad es el tiempo por carretera desde la ciudad de origen de la región del polo.
- **Un viaje sale de su ciudad:** no se duerme a menos de media hora del origen.

## Alternativas descartadas

- **Cambiar de hospedaje cada noche** (un camino abierto): en polos de menos de 80 km de diámetro nadie lo hace, y multiplica las combinaciones.
- **Dormir en la capital de distrito más central**: muchas no registran ningún hospedaje y otras quedan a horas de las paradas que valen más.
- **Resolver el problema exacto** en cada consulta: con 40 candidatas y hasta 14 días no cabe en el segundo de respuesta. La brecha contra el óptimo exacto se mide en la evaluación de la semana 12.

## Consecuencias

- Un viaje recorre un solo polo. Combinar polos vecinos (el Valle Sagrado y Machu Picchu) es trabajo de la fase 4.
- ~~Lo que no se alcanza por carretera queda fuera: las islas del Titicaca, el tren a Machu Picchu, los ríos de la Amazonía. Sumar los botes y el tren que registra OSM es la mejora siguiente de la red.~~ Ya entran: ver la actualización.
- ~~Dos polos pueden compartir base (Huaraz sirve a cuatro); la respuesta no repite base entre sus tres rutas.~~ Ya no: ver la actualización del 7 de octubre.

## Actualización · 1 de octubre de 2026

El tren y los botes entraron a la red ([decisión 0010](./0010-tren-y-botes.md)). La estrella no cambia: se sigue durmiendo en una base y cada día sale un paseo que vuelve a ella, pero la ida, la vuelta o un paseo pueden ir en tren (a Machupicchu Pueblo) o en bote (a Taquile desde Puno). La respuesta dice con qué se viaja (`traslado.medios`, contrato 1.2) y el costo cobra los pasajes. La lejanía de la novedad sigue en la escala de la carretera: vale 1 en el polo más lejano al que se llega sin tren ni bote, y también en los que quedan a días de río.

## Actualización · 7 de octubre de 2026

Los grupos de TA-01 que dormían en el mismo pueblo son ahora un solo polo, y una parada vale 1, 2, 6 o 24 según su jerarquía, en vez de 1, 2, 4 u 8 ([decisión 0013](./0013-un-polo-por-pueblo.md)). Así el motor propone Huaraz, y Machu Picchu desde el Cusco. Un día en el que solo se viaja puede durar 9 horas, y no 8, para que Huaraz quepa desde Lima en cuatro días ([decisión 0014](./0014-dia-de-solo-viaje.md)).

# 0018 · De noche: dónde salir, una noche de estrellas y descansar en la altura

**Fecha:** 18 de octubre de 2026 · **Estado:** vigente · Amplía la [0009](./0009-viaje-en-estrella.md) y suma `vida_nocturna`, `Dia.noche` y la noche de cada zona al [contrato](../CONTRATO.md) (versión 1.5)

## Contexto

El plan terminaba al volver a la base. Quien todavía tiene energía de noche no sabía dónde salir. Quien elige naturaleza no sabía que desde 137 de las 194 bases el cielo es oscuro o muy oscuro. El inventario de MINCETUR no registra bares ni discotecas, y el cielo depende de cosas que no están en ninguna ficha: la luz de las ciudades, las nubes de cada mes y la luna de cada noche.

## Decisión

- **Un interés de noche, `vida_nocturna`**, aparte en el formulario («De noche»). No elige paradas: el día es el mismo con él o sin él. Pesa un poco al elegir la zona: con menos de cinco lugares para salir, el puntaje se multiplica por 0,6 más 0,08 por cada lugar.
- **Qué noches:** las que se duermen en la base, desde el día en que se llega hasta la víspera del día en que se deja.
- **Salir.** Bares, pubs, discotecas, karaokes y peñas a no más de 1,5 km en línea recta de la base, unos 25 minutos a pie ([`pipeline/noche.py`](../../pipeline/noche.py)). Salen de OpenStreetMap y de Overture Maps; de Overture, solo lo de licencia CDLA y con una confianza de al menos 0,7. Cada noche propone hasta tres lugares, de tipos distintos si los hay, y la siguiente, otros tres. Cada uno enlaza a su mapa.
- **Lo que no es de noche se saca por el nombre.** Las reglas salen de revisar a mano los 1 367 lugares de la primera vuelta: Overture tenía un colegio, una sauna, una cancha, una catarata, direcciones y pollerías marcadas como bar. Lo que nunca es de noche sale de las dos fuentes. Lo que solo es dudoso, como un nombre de restaurante o de un sitio, sale de Overture si no dice nada de la noche; lo de OSM queda, porque una persona lo marcó como bar.
- **Descanso**, con `vida_nocturna`: la primera noche en una base de 2 500 m o más, si se llega desde al menos 1 000 m más abajo. El alcohol empeora el soroche.
- **Estrellas**, con `naturaleza` o sin ningún interés: una noche por viaje. Puede ser:
  - desde la base, si su cielo es oscuro (brillo artificial menor que 2, con la escala de abajo);
  - si no, en un observatorio o un planetario a menos de 45 minutos.

  No se propone en un mes en que no sale despejada ni una de cada cinco noches. Con fecha, toca la noche con más horas sin luna; sin fecha, la segunda en la base.
- **El cielo** ([`pipeline/cielo.py`](../../pipeline/cielo.py)). El brillo sale de las luces que ve el satélite VIIRS, con el modelo de Duriscoe et al. (2018) y las clases del Servicio de Parques Nacionales de EE. UU. Las noches despejadas salen de la máscara de nubes de GOES-16, a las 21:00 y a la 01:00, de 2022 a 2024. En la costa se usan los METAR del aeropuerto costero más cercano, si queda a menos de 150 km. La luna, la hora en que oscurece y las lunas nuevas se calculan en [`dreemgo/astronomia.py`](../../dreemgo/astronomia.py), sin dependencias.

## Alternativas descartadas

- **Solo OpenStreetMap.** Solo 62 de las 194 zonas tenían algún lugar para salir. Con Overture tienen 92.
- **Lo de Foursquare en Overture.** Viene con Apache 2.0, una licencia de software. Sin él, los datos de la noche llevan solo ODbL y CDLA.
- **GOES también en la costa.** Contra los METAR, la correlación mes a mes es negativa en Lima (−0,81), Pisco (−0,52) y Tacna (−0,67). De noche, el satélite no ve la neblina baja del invierno. En la sierra y la selva coincide: 0,98 en el Cusco y 0,96 en Arequipa.
- **Proponer el mirador más oscuro.** Un cerro de noche, lejos y sin nadie, no es un plan que la app deba armar sola. Por ejemplo, el Mirador Churup queda a 43 minutos de Huaraz, y Playa Mendieta, dentro de la reserva de Paracas. La página de la zona lo muestra como dato, con «mejor con un tour o un taxi que espere».

## Consecuencias

- **Lugares para salir:** 1 264 (443 de OSM, 821 de Overture), en 92 zonas; 50 tienen cinco o más.
- **El cielo desde la base:** muy oscuro en 48, oscuro en 89 y con luz en 57.
- **Observatorios y planetarios:** 12 bases tienen uno a menos de 45 minutos.
- **Noches despejadas:** salen de GOES en 151 zonas y de un aeropuerto en 32. En 11 no hay dato, y la app lo dice; Nasca es una de ellas.
- La noche se calcula solo para las rutas elegidas: la mediana de una consulta sigue en unos 330 ms.
- Nada de la noche cambia el día: la propiedad 11 lo verifica con y sin `vida_nocturna`.
- **Lo que todavía falla.** Se escapan nombres que son de un sitio, como «Huaytapallana», un nevado. Por eso, un lugar que solo está en Overture y cuyo nombre no dice nada de la noche va al final: se cuenta, pero se nombra solo si no hay otro. Un bar puede haber cerrado, y no se sabe qué noches abre. El horario de OSM viaja en el contrato, pero la app todavía no lo muestra. El modelo de brillo no corrige la altura: en el altiplano, el cielo suele ser más oscuro de lo que dice.
- **Datos nuevos.** Los bajan cuatro scripts de [`pipeline/adquisicion/`](../../pipeline/adquisicion/), y lo crudo no va a git ([`DATA_LICENSES.md`](../../DATA_LICENSES.md)):
  - Overture, bajo CDLA Permissive 2.0, con atribución;
  - VIIRS del Earth Observation Group, de dominio público, con la cita que pide la copia del Banco Mundial;
  - GOES-16, de NOAA, de dominio público;
  - los METAR de NOAA. Los de estaciones fuera de Estados Unidos no se redistribuyen (Resolución 40 de la OMM): el repositorio guarda solo la parte de noches despejadas de cada mes, calculada aquí.

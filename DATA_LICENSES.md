# Licencias de los datos

El código de este repositorio es MIT ([`LICENSE`](./LICENSE)). Los datos tienen la licencia de su fuente, y la app muestra la atribución de cada una junto al resultado.

| Fuente | Qué usamos | Licencia | Qué exige |
|---|---|---|---|
| [Inventario Nacional de Recursos Turísticos](https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos), MINCETUR | El CSV de datos abiertos y la ficha oficial de cada recurso: jerarquía, ingreso, tarifa, actividades, accesos, descripción | [ODC-BY 1.0](https://opendatacommons.org/licenses/by/1-0/) | Atribución |
| [Open-Meteo](https://open-meteo.com/), sobre los reanálisis ERA5 y ERA5-Land del Copernicus Climate Change Service | Clima diario 2016-2025 en cada polo; climatología mensual 2014-2023 por región | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Atribución. La API gratuita es solo para uso no comercial, como este proyecto |
| [OpenStreetMap](https://www.openstreetmap.org/copyright), extracto del Perú de [Geofabrik](https://download.geofabrik.de/south-america/peru.html) | La red de vías, trenes de pasajeros y botes, para calcular tiempos de viaje; los pueblos y los hospedajes que registra, para elegir dónde se duerme en cada polo; los lugares para salir y, desde la versión `2026.10.7`, dónde están los restaurantes, cafés y locales de comida rápida | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | Atribución, y que las bases de datos derivadas se compartan con la misma licencia |
| [Overture Maps](https://overturemaps.org/), tema *places*, versión 2026-09-23.1 | Los bares, pubs, discotecas, karaokes y peñas a no más de 1,5 km de cada base: su nombre, su categoría, su confianza y su ubicación. Desde la versión `2026.10.7`, también dónde hay restaurantes, cafés y comida rápida, sin sus nombres: solo su ubicación, para contar cuántos hay cerca de cada lugar. Solo de las fuentes con licencia CDLA, que son Meta y Microsoft. Nunca sus teléfonos, correos, páginas ni redes | [CDLA Permissive 2.0](https://cdla.dev/permissive-2-0/) | Atribución. Lo que Overture trae de Foursquare, con Apache 2.0, no se usa |
| [VIIRS DNB](https://eogdata.mines.edu/products/vnl/), compuestos mensuales del Earth Observation Group (Colorado School of Mines), de la copia [«Light Every Night»](https://registry.opendata.aws/wb-light-every-night/) del Banco Mundial en AWS | Las luces nocturnas de 17 meses (2024 a junio de 2025, sin octubre de 2024), para estimar cuánta luz artificial tiene el cielo de cada base | Dominio público, según el Earth Observation Group: no tienen derechos de autor ni restricciones de uso. El Banco Mundial lista su copia con su licencia de bases de datos y enlaza a CC BY 4.0 | Por los datos, ninguna. El Banco Mundial pide citar su copia («World Bank - Light Every Night was accessed on 2026-10-18 from https://registry.opendata.aws/wb-light-every-night»): con la cita se cumplen las dos |
| [GOES-16](https://registry.opendata.aws/noaa-goes/), máscara de nubes de disco completo (ABI-L2-ACMF), NOAA | Si el cielo estaba despejado a las 21:00 y a la 01:00 de cada noche de 2022 a 2024, en la ventana del Perú | Dominio público, en el programa de datos abiertos de NOAA | NOAA pide atribución, que no se dé a entender que respalda el proyecto y que un dato modificado no se presente como suyo |
| [Integrated Surface Database](https://registry.opendata.aws/noaa-isd/) (Global Hourly), NOAA | Los METAR de los aeropuertos peruanos de 2022 a 2024, para las noches despejadas de la costa | Abiertos en el programa de datos abiertos de NOAA. Los de estaciones fuera de Estados Unidos, como estos, están sujetos a la Resolución 40 de la OMM, y NOAA advierte que no se redistribuyan | Atribución, y no redistribuir los datos. El repositorio no los guarda: publica, por aeropuerto y por polo, solo la parte de las noches de cada mes que salió despejada, calculada aquí y con su fuente |
| [Wikimedia Commons](https://commons.wikimedia.org/), elegidas con [Wikidata](https://www.wikidata.org/) | Una foto para cada lugar y cada pueblo donde se duerme, cuando la hay: el nombre del archivo, su autor, su licencia y su tamaño. Las fotos no se guardan: la app las pide a Wikimedia del tamaño que necesita | La de cada foto: [CC BY](https://creativecommons.org/licenses/by/4.0/), [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/), [CC0](https://creativecommons.org/publicdomain/zero/1.0/) o dominio público; las demás no se usan. Wikidata es [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | Mostrar el autor y la licencia junto a cada foto, con enlace a su página y a la licencia. CC BY-SA pide además compartir igual las versiones modificadas: las fotos se muestran sin modificar, solo achicadas |

## Atribución que se muestra

- Inventario Nacional de Recursos Turísticos · Ministerio de Comercio Exterior y Turismo del Perú · ODC-BY
- Datos de clima: [Open-Meteo.com](https://open-meteo.com/), con información modificada del Copernicus Climate Change Service · CC BY 4.0
- © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright)
- Lugares para salir y para comer: Overture Maps Foundation, con datos de Meta y Microsoft · CDLA Permissive 2.0
- Luces nocturnas: VIIRS, Earth Observation Group, Colorado School of Mines · dominio público; copia «Light Every Night» del Banco Mundial
- Nubes de noche: GOES-16 y METAR de los aeropuertos, NOAA
- Cada foto, con «Foto: autor, licencia», enlazada a su página en Wikimedia Commons y a su licencia

## Obras derivadas

- **Tiempos de viaje y bases** (`tiempos_*.csv`, `red_paradas.csv` y `polos_bases.csv` en `data/procesados/`): se calculan sobre OpenStreetMap, así que se publican bajo **ODbL 1.0**, con la atribución de arriba.
- **Clima por polo** (`clima_polo_mes.csv`): promedios de Open-Meteo, bajo **CC BY 4.0**.
- **Lugares para salir** (`noche_lugares.csv`): juntan OpenStreetMap y Overture. Como base de datos derivada de OpenStreetMap se publican bajo **ODbL 1.0**; lo que viene de Overture lleva además su aviso de CDLA Permissive 2.0, que permite combinarlo así.
- **Dónde comer cerca** (`comida_cerca.csv`): por cada lugar del inventario y cada base, cuántos restaurantes, cafés y locales de comida rápida registra cada fuente a menos de 1,5 km y a cuántos metros queda el más cercano. No trae ningún nombre ni ninguna ubicación de esos locales. Como sale en parte de OpenStreetMap, va bajo **ODbL 1.0**, con el aviso de CDLA Permissive 2.0 por lo de Overture.
- **El cielo de cada polo** (`cielo_polos.csv` y `cielo_validacion.csv`): el brillo del cielo (de VIIRS), la parte de noches despejadas de cada mes (de GOES-16 o de los METAR) y el mirador, observatorio o planetario más cercano, con sus minutos por la red. Por esto último, que sale de OpenStreetMap, se publican bajo **ODbL 1.0**, con la atribución de VIIRS y de NOAA. No traen ningún dato crudo de NOAA.
- **Lista de fotos** (`app/public/fotos.json`): el archivo, el autor y la licencia de cada foto elegida, tal como los publica Wikimedia Commons, y el elemento de Wikidata (CC0) que la llevó a ese lugar, salvo en las que se pusieron a mano. No contiene ninguna foto.
- **Artefactos del motor** (`dreemgo/datos/`), que combinan todas estas fuentes: llevan la atribución de cada una, y la parte que viene de OpenStreetMap queda bajo ODbL. El manifiesto lista la atribución y cada respuesta del API la repite en `atribucion`.

## Datos personales

Las fichas oficiales publican el nombre, el correo y el teléfono de quien las llenó y, en el texto libre, los de quien atiende cada lugar. El pipeline no lee las secciones "Datos del Responsable" ni "Saneamiento Físico Legal", y en el resto del texto reemplaza teléfonos, correos y el nombre de quien atiende (ver [`pipeline/README.md`](./pipeline/README.md#datos-personales)). Nada de eso llega a los artefactos ni al repositorio. Las fichas de prueba de `tests/fixtures/fichas/` están saneadas con el mismo criterio, y la tabla de fichas de las semanas 6 y 7 se pasó por el mismo filtro el 2 de octubre ([erratas de la semana 6](./deliveries/week06/ERRATA.md)).

## Lo que no se usa

TripAdvisor y Google Places se evaluaron en la semana 4 y se descartaron: sus términos prohíben la extracción automatizada o restringen el almacenamiento y la redistribución. Ningún dato de esas fuentes está en el repositorio.

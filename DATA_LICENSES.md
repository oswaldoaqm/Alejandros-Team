# Licencias de los datos

El código de este repositorio es MIT ([`LICENSE`](./LICENSE)). Los datos tienen la licencia de su fuente, y la app muestra la atribución de cada una junto al resultado.

| Fuente | Qué usamos | Licencia | Qué exige |
|---|---|---|---|
| [Inventario Nacional de Recursos Turísticos](https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos), MINCETUR | El CSV de datos abiertos y la ficha oficial de cada recurso: jerarquía, ingreso, tarifa, actividades, accesos, descripción | [ODC-BY 1.0](https://opendatacommons.org/licenses/by/1-0/) | Atribución |
| [Open-Meteo](https://open-meteo.com/), sobre los reanálisis ERA5 y ERA5-Land del Copernicus Climate Change Service | Clima diario 2016-2025 en cada polo; climatología mensual 2014-2023 por región | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Atribución. La API gratuita es solo para uso no comercial, como este proyecto |
| [OpenStreetMap](https://www.openstreetmap.org/copyright), extracto del Perú de [Geofabrik](https://download.geofabrik.de/south-america/peru.html) | La red de vías, trenes de pasajeros y botes, para calcular tiempos de viaje; los pueblos y los hospedajes que registra, para elegir dónde se duerme en cada polo | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | Atribución, y que las bases de datos derivadas se compartan con la misma licencia |
| [Wikimedia Commons](https://commons.wikimedia.org/), elegidas con [Wikidata](https://www.wikidata.org/) | Una foto para cada lugar y cada pueblo donde se duerme, cuando la hay: el nombre del archivo, su autor, su licencia y su tamaño. Las fotos no se guardan: la app las pide a Wikimedia del tamaño que necesita | La de cada foto: [CC BY](https://creativecommons.org/licenses/by/4.0/), [CC BY-SA](https://creativecommons.org/licenses/by-sa/4.0/), [CC0](https://creativecommons.org/publicdomain/zero/1.0/) o dominio público; las demás no se usan. Wikidata es [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | Mostrar el autor y la licencia junto a cada foto, con enlace a su página y a la licencia. CC BY-SA pide además compartir igual las versiones modificadas: las fotos se muestran sin modificar, solo achicadas |

## Atribución que se muestra

- Inventario Nacional de Recursos Turísticos · Ministerio de Comercio Exterior y Turismo del Perú · ODC-BY
- Datos de clima: [Open-Meteo.com](https://open-meteo.com/), con información modificada del Copernicus Climate Change Service · CC BY 4.0
- © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright)
- Cada foto, con «Foto: autor, licencia», enlazada a su página en Wikimedia Commons y a su licencia

## Obras derivadas

- **Tiempos de viaje y bases** (`tiempos_*.csv`, `red_paradas.csv` y `polos_bases.csv` en `data/procesados/`): se calculan sobre OpenStreetMap, así que se publican bajo **ODbL 1.0**, con la atribución de arriba.
- **Clima por polo** (`clima_polo_mes.csv`): promedios de Open-Meteo, bajo **CC BY 4.0**.
- **Lista de fotos** (`app/public/fotos.json`): el archivo, el autor y la licencia de cada foto elegida, tal como los publica Wikimedia Commons, y el elemento de Wikidata (CC0) que la llevó a ese lugar, salvo en las que se pusieron a mano. No contiene ninguna foto.
- **Artefactos del motor** (`dreemgo/datos/`), que combinan las tres fuentes: llevan la atribución de las tres, y la parte que viene de OpenStreetMap queda bajo ODbL. El manifiesto lista la atribución y cada respuesta del API la repite en `atribucion`.

## Datos personales

Las fichas oficiales publican el nombre, el correo y el teléfono de quien las llenó y, en el texto libre, los de quien atiende cada lugar. El pipeline no lee las secciones "Datos del Responsable" ni "Saneamiento Físico Legal", y en el resto del texto reemplaza teléfonos, correos y el nombre de quien atiende (ver [`pipeline/README.md`](./pipeline/README.md#datos-personales)). Nada de eso llega a los artefactos ni al repositorio. Las fichas de prueba de `tests/fixtures/fichas/` están saneadas con el mismo criterio, y la tabla de fichas de las semanas 6 y 7 se pasó por el mismo filtro el 2 de octubre ([erratas de la semana 6](./deliveries/week06/ERRATA.md)).

## Lo que no se usa

TripAdvisor y Google Places se evaluaron en la semana 4 y se descartaron: sus términos prohíben la extracción automatizada o restringen el almacenamiento y la redistribución. Ningún dato de esas fuentes está en el repositorio.

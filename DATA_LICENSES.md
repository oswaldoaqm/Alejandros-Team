# Licencias de los datos

El código de este repositorio es MIT ([`LICENSE`](./LICENSE)). Los datos tienen la licencia de su fuente, y la app muestra la atribución de cada una junto al resultado.

| Fuente | Qué usamos | Licencia | Qué exige |
|---|---|---|---|
| [Inventario Nacional de Recursos Turísticos](https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos), MINCETUR | El CSV de datos abiertos y la ficha oficial de cada recurso: jerarquía, ingreso, tarifa, actividades, accesos, descripción | [ODC-BY 1.0](https://opendatacommons.org/licenses/by/1-0/) | Atribución |
| [Open-Meteo](https://open-meteo.com/), sobre los reanálisis ERA5 y ERA5-Land del Copernicus Climate Change Service | Clima diario 2016-2025 en cada polo; climatología mensual 2014-2023 por región | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) | Atribución. La API gratuita es solo para uso no comercial, como este proyecto |
| [OpenStreetMap](https://www.openstreetmap.org/copyright), extracto del Perú de [Geofabrik](https://download.geofabrik.de/south-america/peru.html) | La red vial, para calcular tiempos de viaje por carretera | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | Atribución, y que las bases de datos derivadas se compartan con la misma licencia |

## Atribución que se muestra

- Inventario Nacional de Recursos Turísticos · Ministerio de Comercio Exterior y Turismo del Perú · ODC-BY
- Datos de clima: [Open-Meteo.com](https://open-meteo.com/), con información modificada del Copernicus Climate Change Service · CC BY 4.0
- © colaboradores de [OpenStreetMap](https://www.openstreetmap.org/copyright)

## Obras derivadas

- **Tiempos de viaje** (entre paradas de un polo y desde cada ciudad de origen a cada polo): se calculan sobre OpenStreetMap, así que se publican bajo **ODbL 1.0**, con la atribución de arriba.
- **Artefactos del motor** que combinan el inventario con el clima (polos, estacionalidad, puntajes): conservan la atribución de ambas fuentes.

## Datos personales

Las fichas oficiales publican el nombre, el correo y el teléfono de quien las llenó, y a veces el celular de un encargado en el texto libre. El pipeline no lee las secciones "Datos del Responsable" ni "Saneamiento Físico Legal", y en el resto del texto reemplaza teléfonos, correos y el nombre pegado a ellos (ver [`pipeline/README.md`](./pipeline/README.md#datos-personales)). Nada de eso llega a los artefactos ni al repositorio; las fichas de prueba en `tests/fixtures/fichas/` están saneadas con el mismo criterio.

## Lo que no se usa

TripAdvisor y Google Places se evaluaron en la semana 4 y se descartaron: sus términos prohíben la extracción automatizada o restringen el almacenamiento y la redistribución. Ningún dato de esas fuentes está en el repositorio.

# Datos procesados

Lo que construye el pipeline a partir de las descargas de `data/externos/` (fuera de git). Se regenera con:

```bash
python -m pipeline.maestro
python -m pipeline.eventos
python -m pipeline.tiempos     # necesita el extracto de OpenStreetMap (pipeline/adquisicion)
python -m pipeline.clima       # necesita el clima descargado (pipeline/adquisicion)
```

`python -m pipeline.artefactos` junta después estas tablas en lo que carga el motor, en [`dreemgo/datos/`](../../dreemgo/datos/).

| Archivo | Qué es |
|---|---|
| `maestro_v3.csv` | Una fila por recurso del inventario, con lo que dice su ficha oficial, su polo y las marcas de calidad. Separador `;`, UTF-8 con BOM para que Excel muestre bien las tildes (en pandas: `encoding="utf-8-sig"`) |
| `maestro_v3_resumen.json` | Cuántos recursos tiene cada campo y de dónde sale cada valor. Las cifras de este documento salen de aquí |
| `eventos_v3.csv` | Una fila por acontecimiento programado, con la regla de su fecha. Mismo formato que el maestro |
| `tiempos_origen.csv` | Minutos y km por carretera de cada ciudad de origen a cada parada |
| `tiempos_polo.csv` | Minutos y km por carretera entre las paradas de cada polo |
| `red_paradas.csv` | A cuántos metros de la red vial queda cada parada |
| `red_calibracion.json` | Velocidades calibradas de la red y su error, medido por validación cruzada |
| `red_calibracion_recorridos.csv` | Cada recorrido de ficha usado para calibrar, con su tiempo en la ficha y en la red |
| `polos_bases.csv` | Dónde se duerme en cada polo, por qué y a qué altitud |
| `tiempos_base.csv` | Minutos y km de la base de cada polo a cada una de sus paradas |
| `tiempos_origen_base.csv` | Minutos y km de cada ciudad de origen a la base de cada polo |
| `clima_polo_mes.csv` | Lluvia, días con lluvia y temperaturas de cada polo mes a mes, con su veredicto de temporada |

## `maestro_v3.csv`

6 225 recursos del inventario del 29 de septiembre de 2026, todos con su ficha descargada el 30 de septiembre. De ellos, **4 578 pueden ser paradas de un itinerario**. Los demás son:

- 834 de folclore y 758 acontecimientos: dan intereses y fechas al polo, pero no se visitan como un lugar;
- 47 cumbres de más de 5 000 m, que se contemplan desde abajo;
- 8 lugares con la coordenada a revisar.

**Regla general:** lo que la fuente no trae queda vacío. Nada se imputa. Cuando un valor sale de una regla y no de la fuente, una columna `*_fuente` o `*_regla` lo dice.

### Identidad y ubicación

| Columna | Qué es | De dónde sale |
|---|---|---|
| `codigo` | Código del recurso en el inventario de MINCETUR | Inventario |
| `nombre` | Nombre con preposiciones y artículos en minúscula: "Festividad del Señor de los Temblores" | Inventario, con `nombre_legible` |
| `nombre_ficha` | El nombre tal como lo escribe la ficha | Ficha |
| `region`, `provincia`, `distrito` | Ubicación administrativa; el distrito con mayúsculas normales | Inventario |
| `categoria_num`, `categoria` | 1 sitios naturales, 2 manifestaciones culturales, 3 folclore, 4 realizaciones contemporáneas, 5 acontecimientos programados | Inventario |
| `tipo`, `subtipo` | Clasificación de MINCETUR, sin la letra inicial ("g. Cuerpo de Agua" → "Cuerpo de Agua") | Inventario |
| `url_ficha` | Ficha oficial: toda parada es verificable en la fuente | Inventario |
| `tiene_ficha` | Si la ficha se descargó y se leyó | Pipeline |
| `lat`, `lon` | Coordenada en grados decimales | Inventario, corregida |
| `coordenada` | Cómo llegó la coordenada: `intercambiada` (6 224: el archivo trae latitud y longitud al revés), `reparada` (1: el punto decimal corrido de la fila 14707), `correcta`, `sin_coordenada` o `invalida` | `pipeline/inventario.py` |
| `distancia_distrito_km` | Km a la mediana de los demás recursos de su distrito (solo en distritos con al menos cuatro recursos) | Pipeline |
| `coordenada_revisar`, `coordenada_motivo` | 12 coordenadas probablemente mal puestas. `lejos_de_su_distrito` (10): a más de 100 km de sus vecinos de distrito sin que la altitud lo confirme. `costa_en_altura` (2): playas que la ficha pone a nivel del mar y el modelo de elevación en la sierra | Pipeline |

### Polo

| Columna | Qué es | De dónde sale |
|---|---|---|
| `polo` | Polo turístico del modelo v2 (TA-01, semana 6); −1 si no tiene | Ver `polo_fuente` |
| `polo_fuente` | `v2` (4 751): el del modelo v2, con la coordenada igual o todavía dentro del polo. `asignado_v3` (1 267): recursos que en v2 no tenían coordenada o que son nuevos, asignados al polo cuyo miembro más lejano está más cerca, sin pasar de 80 km de viaje efectivo. `v2_revisado` (29): se movieron y cambiaron de polo. `v2_sin_polo` (129), `sin_polo_cercano` (39), `salio_de_su_polo` (1) y `coordenada_revisar` (9): sin polo | `pipeline/maestro.py::asignar_polos` |

Los 222 polos del modelo v2 se mantienen, con sus mismos números. Cada uno sigue cumpliendo que ningún par de sus lugares está a más de 80 km de viaje efectivo. La distancia es la del modelo v2: haversine más 0,06 km por metro de desnivel. El diámetro máximo sigue siendo 79,7 km, igual que en v2. El folclore y los acontecimientos se asocian a un polo, pero no cuentan para el diámetro.

### Valor y altitud

| Columna | Qué es | De dónde sale |
|---|---|---|
| `jerarquia` | 1 a 4. Vacía en folclore y acontecimientos ("No aplica") y en los recursos "POR JERARQUIZAR": nunca se imputa | Ficha |
| `jerarquia_texto` | Lo que dice la ficha | Ficha |
| `altitud_m` | Altitud que usa el motor, en metros | Ver `altitud_fuente` |
| `altitud_fuente` | `ficha` (5 953) o `dem_open_meteo` (226). Manda la ficha, salvo que no traiga altitud o que difiera del modelo de elevación en más de 500 m con la coordenada confirmada. Así "Cañón del Colca: 3" en la ficha queda en 2 215 m | Pipeline |
| `altitud_ficha_m`, `altitud_ficha_max_m` | La altitud de la ficha; si da un rango ("150 - 1550"), la mínima y la máxima | Ficha, con `leer_altitud` |
| `altitud_dem_m` | Modelo de elevación de Open-Meteo (Copernicus GLO-90) que usó el modelo v2, solo si la coordenada no cambió | `deliveries/week06/data/processed/polos_asignados_v2.csv` |
| `altitud_revisar` | La ficha y el modelo difieren en más de 500 m (188 recursos) | Pipeline |

### Visita

| Columna | Qué es | De dónde sale |
|---|---|---|
| `es_parada`, `motivo_no_parada` | Si puede ser parada de un itinerario, y si no, por qué: `folclore`, `acontecimiento`, `cumbre`, `coordenada_revisar`, `sin_coordenada` o `sin_ficha` | Pipeline |
| `intereses` | Los chips del contrato que el recurso atiende, separados por `\|` | Categoría, tipo, subtipo y actividades de la ficha, con [`pipeline/referencia/intereses.csv`](../../pipeline/referencia/intereses.csv) |
| `actividades` | Actividades que registra la ficha, separadas por `\|` | Ficha |
| `visita_min`, `visita_min_fuente` | Minutos de visita, sin contar el acceso. Es un **supuesto del equipo**, no un dato de la fuente | [`pipeline/referencia/duracion_visita.csv`](../../pipeline/referencia/duracion_visita.csv), por subtipo, tipo o categoría |
| `ingreso` | `libre`, `boleto`, `permiso` (semi-restringido) u `otro` | Ficha |
| `tarifa_soles`, `tarifa_regla` | Entrada de un adulto peruano. 0 si el ingreso es libre. La regla dice cómo se eligió entre los montos del texto (ver `leer_tarifa`) | Ficha, con `leer_tarifa` |
| `boleto_combinado` | La entrada es parte de un boleto para varios lugares (Boleto Turístico del Cusco, un circuito): se paga una vez por viaje | Ficha |
| `abre`, `cierra` | Horario en 24 h | Ficha, con `leer_horario` |
| `dias` | Días de atención (`lun\|mar\|…`), solo si la ficha los dice (863 lugares) | Ficha, con `leer_dias` |
| `epoca`, `epoca_observaciones` | Época propicia de visita, como la escribe la ficha | Ficha |

### Acceso

Salen del recorrido más rápido de la ficha entre los que tienen todos sus tiempos. Cuando la ficha repite un tramo con otro medio (en auto, en bus o a pie), son alternativas y no tramos seguidos: cuenta la más rápida.

| Columna | Qué es |
|---|---|
| `acceso_km`, `acceso_min` | Distancia y tiempo total del recorrido |
| `acceso_desde` | Dónde empieza: departamento/provincia/distrito |
| `caminata_min` | Minutos a pie, a caballo o en acémila al final del recorrido: lo que la red vial no cubre |
| `acceso_acuatico`, `acceso_aereo` | Si el recorrido necesita bote o avioneta |
| `ultimo_medio`, `ultimo_via` | Medio de transporte y tipo de vía del último tramo |
| `recorridos` | Cuántas formas de llegar da la ficha |

### Visitantes y servicios

| Columna | Qué es |
|---|---|
| `visitantes_anio` | Año más reciente con registro de visitantes en la ficha |
| `visitantes_nacionales`, `visitantes_extranjeros`, `visitantes_locales` | Visitantes de ese año, según la fuente que cita la ficha |
| `alimentacion_cerca`, `alojamiento_cerca` | La ficha registra servicios de alimentación (dentro o fuera del recurso) o de alojamiento (fuera) |
| `accesible_silla_ruedas` | La ficha registra condiciones para personas con discapacidad física |
| `descripcion_corta` | Las primeras oraciones completas de la descripción, hasta 280 caracteres, sin contactos |
| `foto_url` | Foto principal en el servidor de MINCETUR |
| `fecha_corte` | Fecha de corte del inventario |

## Qué tan completo está

De los 4 633 lugares (categorías 1, 2 y 4):

| Campo | Lugares con dato |
|---|---|
| Jerarquía | 3 741 (81 %) |
| Tarifa, incluido el 0 del ingreso libre | 3 952 (85 %) |
| Horario | 4 589 (99 %) |
| Acceso completo | 4 603 (99 %) |
| Visitantes | 4 620 (100 %) |
| Intereses | 4 596 (99 %) |

## `eventos_v3.csv`

Los 758 acontecimientos programados del inventario (categoría 5) con cuándo se celebran, leído de su ficha por [`pipeline/eventos.py`](../../pipeline/eventos.py). La fecha se guarda como una **regla** y no como un día, porque muchas fiestas cambian de fecha cada año; [`dreemgo/calendario.py`](../../dreemgo/calendario.py) la convierte en fechas para el año del viaje.

| Columna | Qué es |
|---|---|
| `codigo`, `nombre`, `tipo`, `subtipo`, `region`, `provincia`, `distrito`, `lat`, `lon`, `url_ficha` | Como en el maestro |
| `polo` | El polo al que se asocia el acontecimiento; −1 en los 13 que no tienen |
| `regla` | `fija 07-25` (un día), `fija 07-24..07-30` (un rango, que puede cruzar el año: `fija 12-24..01-06`), `pascua -7..0` (días contados desde el Domingo de Pascua), `nesimo 04 2 dom` (el segundo domingo de abril; `-1` es el último), `mes 09` (todo el mes). Vacía si la fecha está por confirmar |
| `dia_central` | El día o los días que la ficha llama centrales dentro del rango: `07-16` o `07-28..07-29` (113 acontecimientos) |
| `precision_fecha` | `exacta` (518): la ficha publica el día. `aproximada` (221): calculada desde la Pascua o el santoral, solo el mes, o la fecha de una edición reciente. `por_confirmar` (19): sin fecha |
| `fuente_fecha` | `texto_ficha` (545), `nombre_movil` (120: Semana Santa, Carnaval, Corpus Christi… por su nombre), `mes_texto` (45), `texto_movil` (24: "un día después de la Octava de Corpus"), `santoral` (5) |
| `evidencia` | La frase de la ficha que respalda la regla, o el patrón del santoral que la dio |

En una muestra al azar de 40 acontecimientos cuyas fechas se leyeron a mano, 38 de las 39 reglas caen en días de fiesta. El detalle está en [`pipeline/README.md`](../../pipeline/README.md#qué-tan-bien-fecha-los-acontecimientos).

## Tiempos por carretera

Salen de la red vial del extracto de OpenStreetMap del 30 de septiembre de 2026, con las velocidades calibradas contra los recorridos de las fichas ([`pipeline/tiempos.py`](../../pipeline/tiempos.py)). Son **obra derivada de OpenStreetMap: se publican bajo ODbL 1.0**, © colaboradores de OpenStreetMap ([DATA_LICENSES.md](../../DATA_LICENSES.md)).

Cada tiempo es de puerta a puerta en auto o bus:

- el camino más rápido por la red;
- lo que falta de cada punta a la vía más cercana, contado 1,3 veces la línea recta y al ritmo de una trocha;
- y 7 minutos fijos por traslado.

La caminata final que registra la ficha (`caminata_min` del maestro) no está incluida. El motor la suma aparte.

| Archivo | Columnas | Filas |
|---|---|---|
| `tiempos_origen.csv` | `origen` (el `id` de [`origenes.csv`](../../pipeline/referencia/origenes.csv)), `codigo` de la parada, `minutos`, `km` | 109 872: las 24 ciudades por las 4 578 paradas |
| `tiempos_polo.csv` | `polo`, `desde`, `hasta` (códigos de parada), `minutos`, `km`. En los dos sentidos | 176 570, en los 221 polos con dos paradas o más |
| `red_paradas.csv` | `codigo`, `polo`, `metros_a_la_red`, `lejos_de_la_red` (más de 5 km de cualquier vía) | 4 578 |
| `tiempos_base.csv` | `polo`, `codigo` de la parada, `minutos`, `km`. Valen igual de vuelta: en la red cada tramo cuesta lo mismo en los dos sentidos | 4 465: cada parada de un polo |
| `tiempos_origen_base.csv` | `origen`, `polo`, `minutos`, `km` | 5 328: las 24 ciudades por los 222 polos |

`minutos` y `km` quedan vacíos cuando no hay camino por carretera. Pasa en tres casos:

- **Iquitos y la selva baja:** ninguna carretera las une con el resto del país, así que el viaje necesita avión o bote.
- **Paradas lejos de la red:** 173 están a más de 5 km de cualquier vía.
- **Paradas de un mismo polo sin unión por carretera:** son 4 202 pares, el 2 %.

Desde Lima quedan sin camino 259 paradas y 9 bases. De la base a sus propias paradas, 144 de 4 465.

### `polos_bases.csv`

Cómo se elige está en [`pipeline/bases.py`](../../pipeline/bases.py) y el resumen en [`pipeline/README.md`](../../pipeline/README.md#dónde-duerme-cada-polo). También es obra derivada de OpenStreetMap.

| Columna | Qué es |
|---|---|
| `polo` | Número del polo |
| `base`, `lat`, `lon` | El lugar de OSM donde se duerme |
| `lugar` | `ciudad`, `pueblo`, `barrio` o `caserío`, según OSM (`place`) |
| `capital_de_distrito` | Si OSM lo marca como capital de su distrito |
| `hospedajes_osm` | Hoteles, hostales, casas de huéspedes y alojamientos que OSM registra a menos de 3 km |
| `criterio` | `carretera` (218): el de menor costo por carretera. `linea_recta` (4): ninguna parada del polo está a menos de 5 km de una vía |
| `paradas`, `paradas_con_camino` | Paradas del polo y cuántas tienen camino por carretera desde la base |
| `minutos_medios` | Minutos de la base a sus paradas, en promedio pesado por jerarquía |
| `altitud_m`, `altitud_fuente` | `osm` (194): la que declara el lugar. `recursos_a_2_km` (13): la mediana de los recursos del inventario a menos de 2 km. Vacía en 15 |

## `clima_polo_mes.csv`

Doce filas por polo, del clima diario 2016-2025 de Open-Meteo en el centro del polo ([`pipeline/clima.py`](../../pipeline/clima.py), [decisión 0006](../../docs/decisiones/0006-clima-por-polo.md)). **Licencia CC BY 4.0**: Open-Meteo.com, sobre ERA5 y ERA5-Land de Copernicus.

| Columna | Qué es |
|---|---|
| `polo`, `mes` | |
| `lluvia_mm` | Lluvia del mes, promedio de diez años |
| `dias_con_lluvia` | Días con 1 mm o más (definición de la OMM) |
| `temp_min_c`, `temp_max_c` | Promedio de las mínimas y de las máximas diarias, llevadas a la altitud de la base con 6,5 °C por km |
| `puesto_lluvia` | 1 es el mes más lluvioso del polo |
| `veredicto` | `viable`, `advertencia` o `desaconsejado`: 150 mm o más en el mes, y estar entre los 3 más lluviosos del polo con más de 50 mm. Los dos, desaconsejado; uno, advertencia |
| `fuente` | `open_meteo_polo` (36 polos al 1 de octubre) o `region_semana6`: mientras la descarga no termina, la capa regional de la semana 6, sin días de lluvia ni temperaturas |
| `altitud_clima_m`, `altitud_base_m` | La altitud del punto de clima según Open-Meteo y la de la base, para ver el ajuste de temperatura |

`red_calibracion.json` guarda las velocidades por clase de vía, los recargos y el error por tramo de distancia; el resumen está en [`pipeline/README.md`](../../pipeline/README.md#qué-tan-bien-estima-los-tiempos-de-viaje). `red_calibracion_recorridos.csv` tiene los 2 259 recorridos de fichas que se consideraron. Por cada uno trae los km y minutos de la ficha y los de la red, y si ambos describen el mismo camino (`misma_distancia`); solo esos entraron al ajuste.

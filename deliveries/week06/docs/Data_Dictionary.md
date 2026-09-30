# DreemGO — Diccionario de datos

**Semana 6** · DS3022 Desarrollo de Producto de Datos · UTEC

Tres tablas en `data/processed/`, unidas por `REGIÓN` y por recurso. Todas con separador `;` y codificación UTF-8.

**Cómo leer la columna «Origen»:**

| Marca | Significado |
|---|---|
| **Fuente** | Viene tal cual del proveedor de datos |
| **Medida** | Obtenida de una API externa |
| **Calculada** | Derivada de otras columnas por una fórmula |
| **Extraída** | Leída de la ficha oficial de MINCETUR por scraping |
| **Inferida** | Producto de una regla nuestra, no de la fuente |
| **Simulada** | Generada artificialmente, sin correspondencia con la realidad |

---

## 1 · `dreemgo_master_dataset.csv` — recursos turísticos

6 160 filas · 19 columnas. Inventario Nacional de Recursos Turísticos de MINCETUR (licencia ODC-BY, corte 2026-08-31), enriquecido.

| Columna | Descripción | Origen | Nulos |
|---|---|---|---:|
| `CODIGO DEL RECURSO` | Identificador único. Clave primaria, sin duplicados | Fuente | 0 |
| `NOMBRE DEL RECURSO` | Nombre oficial del atractivo | Fuente | 0 |
| `REGIÓN` | Departamento. Clave de cruce con clima y eventos | Fuente | 0 |
| `PROVINCIA` · `DISTRITO` | División política menor | Fuente | 0 |
| `CATEGORÍA` | Clasificación nivel 1 (5 valores) | Fuente | 0 |
| `TIPO DE CATEGORÍA` | Clasificación nivel 2 (35 valores) | Fuente | 0 |
| `SUB TIPO CATEGORÍA` | Clasificación nivel 3 (187 valores) | Fuente | 1 |
| `URL` | Enlace a la ficha oficial. Integridad verificada al 100 % | Fuente | 0 |
| `latitud` · `longitud` | Grados decimales WGS 84. **Corregidas**: MINCETUR publica las etiquetas intercambiadas | Fuente (corregida) | 1 245 |
| `FECHA_DE_CORTE` | Fecha de extracción, `YYYYMMDD` | Fuente | 0 |
| `ALTITUD` | Metros sobre el nivel del mar. Modelo digital de elevación de Open-Meteo. Error conocido: +16 a −38 m en valle, hasta +250 m en cañón | Medida | 1 245 |
| `DISTANCIA_CAPITAL_KM` | Distancia Haversine a la capital regional | Calculada | 1 245 |
| `INDICE_COSTO_LOGISTICO` | Categorización ordinal de la anterior: 1 = <20 km · 2 = <80 km · 3 = >80 km. **Ver nota de nomenclatura** | Calculada | 1 245 |
| `ZONA_CLIMATICA` | Piso ecológico peruano deducido de altitud y región (7 valores) | Inferida | 1 245 |
| `JERARQUIA_OFICIAL` | Importancia oficial del recurso, 1 a 4. **Ver nota de verificación** | Extraída | 0 |
| `TIPO_INGRESO` | Libre o Pagado. **No es dato de la ficha** — ver nota | Inferida | 0 |
| `EPOCA_PROPICIA` | Temporada recomendada. **No es dato de la ficha** — ver nota | Inferida | 0 |

### Los 1 245 nulos son los mismos en las cinco columnas geográficas

No son ruido ni error de carga. Se concentran al 100 % en las categorías **Folclore** (663) y **Acontecimientos Programados** (582), que describen prácticas y eventos, no lugares. Una danza o una fiesta patronal no tienen un punto en el mapa. No se imputan; se usan como capa de contexto a nivel de distrito.

### Nota de verificación · `JERARQUIA_OFICIAL`

La columna **es real**, extraída de la ficha oficial. Se verificó por cuatro vías independientes porque el repositorio contiene también un script que genera esta columna al azar:

- No coincide con los pesos de ese generador (χ² = 89,4 · p = 3 × 10⁻¹⁹).
- Está asociada a la categoría del recurso (V de Cramér = 0,234 · p = 1 × 10⁻²⁰⁹). Un dato aleatorio sería independiente.
- Está asociada a la región (V de Cramér = 0,213).
- Los hitos reconocidos reciben jerarquía 4 y sus dependencias bajan: Machu Picchu 4, Chan Chan 4, Nasca 4, Huascarán 4, Valle del Colca 4 — mientras que Museo de Sitio Chan Chan 2, Cañón del Colca 2, Ventana del Colca 1.

**Salvedad:** `clean_impute_dataset.py` convierte en `1` cualquier valor no reconocido, de modo que los recursos donde el scraper falló quedaron mezclados con los de jerarquía 1 legítima. No se sabe cuántos son. Se corrige añadiendo `ORIGEN_JERARQUIA` (`scrapeado` / `imputado`) en la Semana 7.

Distribución: jerarquía 1 → 2 577 · 2 → 2 144 · 3 → 1 122 · 4 → 317.

### Nota · `TIPO_INGRESO` y `EPOCA_PROPICIA` no son datos de la ficha

Ambas fueron extraídas por el scraper y luego **sobrescritas** por `clean_impute_dataset.py`:

- `TIPO_INGRESO` es hoy una función determinista de `JERARQUIA_OFICIAL` — jerarquía 1-2 → "Libre" (4 721), jerarquía 3-4 → "Pagado" (1 439), sin excepciones. No aporta información independiente y **no debe usarse junto a la jerarquía en un modelo**: sería la misma variable dos veces.
- `EPOCA_PROPICIA` es una función determinista de `ZONA_CLIMATICA` y toma tres valores: "Todo el año" (3 337), "Abril a Noviembre" (2 538), "Mayo a Octubre" (285). Los 1 245 recursos sin coordenadas quedan en "Todo el año", lo que declara viable los doce meses a cada fiesta patronal del inventario.

Re-extraerlas con trazabilidad de origen es la deuda técnica prioritaria de la Semana 7.

### Nota de nomenclatura · `INDICE_COSTO_LOGISTICO`

En `Requirements.md` (Semana 5) y en la presentación esta variable se llama **`INDICE_LEJANIA`**, porque no contiene unidades monetarias: aproxima lejanía, no costo. El renombrado en el CSV y en los scripts queda pendiente para la Semana 7, junto con el tipo de ingreso real, que será la primera aproximación al costo.

---

## 2 · `historial_clima_regiones.csv` — climatología mensual

2 880 filas · 7 columnas. 24 regiones × 10 años × 12 meses. Descargado de Open-Meteo Archive para las coordenadas de la capital de cada región.

| Columna | Descripción | Origen |
|---|---|---|
| `REGION` | Clave de cruce con el dataset maestro | Fuente |
| `AÑO` | 2014 a 2023 | Fuente |
| `MES` | 1 a 12 | Fuente |
| `TEMPERATURA_MEDIA_C` | Temperatura media mensual, °C | Medida |
| `PRECIPITACION_TOTAL_MM` | Precipitación total del mes, mm | Medida |
| `NIVEL_RIESGO_CLIMATICO` | `1_Seguro` (≤30 mm) · `2_Precaucion` (≤100 mm) · `3_Peligro` (>100 mm) | Calculada |
| `SENSACION_TERMICA` | `Frio` (≤10 °C) · `Templado` (≤20 °C) · `Calido` (>20 °C) | Calculada |

**Esto es climatología, no pronóstico.** Describe el comportamiento medio observado en diez años; no predice un mes concreto y no modela eventos extremos. **No hay ninguna fuente de huaicos ni de deslizamientos en este pipeline**, y ninguna afirmación del producto debe sugerir lo contrario. Para planificar un viaje con semanas de anticipación la norma climática es lo apropiado; el término correcto es *viabilidad climática histórica*.

**Limitación de granularidad.** La serie es por región, y una región peruana puede ir del nivel del mar a más de 6 000 m: Arequipa mezcla costa desértica con puna. El propio dataset maestro reconoce siete pisos ecológicos. El cruce por `REGIÓN × ZONA_CLIMATICA` queda para la Semana 7.

Distribución: 1 293 observaciones `1_Seguro` · 618 `2_Precaucion` · 969 `3_Peligro`. Tres regiones no registran ningún mes en nivel de peligro.

---

## 3 · `comercios_ferias_locales.csv` — eventos con ventana temporal

> ## ⚠ DATASET SIMULADO
>
> **Las 500 filas de esta tabla fueron generadas artificialmente** por `code/generate_commerce_data.py`. Los nombres son combinaciones de plantillas, las coordenadas son aleatorias dentro de cada región y las fechas corresponden a 2024. **No hay ningún comercio, feria ni evento real aquí**, y la tabla no admite ninguna afirmación empírica sobre el comercio local peruano.
>
> Existe para prototipar el mecanismo de inyección de eventos con ventana temporal, que es el lado de la oferta del producto. La fuente real prevista son los **749 Acontecimientos Programados** del inventario oficial —393 fiestas patronales, 117 festivales, 117 fiestas tradicionales, 23 ferias— cuya fecha MINCETUR no publica y que solo el municipio organizador conoce.

| Columna | Descripción | Origen |
|---|---|---|
| `ID_EVENTO` | Identificador del evento | Simulada |
| `NOMBRE_EVENTO` | Nombre generado por plantilla | Simulada |
| `REGION` | Clave de cruce con el dataset maestro | Simulada |
| `CATEGORIA` | Gastronomía · Cultura · Aventura · Alojamiento · Entretenimiento | Simulada |
| `LATITUD` · `LONGITUD` | Coordenadas del evento | Simulada |
| `FECHA_INICIO` · `FECHA_FIN` | Ventana de vigencia | Simulada |
| `COSTO_PEN` | Costo estimado de entrada, soles | Simulada |
| `RELEVANCIA_PUBLICIDAD` | Peso comercial del anunciante, 1 a 5 | Simulada |

### Regla de uso de `RELEVANCIA_PUBLICIDAD`

**El municipio o el comercio aporta datos; no compra posición.** El orden de los eventos que ve el viajero lo decide la compatibilidad con su consulta —afinidad de categoría, cercanía al itinerario y encaje de fechas—. `RELEVANCIA_PUBLICIDAD` interviene **solo como desempate** entre eventos que ya son elegibles y que ya empataron en compatibilidad. Nunca adelanta a un evento más compatible.

Ordenar por este campo en primer lugar convierte el recomendador en un espacio publicitario, y un recomendador que se puede comprar deja de tener valor para el viajero. La implementación está en `code/DreemGO_Predictive_Engine.ipynb`, celda 8.

---

## 4 · `fichas_mincetur.csv` — extracción de la ficha oficial

6 160 filas · una por recurso del inventario · clave `CODIGO`. Producida por
`code/scraper_mincetur_v3.py`. **6 129 con HTTP 200**; las 31 restantes fallaron y
guardan el texto del error en `HTTP` (bug conocido: debería guardar el código).

| Columna | Descripción | Relleno |
|---|---|---:|
| `CODIGO` · `URL` · `HTTP` | clave, enlace a la ficha y estado de la petición | 100 % |
| `FICHA_JERARQUIA_TXT` | lo que la ficha dice, literal: `1`…`4`, `No aplica`, `POR JERARQUIZAR` | 100 % |
| `FICHA_JERARQUIA_NUM` | solo cuando es un número real de 1 a 4; vacío en otro caso | 59,7 % |
| `FICHA_ALTITUD_M` · `FICHA_TOPONIMIA` | altitud oficial y toponimia | 96 % |
| `INGRESO_TIPO` · `INGRESO_OBS` · `TARIFA_SOLES` | tipo de ingreso, observaciones y monto en soles | 74 % · 12 % |
| `EPOCA_PROPICIA` · `EPOCA_ESPECIFICACION` · `HORA_VISITA` | **frecuencia de visita**, no ventana climática — ver nota | 74 % |
| `N_ACTIVIDADES` · `ACTIVIDADES` | 63 actividades en 6 familias, separadas por `\|`, formato `Familia>Actividad` | 93 % |
| `N_TRAMOS` · `ACCESO_KM` · `ACCESO_MIN` · `ACCESO_MEDIOS` · `ACCESO_VIAS` | acceso desde el pueblo más cercano | 74 % |
| `VISITANTES_NAC` · `_EXT` · `_LOC` · `_ANIO` | visitantes declarados y año de referencia | 64 % |
| `N_SERV_ALOJAMIENTO` · `N_SERV_ALIMENTACION` | servicios registrados en la ficha | 74 % |
| `TABLAS_RECONOCIDAS` | **columna vacía** — el scraper la declara y no la llena. Bug conocido. | 0 % |

### El 26 % que falta es estructural, no un fallo

| Categoría | Fichas | Sin ingreso/época/acceso | % |
|---|---:|---:|---:|
| 5. Acontecimientos programados | 749 | 749 | 100,0 |
| 3. Folclore | 824 | 820 | 99,5 |
| 2. Manifestaciones culturales | 2 105 | 11 | 0,5 |
| 1. Sitios naturales | 2 147 | 9 | 0,4 |
| 4. Realizaciones técnicas | 304 | 0 | 0,0 |

Una danza o una fiesta patronal no tiene acceso en kilómetros ni época propicia porque no
es un lugar. Los tres campos faltan en las mismas fichas con un solapamiento del 96,2 %.

### Nota · `EPOCA_PROPICIA` de la ficha ≠ `EPOCA_PROPICIA` del maestro

Miden cosas distintas y comparten nombre, lo que es una trampa. El maestro trae una
ventana climática derivada por regla (`Abril a Noviembre`, `Todo el año`, `Mayo a
Octubre`); la ficha trae frecuencia de visita (`Todo el año`, `Esporádicamente - algunos
meses`, `Fines de semana`). Coinciden en 36 % por la etiqueta compartida, no por acuerdo.
**La estacionalidad climática sale de TA-05, no de esta columna.**

---

## 5 · `polos_asignados_v2.csv` — etiqueta de polo por recurso

4 915 filas · salida de `code/ta01_polos_acotados.py` · clave `CODIGO DEL RECURSO`.

`POLO` es el identificador del polo, o **−1** para los 129 recursos que no alcanzan el
mínimo de 5. `JERARQUIA_OFICIAL` viene del maestro y **solo es fiable en el 59,7 %**: usar
`FICHA_JERARQUIA_NUM` de la tabla 4 para cualquier análisis nuevo.

---

## 6 · `puntaje_polos.csv` — ranking de polos

222 filas · una por polo · salida de `code/ta03_score_polo.py`.

| Columna | Descripción |
|---|---|
| `POLO` · `recursos` · `region` · `regiones` | identidad y tamaño |
| `jerarquia` | media **sobre los recursos que tienen jerarquía real**, no sobre todos |
| `jer_conocida` · `cobertura_jerarquia` | cuántos la tienen, y qué fracción del polo sostiene el promedio |
| `lejania` | media de `INDICE_COSTO_LOGISTICO` · **sin validar**, ver `ModelSelection.md` §10 |
| `saturacion` · `limpio` | fracción del polo en Lima o Cusco · `limpio` = ninguno |
| `novedad` · `puntaje` | `0,5·(1−saturación) + 0,5·lejanía` · `(1−λ)·jerarquía + λ·novedad`, λ = 0,30 |

`novedad` y `puntaje` quedan **vacíos** en los 10 polos que no entran al ranking: 1 sin
ningún recurso jerarquizado y 9 con cobertura menor al 30 %.

---

## 7 · `estacionalidad_polo_mes.csv` — TA-05

2 664 filas · 222 polos × 12 meses · salida de `code/ta05_estacionalidad.py`.

| Columna | Descripción |
|---|---|
| `POLO` · `MES` · `mes_nombre` | clave compuesta |
| `precip_mm` · `temp_c` | normal climática del polo en ese mes, ponderada por recursos por región |
| `frac_lluvias` | fracción del polo cuya región está en su propia temporada de lluvias |
| `veredicto` | `viable` · `advertencia` · `desaconsejado` |
| `puesto_mes` | ranking del mes dentro del polo, de más seco a más húmedo |

Esta tabla existe **precisamente para no tocar el maestro**: RNF-01 exige que cambiar de
mes no altere el dataset base. Criterios del veredicto en `ModelSelection.md` §9.1.

---

## 8 · `ingreso_por_polo.csv` y `parametros_costo.csv` — modelo de costo

`ingreso_por_polo.csv` · 222 filas · `frac_paradas_pagadas` (fracción de paradas del polo
que cobran entrada, según la ficha) y `tarifa_mediana_soles`. Hay 55 polos donde todo es
libre y 16 donde más de la mitad cobra: por eso no puede ser una constante.

`parametros_costo.csv` · 7 filas · `parametro`, `valor`, `rango_min`, `rango_max`,
`unidad`, `calibrado`, `fuente`. **`calibrado = si`** hace que el Monte Carlo mueva el
parámetro solo ±5 %; **`no`** mete el rango completo y ensancha la banda. Hoy hay 2
calibrados (entradas, desde 782 tarifas reales) y 5 sin calibrar.

---

## 9 · `evaluacion_ta04.csv` — evaluación del ordenamiento

222 filas · salida de `code/ta04_evaluacion.py`. Para cada polo, paradas visitadas y
kilómetros recorridos con los tres métodos: `par_jer`/`km_jer` (orden por jerarquía),
`par_vec`/`km_vec` (vecino más cercano) y `par_2opt`/`km_2opt` (vecino + 2-opt). `base` es
el índice del recurso elegido como punto base del itinerario.

---

## 10 · `puntos_clima_v2.csv` — puntos de descarga pendientes

88 filas · `REG`, `ZONA_CLIMATICA`, `recursos`, `lat`, `lon`, `alt`. Centroides de cada
combinación región × zona climática con al menos 5 recursos, que cubren el 99,3 % del
inventario geolocalizable. Los consume `code/fetch_climate_v2.py`, **aún sin ejecutar**:
mientras tanto TA-05 trabaja con los 24 puntos regionales.

---

## Cómo se relacionan

```
dreemgo_master_dataset        fichas_mincetur          historial_clima_regiones
   (recursos, 6 160)          (ficha oficial, 6 129)      (clima, 2 880)
          │                            │                        │
          │  CODIGO DEL RECURSO ═══════╡                        │ REGION + MES
          │                                                     │
   TA-01 ─┴─ polos_asignados_v2 (4 915) ──┬── puntaje_polos (222) ── TA-03
                                          │
                                          ├── estacionalidad_polo_mes (2 664) ── TA-05
                                          ├── ingreso_por_polo (222) ─────────── costo
                                          └── evaluacion_ta04 (222) ──────────── TA-04
                                                        │
                                               consulta del usuario
                                   origen · mes · días · presupuesto
                                   altitud máxima · intereses
                                                        │
                                    code/consulta.py resuelve y verifica
                                    los criterios de RF-01, RF-02 y RNF-01
```

El agrupamiento corre **offline**. Cambiar el mes de la consulta reordena polos ya
calculados y no reentrena nada, que es de donde sale el requerimiento de responder en
menos de 5 segundos. Ninguna de las tablas derivadas escribe sobre el maestro, que es lo
que RNF-01 exige.

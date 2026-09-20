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

## Cómo se relacionan

```
dreemgo_master_dataset          historial_clima_regiones
  (recursos, 6 160)               (clima, 2 880)
        │                                │
        │  REGIÓN                        │  REGION + MES
        └────────────┬───────────────────┘
                     │
            consulta del usuario
       intereses · mes · días · presupuesto
                     │
                     ├─ TA-01: polo recomendado (81 polos precalculados)
                     ├─ ponderación por JERARQUIA_OFICIAL
                     ├─ penalización por NIVEL_RIESGO_CLIMATICO del mes
                     └─ eventos vigentes ── comercios_ferias_locales (SIMULADO)
```

El agrupamiento corre **offline**. Cambiar el mes de la consulta reordena polos ya calculados y no reentrena nada, que es de donde sale el requerimiento de responder en menos de 5 segundos.

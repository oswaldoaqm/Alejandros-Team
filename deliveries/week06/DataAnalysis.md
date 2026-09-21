# DreemGO — Análisis Exploratorio de Datos

**Semana 6** · DS3022 Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Equipo: Miguel · Alejandro · Diego · Christopher
Entrega: 16 de septiembre de 2026

---

## 1. Qué datos tenemos

El producto se construye sobre tres tablas, unidas por región y por recurso.

| Tabla | Filas | Columnas | Origen | Naturaleza |
|---|---|---|---|---|
| `dreemgo_master_dataset.csv` | 6 160 | 19 | MINCETUR + derivadas | Dimensión: recursos turísticos |
| `historial_clima_regiones.csv` | 2 880 | 7 | Open-Meteo Archive | Hechos: 24 regiones × 10 años × 12 meses |
| `comercios_ferias_locales.csv` | 500 | 10 | **Generado sintéticamente** | Hechos: eventos con ventana temporal |

> **Advertencia sobre la tercera tabla.** `comercios_ferias_locales.csv` no contiene datos reales: fue generado por `code/generate_commerce_data.py` para poder prototipar el mecanismo de inyección de eventos con ventana temporal. No debe usarse para ninguna afirmación empírica sobre el comercio local peruano. Está documentado aquí y en el diccionario de datos.

---

## 2. Estructura y calidad del inventario

### 2.1 Distribución por categoría

| Categoría MINCETUR | Recursos | % |
|---|---:|---:|
| 1. Sitios Naturales | 2 164 | 35,1 % |
| 2. Manifestaciones Culturales | 2 118 | 34,4 % |
| 3. Folclore | 824 | 13,4 % |
| 5. Acontecimientos Programados | 749 | 12,2 % |
| 4. Realizaciones Técnicas y Científicas | 305 | 5,0 % |

### 2.2 El faltante no es ruido

**1 245 recursos (20,2 %) no tienen coordenadas.** La ausencia no es aleatoria y esto cambia una decisión de diseño:

| Categoría | Sin coordenadas |
|---|---:|
| Folclore | 663 |
| Acontecimientos Programados | 582 |
| Resto | 0 |

El 100 % del faltante se concentra en las dos categorías que describen **prácticas y eventos**, no lugares. Una danza, un plato típico o una fiesta patronal no tienen un punto en el mapa. Imputar una coordenada sería inventar un dato.

**Decisión:** los 1 245 registros quedan fuera del cálculo de rutas y se conservan como capa de contexto a nivel de distrito. Son, además, el insumo natural del componente de eventos con ventana temporal (ver §6).

Quedan **4 915 recursos geolocalizables (79,8 %)** como base del modelado.

De esos, el modelo de agrupamiento deja fuera otros 129 por no alcanzar el tamaño mínimo de polo (`ModelSelection.md` §6). Sumando ambas exclusiones, **1 374 recursos — el 22,3 % del inventario — no pueden formar parte de un itinerario de varias paradas.** Es el techo real del producto y conviene tenerlo escrito antes que descubrirlo en la defensa.

> La primera versión del modelo dejaba fuera 2 400 recursos, el 39 %. El cambio de algoritmo documentado en `ModelSelection.md` §5.7 recuperó 1 026.

### 2.3 Hallazgo heredado de la Semana 4

Las columnas `LATITUD` y `LONGITUD` **venían intercambiadas desde la fuente oficial**. Con las etiquetas originales, el 0 % de los recursos cae dentro del territorio peruano; al intercambiarlas, el 100 %. El error es silencioso —no lanza excepción— y habría corrompido todo análisis espacial. Corregido y verificado en `deliveries/week04/code/data_quality_check.py`.

---

## 3. Variables derivadas y su procedencia

Esta es la tabla que hay que leer con atención, porque separa lo medido de lo inferido.

| Variable | Procedencia | Estado |
|---|---|---|
| `ALTITUD` | Modelo digital de elevación de Open-Meteo | **Medida** (con error conocido) |
| `DISTANCIA_CAPITAL_KM` | Haversine a la capital regional | **Calculada** |
| `INDICE_COSTO_LOGISTICO` | Discretización ordinal de la anterior | **Calculada** |
| `ZONA_CLIMATICA` | Regla por pisos ecológicos (altitud + región) | **Inferida** |
| `JERARQUIA_OFICIAL` | Scraping de la ficha oficial | **Real en el 59,7 %** — el 40,3 % restante sin respaldo, ver §3.1 |
| `TIPO_INGRESO` | Regla sobre `JERARQUIA_OFICIAL` | **Inferida** |
| `EPOCA_PROPICIA` | Regla sobre `ZONA_CLIMATICA` | **Inferida** |

### 3.1 Qué sobrevivió de TA-03 y qué no

El pipeline de esta semana tiene dos scripts que escriben las mismas tres columnas sobre el mismo archivo: `scraper_mincetur.py`, que las extrae de la ficha oficial, y `clean_impute_dataset.py`, que las sobrescribe con reglas. Había que determinar cuál quedó en el archivo final. Lo verificamos columna por columna.

**`JERARQUIA_OFICIAL` es real en el 59,7 % del inventario y no tiene respaldo en el 40,3 % restante.** Llegar a esa frase costó tres intentos, y el camino vale más que el resultado.

**Primer intento · pruebas agregadas.** Cuatro comprobaciones indirectas, todas favorables:

| Prueba | Resultado |
|---|---|
| ¿Coincide con los pesos del generador aleatorio de `build_master_dataset.py` (0,40 / 0,40 / 0,15 / 0,05)? | **No** — χ² = 89,4 · p = 3 × 10⁻¹⁹ |
| ¿Está asociada a la categoría del recurso? | **Sí** — V de Cramér = 0,234 · p = 1 × 10⁻²⁰⁹ |
| ¿Está asociada a la región? | **Sí** — V de Cramér = 0,213 · p = 9 × 10⁻¹³¹ |
| ¿Los hitos reconocidos reciben jerarquía 4? | **Sí** — Machu Picchu, Chan Chan, Nasca, Huascarán y el Valle del Colca reciben 4, y sus dependencias bajan: Museo de Sitio Chan Chan 2, Cañón del Colca 2, Ventana del Colca 1 |

La conclusión fue que la columna era real. Fue prematura: **las cuatro pruebas son agregadas, y una prueba agregada no detecta un subconjunto contaminado cuando el subconjunto limpio domina la muestra.** Con el 60 % de la columna correcto, la asociación con categoría y región aparece igual y el χ² rechaza los pesos del generador igual.

**Segundo intento · dos fichas.** Un volcado mostró que el recurso 11 dice «Jerarquía: No aplica» y el 22 «POR JERARQUIZAR», mientras el maestro afirmaba 3 para ambos. Se concluyó lo contrario: que la columna estaba inventada. También prematuro — dos casos no son una muestra, y los dos caían justo en el subconjunto malo.

**Tercero · comparación fila a fila contra la fuente.** Con las 6 129 fichas ya extraídas la comparación es directa:

| Lo que dice la ficha oficial | Recursos | Qué hace el maestro |
|---|---:|---|
| Un número de 1 a 4 | 3 660 (59,7 %) | **coincide en el 100,0 %** |
| «POR JERARQUIZAR» | 896 (14,6 %) | asigna un número igual |
| «No aplica» | 1 573 (25,7 %) | asigna un número igual |

La matriz de confusión sobre los 3 660 es una diagonal perfecta — 1 907 / 1 581 / 157 / 15, cero fuera de la diagonal. Donde MINCETUR publica una jerarquía, el maestro la tiene exacta.

Los otros 2 469 son el problema, y su procedencia no la sabemos: no siguen los pesos documentados del generador (0,40 / 0,40 / 0,15 / 0,05) ni la regla de `clean_impute_dataset.py` de mandar a `"1"` todo lo que no sea numérico. Lo verificable es que la ficha no los jerarquiza y el maestro sí.

**El efecto es grande y va en una sola dirección.** Entre esos 2 469, el maestro asigna jerarquía 3 o 4 a **1 265 recursos**. En la realidad hay **172 recursos de jerarquía 3 o 4 en todo el Perú** — 157 de nivel 3 y 15 de nivel 4. El relleno multiplicó por siete el patrimonio de primer nivel del país, y esa inflación sostenía la cifra de dispersión que este documento publicó hasta ahora: 451 contra 203, cuando las reales son 115 contra 49.

**Lección de método.** Cuatro pruebas estadísticas independientes y significativas no equivalen a una comparación contra la fuente. Cuando la fuente existe, la comparación fila a fila es la primera prueba, no la última; las pruebas agregadas se reservan para cuando la fuente no está disponible, y su resultado es una presunción, no una verificación. `code/verificar_fichas.py` reproduce todo lo anterior.

**`TIPO_INGRESO` y `EPOCA_PROPICIA` no sobrevivieron.**

- `TIPO_INGRESO` es hoy una función determinista de `JERARQUIA_OFICIAL`: jerarquía 1-2 → "Libre" (4 721 recursos), jerarquía 3-4 → "Pagado" (1 439). Sin una sola excepción en 6 160 registros. No aporta información independiente; usar ambas variables en un modelo es usar la misma dos veces.
- `EPOCA_PROPICIA` es una función determinista de `ZONA_CLIMATICA` y toma tres valores. Los 1 245 recursos sin coordenadas caen todos en "Todo el año", lo que declara viable los doce meses a cada fiesta patronal del inventario — lo contrario de lo que se quería modelar.

Ambas quedan fuera del modelado en esta entrega.

**La extracción real ya está hecha.** `code/scraper_mincetur_v3.py` recorrió las 6 160 fichas y `fichas_mincetur.csv` trae `INGRESO_TIPO`, `TARIFA_SOLES` y `EPOCA_PROPICIA` con valores de la ficha. La cobertura es del 74 %, y ese 26 % faltante resultó ser **estructural, no un fallo del extractor**:

| Categoría | Fichas | Sin esos campos | % |
|---|---:|---:|---:|
| 5. Acontecimientos programados | 749 | 749 | 100,0 |
| 3. Folclore | 824 | 820 | 99,5 |
| 2. Manifestaciones culturales | 2 105 | 11 | 0,5 |
| 1. Sitios naturales | 2 147 | 9 | 0,4 |
| 4. Realizaciones técnicas | 304 | 0 | 0,0 |

Una danza o una fiesta patronal no tiene acceso en kilómetros ni época propicia porque no es un lugar. Los tres campos faltan en las mismas fichas con un solapamiento del 96,2 %, que es la firma de una causa estructural y no de un parser que se cae. La integración al dataset maestro, con columna `ORIGEN_JERARQUIA` para distinguir extraído de imputado, es la tarea de la Semana 7.

### 3.1.1 Un script que hay que retirar del pipeline

`code/build_master_dataset.py` contiene esto:

```python
def infer_mock_scraped_data(zona_climatica, altitud):
    # Simulador hiperrealista del resultado del web scraping
    ingreso   = random.choices(["Libre", "Pagado"], weights=[0.7, 0.3])[0]
    jerarquia = random.choices(["1","2","3","4"], weights=[0.4,0.4,0.15,0.05])[0]
```

Genera jerarquía y tipo de ingreso **al azar** y escribe sobre el mismo archivo de salida que el scraper real. Las pruebas de arriba confirman que no es el script que produjo el dataset final — pero sigue en el repositorio, sin aviso, apuntando al mismo destino. Cualquiera que lo ejecute destruye la extracción real, y cualquiera que lo lea concluirá que los datos son inventados.

Queda marcado en su encabezado como código superado y fuera del pipeline reproducible descrito en §9.

### 3.2 Error conocido de la altitud

La altitud del modelo de elevación se contrastó contra la altitud oficial de las fichas: desviación de **+16 a −38 m** en meseta y valle, y hasta **+250 m** en cañón, donde el modelo digital suaviza el relieve. Es aceptable para clasificar pisos ecológicos y para filtrar por tope de altitud tolerada; no lo es para cálculos de desnivel acumulado.

---

## 4. Análisis espacial

### 4.1 Altitud

| Estadístico | Valor |
|---|---:|
| Media | 2 117 m |
| Mediana | 2 407 m |
| Desviación estándar | 1 624 m |
| Mínimo / Máximo | 0 m / 6 692 m |
| Recursos sobre 3 500 m | 1 310 (26,7 %) |
| Recursos sobre 4 000 m | 546 (11,1 %) |

La distribución es **bimodal**: una masa costera cerca del nivel del mar y otra andina entre 2 500 y 4 000 m. El primer cuartil está en 291 m y la mediana en 2 407 m — no hay un "centro" del que hablar. Esto justifica que la altitud entre como variable de agrupamiento y no como covariable de ajuste.

También justifica el campo de altitud máxima tolerada en la interfaz: uno de cada cuatro recursos del inventario está por encima de los 3 500 m, umbral a partir del cual el mal de altura deja de ser una anécdota.

### 4.2 Lejanía

| Estadístico | Valor |
|---|---:|
| Media | 74,4 km |
| Mediana | 63,6 km |
| Máximo | 450,6 km |
| Correlación con altitud | −0,088 |

La correlación con la altitud es prácticamente nula. **Altitud y lejanía son dos ejes independientes del problema:** hay recursos altos y cercanos a su capital, y recursos bajos y remotos. Ninguna de las dos puede sustituir a la otra, y esto valida incluir ambas en el vector de características.

### 4.3 Concentración

| | Recursos | % |
|---|---:|---:|
| Lima y Cusco | 1 585 | 25,7 % |
| Resto de las 23 regiones | 4 575 | **74,3 %** |

Sobre los geolocalizables: 1 133 en Lima o Cusco (23,1 %) y 3 782 fuera (76,9 %). Este es el número que sostiene la tesis de dispersión del producto, y el que las métricas de cobertura de `ModelSelection.md` §6.3 deben verificar.

---

## 5. Análisis climático

Serie histórica mensual 2014–2023 de Open-Meteo Archive: 24 regiones × 10 años × 12 meses = **2 880 observaciones**, con temperatura media y precipitación total.

### 5.1 La estacionalidad es real y es enorme

Precipitación media mensual (mm), promedio de diez años:

| Región | Ene | Feb | Mar | Abr | May | Jun | Jul | Ago | Sep | Oct | Nov | Dic |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Cusco** | 228 | 202 | 154 | 76 | 36 | **8** | 12 | 22 | 37 | 84 | 125 | 193 |
| **Áncash** | 217 | 202 | **265** | 147 | 63 | 23 | 21 | 36 | 98 | 163 | 141 | 201 |
| **Arequipa** | 132 | 165 | 117 | 27 | 1 | 1 | 1 | 1 | 1 | 4 | 5 | 27 |
| **Ica** | 22 | 22 | 19 | 3 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 3 |
| **Loreto** | 243 | 227 | 316 | 317 | 279 | 190 | **167** | 152 | **128** | 186 | 249 | 275 |

Tres lecturas que el producto necesita:

1. **Cusco varía 28 veces entre enero (228 mm) y junio (8 mm).** Recomendar Cusco sin preguntar el mes no es una simplificación: es un error.
2. **Ica es plano todo el año.** Hay destinos donde la estacionalidad no discrimina, y el sistema no debe penalizarlos por defecto.
3. **Loreto nunca baja de 128 mm.** En selva no existe un "mes seguro"; existe un mes menos malo. Un umbral absoluto de precipitación marcaría la selva como inviable los doce meses, lo que sería inútil para el usuario.

### 5.2 Distribución del riesgo discretizado

`NIVEL_RIESGO_CLIMATICO` discretiza la precipitación en tres niveles: 1 293 observaciones `1_Seguro`, 618 `2_Precaución`, 969 `3_Peligro`.

Meses-región en nivel `3_Peligro`, extremos: Loreto 117, Ucayali 87, San Martín 83, Madre de Dios 75, Áncash 73 — frente a La Libertad 1, Moquegua 3, Lambayeque 4, Piura 7. **Tres regiones no registran ningún mes en nivel de peligro.**

### 5.3 Limitación: la región no es una unidad climática

Este es el punto débil del análisis climático y hay que declararlo. **Arequipa va del nivel del mar a más de 6 000 m.** Un promedio regional mezcla costa desértica con puna, y el propio dataset maestro reconoce siete pisos ecológicos distintos dentro del país.

El caso más claro está en los datos: el conglomerado 8 del modelo (§ `ModelSelection.md`) agrupa 215 recursos con altitud media de **4 096 m cuya región modal es Lima**. La sierra de Lima —Yauyos, Huarochirí— es puna, y el promedio climático de "Lima" está dominado por la costa.

**Mitigación para la Semana 7:** cruzar la climatología por `REGIÓN × ZONA_CLIMATICA` en lugar de solo por región. Los datos ya lo permiten; el pipeline aún no lo hace.

### 5.4 Precisión terminológica

La serie histórica es **climatología**, no pronóstico. Describe el comportamiento medio observado de diez años, no predice un mes concreto. Para el producto es suficiente y apropiado —un viajero que planifica con dos meses de anticipación necesita la norma, no el pronóstico— pero los documentos deben decir "viabilidad climática histórica" y no "forecasting". Del mismo modo, un umbral de precipitación media no es un modelo de huaicos: **no hay ninguna fuente de eventos extremos en este pipeline.**

---

## 6. Los eventos: la oportunidad que los datos señalan

Los 749 Acontecimientos Programados del inventario se desglosan así:

| Subtipo | Registros |
|---|---:|
| Fiestas religiosas y patronales | 393 |
| Festivales | 117 |
| Fiestas tradicionales (herranza, carnavales) | 117 |
| Otros | 67 |
| Ferias (no artesanales) | 23 |
| Danza, concursos, deportivos, teatro, música | 32 |

**MINCETUR documenta que el evento existe, pero el CSV de datos abiertos no publica cuándo ocurre.** No hay columna de fecha, y solo el 2 % de los nombres menciona un mes. De los 749, además, 582 no tienen coordenadas.

Esto define un vacío de datos con una única fuente posible: **el municipio que organiza el evento es la única entidad que conoce su fecha y su ubicación exacta.** Ningún scraping lo resuelve. Es el fundamento del lado de la oferta descrito en `ProjectProposal.pdf` y el motivo por el que el prototipo de eventos existe, aunque hoy se alimente de datos simulados.

---

## 7. Hallazgos principales

1. **El faltante tiene significado.** El 20,2 % sin coordenadas son prácticas y eventos, no errores; tratarlos como ruido habría eliminado el 12 % del inventario que más potencial comercial tiene.
2. **Altitud y lejanía son ejes independientes** (r = −0,088). Ambos entran al modelo.
3. **La estacionalidad es de primer orden, no un ajuste fino.** Un factor de 28× en Cusco entre enero y junio.
4. **La división política no describe la geografía turística.** Se demuestra cuantitativamente en `ModelSelection.md`: la partición por región obtiene silueta negativa.
5. **Hay más patrimonio de primer nivel fuera del circuito que dentro, y hay mucho menos del que creíamos.** Con la jerarquía verificada contra la ficha oficial, en todo el inventario hay 172 recursos de jerarquía 3 o 4. De los que caen dentro de un polo, **115 están fuera del circuito saturado y 49 dentro** — un reparto de 70/30 a favor del resto del país. La proporción sostiene la tesis: el desbalance de la demanda no se explica por dónde está lo importante. La magnitud anterior (451 contra 203) venía del 40 % de jerarquías sin respaldo descrito en §3.1.
6. **La extracción de fichas ya está hecha y cambia el diagnóstico.** `fichas_mincetur.csv` trae 6 129 fichas con jerarquía, tipo de ingreso, tarifa, actividades, accesos y visitantes, con 31 errores (0,5 %). `JERARQUIA_OFICIAL` del maestro resultó real en el 59,7 % y sin respaldo en el resto (§3.1). La deuda técnica pasa de «extraer» a «integrar al maestro con trazabilidad de origen».

## 8. Limitaciones declaradas

| Limitación | Efecto | Plan |
|---|---|---|
| `TIPO_INGRESO` y `EPOCA_PROPICIA` sobrescritas | Sin aproximación al costo ni estacionalidad por recurso | Re-ejecutar el scraper con trazabilidad de origen · Semana 7 |
| 2 469 jerarquías del maestro sin respaldo en la ficha oficial | Inflaban por siete el patrimonio de jerarquía 3-4; las cifras que dependían de ellas ya están corregidas | Reemplazar la columna por `FICHA_JERARQUIA_NUM` + `ORIGEN_JERARQUIA` · Semana 7 |
| 1 240 recursos dentro de polos sin jerarquía oficial (25,9 %) | El puntaje del polo promedia sobre los que sí la tienen; 10 de 222 polos quedan fuera del ranking por cobertura insuficiente | Política documentada en `ModelSelection.md` §6.4 · no se imputa |
| `build_master_dataset.py` genera datos al azar | Escribe sobre la salida del scraper real; destruye la extracción si se ejecuta | Retirado del pipeline y marcado en el encabezado |
| Climatología por región, no por piso ecológico | 24 de 81 polos recibían el clima de otro piso ecológico: el polo de la sierra de Lima, a 4 058 m de altitud media, heredaba el clima de la costa limeña | `code/fetch_climate_v2.py` descarga 88 puntos región × zona climática y cubre el 99,3 % de los recursos · pendiente de ejecutar |
| Altitud del modelo digital de elevación | Hasta +250 m de error en cañón | Contrastar con altitud oficial de la ficha |
| Distancias geodésicas, no viales | Subestima el tiempo real de traslado | Red vial de OpenStreetMap · Semana 10 |
| Sin precios por recurso | El costo mostrado es estimación, nunca tarifa | `TIPO_INGRESO` real vía ficha oficial |
| Dataset de eventos simulado | No admite ninguna afirmación empírica | Sembrar con los 749 eventos reales del inventario |

---

## 9. Reproducir

```bash
pip install pandas scikit-learn matplotlib requests beautifulsoup4

python code/fetch_climate_history.py     # clima histórico de Open-Meteo
python code/discretize_climate.py        # discretización del riesgo
python code/build_master_dataset.py      # ensamblado del dataset maestro

python code/ta01_comparativa_modelos.py data/processed/dreemgo_master_dataset.csv
python code/ta01_modelo_final.py        data/processed/dreemgo_master_dataset.csv
```

Los dos últimos scripts regeneran todas las cifras de `ModelSelection.md` y la figura `ta01_seleccion_modelo.png`.

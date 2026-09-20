# DreemGO — Selección de Modelo

**Semana 6** · DS3022 Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Equipo: Miguel · Alejandro · Diego · Christopher
Entrega: 16 de septiembre de 2026

---

## 1. Qué problema resuelve el componente analítico

DreemGO no responde "¿qué hay cerca?". Responde **"¿qué conjunto de destinos puedo recorrer en los días que tengo, en el mes en que viajo, según lo que me interesa?"**. Eso se descompone en tres tareas, y solo la primera es un problema de aprendizaje.

| Tarea | Tipo | Estado en esta entrega |
|---|---|---|
| **TA-01** Agrupamiento espacio-temporal de destinos | Aprendizaje no supervisado | **Implementada, auditada y rehecha (v2)** |
| **TA-02** Ingeniería de variables geoespaciales | Derivación determinista | Implementada (Semana 5) |
| **TA-03** Extracción de fichas oficiales | Extracción | Parcial — ver `DataAnalysis.md` §3.1 |
| **Ordenamiento de la ruta** | Optimización combinatoria | Especificada, Semana 10 |

Este documento cubre **TA-01**.

### 1.1 Por qué no supervisado

El producto arranca **sin etiquetas y sin interacciones de usuario**: no hay clics, ni valoraciones, ni itinerarios históricos que aprender. Es un arranque en frío estricto. Eso descarta de entrada el filtrado colaborativo y cualquier modelo supervisado de relevancia, y deja el agrupamiento por estructura como la vía disponible.

No es una limitación que se compense con un modelo más grande: es una ausencia de datos. La capa supervisada (learning-to-rank sobre itinerarios aceptados) queda condicionada a que el prototipo de la Semana 10 genere uso real.

### 1.2 Qué debe cumplir un buen conglomerado

Un agrupamiento es útil para este producto si cumple dos cosas a la vez:

1. **Cohesión estadística** — los recursos de un grupo se parecen entre sí en el espacio de características.
2. **Recorribilidad** — un viajero puede visitar varios recursos del grupo en un mismo viaje.

La segunda no la miden ni la silueta ni Davies-Bouldin, y resultó ser la que decide: el modelo que gana en cohesión produce polos de hasta doce horas de punta a punta (§5.7). La medimos con el **diámetro** del polo, y el modelo final la garantiza por construcción en lugar de reportarla después.

---

## 2. Datos de entrada

**4 915 recursos geolocalizables** del Inventario Nacional de Recursos Turísticos (MINCETUR), de un total de 6 160. Los 1 245 excluidos son las prácticas y eventos sin coordenada documentados en `DataAnalysis.md` §2.2.

| Variable | Tipo | Papel |
|---|---|---|
| `latitud`, `longitud` | Continua | Estructura geográfica — define qué es encadenable |
| `ALTITUD` | Continua (0–6 692 m) | Separa pisos ecológicos y condiciona el esfuerzo del viaje |
| `INDICE_COSTO_LOGISTICO` | Ordinal 1–3 | Accesibilidad respecto de la capital regional |

Para los candidatos 1 y 2 se estandarizan con `StandardScaler`, de modo que la altitud (rango de miles) no quede aplastada por la latitud (rango de decenas). El candidato 3 no usa ese espacio: opera sobre una matriz de distancias de viaje en kilómetros (§3).

**Variables deliberadamente excluidas del vector de agrupamiento:**

- `TIPO_INGRESO` y `EPOCA_PROPICIA`, por ser funciones deterministas de otras columnas (`DataAnalysis.md` §3.1). Incluirlas sería introducir la misma información dos veces.
- `JERARQUIA_OFICIAL`, que **sí es un dato real y verificado**, pero mide importancia y no ubicación. Meterla en el espacio de agrupamiento produciría polos de «cosas importantes repartidas por 400 km», que es justo lo que el producto no puede recomendar. Entra en el sistema como capa de ordenamiento sobre polos ya formados (§6.5).

**Salida:** una etiqueta de polo por recurso, más los recursos que no alcanzan el tamaño mínimo de polo.

---

## 3. Modelos evaluados

### Baseline 1 · Partición por REGIÓN
La división política del Perú, 25 grupos. Es el baseline correcto porque es **lo que hace hoy cualquier buscador turístico**: te muestra los atractivos del departamento. Si el modelo no le gana, el modelo no aporta.

### Baseline 2 · Partición por REGIÓN × CATEGORÍA
La taxonomía oficial de MINCETUR cruzada con la región, 114 grupos. Baseline más exigente: usa la clasificación que la propia fuente considera relevante.

### Candidato 1 · K-Means
Particional, número de grupos fijado de antemano, grupos convexos y de tamaño comparable. Ventaja: interpretable y determinista. Desventaja: obliga a asignar cada recurso a algún grupo, aunque esté aislado en medio del desierto.

Barrido de k de 4 a 30.

### Candidato 2 · HDBSCAN
Jerárquico basado en densidad. No exige fijar el número de grupos, admite grupos de forma y tamaño arbitrarios, y —lo decisivo para este producto— **puede declarar un recurso como ruido en vez de forzarlo a un grupo**.

Barrido de `min_cluster_size` en {15, 25, 40, 60, 90}.

### Candidato 3 · Enlace completo sobre distancia de viaje

Agrupamiento jerárquico aglomerativo con **enlace completo**, sobre una distancia que no es la euclídea del espacio de características sino el esfuerzo de viaje entre dos recursos:

```
d_viaje(i, j) = √( haversine(i, j)²  +  (|altitud_i − altitud_j| · k)² )       k = 0,06 km/m
```

Con k = 0,06, mil metros de desnivel pesan como sesenta kilómetros de llano. El valor sale de un barrido conjunto de (umbral, k) buscando que ningún polo supere ~1 300 m de rango altitudinal, porque el usuario declara una altitud máxima tolerada y un polo que va de 200 a 4 000 m le sirve a medias.

La propiedad que lo hace candidato: **el enlace completo acota el diámetro del conglomerado por construcción.** Si el umbral es D, ningún par de recursos del mismo polo supera D. No es una métrica que se reporta después del ajuste; es una garantía del algoritmo.

Barrido del umbral en {60, 80, 100, 120} km de viaje efectivo.

---

## 4. Métricas

| Métrica | Qué mide | Dirección |
|---|---|---|
| **Coeficiente de silueta** | Cohesión interna frente a separación entre grupos | Mayor es mejor (−1 a 1) |
| **Índice Davies-Bouldin** | Razón entre dispersión interna y separación | **Menor** es mejor |
| **Calinski-Harabasz** | Razón de varianza entre e intra grupos | Mayor es mejor |
| **Radio medio (km)** | Distancia Haversine media de cada recurso al centroide geográfico de su grupo | **Menor** es mejor |
| **Diámetro (km)** | Distancia Haversine entre los dos recursos más separados del grupo | **Menor** es mejor |

Las dos últimas son **métricas de producto**: traducen el resultado a la pregunta que importa, que es si un viajero puede recorrer el polo.

**El radio no basta, y esa fue una equivocación de una versión anterior de este documento.** El radio mide la dispersión alrededor del centro; el diámetro mide el tamaño del polo. Un conglomerado con muchos recursos apiñados cerca del centroide y unos pocos lejos puede tener radio pequeño y diámetro enorme — que es exactamente lo que pasaba (§5.7). Para un itinerario, lo que limita es el diámetro: la parada más lejana de la otra punta.

Para leer el diámetro en términos de viaje usamos una conversión declarada: **40 km/h de velocidad media en carretera andina con factor de sinuosidad 1,6**, es decir unos 25 km geodésicos por hora de viaje real.

---

## 5. Resultados

### 5.1 Primera comparativa, y por qué no vale tal cual

| Modelo | Grupos | Aislados | Silueta ↑ | Davies-Bouldin ↓ | Radio medio ↓ |
|---|---:|---:|---:|---:|---:|
| Baseline · REGIÓN | 25 | 0 | −0,0446 | 3,2627 | 72,8 km |
| Baseline · REGIÓN × CATEGORÍA | 114 | 0 | −0,3734 | 6,7304 | 69,3 km |
| K-Means k=29 | 29 | 0 | 0,4736 | 0,7732 | 115,5 km |
| HDBSCAN mcs=15 | 81 | 1 155 | 0,6573 | 0,4186 | 30,2 km |

Esta tabla favorece a HDBSCAN por dos motivos que no tienen que ver con el modelo:

1. **Distinto número de grupos.** HDBSCAN forma 81 y el K-Means elegido, 29. Tanto la silueta como el radio mejoran casi siempre al aumentar el número de grupos, así que la fila de HDBSCAN parte con ventaja.
2. **Distinto número de puntos evaluados.** La silueta de HDBSCAN se calcula solo sobre los 3 760 recursos que agrupó, descartando los 1 155 que marcó como aislados — que son justamente los más difíciles. K-Means y los baselines se evalúan sobre los 4 915.

La §5.2 corrige ambas cosas. Dejamos esta tabla porque es la que produce la ejecución directa del barrido, y porque explicar por qué no basta es parte del criterio de selección.

### 5.2 Comparación controlada

**Mismo subconjunto de puntos (los 3 760 que HDBSCAN agrupa) y número de grupos comparable:**

| Modelo | Grupos | Silueta ↑ | Davies-Bouldin ↓ | Radio medio ↓ |
|---|---:|---:|---:|---:|
| **HDBSCAN mcs=15** | 81 | **0,6573** | **0,419** | **30,2 km** |
| K-Means k=81 | 74 | 0,6260 | 0,570 | 39,3 km |
| Baseline · REGIÓN | 25 | −0,0287 | 2,868 | 68,6 km |

HDBSCAN sigue ganando, pero la ventaja real sobre K-Means es de 0,657 frente a 0,626 en silueta — no la brecha de 0,657 frente a 0,474 que sugería la primera tabla.

**Sobre los 4 915 puntos, obligando a HDBSCAN a tratar su ruido como un grupo más:**

| Modelo | Grupos | Silueta ↑ | Davies-Bouldin ↓ |
|---|---:|---:|---:|
| K-Means k=81 | 81 | **0,5366** | **0,680** |
| HDBSCAN + ruido como grupo | 82 | 0,3144 | 1,034 |
| Baseline · REGIÓN | 25 | −0,0446 | 3,263 |

Aquí HDBSCAN pierde, y por bastante. **Toda su ventaja depende de que se le permita no clasificar el 23,5 % del inventario.** Eso no invalida la elección —§6.1 argumenta por qué descartar es lo correcto en este producto— pero sí obliga a enunciarla así: HDBSCAN no agrupa mejor, agrupa mejor *lo que se puede agrupar*.

### 5.3 Los baselines administrativos pierden en cualquier configuración

Silueta negativa bajo las tres formas de medir: −0,0446 sobre el conjunto completo, −0,0287 sobre el subconjunto agrupado, y −0,3734 al cruzar con la taxonomía.

Una silueta negativa quiere decir que el recurso promedio queda más cerca de los recursos de otro grupo que de los de su propio grupo. En términos del producto: **dos recursos del mismo departamento pueden estar a 400 km y a 4 000 m de desnivel, y dos recursos de departamentos distintos pueden estar a media hora de camino.**

Con una salvedad honesta: la silueta se mide en el mismo espacio de características que los algoritmos de agrupamiento optimizan, así que parte del resultado es esperable por construcción. Lo que sí es independiente de esa crítica es el radio medio en kilómetros, que se calcula sobre coordenadas sin estandarizar: 68,6 km para la partición por región frente a 30,2 km del modelo seleccionado, sobre los mismos recursos.

### 5.4 El radio medio depende del número de grupos

Escribí en un borrador anterior que el radio de K-Means era peor que el del baseline y que esa métrica «nos salvó de elegir mal». Es falso, y el barrido lo muestra:

| k (K-Means) | Silueta | Radio medio |
|---:|---:|---:|
| 25 | 0,4498 | 130,1 km |
| 29 | 0,4736 | 115,5 km |
| 48 | 0,5123 | 78,0 km |
| 81 | 0,5366 | 51,1 km |
| 120 | 0,5572 | 36,1 km |

El radio cae de forma monótona al subir k. Con 29 grupos K-Means daba 115,5 km; con 81 da 51,1 km. La comparación original no medía la calidad del algoritmo, medía **cuántos grupos tenía cada uno**.

El radio sigue sirviendo, pero solo con el número de grupos controlado: a 81 grupos, HDBSCAN da 30,2 km y K-Means 39,3 km.

### 5.5 Estabilidad del parámetro

`min_cluster_size` se eligió por silueta, que es la misma métrica que después se reporta. Para descartar que el resultado sea una casualidad del valor elegido:

| `min_cluster_size` | Grupos | Aislados | Silueta | Radio medio |
|---:|---:|---:|---:|---:|
| 10 | 121 | 1 094 | 0,6334 | 26,3 km |
| 12 | 100 | 1 276 | 0,6604 | 26,6 km |
| **15** | **81** | **1 155** | **0,6573** | **30,2 km** |
| 18 | 67 | 1 225 | 0,6416 | 33,0 km |
| 20 | 63 | 1 253 | 0,6401 | 35,2 km |
| 22 | 57 | 1 336 | 0,6350 | 36,9 km |

Entre 10 y 22 la silueta se mueve en una banda estrecha (0,633–0,660). **El número de polos varía mucho y la calidad del agrupamiento casi nada**, lo que indica una estructura jerárquica real: los polos se anidan, y `min_cluster_size` elige a qué altura del árbol se corta. La elección de 15 es una decisión de producto —polos de al menos quince recursos, que es lo mínimo para armar un itinerario de varios días— y no un óptimo numérico.

Por encima de 25 la estructura colapsa: a mcs=40 la silueta cae a 0,171 y el radio sube a 263 km.

### 5.6 Ablación: ¿aportan las variables de TA-02?

| Variables | Grupos | Aislados | Silueta |
|---|---:|---:|---:|
| latitud, longitud | 87 | 1 471 | **0,6858** |
| latitud, longitud, altitud, índice | 81 | **1 155** | 0,6573 |
| latitud, longitud, altitud | 67 | 1 817 | 0,5887 |

Resultado incómodo y hay que decirlo: **solo con latitud y longitud la silueta es más alta que con las cuatro variables.** La altitud y el índice de lejanía no mejoran la métrica.

Se conservan igual, por dos razones concretas:

1. **Cobertura.** Con las cuatro variables quedan 1 155 recursos sin polo; solo con coordenadas, 1 471. Las variables de TA-02 permiten agrupar 316 recursos más.
2. **El producto pregunta por altitud.** La interfaz tiene un campo de altitud máxima tolerada y el 26,7 % del inventario está sobre 3 500 m. Un agrupamiento puramente planar juntaría un recurso a 200 m con otro a 4 000 m por estar cerca en el mapa, que es precisamente el error que el producto dice evitar.

Es un intercambio explícito entre cohesión estadística y utilidad, resuelto a favor de la segunda.

### 5.7 El radio escondía la cola

Con el modelo de §5.2 elegido, una revisión adversaria posterior midió el **diámetro** de cada polo, que hasta entonces no se había calculado. El resultado invalidó la lectura optimista del radio:

| | HDBSCAN mcs=15 |
|---|---:|
| Radio medio ponderado | 30,2 km |
| **Diámetro · mediana** | **65,0 km** |
| **Diámetro · p90** | **215,4 km** |
| **Diámetro · máximo** | **427,9 km** |

**30 de los 81 polos superaban los 100 km de diámetro**, y los más grandes eran justamente los que concentraban recursos:

| Polo | Recursos | Diámetro | Desnivel | Región dominante | Horas de punta a punta |
|---:|---:|---:|---:|---|---:|
| 62 | 234 | 298 km | 2 197 m | Áncash | ~11,9 h |
| 48 | 204 | 315 km | 2 194 m | Lima | ~12,6 h |
| 45 | 125 | 271 km | 2 337 m | Cajamarca | ~10,9 h |

Un polo de doce horas de punta a punta y dos mil metros de desnivel no es un polo: es una macrorregión con otro nombre. El titular «radio medio 30,2 km» describía los polos pequeños, que eran la mitad, y no los que contenían los recursos.

La causa es el algoritmo, no el ajuste: **HDBSCAN optimiza densidad, y nada en su criterio acota la extensión de un grupo.** Una cadena de recursos densamente conectados puede estirarse cuatrocientos kilómetros sin que la densidad se rompa.

### 5.8 La silueta no puede decidir esta elección

Al comparar el candidato 3 contra HDBSCAN apareció algo que obliga a reinterpretar toda la §5.2:

| | Espacio estandarizado (lo que optimiza HDBSCAN) | Métrica de viaje (lo que importa al producto) |
|---|---:|---:|
| HDBSCAN mcs=15 | **0,657** | 0,366 |
| Enlace completo D≤80 | 0,160 | **0,462** |

**Cada modelo gana en el espacio que optimiza.** La silueta no es un árbitro neutral entre algoritmos que optimizan cosas distintas: es una medida de cohesión *relativa a una métrica*, y elegir la métrica es elegir el ganador.

Esto no invalida los baselines de §5.3 —la partición administrativa pierde en ambos espacios y también en kilómetros— pero sí obliga a que la elección entre candidatos se decida por criterios de producto, no por el número de silueta.

### 5.9 Barrido del umbral de diámetro

| Umbral (km de viaje) | Polos | Recursos | Cobertura | Diám. mediana | Diám. máximo | Desnivel mediana |
|---:|---:|---:|---:|---:|---:|---:|
| 60 | 290 | 4 625 | 75,1 % | 37,0 km | 59,7 km | 460 m |
| **80** | **222** | **4 786** | **77,7 %** | **52,6 km** | **79,4 km** | **642 m** |
| 100 | 174 | 4 848 | 78,7 % | 64,5 km | 99,3 km | 808 m |
| 120 | 141 | 4 871 | 79,1 % | 76,1 km | 117,9 km | 1 004 m |

A 80 km de viaje efectivo ningún polo pasa de **3,2 horas** de punta a punta ni de **1 296 m** de rango altitudinal, y se conserva el 77,7 % del inventario. Subir a 100 gana 0,9 puntos de cobertura a cambio de polos de cuatro horas; bajar a 60 los deja en dos horas y media pero pierde 161 recursos.

---

## 6. Modelo seleccionado

> **Enlace completo sobre distancia de viaje, umbral 80 km, tamaño mínimo 5 recursos.**

![Selección de modelo TA-01 v2](./docs/ta01_seleccion_modelo_v2.png)

| | v1 · HDBSCAN mcs=15 | **v2 · enlace completo D≤80** |
|---|---:|---:|
| Polos | 81 | **222** |
| Recursos en un polo | 3 760 (61,0 %) | **4 786 (77,7 %)** |
| No encadenables en una ruta | 2 400 (39,0 %) | **1 374 (22,3 %)** |
| Diámetro · mediana | 65,0 km | **52,6 km** |
| Diámetro · p90 | 215,4 km | **69,5 km** |
| **Diámetro · máximo** | **427,9 km · 17,1 h** | **79,4 km · 3,2 h** |
| Desnivel · máximo | 4 667 m | **1 296 m** |
| Polos de más de 4 h | ~15 | **0** |
| Tamaño mediano | 32 recursos | 14 recursos |

**Mil veintiséis recursos más quedan disponibles para el producto.** El techo que documentaba la versión anterior —39 % del inventario fuera de cualquier itinerario— baja a 22,3 %.

### 6.1 Por qué se cambió de algoritmo

No fue un problema de ajuste de parámetros. HDBSCAN con `min_cluster_size=10` seguía dando un diámetro máximo de 404 km. La densidad no acota extensión, y este producto necesita acotar extensión.

El enlace completo la acota por definición: la distancia entre dos conglomerados es la de su par más lejano, así que fusionar dos grupos solo ocurre si **todos** sus pares quedan bajo el umbral. Lo que en la mayoría de aplicaciones es una desventaja —el enlace completo es sensible a los extremos— aquí es exactamente la propiedad que se busca, porque el extremo es el viajero que tiene que cruzar el polo.

### 6.2 Qué se pierde

**La silueta en el espacio estandarizado cae de 0,657 a 0,160.** Es real y hay que decirlo. Los polos de v2 no son «bonitos» en el espacio de características: son compactos en kilómetros de viaje, que es otra cosa.

En la métrica que el producto usa, la relación se invierte: 0,462 contra 0,366 (§5.8).

**Se pierde también la señal de aislamiento.** HDBSCAN marcaba 1 155 recursos como ruido y eso era información útil: «este recurso no se encadena con nada». En v2 solo quedan fuera 129 recursos, los que no alcanzan el mínimo de cinco. Para recuperar esa señal, un polo de exactamente cinco o seis recursos ya funciona como aviso de que la oferta local es delgada.

### 6.3 Los polos son interpretables y caben en un día

| | |
|---|---:|
| Diámetro mediano | 52,6 km (~2,1 h) |
| Diámetro p90 | 69,5 km (~2,8 h) |
| Desnivel mediano | 642 m |
| Polos que cruzan más de una región | 62 de 222 (28 %) |

Los 62 polos multirregionales siguen siendo la evidencia directa contra el baseline administrativo: son corredores reales que la partición por departamento no puede ver, y ahora además se sabe que caben en un día de viaje.

### 6.4 El ordenamiento: jerarquía con término de novedad

La jerarquía oficial (`DataAnalysis.md` §3.1) ordena polos ya formados. Pero al medirlo apareció un problema de dirección: **con 23 % de polos que contienen Lima o Cusco en la base, el top 10 por jerarquía pura salía con 60 % de ellos.** La capa de ordenamiento empujaba en contra de la tesis de dispersión del producto.

El término de novedad no es un adorno del documento; es lo que hace que la promesa sea cierta:

```
puntaje = (1 − λ) · jerarquía_normalizada  +  λ · novedad
novedad = 0,5 · (1 − saturación)  +  0,5 · lejanía_normalizada
```

donde *saturación* es la fracción del polo que está en Lima o Cusco y *lejanía* el índice de distancia al hub logístico regional.

| λ | Lima/Cusco en el top 10 | Jerarquía media del top 10 | Regiones representadas |
|---:|---:|---:|---:|
| 0,0 | 60 % | 2,63 | 5 |
| 0,2 | 40 % | 2,62 | 7 |
| **0,3** | **30 %** | **2,58 (−1,9 %)** | **7** |
| 0,4 | 0 % | 2,42 (−8,0 %) | 6 |
| 0,7 | 0 % | 2,30 (−12,5 %) | 7 |

**λ = 0,3 es el valor por defecto:** reduce a la mitad la concentración en el circuito saturado a cambio de menos del 2 % de calidad media, y pasa de cinco a siete regiones en el top 10. Implementado en `code/ta03_score_polo.py`.

### 6.5 Cobertura de catálogo

| | |
|---|---:|
| Polos sin ningún recurso de Lima o Cusco | 172 de 222 (77 %) |
| Recursos en esos polos | 3 470 de 4 786 (73 %) |
| Recursos de jerarquía 3-4 fuera del circuito | 451 contra 203 dentro |

### 6.6 Lo que este modelo NO resuelve

El agrupamiento es espacial. El nombre «espacio-temporal» describe el pipeline completo, no TA-01: en el modelo no entra ninguna variable de tiempo, y el mes del usuario actúa después, como ponderación sobre polos ya calculados.

Tampoco resuelve el perfilamiento por intereses. Medimos si los polos se especializan solos por tipo de destino y la respuesta es *poco*: la mediana de la categoría dominante es 0,60 sobre un inventario ya repartido 40/45 entre Sitios Naturales y Manifestaciones Culturales. Los polos responden a **dónde puedo ir**, no a **qué me gusta**. El filtrado por intereses es una capa aparte, aún sin implementar.

---

## 7. Cómo se integra con el resto del sistema

```
Consulta del usuario
  intereses · mes · días · presupuesto · altitud máxima
        │
        ├─ Filtro duro ─────── altitud máxima tolerada
        │
        ├─ TA-01 ───────────── polos precalculados (enlace completo, offline)
        │
        ├─ Cruce estacional ── REGIÓN × MES → NIVEL_RIESGO_CLIMATICO
        │                      penaliza el puntaje del conglomerado
        │
        ├─ Selección ───────── conglomerado ganador + término de novedad
        │
        ├─ Puntaje ─────────── jerarquía oficial + término de novedad (λ = 0,3)
        │
        └─ Ordenamiento ────── secuencia de paradas (Semana 10)
```

**El agrupamiento corre offline**, no en tiempo de consulta. El mes del usuario no re-entrena nada: reordena polos ya calculados. De ahí sale el requerimiento no funcional de menos de 5 segundos, que sería insostenible si el agrupamiento corriera en cada petición — la matriz de distancias de 4 915 × 4 915 pesa 97 MB y tarda segundos en construirse.

---

## 8. Evaluación futura: el ordenamiento

TA-01 se evalúa con métricas internas porque no hay etiquetas. El componente de ordenamiento sí necesita otra estrategia.

**Problema formal:** Tourist Trip Design Problem, una variante del Team Orienteering Problem con ventanas de tiempo — familia de los problemas del viajante con beneficios. No es un TSP puro: no hay que visitar todos los nodos, sino elegir cuáles y en qué orden, maximizando valor bajo un presupuesto de tiempo.

**Implementación prevista:** heurística de construcción más mejora local, con **vecino más cercano como baseline explícito**. Métrica: distancia total del itinerario frente al baseline.

El cambio a polos acotados hace este problema tratable: ordenar catorce paradas dentro de 80 km es resoluble; ordenar doscientas treinta y cuatro repartidas en 298 km no lo era.

**Evaluación de la recomendación sin verdad de campo:** conjunto de consultas etiquetado a mano por los cuatro integrantes, con acuerdo entre anotadores medido por **kappa de Fleiss** — si no hay acuerdo interno, la etiqueta no vale. Sobre ese conjunto: **Precision@5, nDCG@10 y MRR**, más **cobertura de catálogo y novelty@k** para verificar la promesa de dispersión. Es un gold set pequeño y se declarará como tal.

---

## 9. Limitaciones del modelo

| Limitación | Efecto |
|---|---|
| **Baja silueta en el espacio de características** | 0,160 contra 0,657 de HDBSCAN. Los polos de v2 son compactos en kilómetros de viaje, no en el espacio estandarizado. La elección se sostiene en criterios de producto (§5.8, §6.1). |
| **22,3 % del inventario fuera de ruta** | 1 245 sin coordenada más 129 aislados. El producto opera sobre 4 786 recursos, no sobre 6 160. Mejor que el 39 % de la v1, pero sigue siendo un techo. |
| **El umbral de 80 km es una decisión, no un óptimo** | Sale de traducir el diámetro a horas de viaje con supuestos declarados (40 km/h, sinuosidad 1,6). Con red vial real el umbral habrá que recalibrarlo. |
| **Se perdió la señal de aislamiento** | HDBSCAN marcaba 1 155 recursos como no encadenables; v2 solo 129. Un polo de cinco o seis recursos cumple parcialmente esa función de aviso. |
| **El modelo no sabe de intereses** | Los polos responden a *dónde puedo ir*, no a *qué me gusta* (§6.6). |
| **No hay variable temporal en TA-01** | El agrupamiento es espacial; el mes entra después como ponderación. |
| **Distancias geodésicas** | El diámetro de 80 km es una cota inferior del traslado real. Con red vial el número sube y el umbral baja. |
| **Estacionalidad por región** | 24 de 81 polos de la v1 recibían un perfil climático que no corresponde a su piso ecológico. `code/fetch_climate_v2.py` descarga 88 puntos (región × zona climática) en lugar de 24 y cubre el 99,3 % de los recursos; queda pendiente ejecutarlo. |
| **Fallos del scraper dentro de la jerarquía 1** | La jerarquía es real, pero los recursos donde la extracción falló quedaron mezclados con los de jerarquía 1 legítima. Afecta al ordenamiento de §6.4. |
| **Sin costo real** | El producto pide presupuesto como entrada y no hay ninguna columna monetaria en el dataset. Decisión de producto pendiente. |
| **Sin validación externa** | Todas las métricas son internas. La validación con usuarios está comprometida para la Delivery 1. |

---

## 10. Reproducir

```bash
pip install pandas scikit-learn matplotlib

# v1 · baselines y barridos de K-Means y HDBSCAN  (secciones 5.1 a 5.6)
python code/ta01_comparativa_modelos.py    ../data/processed/dreemgo_master_dataset.csv
python code/ta01_modelo_final.py           ../data/processed/dreemgo_master_dataset.csv
python code/ta01_auditoria_comparacion.py  ../data/processed/dreemgo_master_dataset.csv

# v2 · modelo seleccionado  (secciones 5.7 a 6.3)
python code/ta01_polos_acotados.py         ../data/processed/dreemgo_master_dataset.csv
python code/ta03_score_polo.py             ../data/processed/polos_asignados_v2.csv 0.30
python code/ta01_figura_v2.py              ../data/processed/dreemgo_master_dataset.csv
```

Semilla fija (`random_state=42`); el enlace completo es determinista. Generan `polos_asignados_v2.csv`, `perfil_polos_v2.csv`, `comparativa_polos_v2.csv`, `puntaje_polos.csv` y las figuras. Todas las cifras de este documento salen de esas ejecuciones.

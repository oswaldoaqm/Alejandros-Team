# DreemGO — Selección de Modelo

**Semana 6** · DS3022 Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Equipo: Miguel · Alejandro · Diego · Christopher
Entrega: 16 de septiembre de 2026

---

## 1. Qué problema resuelve el componente analítico

DreemGO no responde "¿qué hay cerca?". Responde **"¿qué conjunto de destinos puedo recorrer en los días que tengo, en el mes en que viajo, según lo que me interesa?"**. Eso se descompone en tres tareas, y solo la primera es un problema de aprendizaje.

| Tarea | Tipo | Estado en esta entrega |
|---|---|---|
| **TA-01** Agrupamiento espacio-temporal de destinos | Aprendizaje no supervisado | **Implementada y evaluada** |
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

La segunda no la miden ni la silueta ni Davies-Bouldin. La añadimos como métrica propia.

---

## 2. Datos de entrada

**4 915 recursos geolocalizables** del Inventario Nacional de Recursos Turísticos (MINCETUR), de un total de 6 160. Los 1 245 excluidos son las prácticas y eventos sin coordenada documentados en `DataAnalysis.md` §2.2.

| Variable | Tipo | Papel |
|---|---|---|
| `latitud`, `longitud` | Continua | Estructura geográfica — define qué es encadenable |
| `ALTITUD` | Continua (0–6 692 m) | Separa pisos ecológicos y condiciona el esfuerzo del viaje |
| `INDICE_COSTO_LOGISTICO` | Ordinal 1–3 | Accesibilidad respecto de la capital regional |

Estandarizadas con `StandardScaler` antes del ajuste, para que la altitud (rango de miles) no quede aplastada por la latitud (rango de decenas).

**Variables deliberadamente excluidas del vector de agrupamiento:**

- `TIPO_INGRESO` y `EPOCA_PROPICIA`, por ser funciones deterministas de otras columnas (`DataAnalysis.md` §3.1). Incluirlas sería introducir la misma información dos veces.
- `JERARQUIA_OFICIAL`, que **sí es un dato real y verificado**, pero mide importancia y no ubicación. Meterla en el espacio de agrupamiento produciría polos de «cosas importantes repartidas por 400 km», que es justo lo que el producto no puede recomendar. Entra en el sistema como capa de ordenamiento sobre polos ya formados (§6.5).

**Salida:** una etiqueta de conglomerado por recurso, más un conjunto de recursos marcados como aislados.

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

---

## 4. Métricas

| Métrica | Qué mide | Dirección |
|---|---|---|
| **Coeficiente de silueta** | Cohesión interna frente a separación entre grupos | Mayor es mejor (−1 a 1) |
| **Índice Davies-Bouldin** | Razón entre dispersión interna y separación | **Menor** es mejor |
| **Calinski-Harabasz** | Razón de varianza entre e intra grupos | Mayor es mejor |
| **Radio medio (km)** | Distancia Haversine media de cada recurso al centroide geográfico de su grupo, ponderada por tamaño | **Menor** es mejor |

La última es la **métrica de producto**. Traduce el resultado a la pregunta que importa: si el radio medio de un polo es de 115 km, no es un polo, es una macrorregión, y un itinerario dentro de él gasta el viaje en carretera.

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

## 6. Modelo seleccionado

> **HDBSCAN con `min_cluster_size = 15`** sobre las cuatro variables geoespaciales estandarizadas.

| | |
|---|---:|
| Conglomerados | **81** |
| Recursos agrupados | 3 760 (76,5 %) |
| Recursos marcados como aislados | 1 155 (23,5 %) |
| Radio medio ponderado | **30,2 km** |
| Radio mediano | **13,9 km** |
| Conglomerados con radio ≤ 30 km | 59 de 81 (73 %) — 2 263 recursos |
| Conglomerados con radio ≤ 50 km | 73 de 81 (90 %) — 3 025 recursos |

Frente al baseline administrativo, sobre el mismo subconjunto de recursos: silueta de −0,029 a **0,657**, Davies-Bouldin de 2,87 a **0,42**, radio medio de 68,6 km a **30,2 km**. Frente a K-Means con el mismo número de grupos: 0,626 → 0,657 en silueta y 39,3 → 30,2 km en radio.

### 6.0 Cuánto del inventario queda fuera de un itinerario

Antes de cualquier virtud del modelo, el número que hay que poner encima de la mesa:

| | Recursos | % del inventario |
|---|---:|---:|
| Sin coordenadas — no ruteables | 1 245 | 20,2 % |
| Agrupables pero aislados por el modelo | 1 155 | 18,8 % |
| **No encadenables en una ruta** | **2 400** | **39,0 %** |
| Sí entran a un polo | 3 760 | 61,0 % |

**Cuatro de cada diez recursos del inventario oficial no pueden formar parte de un itinerario de varias paradas.** Una parte es intrínseca —una danza o una fiesta no tienen coordenada— y otra es una decisión del modelo. Pero el producto no puede prometer «itinerarios sobre los 6 160 recursos del inventario»: opera sobre 3 760.

### 6.1 Por qué el ruido es una ventaja, no un defecto

El 23,5 % de recursos marcados como aislados es, en este producto, **información valiosa y no un fallo**. Un recurso que no pertenece a ningún conglomerado denso es un recurso que no se puede encadenar con otros en un itinerario razonable. Forzarlo a un grupo, como haría K-Means, produciría itinerarios que se ven bien en el mapa y no se pueden cumplir.

En la interfaz, esos recursos no desaparecen: se presentan como **destino único**, no como parada de una ruta. Es la diferencia entre un sistema que sabe lo que no sabe y uno que rellena.

### 6.2 Los conglomerados son interpretables

Los doce más compactos:

| Grupo | Recursos | Altitud media | Radio | Región dominante |
|---:|---:|---:|---:|---|
| 21 | 17 | 4 m | 0,7 km | Callao |
| 28 | 56 | 154 m | 0,8 km | Lima |
| 66 | 23 | 1 506 m | 1,3 km | Pasco |
| 29 | 49 | 76 m | 1,8 km | Lima |
| 23 | 15 | 2 516 m | 2,4 km | Apurímac |
| 25 | 20 | 3 722 m | 2,5 km | Huancavelica |
| 20 | 23 | 3 117 m | 3,3 km | Áncash |
| 11 | 17 | 671 m | 4,4 km | Tacna |
| 13 | 39 | 1 362 m | 4,7 km | Moquegua |
| 6 | 24 | 30 m | 4,7 km | Piura |
| 65 | 41 | 1 822 m | 5,0 km | Pasco |
| 2 | 67 | 98 m | 5,0 km | Loreto |

Se reconocen a simple vista: centros históricos urbanos, valles interandinos, el núcleo de Iquitos. El modelo no inventó categorías: recuperó corredores que existen.

**22 de los 81 conglomerados (27 %) cruzan más de una región.** Son polos reales que la partición por departamento no puede ver, y son la evidencia directa de por qué el baseline falla.

### 6.3 Cobertura de catálogo

La tesis de dispersión del producto exige verificación, no declaración:

| | |
|---|---:|
| Recursos agrupados fuera de Lima y Cusco | 2 929 (77,9 %) |
| Conglomerados 100 % fuera del circuito | 64 de 81 (79 % de los polos) |
| Recursos que viven en esos conglomerados | 2 827 de 3 760 (**75 % de los recursos**) |
| Tamaño medio · polo limpio vs polo con Lima o Cusco | 44,2 vs 54,9 recursos |

La cifra está ponderada por recursos y no solo por polos, porque contar polos puede engañar si los limpios fueran diminutos. No lo son: 75 % de los recursos agrupados está en polos sin ningún recurso de Lima o Cusco, frente al 79 % de los polos. La diferencia entre ambos porcentajes es pequeña.

Un recomendador que elige **entre conglomerados** —y no entre recursos sueltos ordenados por popularidad— tiene 64 salidas posibles sin un solo recurso del circuito saturado. La capacidad estructural de dispersar existe y está medida.

Esto no garantiza que el producto disperse: eso depende de la función objetivo final, que llevará un término explícito de novedad.

### 6.4 La jerarquía oficial como capa de ordenamiento

El agrupamiento dice **dónde** se puede ir. `JERARQUIA_OFICIAL` dice **qué vale la pena** dentro de cada sitio, y al estar verificada como dato real (`DataAnalysis.md` §3.1) puede usarse para ordenar.

Separa polos de forma útil: la jerarquía media por polo va de **1,08 a 2,37**, con desviación estándar de 0,317 entre polos frente a 0,702 dentro de ellos. Hay polos consistentemente más valiosos que otros y no es ruido.

| Polo | Recursos | Jerarquía media | % jerarquía 3-4 | Región dominante |
|---:|---:|---:|---:|---|
| 8 | 35 | **2,37** | 37 % | Puno |
| 22 | 87 | 2,36 | 48 % | Cusco |
| 80 | 18 | 2,33 | 44 % | Cusco |
| 76 | 55 | 2,31 | 35 % | Arequipa |
| 38 | 20 | 2,30 | 30 % | Lambayeque |
| … | | | | |
| 67 | 26 | 1,08 | 0 % | Moquegua |

El polo mejor valorado de todo el país según la fuente oficial —el 8, con jerarquía media 2,37— está en **Puno y no contiene ningún recurso de Lima o Cusco**. De los 64 polos completamente fuera del circuito saturado, 12 tienen jerarquía media igual o superior a 2,0.

Esto convierte la tesis de dispersión en algo verificable con el dato del propio Estado: **hay 451 recursos de jerarquía 3 o 4 fuera de Lima y Cusco, frente a 203 dentro.** La concentración de la demanda no se explica por dónde está el patrimonio importante.

**Uso previsto:** puntaje del polo = f(afinidad con los intereses, viabilidad estacional, jerarquía media, término de novedad). La jerarquía pondera; no filtra. Un recurso de jerarquía 1 que está en el camino sigue apareciendo en el itinerario.

### 6.5 Lo que este modelo NO resuelve

El agrupamiento es espacial. El nombre «espacio-temporal» viene del pipeline completo, no de TA-01: en el modelo no entra ninguna variable de tiempo, y el mes del usuario actúa después, como ponderación sobre polos ya calculados.

El ordenamiento por importancia sí lo cubre la jerarquía oficial (§6.4). Lo que no resuelve es el perfilamiento por intereses, que es la otra mitad de RF-01. Medimos si los polos se especializan por sí solos en algún tipo de destino, y la respuesta es *poco*:

| | |
|---|---:|
| Polos con una categoría por encima del 60 % | 39 de 81 |
| Mediana de la categoría dominante | 0,60 |
| Entropía media por polo vs entropía global | 0,864 vs 1,160 |

Hay algo de especialización temática, pero es un efecto colateral de la geografía y no algo que el modelo busque — y el inventario ya está repartido 40/45 entre Sitios Naturales y Manifestaciones Culturales, así que «categoría dominante por encima del 50 %» dice poco por sí solo.

**Conclusión:** los polos responden a *dónde puedo ir sin perder el viaje en carretera*. No responden a *qué me gusta*. El filtrado por intereses tiene que ocurrir en una capa aparte —perfilamiento semántico sobre los 187 subtipos oficiales y sobre las actividades de la ficha— y esa capa no está implementada en esta entrega.

---

## 7. Cómo se integra con el resto del sistema

```
Consulta del usuario
  intereses · mes · días · presupuesto · altitud máxima
        │
        ├─ Filtro duro ─────── altitud máxima tolerada
        │
        ├─ TA-01 ───────────── conglomerados precalculados (HDBSCAN, offline)
        │
        ├─ Cruce estacional ── REGIÓN × MES → NIVEL_RIESGO_CLIMATICO
        │                      penaliza el puntaje del conglomerado
        │
        ├─ Selección ───────── conglomerado ganador + término de novedad
        │
        └─ Ordenamiento ────── secuencia de paradas (Semana 10)
```

**El agrupamiento corre offline**, no en tiempo de consulta. El mes del usuario no re-entrena nada: reordena conglomerados ya calculados. De ahí sale el requerimiento no funcional de menos de 5 segundos, que sería insostenible si HDBSCAN corriera en cada petición.

---

## 8. Evaluación futura: el ordenamiento

TA-01 se evalúa con métricas internas porque no hay etiquetas. El componente de ordenamiento sí necesita otra estrategia.

**Problema formal:** Tourist Trip Design Problem, una variante del Team Orienteering Problem con ventanas de tiempo — familia de los problemas del viajante con beneficios. No es un TSP puro: no hay que visitar todos los nodos, sino elegir cuáles y en qué orden, maximizando valor bajo un presupuesto de tiempo.

**Implementación prevista:** heurística de construcción más mejora local, con **vecino más cercano como baseline explícito**. Métrica: distancia total del itinerario frente al baseline.

**Evaluación de la recomendación sin verdad de campo:** conjunto de consultas etiquetado a mano por los cuatro integrantes, con acuerdo entre anotadores medido por **kappa de Fleiss** — si no hay acuerdo interno, la etiqueta no vale. Sobre ese conjunto: **Precision@5, nDCG@10 y MRR**, más **cobertura de catálogo y novelty@k** para verificar la promesa de dispersión. Es un gold set pequeño y se declarará como tal.

---

## 9. Limitaciones del modelo

| Limitación | Efecto |
|---|---|
| **La ventaja depende del ruido** | Obligado a clasificar los 4 915 recursos, HDBSCAN cae a 0,314 de silueta y K-Means k=81 lo supera con 0,537. La elección se sostiene en el argumento de producto de §6.1, no en la métrica bruta. |
| **39 % del inventario fuera de ruta** | 1 245 sin coordenada más 1 155 aislados. El producto opera sobre 3 760 recursos, no sobre 6 160. |
| **El modelo no sabe de intereses** | Los polos responden a *dónde puedo ir*, no a *qué me gusta* (§6.5). El perfilamiento semántico es una capa aparte, aún sin implementar. |
| **No hay variable temporal en TA-01** | El agrupamiento es espacial; el mes entra después como ponderación. El nombre «espacio-temporal» describe el pipeline, no el modelo. |
| **La silueta se mide donde el algoritmo optimiza** | Parte de la ventaja sobre los baselines es esperable por construcción. El radio en kilómetros, calculado sobre coordenadas sin estandarizar, es el contraste independiente. |
| **Altitud e índice bajan la silueta** | Se conservan por cobertura (316 recursos más agrupados) y porque el producto pregunta por altitud (§5.6), no porque mejoren la métrica. |
| **Fallos del scraper dentro de la jerarquía 1** | La jerarquía es real, pero los recursos donde la extracción falló quedaron mezclados con los de jerarquía 1 legítima. Afecta al ordenamiento de §6.4, no al agrupamiento. Se corrige con la columna `ORIGEN_JERARQUIA`. |
| **Distancias geodésicas** | Los 30,2 km son una cota inferior del traslado real. Con red vial el número sube. |
| **Estacionalidad por región** | El polo con 215 recursos a 4 096 m de altitud media y región modal Lima recibiría el perfil climático de la costa limeña. |
| **`min_cluster_size` elegido por la métrica que se reporta** | Mitigado con el barrido de §5.5 (banda 0,633–0,660 entre 10 y 22), no con validación en datos retenidos. |
| **Sin validación externa** | Todas las métricas son internas. La validación con usuarios está comprometida para la Delivery 1. |

---

## 10. Reproducir

```bash
pip install pandas scikit-learn matplotlib

# baselines + barrido de k + barrido de min_cluster_size  (secciones 5.1 a 5.4)
python code/ta01_comparativa_modelos.py data/processed/dreemgo_master_dataset.csv

# modelo seleccionado, perfiles, cobertura y figura  (secciones 6.1 a 6.3)
python code/ta01_modelo_final.py data/processed/dreemgo_master_dataset.csv
```

Semilla fija (`random_state=42`). Generan `comparativa_modelos.csv`, `barrido_k.csv`, `perfil_clusters.csv`, `perfil_clusters_hdbscan.csv`, `clusters_asignados.csv` y la figura `ta01_seleccion_modelo.png`. Todas las cifras de este documento salen de esas dos ejecuciones.

# Nota de calidad de datos — Inventario Nacional de Recursos Turísticos

**Producto:** DreemGO · **Equipo:** Alejandro's Team · **Semana 4** · **Fecha de análisis:** 2026-09-02
**Archivo analizado:** `data/sample.csv` (6 160 registros × 12 columnas, fecha de corte 2026-08-31)
**Responsable:** Alejandro — Data Scientist / ML Engineer

---

## 1. Cómo leer el archivo

El archivo **no se abre con los parámetros por defecto de pandas**. Estos son los correctos:

```python
df = pd.read_csv("data/sample.csv", sep=";", encoding="latin-1")
```

| Propiedad | Valor | Nota |
|---|---|---|
| Separador | `;` | No es coma, pese a la extensión `.csv` |
| Codificación | `latin-1` / `cp1252` | Falla con UTF-8 (`UnicodeDecodeError`) |
| Fin de línea | CRLF | Origen Windows |
| Registros | 6 160 | |
| Columnas | 12 | |
| Filas duplicadas completas | 0 | |
| `CODIGO DEL RECURSO` duplicado | 0 | Clave primaria válida |

---

## 2. Hallazgo crítico: las columnas de latitud y longitud están intercambiadas

**La columna `LATITUD` contiene la longitud y la columna `LONGITUD` contiene la latitud.** Esto viene así
desde la fuente MINCETUR; no ha sido un error de nuestra extracción.

Evidencia sobre los 4 915 registros que sí tienen coordenadas, usando el *bounding box* del Perú
(latitud −18.35 a −0.04; longitud −81.33 a −68.65):

| Interpretación de las columnas | Registros dentro del territorio peruano |
|---|---|
| Tal como vienen etiquetadas | **0.00 %** |
| Intercambiando ambas columnas | **100.00 %** |

Verificación contra coordenadas conocidas:

| Recurso | `LATITUD` | `LONGITUD` | Ubicación real |
|---|---|---|---|
| Parque Arqueológico Nacional de Machu Picchu | −72.5452 | −13.1629 | lat −13.16, lon −72.54 |
| Lago Titicaca | −69.5043 | −15.7969 | lat −15.80, lon −69.50 |

**Impacto.** Si no lo corrigiesemos todos los recursos caen en el océano Índico frente a Somalia y **el cálculo de
rutas y el clustering geográfico de DreemGO producirían resultados inválidos sin lanzar ningún error**. Es el
tipo de defecto que no se detecta con `df.info()`.

**Corrección aplicada en el pipeline**:

```python
df = df.rename(columns={"LATITUD": "longitud", "LONGITUD": "latitud"})
```

Tras el intercambio, **0 registros** quedan fuera del territorio peruano y no existen coordenadas `(0, 0)`.

---

## 3. Valores faltantes

| Columna | Nulos | % | Naturaleza |
|---|---|---|---|
| `LATITUD` | 1 245 | 20.2 % | Estructural, no aleatorio (ver abajo) |
| `LONGITUD` | 1 245 | 20.2 % | Estructural, no aleatorio |
| `SUB TIPO CATEGORÍA` | 1 | 0.02 % | Registro «La QOcha Fiesta» (Arequipa) |
| Las 9 columnas restantes | 0 | 0 % | Completas |

### Los faltantes no son ruido: son semánticos

El 100 % de las coordenadas ausentes se concentra en dos de las cinco categorías:

| Categoría | Registros | Sin coordenadas | % |
|---|---|---|---|
| 3. Folclore | 824 | 663 | **80.5 %** |
| 5. Acontecimientos programados | 749 | 582 | **77.7 %** |
| 1. Sitios naturales | 2 164 | 0 | 0 % |
| 2. Manifestaciones culturales | 2 118 | 0 | 0 % |
| 4. Realizaciones técnicas | 305 | 0 | 0 % |

La explicación es: **Folclore y Acontecimientos Programados no son lugares, son prácticas y eventos**
(una festividad patronal, una danza, una expresión gastronómica). MINCETUR no les asigna un punto porque no lo
tienen. Tratar de imputar esas coordenadas sería inventar datos.

**Decisión de diseño.** No se imputan. Se parte el inventario en dos capas con usos distintos:

- **Capa geolocalizable — 4 915 recursos (79.8 %).** Alimentaría el clustering espacial y el cálculo de rutas.
- **Capa de experiencia — 1 245 recursos (20.2 %).** Se asocia al **distrito** en vez de a un punto, y se usa
  para enriquecer el itinerario y para el eje de **temporada**: los acontecimientos programados tienen
  estacionalidad propia, que es justamente una de las tres entradas del usuario en DreemGO. Un faltante de
  coordenada se convierte así en una variable de producto, no en una pérdida.

### Sesgo geográfico de la cobertura

El porcentaje sin coordenadas varía mucho por región, así que la capa geolocalizable no cubre el país de forma
uniforme:

| Regiones con menor cobertura | % sin coordenadas |
|---|---|
| La Libertad | 41.9 % |
| Lima | 30.8 % |
| Cusco | 25.4 % |
| Loreto | 23.0 % |

| Regiones con mayor cobertura | % sin coordenadas |
|---|---|
| Huancavelica | 0.0 % |
| Amazonas · Ucayali | 5.2 % |
| Madre de Dios | 6.8 % |

Que Lima y Cusco —los dos destinos más demandados— estén entre los de peor cobertura es un riesgo directo para
el MVP.

---

## 4. Inconsistencias de formato

**a) Espacios sobrantes.** 687 valores de `NOMBRE DEL RECURSO` y 15 de `SUB TIPO CATEGORÍA` tienen espacios al
inicio o al final. Rompe agrupaciones y joins por texto. → `.str.strip()` en todas las columnas de texto.

**b) Mayúsculas inconsistentes entre columnas del mismo eje geográfico.**

| Columna | Formato | Valores únicos |
|---|---|---|
| `REGIÓN` | Title Case (`Cusco`) | 25 |
| `PROVINCIA` | Title Case (`Contumaza`) | 190 |
| `DISTRITO` | MAYÚSCULAS (`CUSCO`) | 1 004 |

Impide cruzar con fuentes externas (INEI, OpenStreetMap) sin normalizar antes. → Normalizar a Title Case y
adicionalmente generar una clave sin tildes y en minúsculas para los joins.

**c) Taxonomía mixta en `TIPO DE CATEGORÍA`.** De los 35 valores únicos, **16 arrastran un prefijo de letra**
del formulario original (`g. Cuerpo de Agua`, `a. Montañas`, `ñ. Zonas paisajísticas`, `l. Costas`) y 19 no
(`Arquitectura y Espacios Urbanos`, `Fiestas`, `Gastronomía`). Si se usará como variable categórica sin limpiar,
el modelo trata el prefijo como parte de la etiqueta. → Eliminamos el prefijo con
`str.replace(r"^[a-zñ]\.\s*", "", regex=True)`.

**d) `FECHA_DE_CORTE` en lugar de ser una fecha, es un entero.** Llega como `20260831` en `int64`. Valor único en todo el
archivo, lo que significa que se trata de una sola extracción. → Convertir con
`pd.to_datetime(col, format="%Y%m%d")`.

---

## 5. Valores sospechosos

**a) Tres pares de recursos duplicados con códigos distintos.** Mismo nombre y mismo distrito, dos fichas
separadas en MINCETUR:

| Recurso | Distrito | Códigos |
|---|---|---|
| Artesanía de Pichanaqui | Pichanaqui, Junín | 13534 · 13549 |
| Comunidad Nativa Asháninka Yavirironi | Río Negro, Junín | 7356 · 13354 |
| Mirador de Tapay | Cabanaconde, Arequipa | 14244 · 14322 |

Son 3 casos sobre 6 160 (0.05 %). Se marcan pero **no se eliminan automáticamente**: pueden ser dos fichas
legítimas del mismo lugar registradas en momentos distintos. Deberíamos revisarlo manualmente pronto.

**b) Precisión de coordenadas bimodal.** La cifra de decimales se agrupa en dos modas: ~5–6 decimales
(1 358 registros) y ~14–15 decimales (1 160 registros). Sugiere dos procesos de captura distintos —digitación
manual contra derivación automática desde un SIG—. La precisión de 15 decimales es espuria (equivale a
fracciones de micrómetro); no invalida el dato, pero desaconseja usar la precisión como señal de confianza.

**c) Códigos con vacíos.** `CODIGO DEL RECURSO` va de 11 a 14 665 pero solo hay 6 160 registros. Los saltos
corresponden a fichas retiradas o no publicadas por MINCETUR. No es un defecto; se documenta para que nadie
asume que el código es un índice correlativo.

**d) Integridad referencial verificada.** Las 6 160 URLs son únicas, todas HTTPS, y **en el 100 % de los casos
el parámetro `cod_Ficha` de la URL coincide con `CODIGO DEL RECURSO`**. Cada registro es trazable a su ficha
oficial, lo que hace el dataset auditable por terceros.

---

## 6. Limitaciones conocidas

1. **El inventario nos describe la oferta, no la demanda.** No contiene visitas, aforo ni popularidad. Para DreemGO no
   se puede ordenar destinos por relevancia real solo con esta fuente; por lo que haría falta cruzar con `datosTurismo` de
   MINCETUR (posiblemente).
2. **No contiene precios ni horarios.** El criterio de presupuesto —una de las tres entradas del usuario— no es
   satisfacible con este dataset. Requiere una segunda fuente aún por definir (la buscaremos).
3. **Sin datos de accesibilidad ni conectividad.** No hay distancias, tiempos de viaje ni estado de vías. El
   cálculo de rutas necesitará geometría vial externa (OpenStreetMap).
4. **Foto de un solo instante.** Una única fecha de corte (2026-08-31) impide analizar evolución temporal.
5. **La cobertura geográfica está sesgada** hacia las regiones con menor demanda turística (ver §3).
6. **Sin control de calidad sobre el nombre.** Los nombres vienen en Title Case forzado, lo que altera la
   grafía original de topónimos quechua y aimara. Afecta la búsqueda por texto.

---

## 7. Resumen para la presentación

| Indicador | Valor |
|---|---|
| Registros | 6 160 |
| Regiones cubiertas | 25 de 25 |
| Provincias · distritos | 190 · 1 004 |
| Categorías · tipos · subtipos | 5 · 35 · 187 |
| Recursos geolocalizables tras corregir | **4 915 (79.8 %)** |
| Duplicados reales | 3 pares (0.05 %) |
| Trazabilidad a ficha oficial | 100 % |
| Licencia | ODC-BY (uso libre con atribución) |

**Conclusión.** El dataset es **pertinente y suficiente para la fase 1 de DreemGO**: cubre las 25 regiones del
país con clasificación jerárquica en tres niveles y casi 5 000 recursos geolocalizables, todos trazables a su
ficha oficial. Aunque requiere una corrección crítica antes de cualquier análisis espacial —el intercambio de
latitud y longitud— y una capa de limpieza documentada. Los faltantes de coordenadas no son un defecto de
calidad sino una propiedad semántica de dos categorías, y se aprovechan como señal de estacionalidad. Las
dimensiones de **precio** y **conectividad vial** no están en esta fuente y son la brecha explícita a cubrir
antes de la semana 6 (otras fuentes).
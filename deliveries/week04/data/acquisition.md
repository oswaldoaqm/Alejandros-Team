# Adquisición de datos

**Producto:** DreemGO · **Equipo:** Alejandro's Team · **Semana 4**

---

## Fuente

| | |
|---|---|
| **Dataset** | Inventario Nacional de Recursos Turísticos |
| **Entidad** | Ministerio de Comercio Exterior y Turismo (MINCETUR) |
| **Ficha oficial** | https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos |
| **Descarga directa** | https://www.mincetur.gob.pe/Datos_abiertos/DGET/Inventario_recursos_turisticos.csv |
| **Licencia** | Open Data Commons Attribution License (ODC-BY) — uso libre con atribución |
| **Última actualización de la ficha** | 30 de septiembre de 2025 |
| **Fecha de corte de nuestra extracción** | 31 de agosto de 2026 |
| **Fecha de descarga** | 1 de septiembre de 2026 |
| **Registros obtenidos** | 6 160 |

El archivo publicado por MINCETUR es la extracción completa del inventario, no una muestra. Se incluye íntegro
en `data/sample.csv` (1.4 MB), por lo que no fue necesario submuestrear.

> **Atribución requerida por la licencia:** «Inventario Nacional de Recursos Turísticos», Ministerio de Comercio
> Exterior y Turismo del Perú, disponible en la Plataforma Nacional de Datos Abiertos bajo licencia ODC-BY.

---

## Cómo obtener los datos

### Opción 1 — descarga directa

```bash
curl -L -o data/sample.csv \
  "https://www.mincetur.gob.pe/Datos_abiertos/DGET/Inventario_recursos_turisticos.csv"
```

### Opción 2 — script reproducible

```bash
python code/download_inventory.py
```

No se requiere clave de API, registro ni autenticación. El recurso es de acceso público y anónimo.
P.D. No hemos generado ese Script, es solo una posible opción.

---

## Parámetros de lectura

El archivo **no se abre con los valores por defecto de pandas**. Estos son los correctos:

```python
import pandas as pd

df = pd.read_csv("data/sample.csv", sep=";", encoding="latin-1")
```

| Propiedad | Valor |
|---|---|
| Separador | `;` (punto y coma, no coma) |
| Codificación | `latin-1` / `cp1252` — falla con UTF-8 |
| Fin de línea | CRLF |
| Cabecera | Fila 1 |

---

## Corrección obligatoria encontrada antes de usar

Las columnas `LATITUD` y `LONGITUD` **vienen intercambiadas desde la fuente**. Verificado sobre los 4 915
registros con coordenadas: con las etiquetas originales, el 0 % de los puntos cae dentro del territorio
peruano; al intercambiarlas, el 100 %.

```python
df = df.rename(columns={"LATITUD": "longitud", "LONGITUD": "latitud"})
```

El detalle completo, junto con el resto de hallazgos de limpieza, está en
[`data_quality.md`](./data_quality.md).

---

## Cobertura y estructura

- 25 regiones (24 departamentos + Callao), 190 provincias, 1 004 distritos
- Taxonomía jerárquica de tres niveles: 5 categorías → 35 tipos → 187 subtipos
- 4 915 recursos (79.8 %) con coordenadas utilizables tras la corrección
- Cada registro es trazable a su ficha oficial mediante la columna `URL`

---

## Fuentes complementarias previstas

Ninguna está incluida todavía en este repositorio. Pero adelantamos documentandolas aquí para dejar avanzada el tipo de arquitectura
de datos planificada y de su situación legal.

| Fuente | Aporta | Licencia | Estado |
|---|---|---|---|
| [datosTurismo — MINCETUR](https://datosturismo.mincetur.gob.pe/) | Flujos de visitantes, estadía y gasto por región | Abierta | Por integrar |
| [Open-Meteo — archivo histórico](https://open-meteo.com/) | Climatología por coordenada para el filtro de temporada | CC-BY | Por integrar |
| [OpenStreetMap / Overpass](https://www.openstreetmap.org/) | Geometría vial y puntos de interés para el cálculo de rutas | ODbL | Por integrar |
| [INEI — estadísticas de turismo](https://m.inei.gob.pe/estadisticas/indice-tematico/turismo-11176/) | Series oficiales de contexto | Abierta | Referencia |

### Fuentes evaluadas y (posiblemente) descartadas para el repositorio

**TripAdvisor (scraping)** y **Google Places API** se evaluaron como capa de enriquecimiento de reseñas y
precios. **Pero no las incluiremos en la entrega**: encontramos que los términos de servicio de TripAdvisor
prohíben la extracción automatizada de contenido, y Google Places restringe el almacenamiento y la
redistribución de sus datos. Siguiendo la guía del curso no debemos de subir a un repositorio público 
datos privados, confidenciales, personales o con derechos restringidos.

Si en fases posteriores consideramos que se requiere esa información, tomaremos la posiblidad de obtenerla mediante acuerdos de API que permitan el uso, y
los datos quedarán fuera del control de versiones (visibles en GitHub).

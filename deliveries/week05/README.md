# DreemGO — Semana 5

**Propuesta de proyecto, Data Product Canvas y requerimientos**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Entrega: 9 de septiembre de 2026

> Corregida el 30 de septiembre. Lo entregado el 9 está en la etiqueta [`entrega/semana-05`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-05); cada corrección, en [`ERRATA.md`](./ERRATA.md).

---

## Producto

**DreemGO** — Inteligencia de rutas en Perú

Plataforma que recibe cuatro restricciones del viajero —intereses, mes de viaje, días disponibles y
presupuesto— y devuelve un **itinerario ordenado**: una secuencia de destinos con orden geográfico coherente,
ventana temporal recomendada, costo estimado y enlace a la ficha oficial de cada parada.

La propuesta completa está en [`ProjectProposal.pdf`](./ProjectProposal.pdf).

---

## Equipo y responsabilidades en esta entrega

| Integrante | Rol | Aporte en la semana 5 |
|---|---|---|
| **Miguel** | Data Engineer / Cloud Architect | Pipeline de enriquecimiento, inferencia climática y construcción del dataset v2 |
| **Alejandro** | Data Scientist / ML Engineer | Calidad y verificación del dataset, requerimientos, casos de uso, wireframes y storyboards |
| **Diego** | Backend & Algorithms Engineer | Definición del motor de rutas y de los criterios de aceptación de RF-02 |
| **Christopher** | Frontend Developer & Product Owner | Data Product Canvas, presentación y diseño de la interfaz |

---

## Contenido de esta entrega

```
week05/
├── README.md                   este archivo
├── ERRATA.md                   correcciones posteriores a la entrega
├── ProjectProposal.pdf         propuesta de proyecto
├── ProjectProposal.docx        fuente editable de la propuesta
├── DataProductCanvas.pdf       canvas completo
├── DataProductCanvas.md        misma versión en texto plano
├── Requirements.md             stakeholders, requerimientos, casos de uso y user stories
├── PresentationWeek05.pdf      presentación de la semana
├── assets/
│   ├── wireframe_01.png        definición del viaje (pantalla de entrada)
│   ├── wireframe_02.png        resultado e itinerario
│   ├── storyboard_01.png       recorrido feliz (CU-02)
│   ├── storyboard_02.png       recorrido con conflicto estacional (CU-01)
│   └── diagrama_casos_uso.png  modelo UML de casos de uso
├── code/                       en el orden en que se corren
│   ├── enrich_data.py          altitud desde el modelo de elevación de Open-Meteo
│   ├── fix_altitudes.py        reintenta las altitudes que faltaron
│   ├── build_features.py       distancia a la capital regional
│   ├── add_climate.py          inferencia de ZONA_CLIMATICA por pisos ecológicos
│   ├── fix_pricing.py          índice de lejanía final: 1 <20 km · 2 <80 km · 3 más
│   ├── verify_enriched.py      verificación del resultado
│   └── legacy/                 dos variantes sin pandas que quedaron duplicadas
└── data/
    ├── dataset_enriched.csv    6 160 registros · 16 columnas · separador ";"
    └── data_dictionary_v2.csv  diccionario ampliado con las variables derivadas
```

---

## Requerimientos

| ID | Requerimiento | Criterio de aceptación |
|---|---|---|
| **RF-01** | Motor de recomendación espacio-temporal | Ningún recurso de una zona en temporada adversa aparece sin advertencia explícita y sin al menos una alternativa viable |
| **RF-02** | Generación de itinerario ordenado | El itinerario cabe en los días indicados y ninguna jornada supera el umbral de traslado diario |
| **RNF-01** | Integridad y trazabilidad analítica | 100 % de los recursos recomendados enlaza a ficha oficial verificable; recalcular con otro mes no modifica el dataset base |
| **RNF-02** | Latencia | Menos de 5 s para una consulta sobre una macrorregión |

El desarrollo completo —stakeholders, supuestos, restricciones, casos de uso con flujos alternativos y user
stories— está en [`Requirements.md`](./Requirements.md).

---

## Tareas analíticas y trazabilidad

| Tarea | Descripción | Responde a |
|---|---|---|
| **TA-01** | Agrupamiento espacio-temporal (K-Means / HDBSCAN) sobre coordenadas, altitud e índice de lejanía; post-procesado cruzando zona climática con el mes de viaje | RF-01 · US1 |
| **TA-02** | Ingeniería de variables geoespaciales y climáticas | RNF-01; habilita RF-01 y RF-02 |
| **TA-03** | Extracción de las 6 160 fichas oficiales (jerarquía, época propicia, tipo de ingreso, actividades) — semana 6 | RF-01, RF-02 y RNF-02 |

---

## Data enriquecida

El dataset base de la semana 4 tenía 12 columnas. El de esta semana tiene **16**: se añadieron cuatro variables
derivadas para resolver la ausencia de altitud, costo y clima en la fuente abierta.

| Variable | Origen | Unidad | Nulos |
|---|---|---|---|
| `ALTITUD` | Modelo digital de elevación de Open-Meteo | msnm | 1 245 (20.2 %) |
| `DISTANCIA_CAPITAL_KM` | Distancia Haversine del recurso a su capital regional | km | 1 245 (20.2 %) |
| `INDICE_COSTO_LOGISTICO` | Categorización ordinal de la distancia anterior | 1 = <20 km · 2 = <80 km · 3 = >80 km | 1 245 (20.2 %) |
| `ZONA_CLIMATICA` | Inferencia determinista por pisos ecológicos (altitud + región) | 7 categorías | 1 245 (20.2 %) |

> **Nota de nomenclatura.** En `Requirements.md` y en la presentación esta variable se denomina
> **`INDICE_LEJANIA`**, porque no contiene unidades monetarias: es una aproximación de lejanía, no un costo.
> El renombrado en el CSV y en los scripts queda pendiente para la semana 6, junto con el tipo de ingreso de la
> ficha oficial, que será la primera aproximación real al costo.

Los 1 245 nulos son los mismos en las cuatro variables y **no son ruido**: corresponden a los recursos sin
coordenadas de las categorías *Folclore* y *Acontecimientos Programados*, que son prácticas y eventos sin punto
geográfico. No entran al cálculo de rutas; se usan como capa de contexto a nivel de distrito.

**Limitación conocida del modelo de elevación.** La altitud de Open-Meteo se contrastó contra la altitud oficial
de las fichas: desviación de **+16 a −38 m** en meseta y valle, y hasta **+250 m** en cañón, donde el modelo
suaviza el relieve. Se corregirá con la altitud oficial en TA-03.

---

## Reproducir

```bash
pip install pandas requests

python code/enrich_data.py        # altitud vía Open-Meteo (requiere red)
python code/fix_altitudes.py      # reintenta las altitudes que faltaron (requiere red)
python code/build_features.py     # distancia a la capital regional
python code/add_climate.py        # ZONA_CLIMATICA por pisos ecológicos
python code/fix_pricing.py        # índice de lejanía final
python code/verify_enriched.py    # verificación del resultado
```

Los tres pasos sin red reproducen exactamente las columnas derivadas del CSV entregado (distancia, índice de lejanía y zona climática) en las 6 160 filas; se verificó el 30 de septiembre.

El dataset se lee con separador `;` y codificación UTF-8:

```python
import pandas as pd
df = pd.read_csv("data/dataset_enriched.csv", sep=";")
```

---

## Enlaces

| Documento | Ruta |
|---|---|
| Propuesta de proyecto | [`ProjectProposal.pdf`](./ProjectProposal.pdf) · [fuente editable](./ProjectProposal.docx) |
| Data Product Canvas | [`DataProductCanvas.pdf`](./DataProductCanvas.pdf) |
| Requerimientos y diseño | [`Requirements.md`](./Requirements.md) |
| Presentación | [`PresentationWeek05.pdf`](./PresentationWeek05.pdf) |
| Entrega anterior | [`../week04/`](../week04/) |
| Nota de calidad de datos | [`../week04/data/data_quality.md`](../week04/data/data_quality.md) |

---

## Nota sobre datos restringidos

Este repositorio contiene únicamente datos abiertos con licencia que permite su redistribución. Las fuentes de
enriquecimiento cuyos términos de servicio restringen la extracción o redistribución —TripAdvisor y Google
Places API— **no se incluyen**. La extracción de fichas oficiales prevista para la semana 6 se hará con una
petición por segundo, agente identificado, caché local y verificación previa del `robots.txt`.

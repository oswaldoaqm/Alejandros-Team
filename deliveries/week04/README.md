# DreemGO — Semana 4

**Tema, equipo y selección de dataset**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Entrega: 2 de septiembre de 2026

---

## Nombre tentativo del producto

**DreemGO** — Inteligencia de rutas en Perú

---

## Equipo

| Integrante | Rol |
|---|---|
| Miguel | Data Engineer / Cloud Architect |
| Alejandro | Data Scientist / ML Engineer |
| Diego | Backend & Algorithms Engineer |
| Christopher | Frontend Developer & Product Owner |

---

## Problema y oportunidad

Planificar un viaje dentro del Perú obliga hoy a resolver a mano una ecuación de tres variables que ninguna
herramienta existente resuelve junta: **qué ver** según los intereses propios, **cuándo ir** según el clima y la
temporada de cada destino, y **cuánto cuesta** encadenar esos destinos en una ruta viable. La información está
fragmentada entre inventarios oficiales, reseñas subjetivas y reportes climáticos aislados, y el viajero termina
comparando pestañas en vez de decidir.

La oportunidad es concreta: la gran mayoría de los viajeros internos peruanos organiza sus viajes por cuenta
propia, sin paquetes de agencia. Es un público numeroso que hoy hace manualmente un trabajo de optimización que
un producto de datos puede hacer en segundos.

**Entrada del usuario:** intereses, temporada, presupuesto y días disponibles.
**Salida del producto:** un itinerario ordenado de destinos con secuencia geográfica coherente, ventana temporal
recomendada y costo estimado.

---

## Dominio

Turismo y movilidad en el Perú. Alcance geográfico limitado al territorio nacional en esta fase del curso.

---

## Fuente de datos

**Inventario Nacional de Recursos Turísticos** — Ministerio de Comercio Exterior y Turismo (MINCETUR)

| | |
|---|---|
| Ficha oficial | https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos |
| Licencia | Open Data Commons Attribution (ODC-BY) |
| Registros | 6 160 |
| Cobertura | 25 regiones · 190 provincias · 1 004 distritos |
| Taxonomía | 5 categorías → 35 tipos → 187 subtipos |
| Geolocalizables | 4 915 (79.8 %) |
| Fecha de corte | 2026-08-31 |

Los detalles de descarga, parámetros de lectura y fuentes complementarias previstas están en
[`data/acquisition.md`](./data/acquisition.md).

---

## Contenido de esta entrega

```
week04/
├── README.md                  este archivo
├── code/
│   └── data_quality_check.py  verificación reproducible de calidad
└── data/
    ├── sample.csv             extracción completa del inventario (6 160 registros)
    ├── data_dictionary.csv    diccionario de las 12 columnas
    ├── acquisition.md         origen, licencia y cómo reproducir la descarga
    └── data_quality.md        nota de calidad: faltantes, duplicados y limitaciones
```

---

## Hallazgo principal del análisis de calidad

Las columnas `LATITUD` y `LONGITUD` **vienen intercambiadas desde la fuente**. Con las etiquetas originales,
el 0 % de los recursos cae dentro del territorio peruano; al intercambiarlas, el 100 %. Sin esta corrección,
el clustering geográfico y el cálculo de rutas producirían resultados inválidos sin lanzar ningún error.

Un segundo hallazgo cambió una decisión de diseño: el 20.2 % de registros sin coordenadas **no es ruido**. La
totalidad se concentra en las categorías *Folclore* y *Acontecimientos Programados*, que son prácticas y eventos
sin punto geográfico. En vez de imputar, se usan como capa de experiencia asociada al distrito y como señal de
**estacionalidad** — justamente una de las tres entradas que pide el usuario.

El análisis completo está en [`data/data_quality.md`](./data/data_quality.md).

---

## Reproducir

```bash
pip install pandas
python code/data_quality_check.py data/sample.csv
```

---

## Nota sobre datos restringidos

Este repositorio contiene únicamente datos abiertos con licencia que permite su redistribución. Las fuentes
de enriquecimiento evaluadas cuyos términos de servicio restringen la extracción o redistribución —TripAdvisor
y Google Places API— **no se incluyen** y se documentan como capa futura sujeta a acuerdos de API.

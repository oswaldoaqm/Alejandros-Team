# DreemGO

**Inteligencia de rutas en Perú**

Plataforma que convierte intereses, temporada y presupuesto en un itinerario de viaje optimizado dentro del
Perú. Combina el inventario turístico oficial de MINCETUR con datos climáticos y algoritmos de clustering y
optimización de rutas, para entregar en segundos lo que hoy toma días de búsqueda dispersa.

> Proyecto final del curso **DS3022 — Desarrollo de Producto de Datos**
> Universidad de Ingeniería y Tecnología (UTEC) · Prof. Germain Garcia-Zanabria · Ciclo 2026-2

---

## El problema

Planificar un viaje dentro del Perú obliga a resolver a mano una ecuación de tres variables que ninguna
herramienta existente resuelve junta: **qué ver** según los intereses propios, **cuándo ir** según el clima y la
temporada de cada destino, y **cuánto cuesta** encadenar esos destinos en una ruta viable. La información está
fragmentada entre inventarios oficiales, reseñas subjetivas y reportes climáticos aislados, y el viajero termina
comparando pestañas en vez de decidir.

La gran mayoría de los viajeros internos peruanos organiza sus viajes por cuenta propia, sin paquetes de
agencia. Es un público numeroso que hoy hace manualmente un trabajo de optimización que un producto de datos
puede automatizar.

| | |
|---|---|
| **Entrada del usuario** | Intereses, temporada, presupuesto y días disponibles |
| **Salida del producto** | Itinerario ordenado con secuencia geográfica coherente, ventana temporal recomendada y costo estimado |
| **Alcance** | Destinos dentro del territorio peruano |

---

## Equipo

| Integrante | Rol | Responsabilidades |
|---|---|---|
| **Miguel** | Data Engineer / Cloud Architect | Pipeline de ingesta, transformación a formatos ligeros, infraestructura cloud y contenedores |
| **Alejandro** | Data Scientist / ML Engineer | Análisis exploratorio, calidad de datos, clustering de destinos por perfil de interés, selección y validación de modelos |
| **Diego** | Backend & Algorithms Engineer | Microservicios, estructuras de datos y cálculo de rutas geográficas |
| **Christopher** | Frontend Developer & Product Owner | Interfaz interactiva, Data Product Canvas, requisitos funcionales y de negocio |

---

## Datos

**Inventario Nacional de Recursos Turísticos** — Ministerio de Comercio Exterior y Turismo (MINCETUR)
Licencia [ODC-BY](https://www.datosabiertos.gob.pe/dataset/inventario-nacional-de-recursos-tur%C3%ADsticos) · 6 160 registros · 25 regiones · fecha de corte 2026-08-31

> **Advertencia para quien use esta fuente:** las columnas `LATITUD` y `LONGITUD` vienen **intercambiadas desde
> el origen**. Con las etiquetas originales, el 0 % de los recursos cae dentro del territorio peruano; al
> intercambiarlas, el 100 %. Sin corregirlo, cualquier análisis espacial falla en silencio, sin lanzar error.
> El análisis completo está en [`deliveries/week04/data/data_quality.md`](./deliveries/week04/data/data_quality.md).

Fuentes complementarias previstas: [datosTurismo](https://datosturismo.mincetur.gob.pe/) (flujos y gasto),
[Open-Meteo](https://open-meteo.com/) (climatología histórica) y
[OpenStreetMap](https://www.openstreetmap.org/) (geometría vial).

Este repositorio contiene únicamente datos abiertos con licencia que permite su redistribución.

---

## Estructura del repositorio

```
Alejandros-Team/
├── README.md
└── deliveries/
    └── week04/                     Tema, equipo y selección de dataset
        ├── README.md
        ├── code/
        │   └── data_quality_check.py
        └── data/
            ├── sample.csv          extracción completa del inventario
            ├── data_dictionary.csv
            ├── acquisition.md
            └── data_quality.md
```

Cada hito del curso vive en su propia carpeta bajo `deliveries/weekXX/`.

---

## Reproducir

```bash
git clone https://github.com/oswaldoaqm/Alejandros-Team.git
cd Alejandros-Team
pip install pandas
python deliveries/week04/code/data_quality_check.py deliveries/week04/data/sample.csv
```

El script regenera todas las cifras reportadas en la nota de calidad de datos.

---

## Cronograma

| Semana | Fecha | Hito | Estado |
|---|---|---|---|
| 4 | 2 sep 2026 | Tema, equipo y selección de dataset | Entregadooo |
| 5 | 9 sep 2026 | Propuesta, Data Product Canvas y requisitos | En curso |
| 6 | 16 sep 2026 | Análisis exploratorio y selección de modelo | Pendiente |
| 7 | 23 sep 2026 | **Delivery 1** — definición integrada del proyecto | Pendiente |
| 10 | 14 oct 2026 | Prototipo funcional | Pendiente |
| 12 | 28 oct 2026 | Prototipo refinado, evaluación y casos de estudio | Pendiente |
| 15 | 18 nov 2026 | Presentación final y **Delivery 2** | Pendiente |

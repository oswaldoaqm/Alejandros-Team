# DreemGO — Semana 7 · Delivery 1

**Definición integrada del proyecto**
DS3022 · Desarrollo de Producto de Datos · UTEC · Prof. Germain Garcia-Zanabria
Entrega: 23 de septiembre de 2026

> Lo entregado el 23 está intacto en la etiqueta [`entrega/semana-07`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-07). Lo que se corrigió después, con su porqué, está en [`ERRATA.md`](./ERRATA.md).

## Contenido

```
week07/
├── README.md                      este archivo
├── ERRATA.md                      correcciones posteriores a la entrega
├── PresentationWeek07.pdf         presentación de la Delivery 1
├── Cloud_Architecture.drawio.png  arquitectura en la nube
├── E-R.png                        modelo entidad-relación
├── code/                          copia del código de week06, más el generador del diagrama por capas
├── data/                          datos procesados, los mismos de week06
└── docs/
    ├── Data_Dictionary.md         diccionario de las diez tablas
    ├── arquitectura_dreemgo.png   arquitectura por capas (y su .svg)
    ├── low-fidelity prototype.jpg prototipo de baja fidelidad
    └── figuras y métricas de TA-01
```

`Delivery1Report.pdf` con su fuente editable, `DataProductCanvas.pdf` y los requisitos se entregaron por la plataforma del curso.

## Cómo correr el código

Es el mismo de `week06/code`. Las instrucciones y el orden están en [`../week06/README.md`](../week06/README.md); el diagrama por capas se regenera con:

```bash
cd deliveries/week07/code
python arquitectura_dreemgo.py ../docs/arquitectura_dreemgo.svg
```

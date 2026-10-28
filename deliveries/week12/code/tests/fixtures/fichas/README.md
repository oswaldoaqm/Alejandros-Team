# Fichas de prueba

Doce fichas reales de MINCETUR, descargadas el 30 de septiembre de 2026 con `pipeline/adquisicion/descargar_fichas_html.py`. Cada una está aquí por un caso que el parser tiene que resolver:

| Código | Recurso | Por qué |
|---|---|---|
| 1237 | Ciudad Sagrada de Caral | Ficha completa: dos recorridos de acceso, tarifa con varias categorías, horario, visitantes |
| 257 | Reserva Nacional de Paracas | Falló en el scraper v3: "4.4.km/ 7 min", "74 km/ 1 hora con 5 min"; tarifa nacional y local |
| 916 | Playa Tortugas | Falló en v3: "2.2. km / 4 min"; ingreso libre |
| 1179 | Museo Salesiano Vicente Rasetto | Falló en v3: "1.1. Km. / 3 minutos."; cierra los domingos; teléfono en el texto |
| 104 | Cuento La Laguna del Toro | Folclore: jerarquía "No aplica", sin accesos ni ingreso |
| 22 | Laguna de Lauricocha | Jerarquía "POR JERARQUIZAR", toponimia, tramo a pie en metros |
| 11 | Festividad del Señor de los Temblores | Acontecimiento: altitud "3,399 m", sin horario |
| 151 | Parque Turístico de Quistococha | Realización contemporánea; tarifa por edades con extranjeros aparte |
| 11287 | Aniversario de Pozuzo, Día del Colono | Acontecimiento con fecha en el texto: 25 de julio, semana del 24 al 30 |
| 12207 | Festival de la Uva, Vino y Canotaje de Lunahuaná | Acontecimiento sin observaciones |
| 11842 | Pozas de Agua y Sal | "64, 4 Km /1h 47m"; época "Esporádicamente - Algunos meses" |
| 3486 | Sitio Arqueológico de Vichama | Tarifa con servicio de guiado aparte |

Están **saneadas** con `sanear.py`: las secciones "Datos del Responsable" y "Saneamiento Físico Legal" van vacías, y los teléfonos, correos y nombres de quien atiende están reemplazados, con el mismo criterio que usa el pipeline. El parser lee de ellas exactamente lo mismo que de la página original. Para agregar una:

```bash
python -m tests.fixtures.fichas.sanear data/externos/fichas_html/<codigo>.html.gz tests/fixtures/fichas/
```

`inventario_muestra.csv`, en la carpeta de arriba, tiene siete filas del inventario del 29 de septiembre de 2026 tal cual (en Windows-1252), la 257 con latitud y longitud puestas en su lugar para probar el caso sin intercambio, y la 11287 del corte del 31 de agosto, cuando los acontecimientos aún no tenían coordenadas.

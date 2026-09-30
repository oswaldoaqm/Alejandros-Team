# Erratas · Semana 7 · Delivery 1

Lo entregado el 23 de septiembre está intacto en la etiqueta [`entrega/semana-07`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-07). Esta carpeta se corrigió el 30 de septiembre, en su sitio.

## Correcciones

| Dónde | Qué decía | Qué dice ahora | Por qué |
|---|---|---|---|
| `code/` | Copia de `week06/code` con el nombre anterior de TA-05 (`ta02_estacionalidad.py`) y los errores de código listados en `../week06/ERRATA.md` | La misma copia, sincronizada con esas correcciones, con `ta05_estacionalidad.py` y los scripts que no se corren en `code/legacy/` | El código vivo es el de `week06/code` y, desde la semana 10, el del producto en la raíz del repositorio |
| `docs/Data_Dictionary.md` | Una versión anterior que llamaba al veredicto de TA-05 «predicción del modelo de Machine Learning», atribuía los polos a «HDBSCAN/K-Means», presentaba la estacionalidad como «salida TA-02» y los eventos simulados como «catálogo B2B», citaba una columna `id_comercio` que no existe y daba UTF-8-SIG como codificación de todas las tablas | El diccionario vigente, el mismo de `week06/docs/` | Cada una de esas afirmaciones era falsa: el veredicto es una regla declarada, los polos salen del enlace completo, los eventos son simulados y la columna se llama `ID_EVENTO` |
| `docs/arquitectura_dreemgo.png` y `.svg` | «TA-02 · Estacionalidad · TA-03 · Puntaje»; polos de «≈ 3,2 h»; top-10 con Lima o Cusco «60 % → 30 %»; «6 parámetros · ninguno calibrado aún»; TA-04 «semana 10» | TA-05 y puntaje del polo; ≈ 3,9 h; 30 % → 10 %; 7 parámetros, 2 calibrados con la ficha; TA-04 por jornada, con la versión 2 en la semana 10 | Numeración anterior, horas con 40 km/h y cifras calculadas con la jerarquía sin respaldo. Los parámetros calibrados y TA-04 ya existían el 20 de septiembre, la fecha del diagrama. Se regeneró con `code/arquitectura_dreemgo.py` |
| `PresentationWeek07.pdf`, diapositiva 17 | Polos 62, 48 y 45 de HDBSCAN con ~11,9 h, ~12,6 h y ~10,9 h de punta a punta | 14,7 h, 15,5 h y 13,3 h | Se calcularon con 40 km/h; la velocidad calibrada es 32,5 km/h. El PDF no se edita: la corrección vale desde aquí |

## Falta en esta carpeta

`Delivery1Report.pdf` con su fuente editable, `DataProductCanvas.pdf` y los requisitos se entregaron por la plataforma del curso el 23 de septiembre. El enunciado también los pide dentro de `deliveries/week07/`, así que se suben aquí.

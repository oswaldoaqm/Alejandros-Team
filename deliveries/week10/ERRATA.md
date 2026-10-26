# Erratas · Semana 10 · Prototipo funcional

Lo entregado el 21 de octubre está intacto en la etiqueta [`entrega/semana-10`](https://github.com/oswaldoaqm/Alejandros-Team/tree/entrega/semana-10). Esta carpeta se actualizó el 25 de octubre, en su sitio, después de que el equipo rehízo el frontend de la app. El motor, el API, los datos y los artefactos no cambiaron.

## Lo que cambió el 25 de octubre

| Dónde | Qué decía | Qué dice ahora | Por qué |
|---|---|---|---|
| `code/app/` | La app del 20 de octubre | La app con el frontend nuevo: el carrusel de destinos en el inicio, el botón del tema claro y oscuro y los estilos de cada pantalla, con las correcciones del carrusel que siguen abajo | Es la copia de `app/`, y el frontend cambió |
| `code/infra/Dockerfile` | La imagen de Python y el adaptador de Lambda 1.0.1, de la galería pública de AWS (`public.ecr.aws`) | Las mismas de Docker Hub, con el adaptador 0.8.3 | Es la copia de `infra/Dockerfile`, que el equipo cambió junto con el frontend |
| `capturas/` | 23 pantallas de la app del 20 de octubre | 25: las mismas con el frontend nuevo, más el inicio en celular y en escritorio | Las anteriores ya no muestran la app publicada |
| `PrototypeReport.md` | La app sin carrusel, 122 kB al abrir y 234 pruebas de la app | El carrusel y sus correcciones, lo que baja ahora al abrir y 238 pruebas de la app | El mismo cambio |
| `PresentationWeek10.pptx` y `.pdf` | 26 diapositivas con las capturas del 20 de octubre | 27: la 5, nueva, muestra el inicio, las capturas son las del 25 y el guion de la demo empieza en el carrusel | Para presentar el avance con la app de hoy. La del 21 de octubre sigue en la etiqueta |
| `README.md` | 23 capturas y el estado al 20 de octubre | 25 capturas y el estado al 25 de octubre | El mismo cambio |

## Las correcciones del carrusel

El carrusel tenía cuatro problemas, y se corrigieron antes de copiar la app a esta carpeta:

- El título y el botón del Cusco eran los de la portada de ytuqueplanes.com: «Descubre una nueva forma de vivir Cusco» y «Descúbrelas». Ahora dicen «Camina el Cusco a tu ritmo» y «Explorar Cusco».
- Las cinco fotos no mostraban su autor ni su licencia, y las cinco son CC BY-SA, que lo pide. Ahora cada una lleva su crédito, con el enlace a su página en Wikimedia Commons y a su licencia, como el resto de la app.
- En el celular, el texto ocupaba poco más de la mitad del ancho: el título se partía en cinco líneas, la etiqueta del lugar quedaba debajo de la cabecera y el botón tapaba los indicadores. Ahora el texto usa todo el ancho, con un título más chico.
- Pasaba solo, y solo se detenía con el puntero o el foco encima: en un celular no había cómo detenerlo. Ahora tiene un botón para pausarlo y reanudarlo, y si el sistema pide menos movimiento arranca detenido (WCAG 2.2.2).

Además, pedía sus cinco fotos al abrir, 1,8 MB en total, y ahora pide la que se ve y, si pasa solo, la siguiente. Y su caligrafía usaba la letra Caveat sin bajarla, así que cada sistema mostraba otra: ahora se baja de Google Fonts, como las otras dos letras de la app.

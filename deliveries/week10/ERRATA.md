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

## Lo que se sumó después

`DemoWeek10.mp4` entró a esta carpeta el 25 de octubre, después de las correcciones: la demo del guion de la presentación en 3 minutos y 20 segundos, sin sonido y con un rótulo en cada paso. Se grabó en escritorio (1 440 × 900) con la app compilada igual que la publicada, contra el API local con los datos `2026.10.8`. El evento que se publica en el video es de prueba y quedó solo en ese API local.

## Después del 25 de octubre

La copia de `code/`, `data/processed/` y `artifacts/` es la del 25 de octubre, y así se queda. La raíz del repositorio siguió cambiando, y la copia del 28 de octubre está en la entrega de la semana 12 ([`deliveries/week12/`](../week12/)). Dos cosas que muestra esta carpeta se corrigieron el 26 de octubre:

- La captura 03 dice «8 h 06 desde Lima» en la tarjeta de Huaraz, y la 05, «8 h 07 por carretera» en la nota del día 1. La tarjeta tomaba las horas de la ida redondeadas a un decimal (8,1 h son 8 h 06), y el plan contaba los minutos enteros. Desde el 26, las dos salen de los mismos minutos y dicen lo mismo.
- El informe pone entre sus límites que el rojo de la marca era el mismo de los avisos críticos. Desde el 26, los avisos críticos tienen su propio rojo, y en el tema oscuro los textos rojos pasan la revisión de contraste.

La pregunta que el informe dejó para la semana 12, si el presupuesto debe dejar fuera lo que no cabe en el P80, se decidió el 27 de octubre: no deja fuera ningún viaje, y avisa cuando el costo central entra y el P80 no ([decisión 0022](../../docs/decisiones/0022-presupuesto-con-margen.md)).

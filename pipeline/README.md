# Pipeline de datos

Convierte lo que bajan los scripts de [`adquisicion/`](./adquisicion/) (en `data/externos/`, fuera de git) en los artefactos que carga el motor. Todo corre en la máquina de un integrante con Python 3.11 o más:

```bash
pip install -e ".[pipeline,dev]"
pytest tests/pipeline
python -m pipeline.maestro   # unos 30 segundos
python -m pipeline.eventos   # después del maestro, unos 10 segundos
python -m pipeline.tiempos   # después del maestro, unos 6 minutos; necesita el extracto de OpenStreetMap
python -m pipeline.clima     # después de tiempos, unos segundos
python -m pipeline.artefactos --version 2026.10.1   # al final: lo que carga el motor
```

## Módulos

| Módulo | Qué hace |
|---|---|
| [`texto.py`](./texto.py) | Lee las cifras que las fichas escriben a mano: distancia y tiempo de cada tramo ("4.4.km/ 7 min", "74 km/ 1 hora con 5 min", "1:30 horas"), altitud ("3,399 m", "3.635 msnm", "150 - 1550"), horario, días de atención y la tarifa de un adulto peruano. Quita teléfonos, correos y el nombre de quien atiende. Funciones puras, sin dependencias |
| [`fichas.py`](./fichas.py) | Convierte el HTML de una ficha oficial en una `Ficha`: encabezado, textos, rutas de acceso por recorrido, ingreso, época y horario, visitantes, actividades y servicios |
| [`inventario.py`](./inventario.py) | Lee el CSV del inventario: codificación Windows-1252, latitud y longitud intercambiadas y el punto decimal corrido de la fila 14707, todo marcado en la columna `coordenada` |
| [`maestro.py`](./maestro.py) | Une inventario, fichas y polos en [`data/procesados/maestro_v3.csv`](../data/procesados/): una fila por recurso, con cada campo derivado marcado con su fuente, las coordenadas y altitudes a revisar, los intereses y si el recurso puede ser parada |
| [`eventos.py`](./eventos.py) | Lee en la ficha de cada acontecimiento cuándo se celebra y lo guarda como una regla (un día, un rango, días desde la Pascua, el segundo domingo de abril, un mes), con su precisión, su día central y la frase que la respalda, en [`data/procesados/eventos_v3.csv`](../data/procesados/). [`dreemgo/calendario.py`](../dreemgo/calendario.py) convierte la regla en fechas para el año del viaje |
| [`red_vial.py`](./red_vial.py) | Convierte el extracto de OpenStreetMap del Perú en una red vial: un vértice en cada cruce y cada kilómetro, y una arista por tramo con su largo, su clase de vía, si es sin asfaltar y cuánto gira. Ubica la capital de cada distrito y busca el camino más rápido |
| [`red_calibracion.py`](./red_calibracion.py) | Calibra la velocidad de cada clase de vía con los recorridos de acceso de las fichas y mide el error por validación cruzada |
| [`tiempos.py`](./tiempos.py) | Con la red calibrada, calcula los tiempos que usa el motor en [`data/procesados/`](../data/procesados/): entre las paradas de cada polo, de su base a cada una y de cada ciudad de origen a cada parada y a cada base. Una sola búsqueda por polo da las tres primeras |
| [`bases.py`](./bases.py) | Elige dónde se duerme en cada polo entre los pueblos de OpenStreetMap: el que deja las paradas más cerca, con preferencia por donde hay hospedaje registrado. Solo decide; los minutos los pone `tiempos.py` |
| [`clima.py`](./clima.py) | El clima de cada polo mes a mes, con la temperatura llevada a la altitud de su base, y su veredicto de temporada (TA-05 v2) |
| [`artefactos.py`](./artefactos.py) | Junta todo en los archivos que carga el motor ([`dreemgo/datos/`](../dreemgo/datos/)), con la versión de los datos y la huella de cada archivo |
| [`referencia/`](./referencia/) | Tablas pequeñas escritas a mano, con su fuente |

## Qué tan bien lee

Sobre las 6 225 fichas descargadas el 30 de septiembre de 2026:

- Se leen todas, sin errores, en unos 25 segundos.
- **Tramos de acceso:** de las 14 561 celdas de distancia y tiempo con texto, 14 402 (98,9 %) dan kilómetros y minutos. Las demás no traen uno de los dos datos ("40 minutos") o lo traen sin unidad ("151 km / 3"), y ese dato queda en `null`. 293 lecturas son posibles pero no seguras, como "1.30 horas" (¿1 h 30 min o 1,3 h?) o "85 km / 2.30 min", y quedan marcadas como `ambigua`.
- **Tarifa:** 832 de las 858 fichas con boleto (97 %) dan una tarifa de adulto peruano. En una muestra al azar de 60, revisada a mano, coincide en 58. Las dos que no:
  - una ficha que solo da el precio del Boleto Turístico del Cusco para extranjeros;
  - una que ofrece varias pozas termales, donde la regla elige la privada en vez de la común.
- **Altitud:** la de 6 135 fichas; 85 no la traen y 5 traen un valor imposible ("8548773").
- **Horario:** el de apertura y cierre en 4 598.

## Qué tan bien fecha los acontecimientos

`eventos.py` da una regla de fecha a 739 de los 758 acontecimientos: 518 con el día que publica la ficha (`exacta`) y 221 calculados desde la Pascua o el santoral, o con solo el mes (`aproximada`). Los otros 19 quedan `por_confirmar`.

Para medir si esas fechas son correctas se sacaron al azar 40 acontecimientos que no se habían usado para ajustar las reglas, y se anotaron a mano, leyendo cada ficha, los días de su fiesta en 2026 y su día central: [`referencia/eventos_anotados.csv`](./referencia/eventos_anotados.csv). Antes de corregir nada con esa muestra:

- 39 de los 40 tienen fecha. El que no, se celebra en la luna llena más próxima al equinoccio de septiembre, y ninguna regla lo expresa.
- 38 de los 39 dan días en que hay fiesta. El que falla es una feria que se hace «una semana antes del aniversario del distrito»: la regla tomó el día del aniversario.
- 28 de los 32 que tienen día central lo incluyen.

Con los errores de esa muestra se corrigieron reglas generales, revisando cada cambio en los 758: el día central que la ficha nombra después de la fecha ("el 28 de agosto es considerado como el día central"), la «fecha central» que se descartaba como si fuera la fecha de un documento, «los días 5 a 8 de enero», las listas «20, 21 y 22 de junio», que perdían el primer día, y el carnaval que la ficha lleva hasta el miércoles de ceniza o el domingo de tentación. Con eso la muestra pasa a 31 de 32 con su día central, cifra que ya no es una medida independiente. Cada corrida de `python -m pipeline.eventos` repite la comparación, y `tests/pipeline/test_eventos.py` exige al menos 90 % en las tres cuentas.

Lo que todavía no se lee:

- Un acontecimiento con dos temporadas al año (la feria de Pacora, en enero y en junio) queda con la primera que da la ficha.
- Las fechas relativas a otra fiesta ("una semana antes del aniversario") y las lunares.
- El día central que la ficha nombra sin fecha ("el sábado es el día central").

## Qué tan bien estima los tiempos de viaje

La red del extracto del 30 de septiembre tiene 1,45 millones de vértices y 1,9 millones de aristas: 421 000 km de vías que puede recorrer un auto. Se calibra con los recorridos de acceso de las fichas que van enteros por carretera, sin caminata, bote ni avión (2 588). La partida se ubica en la capital del distrito según OpenStreetMap, y así se ubican 385 de los 389 distritos. Quedan 2 259 recorridos tras quitar los muy cortos (menos de 3 km o 5 minutos) y los de velocidad imposible. En 1 780 la red y la ficha dan casi la misma distancia (la de la red está entre 0,67 y 1,5 veces la de la ficha). En el resto no describen el mismo camino: casi siempre la ficha pone como partida el distrito del recurso, aunque el tramo empiece en otra ciudad.

El error de la red contra el tiempo de la ficha se mide por validación cruzada por distrito de partida: se calibra sin un grupo de distritos y se mide en ellos.

| Distancia | Recorridos | Error medio | Error mediano | Minutos de error (mediana) |
|---|---:|---:|---:|---:|
| Hasta 10 km | 291 | 31 % | 25 % | 4 |
| 10 a 30 km | 427 | 27 % | 23 % | 8 |
| 30 a 100 km | 560 | 21 % | 16 % | 13 |
| 100 a 300 km | 434 | 15 % | 13 % | 28 |
| Más de 300 km | 68 | 15 % | 12 % | 64 |
| **Todos** | **1 780** | **22 %** | **17 %** | **11** |

Con los mismos recorridos, la fórmula de la semana 6 (línea recta × 1,6 a 32,5 km/h) se equivoca en 48 % en promedio. En los viajes cortos el error relativo es mayor porque las fichas redondean a 5 o 10 minutos, pero en minutos es poco.

Lo calibrado, en [`data/procesados/red_calibracion.json`](../data/procesados/red_calibracion.json):

- **Velocidad por clase de vía:** troncal 58 km/h, primaria 52, secundaria 53, terciaria 38, local 30 y trocha 32. La autopista sale en 48 porque son las vías expresas de Lima, con su tráfico.
- **Recargos:** 0,3 minutos más por km sin asfaltar y 0,1 por km por cada 100° de giro por km, que es lo que frena en la sierra.
- **Tiempo fijo:** 7 minutos por traslado, para salir del pueblo, estacionar o subir al bus.

Sin las curvas, el error medio sube a 23,5 %, y sin los minutos fijos, a 25 %: los viajes cortos quedan muy por debajo. Un solo ritmo para todas las vías, o quitar el recargo por km sin asfaltar, casi no cambia el error sobre rutas ya elegidas (22,4 %). Pero las clases hacen falta para elegir la ruta: con un solo ritmo, el camino más rápido sería casi siempre el más corto, aunque fuera una trocha.

La red muestra lo que la línea recta no ve. En el 10 % de los pares de paradas de un mismo polo, el camino por carretera es más de 2,7 veces la distancia en línea recta, y 4 202 pares (2 %) no se unen por carretera. El caso extremo son las lagunas Jahuacocha y Viconga, a los dos lados de la cordillera Huayhuash: 23 km en línea recta, y 224 km y casi 10 horas por carretera.

## Dónde duerme cada polo

`bases.py` elige entre 9 412 lugares poblados de OpenStreetMap. Los barrios y caseríos a menos de 8 km de una ciudad, o de 4 km de un pueblo, cuentan como parte de ella, para que la base se llame Cusco y no Wanchaq. El costo de cada candidato es el tiempo por carretera a las paradas del polo, en promedio pesado por su jerarquía, con 5 minutos a favor por cada vez que se duplica el hospedaje que OSM registra a menos de 3 km (hasta 25) y un recargo si no registra ninguno. Los 7 978 hoteles, hostales, casas de huéspedes y alojamientos que tiene el extracto se leen con `red_vial.leer_hospedajes`.

Resultado, en [`data/procesados/polos_bases.csv`](../data/procesados/):

- **218 de los 222 polos** duermen en un lugar al que llegan por carretera sus paradas; los otros 4 no tienen ninguna parada a menos de 5 km de una vía y su base se elige en línea recta.
- **200 bases tienen hospedaje registrado** a menos de 3 km (la mediana, 7). Son 103 pueblos, 73 caseríos, 45 ciudades y un barrio (Miraflores, en Lima); 196 son capital de distrito.
- **Altitud:** la del nodo de OSM en 194 bases y la mediana de los recursos a menos de 2 km en 13; 15 caseríos quedan sin altitud.
- **Distancia:** desde la base, la parada típica queda a 40 minutos (la mediana de las 4 465; el 90 % a menos de 2 h 17). El promedio pesado por polo va de 13 minutos a 4 horas en los polos de trekking, como Huayhuash.
- 22 lugares son base de más de un polo: Huaraz de cuatro; Ayacucho, Huánuco, Moquegua y Puerto Maldonado de tres. El motor no repite base entre sus tres rutas.

Lo que esta elección no ve: la red vial no tiene trenes ni botes, así que las islas del Titicaca y los ríos amazónicos no se alcanzan. A Machupicchu Pueblo sí llega una trocha registrada en OSM por la ruta de Hidroeléctrica, y por ella el polo de Machu Picchu queda a 5 h 38 del Cusco.

## Clima por polo

`clima.py` promedia los diez años de cada polo mes por mes y aplica la regla de dos ejes de la semana 6, ahora con el clima del propio polo: 150 mm o más en el mes, y estar entre los tres meses más lluviosos del polo con más de 50 mm. Con los 36 polos descargados al 1 de octubre, 250 de sus 432 meses quedan viables, 100 con advertencia y 82 desaconsejados. Los otros 186 polos usan, hasta que terminen de bajar, la capa regional de la semana 6, y la respuesta del motor lo avisa. Las horas de sol no se publican: el reanálisis no ve la neblina de la costa ([decisión 0006](../docs/decisiones/0006-clima-por-polo.md)).

## Datos personales

Las fichas publican el nombre, el correo y el teléfono de quien las llenó, y a veces el celular de un encargado en el texto libre. El pipeline no lee las secciones "Datos del Responsable" ni "Saneamiento Físico Legal". En el resto del texto reemplaza teléfonos, correos y el nombre pegado a ellos por `[contacto en la ficha oficial]` y `[encargado]`. Nada de eso llega a los artefactos ni al repositorio. Cada parada enlaza a su ficha oficial, donde el viajero encuentra el contacto.

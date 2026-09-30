# Pipeline de datos

Convierte lo que bajan los scripts de [`adquisicion/`](./adquisicion/) (en `data/externos/`, fuera de git) en los artefactos que carga el motor. Todo corre en la máquina de un integrante con Python 3.11 o más:

```bash
pip install -e ".[pipeline,dev]"
pytest tests/pipeline
python -m pipeline.maestro   # unos 30 segundos
python -m pipeline.eventos   # después del maestro, unos 10 segundos
```

## Módulos

| Módulo | Qué hace |
|---|---|
| [`texto.py`](./texto.py) | Lee las cifras que las fichas escriben a mano: distancia y tiempo de cada tramo ("4.4.km/ 7 min", "74 km/ 1 hora con 5 min", "1:30 horas"), altitud ("3,399 m", "3.635 msnm", "150 - 1550"), horario, días de atención y la tarifa de un adulto peruano. Quita teléfonos, correos y el nombre de quien atiende. Funciones puras, sin dependencias |
| [`fichas.py`](./fichas.py) | Convierte el HTML de una ficha oficial en una `Ficha`: encabezado, textos, rutas de acceso por recorrido, ingreso, época y horario, visitantes, actividades y servicios |
| [`inventario.py`](./inventario.py) | Lee el CSV del inventario: codificación Windows-1252, latitud y longitud intercambiadas y el punto decimal corrido de la fila 14707, todo marcado en la columna `coordenada` |
| [`maestro.py`](./maestro.py) | Une inventario, fichas y polos en [`data/procesados/maestro_v3.csv`](../data/procesados/): una fila por recurso, con cada campo derivado marcado con su fuente, las coordenadas y altitudes a revisar, los intereses y si el recurso puede ser parada |
| [`eventos.py`](./eventos.py) | Lee en la ficha de cada acontecimiento cuándo se celebra y lo guarda como una regla (un día, un rango, días desde la Pascua, el segundo domingo de abril, un mes), con su precisión, su día central y la frase que la respalda, en [`data/procesados/eventos_v3.csv`](../data/procesados/). [`dreemgo/calendario.py`](../dreemgo/calendario.py) convierte la regla en fechas para el año del viaje |
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

## Datos personales

Las fichas publican el nombre, el correo y el teléfono de quien las llenó, y a veces el celular de un encargado en el texto libre. El pipeline no lee las secciones "Datos del Responsable" ni "Saneamiento Físico Legal". En el resto del texto reemplaza teléfonos, correos y el nombre pegado a ellos por `[contacto en la ficha oficial]` y `[encargado]`. Nada de eso llega a los artefactos ni al repositorio. Cada parada enlaza a su ficha oficial, donde el viajero encuentra el contacto.

# Contrato de la API

Qué recibe el motor, qué devuelve y cómo encaja eso con el formulario, el modelo de datos y la arquitectura que el equipo diseñó hasta la Delivery 1. La definición ejecutable está en [`dreemgo/contrato.py`](../dreemgo/contrato.py): de ahí sale el esquema OpenAPI (`/v1/openapi.json`, con documentación interactiva en `/v1/docs`), que se guarda en [`docs/openapi.json`](./openapi.json), y de ese archivo salen los tipos de la [app](../app/). Si este documento y el código no coinciden, manda el código y este documento tiene un error.

**Versión 1.2** · 1 de octubre de 2026. La 1.2 suma el tren y el bote: `traslado.medios` dice con qué se hace la ida (carretera, tren o bote), `traslado.acceso` vale `sin_acceso_terrestre` cuando la ida necesita bote, y el costo cobra los pasajes. No quita nada de la 1.1, que conectó el motor y sumó el día de un viaje de ida y vuelta en el día (`ida_visita_y_vuelta`) y tres consultas de apoyo: `/v1/opciones`, `/v1/polos/{id}` y `GET /v1/eventos` (§4). Desde el 2 de octubre responde también `POST /v1/eventos`, con el que un municipio publica un evento (§4.1): la 1.2 ya lo anunciaba y ya traía su modelo, así que la versión no sube. La revisión del equipo sigue antes del 5 de octubre. Desde el 7 de octubre el motor propone entre 194 polos, uno por pueblo donde se duerme, y valora las paradas con otra escala (más abajo, «Cómo decide el motor», y [decisión 0013](./decisiones/0013-un-polo-por-pueblo.md)); ningún campo cambia, así que la versión sigue en 1.2. Ese día cambió también la propiedad 3 (§3): un día de solo viaje, sin visitas, puede llegar a 9 horas ([decisión 0014](./decisiones/0014-dia-de-solo-viaje.md)).

## 1 · La consulta

Viaja en la URL: `GET /v1/viajes?origen=lima&mes=7&dias=6&intereses=historia&intereses=playa`. Es la misma consulta que lleva el enlace para compartir, porque el motor es determinista: la misma consulta con la misma versión de datos devuelve el mismo viaje. No hace falta guardar itinerarios ni tener cuentas ([decisión 0001](./decisiones/0001-sin-login-y-enlace-compartible.md)).

| Campo | Tipo | Obligatorio | Valores | En el formulario |
|---|---|---|---|---|
| `origen` | texto | no, `lima` por defecto | uno de los 24 identificadores de la tabla de abajo | Punto de partida |
| `mes` | entero | sí, salvo que venga `fecha_inicio` | 1 a 12 | Mes de viaje, el único campo forzoso |
| `fecha_inicio` | fecha ISO | no | `2026-07-20` | Opcional: con ella cada día lleva fecha y los eventos se cruzan día a día |
| `dias` | entero | no, 6 por defecto | 1 a 14, **contando la ida y la vuelta** | Días disponibles |
| `intereses` | lista | no | `naturaleza`, `historia`, `gastronomia`, `caminatas`, `playa`, `fiestas`, `arquitectura`, `aventura` | Chips de intereses |
| `presupuesto` | entero | no | 100 a 50 000 soles por persona, todo el viaje | Presupuesto total |
| `altitud_max` | entero | no | 0 a 6 000 metros | Altitud máxima tolerada |
| `sorpresa` | booleano | no | `true` o `false` | Botón «Sorpréndeme» |

Un campo que no está en la tabla se rechaza con 422, igual que un valor fuera de rango. Cada error llega como `{"campo": "dias", "mensaje": "Debe ser menor o igual que 14.", "tipo": "less_than_equal"}`, listo para mostrarlo junto al campo del formulario.

**Orígenes.** La capital o ciudad principal de cada región ([`pipeline/referencia/origenes.csv`](../pipeline/referencia/origenes.csv)):
`lima`, `arequipa`, `trujillo`, `chiclayo`, `piura`, `cusco`, `huancayo`, `iquitos`, `pucallpa`, `tacna`, `ica`, `cajamarca`, `puno`, `ayacucho`, `huaraz`, `huanuco`, `tarapoto`, `chachapoyas`, `abancay`, `huancavelica`, `puerto-maldonado`, `moquegua`, `cerro-de-pasco`, `tumbes`.

**Intereses.** Son el vocabulario del viajero y no la taxonomía de MINCETUR. Cada uno se traduce a categorías, subtipos y actividades de la ficha oficial; la tabla de equivalencias es un artefacto del pipeline y se documenta con cuántos recursos cubre cada interés.

## 2 · La respuesta

```
Respuesta
├── version_contrato, version_datos      la versión de datos también va en el enlace (§6)
├── consulta                             la consulta tal como la entendió el motor
├── rutas[0..3]                          polos distintos, del mejor al peor
│   ├── polo           id, nombre, región, base (donde se duerme), recursos, fuera_del_circuito
│   ├── puntaje, motivos[]               por qué este polo, en frases cortas
│   ├── estacionalidad veredicto del mes, lluvia, días con lluvia, horas de sol, temperaturas, mejores meses
│   ├── traslado       horas de ida, días que se van en ir y volver, con qué se va (carretera, tren, bote), si hace falta bote
│   ├── dias[]         número, fecha, tipo (ida, visita, vuelta… o ida_visita_y_vuelta en un viaje de un día), horas, km
│   │   └── paradas[]  orden, recurso (con su ficha oficial), hora de llegada, traslado y visita en minutos
│   ├── costo          banda P20-P50-P80 en soles, desglose, si entra en el presupuesto
│   ├── eventos[]      fiestas y ferias que caen en las fechas: las del inventario, con la precisión de su fecha,
│   │                  y las que publicó un municipio (fuente «publicado»), con quién las publicó
│   ├── avisos[]       estacionalidad, altitud, aclimatación, presupuesto, días, datos
│   └── indicadores    paradas, jerarquía media, paradas de jerarquía 3-4, altitud máxima, km, valor capturado
├── sin_resultado                        solo si no hay ninguna ruta: por qué y qué relajar
└── atribucion[]                         fuentes y licencias que la app muestra junto al resultado
```

[`docs/ejemplos/respuesta_ilustrativa.json`](./ejemplos/respuesta_ilustrativa.json) es una respuesta del motor, tal cual, para `origen=lima&mes=7&dias=4&intereses=historia&intereses=naturaleza&presupuesto=700&altitud_max=3500` con los datos `2026.10.2`. La genera [`generar_respuesta_ilustrativa.py`](./ejemplos/generar_respuesta_ilustrativa.py). Las pruebas lo validan contra el contrato, así que si el contrato cambia y el ejemplo no, CI falla.

Dos cosas del contrato no aparecen por ahora, y no por descuido: `estacionalidad.horas_sol` viaja en `null` porque el reanálisis no ve la neblina de la costa (da más de 9 horas de sol al día en la costa de Lima en julio) y publicarlo sería engañar; y `traslado.fuente = "estimado"` no aparece, porque el motor solo propone polos a los que se llega por su red: carretera, tren o bote.

### Cómo decide el motor

El detalle está en [`dreemgo/motor/viaje.py`](../dreemgo/motor/viaje.py) y en la [decisión 0009](./decisiones/0009-viaje-en-estrella.md). En corto:

- **Un viaje es una estrella:** se duerme en la base del polo y cada día sale un paseo que vuelve a ella. La base es un pueblo real de OpenStreetMap, elegido por lo cerca que deja las paradas y por el hospedaje que registra ([`pipeline/bases.py`](../pipeline/bases.py)).
- **Un polo es lo que se visita desde un pueblo:** los grupos del agrupamiento de la semana 6 que duermen en el mismo pueblo son un solo polo. Huaraz junta cuatro, y de 222 grupos quedan 194 polos ([decisión 0013](./decisiones/0013-un-polo-por-pueblo.md)).
- **Valor de una parada:** 1, 2, 6 o 24 según su jerarquía; 2 si MINCETUR no la jerarquizó. De un nivel al siguiente se multiplica por 2, por 3 y por 4, para que un lugar de jerarquía 4 pese más que una jornada llena de lugares corrientes. Es un supuesto del producto, todavía sin calibrar. Si la consulta trae intereses, la que no atiende ninguno vale la cuarta parte.
- **Días:** la ida y la vuelta, por carretera, en tren o en bote. Un día de solo viaje puede durar hasta 9 horas; una ida más larga se parte en partes iguales y se duerme a mitad de camino. El día de llegada y el de salida tienen visitas si, con el viaje, sobran al menos 90 minutos de una jornada de 8 horas. Como máximo seis paradas por día ([decisión 0014](./decisiones/0014-dia-de-solo-viaje.md)).
- **Tren y bote:** un camino puede ir en tren (a Machu Picchu) o en bote (a las islas del Titicaca, las Ballestas o por los ríos de la Amazonía). Subir o bajar cuesta 15 minutos, y a una parada se llega en bote solo si su ficha lo dice. La nota del día lo cuenta («En bote hasta Isla Taquile.») y el costo cobra cada tramo en tren y cada km en bote, con su fuente y su rango ([decisión 0010](./decisiones/0010-tren-y-botes.md)).
- **Qué y en qué orden:** orientación por equipos con inserción voraz, 2-opt y tres arranques; se queda el de más valor.
- **Puntaje:** (1 − λ) · calidad · temporada · presupuesto + λ · novedad, con λ = 0,3. La temporada multiplica por 1, 0,75 o 0,4 según el veredicto del mes. El presupuesto multiplica por (presupuesto / costo)² cuando el costo central lo pasa, y por 1 si no: reordena, pero no esconde (§3). «Sorpréndeme» sube λ a 0,5 y deja solo polos fuera del circuito de Lima y Cusco.
- **Eventos publicados:** se suman a `eventos[]` de las rutas que duermen o paran cerca, y nada más. No entran al puntaje ni a los motivos: publicar un evento no mueve ningún polo de su lugar (§4.1 y [decisión 0011](./decisiones/0011-eventos-publicados.md)).
- **Un viaje sale de su ciudad:** no se propone dormir en un polo cuya base queda a menos de media hora del origen, y un viaje de un día no cuenta las paradas de la misma ciudad.
- **Tres rutas, tres pueblos:** cada polo duerme en su propio pueblo, y la respuesta no repite el nombre de una base.

## 3 · Lo que el motor garantiza en cada respuesta

Son propiedades, no intenciones: desde que el motor se conecta, las pruebas las verifican sobre miles de consultas generadas al azar.

1. Ninguna parada supera `altitud_max`.
2. Los días del itinerario suman exactamente `dias`, con la ida y la vuelta incluidas.
3. Ninguna jornada con visitas pasa de 8 horas entre traslados y visitas. Un día de solo viaje, sin visitas, puede llegar a 9.
4. Toda parada enlaza a su ficha oficial de MINCETUR (RNF-01).
5. Un mes desaconsejado nunca aparece sin aviso, y si se descarta hay una alternativa (RF-01).
6. Un evento solo aparece si cae dentro de las fechas o del mes del viaje (RF-03).
7. El presupuesto ordena y advierte, pero nunca esconde una ruta: las tres rutas son las mismas con o sin presupuesto; cambian su orden y sus avisos. El viajero decide.
8. La misma consulta con la misma `version_datos` devuelve exactamente la misma respuesta. Los eventos publicados también son datos: la versión lleva su huella (§6).
9. Las rutas son de polos distintos.
10. Un dato que la fuente no trae viaja como `null`, nunca como un número inventado: la jerarquía que MINCETUR no asignó, la tarifa que la ficha no publica.

Con eventos publicados valen las diez, y las pruebas verifican una cosa más: lo publicado se suma a `eventos[]` de las rutas a las que les toca y no cambia nada más de la respuesta. Ni qué polos se proponen, ni su orden, ni sus motivos, sus días o su costo.

## 4 · Endpoints

| Método y ruta | Qué hace | Desde |
|---|---|---|
| `GET /v1/salud` | Estado, versión del servicio y de los datos | Ya |
| `GET /v1/viajes` | Hasta tres viajes para una consulta | 1.1 |
| `GET /v1/opciones` | Orígenes, intereses con sus etiquetas y cuántas paradas atienden, y rangos del formulario, para no fijarlos en la app | 1.1 |
| `GET /v1/polos/{id}` | Ficha de un polo: sus paradas de mayor a menor jerarquía, su clima mes a mes y sus eventos de los próximos doce meses | 1.1 |
| `GET /v1/eventos?desde=…&hasta=…&polo=…` | Eventos entre dos fechas (hasta un año), de un polo o de todos: los del inventario y los publicados | 1.1 |
| `POST /v1/eventos` | Un municipio u oficina de destino publica un evento. Exige la cabecera `X-Clave-Publicador` (§4.1) | 1.2 |

Sin los artefactos del motor (`dreemgo/datos/`), las consultas de datos responden 503 y `/v1/salud` dice `version_datos: null`.

### 4.1 · Publicar un evento

```
POST /v1/eventos
X-Clave-Publicador: <la clave que el equipo le dio a la entidad>
Content-Type: application/json

{"nombre": "Festival del Café", "fecha_inicio": "2026-11-13", "fecha_fin": "2026-11-15",
 "distrito": "Villa Rica", "provincia": "Oxapampa", "region": "Pasco",
 "lat": -10.7345, "lon": -75.2712, "publicado_por": "Municipalidad Distrital de Villa Rica"}
```

| Campo | Obligatorio | Valores |
|---|---|---|
| `nombre` | sí | 3 a 120 caracteres |
| `fecha_inicio`, `fecha_fin` | sí | Fechas ISO. El evento dura 60 días como mucho, no terminó todavía y empieza en el mes en curso o en los once que siguen, que son los que muestra el calendario |
| `distrito`, `provincia` | sí | 2 a 80 caracteres |
| `region` | sí | Una de las 25 del país. Se acepta sin tildes ni mayúsculas y se guarda como la escribe el inventario |
| `publicado_por` | sí | La entidad que publica, 3 a 120 caracteres. Es lo que el viajero lee junto al evento |
| `lat`, `lon` | no, pero van juntas | Dentro del Perú. Sin ellas el evento sale en el calendario y en ninguna ruta |
| `tipo` | no | Hasta 60 caracteres: «Feria gastronómica» |
| `url` | no | Una dirección `http` o `https` con más información |
| `descripcion` | no | Hasta 1 000 caracteres. Se guarda; todavía no se muestra |

Responde **201** con el evento tal como lo verá el viajero: un `Evento` con `fuente: "publicado"`, `precision_fecha: "exacta"`, su `publicado_por` y un `id` que empieza con `p-`.

- **Dónde aparece.** En `GET /v1/eventos` siempre. Con coordenadas, también en `eventos[]` de las rutas y en la ficha de los polos que duermen o tienen algún lugar del inventario a 10 km o menos, en línea recta. Si varios polos duermen en el mismo pueblo, sale en todos.
- **Qué no cambia.** Ni qué polos se proponen, ni su orden, ni sus motivos (§3).
- **Corregir.** Publicar otra vez el mismo evento (mismo nombre, fechas, distrito, provincia, región y entidad, sin contar tildes ni mayúsculas) lo reemplaza: sirve para ponerle la ubicación o el enlace. Con otro nombre u otras fechas es otro evento.
- **Cuándo se ve.** Enseguida en el servidor que lo recibió y, en los demás, a los dos segundos como mucho. Si justo entonces falla el almacén, en un minuto.
- **Lo que todavía no hay:** retirar un evento por el API, saber por la respuesta a qué polos tocó y ver la descripción. Quedan para la 1.3.

| Respuesta | Cuándo |
|---|---|
| 401 | Falta la cabecera `X-Clave-Publicador` o la clave no es la correcta |
| 403 | El servidor no tiene una clave configurada: no acepta publicaciones |
| 422 | El evento no cumple la tabla de arriba. Cada error llega con su `campo`, como en `/v1/viajes`; el que es de todo el evento (las fechas al revés, una coordenada sin la otra) llega con `campo: "evento"` |
| 503 | No se pudo guardar, o ya hay 500 eventos por venir. No queda nada a medias |

## 5 · Cómo encaja con lo que ya diseñamos

Hasta la Delivery 1 había cuatro piezas hechas por separado: el formulario y la pantalla de resultado (wireframes de la semana 5 y prototipo de la semana 7), el modelo entidad-relación y la arquitectura en la nube. Este contrato las junta. Lo que cambia, cambia por una razón que se puede defender.

### El formulario

| En el diseño | En el contrato | Por qué |
|---|---|---|
| Punto de partida, días, mes, presupuesto y altitud (wireframe 1) | `origen`, `dias`, `mes`, `presupuesto`, `altitud_max` | Igual |
| Ocho chips de intereses (wireframe 1); tres casillas: aventura, cultura, naturaleza (prototipo) | Los ocho chips del wireframe | Tres casillas no distinguen playa de arqueología, que llevan a polos distintos |
| «Sorpréndeme» (wireframe 1) | `sorpresa` | Igual |
| Campo de texto libre (wireframe 1); «notas adicionales: presupuesto, duración» (prototipo) | Fuera de la versión 1 | Un intérprete de texto que convierta la frase en campos es un proyecto aparte. Presupuesto y duración ya son campos |
| Solo mes | `mes` o `fecha_inicio` | Con fecha, los eventos se cruzan día a día (RF-03) |

### La pantalla de resultado

| En el diseño | En el contrato |
|---|---|
| Chips de la consulta, editables (wireframe 2) | `consulta`: la app pinta los chips desde ahí y al quitar uno arma otra URL |
| Mapa con la secuencia numerada | `dias[].paradas[].recurso.lat/lon` y `polo.base` |
| Tres rutas comparables | `rutas`, hasta tres, de polos distintos |
| Costo, paradas, altitud máxima y km por ruta | `costo` e `indicadores` |
| Insignia «fuera del circuito», jerarquía media | `polo.fuera_del_circuito`, `indicadores.jerarquia_media` |
| Alerta de estacionalidad | `estacionalidad` y `avisos` |
| Itinerario por día con km y jerarquía | `dias[].paradas[]` |
| Horario del día: 9:00 Sacsayhuamán, 90 min (prototipo) | `paradas[].llegada` y `minutos_visita` |
| Evento sugerido dentro del día, «Añadir a mi ruta» (prototipo) | `eventos[]`, que la app ubica en su fecha |
| Enlace a la ficha oficial en cada parada | `recurso.url_ficha` |
| Guardar, exportar PDF | Guardar es el enlace. Exportar es trabajo de la app, no del API |

### El modelo entidad-relación

| Entidad | Dónde vive ahora | Por qué |
|---|---|---|
| `RECURSO`, `POLO`, `CLIMA_ESTACIONALIDAD` | Artefactos de solo lectura que el pipeline genera y el motor carga al arrancar | Cambian cuando se recalcula el modelo, no cuando alguien usa la app. Una base relacional para datos de solo lectura suma costo y latencia sin ganar nada ([decisión 0003](./decisiones/0003-artefactos-precalculados.md)) |
| `CLIMA_ESTACIONALIDAD.veredicto_predictivo` | `estacionalidad.veredicto` | Es una regla declarada sobre diez años de clima, no una predicción ([decisión 0004](./decisiones/0004-sin-modelos-supervisados.md)) |
| `EVENTO_COMERCIO` | `Evento`: los 758 acontecimientos del inventario más los que publican los municipios, en DynamoDB | `relevancia_publicidad` no existe: el orden no se vende. Los comercios simulados no entran al producto |
| `ITINERARIO`, `ITINERARIO_PARADA` | No se guardan | El itinerario es función de la consulta y la versión de datos; el enlace lo reconstruye |
| `USUARIO` | No existe | Sin cuentas ([decisión 0001](./decisiones/0001-sin-login-y-enlace-compartible.md)): sin contraseñas ni datos personales que proteger |

### La arquitectura en la nube

| En el diseño | En el producto | Por qué |
|---|---|---|
| Amplify para la web | GitHub Pages | Gratis, en el mismo repositorio, sin cuenta de AWS |
| Cognito | No hay cuentas | Decisión 0001 |
| Tres API Gateway y seis funciones Lambda | Una HTTP API y una función con la imagen del contenedor | Un solo despliegue y un solo arranque en frío; la misma imagen corre fuera de AWS |
| Amazon RDS | Artefactos en la imagen y DynamoDB para eventos | RDS no tiene capa gratuita permanente y los datos del motor son de solo lectura |
| EventBridge y un scraper en Lambda | `pipeline/`, corrido por el equipo cuando cambia una fuente | El scraper de fichas toma unas 2 horas y Lambda corta a los 15 minutos; las fuentes cambian pocas veces al año |
| Data lake en S3 y entrenamiento de ML | `data/externos/` fuera de git y el pipeline versionado | No hay etiquetas con que entrenar: el motor es agrupamiento, reglas de clima y optimización ([ModelSelection §12](../deliveries/week06/ModelSelection.md)) |

## 6 · El enlace para compartir

```
https://oswaldoaqm.github.io/Alejandros-Team/?origen=lima&mes=7&dias=6&intereses=historia&v=2026.10.2
```

Los parámetros son los de la consulta, más `v`, la `version_datos` con que se calculó. Si al abrirlo la versión de datos cambió, la app lo dice («Este enlace se armó con los datos 2026.10.1. Lo que ves está calculado con los datos 2026.10.2…») en vez de mostrar otro viaje en silencio.

La versión de datos tiene dos partes: la de los artefactos del motor y, cuando hay eventos publicados, la huella de ese calendario: `2026.10.2-e3f9a1c`. Sin eventos publicados es solo `2026.10.2`. Si entre el enlace y lo que se ve cambió la primera parte, las rutas pueden ser otras. Si solo cambió la huella, las rutas son las mismas y lo que puede haber cambiado son los eventos que las acompañan: la app no avisa y pone en el enlace la versión vigente.

## 7 · Cómo se cambia el contrato

En un PR que toque a la vez `dreemgo/contrato.py`, este documento, el esquema del que salen los tipos de la app (`python docs/generar_openapi.py` y, en `app/`, `npm run tipos`) y, si hace falta, el ejemplo ilustrativo. Las pruebas fallan si el esquema guardado queda atrás del contrato. Un campo nuevo opcional sube la versión menor (de 1.1 a 1.2, por ejemplo); quitar o renombrar un campo sube la mayor (2.0) y se avisa a quien construye la app antes de fusionar.

# Contrato de la API

Qué recibe el motor, qué devuelve y cómo encaja eso con el formulario, el modelo de datos y la arquitectura que el equipo diseñó hasta la Delivery 1. La definición ejecutable está en [`dreemgo/contrato.py`](../dreemgo/contrato.py): de ahí sale el esquema OpenAPI (`/v1/openapi.json`, con documentación interactiva en `/v1/docs`), que se guarda en [`docs/openapi.json`](./openapi.json), y de ese archivo salen los tipos de la [app](../app/). Si este documento y el código no coinciden, manda el código y este documento tiene un error.

**Versión 1.7** · 20 de octubre de 2026. La 1.7 hace tranquilo el primer día en la altura ([decisión 0020](./decisiones/0020-primer-dia-tranquilo.md)), como ya lo prometía el aviso de aclimatación:

- **`Dia.tranquilo`.** Si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, el primer día en la base es tranquilo: medio día de visitas como mucho, ninguna parada a más de 500 m sobre la base y ninguna caminata larga. Es el de llegada, si queda tiempo para visitar, o el siguiente; después de un bus de noche, empieza a las 9:00. Es la misma regla de la noche de descanso de la 1.5.
- **La base, con altitud máxima.** La propiedad 1 (§3) dice ahora también la base: con `altitud_max`, no se duerme más arriba, y una base de la que no se sabe la altura no se propone. Desde los datos `2026.10.8`, todas la tienen.

No quita nada de la 1.6. Suma una propiedad, la 14.

La 1.6, del 19 de octubre, hizo creíble el plan ([decisión 0019](./decisiones/0019-plan-creible.md)):

- **El almuerzo.** Cada día con visitas trae `almuerzo`: a qué hora, después de cuántas paradas, dónde y si cerca hay dónde comer. Es una hora que no cuenta en las 8 de la jornada, así que un día entero va de 8:00 a 17:00. Si se almuerza al llegar a una parada, su `llegada` es la hora de después del almuerzo.
- **El bus de noche.** Lo que por tierra toma de 7 a 16 horas, sin tren ni bote, va en bus de noche, y `traslado.bus_de_noche` dice a qué hora sale y llega. Sus noches van fuera de los días: **con bus de noche cambia el sentido de `dias` y de `fecha_inicio`**. `dias` cuenta los días allá, y `fecha_inicio` es el día 1, en que se llega, porque el bus sale la noche anterior. `traslado.dias_de_viaje` vale 0, ningún día lleva las horas del bus y `indicadores.km_total` suma sus km.
- **Con destino, se vuela aunque el viaje sea corto**: la propiedad 9 (§3) tiene ahora esa excepción.

No quitó nada de la 1.5. Sumó dos propiedades: la 12, del almuerzo, y la 13, del bus de noche.

La 1.5, del 18 de octubre, sumó la noche ([decisión 0018](./decisiones/0018-planes-de-noche.md)). Hay un interés nuevo, `vida_nocturna`, que no elige paradas: elige dónde salir. Cada día que se duerme en la zona puede traer `noche`, de uno de tres tipos:

- `salir`: hasta tres lugares a pie de la base;
- `estrellas`: desde dónde, cuántas noches salen despejadas ese mes y, con fecha, la luna de esa noche;
- `descanso`: la primera noche en la altura.

`/v1/opciones` dice qué intereses son de noche (`de_noche`), y `/v1/polos/{id}` trae la noche de la zona (`noche`). No quitó nada de la 1.4. Nada de la noche cambia los días: las paradas, sus horas, el traslado y el costo son los mismos con plan de noche o sin él (propiedad 11, §3).

La 1.4, del 16 de octubre, sumó «Quiero ir a…» ([decisión 0017](./decisiones/0017-quiero-ir-a.md)): la consulta acepta `destino`, el número de una zona, y el motor arma solo el viaje a esa zona. Si no cabe, `sin_resultado` dice qué lo impide y propone los cambios con que sí sale; el último, buscar en todas las zonas (una sugerencia con `campo: "destino"` y `valor: null`). Además, cada evento dice su zona (`polo`). No quitó nada de la 1.3, y la propiedad 9 (§3) dice también qué pasa con un destino.

La 1.3, del 15 de octubre, sumó los vuelos ([decisión 0016](./decisiones/0016-vuelos.md)): la consulta acepta `solo_por_tierra`; `traslado.medios` puede empezar con `avion`, `traslado.vuelos` lista los vuelos de la ida y `traslado.fuente` vale `red_vial_y_vuelos` cuando se vuela; el costo suma `vuelos` a su desglose; y una sugerencia puede proponer volar (`solo_por_tierra: false`). No quitó nada de la 1.2. Cambió, eso sí, la propiedad 7 (§3): el presupuesto ya no solo ordena las tres rutas, también entra a elegirlas.

La 1.2, del 1 de octubre, sumó el tren y el bote: `traslado.medios` dice con qué se hace la ida (carretera, tren o bote), `traslado.acceso` vale `sin_acceso_terrestre` cuando la ida necesita bote, y el costo cobra los pasajes. No quita nada de la 1.1, que conectó el motor y sumó el día de un viaje de ida y vuelta en el día (`ida_visita_y_vuelta`) y tres consultas de apoyo: `/v1/opciones`, `/v1/polos/{id}` y `GET /v1/eventos` (§4). Desde el 2 de octubre responde también `POST /v1/eventos`, con el que un municipio publica un evento (§4.1): la 1.2 ya lo anunciaba y ya traía su modelo, así que la versión no sube. La revisión del equipo sigue antes del 5 de octubre. Desde el 7 de octubre el motor propone entre 194 polos, uno por pueblo donde se duerme, y valora las paradas con otra escala (más abajo, «Cómo decide el motor», y [decisión 0013](./decisiones/0013-un-polo-por-pueblo.md)); ningún campo cambia, así que la versión sigue en 1.2. Ese día cambió también la propiedad 3 (§3): un día de solo viaje, sin visitas, puede llegar a 9 horas ([decisión 0014](./decisiones/0014-dia-de-solo-viaje.md)). Y desde el 8 de octubre no propone un viaje con más días de camino que de visita ([decisión 0015](./decisiones/0015-mas-dias-alla-que-en-el-camino.md)).

## 1 · La consulta

Viaja en la URL: `GET /v1/viajes?origen=lima&mes=7&dias=6&intereses=historia&intereses=playa`. Es la misma consulta que lleva el enlace para compartir, porque el motor es determinista: la misma consulta con la misma versión de datos devuelve el mismo viaje. No hace falta guardar itinerarios ni tener cuentas ([decisión 0001](./decisiones/0001-sin-login-y-enlace-compartible.md)).

| Campo | Tipo | Obligatorio | Valores | En el formulario |
|---|---|---|---|---|
| `origen` | texto | no, `lima` por defecto | uno de los 24 identificadores de la tabla de abajo | Punto de partida |
| `mes` | entero | sí, salvo que venga `fecha_inicio` | 1 a 12 | Mes de viaje, el único campo forzoso |
| `fecha_inicio` | fecha ISO | no | `2026-07-20` | Opcional: con ella cada día lleva fecha y los eventos se cruzan día a día. Con bus de noche, es el día en que se llega: el bus sale la noche anterior (desde 1.6) |
| `dias` | entero | no, 6 por defecto | 1 a 14, **contando la ida y la vuelta**. Con bus de noche, sus noches van aparte (desde 1.6) | Días disponibles |
| `intereses` | lista | no | `naturaleza`, `historia`, `gastronomia`, `caminatas`, `playa`, `fiestas`, `arquitectura`, `aventura` y, de noche, `vida_nocturna` (desde 1.5) | Chips de intereses; `vida_nocturna`, aparte, bajo «De noche» |
| `presupuesto` | entero | no | 100 a 50 000 soles por persona, todo el viaje | Presupuesto total |
| `altitud_max` | entero | no | 0 a 6 000 metros | Altitud máxima tolerada |
| `sorpresa` | booleano | no | `true` o `false` | Botón «Sorpréndeme» |
| `solo_por_tierra` | booleano | no, `false` por defecto | `true` o `false` | Interruptor «Vuelos», apagado. Sin él, el motor vuela a lo que por tierra queda a más de 16 horas (desde 1.3) |
| `destino` | entero | no | el número de una zona (`polo.id`). No va con `sorpresa` | Fila «A dónde», «Armar un viaje aquí» en la zona e «Ir a esta fiesta» en las fiestas (desde 1.4) |

Un campo que no está en la tabla se rechaza con 422, igual que un valor fuera de rango, un `destino` que no es el número de ninguna zona (`campo: "destino"`) o un `destino` con `sorpresa` (`campo: "consulta"`). Cada error llega como `{"campo": "dias", "mensaje": "Debe ser menor o igual que 14.", "tipo": "less_than_equal"}`, listo para mostrarlo junto al campo del formulario.

**Orígenes.** La capital o ciudad principal de cada región ([`pipeline/referencia/origenes.csv`](../pipeline/referencia/origenes.csv)):
`lima`, `arequipa`, `trujillo`, `chiclayo`, `piura`, `cusco`, `huancayo`, `iquitos`, `pucallpa`, `tacna`, `ica`, `cajamarca`, `puno`, `ayacucho`, `huaraz`, `huanuco`, `tarapoto`, `chachapoyas`, `abancay`, `huancavelica`, `puerto-maldonado`, `moquegua`, `cerro-de-pasco`, `tumbes`.

**Intereses.** Son el vocabulario del viajero y no la taxonomía de MINCETUR. Cada uno se traduce a categorías, subtipos y actividades de la ficha oficial; la tabla de equivalencias es un artefacto del pipeline y se documenta con cuántos recursos cubre cada interés. `vida_nocturna` es distinto: no atiende ninguna parada (`paradas: 0` en `/v1/opciones`, con `de_noche: true`), así que no cambia qué se visita de día. Cambia la noche, y pesa un poco al elegir la zona (§2, «Cómo decide el motor»). Con `naturaleza`, o sin ningún interés, el plan propone una noche de estrellas.

**Zonas.** La app no le pide al API la lista de zonas para elegir un destino: la busca en [`app/public/destinos.json`](../app/public/destinos.json), que escribe el pipeline ([`pipeline/destinos.py`](../pipeline/destinos.py)) con el nombre, las regiones y los lugares de cada zona, y se publica con la app. Así se busca aunque el API todavía esté despertando.

## 2 · La respuesta

```
Respuesta
├── version_contrato, version_datos      la versión de datos también va en el enlace (§6)
├── consulta                             la consulta tal como la entendió el motor
├── rutas[0..3]                          polos distintos, del mejor al peor; con destino, solo el de esa zona
│   ├── polo           id, nombre, región, base (donde se duerme), recursos, fuera_del_circuito
│   ├── puntaje, motivos[]               por qué este polo, en frases cortas
│   ├── estacionalidad veredicto del mes, lluvia, días con lluvia, horas de sol, temperaturas, mejores meses
│   ├── traslado       horas de ida de puerta a puerta, días que se van en ir y volver, con qué se va (avión, carretera,
│   │                  tren, bote), los vuelos de la ida, si por tierra haría falta bote y, si va de noche, las horas
│   │                  del bus (desde 1.6)
│   ├── dias[]         número, fecha, tipo (ida, visita, vuelta… o ida_visita_y_vuelta en un viaje de un día), horas, km
│   │   ├── paradas[]  orden, recurso (con su ficha oficial), hora de llegada, traslado y visita en minutos
│   │   ├── almuerzo   a qué hora, después de cuántas paradas, dónde y si cerca hay dónde comer (desde 1.6)
│   │   ├── noche      si se duerme en la zona y la consulta la pide: salir (lugares[], a pie de la base), estrellas
│   │   │              (cielo: desde dónde, noches despejadas del mes, la luna si hay fecha) o descanso (desde 1.5)
│   │   └── tranquilo  si es el primer día en la altura: medio día, sin subir más de 500 m ni caminatas largas (desde 1.7)
│   ├── costo          banda P20-P50-P80 en soles, desglose, si entra en el presupuesto
│   ├── eventos[]      fiestas y ferias que caen en las fechas: las del inventario, con la precisión de su fecha,
│   │                  y las que publicó un municipio (fuente «publicado»), con quién las publicó; cada una con su
│   │                  zona (polo, desde 1.4)
│   ├── avisos[]       estacionalidad, altitud, aclimatación, presupuesto, días, datos
│   └── indicadores    paradas, jerarquía media, paradas de jerarquía 3-4, altitud máxima, km, valor capturado
├── sin_resultado                        solo si no hay ninguna ruta: por qué y qué cambiar para que salga
└── atribucion[]                         fuentes y licencias que la app muestra junto al resultado
```

[`docs/ejemplos/respuesta_ilustrativa.json`](./ejemplos/respuesta_ilustrativa.json) es una respuesta del motor, tal cual, para `origen=lima&mes=7&dias=4&intereses=historia&intereses=naturaleza&presupuesto=700&altitud_max=3500` con los datos `2026.10.8`. Con `naturaleza`, trae su noche de estrellas; además, el almuerzo de cada día, dos viajes en bus de noche, a Trujillo y a Oxapampa, y en Huancayo, a 3 256 m, un primer día tranquilo. La genera [`generar_respuesta_ilustrativa.py`](./ejemplos/generar_respuesta_ilustrativa.py). Las pruebas lo validan contra el contrato, así que si el contrato cambia y el ejemplo no, CI falla.

Dos cosas del contrato no aparecen por ahora, y no por descuido: `estacionalidad.horas_sol` viaja en `null` porque el reanálisis no ve la neblina de la costa (da más de 9 horas de sol al día en la costa de Lima en julio) y publicarlo sería engañar; y `traslado.fuente = "estimado"` no aparece, porque el motor solo propone polos a los que se llega por su red (carretera, tren o bote) o en avión.

Los textos que el motor escribe para el viajero se muestran tal cual: `motivos`, la `nota` de cada día, el `titulo` y la `nota` de cada noche, los avisos, `estacionalidad.explicacion`, los supuestos del costo y `sin_resultado`. Dicen «zona» y «viaje», como la app, aunque los campos se sigan llamando `polo` y `rutas`. Y separan los miles y el «S/» de su monto con un espacio que no parte la línea (U+00A0), para que «3 500 m» o «S/ 706» no queden entre dos renglones.

### Cómo decide el motor

El detalle está en [`dreemgo/motor/viaje.py`](../dreemgo/motor/viaje.py) y en la [decisión 0009](./decisiones/0009-viaje-en-estrella.md). En corto:

- **Un viaje es una estrella:** se duerme en la base del polo y cada día sale un paseo que vuelve a ella. La base es un pueblo real de OpenStreetMap, elegido por lo cerca que deja las paradas y por el hospedaje que registra ([`pipeline/bases.py`](../pipeline/bases.py)).
- **Un polo es lo que se visita desde un pueblo:** los grupos del agrupamiento de la semana 6 que duermen en el mismo pueblo son un solo polo. Huaraz junta cuatro, y de 222 grupos quedan 194 polos ([decisión 0013](./decisiones/0013-un-polo-por-pueblo.md)).
- **Valor de una parada:** 1, 2, 6 o 24 según su jerarquía; 2 si MINCETUR no la jerarquizó. De un nivel al siguiente se multiplica por 2, por 3 y por 4, para que un lugar de jerarquía 4 pese más que una jornada llena de lugares corrientes. Es un supuesto del producto, todavía sin calibrar. Si la consulta trae intereses, la que no atiende ninguno vale la cuarta parte.
- **Días:** la ida y la vuelta, por carretera, en tren, en bote o con vuelo. Un día de solo viaje puede durar hasta 9 horas; una ida más larga se parte en partes iguales y se duerme a mitad de camino. Con vuelo, en cambio, se duerme junto a un aeropuerto: el de llegada, si el vuelo y lo de antes caben en el día, y si no, también el de salida, la noche antes de volar. El día de llegada y el de salida tienen visitas si, con el viaje, sobran al menos 90 minutos de una jornada de 8 horas. Como máximo seis paradas por día ([decisión 0014](./decisiones/0014-dia-de-solo-viaje.md)).
- **Bus de noche:** lo que por tierra toma de 7 a 16 horas, sin tren ni bote, en un viaje de dos días o más. Sale a las 19:00 o después, para llegar a eso de las 6:00; la vuelta, a la misma hora. Sus noches van fuera de los días, y el día 1 se visita desde una hora después de llegar, nunca antes de las 8:00. No va si ida y vuelta se llevan el 40 % de las horas del viaje, con sus noches: en dos días, hasta unas 9 horas y media por tramo. Se cobra a la misma tarifa por km que el bus de día, y sus noches no pagan hospedaje ([decisión 0019](./decisiones/0019-plan-creible.md)).
- **El almuerzo:** una hora que no cuenta en las 8 de la jornada. Va al terminar la primera visita después de las 12:30, en un lugar con dónde comer si lo hay a la hora; antes, desde las 11:30, si lo que sigue llega tarde; al llegar, si se llega después de las 14:00; o en la base. Dónde comer sale de OpenStreetMap y de Overture: restaurantes, cafés y comida rápida a menos de 1,5 km. Si no registran nada, `hay_donde_comer` es `false` y la app dice que lo lleves.
- **La jornada no se corre:** si el primer lugar abre tarde, se sale más tarde, pero se vuelve a la hora de siempre: el final del tope más la hora del almuerzo. Y no se espera más de una hora en la puerta de un lugar, sin contar el almuerzo.
- **El primer día en la altura:** si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, sea en bus, en bus de noche o en avión, el primer día en la base es tranquilo: 4 horas de jornada como mucho, más el almuerzo; ninguna parada a más de 500 m sobre la base; nada exigente, ni una caminata de acceso de más de 30 minutos ni una visita de más de 2 horas; y después de un bus de noche, desde las 9:00. Es el de llegada, si queda tiempo para visitar, o el siguiente, y `tranquilo` lo marca. La altura del origen es la de la base de la zona de su misma ciudad. Es la misma regla de la noche de descanso, y sale del Yellow Book del CDC: solo ejercicio suave en las primeras 48 horas ([decisión 0020](./decisiones/0020-primer-dia-tranquilo.md)).
- **Más días allá que en el camino:** no se propone un viaje que pasaría más días solo viajando que días en que se puede visitar. Un empate sí: a Huaraz con cuatro días, dos de viaje y dos allá. Sin vuelos, el Cusco desde Lima solo cabe con doce días o más ([decisión 0015](./decisiones/0015-mas-dias-alla-que-en-el-camino.md)).
- **Vuelos:** las 22 rutas regulares que salen de Lima; entre otros dos aeropuertos se vuela con escala en Lima. De puerta a puerta se suman el camino por tierra hasta el aeropuerto, dos horas antes del vuelo, el vuelo, media hora para salir y el camino hasta la base. Se vuela solo a lo lejano: si por tierra la ida pasa de 16 horas, que ya no se hacen en un bus de noche; si en avión se llega al menos media jornada antes, contando las noches del camino; y si ida y vuelta en avión no se llevan el 40 % de las horas del viaje, salvo con `destino` (desde 1.6). Nunca con `solo_por_tierra`. Así, desde Lima se vuela al Cusco, a Arequipa o a Iquitos, y a Huaraz o a Trujillo se va en bus de noche; y un fin de semana no se vuela, salvo a una zona elegida. `traslado.acceso` sigue hablando del camino por tierra: Iquitos sigue `sin_acceso_terrestre` aunque se vuele. El costo cobra cada tramo, de ida y de vuelta, en una banda que va de la tarifa más baja publicada a 2,2 veces esa ([decisión 0016](./decisiones/0016-vuelos.md)).
- **Tren y bote:** un camino puede ir en tren (a Machu Picchu) o en bote (a las islas del Titicaca, las Ballestas o por los ríos de la Amazonía). Subir o bajar cuesta 15 minutos, y a una parada se llega en bote solo si su ficha lo dice. La nota del día lo cuenta («En bote hasta Isla Taquile.») y el costo cobra cada tramo en tren y cada km en bote, con su fuente y su rango ([decisión 0010](./decisiones/0010-tren-y-botes.md)).
- **Qué y en qué orden:** orientación por equipos con inserción voraz, 2-opt y tres arranques; se queda el de más valor.
- **Puntaje:** (1 − λ) · calidad · temporada · noche · bus · presupuesto + λ · novedad, con λ = 0,3. La temporada multiplica por 1, 0,75 o 0,4 según el veredicto del mes. La noche, solo con `vida_nocturna`, multiplica por 1 si hay al menos cinco lugares para salir a pie de la base y, si no, por 0,6 más 0,08 por cada uno: una zona sin bares baja, pero no desaparece. El bus de noche multiplica por D / (D + 1) en un viaje de D días: sus dos noches pesan como un día más, para que un fin de semana no salga siempre lejos (desde 1.6). El presupuesto multiplica por (presupuesto / costo)² cuando el costo central lo pasa, y por 1 si no, y cuenta desde que se eligen las tres rutas: un viaje que lo pasa sale solo si es mucho mejor que los que entran (§3). «Sorpréndeme» sube λ a 0,5 y deja solo polos fuera del circuito de Lima y Cusco.
- **Eventos publicados:** se suman a `eventos[]` de las rutas que duermen o paran cerca, y nada más. No entran al puntaje ni a los motivos: publicar un evento no mueve ningún polo de su lugar (§4.1 y [decisión 0011](./decisiones/0011-eventos-publicados.md)).
- **Un destino:** con `destino`, el motor prepara y planifica solo esa zona, con las mismas reglas. El viaje es el mismo que arma cuando la elige él; solo cambia el puntaje, que la compara con las demás, y, desde la 1.6, puede volar donde él iría por tierra: con la zona elegida, el 40 % del viaje no impide volar. Si no sale, `sin_resultado.motivo` dice lo primero que lo impide: la altura de la base o de los lugares, que queda en la misma ciudad, que los días no alcanzan para ir y volver o se irían más en el camino que allá, o que no hay qué visitar en una jornada. Cada sugerencia cambia un solo campo y el motor ya comprobó que con ella el viaje sale: los menos días que hacen falta, un día si es la misma ciudad, volar, quitar el límite de altitud. La última es buscar en todas las zonas, con cuántos viajes aparecen. Si ningún cambio solo alcanza, el motivo dice qué cambios juntos sí: «Volando, cabe en 4 días» ([decisión 0017](./decisiones/0017-quiero-ir-a.md)).
- **De noche:** cada noche que se duerme en la base, desde el día en que se llega hasta la víspera del día en que se deja, puede traer un plan, y nada de él cambia el día. Un viaje de un día no tiene noche ([decisión 0018](./decisiones/0018-planes-de-noche.md)).
  - **Salir**, con `vida_nocturna`: bares, pubs, discotecas, karaokes y peñas a no más de 1,5 km en línea recta de la base, unos 25 minutos a pie. Salen de OpenStreetMap y de Overture Maps. Cada noche propone hasta tres, de tipos distintos si los hay, y la siguiente, otros tres. Cada lugar enlaza a su mapa, para verificar que siga abierto.
  - **Descanso**, con `vida_nocturna`: la primera noche en una base de 2 500 m o más, si se llega de al menos 1 000 m más abajo.
  - **Estrellas**, con `naturaleza` o sin ningún interés: una noche por viaje, desde la base si su cielo es oscuro, o en un observatorio o planetario a menos de 45 minutos si no. La noche no se propone en un mes en que no sale despejada ni una de cada cinco noches. Con fecha, es la noche con más horas sin luna; sin fecha, la segunda en la base.
- **Un viaje sale de su ciudad:** no se propone dormir en un polo cuya base queda a menos de media hora del origen, y un viaje de un día no cuenta las paradas de la misma ciudad.
- **Tres rutas, tres pueblos:** cada polo duerme en su propio pueblo, y la respuesta no repite el nombre de una base.

## 3 · Lo que el motor garantiza en cada respuesta

Son propiedades, no intenciones: desde que el motor se conecta, las pruebas las verifican sobre miles de consultas generadas al azar.

1. Ninguna parada supera `altitud_max`, ni la base donde se duerme (desde 1.7).
2. Los días del itinerario suman exactamente `dias`, con la ida y la vuelta incluidas. Con bus de noche, sus noches van aparte (desde 1.6).
3. Ninguna jornada con visitas pasa de 8 horas entre traslados y visitas, sin contar el almuerzo (desde 1.6). Un día de solo viaje, sin visitas, puede llegar a 9, con vuelo o sin él.
4. Toda parada enlaza a su ficha oficial de MINCETUR (RNF-01).
5. Un mes desaconsejado nunca aparece sin aviso, y si se descarta hay una alternativa (RF-01).
6. Un evento solo aparece si cae dentro de las fechas o del mes del viaje (RF-03).
7. El presupuesto ordena, elige y avisa. Con presupuesto salen tantas rutas como sin él; una que entra en el presupuesto y salía sin él sigue saliendo; y una que lo pasa sale con su aviso. Hasta la 1.2 el presupuesto solo ordenaba: las tres rutas eran las mismas con o sin él. Con vuelos, eso dejaba tres viajes en avión fuera del presupuesto donde había uno en bus que entraba ([decisión 0016](./decisiones/0016-vuelos.md)).
8. La misma consulta con la misma `version_datos` devuelve exactamente la misma respuesta. Los eventos publicados también son datos: la versión lleva su huella (§6).
9. Las rutas son de polos distintos. Con `destino` hay una como mucho, y es la de esa zona: la misma que el motor arma cuando la elige él, salvo el puntaje (desde 1.4) y salvo que puede volar donde él iría por tierra (desde 1.6).
10. Un dato que la fuente no trae viaja como `null`, nunca como un número inventado: la jerarquía que MINCETUR no asignó, la tarifa que la ficha no publica, las noches despejadas donde no hay de dónde sacarlas.
11. La noche no cambia el día. Con `vida_nocturna` o sin ella, en la misma zona, las paradas, sus horas, el traslado y el costo son los mismos. Y la noche sigue a la consulta: salir y descansar solo con `vida_nocturna`, estrellas solo con `naturaleza` o sin intereses y en una noche como mucho, cada lugar para salir a pie de la base, y ninguna noche en un día en que no se duerme en ella (desde 1.5).
12. Cada almuerzo va en su lugar: solo en un día con paradas, desde las 11:30, después de la parada que va antes y una hora antes de la que va después. Si no hay dónde comer registrado, es en una parada, nunca en la base. Y un día con paradas que no lo trae termina sus visitas antes de las 12:30 (desde 1.6).
13. El bus de noche va cuando debe: solo por carretera, de 7 a 16 horas, en un viaje de dos días o más, y si ida y vuelta no se llevan el 40 % de las horas del viaje, con sus noches; y lo que cumple todo eso va en él. Sale a las 19:00 o después, ningún día lleva horas de camino, el día 1 es de ida y el último de vuelta, y el día 1 se visita desde una hora después de llegar (desde 1.6).
14. El primer día en la altura es tranquilo. Si se duerme a 2 500 m o más y se llega desde 1 000 m o más abajo, un día y solo uno trae `tranquilo`, y es el primero en la base: sus visitas y traslados no pasan de 4 horas, ninguna parada sube más de 500 m sobre la base, ninguna tiene una caminata de acceso de más de 30 minutos ni una visita de más de 2 horas, y después de un bus de noche se sale desde las 9:00; el aviso de aclimatación dice qué día es. Si no, ningún día lo trae. Y no hay noche de descanso donde la altura no pesa (desde 1.7).

Las pruebas verifican además que, cuando no hay rutas, cada sugerencia de `sin_resultado`, aceptada sola, hace salir algún viaje.

Con eventos publicados valen las catorce, y las pruebas verifican una cosa más: lo publicado se suma a `eventos[]` de las rutas a las que les toca y no cambia nada más de la respuesta. Ni qué polos se proponen, ni su orden, ni sus motivos, sus días o su costo.

## 4 · Endpoints

| Método y ruta | Qué hace | Desde |
|---|---|---|
| `GET /v1/salud` | Estado, versión del servicio y de los datos | Ya |
| `GET /v1/viajes` | Hasta tres viajes para una consulta | 1.1 |
| `GET /v1/opciones` | Orígenes, intereses con sus etiquetas, cuántas paradas atienden y si son de noche (desde 1.5), y rangos del formulario, para no fijarlos en la app | 1.1 |
| `GET /v1/polos/{id}` | Ficha de un polo: sus paradas de mayor a menor jerarquía, su clima mes a mes, sus eventos de los próximos doce meses y su noche (desde 1.5): dónde salir, cuánta luz tiene su cielo y cuántas noches salen despejadas cada mes | 1.1 |
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

- **Dónde aparece.** En `GET /v1/eventos` siempre. Con coordenadas, también en `eventos[]` de las rutas y en la ficha de los polos que duermen o tienen algún lugar del inventario a 10 km o menos, en línea recta. Si varios polos duermen en el mismo pueblo, sale en todos. De esos polos, el que duerme más cerca es su zona (`polo`, desde 1.4): adonde lleva «Ir a esta fiesta». Sin coordenadas, o lejos de todo, `polo` es `null`.
- **Qué no cambia.** Ni qué polos se proponen, ni su orden, ni sus motivos (§3).
- **Corregir.** Publicar otra vez el mismo evento (mismo nombre, fechas, distrito, provincia, región y entidad, sin contar tildes ni mayúsculas) lo reemplaza: sirve para ponerle la ubicación o el enlace. Con otro nombre u otras fechas es otro evento.
- **Cuándo se ve.** Enseguida en el servidor que lo recibió y, en los demás, a los dos segundos como mucho. Si justo entonces falla el almacén, en un minuto.
- **Lo que todavía no hay:** retirar un evento por el API, saber por la respuesta todos los polos a los que tocó (dice su zona desde la 1.4) y ver la descripción.

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
| Sin equivalente | `solo_por_tierra` (desde 1.3) | Con vuelos, el Cusco o Iquitos caben en un viaje corto desde Lima; quien no quiere o no puede volar lo apaga |
| Sin equivalente | `destino` (desde 1.4) | Quien ya sabe a dónde quiere ir no busca tres propuestas: quiere saber si su viaje cabe y, si no, qué cambiar |
| Sin equivalente | `vida_nocturna` (desde 1.5) | El plan decía qué hacer de día y terminaba al volver a la base. Quien todavía tiene energía de noche quiere saber dónde salir |
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
| Sin equivalente | `dias[].noche` (desde 1.5): qué hacer esa noche, debajo de los lugares del día |
| Sin equivalente | `dias[].almuerzo` (desde 1.6): la hora del almuerzo, entre los lugares del día, y si conviene llevarlo |
| Sin equivalente | `traslado.bus_de_noche` (desde 1.6): a qué hora sale y llega el bus, en los datos del viaje y en la nota del día 1 y del último |
| Sin equivalente | `dias[].tranquilo` (desde 1.7): «Día tranquilo para acostumbrarte a la altura», en la lista de días, en el día y en el plan impreso |
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
https://oswaldoaqm.github.io/Alejandros-Team/?origen=lima&mes=7&dias=6&intereses=historia&v=2026.10.3
```

Los parámetros son los de la consulta, más `v`, la `version_datos` con que se calculó. Con un destino lo lleva también (`destino=36`), y el enlace abre directo ese viaje. Si al abrirlo la versión de datos cambió, la app lo dice («Este enlace se armó con los datos 2026.10.2. Lo que ves está calculado con los datos 2026.10.3…») en vez de mostrar otro viaje en silencio.

La versión de datos tiene dos partes: la de los artefactos del motor y, cuando hay eventos publicados, la huella de ese calendario: `2026.10.3-e3f9a1c`. Sin eventos publicados es solo `2026.10.3`. Si entre el enlace y lo que se ve cambió la primera parte, las rutas pueden ser otras. Si solo cambió la huella, las rutas son las mismas y lo que puede haber cambiado son los eventos que las acompañan: la app no avisa y pone en el enlace la versión vigente.

## 7 · Cómo se cambia el contrato

En un PR que toque a la vez `dreemgo/contrato.py`, este documento, el esquema del que salen los tipos de la app (`python docs/generar_openapi.py` y, en `app/`, `npm run tipos`) y, si hace falta, el ejemplo ilustrativo. Las pruebas fallan si el esquema guardado queda atrás del contrato. Un campo nuevo opcional sube la versión menor (de 1.1 a 1.2, por ejemplo); quitar o renombrar un campo sube la mayor (2.0) y se avisa a quien construye la app antes de fusionar.

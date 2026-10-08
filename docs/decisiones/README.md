# Registro de decisiones

Cada decisión de arquitectura o de método que alguien podría preguntar «¿por qué así?» queda aquí, con el contexto que la motivó y lo que implica. Una decisión no se borra: si cambia, se escribe otra que la reemplaza y se anota en la vieja.

| N.º | Decisión | Estado |
|---|---|---|
| [0001](./0001-sin-login-y-enlace-compartible.md) | Sin cuentas: el viaje se comparte por enlace | Vigente |
| [0002](./0002-stack-y-despliegue.md) | FastAPI en Lambda con imagen de contenedor; app estática en GitHub Pages | Vigente; sin OR-Tools y con receta para un host gratuito (actualización del 2 de octubre) |
| [0003](./0003-artefactos-precalculados.md) | El motor carga artefactos precalculados; no hay base relacional | Vigente; lo que publican los municipios lo versiona la 0011 |
| [0004](./0004-sin-modelos-supervisados.md) | Sin modelos supervisados: agrupamiento, reglas de clima y optimización | Vigente |
| [0005](./0005-historial-y-erratas.md) | Las entregas se etiquetan y se corrigen en su sitio con erratas | Vigente |
| [0006](./0006-clima-por-polo.md) | Clima diario en el centro de cada polo, no en la capital regional | Vigente; sin horas de sol (actualización del 1 de octubre) |
| [0007](./0007-red-vial-propia.md) | Tiempos de viaje sobre un extracto propio de OpenStreetMap | Vigente; su calibración la precisa la 0008 y la 0010 le suma el tren y los botes |
| [0008](./0008-calibrar-con-las-fichas.md) | Calibrar la red vial con los recorridos de las fichas | Vigente |
| [0009](./0009-viaje-en-estrella.md) | El viaje es una estrella desde la base de un polo | Vigente; el tren y los botes ya entran (0010), cada pueblo es la base de un solo polo, con otro valor por parada (0013), un día de solo viaje llega a 9 horas (0014) y ningún viaje pasa más días en el camino que allá (0015) |
| [0010](./0010-tren-y-botes.md) | El tren y los botes entran a la red; cada parada se ubica según su ficha | Vigente |
| [0011](./0011-eventos-publicados.md) | Los municipios publican eventos; lo publicado se suma sin mover las rutas | Vigente; lo publicado se ve en dos segundos en todos los servidores (actualización del 2 de octubre) |
| [0013](./0013-un-polo-por-pueblo.md) | Un polo por pueblo, y un valor que distingue lo imperdible | Vigente |
| [0014](./0014-dia-de-solo-viaje.md) | Un día de solo viaje puede durar nueve horas | Vigente |
| [0015](./0015-mas-dias-alla-que-en-el-camino.md) | Un viaje no pasa más días en el camino que allá | Vigente |

Formato de cada una: contexto, decisión, alternativas descartadas y consecuencias. Media página como máximo.

# 0034 · La revisión del profesor: el asistente, la comparación y los tableros

**Fecha:** 17 de noviembre de 2026 · **Estado:** vigente

## Contexto

El 13 de noviembre el profesor Carlos Dominguez nos entregó una copia revisada de DreemGO y pidió incorporarla al repositorio. Su copia parte de `main` del 9 de noviembre, el PR 50: de sus 538 archivos, 436 eran idénticos a los de ese día. Desde entonces fusionamos siete PRs, con las decisiones 0027 a 0033, el contrato hasta la 1.10 y los datos hasta la `2026.11.5`. Copiar su carpeta encima habría deshecho todo eso, así que se pasaron sus cambios sobre lo nuevo con una fusión de tres vías. Solo cinco archivos chocaron, y dos de ellos son generados (`openapi.json` y `esquema.d.ts`).

Su copia pasa sus propias pruebas: pytest entero y 304 de vitest. Sus notas, sus guías en Word y sus registros de cambios quedan en [`docs/revision_del_profesor/`](../revision_del_profesor/).

## Decisión

Entra todo lo que trae, con un cambio en el motor:

- **Arreglos.** Una consulta nueva ya no muestra un instante los viajes de la anterior. Si el navegador no deja borrar un guardado, la app ya no dice que lo borró. El API responde 503 si faltan archivos de datos y 422 si la fecha cae fuera del calendario, y acepta pedidos desde `127.0.0.1`. «Antes de ir» pide confirmar horarios, cierres, entradas y transporte. En `evaluacion/informe.py`, un viaje que nadie calificó deja la consulta pendiente en vez de contar como cero; con las notas del equipo no cambia ninguna cifra, porque los 196 viajes tienen nota.
- **«Compara antes de elegir».** Una tabla con las rutas lado a lado: costo P50 y P80, la ida y el puntaje.
- **El asistente, «¿Te ayudamos?».** Reconoce con reglas el origen, el mes, los días, el presupuesto y los intereses de una frase, y le pide los viajes al mismo `GET /v1/viajes` del planificador. No usa un modelo de lenguaje ni inventa destinos. También responde preguntas frecuentes sobre nueve temas.
- **El buzón.** `POST /v1/comentarios` recibe dudas sin nombre ni correo, de 10 a 1 000 caracteres y hasta tres por hora por sesión. El equipo las lee en `/#/equipo/comentarios` con la clave `DREEMGO_CLAVE_COMENTARIOS` ([`COMENTARIOS.md`](../COMENTARIOS.md)).
- **La actividad anónima y sus paneles.** Es voluntaria: solo se envía si el visitante marca la casilla del pie de página. Guarda tipos de acción y filtros del viaje, nunca nombres, correos, preguntas ni la dirección IP. El panel `/#/indicadores` muestra 24 indicadores sobre una simulación de 200 usuarios ficticios, o sobre la actividad real con la clave `DREEMGO_CLAVE_ANALITICA` ([`INDICADORES.md`](../INDICADORES.md)).
- **Los tableros de simulación.** `app/public/tablero-gerencial.html` y `app/public/tablero-negocio.html`, con 200 y 300 usuarios ficticios, compras y canales simulados ([`TABLERO_NEGOCIO_300.md`](../TABLERO_NEGOCIO_300.md)). DreemGO no vende nada: cada vez que se muestren hay que decir que es una simulación.
- **Lo pedido va primero.** Una ruta que no visita ninguna parada de lo pedido lo avisa («Este itinerario no incluye paradas registradas de…»). En su copia, además, se quitaba si otra ruta sí lo cubría, y por eso una consulta podía devolver una sola. Aquí se ordena detrás, sin quitarla: el viajero sigue viendo hasta tres opciones y sabe cuál no tiene lo que pidió. Con un destino elegido no se reordena nada. Es la propiedad 21 del contrato 1.11.

## Lo que se midió

Se midió sobre el motor de los datos `2026.11.5`, en las 40 consultas del kit y en 768 consultas con un interés: los 24 orígenes, 3 y 5 días, febrero y julio, y cada uno de los ocho intereses del día.

Ordenar detrás no cambia cuántas rutas salen: 120 en el kit y 2 288 en las 768, igual que antes. Sí cambia cuáles: como una ruta sin lo pedido compite al final, entra otra que lo cubre si la hay. En el kit cambia una consulta, la 23, donde La Pampa reemplaza a Moquegua. En las 768 cambian 65, y en 3 de ellas solo el orden. Con el motor de ahora, las propuestas del kit sin nota bajan de 31 a 30.

Con el filtro de su copia, en esas 768 consultas, 10 respuestas bajaban de dos o tres viajes a uno. Seis eran desde Iquitos (historia, gastronomía o caminatas, tres días) y cuatro de playa desde Chachapoyas o Pucallpa. Ninguna se quedaba sin viajes.

## Lo que queda

- **Dónde se guarda.** El buzón y la actividad real usan SQLite en el disco del servidor. Render, en el plan gratuito, borra ese disco cada vez que el servicio se duerme o se vuelve a desplegar, y en Lambda pasa lo mismo con `/tmp`. Mientras no se guarden en DynamoDB, lo que llegue se pierde, y los paneles reales lo muestran vacío. Las claves las configuran Miguel o Alejandro en el servidor; el código no trae ninguna.
- **El puntaje que muestra la comparación** es interno: sirve para ordenar, no es una nota que el viajero pueda leer como probabilidad.

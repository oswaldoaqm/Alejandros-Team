# 0017 · «Quiero ir a…»: el viaje a la zona elegida, y si no cabe, qué cambiar

**Fecha:** 16 de octubre de 2026 · **Estado:** vigente · Amplía la [0009](./0009-viaje-en-estrella.md) y suma `destino` al [contrato](../CONTRATO.md) (versión 1.4)

## Contexto

Hasta la 1.3 el motor solo proponía tres zonas. Quien ya sabía a dónde quería ir, a Machu Picchu, al Colca o a la Candelaria de Puno, no tenía cómo pedirlo. La zona de un viaje y el calendario de fiestas mostraban un lugar sin camino para armar el viaje hasta ahí. Y cuando un viaje no cabía, nadie decía por qué.

## Decisión

- **La consulta acepta `destino`**, el número de una zona, y no va con `sorpresa`. El motor prepara y planifica solo esa zona, con las reglas de siempre: el viaje es el mismo que arma cuando la elige él, salvo el puntaje.
- **Si no cabe, dice por qué**: lo primero que lo impide, en el orden en que el motor descarta una zona. Puede ser la altura de la base o de sus lugares, que queda en la misma ciudad, los días que no alcanzan para ir y volver, más días de camino que de visita o que no hay qué visitar en una jornada. Dice con qué se haría la ida y cuánto toma, y si no se vuela por ser corto el viaje, cuánto tomaría el avión.
- **Y qué cambiar.** Cada sugerencia cambia un solo campo, y el motor ya comprobó que con ella el viaje sale: los menos días que hacen falta, un día si es la misma ciudad, volar o quitar el límite de altitud. Cada una dice si el viaje que sale vuela. La última es buscar en todas las zonas. Si ningún cambio solo alcanza, el motivo dice qué cambios juntos sí: «Volando, cabe en 4 días».
- **La lista de zonas va con la app.** [`pipeline/destinos.py`](../../pipeline/destinos.py) escribe `app/public/destinos.json` (47 KB comprimido). La app busca ahí por el nombre de la zona, por uno de sus lugares o por su región. Ignora las tildes y junta las grafías del quechua y del castellano, como al elegir fotos: «cusco» encuentra Cuzco. Ordena por lo que valen los doce lugares más importantes de cada zona. Queropalca queda fuera: solo tiene caminatas de más de un día.
- **Tres entradas:**
  - la fila «A dónde» del formulario;
  - «Armar un viaje aquí», en la zona;
  - «Ir a esta fiesta», en la zona y en el calendario, que sale la víspera de la fiesta, o en su mes si dura más de una semana.
- **Cada evento dice su zona** (`Evento.polo`). La de los publicados es, de los polos en que salen, el que duerme más cerca.

## Alternativas descartadas

- **El destino como preferencia entre las tres.** La zona elegida saldría primera, pero junto a dos que nadie pidió, y sin decir por qué no cabe.
- **Un endpoint para la lista de zonas.** El API gratuito duerme, y la lista solo cambia con los datos. Como archivo estático la sirve Pages enseguida, como `fotos.json`.
- **Ordenar por todos los lugares de cada zona.** Al buscar «cusco», Kimbiri, con cincuenta y seis lugares corrientes, salía antes que Urubamba y Machu Picchu.
- **Sugerencias de dos cambios.** El contrato tiene un campo por sugerencia, y la app sabe aplicar uno. Lo dice el motivo.

## Consecuencias

- Desde Lima, en julio, hacen falta:
  - 3 días, en avión: el Cusco, Arequipa, Chachapoyas, Puerto Maldonado, Tarapoto y Cajamarca;
  - 4, en avión: Puno, Iquitos y Máncora;
  - 5, en avión: Machu Picchu y el Colca;
  - 4, en bus: Huaraz, Trujillo, Nasca y Ayacucho, porque todavía no hay buses de noche (el plan creíble).
- Con destino, una consulta que sale tarda 10 ms en la mediana. Una que no sale, con sus sugerencias, tarda 190 ms, como una de tres viajes.
- Las propiedades sortean un destino en una de cada tres consultas. Verifican que el viaje es el mismo que el motor arma solo y que cada sugerencia hace salir algún viaje.
- **Queda abierto si con destino se vuela en viajes cortos.** La [0016](./0016-vuelos.md) no vuela si ir y volver se lleva el 40 % del viaje, porque en un viaje corto rinde más quedarse cerca, y eso no aplica si la zona ya está elegida. Sin esa regla, el Cusco, Arequipa, Puno e Iquitos saldrían desde Lima en 2 días, con entre tres y seis horas de visita en todo el viaje y el aviso «dias». A cambio, el viaje dejaría de ser el que arma el motor cuando elige él. Lo decide el equipo.

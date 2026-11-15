# 0029 · Los avisos de seguridad y de entradas

**Fecha:** 12 de noviembre de 2026 · **Estado:** vigente · Suma los avisos `seguridad` y `entradas` al [contrato](../CONTRATO.md) (versión 1.8), con las propiedades 17 y 18, y cierra los puntos 9 y 13 de la [auditoría](../AUDITORIA.md)

## Contexto

Hay polos con paradas en el VRAEM, el valle de los ríos Apurímac, Ene y Mantaro: Kimbiri, Mazamari, San Martín de Pangoa, Llochegua y Chirumpiari duermen ahí. Sin intereses no salen en la rejilla de la auditoría, pero salen con intereses (Kimbiri está en cuatro consultas del kit) y se pueden elegir como destino, y el motor no avisaba nada. Canadá recomienda evitar todo viaje a la zona y Estados Unidos la tiene en su nivel 4, no viajar, por el narcotráfico y los remanentes de Sendero Luminoso.

Machu Picchu vende un número fijo de entradas por día, y el motor no lo decía. Del tren, que también tiene cupos, sí avisaba.

El 10 de noviembre, el PR 52, de Miguel, sumó tres avisos: uno de `acceso` en los viajes que pasan por Machu Picchu, con 5 600 entradas al día; otro de `acceso` cuando el polo se llama como una de seis zonas del VRAEM, y uno de `dias` cuando el viaje no tiene fecha y alguna parada no abre todos los días.

## Decisión

- La zona es la que delimita el Estado: los 37 distritos del ámbito de intervención directa del VRAEM, del D.S. 133-2022-PCM, que reemplazó el artículo 1 del D.S. 040-2016-PCM ([`zonas_de_seguridad.csv`](../../pipeline/referencia/zonas_de_seguridad.csv)). Un recurso de esos distritos lleva su zona, con el nombre que traiga la ficha (Kimbiri también se escribe Quimbiri). La base de un polo la lleva si es la capital de uno de esos distritos: la misma coordenada que OpenStreetMap marca como su centro.
- Si se duerme en la zona, o alguna parada está en ella, el primer aviso es de `seguridad`, con nivel `advertencia`: dice dónde, por qué y que se revisen las alertas vigentes. En una excursión de un día no se duerme en la base, así que la base no cuenta. El aviso no cambia el plan ni el puntaje. La propiedad 17 lo verifica.
- [`entradas_con_cupo.csv`](../../pipeline/referencia/entradas_con_cupo.csv) dice cuántas personas entran al día a un lugar y dónde se compran las entradas. Cada parada con cupo trae su aviso de `entradas`, con nivel `info`. Hoy, Machu Picchu: 4 500 al día y 5 600 en temporada alta, en tuboleto.cultura.pe y, solo 1 000 al día, en persona en Machu Picchu Pueblo. La propiedad 18 lo verifica.

## Alternativas descartadas

- Sacar del motor los polos del VRAEM: decidir si va es del viajero, y esconderlos no le dice nada a quien igual quiere ir.
- Marcar también el ámbito de influencia, o el área que lista Canadá, que suma provincias enteras: Abancay, Andahuaylas, Chincheros, Huanta, La Mar, Churcampa, Tayacaja, Concepción y Satipo, más Vilcabamba. Estados Unidos no las incluye, y el Estado no las trata como el VRAEM. Abancay, a donde el motor manda desde el Cusco, saldría con advertencia. Queda para decidirlo en equipo.
- Ubicar la base por el recurso más cercano: para Atalaya, el más cercano está a 5,6 km, en su distrito, y el siguiente a 5,7 km, en Río Tambo, que es del VRAEM. Cien metros cambiaban la zona.
- Dar el aforo del día según la fecha del viaje: el de 2027 todavía no se conoce.
- Dejar los dos avisos de `acceso` del PR 52 junto a estos: el viaje avisaba dos veces lo mismo y, en Machu Picchu, con dos cifras distintas. Los de esta decisión los reemplazan: el del VRAEM del PR 52 miraba solo el nombre del polo, y no sus paradas, y el de Machu Picchu daba la cifra de la temporada alta como la de todo el año. El de los días que no abre queda como está.

## Consecuencias

- Con los datos `2026.11.2`, 126 paradas en 9 polos llevan la zona, y 5 bases: Kimbiri, Chirumpiari, Mazamari, Llochegua y San Martín de Pangoa. Huanta, Atalaya, Chilcas y Huancavelica avisan solo si el viaje para en uno de sus lugares del VRAEM.
- En la rejilla de la auditoría, sin intereses, ningún viaje entra al VRAEM, y el aviso de entradas sale en los pocos que pasan por Machu Picchu, el 0,1 %. El de seguridad sale cuando se elige la zona o con intereses.
- El aviso del PR 52 de los lugares que no abren todos los días sale en el 85,1 % de los viajes de la rejilla, que no llevan fecha (2 922 de 3 432). Un aviso que sale casi siempre se deja de leer: queda por decidir con el equipo si sigue o si basta lo que dice cada fila del plan.
- Kumpirushiato, creado en 2021 (Ley 31142), no está en el decreto: sus 19 paradas, que se visitan desde Chirumpiari, no se marcan. Ese viaje igual avisa, porque Chirumpiari es la capital de Cielo Punco.
- Una base que no es capital de distrito no se reconoce, aunque esté en la zona. Hoy no hay ninguna.
- El mensaje nombra a Canadá y Estados Unidos con sus alertas de noviembre de 2026 y mayo de 2025. Si cambian, se cambia el mensaje (`ZONAS_DE_SEGURIDAD` en `dreemgo/motor/viaje.py`).
- La cifra de entradas de los días normales no es la misma en todas partes: Andina y El Peruano dicen 4 500, y La República (junio de 2026), 4 600. Va la de los medios del Estado.

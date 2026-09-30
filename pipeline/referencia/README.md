# Datos de referencia

Tablas pequeñas que escribimos a mano y que el pipeline usa como entrada. Cada fila dice de dónde sale.

| Archivo | Qué es | Fuente |
|---|---|---|
| `origenes.csv` | Las 24 ciudades desde donde se puede partir: la capital o ciudad principal de cada región, con Callao incluido en Lima. `id` es el valor que viaja en la consulta (`origen`). | Las mismas coordenadas que usaron las semanas 5 y 6 para la distancia a la capital regional. En San Martín la ciudad es Tarapoto, no la capital administrativa (Moyobamba), porque es donde llegan los buses y el aeropuerto. |
| `intereses.csv` | Qué intereses del contrato (los ocho chips de la app) atiende cada recurso, según su categoría, tipo, subtipo o las actividades que registra su ficha. Una fila `excluir_subtipo` quita el interés que daría la categoría: una playa no es «naturaleza» por ser sitio natural, sino «playa». | Criterio del equipo sobre la clasificación oficial de MINCETUR. Las actividades son las que registra cada ficha. |
| `duracion_visita.csv` | Minutos de visita típicos, sin contar el acceso, por subtipo, tipo o categoría: se usa la regla más específica que exista. | **Supuesto del equipo**, revisable: no hay una fuente oficial de tiempos de visita. La caminata o el bote para llegar salen de la ficha, no de aquí. |

# Mensajes de quienes usan DreemGO

El botón de ayuda permite dejar una duda, una sugerencia o el aviso de un problema. El texto del mensaje se guarda en un buzón del API, separado de las estadísticas de uso. Si el visitante aceptó compartir estadísticas, el panel registra únicamente que se envió un comentario; no recibe su contenido. No se solicita nombre ni correo y el sitio no promete una respuesta personal.

## Enviar

`POST /v1/comentarios` recibe este JSON:

```json
{
  "sesion": "d5834e52-cba4-45ee-9bd6-207b50961df5",
  "categoria": "duda",
  "mensaje": "¿Cómo se calcula el costo estimado?"
}
```

`categoria` admite `duda`, `sugerencia` o `problema`. `mensaje` debe tener entre 10 y 1000 caracteres después de quitar espacios al inicio y al final. El API responde `201` con un identificador y el estado `recibido`. Si la misma sesión envía más de tres mensajes en una hora, responde `429`. Los datos inválidos responden `422`.

## Leer como equipo

Configuren `DREEMGO_CLAVE_COMENTARIOS` en el servidor. Luego hagan `GET /v1/comentarios` con la cabecera `X-Clave-Comentarios` y esa clave. Se devuelven los últimos 50 mensajes; `?limite=10` cambia la cantidad entre 1 y 100. La clave no debe incluirse en el código del navegador ni compartirse con visitantes. Sin clave configurada, la lectura responde `403`.

La base SQLite se guarda por defecto en `~/.dreemgo/comentarios.sqlite3` (o en `/tmp/dreemgo/comentarios.sqlite3` si corre en AWS Lambda). Para elegir otra ruta, configuren `DREEMGO_COMENTARIOS_DB`. En un despliegue, esa ruta debe estar en almacenamiento persistente; de lo contrario los mensajes se perderán al recrear el servidor. No se guarda la dirección IP, el nombre ni el correo. La sesión aleatoria solo sirve para limitar envíos repetidos y no se devuelve en la consulta del equipo.

### Pantalla de lectura del equipo

Con el API en marcha y `DREEMGO_CLAVE_COMENTARIOS` configurada, abran `http://localhost:5173/#/equipo/comentarios`. Introduzcan la clave para ver los mensajes recibidos, sus categorías y la fecha en hora de Perú. «Actualizar» vuelve a consultar el API; «Cerrar buzón» borra la clave de esta pantalla y oculta los mensajes. La ruta no aparece en el menú público. La clave solo se mantiene en memoria mientras la pantalla está abierta: no se añade a la URL ni se guarda en el navegador.

Esta pantalla es una vista de lectura, no un chat en vivo ni un sistema para contestar. El control de acceso está en el API: ocultar el enlace de la navegación no protege los datos por sí solo. Para una prueba local basta la base SQLite; antes de recibir mensajes públicos se necesita un almacenamiento que sobreviva a reinicios y despliegues.

Esta es una herramienta para escuchar a quienes prueban el prototipo. Antes de usarla con público abierto, el equipo debe decidir quién revisará los mensajes y con qué frecuencia.

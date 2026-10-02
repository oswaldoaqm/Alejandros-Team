# La app de DreemGO

La web que usa el viajero: pregunta qué viaje quiere, muestra hasta tres rutas para comparar y abre el itinerario de la que elija, con su mapa, su costo, su mes y sus fiestas. Está pensada primero para celular, en español, y consume el API tal como lo define el [contrato](../docs/CONTRATO.md).

React 19, Vite, TypeScript y MapLibre GL. Sin librería de rutas ni de estado: la consulta vive en la URL, que es también el enlace para compartir ([decisión 0001](../docs/decisiones/0001-sin-login-y-enlace-compartible.md)).

## Correrla en tu máquina

Hace falta Node 22.12 o más nuevo, y el API corriendo.

```bash
# 1. El API, desde la raíz del repositorio
pip install -e ".[api]"
uvicorn dreemgo.api.app:app --port 8000

# 2. La app, en otra terminal
cd app
npm ci
npm run dev          # http://localhost:5173
```

La app busca el API en `http://localhost:8000`. Para apuntarla a otro, copia `.env.example` como `.env.local` y cambia `VITE_API_URL`. El API solo acepta pedidos de los orígenes de su lista (`DREEMGO_CORS`); ya trae `http://localhost:5173` y la dirección de GitHub Pages.

### Verla en un celular antes de desplegar

Con el celular y la computadora en la misma red wifi, y sabiendo la IP de la computadora en esa red (por ejemplo `192.168.1.20`):

1. El API, con la variable `DREEMGO_CORS=http://192.168.1.20:5173` y escuchando en toda la red: `uvicorn dreemgo.api.app:app --host 0.0.0.0 --port 8000`.
2. En `app/.env.local`, `VITE_API_URL=http://192.168.1.20:8000`; y la app con `npm run dev -- --host`.
3. En el celular, `http://192.168.1.20:5173`.

Así, sin `https`, el navegador no deja copiar ni usar el menú de compartir: «Compartir» muestra el enlace para copiarlo a mano. Publicada, sí funciona.

## Comandos

| Comando | Qué hace |
|---|---|
| `npm run dev` | Servidor de desarrollo, con recarga al guardar |
| `npm run build` | Revisa los tipos y construye `dist/` |
| `npm run preview` | Sirve `dist/` en el puerto 5173, como quedará publicado |
| `npm test` | Pruebas de cada pieza (vitest), sin red: usan un API de mentira |
| `npm run e2e` | Prueba de humo en un navegador de verdad, contra el API de verdad |
| `npm run revisar` | Estilo y errores comunes (Biome) y tipos (TypeScript) |
| `npm run formato` | Aplica el formato |
| `npm run tipos` | Regenera los tipos del contrato desde `docs/openapi.json` |

## Las pantallas

| Dirección | Pantalla | De dónde salen sus datos |
|---|---|---|
| `./` | El formulario | `GET /v1/opciones` |
| `./?origen=lima&mes=7&dias=6&…&v=2026.10.2` | Las rutas y el detalle de la primera | `GET /v1/viajes` |
| `…#/ruta/2` | Lo mismo, con la segunda ruta abierta | |
| `…#/editar` | El formulario con esa consulta | |
| `…#/polo/33` | La ficha de un polo: clima de los doce meses, lugares y fiestas | `GET /v1/polos/{id}` |
| `…#/calendario` | Fiestas y eventos de un mes | `GET /v1/eventos` |
| `./#/mis-viajes` | Los viajes guardados en este navegador | `localStorage` |
| `./#/acerca` | Cómo funciona y de dónde salen los datos | |

Los parámetros son los de la consulta del contrato, más `v`, la versión de datos con que se calculó. Si el enlace trae una versión que ya no es la vigente, la app lo avisa en vez de mostrar otro viaje en silencio. Lo que va después de `#` es de la app: GitHub Pages lo sirve sin configurar nada.

## Cómo está hecha

```
src/
├── main.tsx · App.tsx     arranque y marco: cabecera, pantalla según la URL, pie
├── ruta.ts                de la URL a la pantalla, y de la pantalla a la URL
├── consulta.ts            la consulta del viajero: ida y vuelta a la URL, chips y título
├── formato.ts · textos.ts números, fechas y frases, escritos como los escribe el motor
├── itinerario.ts          paradas numeradas de corrido: el mismo número en la lista y en el mapa
├── eventos.ts             en qué día del viaje cae un evento
├── almacen.ts             «Mis viajes», en el navegador
├── api/                   cliente del API y tipos generados del contrato
├── estado/                navegación, pedidos al API y título de la pestaña
├── piezas/                tarjeta de ruta, itinerario, mapa, banda de costo, clima…
├── vistas/                una por pantalla
└── pruebas/               el API de mentira y la preparación de las pruebas
```

- **Los tipos salen del contrato.** `src/api/esquema.d.ts` se genera de `docs/openapi.json`, y ese archivo, del API. Si el contrato cambia: `python docs/generar_openapi.py` en la raíz y `npm run tipos` aquí. Las pruebas del API fallan si `docs/openapi.json` queda atrás.
- **Lo que escribe el motor no se reescribe.** Motivos, avisos, notas de cada día y explicaciones del mes se muestran tal como llegan.
- **El mapa se descarga aparte.** MapLibre pesa más que todo el resto: va en su propio archivo y llega después de que la página ya se puede leer. El fondo es de [OpenFreeMap](https://openfreemap.org/), gratis y sin clave. Si el fondo o el mapa fallan, el itinerario dice lo mismo con palabras.
- **El estado no va solo en el color.** El veredicto del mes y los avisos llevan siempre su ícono y su palabra.

### Cuánto pesa

Con gzip, lo que se baja al abrir la app son unos 95 kB (89 de JavaScript y 5 de estilos). El mapa suma unos 440 kB la primera vez que se abre una ruta (MapLibre, su proceso de dibujo y sus estilos), y después queda en la caché del navegador.

## Pruebas

`npm test` corre las pruebas de la lógica y de cada pantalla en jsdom, con un API de mentira que responde con [`docs/ejemplos/respuesta_ilustrativa.json`](../docs/ejemplos/respuesta_ilustrativa.json), una respuesta real del motor: si el contrato cambia y el ejemplo se regenera, las pruebas corren contra la forma nueva.

`npm run e2e` abre un navegador (Playwright), en tamaño de celular y de escritorio, y recorre lo que hace un viajero contra el API de verdad: llenar el formulario, comparar rutas, abrir el mapa, compartir el enlace, guardar el viaje. También revisa que ninguna pantalla se desborde a lo ancho y pasa [axe](https://github.com/dequelabs/axe-core) por cada una (sin contar el mapa, cuya alternativa accesible es el itinerario). Levanta el API y la app por su cuenta, o usa los que ya estén corriendo. Playwright va con versión fija en `package.json`, porque el navegador que se baja tiene que ser el de esa versión. La primera vez hay que bajarlo:

```bash
(cd .. && pip install -e ".[api]")   # el API que van a usar las pruebas
npx playwright install chromium
npm run e2e
```

## Publicarla

La app se publica en GitHub Pages con [`.github/workflows/pages.yml`](../.github/workflows/pages.yml), en cada cambio de `main` que toque `app/`. La dirección del API se toma de la variable `API_URL` del repositorio (Settings → Secrets and variables → Actions → Variables); sin ella, la app publicada busca el API en `http://localhost:8000`, que solo sirve en la máquina de quien lo tenga corriendo. Después de crear o cambiar la variable hay que volver a publicar: Actions → Pages → Run workflow.

El build usa rutas relativas (`base: "./"`), así que la misma carpeta `dist/` sirve en `https://oswaldoaqm.github.io/Alejandros-Team/` o en cualquier otro lugar.

## Lo que todavía no hace

- Al imprimir o guardar como PDF sale todo menos el mapa.
- Con muchas paradas muy juntas, las marcas del mapa se enciman al ver todo el viaje; al elegir un día se abren para que se lea cada número.
- No hay modo oscuro.

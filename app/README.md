# La app de DreemGO

La web que usa el viajero: pregunta qué viaje quiere, propone hasta tres para comparar y abre el que elija en su propia pantalla, con su plan día por día, su mapa, su costo, su mes y sus fiestas. Tiene además una página para que una municipalidad publique un evento. Está pensada primero para celular, en español, con tema claro y oscuro, y consume el API tal como lo define el [contrato](../docs/CONTRATO.md).

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

Para probar «Publicar un evento», el API tiene que arrancar con una clave de publicador; sin ella responde que no acepta publicaciones. La clave es la que después se escribe en el formulario, y lo publicado queda en memoria hasta que el API se cierra:

```bash
# macOS, Linux o Git Bash
DREEMGO_CLAVE_PUBLICADOR=una-clave-para-probar uvicorn dreemgo.api.app:app --port 8000
```

```powershell
# PowerShell, en Windows
$env:DREEMGO_CLAVE_PUBLICADOR = "una-clave-para-probar"
uvicorn dreemgo.api.app:app --port 8000
```

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
| `./` | El formulario: cinco filas, y las que piden elegir abren su hoja | `GET /v1/opciones` |
| `./?origen=lima&mes=7&dias=6&…&v=2026.10.2` | Los tres viajes, en tarjetas para comparar | `GET /v1/viajes` |
| `…#/ruta/2` | El segundo viaje, en su pantalla: por qué conviene, qué saber antes de ir, el plan día por día con su mapa, el costo, el clima y las fiestas. Cada lugar abre su hoja | |
| `…#/editar` | El formulario con esa consulta | |
| `…#/polo/33` | La zona de un viaje: sus lugares, su clima de los doce meses y sus fiestas | `GET /v1/polos/{id}` |
| `…#/calendario` | Fiestas: los eventos de un mes, por región; `#/calendario/11` lo abre en noviembre | `GET /v1/eventos` |
| `./#/mis-viajes` | Guardados: los viajes guardados en este navegador | `localStorage` |
| `./#/acerca` | Cómo funciona y de dónde salen los datos | |
| `./#/publicar` | Para municipalidades: publicar un evento, con su lugar marcado en un mapa | `POST /v1/eventos` |

Los parámetros son los de la consulta del contrato, más `v`, la versión de datos con que se calculó. Si el enlace trae una versión que ya no es la vigente, la app lo avisa en vez de mostrar otro viaje en silencio. Si lo único que cambió son los eventos que publicaron los municipios (la parte `-e…` de la versión), los viajes son los mismos: no avisa y pone en el enlace la versión vigente. Lo que va después de `#` es de la app: GitHub Pages lo sirve sin configurar nada.

La app le habla al viajero con sus palabras: un «polo» del contrato es una zona, y una «ruta», un viaje. Las direcciones conservan las del contrato (`#/polo/33`, `#/ruta/2`), así los enlaces que ya se compartieron siguen abriendo.

## Cómo está hecha

```
src/
├── main.tsx · App.tsx     arranque y marco: cabecera, barra de abajo en celular, pantalla según la URL, pie
├── ruta.ts                de la URL a la pantalla, y de la pantalla a la URL
├── consulta.ts            la consulta del viajero: ida y vuelta a la URL, y cómo se dice en una frase
├── formato.ts · textos.ts números, fechas y frases, escritos como los escribe el motor
├── itinerario.ts          las paradas de cada día, numeradas igual en la lista y en el mapa
├── flor.ts                la flor de cada viaje y los pétalos del mapa: uno por día
├── fotos.ts               qué foto va con cada viaje, zona y lugar, y cómo se le pide a Wikimedia
├── eventos.ts             en qué día del viaje cae un evento
├── version.ts             la versión de datos: qué parte es de los artefactos y cuál de lo publicado
├── regiones.ts            las 25 regiones, cada una con su ciudad, para el mapa de publicar
├── almacen.ts             «Guardados», en el navegador
├── api/                   cliente del API y tipos generados del contrato
├── estado/                navegación, pedidos al API, la lista de fotos y título de la pestaña
├── estilos/               un archivo por pantalla; base.css tiene los colores y las medidas de los dos temas
├── piezas/                tarjeta de viaje, plan del día, hojas, los dos mapas, banda de costo, clima…
├── vistas/                una por pantalla
└── pruebas/               el API de mentira y la preparación de las pruebas
public/fotos.json          la lista de fotos: la escribe el pipeline, no se edita a mano
```

- **Los tipos salen del contrato.** `src/api/esquema.d.ts` se genera de `docs/openapi.json`, y ese archivo, del API. Si el contrato cambia: `python docs/generar_openapi.py` en la raíz y `npm run tipos` aquí. Las pruebas del API fallan si `docs/openapi.json` queda atrás.
- **Lo que escribe el motor no se reescribe.** Motivos, avisos, notas de cada día y explicaciones del mes se muestran tal como llegan.
- **El mapa es un croquis del viaje, no el trazo del camino.** Cada día es un pétalo que sale de donde se duerme y abarca los lugares de ese día; con un día elegido, sus lugares llevan el número que tienen en la lista. La misma idea, en chico, es la flor de cada viaje: el tallo es el camino de ida y cada pétalo, un día, más largo cuanto más lejos se llega y más ancho cuantos más lugares tiene.
- **El mapa se descarga aparte.** MapLibre pesa más que todo el resto: va en su propio archivo y llega después de que la página ya se puede leer. El fondo es de [OpenFreeMap](https://openfreemap.org/), gratis y sin clave. Si el fondo no carga, queda un lienzo liso con los pétalos y los lugares en su sitio; si el mapa entero falla, el plan dice lo mismo con palabras; y al publicar un evento, el lugar se puede escribir en coordenadas.
- **Las fotos son de Wikimedia Commons y no se guardan aquí.** `public/fotos.json` dice qué foto va con cada lugar y con cada pueblo donde se duerme: lo escribe el pipeline, que las elige con Wikidata y deja fuera las que se quitaron al revisarlas ([`pipeline/README.md`](../pipeline/README.md#fotos)). La app le pide a Wikimedia la miniatura del ancho que necesita cada pantalla y muestra el autor y la licencia junto a cada foto. Lo que no tiene foto, o cuya foto no carga, muestra la flor del viaje o un ícono.
- **Claro y oscuro.** La app sigue el tema del sistema. Los colores y las medidas de los dos temas están en `src/estilos/base.css`; el mapa es claro en los dos.
- **La clave de publicador no se guarda.** Vive en la página mientras está abierta y viaja solo en la cabecera del pedido que publica.
- **El estado no va solo en el color.** El veredicto del mes y los avisos llevan siempre su ícono y su palabra.

### Cuánto pesa

Con gzip, lo que se baja al abrir la app son unos 113 kB (101 de JavaScript y 11 de estilos). La lista de fotos suma 25 kB la primera vez que se ven unos viajes, y cada foto llega del tamaño de su recuadro. El mapa suma unos 440 kB la primera vez que se abre un viaje (MapLibre, su proceso de dibujo y sus estilos), y después queda en la caché del navegador.

## Pruebas

`npm test` corre las pruebas de la lógica y de cada pantalla en jsdom, con un API de mentira que responde con [`docs/ejemplos/respuesta_ilustrativa.json`](../docs/ejemplos/respuesta_ilustrativa.json), una respuesta real del motor: si el contrato cambia y el ejemplo se regenera, las pruebas corren contra la forma nueva.

`npm run e2e` abre un navegador (Playwright), en tamaño de celular y de escritorio, y recorre lo que hace un viajero contra el API de verdad: llenar el formulario, comparar los viajes, abrir uno con su mapa, compartir el enlace, guardarlo y volver a él. Y lo que hace una municipalidad: publicar un evento marcando su lugar en el mapa y verlo en el calendario. También revisa que ninguna pantalla se desborde a lo ancho y pasa [axe](https://github.com/dequelabs/axe-core) por cada una (sin contar el mapa, cuya alternativa accesible es el itinerario). Levanta el API y la app por su cuenta, o usa los que ya estén corriendo; si el API ya estaba corriendo sin la clave de la prueba, la de publicar se salta y lo dice. Playwright va con versión fija en `package.json`, porque el navegador que se baja tiene que ser el de esa versión. La primera vez hay que bajarlo:

```bash
(cd .. && pip install -e ".[api]")   # el API que van a usar las pruebas
npx playwright install chromium
npm run e2e
```

## Publicarla

La app se publica en GitHub Pages con [`.github/workflows/pages.yml`](../.github/workflows/pages.yml), en cada cambio de `main` que toque `app/`. La dirección del API se toma de la variable `API_URL` del repositorio (Settings → Secrets and variables → Actions → Variables); sin ella, la app publicada busca el API en `http://localhost:8000`, que solo sirve en la máquina de quien lo tenga corriendo. Después de crear o cambiar la variable hay que volver a publicar: Actions → Pages → Run workflow.

El build usa rutas relativas (`base: "./"`), así que la misma carpeta `dist/` sirve en `https://oswaldoaqm.github.io/Alejandros-Team/` o en cualquier otro lugar.

## Lo que todavía no hace

- Al imprimir o guardar como PDF sale el viaje entero, con la dirección de cada ficha oficial, pero sin el mapa ni la foto.
- Con todo el viaje a la vista, los lugares muy juntos se enciman en el mapa; al elegir un día se corren hacia los lados para que se lea cada número.
- Tienen foto 479 de las 4 465 paradas y 77 de los 161 imperdibles. Lo demás muestra la flor del viaje o un ícono.
- Las fotos y el fondo del mapa se piden a Wikimedia y a OpenFreeMap desde el navegador del viajero. Sin ellos la app sigue: sin fotos y con el mapa liso.
- El mapa es claro también con el tema oscuro.
- Un viaje guardado o compartido se recuerda por su puesto entre los tres. Si los datos cambian, en ese puesto puede salir otro viaje: la app lo avisa.
- El motor todavía dice «polo» y «rutas» en algunos de sus textos (el aviso del clima, el veredicto del mes, cuando no hay viajes), donde la app dice «zona» y «viajes».

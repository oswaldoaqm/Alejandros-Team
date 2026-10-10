// Lo que comparten los mapas de la app: el fondo, el proceso que dibuja y los textos en español.
// Solo lo importan las piezas que se descargan aparte (MapaRuta y MapaLugar): MapLibre pesa
// más que todo el resto de la app.

import { LngLatBounds, type StyleSpecification, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// MapLibre dibuja con un proceso aparte (worker), que vive en su propio archivo. Con
// `?worker&url`, Vite lo empaqueta con lo que necesita y devuelve su dirección.
import urlDelTrabajador from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";
import { type NombreDeIcono, TRAZOS } from "./Icono";

setWorkerUrl(urlDelTrabajador);

/** El fondo es de OpenFreeMap: gratis y sin clave. */
export const ESTILO = "https://tiles.openfreemap.org/styles/positron";

/**
 * Si el fondo no carga (sin conexión, o un servidor caído), el mapa sigue: un lienzo liso donde
 * el recorrido y los lugares quedan en su sitio, como un croquis.
 */
export const ESTILO_LISO: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "fondo", type: "background", paint: { "background-color": "#e8edf0" } }],
};

export const PERU = new LngLatBounds([-81.4, -18.4], [-68.6, 0.1]);

// Lo que MapLibre dice por su cuenta, en español.
export const TEXTOS = {
  "AttributionControl.ToggleAttribution": "Mostrar u ocultar las fuentes del mapa",
  "Map.Title": "Mapa",
  "Marker.Title": "Marcador",
  "NavigationControl.ZoomIn": "Acercar",
  "NavigationControl.ZoomOut": "Alejar",
  "Popup.Close": "Cerrar",
  "CooperativeGesturesHandler.WindowsHelpText": "Usa Ctrl y la rueda para acercar el mapa",
  "CooperativeGesturesHandler.MacHelpText": "Usa ⌘ y la rueda para acercar el mapa",
  "CooperativeGesturesHandler.MobileHelpText": "Usa dos dedos para mover el mapa",
};

/** Un botón para usar de marca en el mapa. Lo que dice va en `rotulo`: lo lee un lector de pantalla. */
export function boton(clase: string, rotulo: string, texto = ""): HTMLButtonElement {
  const elemento = document.createElement("button");
  elemento.type = "button";
  elemento.className = clase;
  elemento.textContent = texto;
  elemento.setAttribute("aria-label", rotulo);
  return elemento;
}

/** Uno de los íconos de la app, para ponerlo dentro de una marca del mapa. */
export function icono(nombre: NombreDeIcono, tamano = 16): SVGSVGElement {
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  for (const [atributo, valor] of Object.entries({
    width: String(tamano),
    height: String(tamano),
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    "stroke-width": "2",
    "stroke-linecap": "round",
    "stroke-linejoin": "round",
    "aria-hidden": "true",
    focusable: "false",
  })) {
    svg.setAttribute(atributo, valor);
  }
  for (const d of TRAZOS[nombre]) {
    const trazo = document.createElementNS(ns, "path");
    trazo.setAttribute("d", d);
    svg.append(trazo);
  }
  return svg;
}

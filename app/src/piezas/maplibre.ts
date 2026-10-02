// Lo que comparten los mapas de la app: el fondo, el proceso que dibuja y los textos en español.
// Solo lo importan las piezas que se descargan aparte (MapaRuta y MapaLugar): MapLibre pesa
// más que todo el resto de la app.

import { LngLatBounds, setWorkerUrl } from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
// MapLibre dibuja con un proceso aparte (worker), que vive en su propio archivo. Con
// `?worker&url`, Vite lo empaqueta con lo que necesita y devuelve su dirección.
import urlDelTrabajador from "maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url";

setWorkerUrl(urlDelTrabajador);

/** El fondo es de OpenFreeMap: gratis y sin clave. */
export const ESTILO = "https://tiles.openfreemap.org/styles/positron";

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

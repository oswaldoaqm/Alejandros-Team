// El mapa de una ruta: la base y las paradas numeradas en el orden del recorrido.
// Va en su propio archivo del build (MapLibre pesa más que todo el resto de la app) y solo
// se descarga cuando el mapa está por verse.

import { LngLatBounds, Map as MapaLibre, Marker, NavigationControl, Popup } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { abanico, type PuntoDeMapa } from "../itinerario";
import { sinMovimiento } from "../movimiento";
import { boton, ESTILO, PERU, TEXTOS } from "./maplibre";

const FUENTE = "recorrido";
const CAPAS = ["recorrido-fondo", "recorrido"] as const;

export interface BaseDeMapa {
  nombre: string;
  lat: number;
  lon: number;
}

export interface PropsDeMapa {
  /** Dónde se duerme. null en un viaje de ida y vuelta en el día: no hay base. */
  base: BaseDeMapa | null;
  puntos: PuntoDeMapa[];
  /** El día que se resalta; null, todo el viaje. */
  dia: number | null;
}

function recorridos(base: BaseDeMapa | null, puntos: PuntoDeMapa[]) {
  const dias = [...new Set(puntos.map((p) => p.dia))];
  const extremo = base ? [[base.lon, base.lat]] : [];
  return {
    type: "FeatureCollection" as const,
    features: dias
      .map((dia) => ({
        type: "Feature" as const,
        properties: { dia },
        geometry: {
          type: "LineString" as const,
          // Cada paseo sale de la base y vuelve a ella. Es el orden de visita, no el trazo de la vía.
          coordinates: [
            ...extremo,
            ...puntos.filter((p) => p.dia === dia).map((p) => [p.lon, p.lat]),
            ...extremo,
          ],
        },
      }))
      .filter((linea) => linea.geometry.coordinates.length >= 2),
  };
}

function limites(base: BaseDeMapa | null, puntos: PuntoDeMapa[]): LngLatBounds | null {
  const todos: [number, number][] = puntos.map((p) => [p.lon, p.lat]);
  if (base) todos.push([base.lon, base.lat]);
  const primero = todos[0];
  if (!primero) return null;
  const caja = new LngLatBounds(primero, primero);
  for (const punto of todos) caja.extend(punto);
  return caja;
}

// Un solo punto no tiene tamaño: sin tope, el mapa se acercaría hasta la puerta.
const ENCUADRE = { padding: 48, maxZoom: 13 };

function globo(titulo: string, detalle: string): HTMLElement {
  const caja = document.createElement("div");
  const fuerte = document.createElement("strong");
  fuerte.textContent = titulo; // los nombres vienen de fuera: siempre como texto
  const resto = document.createElement("span");
  resto.textContent = detalle;
  caja.append(fuerte, resto);
  return caja;
}

interface Marcado {
  dia: number;
  marcador: Marker;
}

const JUNTOS_PX = 30; // dos marcadores más cerca que esto se tapan
const PASO_PX = 30; // lo que se corre cada uno: un marcador con su borde

interface Dibujo {
  marcados: Marcado[];
  base: Marker | null;
  /** Si el viaje tiene paradas en más de un día. */
  variosDias: boolean;
}

/**
 * Con un día elegido, corre hacia los lados las paradas que se tapan, para que se lean todos
 * sus números. Con todo el viaje a la vista cada parada queda en su sitio: son demasiadas
 * para abrirlas sin sacarlas del mapa.
 */
function separar(mapa: MapaLibre, dibujo: Dibujo, dia: number | null): void {
  for (const m of dibujo.marcados) m.marcador.setOffset([0, 0]);
  if (dia === null && dibujo.variosDias) return;
  const visibles = dibujo.marcados.filter((m) => dia === null || m.dia === dia);
  const posiciones = visibles.map((m) => mapa.project(m.marcador.getLngLat()));
  // La base va primera y no se mueve: lo que se le encima se abre hacia su derecha.
  const todas = dibujo.base ? [mapa.project(dibujo.base.getLngLat()), ...posiciones] : posiciones;
  const corrimiento = abanico(todas, JUNTOS_PX, dibujo.base !== null);
  const salto = dibujo.base ? 1 : 0;
  visibles.forEach((m, i) => {
    m.marcador.setOffset([(corrimiento[i + salto] ?? 0) * PASO_PX, 0]);
  });
}

/** Deja a la vista el recorrido de un día, o los de todo el viaje. */
function resaltar(mapa: MapaLibre, dibujo: Dibujo, dia: number | null): void {
  for (const capa of CAPAS) {
    if (!mapa.getLayer(capa)) continue;
    mapa.setFilter(capa, dia === null ? null : ["==", ["get", "dia"], dia]);
    // Con varios días a la vez las líneas se cruzan: van más tenues, y firmes al elegir un día.
    mapa.setPaintProperty(capa, "line-opacity", dia === null && dibujo.variosDias ? 0.45 : 1);
  }
}

const SIN_DIBUJO: Dibujo = { marcados: [], base: null, variosDias: false };

export default function MapaRuta({ base, puntos, dia }: PropsDeMapa) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaLibre | null>(null);
  const dibujo = useRef<Dibujo>(SIN_DIBUJO);
  const diaElegido = useRef(dia);
  const [fallo, ponerFallo] = useState<string | null>(null);

  useEffect(() => {
    if (!contenedor.current) return;
    let nuevo: MapaLibre;
    try {
      nuevo = new MapaLibre({
        container: contenedor.current,
        style: ESTILO,
        bounds: limites(base, puntos) ?? PERU,
        fitBoundsOptions: ENCUADRE,
        cooperativeGestures: true, // con un dedo se sigue bajando por la página
        attributionControl: { compact: true },
        locale: TEXTOS,
        // Siempre con el norte arriba y visto desde arriba: es un croquis del recorrido.
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
      });
    } catch {
      ponerFallo("Este navegador no puede dibujar el mapa. El itinerario tiene las mismas paradas.");
      return;
    }
    mapa.current = nuevo;
    nuevo.touchZoomRotate.disableRotation();
    nuevo.keyboard.disableRotation();
    nuevo.addControl(new NavigationControl({ showCompass: false }), "top-right");
    nuevo.on("zoomend", () => separar(nuevo, dibujo.current, diaElegido.current));
    nuevo.on("error", (evento) => {
      // Sin el fondo, las paradas igual quedan en su sitio: se avisa y se sigue.
      if (!nuevo.isStyleLoaded())
        ponerFallo("No se pudo cargar el fondo del mapa. Las paradas siguen en su lugar.");
      console.warn("Mapa:", evento.error?.message ?? evento);
    });
    nuevo.on("load", () => {
      ponerFallo(null);
      nuevo.addSource(FUENTE, { type: "geojson", data: recorridos(base, puntos) });
      nuevo.addLayer({
        id: "recorrido-fondo",
        type: "line",
        source: FUENTE,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#fcfcfb", "line-width": 5 },
      });
      nuevo.addLayer({
        id: "recorrido",
        type: "line",
        source: FUENTE,
        layout: { "line-cap": "round", "line-join": "round" },
        paint: { "line-color": "#1c5cab", "line-width": 2, "line-dasharray": [1.5, 2] },
      });
      resaltar(nuevo, dibujo.current, diaElegido.current);
    });

    const marcados = puntos.map((p) => {
      const rotulo = `Parada ${p.numero}: ${p.nombre}. Día ${p.dia}, ${p.hora}.`;
      const marcador = new Marker({ element: boton("marcador", rotulo, String(p.numero)) })
        .setLngLat([p.lon, p.lat])
        .setPopup(new Popup({ offset: 16 }).setDOMContent(globo(p.nombre, `Día ${p.dia} · ${p.hora}`)))
        .addTo(nuevo);
      return { dia: p.dia, marcador };
    });
    // La base va al final para quedar encima: es el punto del que sale cada día.
    const marcaBase = base
      ? new Marker({ element: boton("marcador marcador--base", `${base.nombre}: aquí se duerme.`) })
          .setLngLat([base.lon, base.lat])
          .setPopup(new Popup({ offset: 14 }).setDOMContent(globo(base.nombre, "Aquí se duerme")))
          .addTo(nuevo)
      : null;
    dibujo.current = { marcados, base: marcaBase, variosDias: new Set(puntos.map((p) => p.dia)).size > 1 };

    return () => {
      dibujo.current = SIN_DIBUJO;
      mapa.current = null;
      nuevo.remove();
    };
  }, [base, puntos]);

  useEffect(() => {
    diaElegido.current = dia;
    const actual = mapa.current;
    if (!actual) return;
    for (const { dia: suDia, marcador } of dibujo.current.marcados) {
      const apagado = dia !== null && suDia !== dia;
      // La opacidad se pide a MapLibre, que es quien la maneja en cada marcador.
      marcador.setOpacity(apagado ? "0.22" : "1");
      marcador.getElement().classList.toggle("marcador--apagado", apagado);
    }
    resaltar(actual, dibujo.current, dia); // si las capas todavía no están, lo hace el `load` de arriba
    separar(actual, dibujo.current, dia);
    const visibles = dia === null ? puntos : puntos.filter((p) => p.dia === dia);
    const caja = limites(base, visibles);
    if (caja) actual.fitBounds(caja, { ...ENCUADRE, animate: !sinMovimiento() });
  }, [dia, base, puntos]);

  return (
    <div className="mapa">
      <div ref={contenedor} className="mapa__lienzo" />
      {fallo ? (
        <p className="mapa__fallo" role="status">
          {fallo}
        </p>
      ) : null}
    </div>
  );
}

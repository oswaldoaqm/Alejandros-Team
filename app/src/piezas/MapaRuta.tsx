// El mapa de un viaje. Cada día es un pétalo: sale de donde se duerme, pasa por sus lugares en
// orden y vuelve (src/flor.ts). Con todo el viaje a la vista se ve la flor entera y cada lugar es
// un punto; con un día elegido, su pétalo queda pleno, sus lugares numerados como en la lista y
// lo demás se apaga. Es el orden de las visitas, no el trazo de la vía.
// Va en su propio archivo del build (MapLibre pesa más que todo el resto de la app) y solo se
// descarga cuando el mapa está por verse.

import {
  type ExpressionSpecification,
  LngLatBounds,
  Map as MapaLibre,
  Marker,
  NavigationControl,
  Popup,
} from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { petaloGeografico } from "../flor";
import { abanico, type PuntoDeMapa } from "../itinerario";
import { sinMovimiento } from "../movimiento";
import { boton, ESTILO, ESTILO_LISO, icono, PERU, TEXTOS } from "./maplibre";

const FUENTE = "petalos";
// El lago de la marca. El fondo del mapa es claro también en modo oscuro: va el tono de día.
const LAGO = "#0b5c80";
const BLANCO = "#ffffff";

export interface BaseDeMapa {
  nombre: string;
  lat: number;
  lon: number;
}

export interface PropsDeMapa {
  /** Dónde se duerme. null en un viaje de ida y vuelta en el día: no hay base. */
  base: BaseDeMapa | null;
  puntos: PuntoDeMapa[];
  /** El día elegido; null, todo el viaje. */
  dia: number | null;
  /** Con todo el viaje a la vista, tocar un lugar elige su día. */
  elegirDia?: (dia: number) => void;
  /** Con un día elegido, tocar uno de sus lugares abre su hoja. */
  abrirLugar?: (dia: number, codigo: string) => void;
}

type LonLat = [number, number];

function petalos(base: BaseDeMapa | null, puntos: PuntoDeMapa[]) {
  const dias = [...new Set(puntos.map((p) => p.dia))].sort((a, b) => a - b);
  const centro: LonLat | null = base ? [base.lon, base.lat] : null;
  return {
    type: "FeatureCollection" as const,
    features: dias.flatMap((dia) => {
      const lugares = puntos.filter((p) => p.dia === dia).map((p): LonLat => [p.lon, p.lat]);
      const anillo = petaloGeografico(centro, lugares);
      if (!anillo || anillo.length < 4) return [];
      return [
        {
          type: "Feature" as const,
          properties: { dia },
          geometry: { type: "Polygon" as const, coordinates: [anillo] },
        },
      ];
    }),
  };
}

/** La caja que contiene a los lugares, la base y los pétalos (que se abren un poco más allá). */
function limites(base: BaseDeMapa | null, puntos: PuntoDeMapa[], dia: number | null): LngLatBounds | null {
  const visibles = dia === null ? puntos : puntos.filter((p) => p.dia === dia);
  const todos: LonLat[] = visibles.map((p) => [p.lon, p.lat]);
  if (base) todos.push([base.lon, base.lat]);
  for (const f of petalos(base, visibles).features) todos.push(...(f.geometry.coordinates[0] ?? []));
  const primero = todos[0];
  if (!primero) return null;
  const caja = new LngLatBounds(primero, primero);
  for (const punto of todos) caja.extend(punto);
  return caja;
}

// Un solo punto no tiene tamaño: sin tope, el mapa se acercaría hasta la puerta. El margen deja
// lugar a las marcas, que miden casi 40 px, y a los botones de acercar.
const ENCUADRE = { padding: { top: 40, bottom: 36, left: 36, right: 56 }, maxZoom: 14 };

const JUNTOS_PX = 28; // dos lugares más cerca que esto se tapan
const PASO_PX = 30; // lo que se corre cada uno: una marca con su borde

interface Marcado {
  punto: PuntoDeMapa;
  marcador: Marker;
}

interface Dibujo {
  marcados: Marcado[];
  base: Marker | null;
}

const SIN_DIBUJO: Dibujo = { marcados: [], base: null };

/** Con un día elegido, corre hacia los lados los lugares que se tapan, para que se lean sus números. */
function separar(mapa: MapaLibre, dibujo: Dibujo, dia: number | null): void {
  for (const m of dibujo.marcados) m.marcador.setOffset([0, 0]);
  if (dia === null) return;
  const visibles = dibujo.marcados.filter((m) => m.punto.dia === dia);
  const posiciones = visibles.map((m) => mapa.project(m.marcador.getLngLat()));
  // La base va primera y no se mueve: lo que se le encima se abre hacia su derecha.
  const todas = dibujo.base ? [mapa.project(dibujo.base.getLngLat()), ...posiciones] : posiciones;
  const corrimiento = abanico(todas, JUNTOS_PX, dibujo.base !== null);
  const salto = dibujo.base ? 1 : 0;
  visibles.forEach((m, i) => {
    m.marcador.setOffset([(corrimiento[i + salto] ?? 0) * PASO_PX, 0]);
  });
}

/** El pétalo del día elegido, pleno y encima; los demás, apenas. Con todo el viaje, la flor pareja. */
function pintar(mapa: MapaLibre, dia: number | null): void {
  if (!mapa.getLayer("petalos-linea")) return;
  const elegido: ExpressionSpecification = ["==", ["get", "dia"], dia ?? -1];
  const segun = (siElegido: number, siNo: number, todos: number) =>
    dia === null ? todos : (["case", elegido, siElegido, siNo] as ExpressionSpecification);
  mapa.setPaintProperty("petalos-relleno", "fill-opacity", segun(0.14, 0.03, 0.08));
  mapa.setPaintProperty("petalos-casco", "line-opacity", segun(0.9, 0, 0.7));
  mapa.setPaintProperty("petalos-linea", "line-opacity", segun(1, 0.14, 0.85));
  mapa.setPaintProperty("petalos-linea", "line-width", segun(2.5, 1, 1.75));
  const encima = segun(1, 0, 0);
  mapa.setLayoutProperty("petalos-relleno", "fill-sort-key", encima);
  mapa.setLayoutProperty("petalos-linea", "line-sort-key", encima);
  mapa.setLayoutProperty("petalos-casco", "line-sort-key", encima);
}

function ponerPetalos(mapa: MapaLibre, base: BaseDeMapa | null, puntos: PuntoDeMapa[]): void {
  if (mapa.getSource(FUENTE)) return;
  mapa.addSource(FUENTE, { type: "geojson", data: petalos(base, puntos) });
  mapa.addLayer({ id: "petalos-relleno", type: "fill", source: FUENTE, paint: { "fill-color": LAGO } });
  mapa.addLayer({
    id: "petalos-casco",
    type: "line",
    source: FUENTE,
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": BLANCO, "line-width": 6 },
  });
  mapa.addLayer({
    id: "petalos-linea",
    type: "line",
    source: FUENTE,
    layout: { "line-cap": "round", "line-join": "round" },
    paint: { "line-color": LAGO },
  });
}

export default function MapaRuta({ base, puntos, dia, elegirDia, abrirLugar }: PropsDeMapa) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaLibre | null>(null);
  const dibujo = useRef<Dibujo>(SIN_DIBUJO);
  const diaElegido = useRef(dia);
  // Las marcas se crean una vez por viaje; lo que hacen al tocarlas se lee de aquí, siempre al día.
  const acciones = useRef({ elegirDia, abrirLugar });
  acciones.current = { elegirDia, abrirLugar };
  const [fallo, ponerFallo] = useState<string | null>(null);

  useEffect(() => {
    if (!contenedor.current) return;
    let nuevo: MapaLibre;
    try {
      nuevo = new MapaLibre({
        container: contenedor.current,
        style: ESTILO,
        bounds: limites(base, puntos, diaElegido.current) ?? PERU,
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
      ponerFallo("Este navegador no puede dibujar el mapa. El plan de abajo tiene los mismos lugares.");
      return;
    }
    mapa.current = nuevo;
    nuevo.touchZoomRotate.disableRotation();
    nuevo.keyboard.disableRotation();
    nuevo.addControl(new NavigationControl({ showCompass: false }), "top-right");
    nuevo.on("moveend", () => separar(nuevo, dibujo.current, diaElegido.current));

    // Si el fondo no llega, se cambia por uno liso: el recorrido se dibuja igual.
    let fondoListo = false;
    let liso = false;
    nuevo.on("error", (evento) => {
      if (!fondoListo && !liso) {
        liso = true;
        nuevo.setStyle(ESTILO_LISO);
      }
      console.warn("Mapa:", evento.error?.message ?? evento);
    });
    nuevo.on("style.load", () => {
      fondoListo = true;
      ponerPetalos(nuevo, base, puntos);
      pintar(nuevo, diaElegido.current);
    });

    const marcados = puntos.map((punto) => {
      const elemento = boton(
        "pin",
        `Día ${punto.dia}, lugar ${punto.numero}: ${punto.nombre}, a las ${punto.hora}.`,
        String(punto.numero),
      );
      elemento.addEventListener("click", (evento) => {
        evento.stopPropagation();
        if (diaElegido.current === null) acciones.current.elegirDia?.(punto.dia);
        else acciones.current.abrirLugar?.(punto.dia, punto.codigo);
      });
      const marcador = new Marker({ element: elemento }).setLngLat([punto.lon, punto.lat]).addTo(nuevo);
      return { punto, marcador };
    });
    // La base va al final para quedar encima: es el punto del que sale cada día.
    let marcaBase: Marker | null = null;
    if (base) {
      const elemento = boton("pin-base", `${base.nombre}: aquí duermes.`);
      elemento.append(icono("cama", 16));
      const globo = document.createElement("div");
      const fuerte = document.createElement("strong");
      fuerte.textContent = base.nombre; // los nombres vienen de fuera: siempre como texto
      const detalle = document.createElement("span");
      detalle.textContent = "Aquí duermes";
      globo.append(fuerte, detalle);
      marcaBase = new Marker({ element: elemento })
        .setLngLat([base.lon, base.lat])
        .setPopup(new Popup({ offset: 18, closeButton: false }).setDOMContent(globo))
        .addTo(nuevo);
    }
    dibujo.current = { marcados, base: marcaBase };

    return () => {
      dibujo.current = SIN_DIBUJO;
      mapa.current = null;
      nuevo.remove();
    };
  }, [base, puntos]);

  useEffect(() => {
    diaElegido.current = dia;
    const actual = mapa.current;
    for (const { punto, marcador } of dibujo.current.marcados) {
      const elemento = marcador.getElement();
      elemento.classList.toggle("pin--punto", dia === null);
      elemento.classList.toggle("pin--oculto", dia !== null && punto.dia !== dia);
    }
    if (!actual) return;
    pintar(actual, dia); // si las capas todavía no están, lo hace el `style.load` de arriba
    separar(actual, dibujo.current, dia);
    const caja = limites(base, puntos, dia);
    if (caja) actual.fitBounds(caja, { ...ENCUADRE, animate: !sinMovimiento() });
  }, [dia, base, puntos]);

  return (
    <div className="mapa-viaje__marco">
      <div ref={contenedor} className="mapa-viaje__lienzo" />
      {fallo ? (
        <p className="mapa-viaje__fallo" role="status">
          {fallo}
        </p>
      ) : null}
    </div>
  );
}

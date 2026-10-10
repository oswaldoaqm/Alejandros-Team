// El mapa donde se marca el lugar de un evento: un toque pone la marca, y la marca se puede
// arrastrar. Como el de las rutas, va en su propio archivo del build.

import { LngLatBounds, Map as MapaLibre, Marker, NavigationControl } from "maplibre-gl";
import { useEffect, useRef, useState } from "react";
import { sinMovimiento } from "../movimiento";
import { dentroDelPeru } from "../regiones";
import { boton, ESTILO, PERU, TEXTOS } from "./maplibre";

export interface Lugar {
  lat: number;
  lon: number;
}

export interface PropsDeMapaLugar {
  /** Dónde está la marca; null si todavía no se puso. */
  lugar: Lugar | null;
  /** Adónde acercarse mientras no hay marca: la ciudad principal de la región elegida. */
  cerca: Lugar | null;
  alElegir: (lugar: Lugar) => void;
}

// El mapa no se va del país: un poco de margen alrededor para poder encuadrar las fronteras.
const ALREDEDOR_DEL_PERU = new LngLatBounds([-85, -21], [-65, 3]);
const ZOOM_DE_CIUDAD = 11;
const ZOOM_DE_MARCA = 13;

/** Cinco decimales son cerca de un metro: más es ruido. */
function redondear(n: number): number {
  return Math.round(n * 1e5) / 1e5;
}

export default function MapaLugar({ lugar, cerca, alElegir }: PropsDeMapaLugar) {
  const contenedor = useRef<HTMLDivElement>(null);
  const mapa = useRef<MapaLibre | null>(null);
  const marca = useRef<Marker | null>(null);
  const [fallo, ponerFallo] = useState<string | null>(null);
  const [fuera, ponerFuera] = useState(false);
  // Lo último que se sabe, para los manejadores del mapa, que se registran una sola vez.
  // Este efecto va primero: los de abajo ya lo encuentran al día.
  const elegir = useRef(alElegir);
  const lugarActual = useRef(lugar);
  useEffect(() => {
    elegir.current = alElegir;
    lugarActual.current = lugar;
  });

  useEffect(() => {
    if (!contenedor.current) return;
    let nuevo: MapaLibre;
    const inicial = lugarActual.current;
    try {
      nuevo = new MapaLibre({
        container: contenedor.current,
        style: ESTILO,
        ...(inicial ? { center: [inicial.lon, inicial.lat], zoom: ZOOM_DE_MARCA } : { bounds: PERU }),
        maxBounds: ALREDEDOR_DEL_PERU,
        cooperativeGestures: true, // con un dedo se sigue bajando por la página
        attributionControl: { compact: true },
        locale: TEXTOS,
        dragRotate: false,
        pitchWithRotate: false,
        touchPitch: false,
      });
    } catch {
      ponerFallo("Este navegador no puede dibujar el mapa. Puedes escribir las coordenadas más abajo.");
      return;
    }
    mapa.current = nuevo;
    nuevo.touchZoomRotate.disableRotation();
    nuevo.keyboard.disableRotation();
    nuevo.addControl(new NavigationControl({ showCompass: false }), "top-right");
    nuevo.on("error", (evento) => {
      if (!nuevo.isStyleLoaded())
        ponerFallo("No se pudo cargar el fondo del mapa. Puedes escribir las coordenadas más abajo.");
      console.warn("Mapa:", evento.error?.message ?? evento);
    });
    nuevo.on("load", () => ponerFallo(null));
    nuevo.on("click", (evento) => {
      const lat = redondear(evento.lngLat.lat);
      const lon = redondear(evento.lngLat.lng);
      const vale = dentroDelPeru(lat, lon);
      ponerFuera(!vale);
      if (vale) elegir.current({ lat, lon });
    });
    return () => {
      marca.current = null;
      mapa.current = null;
      nuevo.remove();
    };
  }, []);

  // La marca sigue al lugar, venga del mapa o de las coordenadas escritas a mano.
  useEffect(() => {
    const actual = mapa.current;
    if (!actual) return;
    if (!lugar) {
      marca.current?.remove();
      marca.current = null;
      return;
    }
    if (!marca.current) {
      const nueva = new Marker({
        element: boton("marcador marcador--lugar", "El lugar del evento. Se puede arrastrar."),
        draggable: true,
      });
      nueva.on("dragend", () => {
        const { lat, lng } = nueva.getLngLat();
        const vale = dentroDelPeru(lat, lng);
        ponerFuera(!vale);
        if (vale) elegir.current({ lat: redondear(lat), lon: redondear(lng) });
        else if (lugarActual.current) nueva.setLngLat([lugarActual.current.lon, lugarActual.current.lat]);
      });
      marca.current = nueva.setLngLat([lugar.lon, lugar.lat]).addTo(actual);
    } else {
      marca.current.setLngLat([lugar.lon, lugar.lat]);
    }
    ponerFuera(false);
    // Si la marca quedó fuera de la vista (se escribieron las coordenadas), el mapa va hasta ella.
    if (!actual.getBounds().contains([lugar.lon, lugar.lat])) {
      actual.easeTo({
        center: [lugar.lon, lugar.lat],
        zoom: Math.max(actual.getZoom(), ZOOM_DE_MARCA),
        animate: !sinMovimiento(),
      });
    }
  }, [lugar]);

  // Al elegir la región, el mapa se acerca a su ciudad principal; con la marca puesta no se mueve.
  useEffect(() => {
    const actual = mapa.current;
    if (!actual || !cerca || lugarActual.current) return;
    actual.easeTo({ center: [cerca.lon, cerca.lat], zoom: ZOOM_DE_CIUDAD, animate: !sinMovimiento() });
  }, [cerca]);

  return (
    <div className="mapa mapa--elegir">
      <div ref={contenedor} className="mapa__lienzo" />
      {fallo || fuera ? (
        <p className="mapa__fallo" role="status">
          {fallo ?? "Ese punto queda fuera del Perú."}
        </p>
      ) : null}
    </div>
  );
}

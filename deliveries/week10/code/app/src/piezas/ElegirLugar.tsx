// Dónde es un evento: se marca en el mapa o se escriben las coordenadas. MapLibre se descarga
// aparte, cuando esta pieza aparece; si no llega, quedan las coordenadas.

import { lazy, Suspense, useEffect, useId, useState } from "react";
import { dentroDelPeru, PERU } from "../regiones";
import { Limite } from "./Limite";
import type { Lugar } from "./MapaLugar";

const MapaLugar = lazy(() => import("./MapaLugar"));

const MENOS = "−"; // el signo menos de imprenta: «−9,5278»

/** −9.5278 → «−9,52780». */
export function coordenada(n: number): string {
  return n.toFixed(5).replace(".", ",").replace("-", MENOS);
}

/** «−9,5278», «-9.5278» o « -9,5278 » → −9.5278; null si no es un número. */
export function leerCoordenada(texto: string): number | null {
  const limpio = texto.trim().replace(MENOS, "-").replace(",", ".");
  if (!/^-?\d+(\.\d+)?$/.test(limpio)) return null;
  return Number(limpio);
}

interface Props {
  lugar: Lugar | null;
  /** Adónde se acerca el mapa mientras no hay marca. */
  cerca: Lugar | null;
  alElegir: (lugar: Lugar | null) => void;
}

export function ElegirLugar({ lugar, cerca, alElegir }: Props) {
  const id = useId();
  const [lat, ponerLat] = useState("");
  const [lon, ponerLon] = useState("");

  // Lo que se marca en el mapa se ve también en las casillas. Si lo escrito ya dice ese
  // número, se deja como está: no se le cambia el texto a quien todavía está escribiendo.
  useEffect(() => {
    const poner = (valor: number | undefined) => (antes: string) =>
      valor === undefined ? "" : leerCoordenada(antes) === valor ? antes : coordenada(valor);
    ponerLat(poner(lugar?.lat));
    ponerLon(poner(lugar?.lon));
  }, [lugar]);

  const escribir = (nuevaLat: string, nuevaLon: string) => {
    ponerLat(nuevaLat);
    ponerLon(nuevaLon);
    const a = leerCoordenada(nuevaLat);
    const b = leerCoordenada(nuevaLon);
    if (a !== null && b !== null && dentroDelPeru(a, b)) alElegir({ lat: a, lon: b });
  };
  const a = leerCoordenada(lat);
  const b = leerCoordenada(lon);
  const aMedias = (lat.trim() !== "" || lon.trim() !== "") && (a === null || b === null);
  const fuera = a !== null && b !== null && !dentroDelPeru(a, b);

  return (
    <div className="lugar">
      <Limite
        respaldo={
          <p className="mapa mapa--elegir mapa--vacio" role="status">
            No se pudo cargar el mapa. Puedes escribir las coordenadas aquí abajo.
          </p>
        }
      >
        <Suspense
          fallback={
            <p className="mapa mapa--elegir mapa--vacio" role="status">
              Cargando el mapa…
            </p>
          }
        >
          <MapaLugar lugar={lugar} cerca={cerca} alElegir={alElegir} />
        </Suspense>
      </Limite>

      <p className="lugar__lectura">
        <span role="status">
          {lugar ? `Marcado en ${coordenada(lugar.lat)}, ${coordenada(lugar.lon)}.` : "Todavía sin marcar."}
        </span>{" "}
        {lugar ? (
          <button type="button" className="boton boton--texto" onClick={() => alElegir(null)}>
            Quitar la marca
          </button>
        ) : null}
      </p>

      <details className="plegable plegable--chico">
        <summary>Escribir las coordenadas</summary>
        <div className="formulario__par">
          <div className="campo">
            <label htmlFor={`${id}-lat`}>Latitud</label>
            <input
              id={`${id}-lat`}
              type="text"
              inputMode="text"
              autoComplete="off"
              placeholder={coordenada(-9.5278)}
              value={lat}
              aria-describedby={`${id}-coordenadas`}
              aria-invalid={aMedias || fuera}
              onChange={(e) => escribir(e.target.value, lon)}
            />
          </div>
          <div className="campo">
            <label htmlFor={`${id}-lon`}>Longitud</label>
            <input
              id={`${id}-lon`}
              type="text"
              inputMode="text"
              autoComplete="off"
              placeholder={coordenada(-77.5278)}
              value={lon}
              aria-describedby={`${id}-coordenadas`}
              aria-invalid={aMedias || fuera}
              onChange={(e) => escribir(lat, e.target.value)}
            />
          </div>
        </div>
        <p id={`${id}-coordenadas`}>
          {fuera
            ? `Ese punto queda fuera del Perú: la latitud va de ${coordenada(PERU.latMin)} a ${coordenada(PERU.latMax)} y la longitud de ${coordenada(PERU.lonMin)} a ${coordenada(PERU.lonMax)}.`
            : aMedias
              ? "Hacen falta las dos, en grados decimales y con su signo."
              : "En grados decimales y con su signo, como las da un mapa en el celular: al sur y al oeste son negativas."}
        </p>
      </details>
    </div>
  );
}

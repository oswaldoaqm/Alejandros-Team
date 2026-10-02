// El mapa de una ruta, con su selector de días. MapLibre se descarga aparte, cuando esta
// pieza aparece: hasta entonces (y si falla) el itinerario dice lo mismo con palabras.

import { lazy, Suspense } from "react";
import { Limite } from "./Limite";
import type { PropsDeMapa } from "./MapaRuta";

const MapaRuta = lazy(() => import("./MapaRuta"));

interface Props extends PropsDeMapa {
  /** Los días que tienen paradas, en orden. */
  dias: number[];
  elegirDia: (dia: number | null) => void;
}

export function Mapa({ base, puntos, dia, dias, elegirDia }: Props) {
  return (
    <div className="mapa-marco">
      {dias.length > 1 ? (
        <fieldset className="selector-dias">
          <legend className="solo-lector">Qué días se ven en el mapa</legend>
          <label className="chip chip--elegible chip--chico">
            <input type="radio" name="dia-del-mapa" checked={dia === null} onChange={() => elegirDia(null)} />
            <span>Todo el viaje</span>
          </label>
          {dias.map((d) => (
            <label key={d} className="chip chip--elegible chip--chico">
              <input type="radio" name="dia-del-mapa" checked={dia === d} onChange={() => elegirDia(d)} />
              <span>Día {d}</span>
            </label>
          ))}
        </fieldset>
      ) : null}
      <Limite
        respaldo={
          <p className="mapa mapa--vacio" role="status">
            No se pudo cargar el mapa. El itinerario tiene las mismas paradas, en el mismo orden.
          </p>
        }
      >
        <Suspense
          fallback={
            <p className="mapa mapa--vacio" role="status">
              Cargando el mapa…
            </p>
          }
        >
          <MapaRuta base={base} puntos={puntos} dia={dia} />
        </Suspense>
      </Limite>
      <p className="ayuda mapa__leyenda">
        <span className="marcador marcador--muestra" aria-hidden="true">
          1
        </span>{" "}
        parada, en el orden del recorrido
        {base ? (
          <>
            {" · "}
            <span className="marcador marcador--base marcador--muestra" aria-hidden="true" /> {base.nombre},
            donde se duerme
          </>
        ) : null}
        {" · "}la línea une las paradas de cada día; no es el trazo de la vía
        {dias.length > 1 ? ". Elige un día para ver solo su recorrido." : "."}
      </p>
    </div>
  );
}

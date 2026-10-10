// El mapa del viaje. MapLibre se descarga aparte, cuando esta pieza aparece: mientras llega se
// ve la flor del viaje en su lugar, y si falla, el plan de al lado dice lo mismo con palabras.

import { lazy, Suspense } from "react";
import { DibujoFlor } from "./Flor";
import { Limite } from "./Limite";
import type { PropsDeMapa } from "./MapaRuta";

const MapaRuta = lazy(() => import("./MapaRuta"));

export function Mapa(props: PropsDeMapa) {
  const espera = (
    <div className="mapa-viaje__espera">
      <DibujoFlor base={props.base} puntos={props.puntos} resaltado={props.dia} />
    </div>
  );
  return (
    <div className="mapa-viaje">
      <Limite
        respaldo={
          <div className="mapa-viaje__espera">
            <p role="status">
              No se pudo cargar el mapa. El plan tiene los mismos lugares, en el mismo orden.
            </p>
          </div>
        }
      >
        <Suspense fallback={espera}>
          <MapaRuta {...props} />
        </Suspense>
      </Limite>
    </div>
  );
}

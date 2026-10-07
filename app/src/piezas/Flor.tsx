// La flor del viaje, dibujada (src/flor.ts): en la tarjeta, en la portada del viaje y mientras
// carga el mapa. El tallo es el camino de ida; cada pétalo, un día allá. Y la marca de la app.

import { useMemo } from "react";
import { diasDeLaFlor, florDelViaje, hoja, type PuntoDelViaje } from "../flor";

interface Props {
  base: { lat: number; lon: number } | null;
  puntos: readonly PuntoDelViaje[];
  /** Las horas del viaje de ida: el largo del tallo. Sin ellas, la flor va sin tallo. */
  ida?: number | null;
  /** Un día para resaltar; los demás pétalos quedan tenues. */
  resaltado?: number | null;
  /** Que la flor se abra al aparecer: el único movimiento que la app hace sola. */
  dibujar?: boolean;
  className?: string;
}

export function DibujoFlor({
  base,
  puntos,
  ida = null,
  resaltado = null,
  dibujar = false,
  className = "",
}: Props) {
  const flor = useMemo(() => florDelViaje(diasDeLaFlor(base, puntos), ida), [base, puntos, ida]);
  const tenue = (dia: number) => resaltado !== null && resaltado !== dia;
  // Los pétalos se abren desde el centro de la flor (en % del dibujo, que mide 100).
  const origen = `${flor.centro.x}% ${flor.centro.y}%`;
  return (
    <svg
      viewBox="0 0 100 100"
      className={`flor${dibujar ? " flor--dibujar" : ""} ${className}`}
      aria-hidden="true"
      focusable="false"
    >
      {flor.tallo ? (
        <path d={flor.tallo} className="flor__tallo" style={{ transformOrigin: origen }} />
      ) : null}
      {flor.petalos.map((p, i) => (
        <path
          key={p.dia}
          d={p.d}
          className={`flor__petalo${tenue(p.dia) ? " flor__petalo--tenue" : ""}`}
          style={{ transformOrigin: origen, animationDelay: `${(flor.tallo ? 280 : 0) + i * 110}ms` }}
        />
      ))}
      <circle cx={flor.centro.x} cy={flor.centro.y} r={3.4} className="flor__centro" />
    </svg>
  );
}

/** La marca: una flor de cinco pétalos, simétrica. */
export function MarcaFlor({ className = "" }: { className?: string }) {
  const centro = { x: 12, y: 12 };
  const petalos = [0, 72, 144, 216, 288].map((grados) => {
    const a = ((grados - 90) * Math.PI) / 180;
    return hoja(centro, { x: 12 + Math.cos(a) * 10, y: 12 + Math.sin(a) * 10 }, 0.36);
  });
  return (
    <svg viewBox="0 0 24 24" className={`marca__flor ${className}`} aria-hidden="true" focusable="false">
      {petalos.map((d) => (
        <path key={d} d={d} fill="currentColor" fillOpacity={0.16} stroke="currentColor" strokeWidth={1.6} />
      ))}
      <circle cx={12} cy={12} r={2.2} fill="currentColor" />
    </svg>
  );
}

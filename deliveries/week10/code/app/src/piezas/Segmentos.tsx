// Elegir uno entre pocos: los días del viaje, los meses del calendario. Si no caben a lo ancho,
// se deslizan de costado, y el elegido siempre queda a la vista.

import { type ReactNode, useEffect, useId, useRef } from "react";

export interface Segmento<T> {
  valor: T;
  /** Lo que se ve. */
  texto: ReactNode;
  /** Lo que se lee, si lo que se ve es una abreviatura: «Julio» para «Jul». */
  nombre?: string;
}

interface Props<T> {
  /** Qué se elige, para quien no ve la pantalla. */
  leyenda: string;
  segmentos: readonly Segmento<T>[];
  valor: T;
  elegir: (valor: T) => void;
  className?: string;
}

export function Segmentos<T extends string | number | null>({
  leyenda,
  segmentos,
  valor,
  elegir,
  className = "",
}: Props<T>) {
  const nombre = useId();
  const marco = useRef<HTMLFieldSetElement>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: se acomoda cada vez que cambia lo elegido
  useEffect(() => {
    const caja = marco.current;
    const elegido = caja?.querySelector<HTMLElement>("input:checked")?.parentElement;
    if (!caja || !elegido || typeof caja.scrollBy !== "function") return;
    const a = elegido.getBoundingClientRect();
    const b = caja.getBoundingClientRect();
    // Si no se ve entero, queda al centro: así también se ven los que tiene a cada lado.
    if (a.left < b.left || a.right > b.right)
      caja.scrollBy({ left: a.left + a.width / 2 - (b.left + b.width / 2) });
  }, [valor]);

  return (
    <fieldset ref={marco} className={`segmentos ${className}`.trim()}>
      <legend className="solo-lector">{leyenda}</legend>
      {segmentos.map((s) => (
        <label key={String(s.valor)}>
          <input
            type="radio"
            name={nombre}
            checked={s.valor === valor}
            onChange={() => elegir(s.valor)}
            aria-label={s.nombre}
          />
          <span>{s.texto}</span>
        </label>
      ))}
    </fieldset>
  );
}

// Cuatro datos que deciden, en una franja: el valor grande y, debajo, de qué es. Van bajo el
// nombre de un viaje (costo, ida, clima, altura) y bajo el de una zona (lugares, mejor época…).

import { Icono, type NombreDeIcono } from "./Icono";

export interface Dato {
  etiqueta: string;
  icono: NombreDeIcono;
  valor: string;
  nota: string;
  /** Si la nota es un aviso (el costo pasa el presupuesto). */
  aviso?: boolean;
  /** La estrella de los imperdibles va en su oro, como en todas partes. */
  imperdible?: boolean;
}

export function DatosClave({ datos }: { datos: Dato[] }) {
  return (
    <dl className="datos-clave">
      {datos.map((d) => (
        <div
          key={d.etiqueta}
          className={`datos-clave__dato${d.imperdible ? " datos-clave__dato--imperdible" : ""}`}
        >
          <dt className="solo-lector">{d.etiqueta}</dt>
          <dd>
            <Icono nombre={d.icono} tamano={20} relleno={d.imperdible} />
            <span className="datos-clave__valor num">{d.valor}</span>
            <span className={`datos-clave__nota${d.aviso ? " datos-clave__nota--aviso" : ""}`}>{d.nota}</span>
          </dd>
        </div>
      ))}
    </dl>
  );
}

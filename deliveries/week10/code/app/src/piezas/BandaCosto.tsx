// El costo como lo entrega el motor: una banda y no un precio. El número grande es el
// centro (P50); la barra muestra del percentil 20 al 80 y, si cabe, dónde cae el presupuesto.

import type { Costo } from "../api/tipos";
import { mayuscula, soles } from "../formato";

const COMPONENTES: Record<string, string> = {
  transporte: "Transporte",
  alojamiento: "Alojamiento",
  alimentacion: "Alimentación",
  entradas: "Entradas",
};

/** Un presupuesto muy por encima del costo no se dibuja: dejaría la banda hecha una raya. */
const TOPE_MAXIMO = 1.5;

/**
 * Dónde cae cada valor en la barra, de 0 a 100, con aire a los lados. `tope` es el
 * presupuesto si entra en el dibujo, o null.
 */
export function escalaDeBanda(costo: Pick<Costo, "p20" | "p50" | "p80">, presupuesto: number | null) {
  const tope = presupuesto !== null && presupuesto <= costo.p80 * TOPE_MAXIMO ? presupuesto : null;
  const valores = [costo.p20, costo.p80, ...(tope === null ? [] : [tope])];
  const menor = Math.min(...valores);
  const mayor = Math.max(...valores);
  const aire = Math.max((mayor - menor) * 0.18, mayor * 0.04, 1);
  const desde = Math.max(0, menor - aire);
  const hasta = mayor + aire;
  const en = (valor: number) => Math.min(100, Math.max(0, ((valor - desde) / (hasta - desde)) * 100));
  return { en, tope };
}

export function BandaCosto({ costo, presupuesto }: { costo: Costo; presupuesto: number | null }) {
  const { en, tope } = escalaDeBanda(costo, presupuesto);
  const descripcion =
    `Costo estimado por persona: entre ${soles(costo.p20)} y ${soles(costo.p80)}, con centro en ${soles(costo.p50)}.` +
    (presupuesto === null ? "" : ` Tu presupuesto es ${soles(presupuesto)}.`);
  const desglose = Object.entries(costo.desglose ?? {});
  const mayor = Math.max(1, ...desglose.map(([, monto]) => monto));

  return (
    <div className="costo">
      <p className="costo__central">
        <span className="costo__numero">{soles(costo.p50)}</span>
        <span className="costo__nota">por persona, todo el viaje</span>
      </p>

      <div className="banda" role="img" aria-label={descripcion}>
        <div className="banda__pista">
          <span
            className="banda__tramo"
            style={{ left: `${en(costo.p20)}%`, width: `${en(costo.p80) - en(costo.p20)}%` }}
          />
          <span className="banda__centro" style={{ left: `${en(costo.p50)}%` }} />
          {tope === null ? null : <span className="banda__tope" style={{ left: `${en(tope)}%` }} />}
        </div>
        {/* Cada rótulo termina o empieza en su extremo de la banda, y nunca se sale de la barra. */}
        <div className="banda__rotulos" aria-hidden="true">
          <span style={{ width: `${en(costo.p20)}%` }}>{soles(costo.p20)}</span>
          <span style={{ width: `${100 - en(costo.p80)}%` }}>{soles(costo.p80)}</span>
        </div>
      </div>
      <p className="costo__leyenda">
        Lo más probable es que gastes entre {soles(costo.p20)} y {soles(costo.p80)}.
        {presupuesto === null ? null : (
          <>
            {" "}
            {tope === null ? null : <span className="costo__tope-clave" aria-hidden="true" />} Tu presupuesto:{" "}
            {soles(presupuesto)}
            {costo.exceso
              ? `; el costo central lo pasa por ${soles(costo.exceso)}.`
              : ", y el costo central entra."}
          </>
        )}
      </p>

      {desglose.length > 0 ? (
        <>
          <p className="solo-lector">En qué se va el costo central:</p>
          <ul className="desglose">
            {desglose.map(([clave, monto]) => (
              <li key={clave}>
                <span className="desglose__nombre">{COMPONENTES[clave] ?? mayuscula(clave)}</span>
                <span className="desglose__barra" aria-hidden="true">
                  <span style={{ width: `${(monto / mayor) * 100}%` }} />
                </span>
                <span className="desglose__monto">{soles(monto)}</span>
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {costo.supuestos && costo.supuestos.length > 0 ? (
        <details className="plegable">
          <summary>Cómo se estimó</summary>
          <ul className="lista-simple">
            {costo.supuestos.map((s) => (
              <li key={s}>{s}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </div>
  );
}

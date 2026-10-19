// La noche: qué hacer cada noche que se duerme en la base (salir, mirar las estrellas o descansar).
// Es lo único con fondo de noche en la app: se distingue del día de un vistazo.

import type { LugarDeNoche, Luna, Noche } from "../api/tipos";
import { decimal, mayuscula } from "../formato";
import { claseDelCielo, tipoDeLugarDeNoche } from "../textos";
import { EnlaceExterno } from "./Enlace";
import { Icono, type NombreDeIcono } from "./Icono";

const ICONO: Record<Noche["tipo"], NombreDeIcono> = {
  salir: "copa",
  estrellas: "estrellas",
  descanso: "luna",
};

/** La luna como se ve esa noche desde el Perú: en el sur, la creciente se ilumina por la izquierda. */
export function FaseDeLuna({
  luna,
  tamano = 36,
}: {
  luna: Pick<Luna, "iluminada" | "creciente">;
  tamano?: number;
}) {
  const r = 9;
  const k = Math.min(1, Math.max(0, luna.iluminada));
  const rx = Math.abs(1 - 2 * k) * r;
  const izquierda = luna.creciente;
  // El borde iluminado y, de vuelta, la sombra: una media elipse que se curva hacia la luz en la
  // luna menguada (menos de la mitad) y hacia la sombra en la gibosa.
  const borde = izquierda ? 0 : 1;
  const sombra = k < 0.5 === izquierda ? 1 : 0;
  const iluminada = `M12 3A${r} ${r} 0 0 ${borde} 12 21A${rx.toFixed(2)} ${r} 0 0 ${sombra} 12 3Z`;
  return (
    <svg
      className="luna"
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      aria-hidden="true"
      focusable="false"
    >
      <circle cx="12" cy="12" r={r} className="luna__sombra" />
      {k > 0.01 ? <path d={iluminada} className="luna__luz" /> : null}
      <circle cx="12" cy="12" r={r} className="luna__borde" />
    </svg>
  );
}

function Lugar({ lugar }: { lugar: LugarDeNoche }) {
  return (
    <li className="noche__lugar">
      <EnlaceExterno href={lugar.url}>{lugar.nombre}</EnlaceExterno>{" "}
      <span className="noche__meta">
        {mayuscula(tipoDeLugarDeNoche(lugar.tipo))} · {lugar.minutos_a_pie} min a pie
      </span>
    </li>
  );
}

/** La noche de un día del plan. */
export function NocheDelDia({ noche }: { noche: Noche }) {
  const lugares = noche.lugares ?? [];
  const cielo = noche.cielo ?? null;
  return (
    <section className={`noche noche--${noche.tipo}`} aria-label={`De noche: ${noche.titulo}`}>
      <div className="noche__cabeza">
        <Icono nombre={ICONO[noche.tipo]} tamano={20} />
        <h4 className="noche__titulo">{noche.titulo}</h4>
        {cielo?.luna ? (
          <span className="noche__luna">
            <FaseDeLuna luna={cielo.luna} tamano={28} />
            <span>Luna al {decimal(cielo.luna.iluminada * 100, 0)} %</span>
          </span>
        ) : null}
      </div>
      {cielo ? (
        <p className="noche__clase">
          {claseDelCielo(cielo.desde.clase)}
          {cielo.desde.url ? (
            <>
              {" · "}
              <EnlaceExterno href={cielo.desde.url}>{cielo.desde.nombre} en el mapa</EnlaceExterno>
            </>
          ) : null}
        </p>
      ) : null}
      <p className="noche__nota">{noche.nota}</p>
      {lugares.length > 0 ? (
        <>
          <ul className="noche__lugares" aria-label="Para esta noche">
            {lugares.map((lugar) => (
              <Lugar key={lugar.url} lugar={lugar} />
            ))}
          </ul>
          <p className="noche__pie">
            De OpenStreetMap y Overture Maps: confirma que sigan abiertos antes de ir.
          </p>
        </>
      ) : null}
    </section>
  );
}

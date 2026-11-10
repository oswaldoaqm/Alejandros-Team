// La noche: qué hacer cada noche que se duerme en la base (salir, mirar las estrellas o descansar)
// y, en la página de la zona, lo que hay para salir y cuántas noches salen despejadas mes a mes. Es
// lo único con fondo de noche en la app: se distingue del día de un vistazo.

import { useId } from "react";
import type { LugarDeEstrellas, LugarDeNoche, Luna, Noche, NocheDeLaZona } from "../api/tipos";
import { decimal, duracion, MESES_CORTOS, mayuscula, mes } from "../formato";
import { claseDelCielo, cuantosLugaresDeNoche, tipoDeLugarDeNoche } from "../textos";
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

/** Un lugar para ver estrellas, con su enlace al mapa si lo tiene. Un mirador cuyo nombre no lo
 * dice («Gato Holgazán») se presenta como mirador. */
function LugarDelCielo({ lugar }: { lugar: LugarDeEstrellas }) {
  const nombre = lugar.url ? <EnlaceExterno href={lugar.url}>{lugar.nombre}</EnlaceExterno> : lugar.nombre;
  const loDice = lugar.nombre.toLowerCase().includes(lugar.tipo);
  return lugar.tipo === "mirador" && !loDice ? <>el mirador {nombre}</> : nombre;
}

/** Lo que una zona tiene de noche: dónde salir y cuántas noches salen despejadas en cada mes. */
export function NocheDeLaZonaVista({
  noche,
  base,
  mesElegido,
}: {
  noche: NocheDeLaZona;
  base: string;
  mesElegido: number | null;
}) {
  const id = useId();
  const { lugares, cielo } = noche;
  const despejadas = cielo.noches_despejadas;
  const hayNubes = despejadas.some((x) => x != null);
  const primeros = lugares.slice(0, 6);
  const lejos = Math.max(0, ...lugares.map((l) => l.minutos_a_pie));
  return (
    <div className="noche noche--zona">
      <div className="noche__cabeza">
        <Icono nombre="copa" tamano={20} />
        <h3 className="noche__titulo">Para salir</h3>
      </div>
      {lugares.length > 0 ? (
        <>
          <p className="noche__nota">
            {mayuscula(cuantosLugaresDeNoche(lugares))}, a no más de {lejos} minutos a pie de {base}.
          </p>
          <ul className="noche__lugares">
            {primeros.map((lugar) => (
              <Lugar key={lugar.url} lugar={lugar} />
            ))}
          </ul>
        </>
      ) : (
        <p className="noche__nota">No tenemos registrados lugares para salir cerca de {base}.</p>
      )}

      <div className="noche__cabeza">
        <Icono nombre="estrellas" tamano={20} />
        <h3 className="noche__titulo">Para ver estrellas</h3>
      </div>
      <p className="noche__clase">
        Desde {base}: {claseDelCielo(cielo.desde.clase).toLowerCase()}
      </p>
      {cielo.mas_oscuro ? (
        <p className="noche__nota">
          El cielo oscuro más cercano está en <LugarDelCielo lugar={cielo.mas_oscuro} />, a{" "}
          {duracion(cielo.mas_oscuro.minutos)}. De noche, mejor con un tour o un taxi que espere.
        </p>
      ) : null}
      {cielo.observatorio ? (
        <p className="noche__nota">
          <LugarDelCielo lugar={cielo.observatorio} /> es un {cielo.observatorio.tipo} a{" "}
          {duracion(cielo.observatorio.minutos)}: confirma sus horarios.
        </p>
      ) : null}

      {hayNubes ? (
        <figure className="despejadas">
          <figcaption className="despejadas__titulo">Noches despejadas, de cada diez</figcaption>
          <ol className="despejadas__meses" aria-describedby={`${id}-fuente`}>
            {despejadas.map((parte, i) => {
              const numero = i + 1;
              const diez = parte == null ? null : Math.round(parte * 10);
              return (
                <li
                  key={numero}
                  className={`despejadas__mes${numero === mesElegido ? " despejadas__mes--elegido" : ""}`}
                >
                  <span className="solo-lector">
                    {mayuscula(mes(numero))}:{" "}
                    {diez == null ? "sin dato" : `${diez} de cada 10 noches despejadas`}
                  </span>
                  <span className="despejadas__columna" aria-hidden="true">
                    {diez != null ? (
                      <span
                        className="despejadas__barra"
                        style={{ height: `${Math.max(4, (parte ?? 0) * 100)}%` }}
                      />
                    ) : null}
                  </span>
                  <span className="despejadas__valor" aria-hidden="true">
                    {diez ?? "—"}
                  </span>
                  <span className="despejadas__nombre" aria-hidden="true">
                    {mayuscula(MESES_CORTOS[i] ?? "")}
                  </span>
                </li>
              );
            })}
          </ol>
          <p id={`${id}-fuente`} className="noche__pie">
            A las 21:00 y a la 01:00, de 2022 a 2024:{" "}
            {cielo.fuente_nubes === "metar"
              ? `lo que reportó el aeropuerto de ${cielo.aeropuerto ?? "la zona"}.`
              : "la máscara de nubes del satélite GOES-16."}
          </p>
        </figure>
      ) : (
        <p className="noche__pie">
          En la costa, de noche el satélite no ve bien las nubes bajas, y no hay un aeropuerto cerca que las
          reporte: no damos cuántas noches salen despejadas.
        </p>
      )}
    </div>
  );
}

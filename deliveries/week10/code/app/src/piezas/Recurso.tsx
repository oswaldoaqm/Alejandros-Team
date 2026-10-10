// Un lugar del inventario, abierto en su hoja: su foto, qué es, a qué altura está, si se paga,
// qué importancia le da MINCETUR y su descripción. Al pie, su ficha oficial, que es donde se
// verifica todo lo demás. La usan el plan de un viaje y la lista de lugares de una zona.

import type { ReactNode } from "react";
import type { Recurso } from "../api/tipos";
import { metros, solesExactos } from "../formato";
import type { Foto as DatosDeFoto } from "../fotos";
import { EnlaceExterno } from "./Enlace";
import { Foto } from "./Foto";
import { Hoja } from "./Hoja";
import { Icono } from "./Icono";

/** Desde jerarquía 3, MINCETUR lo cuenta entre los lugares más importantes del país. */
const IMPERDIBLE = 3;

export function esImperdible(recurso: Pick<Recurso, "jerarquia">): boolean {
  return (recurso.jerarquia ?? 0) >= IMPERDIBLE;
}

/** «Capilla», «Museos de sitio»: el subtipo de la ficha, o el tipo si el subtipo no dice nada. */
export function claseDeRecurso(recurso: Pick<Recurso, "tipo" | "subtipo">): string {
  return recurso.subtipo && recurso.subtipo !== "Otros" ? recurso.subtipo : recurso.tipo;
}

function precioDeEntrada(recurso: Pick<Recurso, "ingreso" | "tarifa_soles">): string {
  if (recurso.ingreso === "libre") return "Libre";
  if (recurso.ingreso === "pagado") {
    return recurso.tarifa_soles != null && recurso.tarifa_soles > 0
      ? solesExactos(recurso.tarifa_soles)
      : "Se paga; la ficha no publica cuánto";
  }
  return "La ficha no dice si se paga";
}

/** La estrella de los imperdibles, con su palabra: el estado nunca va solo en el color. */
export function Imperdible({ tamano = 15 }: { tamano?: number }) {
  return (
    <span className="imperdible">
      <Icono nombre="estrella" relleno tamano={tamano} />
      Imperdible
    </span>
  );
}

interface Props {
  /** El lugar abierto; null, la hoja cerrada. */
  recurso: Recurso | null;
  foto: DatosDeFoto | null;
  /** Lo que importa del lugar dentro de un viaje (cuándo se llega, cuánto dura la visita): va primero. */
  visita?: ReactNode;
  alCerrar: () => void;
}

export function HojaDeRecurso({ recurso, foto, visita, alCerrar }: Props) {
  return (
    <Hoja
      abierta={recurso !== null}
      alCerrar={alCerrar}
      titulo={recurso?.nombre ?? ""}
      pie={
        recurso ? (
          <EnlaceExterno href={recurso.url_ficha} className="boton boton--secundario boton--ancho">
            Ver la ficha oficial <span className="solo-lector">de {recurso.nombre} en MINCETUR</span>
            <Icono nombre="externo" tamano={16} />
          </EnlaceExterno>
        ) : null
      }
    >
      {recurso ? (
        <div className="lugar-hoja">
          {foto ? (
            <Foto foto={foto} alt={recurso.nombre} sizes="(min-width: 720px) 520px, 100vw" tope={960} />
          ) : null}
          <p className="lugar-hoja__clase">
            {esImperdible(recurso) ? (
              <>
                <Imperdible />{" "}
              </>
            ) : null}
            <span>{claseDeRecurso(recurso)}</span>
          </p>
          <dl className="lugar-hoja__datos">
            {visita}
            {recurso.altitud_m != null ? (
              <div>
                <dt>Altura</dt>
                <dd>{metros(recurso.altitud_m)}</dd>
              </div>
            ) : null}
            <div>
              <dt>Entrada</dt>
              <dd>{precioDeEntrada(recurso)}</dd>
            </div>
            <div>
              <dt>Importancia</dt>
              <dd>
                {recurso.jerarquia != null
                  ? `${recurso.jerarquia} de 4, según MINCETUR`
                  : "MINCETUR no la ha calificado"}
              </dd>
            </div>
          </dl>
          {recurso.descripcion ? <p className="lugar-hoja__descripcion">{recurso.descripcion}</p> : null}
        </div>
      ) : null}
    </Hoja>
  );
}

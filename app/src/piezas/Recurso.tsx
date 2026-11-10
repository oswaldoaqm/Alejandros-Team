// Un lugar del inventario, abierto en su hoja: su foto, qué es, a qué altura está, si se paga,
// qué importancia le da MINCETUR y su descripción. Al pie, su ficha oficial, que es donde se
// verifica todo lo demás. La usan el plan de un viaje y la lista de lugares de una zona.

import type { ReactNode } from "react";
import type { Recurso } from "../api/tipos";
import { lista, metros, solesExactos } from "../formato";
import type { Foto as DatosDeFoto } from "../fotos";
import { EnlaceExterno } from "./Enlace";
import { Foto } from "./Foto";
import { Hoja } from "./Hoja";
import { Icono } from "./Icono";
import { InsigniaJerarquia } from "./InsigniaJerarquia";

/** Desde jerarquía 3, MINCETUR lo cuenta entre los lugares más importantes del país. */
const IMPERDIBLE = 3;

const SEMANA = ["lun", "mar", "mie", "jue", "vie", "sab", "dom"] as const;
const PLURAL_DIA: Record<(typeof SEMANA)[number], string> = {
  lun: "lunes",
  mar: "martes",
  mie: "miércoles",
  jue: "jueves",
  vie: "viernes",
  sab: "sábados",
  dom: "domingos",
};

export function esImperdible(recurso: Pick<Recurso, "jerarquia">): boolean {
  return (recurso.jerarquia ?? 0) >= IMPERDIBLE;
}

/** «Capilla», «Museos de sitio»: el subtipo de la ficha, o el tipo si el subtipo no dice nada. */
export function claseDeRecurso(recurso: Pick<Recurso, "tipo" | "subtipo">): string {
  return recurso.subtipo && recurso.subtipo !== "Otros" ? recurso.subtipo : recurso.tipo;
}

/** «09:00 a 17:00», «09:00 a 16:00 (cierra los lunes)»; null si la ficha no trae horario ni días. */
export function horarioDeRecurso(recurso: Pick<Recurso, "abre" | "cierra" | "dias">): string | null {
  const horas = recurso.abre && recurso.cierra ? `${recurso.abre} a ${recurso.cierra}` : null;
  const abiertos = recurso.dias ? SEMANA.filter((d) => recurso.dias?.includes(d)) : [];
  let notaDias: string | null = null;
  if (abiertos.length > 0 && abiertos.length < SEMANA.length) {
    const cerrados = SEMANA.filter((d) => !abiertos.includes(d));
    if (cerrados.length === 1 && cerrados[0]) {
      notaDias = `cierra los ${PLURAL_DIA[cerrados[0]]}`;
    } else if (cerrados.length === 2) {
      notaDias = `cierra ${lista(cerrados.map((d) => PLURAL_DIA[d]))}`;
    } else {
      notaDias = `abre ${lista(abiertos.map((d) => PLURAL_DIA[d]))}`;
    }
  }
  if (horas && notaDias) return `${horas} (${notaDias})`;
  if (horas) return horas;
  return notaDias ? notaDias.charAt(0).toUpperCase() + notaDias.slice(1) : null;
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
  const horario = recurso ? horarioDeRecurso(recurso) : null;
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
            <Foto
              foto={foto}
              alt={recurso.nombre}
              sizes="(min-width: 720px) 520px, 100vw"
              tope={960}
              principal
            />
          ) : null}
          <p className="lugar-hoja__clase">
            {esImperdible(recurso) ? (
              <>
                <Imperdible />{" "}
              </>
            ) : null}
            {recurso.jerarquia && recurso.jerarquia >= 3 ? (
              <InsigniaJerarquia jerarquia={recurso.jerarquia} variante="insignia" contexto="lugar" />
            ) : null}
            <span>{claseDeRecurso(recurso)}</span>
          </p>
          <section className="lugar-hoja__seccion" aria-label="Detalles importantes">
            <h3 className="lugar-hoja__seccion-titulo">
              <Icono nombre="info" tamano={17} />
              Detalles importantes
            </h3>
            <dl className="lugar-hoja__datos">
              {visita}
              {horario ? (
                <div>
                  <dt>Horario</dt>
                  <dd>{horario}</dd>
                </div>
              ) : null}
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
          </section>

          {recurso.descripcion ? (
            <section
              className="lugar-hoja__seccion lugar-hoja__seccion--info"
              aria-label="Información del lugar"
            >
              <h3 className="lugar-hoja__seccion-titulo">
                <Icono nombre="destino" tamano={17} />
                Información del lugar
              </h3>
              <p className="lugar-hoja__descripcion">{recurso.descripcion}</p>
            </section>
          ) : null}
        </div>
      ) : null}
    </Hoja>
  );
}

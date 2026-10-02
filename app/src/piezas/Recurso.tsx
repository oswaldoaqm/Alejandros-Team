// Lo que se muestra de un lugar del inventario: qué es, a qué altura está, si se paga, su
// descripción y el enlace a su ficha oficial, que es donde se verifica todo lo demás.

import type { Recurso } from "../api/tipos";
import { metros } from "../formato";
import { entrada } from "../textos";
import { EnlaceExterno } from "./Enlace";
import { Icono } from "./Icono";

/** «Capilla», «Museos de sitio»: el subtipo de la ficha, o el tipo si el subtipo no dice nada. */
export function claseDeRecurso(recurso: Pick<Recurso, "tipo" | "subtipo">): string {
  return recurso.subtipo && recurso.subtipo !== "Otros" ? recurso.subtipo : recurso.tipo;
}

export function DatosDeRecurso({ recurso }: { recurso: Recurso }) {
  const datos = [
    claseDeRecurso(recurso),
    recurso.altitud_m != null ? metros(recurso.altitud_m) : null,
    entrada(recurso),
  ];
  return <p className="parada__meta">{datos.filter(Boolean).join(" · ")}</p>;
}

export function MasDeRecurso({ recurso }: { recurso: Recurso }) {
  return (
    <div className="parada__mas">
      {recurso.descripcion ? (
        <details className="plegable plegable--chico">
          <summary>Qué es</summary>
          <p>{recurso.descripcion}</p>
        </details>
      ) : (
        <span />
      )}
      <EnlaceExterno href={recurso.url_ficha} className="parada__ficha">
        Ficha oficial
        <span className="solo-lector"> de {recurso.nombre} en MINCETUR</span>
        <Icono nombre="externo" tamano={14} />
      </EnlaceExterno>
    </div>
  );
}

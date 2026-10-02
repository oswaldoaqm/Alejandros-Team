// Avisos y eventos de una ruta.

import type { Aviso, Evento } from "../api/tipos";
import { rangoDeFechas } from "../formato";
import { EnlaceExterno } from "./Enlace";
import { Icono } from "./Icono";

export function ListaAvisos({ avisos }: { avisos: Aviso[] }) {
  if (avisos.length === 0) return null;
  const ordenados = [...avisos].sort(
    (a, b) => Number(b.nivel === "advertencia") - Number(a.nivel === "advertencia"),
  );
  return (
    <ul className="avisos" aria-label="Avisos de esta ruta">
      {ordenados.map((a) => (
        <li key={`${a.tipo}-${a.mensaje}`} className={`aviso aviso--${a.nivel}`}>
          <Icono nombre={a.nivel === "advertencia" ? "aviso" : "info"} />
          <p>
            <span className="solo-lector">
              {a.nivel === "advertencia" ? "Advertencia: " : "Para saber: "}
            </span>
            {a.mensaje}
          </p>
        </li>
      ))}
    </ul>
  );
}

const PRECISION: Record<Evento["precision_fecha"], string | null> = {
  exacta: null,
  aproximada: "fecha aproximada",
  por_confirmar: "fecha por confirmar",
};

export function ListaEventos({ eventos, vacio }: { eventos: Evento[]; vacio?: string }) {
  if (eventos.length === 0) return vacio ? <p className="ayuda">{vacio}</p> : null;
  return (
    <ul className="eventos">
      {eventos.map((e) => {
        const precision = PRECISION[e.precision_fecha];
        return (
          <li key={e.id} className="evento">
            <p className="evento__fecha">
              {rangoDeFechas(e.fecha_inicio, e.fecha_fin) || "Sin fecha"}
              {precision ? <span className="evento__precision"> · {precision}</span> : null}
            </p>
            <p className="evento__nombre">
              {e.url ? (
                <EnlaceExterno href={e.url}>
                  {e.nombre}
                  {"\u00a0"}
                  <Icono nombre="externo" tamano={14} />
                </EnlaceExterno>
              ) : (
                e.nombre
              )}
            </p>
            <p className="evento__lugar">
              {e.distrito}, {e.provincia} · {e.region}
              {e.fuente === "publicado" && e.publicado_por ? ` · Publicado por ${e.publicado_por}` : ""}
            </p>
          </li>
        );
      })}
    </ul>
  );
}

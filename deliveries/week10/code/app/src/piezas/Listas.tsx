// Las fiestas y eventos, como los ve el viajero: el día en grande y, al lado, qué es, dónde y
// cuándo. La misma lista va en el viaje, en la zona, en el calendario y en la vista previa de
// quien publica un evento.

import { useState } from "react";
import type { Evento } from "../api/tipos";
import { fechaLocal, MESES_CORTOS, plural, rangoDeFechas } from "../formato";
import { EnlaceExterno } from "./Enlace";
import { Icono } from "./Icono";

const PRECISION: Record<Evento["precision_fecha"], string | null> = {
  exacta: null,
  aproximada: "Fecha aproximada",
  por_confirmar: "Fecha por confirmar",
};

function FilaDeEvento({ evento: e }: { evento: Evento }) {
  const inicio = e.fecha_inicio ? fechaLocal(e.fecha_inicio) : null;
  const precision = PRECISION[e.precision_fecha];
  const lugar = [e.distrito, e.provincia !== e.distrito ? e.provincia : null, e.region]
    .filter(Boolean)
    .join(", ");
  return (
    <li className="evento">
      <span className="evento__dia" aria-hidden="true">
        {inicio ? (
          <>
            <span className="evento__numero">{inicio.getDate()}</span>
            <span className="evento__mes">{MESES_CORTOS[inicio.getMonth()]}</span>
          </>
        ) : (
          <Icono nombre="calendario" />
        )}
      </span>
      <div className="evento__texto">
        <p className="evento__nombre">
          {e.url ? (
            <EnlaceExterno href={e.url} aria-label={`${e.nombre} (se abre en otra pestaña)`}>
              {e.nombre}
              <Icono nombre="externo" tamano={14} />
            </EnlaceExterno>
          ) : (
            e.nombre
          )}
        </p>
        <p className="evento__lugar">{lugar}</p>
        <p className="evento__cuando">
          <span>{rangoDeFechas(e.fecha_inicio, e.fecha_fin) || "Sin fecha"}</span>
          {precision ? <span className="etiqueta">{precision}</span> : null}
          {e.fuente === "publicado" && e.publicado_por ? (
            <span className="etiqueta etiqueta--publicado">Publicado por {e.publicado_por}</span>
          ) : null}
        </p>
      </div>
    </li>
  );
}

interface Props {
  eventos: Evento[];
  /** Qué decir si no hay ninguno; sin esto, no se muestra nada. */
  vacio?: string;
  /** Cuántos mostrar antes de «Ver todos». */
  limite?: number;
}

export function ListaEventos({ eventos, vacio, limite }: Props) {
  const [todos, verTodos] = useState(false);
  if (eventos.length === 0) return vacio ? <p className="eventos-vacio">{vacio}</p> : null;
  const corta = limite !== undefined && eventos.length > limite && !todos;
  const visibles = corta ? eventos.slice(0, limite) : eventos;
  return (
    <>
      <ul className="eventos">
        {visibles.map((e) => (
          <FilaDeEvento key={e.id} evento={e} />
        ))}
      </ul>
      {corta ? (
        <button type="button" className="boton boton--secundario eventos__mas" onClick={() => verTodos(true)}>
          Ver {plural(eventos.length - visibles.length, "evento más", "eventos más")}
        </button>
      ) : null}
    </>
  );
}

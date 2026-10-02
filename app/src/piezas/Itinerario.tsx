// El itinerario, día por día: a qué hora se llega a cada parada, cuánto se tarda en llegar,
// cuánto dura la visita y dónde verificarla en la ficha oficial.

import type { Evento } from "../api/tipos";
import { eventosDelDia } from "../eventos";
import { duracion, fechaCorta, horas, km } from "../formato";
import type { DiaNumerado, ParadaNumerada } from "../itinerario";
import { tipoDeDia } from "../textos";
import { EnlaceExterno } from "./Enlace";
import { Icono } from "./Icono";
import { Jerarquia } from "./Insignias";
import { DatosDeRecurso, MasDeRecurso } from "./Recurso";

interface Props {
  dias: DiaNumerado[];
  eventos: Evento[];
  /** Desde dónde sale el primer traslado de cada día: la base o, en un viaje de un día, el origen. */
  desde: string;
  /** Lleva el mapa a ese día. Sin mapa, no se ofrece. */
  verEnMapa?: (dia: number) => void;
}

function FilaDeParada({
  numero,
  parada,
  primera,
  desde,
}: ParadaNumerada & { primera: boolean; desde: string }) {
  const { recurso } = parada;
  return (
    <li className="parada">
      <span className="parada__numero" aria-hidden="true">
        {numero}
      </span>
      <div className="parada__cuerpo">
        <p className="parada__linea">
          <span className="solo-lector">Parada {numero}, a las </span>
          <span className="parada__hora">{parada.llegada}</span>
          <span className="parada__nombre">{recurso.nombre}</span>
          <Jerarquia valor={recurso.jerarquia} />
        </p>
        <DatosDeRecurso recurso={recurso} />
        <p className="parada__meta">
          A {duracion(parada.minutos_traslado)} de {primera ? desde : "la anterior"} (
          {km(parada.km_desde_anterior)}) · visita de {duracion(parada.minutos_visita)}
        </p>
        <MasDeRecurso recurso={recurso} />
      </div>
    </li>
  );
}

export function Itinerario({ dias, eventos, desde, verEnMapa }: Props) {
  return (
    <ol className="dias">
      {dias.map(({ dia, paradas }) => {
        const fiestas = eventosDelDia(eventos, dia.fecha);
        return (
          <li key={dia.numero} className="dia">
            <div className="dia__cabeza">
              <h4 className="dia__titulo">
                <span className="dia__numero">Día {dia.numero}</span>
                {dia.fecha ? <span className="dia__fecha">{fechaCorta(dia.fecha)}</span> : null}
                <span className="dia__tipo">{tipoDeDia(dia)}</span>
              </h4>
              {dia.horas > 0 ? (
                <p className="dia__cifras">
                  <span className="solo-lector">Jornada de </span>
                  {horas(dia.horas)} · {km(dia.km)}
                </p>
              ) : null}
            </div>
            {dia.nota ? <p className="dia__nota">{dia.nota}</p> : null}
            {paradas.length > 0 ? (
              <ol className="paradas">
                {paradas.map((p, indice) => (
                  <FilaDeParada key={p.parada.recurso.codigo} {...p} primera={indice === 0} desde={desde} />
                ))}
              </ol>
            ) : null}
            {fiestas.map((e) => (
              <p key={e.id} className="dia__evento">
                <Icono nombre="calendario" tamano={16} />
                <span>
                  Ese día: {e.url ? <EnlaceExterno href={e.url}>{e.nombre}</EnlaceExterno> : e.nombre}, en{" "}
                  {e.distrito}
                  {e.precision_fecha === "aproximada" ? " (fecha aproximada)" : ""}
                  {e.fuente === "publicado" && e.publicado_por ? ` (publicado por ${e.publicado_por})` : ""}.
                </span>
              </p>
            ))}
            {verEnMapa && paradas.length > 0 ? (
              <button type="button" className="boton boton--texto" onClick={() => verEnMapa(dia.numero)}>
                <Icono nombre="pin" tamano={16} />
                Ver el día {dia.numero} en el mapa
              </button>
            ) : null}
          </li>
        );
      })}
    </ol>
  );
}

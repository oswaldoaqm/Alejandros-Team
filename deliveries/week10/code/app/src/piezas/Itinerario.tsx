// El plan, de a un día. Con «Todo» se ven los días en una lista (qué se hace en cada uno); al
// elegir un día, sus lugares en orden con la hora de llegada. Lo demás de cada lugar (cuánto
// dura la visita, si se paga, su ficha oficial) se abre al tocarlo, en una hoja.

import type { Evento, Parada } from "../api/tipos";
import { eventosDelDia } from "../eventos";
import { duracion, fechaCorta, horas, km } from "../formato";
import type { Foto as DatosDeFoto } from "../fotos";
import type { DiaNumerado } from "../itinerario";
import { entrada, resumenDeLugares, tipoDeDia } from "../textos";
import { EnlaceExterno } from "./Enlace";
import { Icono } from "./Icono";
import { esImperdible, HojaDeRecurso, Imperdible } from "./Recurso";
import { type Segmento, Segmentos } from "./Segmentos";

// ── El selector: «Todo» y cada día ─────────────────────────────────────────────────

interface PropsDelSelector {
  dias: number[];
  dia: number | null;
  elegirDia: (dia: number | null) => void;
}

export function SelectorDeDias({ dias, dia, elegirDia }: PropsDelSelector) {
  const segmentos: Segmento<number | null>[] = [
    { valor: null, texto: "Todo" },
    ...dias.map((d) => ({ valor: d, texto: `Día ${d}` })),
  ];
  return (
    <Segmentos
      leyenda="Qué parte del viaje ver"
      segmentos={segmentos}
      valor={dia}
      elegir={elegirDia}
      className="selector-de-dias"
    />
  );
}

// ── El plan ────────────────────────────────────────────────────────────────────────

interface Props {
  dias: DiaNumerado[];
  eventos: Evento[];
  dia: number | null;
  elegirDia: (dia: number | null) => void;
  abrirLugar: (dia: number, codigo: string) => void;
}

function TodosLosDias({ dias, elegirDia }: Pick<Props, "dias" | "elegirDia">) {
  return (
    <ol className="dias-lista">
      {dias.map(({ dia, paradas }) => (
        <li key={dia.numero}>
          <button type="button" className="dia-fila" onClick={() => elegirDia(dia.numero)}>
            <span className="dia-fila__dia">
              Día {dia.numero}{" "}
              {dia.fecha ? <span className="dia-fila__fecha">{fechaCorta(dia.fecha)}</span> : null}
            </span>{" "}
            <span className="dia-fila__texto">
              <span className="dia-fila__tipo">{tipoDeDia(dia)}</span>{" "}
              <span className="dia-fila__lugares">
                {paradas.length > 0
                  ? resumenDeLugares(paradas.map((p) => p.parada.recurso.nombre))
                  : (dia.nota ?? "Sin visitas")}
              </span>
            </span>
            <Icono nombre="flecha" tamano={18} />
          </button>
        </li>
      ))}
    </ol>
  );
}

function UnDia({
  numerado,
  eventos,
  siguiente,
  elegirDia,
  abrirLugar,
}: {
  numerado: DiaNumerado;
  eventos: Evento[];
  siguiente: number | null;
  elegirDia: Props["elegirDia"];
  abrirLugar: Props["abrirLugar"];
}) {
  const { dia, paradas } = numerado;
  const fiestas = dia.fecha ? eventosDelDia(eventos, dia.fecha) : [];
  return (
    <div className="un-dia">
      <div className="un-dia__cabeza">
        <h3 className="un-dia__titulo">
          Día {dia.numero} {dia.fecha ? <span className="un-dia__fecha">{fechaCorta(dia.fecha)}</span> : null}
        </h3>
        <p className="un-dia__resumen">
          {tipoDeDia(dia)}
          {dia.horas > 0 ? `: ${horas(dia.horas)} de jornada y ${km(dia.km)} de camino.` : "."}
        </p>
      </div>

      {dia.nota ? (
        <p className="un-dia__nota">
          <Icono nombre="bus" />
          <span>{dia.nota}</span>
        </p>
      ) : null}

      {paradas.length > 0 ? (
        <ol className="lugares" aria-label={`Lugares del día ${dia.numero}`}>
          {paradas.map(({ numero, parada }) => (
            <li key={parada.recurso.codigo}>
              <button
                type="button"
                className="lugar-fila"
                onClick={() => abrirLugar(dia.numero, parada.recurso.codigo)}
              >
                <span className="lugar-fila__hora num">{parada.llegada}</span>{" "}
                <span className="lugar-fila__numero" aria-hidden="true">
                  {numero}
                </span>
                <span className="lugar-fila__texto">
                  <span className="lugar-fila__nombre">{parada.recurso.nombre}</span>{" "}
                  <span className="lugar-fila__meta">
                    {esImperdible(parada.recurso) ? (
                      <>
                        <Imperdible tamano={14} />{" "}
                      </>
                    ) : null}
                    <span>Visita de {duracion(parada.minutos_visita)}</span>
                  </span>
                </span>
                <Icono nombre="flecha" tamano={18} />
              </button>
            </li>
          ))}
        </ol>
      ) : dia.nota ? null : (
        <p className="un-dia__libre">Un día libre, sin visitas en el plan.</p>
      )}

      {fiestas.map((e) => (
        <p key={e.id} className="un-dia__fiesta">
          <Icono nombre="fiestas" />
          <span>
            Ese día: {e.url ? <EnlaceExterno href={e.url}>{e.nombre}</EnlaceExterno> : e.nombre}, en{" "}
            {e.distrito}
            {e.precision_fecha === "aproximada" ? " (fecha aproximada)" : ""}
            {e.fuente === "publicado" && e.publicado_por ? ` (publicado por ${e.publicado_por})` : ""}.
          </span>
        </p>
      ))}

      <button
        type="button"
        className="boton boton--secundario un-dia__siguiente"
        onClick={() => elegirDia(siguiente)}
      >
        {siguiente === null ? "Ver todo el viaje" : `Ver el día ${siguiente}`}
        {siguiente === null ? null : <Icono nombre="flecha" tamano={16} />}
      </button>
    </div>
  );
}

export function Itinerario({ dias, eventos, dia, elegirDia, abrirLugar }: Props) {
  const indice = dia === null ? -1 : dias.findIndex((d) => d.dia.numero === dia);
  const elegido = dias[indice];
  if (!elegido) return <TodosLosDias dias={dias} elegirDia={elegirDia} />;
  return (
    <UnDia
      numerado={elegido}
      eventos={eventos}
      siguiente={dias[indice + 1]?.dia.numero ?? null}
      elegirDia={elegirDia}
      abrirLugar={abrirLugar}
    />
  );
}

/** El plan completo, todos los días, para imprimir o guardar en PDF. En pantalla no se ve. */
export function PlanParaImprimir({ dias }: { dias: DiaNumerado[] }) {
  return (
    <div className="solo-impresion plan-impreso">
      {dias.map(({ dia, paradas }) => (
        <section key={dia.numero} className="plan-impreso__dia">
          <h3>
            Día {dia.numero}
            {dia.fecha ? `, ${fechaCorta(dia.fecha)}` : ""}: {tipoDeDia(dia)}
          </h3>
          {dia.nota ? <p>{dia.nota}</p> : null}
          {paradas.length > 0 ? (
            <ol>
              {paradas.map(({ numero, parada }) => (
                <li key={parada.recurso.codigo}>
                  <span className="num">{parada.llegada}</span>{" "}
                  <strong>
                    {numero}. {parada.recurso.nombre}
                  </strong>
                  . Visita de {duracion(parada.minutos_visita)}. {entrada(parada.recurso)}.{" "}
                  <span className="plan-impreso__ficha">{parada.recurso.url_ficha}</span>
                </li>
              ))}
            </ol>
          ) : null}
        </section>
      ))}
    </div>
  );
}

// ── Un lugar, en su hoja ───────────────────────────────────────────────────────────

export interface LugarAbierto {
  parada: Parada;
  numero: number;
  dia: number;
  /** De dónde se llega: donde se duerme (o el origen) para el primero del día; si no, el anterior. */
  desde: string;
  foto: DatosDeFoto | null;
}

export function HojaDeLugar({ lugar, alCerrar }: { lugar: LugarAbierto | null; alCerrar: () => void }) {
  return (
    <HojaDeRecurso
      recurso={lugar?.parada.recurso ?? null}
      foto={lugar?.foto ?? null}
      alCerrar={alCerrar}
      visita={
        lugar ? (
          <>
            <div>
              <dt>Llegas</dt>
              <dd className="num">
                {lugar.parada.llegada}, día {lugar.dia}
              </dd>
            </div>
            <div>
              <dt>Visita</dt>
              <dd>{duracion(lugar.parada.minutos_visita)}</dd>
            </div>
            <div>
              <dt>Desde {lugar.desde}</dt>
              <dd>
                {duracion(lugar.parada.minutos_traslado)}, {km(lugar.parada.km_desde_anterior)}
              </dd>
            </div>
          </>
        ) : null
      }
    />
  );
}

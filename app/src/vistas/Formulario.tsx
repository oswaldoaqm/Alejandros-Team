// Pantalla 1: qué viaje quiere el viajero. Una pregunta grande y una tarjeta con cinco filas;
// cada fila abre una hoja para elegir. Ya viene lista para buscar: el mes que viene, desde
// Lima y seis días. Las opciones (orígenes, intereses y rangos) vienen de GET /v1/opciones.

import { type FormEvent, useId, useMemo, useState } from "react";
import type { Opciones } from "../api/tipos";
import { type Consulta, POR_DEFECTO } from "../consulta";
import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { aIso, fecha, fechaLocal, MESES_CORTOS, mayuscula, mes, metros, plural, soles } from "../formato";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { Hoja } from "../piezas/Hoja";
import { Icono, type NombreDeIcono } from "../piezas/Icono";
import { enlaces } from "../ruta";

// Los dos deslizadores terminan en «sin tope»: ese extremo no manda nada al API.
const PRESUPUESTO = { minimo: 200, maximo: 5000, paso: 100 };
const ALTITUD = { minimo: 500, maximo: 5000, paso: 100 };

const ICONO_DE_INTERES: Record<string, NombreDeIcono> = {
  naturaleza: "naturaleza",
  historia: "historia",
  gastronomia: "gastronomia",
  caminatas: "caminatas",
  playa: "playa",
  fiestas: "fiestas",
  arquitectura: "arquitectura",
  aventura: "aventura",
};

type Eleccion = "origen" | "cuando" | "intereses" | "filtros" | null;

function mesQueViene(): number {
  return ((new Date().getMonth() + 1) % 12) + 1;
}

function acotar(valor: number, minimo: number, maximo: number): number {
  return Math.min(maximo, Math.max(minimo, valor));
}

/** Sin tildes ni mayúsculas: «cusco» encuentra «Cusco» y «junin» encuentra «Junín». */
function plano(texto: string): string {
  return texto
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase();
}

export function Formulario({ inicial }: { inicial: Consulta | null }) {
  const { opciones } = useApp();
  useTitulo(inicial ? "Cambiar el viaje" : null);
  return (
    <section className="pagina inicio">
      <div className="inicio__cabeza">
        <h1 tabIndex={-1} className="inicio__titulo">
          {inicial ? "Cambia tu viaje" : "¿A dónde te escapas?"}
        </h1>
        <p className="inicio__bajada">
          Dinos desde dónde sales y cuándo. Te armamos tres viajes por el Perú, con su plan día por día.
        </p>
      </div>
      {opciones.datos ? (
        <Campos opciones={opciones.datos} inicial={inicial} />
      ) : opciones.error ? (
        <ErrorVista error={opciones.error} reintentar={opciones.reintentar} />
      ) : (
        <Cargando texto="Preparando el planificador…" />
      )}
    </section>
  );
}

function Campos({ opciones, inicial }: { opciones: Opciones; inicial: Consulta | null }) {
  const { navegar } = useApp();
  const id = useId();
  const [c, poner] = useState<Consulta>(() => inicial ?? { ...POR_DEFECTO, mes: mesQueViene() });
  const [abierta, abrir] = useState<Eleccion>(null);
  const cambiar = (parte: Partial<Consulta>) => poner((antes) => ({ ...antes, ...parte }));
  const cerrar = () => abrir(null);

  const dias = { minimo: opciones.dias.minimo, maximo: opciones.dias.maximo };
  const origen = opciones.origenes.find((o) => o.id === c.origen)?.nombre ?? c.origen;
  const etiquetas = new Map<string, string>(opciones.intereses.map((i) => [i.id, i.etiqueta]));

  const buscar = (sorpresa: boolean) => navegar(enlaces.resultados({ ...c, sorpresa }));
  const enviar = (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    buscar(false);
  };

  const cuando = c.fecha_inicio ? `Sale el ${fecha(c.fecha_inicio, false)}` : mayuscula(mes(c.mes));
  const gustos =
    c.intereses.length === 0
      ? "De todo un poco"
      : c.intereses.length <= 2
        ? c.intereses.map((i) => etiquetas.get(i) ?? i).join(" y ")
        : `${etiquetas.get(c.intereses[0] ?? "") ?? ""} y ${c.intereses.length - 1} más`;
  const filtros = [
    c.presupuesto !== null ? `Hasta ${soles(c.presupuesto)}` : null,
    c.altitud_max !== null ? `hasta ${metros(c.altitud_max)} de altura` : null,
  ].filter(Boolean);

  return (
    <form className="inicio__formulario" onSubmit={enviar} aria-label="Planear el viaje">
      <div className="grupo inicio__grupo">
        <button type="button" className="fila" onClick={() => abrir("origen")} aria-haspopup="dialog">
          <span className="fila__icono">
            <Icono nombre="pin" />
          </span>
          <span className="fila__texto">
            <span className="fila__nombre">Desde</span> <span className="fila__valor">{origen}</span>
          </span>
          <span className="fila__fin">
            <Icono nombre="flecha" />
          </span>
        </button>

        <button type="button" className="fila" onClick={() => abrir("cuando")} aria-haspopup="dialog">
          <span className="fila__icono">
            <Icono nombre="calendario" />
          </span>
          <span className="fila__texto">
            <span className="fila__nombre">Cuándo</span> <span className="fila__valor">{cuando}</span>
          </span>
          <span className="fila__fin">
            <Icono nombre="flecha" />
          </span>
        </button>

        <fieldset className="fila" aria-labelledby={`${id}-dias`}>
          <span className="fila__icono">
            <Icono nombre="reloj" />
          </span>
          <span className="fila__texto">
            <span className="fila__nombre" id={`${id}-dias`}>
              Días, con la ida y la vuelta
            </span>{" "}
            <span className="fila__valor" aria-live="polite">
              {plural(c.dias, "día", "días")}
            </span>
          </span>
          <span className="paso">
            <button
              type="button"
              aria-label="Un día menos"
              disabled={c.dias <= dias.minimo}
              onClick={() => cambiar({ dias: acotar(c.dias - 1, dias.minimo, dias.maximo) })}
            >
              <Icono nombre="menos" />
            </button>
            <button
              type="button"
              aria-label="Un día más"
              disabled={c.dias >= dias.maximo}
              onClick={() => cambiar({ dias: acotar(c.dias + 1, dias.minimo, dias.maximo) })}
            >
              <Icono nombre="mas" />
            </button>
          </span>
        </fieldset>

        <button type="button" className="fila" onClick={() => abrir("intereses")} aria-haspopup="dialog">
          <span className="fila__icono">
            <Icono nombre="corazon" />
          </span>
          <span className="fila__texto">
            <span className="fila__nombre">Qué te gusta</span> <span className="fila__valor">{gustos}</span>
          </span>
          <span className="fila__fin">
            <Icono nombre="flecha" />
          </span>
        </button>

        <button type="button" className="fila" onClick={() => abrir("filtros")} aria-haspopup="dialog">
          <span className="fila__icono">
            <Icono nombre="ajustes" />
          </span>
          <span className="fila__texto">
            <span className="fila__nombre">Presupuesto y altura</span>{" "}
            <span className="fila__valor">
              {filtros.length > 0 ? mayuscula(filtros.join(", ")) : "Sin límites"}
            </span>
          </span>
          <span className="fila__fin">
            <Icono nombre="flecha" />
          </span>
        </button>
      </div>

      <div className="inicio__acciones">
        <button type="submit" className="boton boton--primario boton--grande boton--ancho">
          Ver mis viajes
        </button>
        <button type="button" className="boton boton--texto" onClick={() => buscar(true)}>
          Sorpréndeme con lugares poco turísticos
        </button>
      </div>

      <Hoja abierta={abierta === "origen"} alCerrar={cerrar} titulo="¿Desde dónde sales?">
        <ElegirOrigen
          opciones={opciones}
          elegido={c.origen}
          elegir={(o) => {
            cambiar({ origen: o });
            cerrar();
          }}
        />
      </Hoja>

      <Hoja
        abierta={abierta === "cuando"}
        alCerrar={cerrar}
        titulo="¿Cuándo viajas?"
        pie={
          <button type="button" className="boton boton--primario boton--grande boton--ancho" onClick={cerrar}>
            Listo
          </button>
        }
      >
        <ElegirCuando c={c} cambiar={cambiar} />
      </Hoja>

      <Hoja
        abierta={abierta === "intereses"}
        alCerrar={cerrar}
        titulo="¿Qué te gusta?"
        pie={
          <button type="button" className="boton boton--primario boton--grande boton--ancho" onClick={cerrar}>
            Listo
          </button>
        }
      >
        <p className="hoja__ayuda">
          Elige uno, varios o ninguno. Los lugares que te gustan pesan más en el plan.
        </p>
        <div className="gustos">
          {opciones.intereses.map((i) => (
            <label key={i.id} className="gusto">
              <input
                type="checkbox"
                checked={c.intereses.includes(i.id)}
                onChange={() =>
                  cambiar({
                    intereses: c.intereses.includes(i.id)
                      ? c.intereses.filter((x) => x !== i.id)
                      : [...c.intereses, i.id],
                  })
                }
              />
              <span>
                <Icono nombre={ICONO_DE_INTERES[i.id] ?? "estrella"} tamano={26} />
                {i.etiqueta}
              </span>
            </label>
          ))}
        </div>
      </Hoja>

      <Hoja
        abierta={abierta === "filtros"}
        alCerrar={cerrar}
        titulo="Presupuesto y altura"
        pie={
          <button type="button" className="boton boton--primario boton--grande boton--ancho" onClick={cerrar}>
            Listo
          </button>
        }
      >
        <ElegirFiltros c={c} cambiar={cambiar} />
      </Hoja>
    </form>
  );
}

function ElegirOrigen({
  opciones,
  elegido,
  elegir,
}: {
  opciones: Opciones;
  elegido: string;
  elegir: (id: string) => void;
}) {
  const [texto, ponerTexto] = useState("");
  const lista = useMemo(
    () => opciones.origenes.filter((o) => plano(o.nombre).includes(plano(texto.trim()))),
    [opciones.origenes, texto],
  );
  return (
    <>
      <label className="buscador">
        <Icono nombre="lupa" />
        <span className="solo-lector">Buscar una ciudad</span>
        <input
          type="search"
          placeholder="Busca tu ciudad"
          value={texto}
          onChange={(e) => ponerTexto(e.target.value)}
          // Enter elige la primera ciudad que coincide; no manda el formulario de atrás.
          onKeyDown={(e) => {
            if (e.key !== "Enter") return;
            e.preventDefault();
            const primera = lista[0];
            if (primera) elegir(primera.id);
          }}
          autoComplete="off"
        />
      </label>
      <ul className="opciones-lista">
        {lista.map((o) => (
          <li key={o.id}>
            <button
              type="button"
              className="opcion"
              aria-pressed={o.id === elegido}
              onClick={() => elegir(o.id)}
            >
              <span>{o.nombre}</span>
              {o.id === elegido ? <Icono nombre="bien" /> : null}
            </button>
          </li>
        ))}
        {lista.length === 0 ? <li className="opciones-lista__vacia">Ninguna ciudad coincide.</li> : null}
      </ul>
    </>
  );
}

function ElegirCuando({ c, cambiar }: { c: Consulta; cambiar: (p: Partial<Consulta>) => void }) {
  const id = useId();
  return (
    <>
      <fieldset>
        <legend className="hoja__ayuda">El mes del viaje</legend>
        <div className="meses-grilla">
          {MESES_CORTOS.map((corto, indice) => (
            <label key={corto} className="mes-opcion">
              <input
                type="radio"
                name={`${id}-mes`}
                value={indice + 1}
                checked={c.mes === indice + 1}
                onChange={() => {
                  const mismaFecha = c.fecha_inicio && fechaLocal(c.fecha_inicio)?.getMonth() === indice;
                  cambiar({ mes: indice + 1, fecha_inicio: mismaFecha ? c.fecha_inicio : null });
                }}
              />
              <span>{mayuscula(mes(indice + 1))}</span>
            </label>
          ))}
        </div>
      </fieldset>
      <div className="fecha-exacta">
        <label htmlFor={`${id}-fecha`}>¿Ya tienes fecha de salida?</label>
        <input
          id={`${id}-fecha`}
          type="date"
          min={aIso(new Date())}
          value={c.fecha_inicio ?? ""}
          // Enter en la fecha no busca: la hoja se cierra con «Listo».
          onKeyDown={(e) => {
            if (e.key === "Enter") e.preventDefault();
          }}
          onChange={(e) => {
            const f = e.target.value ? fechaLocal(e.target.value) : null;
            cambiar(f ? { fecha_inicio: e.target.value, mes: f.getMonth() + 1 } : { fecha_inicio: null });
          }}
        />
        <p className="hoja__ayuda">
          Con la fecha, cada día lleva su fecha y te avisamos de las fiestas de ese día.
        </p>
      </div>
    </>
  );
}

function ElegirFiltros({ c, cambiar }: { c: Consulta; cambiar: (p: Partial<Consulta>) => void }) {
  const id = useId();
  const topePresupuesto = PRESUPUESTO.maximo + PRESUPUESTO.paso;
  const topeAltitud = ALTITUD.maximo + ALTITUD.paso;
  return (
    <div className="filtros-hoja">
      <div className="deslizador">
        <div className="deslizador__cabeza">
          <label htmlFor={`${id}-presupuesto`}>Presupuesto por persona</label>
          <output htmlFor={`${id}-presupuesto`}>
            {c.presupuesto === null ? "Sin tope" : soles(c.presupuesto)}
          </output>
        </div>
        <input
          id={`${id}-presupuesto`}
          type="range"
          min={PRESUPUESTO.minimo}
          max={topePresupuesto}
          step={PRESUPUESTO.paso}
          value={
            c.presupuesto === null
              ? topePresupuesto
              : acotar(c.presupuesto, PRESUPUESTO.minimo, PRESUPUESTO.maximo)
          }
          aria-valuetext={c.presupuesto === null ? "Sin tope" : `${c.presupuesto} soles`}
          onChange={(e) => {
            const n = Number(e.target.value);
            cambiar({ presupuesto: n > PRESUPUESTO.maximo ? null : n });
          }}
        />
        <p className="hoja__ayuda">
          Para todo el viaje. Ordena los viajes y te avisa si uno se pasa; no esconde ninguno.
        </p>
      </div>
      <div className="deslizador">
        <div className="deslizador__cabeza">
          <label htmlFor={`${id}-altitud`}>Altura máxima</label>
          <output htmlFor={`${id}-altitud`}>
            {c.altitud_max === null ? "Sin límite" : metros(c.altitud_max)}
          </output>
        </div>
        <input
          id={`${id}-altitud`}
          type="range"
          min={ALTITUD.minimo}
          max={topeAltitud}
          step={ALTITUD.paso}
          value={c.altitud_max === null ? topeAltitud : acotar(c.altitud_max, ALTITUD.minimo, ALTITUD.maximo)}
          aria-valuetext={c.altitud_max === null ? "Sin límite" : `${c.altitud_max} metros`}
          onChange={(e) => {
            const n = Number(e.target.value);
            cambiar({ altitud_max: n > ALTITUD.maximo ? null : n });
          }}
        />
        <p className="hoja__ayuda">Si la altura te cae mal, ninguna parada pasará de ahí.</p>
      </div>
    </div>
  );
}

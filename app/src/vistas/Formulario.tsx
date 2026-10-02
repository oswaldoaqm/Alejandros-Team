// Pantalla 1: qué viaje quiere el viajero. Solo el mes es obligatorio. Las opciones (orígenes,
// intereses y rangos) vienen de GET /v1/opciones: aquí no hay ninguna lista fija.

import { type FormEvent, useId, useState } from "react";
import type { Opciones } from "../api/tipos";
import { type Consulta, POR_DEFECTO } from "../consulta";
import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { aIso, fechaLocal, MESES_CORTOS, mayuscula, mes, metros, soles } from "../formato";
import { Enlace } from "../piezas/Enlace";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { Icono } from "../piezas/Icono";
import { enlaces } from "../ruta";

// Los dos deslizadores terminan en «sin tope»: ese extremo no manda nada al API.
const PRESUPUESTO = { minimo: 200, maximo: 5000, paso: 100 };
const ALTITUD = { minimo: 500, maximo: 5000, paso: 100 };

function mesQueViene(): number {
  return ((new Date().getMonth() + 1) % 12) + 1;
}

function acotar(valor: number, minimo: number, maximo: number): number {
  return Math.min(maximo, Math.max(minimo, valor));
}

export function Formulario({ inicial }: { inicial: Consulta | null }) {
  const { opciones } = useApp();
  useTitulo(inicial ? "Cambiar la consulta" : null);
  return (
    <section className="pagina pagina--angosta">
      <p className="sobretitulo">Paso 1 de 2 · Definir el viaje</p>
      <h1 tabIndex={-1}>¿Qué viaje quieres hacer?</h1>
      <p className="bajada">
        Cuéntanos lo que sepas y te proponemos tres viajes, día por día. Solo el mes es obligatorio.
      </p>
      {opciones.datos ? (
        <Campos opciones={opciones.datos} inicial={inicial} />
      ) : opciones.error ? (
        <ErrorVista error={opciones.error} reintentar={opciones.reintentar} />
      ) : (
        <Cargando texto="Cargando las opciones del viaje…" />
      )}
    </section>
  );
}

function Campos({ opciones, inicial }: { opciones: Opciones; inicial: Consulta | null }) {
  const { navegar } = useApp();
  const id = useId();
  const [c, poner] = useState<Consulta>(() => inicial ?? { ...POR_DEFECTO, mes: mesQueViene() });
  const cambiar = (parte: Partial<Consulta>) => poner((antes) => ({ ...antes, ...parte }));

  const dias = { minimo: opciones.dias.minimo, maximo: opciones.dias.maximo };
  const alternar = (interes: string) =>
    cambiar({
      intereses: c.intereses.includes(interes)
        ? c.intereses.filter((i) => i !== interes)
        : [...c.intereses, interes],
    });

  const buscar = (sorpresa: boolean) => navegar(enlaces.resultados({ ...c, sorpresa }));
  // Enter en cualquier campo envía el formulario: eso es «Generar mis rutas», no la sorpresa.
  const enviar = (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    buscar(false);
  };

  const topePresupuesto = PRESUPUESTO.maximo + PRESUPUESTO.paso;
  const topeAltitud = ALTITUD.maximo + ALTITUD.paso;

  return (
    <form className="formulario" onSubmit={enviar} aria-label="Definir el viaje">
      <div className="formulario__par">
        <div className="campo">
          <label htmlFor={`${id}-origen`}>Punto de partida</label>
          <select id={`${id}-origen`} value={c.origen} onChange={(e) => cambiar({ origen: e.target.value })}>
            {opciones.origenes.map((o) => (
              <option key={o.id} value={o.id}>
                {o.nombre}
              </option>
            ))}
          </select>
        </div>

        <div className="campo">
          <label htmlFor={`${id}-dias`}>Días disponibles</label>
          <div className="contador">
            <button
              type="button"
              aria-label="Un día menos"
              disabled={c.dias <= dias.minimo}
              onClick={() => cambiar({ dias: acotar(c.dias - 1, dias.minimo, dias.maximo) })}
            >
              <Icono nombre="menos" />
            </button>
            <input
              id={`${id}-dias`}
              type="number"
              inputMode="numeric"
              min={dias.minimo}
              max={dias.maximo}
              value={c.dias}
              aria-describedby={`${id}-dias-ayuda`}
              onChange={(e) => {
                const n = Number(e.target.value);
                if (Number.isInteger(n)) cambiar({ dias: acotar(n, dias.minimo, dias.maximo) });
              }}
            />
            <button
              type="button"
              aria-label="Un día más"
              disabled={c.dias >= dias.maximo}
              onClick={() => cambiar({ dias: acotar(c.dias + 1, dias.minimo, dias.maximo) })}
            >
              <Icono nombre="mas" />
            </button>
          </div>
          <p className="ayuda" id={`${id}-dias-ayuda`}>
            Cuentan la ida y la vuelta.
          </p>
        </div>
      </div>

      <fieldset className="campo">
        <legend>
          ¿Qué te interesa? <span className="opcional">Uno, varios o ninguno</span>
        </legend>
        <div className="chips">
          {opciones.intereses.map((i) => (
            <label key={i.id} className="chip chip--elegible">
              <input type="checkbox" checked={c.intereses.includes(i.id)} onChange={() => alternar(i.id)} />
              <span>{i.etiqueta}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <fieldset className="campo">
        <legend>
          Mes de viaje <span className="obligatorio">Obligatorio</span>
        </legend>
        <div className="meses">
          {MESES_CORTOS.map((corto, indice) => (
            <label key={corto} className="mes">
              <input
                type="radio"
                name={`${id}-mes`}
                value={indice + 1}
                checked={c.mes === indice + 1}
                onChange={() => {
                  const mismaFecha = c.fecha_inicio && fechaLocal(c.fecha_inicio)?.getMonth() === indice;
                  cambiar({ mes: indice + 1, fecha_inicio: mismaFecha ? c.fecha_inicio : null });
                }}
                required
              />
              <span>
                <span aria-hidden="true">{mayuscula(corto)}</span>
                <span className="solo-lector">{mayuscula(mes(indice + 1))}</span>
              </span>
            </label>
          ))}
        </div>
        <div className="campo campo--suelto">
          <label htmlFor={`${id}-fecha`}>
            ¿Ya tienes fecha de salida? <span className="opcional">Opcional</span>
          </label>
          <input
            id={`${id}-fecha`}
            type="date"
            min={aIso(new Date())}
            value={c.fecha_inicio ?? ""}
            aria-describedby={`${id}-fecha-ayuda`}
            onChange={(e) => {
              const f = e.target.value ? fechaLocal(e.target.value) : null;
              cambiar(f ? { fecha_inicio: e.target.value, mes: f.getMonth() + 1 } : { fecha_inicio: null });
            }}
          />
          <p className="ayuda" id={`${id}-fecha-ayuda`}>
            Con la fecha, cada día del viaje lleva su día y las fiestas se cruzan día por día.
          </p>
        </div>
      </fieldset>

      <div className="formulario__par">
        <div className="campo">
          <label htmlFor={`${id}-presupuesto`}>
            Presupuesto total <span className="opcional">Opcional</span>
          </label>
          <output className="lectura" htmlFor={`${id}-presupuesto`}>
            {c.presupuesto === null ? "Sin tope" : soles(c.presupuesto)}
          </output>
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
            aria-describedby={`${id}-presupuesto-ayuda`}
            onChange={(e) => {
              const n = Number(e.target.value);
              cambiar({ presupuesto: n > PRESUPUESTO.maximo ? null : n });
            }}
          />
          <div className="extremos" aria-hidden="true">
            <span>{soles(PRESUPUESTO.minimo)}</span>
            <span>Sin tope</span>
          </div>
          <p className="ayuda" id={`${id}-presupuesto-ayuda`}>
            Por persona, para todo el viaje. Ordena las rutas y avisa; no esconde ninguna.
          </p>
        </div>

        <div className="campo">
          <label htmlFor={`${id}-altitud`}>
            Altitud máxima <span className="opcional">Opcional</span>
          </label>
          <output className="lectura" htmlFor={`${id}-altitud`}>
            {c.altitud_max === null ? "Sin límite" : metros(c.altitud_max)}
          </output>
          <input
            id={`${id}-altitud`}
            type="range"
            min={ALTITUD.minimo}
            max={topeAltitud}
            step={ALTITUD.paso}
            value={
              c.altitud_max === null ? topeAltitud : acotar(c.altitud_max, ALTITUD.minimo, ALTITUD.maximo)
            }
            aria-valuetext={c.altitud_max === null ? "Sin límite" : `${c.altitud_max} metros`}
            aria-describedby={`${id}-altitud-ayuda`}
            onChange={(e) => {
              const n = Number(e.target.value);
              cambiar({ altitud_max: n > ALTITUD.maximo ? null : n });
            }}
          />
          <div className="extremos" aria-hidden="true">
            <span>{metros(ALTITUD.minimo)}</span>
            <span>Sin límite</span>
          </div>
          <p className="ayuda" id={`${id}-altitud-ayuda`}>
            Ninguna parada pasará de esa altura.
          </p>
        </div>
      </div>

      <div className="formulario__acciones">
        <button type="button" className="boton boton--secundario boton--grande" onClick={() => buscar(true)}>
          Sorpréndeme
        </button>
        <button type="submit" className="boton boton--primario boton--grande">
          Generar mis rutas
        </button>
      </div>
      <p className="ayuda ayuda--centrada">«Sorpréndeme» busca solo fuera del circuito de Lima y Cusco.</p>

      <p className="procedencia">
        Datos {opciones.version_datos} · Inventario oficial de MINCETUR, OpenStreetMap y Open-Meteo ·{" "}
        <Enlace href={enlaces.acerca()}>Cómo funciona</Enlace>
      </p>
    </form>
  );
}

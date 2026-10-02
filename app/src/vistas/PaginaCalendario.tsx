// El calendario de fiestas y eventos de un mes, en todo el país o en una región.
// Sale de GET /v1/eventos?desde=…&hasta=…

import { useId, useMemo, useState } from "react";
import type { Eventos } from "../api/tipos";
import { type Consulta, POR_DEFECTO } from "../consulta";
import { usePedido } from "../estado/pedido";
import { useTitulo } from "../estado/titulo";
import { aIso, MESES_CORTOS, mayuscula, mes, plural } from "../formato";
import { Enlace } from "../piezas/Enlace";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { Icono } from "../piezas/Icono";
import { ListaEventos } from "../piezas/Listas";
import { enlaces } from "../ruta";

/** El primer y el último día de la próxima vez que cae ese mes (el actual cuenta). */
export function ventanaDelMes(numero: number, hoy: Date): { desde: string; hasta: string; anio: number } {
  const anio = hoy.getFullYear() + (numero < hoy.getMonth() + 1 ? 1 : 0);
  return {
    desde: aIso(new Date(anio, numero - 1, 1)),
    hasta: aIso(new Date(anio, numero, 0)),
    anio,
  };
}

interface Props {
  consulta: Consulta | null;
  /** El mes en que se abre; sin él, el de la consulta o el actual. */
  mes: number | null;
}

export function PaginaCalendario({ consulta, mes: alAbrir }: Props) {
  const id = useId();
  const [elegido, elegir] = useState(() => alAbrir ?? consulta?.mes ?? new Date().getMonth() + 1);
  const [region, elegirRegion] = useState("");
  const { desde, hasta, anio } = useMemo(() => ventanaDelMes(elegido, new Date()), [elegido]);
  const pedido = usePedido<Eventos>("/v1/eventos", `desde=${desde}&hasta=${hasta}`);
  const alDia = pedido.datos !== null && !pedido.cargando;
  useTitulo(`Fiestas de ${mes(elegido)}`);

  const eventos = pedido.datos?.eventos ?? [];
  const regiones = useMemo(
    () => [...new Set(eventos.map((e) => e.region))].sort((a, b) => a.localeCompare(b, "es")),
    [eventos],
  );
  // La región elegida puede no tener eventos en el mes nuevo: entonces se ven todas.
  const filtro = regiones.includes(region) ? region : "";
  const visibles = filtro ? eventos.filter((e) => e.region === filtro) : eventos;

  return (
    <section className="pagina pagina--media">
      {consulta ? (
        <p className="volver">
          <Enlace href={enlaces.resultados(consulta)} volver>
            <Icono nombre="atras" tamano={16} />
            Volver a tus rutas
          </Enlace>
        </p>
      ) : null}
      <h1 tabIndex={-1}>Fiestas y eventos</h1>
      <p className="bajada">
        Las fiestas, ferias y festivales del inventario oficial de MINCETUR y los eventos que publican las
        municipalidades, mes por mes.
      </p>

      <div className="filtros">
        <fieldset className="campo">
          <legend>Mes</legend>
          <div className="meses">
            {MESES_CORTOS.map((corto, indice) => (
              <label key={corto} className="mes">
                <input
                  type="radio"
                  name={`${id}-mes`}
                  checked={elegido === indice + 1}
                  onChange={() => elegir(indice + 1)}
                />
                <span>
                  <span aria-hidden="true">{mayuscula(corto)}</span>
                  <span className="solo-lector">{mayuscula(mes(indice + 1))}</span>
                </span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="campo">
          <label htmlFor={`${id}-region`}>Región</label>
          <select id={`${id}-region`} value={filtro} onChange={(e) => elegirRegion(e.target.value)}>
            <option value="">Todo el país</option>
            {regiones.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Sigue siendo un título; lo de adentro avisa a los lectores de pantalla cuando cambia la cuenta. */}
      <h2 className="rotulo">
        <span role="status">
          {pedido.cargando
            ? "Buscando…"
            : alDia
              ? `${plural(visibles.length, "evento", "eventos")} en ${mes(elegido)} de ${anio}${filtro ? ` · ${filtro}` : ""}`
              : `${mayuscula(mes(elegido))} de ${anio}`}
        </span>
      </h2>

      {pedido.error ? <ErrorVista error={pedido.error} reintentar={pedido.reintentar} /> : null}
      {pedido.datos === null && pedido.cargando ? <Cargando texto="Cargando el calendario…" /> : null}
      {pedido.datos !== null ? (
        <div aria-busy={pedido.cargando} className={pedido.cargando ? "resultado--espera" : undefined}>
          <ListaEventos eventos={visibles} vacio="No hay eventos registrados ese mes." />
        </div>
      ) : null}

      <p className="ayuda">
        Una fecha «aproximada» no viene con su día en la ficha: se calcula (el santo del día, la Pascua) o
        solo se conoce el mes. Conviene confirmarla antes de viajar. Cada evento del inventario enlaza a su
        ficha oficial; los que dicen «Publicado por…» los anunció esa entidad, con sus fechas.{" "}
        <Enlace href={enlaces.publicar()}>¿Organizas uno? Publícalo</Enlace>
      </p>

      <p>
        <Enlace
          href={enlaces.editar({ ...(consulta ?? POR_DEFECTO), mes: elegido, fecha_inicio: null })}
          className="boton boton--primario"
        >
          Armar un viaje para {mes(elegido)}
        </Enlace>
      </p>
    </section>
  );
}

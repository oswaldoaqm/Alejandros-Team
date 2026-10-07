// Las fiestas de un mes, en todo el país o en una región: las del inventario oficial de
// MINCETUR y las que publican las municipalidades. Sale de GET /v1/eventos?desde=…&hasta=…

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
import { type Segmento, Segmentos } from "../piezas/Segmentos";
import { enlaces } from "../ruta";

/** Cuántas se ven antes de «Ver N eventos más»: un mes de fiestas llega a cien. */
const PRIMEROS = 30;

const MESES: Segmento<number>[] = MESES_CORTOS.map((corto, indice) => ({
  valor: indice + 1,
  texto: mayuscula(corto),
  nombre: mayuscula(mes(indice + 1)),
}));

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
  // Primero lo que empieza en el mes; lo que viene del anterior y todavía dura, aparte y al final.
  const empiezan = visibles.filter((e) => !e.fecha_inicio || e.fecha_inicio >= desde);
  const siguen = visibles.filter((e) => e.fecha_inicio && e.fecha_inicio < desde);
  const cuando = `${mes(elegido)} de ${anio}`;

  return (
    <section className="pagina pagina--media calendario">
      {consulta ? (
        <p className="volver">
          <Enlace href={enlaces.resultados(consulta)} volver>
            <Icono nombre="atras" tamano={16} />
            Volver a tus viajes
          </Enlace>
        </p>
      ) : null}
      <h1 tabIndex={-1} className="pagina__titulo">
        Fiestas
      </h1>
      <p className="pagina__bajada">Fiestas, ferias y festivales de todo el Perú, mes por mes.</p>

      <div className="calendario__filtros">
        <Segmentos
          leyenda="Mes"
          segmentos={MESES}
          valor={elegido}
          elegir={elegir}
          className="selector-de-meses"
        />
        <div className="calendario__region">
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
      <h2 className="calendario__cuenta">
        <span role="status">
          {pedido.cargando
            ? "Buscando…"
            : alDia
              ? `${plural(visibles.length, "evento", "eventos")} en ${filtro ? `${filtro}, en ` : ""}${cuando}`
              : mayuscula(cuando)}
        </span>
      </h2>

      {pedido.error ? <ErrorVista error={pedido.error} reintentar={pedido.reintentar} /> : null}
      {pedido.datos === null && pedido.cargando ? <Cargando texto="Cargando las fiestas…" /> : null}
      {pedido.datos !== null ? (
        <div aria-busy={pedido.cargando} className={pedido.cargando ? "resultado--espera" : undefined}>
          {/* La llave la rehace al cambiar de mes o de región: vuelve a mostrar solo las primeras. */}
          <ListaEventos
            key={`${elegido}-${filtro}`}
            eventos={empiezan}
            limite={PRIMEROS}
            vacio={
              siguen.length > 0
                ? `Ninguno empieza en ${mes(elegido)}.`
                : "No hay fiestas ni eventos registrados ese mes."
            }
          />
          {siguen.length > 0 ? (
            <section className="calendario__siguen" aria-labelledby={`${id}-siguen`}>
              <h3 id={`${id}-siguen`} className="calendario__subtitulo">
                Empezaron en {mes(elegido === 1 ? 12 : elegido - 1)} y siguen en {mes(elegido)}
              </h3>
              <ListaEventos key={`${elegido}-${filtro}`} eventos={siguen} limite={5} />
            </section>
          ) : null}
        </div>
      ) : null}

      <div className="calendario__accion">
        <Enlace
          href={enlaces.editar({ ...(consulta ?? POR_DEFECTO), mes: elegido, fecha_inicio: null })}
          className="boton boton--primario"
        >
          Armar un viaje para {mes(elegido)}
        </Enlace>
        <p>
          ¿Organizas una fiesta o una feria? <Enlace href={enlaces.publicar()}>Publícala aquí</Enlace>
        </p>
      </div>

      <footer className="letra-chica">
        <h2 className="letra-chica__titulo">Sobre estos datos</h2>
        <p>
          Una fecha aproximada no viene con su día en la ficha: se calcula (el santo del día, la Pascua) o
          solo se conoce el mes. Conviene confirmarla antes de viajar.
        </p>
        <p>
          La mayoría de las fiestas viene del inventario oficial de MINCETUR, y cada una enlaza a su ficha.
          Las que dicen «Publicado por…» las anunció esa municipalidad o entidad, con sus fechas.
        </p>
      </footer>
    </section>
  );
}

// La ficha de un polo: qué hay para ver, cómo es su clima mes a mes y qué fiestas vienen.
// Sale de GET /v1/polos/{id}.

import { useState } from "react";
import type { PoloDetalle } from "../api/tipos";
import type { Consulta } from "../consulta";
import { usePedido } from "../estado/pedido";
import { useTitulo } from "../estado/titulo";
import { lista, metros, plural } from "../formato";
import { ClimaAnual } from "../piezas/ClimaAnual";
import { Enlace } from "../piezas/Enlace";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { Icono } from "../piezas/Icono";
import { Jerarquia } from "../piezas/Insignias";
import { ListaEventos } from "../piezas/Listas";
import { DatosDeRecurso, MasDeRecurso } from "../piezas/Recurso";
import { enlaces } from "../ruta";

const PRIMEROS = 10;

function Ficha({ detalle, consulta }: { detalle: PoloDetalle; consulta: Consulta | null }) {
  const { polo, recursos, clima, eventos } = detalle;
  const [todos, verTodos] = useState(false);
  const visibles = todos ? recursos : recursos.slice(0, PRIMEROS);
  const mesInicial = consulta?.mes ?? new Date().getMonth() + 1;

  return (
    <>
      <p className="bajada">
        {lista(polo.regiones)} · se duerme en {polo.base.nombre}
        {polo.base.altitud_m != null ? ` (${metros(polo.base.altitud_m)})` : ""} ·{" "}
        {plural(polo.recursos, "lugar", "lugares")} del inventario oficial.
      </p>
      {polo.fuera_del_circuito ? (
        <p>
          <span className="insignia insignia--fuerte">Fuera del circuito</span>{" "}
          <span className="ayuda">Ningún lugar del polo está en Lima ni en Cusco.</span>
        </p>
      ) : null}

      <section aria-labelledby="polo-clima">
        <h2 className="rotulo" id="polo-clima">
          El clima, mes a mes
        </h2>
        <ClimaAnual clima={clima} inicial={mesInicial} />
      </section>

      <section aria-labelledby="polo-lugares">
        <h2 className="rotulo" id="polo-lugares">
          Qué hay para ver · {plural(recursos.length, "parada posible", "paradas posibles")}
        </h2>
        <p className="ayuda">
          Los lugares del polo que pueden ser una parada, de mayor a menor jerarquía. En un viaje entran los
          que caben en tus días.
        </p>
        <ol className="paradas paradas--sueltas">
          {visibles.map((recurso) => (
            <li key={recurso.codigo} className="parada">
              <div className="parada__cuerpo">
                <p className="parada__linea">
                  <span className="parada__nombre">{recurso.nombre}</span>
                  <Jerarquia valor={recurso.jerarquia} />
                </p>
                <DatosDeRecurso recurso={recurso} />
                <MasDeRecurso recurso={recurso} />
              </div>
            </li>
          ))}
        </ol>
        {recursos.length > PRIMEROS ? (
          <button
            type="button"
            className="boton boton--secundario"
            aria-expanded={todos}
            onClick={() => verTodos(!todos)}
          >
            {todos ? `Ver solo las ${PRIMEROS} primeras` : `Ver las ${recursos.length}`}
          </button>
        ) : null}
      </section>

      <section aria-labelledby="polo-eventos">
        <h2 className="rotulo" id="polo-eventos">
          Fiestas y eventos de los próximos doce meses
        </h2>
        <ListaEventos eventos={eventos} vacio="No hay eventos registrados en este polo." />
      </section>

      <footer className="fuentes">
        <h2 className="rotulo">De dónde sale esto</h2>
        <ul className="lista-simple">
          {detalle.atribucion.map((linea) => (
            <li key={linea}>{linea}</li>
          ))}
        </ul>
        <p>Datos {detalle.version_datos}.</p>
      </footer>
    </>
  );
}

export function PaginaPolo({ id, consulta }: { id: number; consulta: Consulta | null }) {
  const pedido = usePedido<PoloDetalle>(`/v1/polos/${id}`);
  const nombre = pedido.datos?.polo.nombre ?? null;
  useTitulo(nombre ?? "Polo");

  return (
    <section className="pagina pagina--media">
      <p className="volver">
        <Enlace href={consulta ? enlaces.resultados(consulta) : enlaces.inicio()} volver>
          <Icono nombre="atras" tamano={16} />
          {consulta ? "Volver a tus rutas" : "Ir al inicio"}
        </Enlace>
      </p>
      <p className="sobretitulo">Polo</p>
      <h1 tabIndex={-1}>{nombre ?? "Polo"}</h1>
      {pedido.datos ? (
        <Ficha detalle={pedido.datos} consulta={consulta} />
      ) : pedido.error ? (
        <ErrorVista error={pedido.error} reintentar={pedido.reintentar} />
      ) : (
        <Cargando texto="Cargando el polo…" />
      )}
    </section>
  );
}

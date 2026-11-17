// Panel separado del viaje. La simulación y la actividad registrada nunca se mezclan.

import { useEffect, useMemo, useState } from "react";
import { ErrorApi, pedir } from "../api/cliente";
import { useTitulo } from "../estado/titulo";
import { type Analisis, AnalisisGerencial, type VistaGerencial } from "./AnalisisGerencial";

type Modo = "simulacion" | "real";
type SerieClave = "sesiones" | "busquedas" | "detalles" | "guardados";

interface Indicador {
  id: string;
  etiqueta: string;
  valor: number | null;
  unidad?: string;
  descripcion?: string;
  grupo?: string;
}

interface PuntoSerie {
  fecha: string;
  sesiones: number;
  busquedas: number;
  detalles: number;
  guardados: number;
}

interface Resumen {
  analisis?: Analisis;
  modo: Modo;
  actualizado: string | null;
  consultado?: string;
  total_eventos?: number;
  actividad_reciente?: { instante: string; tipo: string; etiqueta: string }[];
  periodo: { desde: string | null; hasta: string | null };
  indicadores: Indicador[];
  serie: PuntoSerie[];
  destinos: { nombre: string; cantidad: number }[];
  intereses: { nombre: string; cantidad: number }[];
  fuente?: string;
}

const SERIES: { id: SerieClave; nombre: string }[] = [
  { id: "sesiones", nombre: "Sesiones" },
  { id: "busquedas", nombre: "Búsquedas" },
  { id: "detalles", nombre: "Itinerarios abiertos" },
  { id: "guardados", nombre: "Guardados" },
];

const NOMBRES_GRUPO: Record<string, string> = {
  uso: "Uso",
  busqueda: "Búsqueda",
  interaccion: "Interacción",
  calidad: "Calidad",
  preferencias: "Preferencias",
};

const DESTACADOS = ["sesiones", "busquedas_iniciadas", "busquedas_completadas", "itinerarios_abiertos"];

function numero(valor: number | null, unidad = ""): string {
  if (valor === null || !Number.isFinite(valor)) return "Sin datos";
  const cifra = new Intl.NumberFormat("es-PE", {
    maximumFractionDigits: Number.isInteger(valor) ? 0 : 1,
  }).format(valor);
  if (unidad === "S/") return `S/ ${cifra}`;
  return unidad ? `${cifra} ${unidad}` : cifra;
}

function fechaLegible(valor: string): string {
  const fecha = new Date(valor);
  return Number.isNaN(fecha.getTime())
    ? valor
    : new Intl.DateTimeFormat("es-PE", {
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        timeZone: "America/Lima",
      }).format(fecha);
}

function Trayectoria({
  puntos,
  campo,
  comparar,
}: {
  puntos: PuntoSerie[];
  campo: SerieClave;
  comparar: SerieClave | "ninguna";
}) {
  if (puntos.length === 0)
    return <p className="indicadores__vacio">Todavía no hay actividad en este periodo.</p>;
  const valores = puntos.map((p) => p[campo]);
  const segundoCampo = comparar !== "ninguna" && comparar !== campo ? comparar : null;
  const segundosValores = segundoCampo ? puntos.map((p) => p[segundoCampo]) : [];
  // Un eje con pasos enteros evita etiquetas repetidas (0, 0, 1, 1) con poco uso.
  const maximo = Math.max(4, Math.ceil(Math.max(...valores, ...segundosValores) / 4) * 4);
  const ancho = 720;
  const alto = 230;
  const margenX = 34;
  const margenY = 24;
  const areaX = ancho - margenX * 2;
  const areaY = alto - margenY * 2;
  const posicion = (valor: number, indice: number) => ({
    x: margenX + (puntos.length === 1 ? areaX / 2 : (indice * areaX) / (puntos.length - 1)),
    y: margenY + areaY - (valor * areaY) / maximo,
  });
  const trazar = (datos: number[]) =>
    datos
      .map((v, i) => {
        const { x, y } = posicion(v, i);
        return `${i === 0 ? "M" : "L"}${x.toFixed(1)} ${y.toFixed(1)}`;
      })
      .join(" ");
  const linea = trazar(valores);
  const primero = posicion(0, 0);
  const ultimo = posicion(0, puntos.length - 1);
  const area = `${linea} L${ultimo.x.toFixed(1)} ${ultimo.y.toFixed(1)} L${primero.x.toFixed(1)} ${primero.y.toFixed(1)} Z`;
  const nombre = SERIES.find((s) => s.id === campo)?.nombre ?? campo;
  const nombreComparacion = SERIES.find((s) => s.id === segundoCampo)?.nombre;

  return (
    <>
      <div className="indicadores__leyenda">
        <span>
          <i className="indicadores__muestra indicadores__muestra--principal" />
          {nombre}
        </span>
        {nombreComparacion ? (
          <span>
            <i className="indicadores__muestra indicadores__muestra--comparacion" />
            {nombreComparacion}
          </span>
        ) : null}
      </div>
      <svg
        viewBox={`0 0 ${ancho} ${alto}`}
        role="img"
        aria-label={`${nombre}${nombreComparacion ? ` y ${nombreComparacion}` : ""} por día; máximo ${maximo}`}
      >
        <title>
          {nombre}
          {nombreComparacion ? ` y ${nombreComparacion}` : ""} por día, en el mismo eje de cantidad
        </title>
        {[0, 0.25, 0.5, 0.75, 1].map((parte) => {
          const y = margenY + areaY * (1 - parte);
          return (
            <g key={parte}>
              <line x1={margenX} x2={ancho - margenX} y1={y} y2={y} className="indicadores__guia" />
              <text x={margenX - 8} y={y + 4} textAnchor="end" className="indicadores__eje">
                {Math.round(maximo * parte)}
              </text>
            </g>
          );
        })}
        <path d={area} className="indicadores__area" />
        <path d={linea} className="indicadores__linea" />
        {segundoCampo ? (
          <path d={trazar(segundosValores)} className="indicadores__linea-comparacion" />
        ) : null}
        {puntos.length <= 14
          ? valores.map((v, i) => {
              const { x, y } = posicion(v, i);
              return (
                <circle key={puntos[i]?.fecha} cx={x} cy={y} r="4" className="indicadores__punto">
                  <title>{`${puntos[i]?.fecha}: ${v} ${nombre.toLowerCase()}`}</title>
                </circle>
              );
            })
          : null}
      </svg>
      <div className="indicadores__extremos" aria-hidden="true">
        <span>{puntos[0]?.fecha}</span>
        <span>{puntos[puntos.length - 1]?.fecha}</span>
      </div>
      <details className="indicadores__tabla">
        <summary>Ver los valores por día</summary>
        <div className="indicadores__tabla-scroll">
          <table>
            <thead>
              <tr>
                <th scope="col">Día</th>
                <th scope="col">{nombre}</th>
                {nombreComparacion ? <th scope="col">{nombreComparacion}</th> : null}
              </tr>
            </thead>
            <tbody>
              {puntos.map((p) => (
                <tr key={p.fecha}>
                  <th scope="row">{p.fecha}</th>
                  <td>{p[campo]}</td>
                  {segundoCampo ? <td>{p[segundoCampo]}</td> : null}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}

function Ranking({ titulo, filas }: { titulo: string; filas: { nombre: string; cantidad: number }[] }) {
  const maximo = Math.max(1, ...filas.map((f) => f.cantidad));
  return (
    <section className="indicadores__panel" aria-label={titulo}>
      <h2>{titulo}</h2>
      {filas.length === 0 ? (
        <p className="indicadores__vacio">Todavía no hay datos en este periodo.</p>
      ) : (
        <ol className="indicadores__ranking">
          {filas.slice(0, 7).map((fila) => (
            <li key={fila.nombre}>
              <div>
                <span>{fila.nombre}</span>
                <strong>{numero(fila.cantidad)}</strong>
              </div>
              <span className="indicadores__barra">
                <span style={{ width: `${(fila.cantidad * 100) / maximo}%` }} />
              </span>
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}

function descargarIndicadores(resumen: Resumen) {
  const celda = (valor: string | number | null | undefined) =>
    `"${String(valor ?? "").replaceAll('"', '""')}"`;
  const filas = [
    ["Fuente", "Desde", "Hasta", "Indicador", "Valor", "Unidad", "Definición"],
    ...resumen.indicadores.map((i) => [
      resumen.modo,
      resumen.periodo.desde,
      resumen.periodo.hasta,
      i.etiqueta,
      i.valor,
      i.unidad,
      i.descripcion,
    ]),
  ];
  const blob = new Blob([`\uFEFF${filas.map((fila) => fila.map(celda).join(";")).join("\r\n")}`], {
    type: "text/csv;charset=utf-8",
  });
  const enlace = document.createElement("a");
  const url = URL.createObjectURL(blob);
  enlace.href = url;
  enlace.download = `DreemGO_indicadores_${resumen.modo}.csv`;
  enlace.click();
  URL.revokeObjectURL(url);
}

export function Indicadores() {
  useTitulo("Indicadores");
  const [modo, ponerModo] = useState<Modo>("simulacion");
  const [vista, ponerVista] = useState<VistaGerencial>("resumen");
  const [desde, ponerDesde] = useState("");
  const [hasta, ponerHasta] = useState("");
  const [clave, ponerClave] = useState("");
  const [claveActiva, ponerClaveActiva] = useState("");
  const [serie, ponerSerie] = useState<SerieClave>("busquedas");
  const [comparar, ponerComparar] = useState<SerieClave | "ninguna">("ninguna");
  const [grupo, ponerGrupo] = useState("todos");
  const [resumen, ponerResumen] = useState<Resumen | null>(null);
  const [error, ponerError] = useState("");
  const [cargando, ponerCargando] = useState(false);
  const [recargar, ponerRecargar] = useState(0);
  const [automatico, ponerAutomatico] = useState(true);
  const [visible, ponerVisible] = useState(() => document.visibilityState !== "hidden");
  const [ultimaLectura, ponerUltimaLectura] = useState<string | null>(null);

  useEffect(() => {
    const alCambiar = () => ponerVisible(document.visibilityState !== "hidden");
    document.addEventListener("visibilitychange", alCambiar);
    return () => document.removeEventListener("visibilitychange", alCambiar);
  }, []);

  const periodoInvalido = Boolean(desde && hasta && hasta < desde);
  const grupos = resumen
    ? [...new Set(resumen.indicadores.map((i) => i.grupo).filter((g): g is string => Boolean(g)))]
    : [];
  const indicadoresVisibles =
    resumen?.indicadores.filter((i) => grupo === "todos" || i.grupo === grupo) ?? [];
  const parametros = useMemo(() => {
    const p = new URLSearchParams({ modo });
    if (desde) p.set("desde", desde);
    if (hasta) p.set("hasta", hasta);
    return p;
  }, [modo, desde, hasta]);

  useEffect(() => {
    void parametros;
    ponerResumen(null);
    ponerUltimaLectura(null);
  }, [parametros]);

  useEffect(() => {
    // Cambiar este número con «Actualizar ahora» fuerza una lectura inmediata.
    void recargar;
    if (periodoInvalido || (modo === "real" && !claveActiva)) {
      ponerResumen(null);
      ponerCargando(false);
      return;
    }
    let cancelado = false;
    let reloj: number | undefined;
    const control = new AbortController();
    if (!visible) return;
    const cargar = async () => {
      ponerCargando(true);
      try {
        const datos = await pedir<Resumen>("/v1/analitica/resumen", {
          parametros,
          cabeceras: modo === "real" ? { "X-Clave-Analitica": claveActiva } : undefined,
          senal: control.signal,
        });
        if (cancelado) return;
        ponerResumen(datos);
        ponerUltimaLectura(datos.consultado ?? new Date().toISOString());
        ponerError("");
      } catch (causa) {
        if (cancelado) return;
        if (causa instanceof ErrorApi && causa.tipo === "sin_permiso") {
          ponerResumen(null);
          ponerClaveActiva("");
          ponerError(
            causa.estado === 403
              ? "Este servidor aún no tiene habilitada la lectura de actividad. Configuren DREEMGO_CLAVE_ANALITICA en el API."
              : "La clave de lectura no es correcta. Revísala e inténtalo de nuevo.",
          );
        } else {
          ponerError(
            "No pudimos actualizar. Las cifras visibles corresponden a la última lectura correcta; volveremos a intentarlo.",
          );
        }
      } finally {
        if (!cancelado) {
          ponerCargando(false);
          if (modo === "real" && automatico) reloj = window.setTimeout(cargar, 3_000);
        }
      }
    };
    void cargar();
    return () => {
      cancelado = true;
      control.abort();
      window.clearTimeout(reloj);
    };
  }, [modo, claveActiva, parametros, periodoInvalido, recargar, automatico, visible]);

  return (
    <div className="indicadores">
      <header className="indicadores__hero">
        <div className="pagina">
          <p className="indicadores__eyebrow">DREEMGO · VISIÓN DEL PRODUCTO</p>
          <h1 tabIndex={-1}>Indicadores de uso</h1>
          <p>Qué exploran las personas, dónde encuentran valor y dónde se interrumpe el recorrido.</p>
          <span className="indicadores__hero-adorno" aria-hidden="true">
            ✳
          </span>
          {resumen ? (
            <dl className="indicadores__destacados">
              {DESTACADOS.flatMap((id) => {
                const indicador = resumen.indicadores.find((item) => item.id === id);
                return indicador
                  ? [
                      <div key={id}>
                        <dt>{indicador.etiqueta}</dt>
                        <dd>{numero(indicador.valor, indicador.unidad)}</dd>
                      </div>,
                    ]
                  : [];
              })}
            </dl>
          ) : null}
        </div>
      </header>

      <div className="pagina indicadores__contenido">
        <fieldset className="indicadores__modos">
          <legend className="solo-lector">Fuente de los indicadores</legend>
          <button
            type="button"
            aria-pressed={modo === "simulacion"}
            onClick={() => {
              ponerModo("simulacion");
              ponerResumen(null);
              ponerError("");
            }}
          >
            Simulación · 200 usuarios
          </button>
          <button
            type="button"
            aria-pressed={modo === "real"}
            onClick={() => {
              ponerModo("real");
              ponerResumen(null);
              ponerError("");
            }}
          >
            Actividad registrada
          </button>
        </fieldset>

        <p className={`indicadores__aviso ${modo === "simulacion" ? "indicadores__aviso--demo" : ""}`}>
          {modo === "simulacion"
            ? "Escenario de 200 usuarios ficticios, con una sesión por usuario durante 28 días. Los filtros cambian la muestra visible; no son visitantes ni compras reales."
            : "Solo se muestran acciones anónimas de visitantes que aceptaron compartir estadísticas. No hay ventas ni reservas."}
        </p>

        {modo === "real" ? (
          <div className="indicadores__prueba">
            <div>
              <strong>Mira cómo cambia mientras alguien usa DreemGO</strong>
              <p>
                Abre la web en otra pestaña, activa las estadísticas y busca un viaje. Vuelve aquí: las
                acciones aparecerán en la siguiente lectura.
              </p>
            </div>
            <a
              href="./#/planear"
              target="_blank"
              rel="noopener noreferrer"
              className="boton boton--secundario"
            >
              Abrir la web para probar
            </a>
          </div>
        ) : null}

        {modo === "real" && !claveActiva ? (
          <form
            className="indicadores__acceso"
            onSubmit={(evento) => {
              evento.preventDefault();
              ponerError("");
              ponerClaveActiva(clave.trim());
            }}
          >
            <label htmlFor="clave-indicadores">Clave de lectura del panel</label>
            <div>
              <input
                id="clave-indicadores"
                type="password"
                autoComplete="off"
                value={clave}
                onChange={(e) => ponerClave(e.target.value)}
              />
              <button type="submit" className="boton boton--primario" disabled={!clave.trim()}>
                Ver actividad
              </button>
            </div>
            <p>La clave se mantiene solo mientras esta pantalla está abierta.</p>
          </form>
        ) : null}

        {modo === "real" && claveActiva ? (
          <button
            type="button"
            className="indicadores__olvidar"
            onClick={() => {
              ponerClave("");
              ponerClaveActiva("");
              ponerResumen(null);
              ponerError("");
              ponerUltimaLectura(null);
            }}
          >
            Olvidar clave
          </button>
        ) : null}

        <div className="indicadores__filtros">
          <div>
            <label htmlFor="indicadores-desde">Desde</label>
            <input
              id="indicadores-desde"
              type="date"
              value={desde}
              onChange={(e) => ponerDesde(e.target.value)}
            />
          </div>
          <div>
            <label htmlFor="indicadores-hasta">Hasta</label>
            <input
              id="indicadores-hasta"
              type="date"
              value={hasta}
              onChange={(e) => ponerHasta(e.target.value)}
            />
          </div>
          <button
            type="button"
            className="boton boton--secundario"
            onClick={() => {
              ponerDesde("");
              ponerHasta("");
            }}
          >
            Todo el periodo
          </button>
          <button
            type="button"
            className="boton boton--secundario"
            onClick={() => ponerRecargar((n) => n + 1)}
            disabled={cargando || periodoInvalido || (modo === "real" && !claveActiva)}
          >
            Actualizar ahora
          </button>
        </div>
        {periodoInvalido ? (
          <p role="alert" className="indicadores__error">
            «Hasta» debe ser igual o posterior a «Desde».
          </p>
        ) : null}
        {error ? (
          <p role="alert" className="indicadores__error">
            {error}
          </p>
        ) : null}
        <div className="indicadores__conexion">
          <span
            className={`indicadores__pulso ${error ? "indicadores__pulso--error" : ""}`}
            aria-hidden="true"
          />
          <span role="status">
            {error
              ? "Conexión pendiente"
              : modo === "simulacion"
                ? "Ejemplo fijo para explorar"
                : !claveActiva
                  ? "Acceso protegido"
                  : !visible
                    ? "Pausado en segundo plano"
                    : automatico
                      ? "En vivo · lectura cada 3 segundos"
                      : "Actualización pausada"}
          </span>
          {modo === "real" && claveActiva ? (
            <button type="button" onClick={() => ponerAutomatico((valor) => !valor)}>
              {automatico ? "Pausar" : "Reanudar"}
            </button>
          ) : null}
        </div>
        <p className="indicadores__actualizado">
          {ultimaLectura
            ? `Última lectura: ${fechaLegible(ultimaLectura)} (Lima). `
            : cargando
              ? "Conectando con el API… "
              : ""}
          {resumen?.actualizado
            ? `Última acción: ${fechaLegible(resumen.actualizado)}.`
            : resumen
              ? "Aún sin actividad registrada."
              : ""}
        </p>

        {resumen ? (
          <>
            {resumen.analisis ? (
              <>
                <nav className="gerencia__vistas" aria-label="Vistas del dashboard">
                  {(
                    [
                      ["resumen", "Resumen ejecutivo", "Actividad y alcance"],
                      ["comportamiento", "Comportamiento", "Recorrido y concentración"],
                      ["estadistica", "Estadística", "Distribución y relaciones"],
                      ["proyeccion", "Proyección", "Próximos siete días"],
                    ] as const
                  ).map(([id, nombre, descripcion]) => (
                    <button type="button" key={id} aria-pressed={vista === id} onClick={() => ponerVista(id)}>
                      <strong>{nombre}</strong>
                      <span>{descripcion}</span>
                    </button>
                  ))}
                </nav>
                {vista === "resumen" ? (
                  <div className="gerencia__lectura">
                    <div>
                      <p>LECTURA DEL PERIODO</p>
                      <h2>Una mirada para decidir qué revisar</h2>
                      <p>
                        {resumen.analisis.pareto[0]
                          ? `${resumen.analisis.pareto[0].nombre} concentra ${numero(resumen.analisis.pareto[0].cantidad)} sesiones y el ${numero(resumen.analisis.pareto[0].porcentaje)} % de las sesiones sin guardar. Es un punto para investigar, no una causa demostrada.`
                          : "Todavía no hay sesiones sin guardar para identificar una concentración. Revisa el recorrido completo antes de sacar conclusiones."}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="boton boton--secundario"
                      onClick={() => descargarIndicadores(resumen)}
                    >
                      Descargar indicadores CSV
                    </button>
                  </div>
                ) : null}
                <AnalisisGerencial
                  datos={resumen.analisis}
                  vista={vista}
                  serie={resumen.serie}
                  indicadores={resumen.indicadores}
                  simulacion={modo === "simulacion"}
                />
              </>
            ) : null}
            {!resumen.analisis || vista === "resumen" ? (
              <details className="gerencia__detalle-indicadores" open={!resumen.analisis}>
                <summary>
                  Consultar los {resumen.indicadores.length} indicadores y la actividad reciente
                </summary>
                {resumen.actividad_reciente ? (
                  <section
                    className="indicadores__panel indicadores__actividad"
                    aria-labelledby="actividad-reciente-titulo"
                  >
                    <div className="indicadores__panel-cabeza">
                      <div>
                        <p>{modo === "simulacion" ? "RECORRIDO SIMULADO" : "LO QUE ESTÁ PASANDO"}</p>
                        <h2 id="actividad-reciente-titulo">Actividad reciente del periodo</h2>
                      </div>
                      <strong>{numero(resumen.total_eventos ?? 0)} acciones</strong>
                    </div>
                    {resumen.actividad_reciente.length > 0 ? (
                      <ol className="indicadores__actividad-lista">
                        {resumen.actividad_reciente.slice(0, 5).map((evento) => (
                          <li key={`${evento.instante}:${evento.tipo}`}>
                            <span aria-hidden="true" />
                            <strong>{evento.etiqueta}</strong>
                            <time dateTime={evento.instante}>{fechaLegible(evento.instante)}</time>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p className="indicadores__vacio">
                        La primera acción aparecerá aquí cuando alguien acepte compartir estadísticas y use la
                        web.
                      </p>
                    )}
                  </section>
                ) : null}
                <section aria-labelledby="indicadores-resumen">
                  <div className="indicadores__seccion-titulo">
                    <div>
                      <p>Vista general</p>
                      <h2 id="indicadores-resumen">
                        {grupo === "todos" ? resumen.indicadores.length : indicadoresVisibles.length}{" "}
                        indicadores
                      </h2>
                    </div>
                    <span>{resumen.modo === "simulacion" ? "SIMULACIÓN" : "ACTIVIDAD REGISTRADA"}</span>
                  </div>
                  <fieldset className="indicadores__grupos">
                    <legend>Mostrar indicadores de</legend>
                    <button
                      type="button"
                      aria-pressed={grupo === "todos"}
                      onClick={() => ponerGrupo("todos")}
                    >
                      Todos
                    </button>
                    {grupos.map((nombre) => (
                      <button
                        key={nombre}
                        type="button"
                        aria-pressed={grupo === nombre}
                        onClick={() => ponerGrupo(nombre)}
                      >
                        {NOMBRES_GRUPO[nombre] ?? nombre}
                      </button>
                    ))}
                  </fieldset>
                  <div className="indicadores__tarjetas">
                    {indicadoresVisibles.map((indicador, indice) => (
                      <article
                        key={indicador.id}
                        className={`indicadores__tarjeta ${indice < 4 ? "indicadores__tarjeta--principal" : ""}`}
                      >
                        <p>{indicador.etiqueta}</p>
                        <strong>{numero(indicador.valor, indicador.unidad)}</strong>
                        {indicador.descripcion ? <span>{indicador.descripcion}</span> : null}
                      </article>
                    ))}
                  </div>
                </section>

                <div className="indicadores__graficos">
                  <section
                    className="indicadores__panel indicadores__panel--serie"
                    aria-label="Evolución diaria"
                  >
                    <div className="indicadores__panel-cabeza">
                      <div>
                        <p>EVOLUCIÓN</p>
                        <h2>Actividad por día</h2>
                      </div>
                      <div className="indicadores__selectores">
                        <label>
                          Mostrar
                          <select
                            value={serie}
                            onChange={(e) => {
                              const elegida = e.target.value as SerieClave;
                              ponerSerie(elegida);
                              if (comparar === elegida) ponerComparar("ninguna");
                            }}
                          >
                            {SERIES.map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.nombre}
                              </option>
                            ))}
                          </select>
                        </label>
                        <label>
                          Comparar con
                          <select
                            value={comparar}
                            onChange={(e) => ponerComparar(e.target.value as SerieClave | "ninguna")}
                          >
                            <option value="ninguna">Sin comparación</option>
                            {SERIES.filter((s) => s.id !== serie).map((s) => (
                              <option key={s.id} value={s.id}>
                                {s.nombre}
                              </option>
                            ))}
                          </select>
                        </label>
                      </div>
                    </div>
                    <Trayectoria puntos={resumen.serie} campo={serie} comparar={comparar} />
                  </section>
                  <Ranking titulo="Destinos más abiertos" filas={resumen.destinos} />
                  <Ranking titulo="Intereses más elegidos" filas={resumen.intereses} />
                </div>

                <aside className="indicadores__no-comercio" aria-labelledby="sin-ventas-titulo">
                  <div>
                    <p>ALCANCE DEL PRODUCTO</p>
                    <h2 id="sin-ventas-titulo">Lo que aún no se puede medir</h2>
                    <span>DreemGO propone viajes; actualmente no vende ni reserva.</span>
                  </div>
                  <dl>
                    {["Compradores", "Ingresos", "Ganancias", "Pérdidas", "Ausencias"].map((nombre) => (
                      <div key={nombre}>
                        <dt>{nombre}</dt>
                        <dd>No disponible</dd>
                      </div>
                    ))}
                  </dl>
                </aside>
              </details>
            ) : null}
            <p className="indicadores__fuente">
              {resumen.fuente ?? "El panel muestra acciones registradas; no representa ventas."}
            </p>
          </>
        ) : modo === "real" && !claveActiva ? (
          <p className="indicadores__espera">Ingresa la clave de lectura para ver la actividad registrada.</p>
        ) : !periodoInvalido && !error ? (
          <p className="indicadores__espera">Preparando indicadores…</p>
        ) : null}
      </div>
    </div>
  );
}

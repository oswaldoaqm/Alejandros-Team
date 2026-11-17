// Los cálculos llegan desde la API. Aquí se dibujan y explican, sin volver a estimarlos.
import { useState } from "react";

export type VistaGerencial = "resumen" | "comportamiento" | "estadistica" | "proyeccion" | "indicadores";

export interface Analisis {
  distribucion: { id: string; nombre: string; cantidad: number; porcentaje: number }[];
  embudo: { id: string; nombre: string; sesiones: number; porcentaje: number | null }[];
  pareto: { nombre: string; cantidad: number; porcentaje: number; acumulado: number }[];
  mapa_calor: { dia: number; hora: number; acciones: number }[];
  latencia: {
    n: number;
    media: number | null;
    mediana: number | null;
    p25: number | null;
    p75: number | null;
    p95: number | null;
    desviacion: number | null;
    minimo: number | null;
    maximo: number | null;
    histograma: { desde: number; hasta: number; cantidad: number }[];
  };
  correlacion: {
    variables: { id: string; nombre: string }[];
    pares: { x: string; y: string; r: number | null; n: number }[];
    nota: string;
  };
  dispersion?: { dias: number; presupuesto: number }[];
  proyeccion: {
    estado: "disponible" | "insuficiente";
    metodo: string | null;
    dias_historia: number;
    n_validacion: number;
    mae_validacion: number | null;
    candidatos: { metodo: string; mae: number }[];
    historico: { fecha: string; valor: number }[];
    futuro: { fecha: string; valor: number }[];
    nota: string;
  };
  nota: string;
}

interface PuntoDiario {
  fecha: string;
  sesiones: number;
  busquedas: number;
  detalles: number;
  guardados: number;
}
interface DatoIndicador {
  id: string;
  valor: number | null;
}

const HORAS = Array.from({ length: 24 }, (_, hora) => hora);
const DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const PALETA = ["#a50d2d", "#db8d18", "#31566c", "#806647", "#cf4b63", "#627c76", "#8f78a7"];
const n = (valor: number | null, decimales = 1) =>
  valor === null || !Number.isFinite(valor)
    ? "Sin datos"
    : new Intl.NumberFormat("es-PE", { maximumFractionDigits: decimales }).format(valor);
const fecha = (valor: string) => {
  const partes = valor.split("-");
  return `${partes[2]}/${partes[1]}`;
};
const limite = (valores: number[]) => Math.max(4, Math.ceil(Math.max(0, ...valores) / 4) * 4);

function Tabla({
  titulo,
  columnas,
  filas,
}: {
  titulo: string;
  columnas: string[];
  filas: (string | number)[][];
}) {
  return (
    <details className="indicadores__tabla">
      <summary>{titulo}</summary>
      <div className="indicadores__tabla-scroll">
        <table>
          <thead>
            <tr>
              {columnas.map((c) => (
                <th scope="col" key={c}>
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {filas.map((fila) => (
              <tr key={fila.join("|")}>
                {fila.map((valor, i) => (
                  <td key={columnas[i]}>{valor}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </details>
  );
}

function Ejes({ maximo, ancho = 720, alto = 260 }: { maximo: number; ancho?: number; alto?: number }) {
  return (
    <>
      {[0, 0.25, 0.5, 0.75, 1].map((parte) => {
        const y = 20 + (alto - 56) * (1 - parte);
        return (
          <g key={parte}>
            <line x1={48} x2={ancho - 22} y1={y} y2={y} className="indicadores__guia" />
            <text x={40} y={y + 4} textAnchor="end" className="indicadores__eje">
              {n(maximo * parte, 0)}
            </text>
          </g>
        );
      })}
    </>
  );
}

function Combinado({ serie }: { serie: PuntoDiario[] }) {
  const [mostrarBusquedas, ponerBusquedas] = useState(true);
  if (!serie.length) return <p className="indicadores__vacio">El periodo todavía no tiene actividad.</p>;
  const maximo = limite(serie.flatMap((p) => [p.sesiones, p.busquedas]));
  const paso = 650 / serie.length;
  const x = (i: number) => 48 + paso * (i + 0.5);
  const y = (v: number) => 224 - (v * 204) / maximo;
  const linea = serie.map((p, i) => `${i ? "L" : "M"}${x(i)} ${y(p.busquedas)}`).join(" ");
  return (
    <>
      <div className="gerencia__leyenda">
        <span>
          <i style={{ background: PALETA[0] }} />
          Sesiones
        </span>
        <label>
          <input
            type="checkbox"
            checked={mostrarBusquedas}
            onChange={(e) => ponerBusquedas(e.target.checked)}
          />
          Mostrar búsquedas
        </label>
      </div>
      <svg viewBox="0 0 720 260" role="img" aria-label="Gráfico combinado de sesiones y búsquedas por día">
        <title>Sesiones en barras y búsquedas en línea sobre el mismo eje de cantidad</title>
        <Ejes maximo={maximo} />
        {serie.map((p, i) => (
          <g key={p.fecha}>
            <rect
              x={x(i) - paso * 0.29}
              y={y(p.sesiones)}
              width={paso * 0.58}
              height={224 - y(p.sesiones)}
              rx="3"
              className="gerencia__barra-roja"
            >
              <title>{`${p.fecha}: ${p.sesiones} sesiones, ${p.busquedas} búsquedas`}</title>
            </rect>
            {(i === 0 || i === serie.length - 1 || i % 7 === 0) && (
              <text x={x(i)} y="249" textAnchor="middle" className="indicadores__eje">
                {fecha(p.fecha)}
              </text>
            )}
          </g>
        ))}
        {mostrarBusquedas && <path d={linea} className="gerencia__linea-dorada" />}
      </svg>
      <Tabla
        titulo="Ver datos del gráfico combinado"
        columnas={["Fecha", "Sesiones", "Búsquedas", "Itinerarios", "Guardados"]}
        filas={serie.map((p) => [p.fecha, p.sesiones, p.busquedas, p.detalles, p.guardados])}
      />
    </>
  );
}

function Distribucion({ filas }: { filas: Analisis["distribucion"] }) {
  const [seleccion, ponerSeleccion] = useState<string | null>(null);
  const total = filas.reduce((s, f) => s + f.cantidad, 0);
  let recorrido = 0;
  const elegida = filas.find((f) => f.id === seleccion);
  if (!total) return <p className="indicadores__vacio">Aún no hay sesiones en el periodo.</p>;
  return (
    <div className="gerencia__donut-contenido">
      <svg
        viewBox="0 0 260 260"
        role="img"
        aria-label="Distribución circular de sesiones por estado alcanzado"
      >
        <title>Cada sesión se cuenta una vez según su estado más avanzado</title>
        <circle cx="130" cy="130" r="83" fill="none" stroke="var(--superficie-2)" strokeWidth="33" />
        {filas.map((f, i) => {
          const inicio = recorrido;
          recorrido += f.cantidad / total;
          return (
            <circle
              key={f.id}
              cx="130"
              cy="130"
              r="83"
              fill="none"
              stroke={PALETA[i % PALETA.length]}
              strokeWidth={seleccion === f.id ? 39 : 33}
              pathLength="100"
              strokeDasharray={`${(f.cantidad * 100) / total} ${100 - (f.cantidad * 100) / total}`}
              strokeDashoffset={-inicio * 100}
              transform="rotate(-90 130 130)"
              opacity={seleccion && seleccion !== f.id ? 0.25 : 1}
            >
              <title>{`${f.nombre}: ${f.cantidad} (${n(f.porcentaje)} %)`}</title>
            </circle>
          );
        })}
        <text x="130" y="128" textAnchor="middle" className="gerencia__donut-numero">
          {n(elegida?.cantidad ?? total, 0)}
        </text>
        <text x="130" y="151" textAnchor="middle" className="indicadores__eje">
          {elegida ? "seleccionadas" : "sesiones"}
        </text>
      </svg>
      <ul className="gerencia__leyenda-lista">
        {filas.map((f, i) => (
          <li key={f.id}>
            <button
              type="button"
              aria-pressed={seleccion === f.id}
              onClick={() => ponerSeleccion(seleccion === f.id ? null : f.id)}
            >
              <i style={{ background: PALETA[i % PALETA.length] }} />
              <span>{f.nombre}</span>
              <strong>
                {n(f.cantidad, 0)} <small>{n(f.porcentaje)} %</small>
              </strong>
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

function Embudo({ filas }: { filas: Analisis["embudo"] }) {
  const maximo = Math.max(1, ...filas.map((f) => f.sesiones));
  return (
    <ol className="gerencia__embudo">
      {filas.map((f, i) => (
        <li key={f.id}>
          <span className="gerencia__paso">{i + 1}</span>
          <div>
            <span>{f.nombre}</span>
            <span className="gerencia__pista">
              <span style={{ width: `${(f.sesiones * 100) / maximo}%`, opacity: 1 - i * 0.09 }} />
            </span>
          </div>
          <strong>
            {n(f.sesiones, 0)}
            <small>{n(f.porcentaje)} % del inicio</small>
          </strong>
        </li>
      ))}
    </ol>
  );
}

function Pareto({ filas }: { filas: Analisis["pareto"] }) {
  if (!filas.length)
    return <p className="indicadores__vacio">No hay sesiones sin guardar en este periodo.</p>;
  const maximo = limite(filas.map((f) => f.cantidad));
  const paso = 620 / filas.length;
  const x = (i: number) => 48 + paso * (i + 0.5);
  const y = (v: number) => 224 - (v * 204) / maximo;
  const linea = filas.map((p, i) => `${i ? "L" : "M"}${x(i)} ${224 - p.acumulado * 2.04}`).join(" ");
  return (
    <>
      <div className="gerencia__leyenda">
        <span>
          <i style={{ background: PALETA[0] }} />
          Sesiones · eje izquierdo
        </span>
        <span>
          <i style={{ background: PALETA[1] }} />
          Acumulado · eje derecho
        </span>
      </div>
      <svg viewBox="0 0 720 270" role="img" aria-label="Pareto de estados de sesiones sin guardar">
        <title>Pareto descriptivo de sesiones sin guardar, ordenado por frecuencia</title>
        <Ejes maximo={maximo} ancho={690} />
        <line x1="48" x2="668" y1={224 - 80 * 2.04} y2={224 - 80 * 2.04} className="gerencia__referencia" />
        {filas.map((f, i) => (
          <g key={f.nombre}>
            <rect
              x={x(i) - paso * 0.27}
              y={y(f.cantidad)}
              width={paso * 0.54}
              height={224 - y(f.cantidad)}
              rx="4"
              className="gerencia__barra-roja"
            >
              <title>{`${f.nombre}: ${f.cantidad} sesiones; ${n(f.acumulado)} % acumulado`}</title>
            </rect>
            <text x={x(i)} y="247" textAnchor="middle" className="indicadores__eje">
              {i + 1}
            </text>
          </g>
        ))}
        <path d={linea} className="gerencia__linea-dorada" />
        {[0, 25, 50, 75, 100].map((v) => (
          <text key={v} x="682" y={228 - v * 2.04} className="indicadores__eje">
            {v}%
          </text>
        ))}
      </svg>
      <ol className="gerencia__claves-pareto">
        {filas.map((f) => (
          <li key={f.nombre}>
            {f.nombre} <strong>{n(f.cantidad, 0)}</strong>
          </li>
        ))}
      </ol>
      <p className="gerencia__nota">
        La línea muestra el porcentaje acumulado. El 80 % es una referencia visual, no una regla de
        causalidad.
      </p>
      <Tabla
        titulo="Ver frecuencias y acumulados"
        columnas={["Estado", "Sesiones", "Porcentaje", "Acumulado"]}
        filas={filas.map((f) => [f.nombre, f.cantidad, `${n(f.porcentaje)} %`, `${n(f.acumulado)} %`])}
      />
    </>
  );
}

function MapaCalor({ celdas }: { celdas: Analisis["mapa_calor"] }) {
  const [seleccion, ponerSeleccion] = useState<{ dia: number; hora: number } | null>(null);
  const celdaElegida = seleccion
    ? celdas.find((c) => c.dia === seleccion.dia && c.hora === seleccion.hora)
    : null;
  const maximo = Math.max(1, ...celdas.map((c) => c.acciones));
  return (
    <>
      <p className="gerencia__nota">
        Acciones acumuladas por día de la semana y hora de Perú. Un tono más intenso representa más actividad.
      </p>
      <div className="gerencia__calor-scroll">
        <div className="gerencia__calor">
          <span />
          {HORAS.map((hora) => (
            <span className="gerencia__hora" key={`h${hora}`}>
              {hora % 3 === 0 ? `${hora}h` : ""}
            </span>
          ))}
          {DIAS.flatMap((dia, i) => [
            <span className="gerencia__dia" key={dia}>
              {dia.slice(0, 3)}
            </span>,
            ...HORAS.map((hora) => {
              const celda = celdas.find((c) => c.dia === i && c.hora === hora) ?? {
                dia: i,
                hora,
                acciones: 0,
              };
              return (
                <button
                  key={`${dia}-${hora}`}
                  type="button"
                  aria-label={`${dia}, ${hora}:00, ${celda.acciones} acciones`}
                  aria-pressed={seleccion?.dia === i && seleccion.hora === hora}
                  onClick={() => ponerSeleccion({ dia: i, hora })}
                  style={{
                    background: `color-mix(in srgb, var(--lago) ${(celda.acciones * 85) / maximo + (celda.acciones ? 15 : 0)}%, var(--superficie-2))`,
                  }}
                  title={`${dia} ${hora}:00 · ${celda.acciones} acciones`}
                />
              );
            }),
          ])}
        </div>
      </div>
      <div className="gerencia__calor-leyenda">
        <span>0</span>
        <span aria-hidden="true" />
        <span>{n(maximo, 0)} acciones</span>
      </div>
      <p className="gerencia__seleccion" role="status">
        {seleccion
          ? `${DIAS[seleccion.dia]}, de ${seleccion.hora}:00 a ${seleccion.hora}:59: ${celdaElegida?.acciones ?? 0} acciones en el periodo.`
          : "Selecciona una celda para consultar su cantidad."}
      </p>
    </>
  );
}

function Histograma({ datos }: { datos: Analisis["latencia"] }) {
  const ms = (valor: number | null) => (valor === null ? "Sin datos" : `${n(valor)} ms`);
  const maximo = limite(datos.histograma.map((f) => f.cantidad));
  const paso = 650 / Math.max(1, datos.histograma.length);
  return (
    <>
      <dl className="gerencia__estadisticos">
        {[
          ["Respuestas medidas", n(datos.n, 0)],
          ["Media", ms(datos.media)],
          ["Mediana", ms(datos.mediana)],
          ["Percentil 95", ms(datos.p95)],
          ["Desviación muestral", datos.desviacion === null ? "Sin datos" : `${n(datos.desviacion)} ms`],
          ["Mitad central", datos.p25 === null ? "Sin datos" : `${n(datos.p25)}–${n(datos.p75)} ms`],
        ].map(([etiqueta, valor]) => (
          <div key={etiqueta}>
            <dt>{etiqueta}</dt>
            <dd>{valor}</dd>
          </div>
        ))}
      </dl>
      {datos.n ? (
        <svg
          viewBox="0 0 720 280"
          role="img"
          aria-label="Histograma de duración de las respuestas en milisegundos"
        >
          <title>Distribución del tiempo de respuesta</title>
          <Ejes maximo={maximo} />
          {datos.histograma.map((f, i) => (
            <g key={`${f.desde}-${f.hasta}`}>
              <rect
                x={49 + i * paso}
                y={224 - (f.cantidad * 204) / maximo}
                width={Math.max(1, paso - 3)}
                height={(f.cantidad * 204) / maximo}
                className="gerencia__barra-roja"
              >
                <title>{`${f.desde} a ${f.hasta} ms: ${f.cantidad} respuestas`}</title>
              </rect>
              <text x={49 + i * paso + paso / 2} y="245" textAnchor="middle" className="indicadores__eje">
                {n(f.desde, 0)}
              </text>
            </g>
          ))}
          <text x="375" y="272" textAnchor="middle" className="indicadores__eje">
            Límite inferior del intervalo · milisegundos
          </text>
        </svg>
      ) : (
        <p className="indicadores__vacio">Todavía no hay respuestas con duración registrada.</p>
      )}
      <Tabla
        titulo="Ver intervalos del histograma"
        columnas={["Desde (ms)", "Hasta (ms)", "Respuestas"]}
        filas={datos.histograma.map((f) => [f.desde, f.hasta, f.cantidad])}
      />
    </>
  );
}

function Correlacion({ datos }: { datos: Analisis["correlacion"] }) {
  const [seleccion, ponerSeleccion] = useState<{ x: string; y: string } | null>(null);
  const par = seleccion ? datos.pares.find((p) => p.x === seleccion.x && p.y === seleccion.y) : null;
  const nombre = (id: string) => datos.variables.find((v) => v.id === id)?.nombre ?? id;
  return (
    <>
      <div className="gerencia__matriz-scroll">
        <table className="gerencia__matriz">
          <thead>
            <tr>
              <th scope="col">Variable</th>
              {datos.variables.map((v) => (
                <th key={v.id} scope="col">
                  {v.nombre}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {datos.variables.map((v) => (
              <tr key={v.id}>
                <th scope="row">{v.nombre}</th>
                {datos.variables.map((u) => {
                  const celda = datos.pares.find((p) => p.x === v.id && p.y === u.id);
                  const r = celda?.r ?? null;
                  return (
                    <td key={u.id}>
                      <button
                        type="button"
                        onClick={() => ponerSeleccion({ x: v.id, y: u.id })}
                        aria-label={`${v.nombre} y ${u.nombre}: ${r === null ? "sin datos suficientes" : `r ${r}`}, n ${celda?.n ?? 0}`}
                        style={{
                          background:
                            r === null
                              ? "var(--superficie-2)"
                              : `color-mix(in srgb, ${r < 0 ? "#31566c" : "var(--lago)"} ${Math.abs(r) * 75 + 15}%, var(--superficie))`,
                          color: r !== null && Math.abs(r) > 0.45 ? "white" : "var(--tinta)",
                        }}
                      >
                        <strong>{r === null ? "—" : n(r, 2)}</strong>
                        <small>n = {celda?.n ?? 0}</small>
                      </button>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="gerencia__leyenda">
        <span>
          <i style={{ background: "#31566c" }} />
          Relación negativa
        </span>
        <span>
          <i style={{ background: "var(--superficie-2)" }} />
          Cerca de cero
        </span>
        <span>
          <i style={{ background: PALETA[0] }} />
          Relación positiva
        </span>
      </div>
      <p className="gerencia__seleccion" role="status">
        {par
          ? `${nombre(par.x)} y ${nombre(par.y)}: ${par.r === null ? "no se puede estimar una correlación con estos datos" : `r = ${n(par.r, 2)}`}; ${par.n} pares completos.`
          : "Selecciona una celda para revisar el tamaño de muestra y el coeficiente."}
      </p>
      <p className="gerencia__nota">{datos.nota} Una correlación no demuestra causa y efecto.</p>
    </>
  );
}

function Dispersion({ puntos }: { puntos: NonNullable<Analisis["dispersion"]> }) {
  if (!puntos.length)
    return (
      <p className="indicadores__vacio">Faltan sesiones con días y presupuesto para mostrar la dispersión.</p>
    );
  const coordenadas = new Map<string, { dias: number; presupuesto: number; cantidad: number }>();
  for (const punto of puntos) {
    const clave = `${punto.dias}:${punto.presupuesto}`;
    const grupo = coordenadas.get(clave);
    if (grupo) grupo.cantidad += 1;
    else coordenadas.set(clave, { ...punto, cantidad: 1 });
  }
  const maxX = Math.max(1, ...puntos.map((p) => p.dias));
  const maxY = limite(puntos.map((p) => p.presupuesto));
  return (
    <>
      <svg
        viewBox="0 0 720 285"
        role="img"
        aria-label="Dispersión de días solicitados y presupuesto por sesión"
      >
        <title>
          Días solicitados frente a presupuesto; cada posición agrupa sesiones con los mismos días y
          presupuesto
        </title>
        <Ejes maximo={maxY} />
        {[...coordenadas.values()].map((p) => (
          <circle
            key={`${p.dias}-${p.presupuesto}`}
            cx={48 + (p.dias / maxX) * 650}
            cy={224 - (p.presupuesto / maxY) * 204}
            r="5"
            fill="var(--lago)"
            opacity={Math.min(0.85, 0.25 + p.cantidad * 0.08)}
          >
            <title>{`${p.dias} días · S/ ${n(p.presupuesto, 0)} · ${p.cantidad} sesiones`}</title>
          </circle>
        ))}
        {[0, 0.25, 0.5, 0.75, 1].map((v) => (
          <text key={v} x={48 + 650 * v} y="247" textAnchor="middle" className="indicadores__eje">
            {n(maxX * v, 0)}
          </text>
        ))}
        <text x="375" y="275" textAnchor="middle" className="indicadores__eje">
          Días solicitados · presupuesto en S/ en el eje vertical
        </text>
      </svg>
      <Tabla
        titulo="Ver valores de dispersión"
        columnas={["Días", "Presupuesto (S/)", "Sesiones en esta posición"]}
        filas={[...coordenadas.values()].map((p) => [p.dias, p.presupuesto, p.cantidad])}
      />
      <p className="gerencia__nota">
        {puntos.length} sesiones con ambos datos. Los puntos coincidentes se superponen; no son ingresos del
        negocio.
      </p>
    </>
  );
}

function Proyeccion({ datos, simulacion }: { datos: Analisis["proyeccion"]; simulacion: boolean }) {
  const puntos = [...datos.historico, ...datos.futuro];
  const maximo = limite(puntos.map((p) => p.valor));
  const x = (i: number) => 48 + (i * 650) / Math.max(1, puntos.length - 1);
  const y = (valor: number) => 224 - (valor * 204) / maximo;
  const linea = (lista: { valor: number }[], inicio: number) =>
    lista.map((p, i) => `${i ? "L" : "M"}${x(i + inicio)} ${y(p.valor)}`).join(" ");
  return (
    <section className="indicadores__panel gerencia__ancho" aria-label="Proyección de sesiones">
      <div className="indicadores__panel-cabeza">
        <div>
          <p>PRÓXIMOS SIETE DÍAS</p>
          <h2>Proyección de sesiones</h2>
        </div>
        <span className="gerencia__insignia">
          {simulacion ? "EJERCICIO CON DATOS SIMULADOS" : "ESTIMACIÓN EXPLORATORIA"}
        </span>
      </div>
      <p className="gerencia__bajada">
        Una referencia para practicar la planificación de actividad. No es una promesa de visitantes ni de
        ventas.
      </p>
      {datos.estado === "insuficiente" ? (
        <p className="gerencia__seleccion">
          Todavía no hay al menos 21 días completos para comparar los métodos. Hay {datos.dias_historia} días
          disponibles en este periodo.
        </p>
      ) : (
        <>
          <dl className="gerencia__estadisticos">
            <div>
              <dt>Método seleccionado</dt>
              <dd>{datos.metodo}</dd>
            </div>
            <div>
              <dt>Días de historia</dt>
              <dd>{datos.dias_historia}</dd>
            </div>
            <div>
              <dt>Validación</dt>
              <dd>{datos.n_validacion} días</dd>
            </div>
            <div>
              <dt>Error absoluto medio</dt>
              <dd>{n(datos.mae_validacion)} sesiones/día</dd>
            </div>
          </dl>
          <div className="gerencia__leyenda">
            <span>
              <i style={{ background: PALETA[0] }} />
              Historia
            </span>
            <span>
              <i style={{ background: PALETA[1] }} />
              Proyección
            </span>
          </div>
          <svg
            viewBox="0 0 720 260"
            role="img"
            aria-label="Historia y proyección de sesiones para los próximos siete días"
          >
            <title>Historia y proyección exploratoria de sesiones</title>
            <Ejes maximo={maximo} />
            <rect
              x={x(Math.max(0, datos.historico.length - 1))}
              y="20"
              width={698 - x(Math.max(0, datos.historico.length - 1))}
              height="204"
              fill="var(--aviso-fondo)"
              opacity=".7"
            />
            <path d={linea(datos.historico, 0)} className="indicadores__linea" />
            <path
              d={linea(
                [...datos.historico.slice(-1), ...datos.futuro],
                Math.max(0, datos.historico.length - 1),
              )}
              className="gerencia__linea-dorada gerencia__proyeccion-linea"
            />
            {puntos.map(
              (p, i) =>
                (i === 0 || i === datos.historico.length - 1 || i === puntos.length - 1) && (
                  <text key={p.fecha} x={x(i)} y="249" textAnchor="middle" className="indicadores__eje">
                    {fecha(p.fecha)}
                  </text>
                ),
            )}
          </svg>
          <Tabla
            titulo="Ver la proyección día por día"
            columnas={["Día", "Sesiones estimadas"]}
            filas={datos.futuro.map((p) => [p.fecha, n(p.valor)])}
          />
          <Tabla
            titulo="Ver comparación de métodos"
            columnas={["Método", "Error absoluto medio en validación"]}
            filas={datos.candidatos.map((c) => [c.metodo, `${n(c.mae)} sesiones/día`])}
          />
        </>
      )}
      <p className="gerencia__nota">{datos.nota}</p>
    </section>
  );
}

function Hipotesis({ indicadores }: { indicadores: DatoIndicador[] }) {
  const valor = (id: string) => n(indicadores.find((i) => i.id === id)?.valor ?? null);
  const ramas = [
    {
      nombre: "Interacción",
      dato: `Formularios sin búsqueda: ${valor("tasa_abandono_formulario")}${valor("tasa_abandono_formulario") === "Sin datos" ? "" : " %"}`,
      pregunta: "¿La persona entendió qué completar?",
      prueba: "Observar a un compañero completar el formulario, sin guiarlo.",
    },
    {
      nombre: "Respuesta",
      dato: `Búsquedas sin viajes: ${valor("busquedas_sin_resultados")}`,
      pregunta: "¿Las preferencias dejan pocas alternativas?",
      prueba: "Repetir una consulta sin resultados y cambiar una sola preferencia.",
    },
    {
      nombre: "Disponibilidad",
      dato: `Errores de consulta: ${valor("errores_consulta")}`,
      pregunta: "¿Se pudo contactar con el servidor?",
      prueba: "Revisar la respuesta de la API y la conexión en ese caso.",
    },
    {
      nombre: "Tiempo",
      dato: `Respuesta p95: ${valor("latencia_p95_ms")}${valor("latencia_p95_ms") === "Sin datos" ? "" : " ms"}`,
      pregunta: "¿La espera dificulta continuar?",
      prueba: "Observar la espera y preguntar al participante antes de atribuirle un motivo.",
    },
  ];
  return (
    <section className="indicadores__panel gerencia__ancho" aria-label="Causa y efecto como hipótesis">
      <div className="indicadores__panel-cabeza">
        <div>
          <p>DIAGRAMA CAUSA EFECTO</p>
          <h2>Hipótesis para investigar</h2>
        </div>
        <span className="gerencia__insignia">NO SON CAUSAS DEMOSTRADAS</span>
      </div>
      <p className="gerencia__bajada">
        Punto de revisión: sesiones que no llegaron a guardar un viaje. Estos datos abren preguntas; no
        explican por sí solos el motivo.
      </p>
      <div className="gerencia__espina">
        <div className="gerencia__ramas">
          {ramas.map((r) => (
            <article key={r.nombre}>
              <h3>{r.nombre}</h3>
              <strong>{r.dato}</strong>
              <p>{r.pregunta}</p>
              <small>{r.prueba}</small>
            </article>
          ))}
        </div>
        <div className="gerencia__efecto">
          Sesiones
          <br />
          sin guardar
        </div>
      </div>
      <p className="gerencia__nota">
        Un diagrama de Ishikawa organiza posibles explicaciones para comprobar. Las sesiones pueden seguir
        activas o preferir no guardar: eso no implica insatisfacción.
      </p>
    </section>
  );
}

export function AnalisisGerencial({
  datos,
  vista,
  serie,
  indicadores,
  simulacion,
}: {
  datos: Analisis;
  vista: VistaGerencial;
  serie: PuntoDiario[];
  indicadores: DatoIndicador[];
  simulacion: boolean;
}) {
  return (
    <div className="gerencia__graficos">
      {vista === "resumen" && (
        <>
          <section className="indicadores__panel gerencia__ancho" aria-label="Evolución combinada">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>ALCANCE Y PARTICIPACIÓN</p>
                <h2>Cómo evoluciona la actividad</h2>
              </div>
            </div>
            <Combinado serie={serie} />
          </section>
          <section className="indicadores__panel gerencia__ancho" aria-label="Distribución de sesiones">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>ESTADOS DEL RECORRIDO</p>
                <h2>Hasta dónde llegaron las sesiones</h2>
              </div>
            </div>
            <Distribucion filas={datos.distribucion} />
            <p className="gerencia__nota">
              Cada sesión se asigna una sola vez al estado más avanzado observado dentro del periodo. No
              representa una compra ni confirma abandono.
            </p>
          </section>
        </>
      )}
      {vista === "comportamiento" && (
        <>
          <section className="indicadores__panel" aria-label="Embudo de uso">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>RECORRIDO DEL PRODUCTO</p>
                <h2>De la visita al guardado</h2>
              </div>
            </div>
            <Embudo filas={datos.embudo} />
            <p className="gerencia__nota">
              Cada etapa cuenta sesiones presentes en todas las etapas anteriores dentro del periodo. Es
              continuidad observada, no una tasa de ventas.
            </p>
          </section>
          <section className="indicadores__panel" aria-label="Pareto descriptivo">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>PRIORIDADES DE REVISIÓN</p>
                <h2>Dónde se concentran las sesiones sin guardar</h2>
              </div>
            </div>
            <Pareto filas={datos.pareto} />
          </section>
          <section className="indicadores__panel gerencia__ancho" aria-label="Mapa de calor de actividad">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>RITMO SEMANAL</p>
                <h2>Cuándo se usa la plataforma</h2>
              </div>
            </div>
            <MapaCalor celdas={datos.mapa_calor} />
          </section>
          <Hipotesis indicadores={indicadores} />
        </>
      )}
      {vista === "estadistica" && (
        <>
          <section className="indicadores__panel gerencia__ancho" aria-label="Estadística de tiempos">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>CALIDAD DE RESPUESTA</p>
                <h2>Cómo se distribuyen los tiempos</h2>
              </div>
            </div>
            <Histograma datos={datos.latencia} />
          </section>
          <section className="indicadores__panel gerencia__ancho" aria-label="Matriz de correlación">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>RELACIONES ENTRE VARIABLES</p>
                <h2>Matriz de correlación de Pearson</h2>
              </div>
            </div>
            <Correlacion datos={datos.correlacion} />
          </section>
          <section className="indicadores__panel gerencia__ancho" aria-label="Dispersión de preferencias">
            <div className="indicadores__panel-cabeza">
              <div>
                <p>PREFERENCIAS DEL VIAJE</p>
                <h2>Días y presupuesto solicitado</h2>
              </div>
            </div>
            <Dispersion puntos={datos.dispersion ?? []} />
          </section>
        </>
      )}
      {vista === "proyeccion" && <Proyeccion datos={datos.proyeccion} simulacion={simulacion} />}
    </div>
  );
}

// Pantalla 2: hasta tres rutas para la consulta de la URL, comparables de un vistazo, y el
// detalle de la que se elige. La consulta se ve como chips: quitar uno arma otra URL.

import { useEffect, useState } from "react";
import { borrarViaje, estaGuardado, guardarViaje } from "../almacen";
import type { Respuesta } from "../api/tipos";
import { aParametros, type Consulta, clave, type Nombres, nombreDeOrigen, piezas, titulo } from "../consulta";
import { useApp } from "../estado/contexto";
import { usePedido } from "../estado/pedido";
import { useTitulo } from "../estado/titulo";
import { fecha, mes } from "../formato";
import { llevarA } from "../movimiento";
import { DetalleRuta } from "../piezas/DetalleRuta";
import { Enlace } from "../piezas/Enlace";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { Icono } from "../piezas/Icono";
import { TarjetaRuta } from "../piezas/TarjetaRuta";
import { enlaces } from "../ruta";
import { aplicarSugerencia, textoDeSugerencia } from "../textos";
import { cambioDeVersion } from "../version";

interface Props {
  consulta: Consulta;
  /** La versión de datos que traía el enlace, si traía alguna. */
  version: string | null;
  /** Cuál de las rutas está abierta: 1, 2 o 3. */
  elegida: number;
}

/** La consulta tal como la entendió el motor: de ahí se pintan los chips (docs/CONTRATO.md §5). */
function comoLaEntendio(c: Respuesta["consulta"]): Consulta {
  return {
    origen: c.origen,
    mes: c.mes ?? null,
    fecha_inicio: c.fecha_inicio ?? null,
    dias: c.dias,
    intereses: [...(c.intereses ?? [])],
    presupuesto: c.presupuesto ?? null,
    altitud_max: c.altitud_max ?? null,
    sorpresa: c.sorpresa,
  };
}

const CUANTAS = ["Ninguna ruta", "Una ruta", "Dos rutas", "Tres rutas"];

function resumen(rutas: number, c: Consulta, nombres: Nombres): string {
  const cuando = c.fecha_inicio ? `saliendo el ${fecha(c.fecha_inicio, false)}` : `para ${mes(c.mes)}`;
  const orden = rutas > 1 ? ", de la más a la menos recomendada" : "";
  const sorpresa = c.sorpresa ? " Solo fuera del circuito de Lima y Cusco." : "";
  const cuantas = CUANTAS[rutas] ?? `${rutas} rutas`;
  return `${cuantas} desde ${nombreDeOrigen(c.origen, nombres)} ${cuando}${orden}.${sorpresa}`;
}

function Chips({ consulta, version }: { consulta: Consulta; version: string | null }) {
  const { nombres } = useApp();
  return (
    <ul className="chips chips--consulta" aria-label="Tu consulta">
      {piezas(consulta, nombres).map((pieza) => (
        <li key={`${pieza.campo}-${pieza.valor ?? ""}`} className="chip">
          <span>{pieza.texto}</span>
          {pieza.sin ? (
            <Enlace
              href={enlaces.resultados(pieza.sin, version)}
              className="chip__quitar"
              aria-label={`Quitar: ${pieza.texto}`}
              conservarPosicion
            >
              <Icono nombre="cerrar" tamano={14} />
            </Enlace>
          ) : null}
        </li>
      ))}
      <li>
        <Enlace href={enlaces.editar(consulta, version)} className="chip chip--accion">
          <Icono nombre="editar" tamano={15} />
          Editar
        </Enlace>
      </li>
    </ul>
  );
}

interface Mensaje {
  texto: string;
  /** El enlace a la vista, cuando el navegador no deja copiarlo. */
  enlace?: string;
}

function Acciones({ consulta, version, elegida }: { consulta: Consulta; version: string; elegida: number }) {
  const { nombres } = useApp();
  const llave = clave(consulta);
  const [guardado, ponerGuardado] = useState(() => estaGuardado(consulta));
  const [mensaje, ponerMensaje] = useState<Mensaje | null>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: la llave resume la consulta
  useEffect(() => {
    ponerGuardado(estaGuardado(consulta));
    ponerMensaje(null);
  }, [llave]);

  const alternarGuardado = () => {
    if (guardado) {
      borrarViaje(consulta);
      ponerGuardado(false);
      ponerMensaje({ texto: "Lo quitamos de Mis viajes." });
      return;
    }
    const listo = guardarViaje({
      consulta,
      version,
      titulo: titulo(consulta, nombres),
      guardado: new Date().toISOString(),
    });
    ponerGuardado(listo);
    ponerMensaje({
      texto: listo
        ? "Guardado en Mis viajes, en este navegador."
        : "Este navegador no deja guardar. Usa «Compartir» y guarda el enlace.",
    });
  };

  const compartir = async () => {
    const enlace = new URL(enlaces.resultados(consulta, version, elegida), window.location.href).href;
    const nombre = titulo(consulta, nombres);
    const conElDedo =
      typeof window.matchMedia === "function" && window.matchMedia("(pointer: coarse)").matches;
    if (conElDedo && typeof navigator.share === "function") {
      try {
        await navigator.share({
          title: `DreemGO · ${nombre}`,
          text: `Mira este viaje: ${nombre}`,
          url: enlace,
        });
        return;
      } catch (causa) {
        if (causa instanceof DOMException && causa.name === "AbortError") return; // cerró el menú
      }
    }
    try {
      await navigator.clipboard.writeText(enlace);
      ponerMensaje({ texto: "Enlace copiado. Quien lo abra ve este mismo viaje." });
    } catch {
      ponerMensaje({ texto: "Copia este enlace:", enlace });
    }
  };

  const imprimir = () => {
    // Lo plegado no se imprime: se abre todo antes.
    for (const plegable of document.querySelectorAll("details")) plegable.open = true;
    window.print();
  };

  return (
    <div className="acciones">
      <div className="acciones__botones">
        <button
          type="button"
          className="boton boton--secundario"
          aria-pressed={guardado}
          onClick={alternarGuardado}
        >
          <Icono nombre={guardado ? "bien" : "guardar"} />
          {guardado ? "Guardado" : "Guardar"}
        </button>
        <button type="button" className="boton boton--secundario" onClick={compartir}>
          <Icono nombre="compartir" />
          Compartir
        </button>
        <button
          type="button"
          className="boton boton--secundario"
          title="Imprimir o guardar como PDF"
          onClick={imprimir}
        >
          <Icono nombre="imprimir" />
          Imprimir
        </button>
      </div>
      <p className="acciones__mensaje" role="status">
        {mensaje ? (
          <>
            {mensaje.texto}
            {mensaje.enlace ? (
              <input
                type="text"
                readOnly
                value={mensaje.enlace}
                aria-label="Enlace del viaje"
                onFocus={(e) => e.currentTarget.select()}
              />
            ) : null}
          </>
        ) : null}
      </p>
    </div>
  );
}

function SinRutas({ respuesta, consulta }: { respuesta: Respuesta; consulta: Consulta }) {
  const { nombres } = useApp();
  const sin = respuesta.sin_resultado;
  const sugerencias = (sin?.sugerencias ?? []).flatMap((s) => {
    const nueva = aplicarSugerencia(consulta, s);
    return nueva ? [{ s, nueva }] : [];
  });
  return (
    <div className="aviso aviso--advertencia">
      <Icono nombre="aviso" />
      <div>
        <p className="aviso__titulo">No hay rutas para esta consulta</p>
        <p>{sin?.motivo ?? "El motor no encontró ningún polo que cumpla lo que pediste."}</p>
        {sugerencias.length > 0 ? (
          <>
            <p>Con un cambio sí aparecen:</p>
            <ul className="sugerencias">
              {sugerencias.map(({ s, nueva }) => (
                <li key={`${s.campo}-${String(s.valor)}`}>
                  <Enlace
                    href={enlaces.resultados(nueva, respuesta.version_datos)}
                    className="boton boton--secundario"
                  >
                    {textoDeSugerencia(s, nombres)}
                  </Enlace>
                  <span className="sugerencias__efecto">{s.efecto}</span>
                </li>
              ))}
            </ul>
          </>
        ) : null}
        <div className="aviso__acciones">
          <Enlace
            href={enlaces.editar(consulta, respuesta.version_datos)}
            className="boton boton--secundario"
          >
            Cambiar la consulta
          </Enlace>
        </div>
      </div>
    </div>
  );
}

export function Resultados({ consulta, version, elegida }: Props) {
  const { navegar, nombres, opciones } = useApp();
  const parametros = aParametros(consulta).toString();
  const pedido = usePedido<Respuesta>("/v1/viajes", parametros);
  const respuesta = pedido.datos;
  const alDia = respuesta !== null && !pedido.cargando && pedido.de === `/v1/viajes?${parametros}`;
  const vigente = respuesta?.version_datos ?? version;

  useTitulo(titulo(consulta, nombres));

  // El enlace completo lleva la versión de datos: si la barra de direcciones no la trae, se le
  // pone. Y si solo cambiaron los eventos publicados, se pone la vigente sin avisar: las rutas
  // son las mismas (src/version.ts).
  const versionRecibida = alDia ? respuesta.version_datos : null;
  const cambio = versionRecibida === null ? "ninguno" : cambioDeVersion(version, versionRecibida);
  useEffect(() => {
    if (versionRecibida !== null && (version === null || cambio === "eventos")) {
      navegar(enlaces.resultados(consulta, versionRecibida, elegida), {
        reemplazar: true,
        conservarPosicion: true,
      });
    }
  }, [versionRecibida, version, cambio, consulta, elegida, navegar]);

  const rutas = respuesta?.rutas ?? [];
  const indice = Math.min(Math.max(elegida, 1), Math.max(rutas.length, 1)) - 1;
  const abierta = rutas[indice];
  const deOtraVersion = alDia && cambio === "datos";

  const elegir = () => {
    // En celular el detalle queda debajo de las tarjetas: se lleva la vista hasta él.
    requestAnimationFrame(() => {
      const detalle = document.getElementById("detalle");
      if (!detalle || detalle.getBoundingClientRect().top < window.innerHeight * 0.6) return;
      llevarA(detalle, "start");
    });
  };

  return (
    <section className="pagina">
      <p className="sobretitulo">Paso 2 de 2 · Elegir la ruta</p>
      <h1 tabIndex={-1}>Tus rutas</h1>
      <Chips consulta={alDia ? comoLaEntendio(respuesta.consulta) : consulta} version={vigente} />

      <p className="bajada" role="status">
        {pedido.cargando
          ? "Armando tus rutas…"
          : alDia
            ? resumen(rutas.length, consulta, nombres)
            : "No pudimos armar tus rutas."}
      </p>

      {pedido.error ? (
        <ErrorVista
          error={pedido.error}
          reintentar={() => {
            // Si las opciones tampoco llegaron, se piden otra vez: de ahí salen los nombres.
            if (opciones.error) opciones.reintentar();
            pedido.reintentar();
          }}
        >
          <Enlace href={enlaces.editar(consulta, version)} className="boton boton--secundario">
            Revisar la consulta
          </Enlace>
        </ErrorVista>
      ) : null}

      {respuesta === null && pedido.cargando ? (
        <Cargando texto="Buscando entre los polos del país. La primera consulta puede tardar unos segundos." />
      ) : null}

      {deOtraVersion ? (
        <div className="aviso aviso--info">
          <Icono nombre="info" />
          <div>
            <p>
              Este enlace se armó con los datos {version}. Lo que ves está calculado con los datos{" "}
              {respuesta.version_datos}, que son los vigentes: las rutas pueden haber cambiado.
            </p>
            <div className="aviso__acciones">
              <Enlace
                href={enlaces.resultados(consulta, respuesta.version_datos, elegida)}
                className="boton boton--secundario"
                reemplazar
                conservarPosicion
              >
                Entendido
              </Enlace>
            </div>
          </div>
        </div>
      ) : null}

      {respuesta !== null && rutas.length === 0 && alDia ? (
        <SinRutas respuesta={respuesta} consulta={consulta} />
      ) : null}

      {respuesta !== null && abierta ? (
        <>
          {alDia ? (
            <Acciones consulta={consulta} version={respuesta.version_datos} elegida={indice + 1} />
          ) : null}
          <div
            className={`resultado${pedido.cargando ? " resultado--espera" : ""}`}
            aria-busy={pedido.cargando}
          >
            <ol className="tarjetas" aria-label="Rutas propuestas">
              {rutas.map((ruta, i) => (
                <li key={ruta.polo.id}>
                  <TarjetaRuta
                    ruta={ruta}
                    indice={i}
                    elegida={i === indice}
                    enlace={enlaces.resultados(consulta, vigente, i + 1)}
                    dias={respuesta.consulta.dias}
                    alElegir={elegir}
                  />
                </li>
              ))}
            </ol>
            <DetalleRuta
              key={`${respuesta.version_datos}-${abierta.polo.id}`}
              ruta={abierta}
              indice={indice}
              consulta={comoLaEntendio(respuesta.consulta)}
              version={vigente}
            />
          </div>
          <footer className="fuentes">
            <h2 className="rotulo">De dónde sale esto</h2>
            <ul className="lista-simple">
              {respuesta.atribucion.map((linea) => (
                <li key={linea}>{linea}</li>
              ))}
            </ul>
            <p>
              Datos {respuesta.version_datos} · contrato {respuesta.version_contrato}. Las horas y los costos
              son estimaciones: DreemGO no vende ni reserva.{" "}
              <Enlace href={enlaces.acerca()}>Cómo se calcula</Enlace>
            </p>
          </footer>
        </>
      ) : null}
    </section>
  );
}

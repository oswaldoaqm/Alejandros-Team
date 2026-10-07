// Pantalla 2: los tres viajes de la consulta de la URL, para elegir de un vistazo. Al tocar uno
// se abre su plan (`#/ruta/N`), en su propia pantalla; «Volver» regresa a los tres.

import { useEffect, useState } from "react";
import { borrarViaje, estaGuardado, guardarViaje } from "../almacen";
import type { Respuesta } from "../api/tipos";
import { aParametros, type Consulta, clave, detalles, titulo } from "../consulta";
import { useApp } from "../estado/contexto";
import { useFotos } from "../estado/fotos";
import { usePedido } from "../estado/pedido";
import { useTitulo } from "../estado/titulo";
import { fotoDelViaje } from "../fotos";
import { DetalleRuta } from "../piezas/DetalleRuta";
import { Enlace } from "../piezas/Enlace";
import { Cargando, ErrorVista } from "../piezas/Estados";
import { Icono } from "../piezas/Icono";
import { TarjetaRuta } from "../piezas/TarjetaRuta";
import { enlaces } from "../ruta";
import { aplicarSugerencia, nombreDelViaje, textoDeSugerencia } from "../textos";
import { cambioDeVersion } from "../version";

interface Props {
  consulta: Consulta;
  /** La versión de datos que traía el enlace, si traía alguna. */
  version: string | null;
  /** El viaje abierto: 1, 2 o 3; null para ver los tres. */
  elegida: number | null;
}

/** La consulta tal como la entendió el motor (docs/CONTRATO.md §5). */
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

const CUANTOS = ["Ningún viaje", "Un viaje para ti", "Dos viajes para ti", "Tres viajes para ti"];

interface Mensaje {
  texto: string;
  /** El enlace del viaje, cuando el navegador no deja copiarlo. */
  enlace?: string;
}

/** Guardar y compartir: dos círculos sobre la portada del viaje, y un aviso abajo. */
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

  useEffect(() => {
    if (!mensaje || mensaje.enlace) return;
    const reloj = window.setTimeout(() => ponerMensaje(null), 4000);
    return () => window.clearTimeout(reloj);
  }, [mensaje]);

  const alternarGuardado = () => {
    if (guardado) {
      borrarViaje(consulta);
      ponerGuardado(false);
      ponerMensaje({ texto: "Lo quitamos de Guardados." });
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
      texto: listo ? "Guardado en este navegador." : "Este navegador no deja guardar. Comparte el enlace.",
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

  // En celular son círculos con su ícono; en pantalla ancha, botones con su nombre. El nombre
  // está siempre: es lo que lee un lector de pantalla.
  return (
    <>
      <div className="portada__acciones">
        <button
          type="button"
          className="boton boton--flotante"
          aria-pressed={guardado}
          onClick={alternarGuardado}
        >
          <Icono nombre={guardado ? "bien" : "guardar"} tamano={20} />
          <span className="boton__texto">{guardado ? "Guardado" : "Guardar"}</span>
        </button>
        <button type="button" className="boton boton--flotante" onClick={compartir}>
          <Icono nombre="compartir" tamano={20} />
          <span className="boton__texto">Compartir</span>
        </button>
        <button type="button" className="boton boton--flotante" onClick={imprimir}>
          <Icono nombre="imprimir" tamano={20} />
          <span className="boton__texto">Imprimir o guardar en PDF</span>
        </button>
      </div>
      <p className="aviso-flotante" role="status">
        {mensaje ? (
          <span>
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
          </span>
        ) : null}
      </p>
    </>
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
    <div className="vacio-viajes">
      <h2>No encontramos un viaje así</h2>
      <p>{sin?.motivo ?? "Ninguna zona cumple todo lo que pediste."}</p>
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
      <Enlace href={enlaces.editar(consulta, respuesta.version_datos)} className="boton boton--primario">
        Cambiar el viaje
      </Enlace>
    </div>
  );
}

export function Resultados({ consulta, version, elegida }: Props) {
  const { navegar, nombres, opciones } = useApp();
  const parametros = aParametros(consulta).toString();
  const pedido = usePedido<Respuesta>("/v1/viajes", parametros);
  const fotos = useFotos();
  const respuesta = pedido.datos;
  const alDia = respuesta !== null && !pedido.cargando && pedido.de === `/v1/viajes?${parametros}`;
  const vigente = respuesta?.version_datos ?? version;

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
  const deOtraVersion = alDia && cambio === "datos";
  const entendida = alDia ? comoLaEntendio(respuesta.consulta) : consulta;

  const avisoDeVersion = deOtraVersion ? (
    <div className="aviso aviso--info">
      <Icono nombre="info" />
      <div>
        <p>
          Este enlace se armó con los datos {version}. Lo que ves sale de los datos {respuesta.version_datos},
          que son los vigentes: el viaje puede haber cambiado.
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
  ) : null;

  // Un viaje abierto: su plan completo, en su propia pantalla.
  const abierta = elegida !== null ? rutas[Math.min(Math.max(elegida, 1), rutas.length) - 1] : undefined;
  useTitulo(abierta ? nombreDelViaje(abierta.polo.nombre).titulo : titulo(consulta, nombres));
  if (respuesta !== null && abierta && elegida !== null) {
    const indice = rutas.indexOf(abierta);
    return (
      <section className="viaje" aria-busy={pedido.cargando}>
        <DetalleRuta
          key={`${respuesta.version_datos}-${abierta.polo.id}`}
          ruta={abierta}
          fotos={fotos}
          consulta={entendida}
          version={vigente}
          volver={enlaces.resultados(consulta, vigente)}
          aviso={avisoDeVersion}
          acciones={
            alDia ? (
              <Acciones consulta={consulta} version={respuesta.version_datos} elegida={indice + 1} />
            ) : null
          }
          atribucion={respuesta.atribucion}
          versiones={`Datos ${respuesta.version_datos}, contrato ${respuesta.version_contrato}`}
        />
      </section>
    );
  }

  const demas = detalles(entendida, nombres);
  // Si ninguno pasa por Lima ni por Cusco, lo dice una frase arriba y no la etiqueta de cada tarjeta.
  const todosPocoTuristicos = rutas.length > 1 && rutas.every((r) => r.polo.fuera_del_circuito);

  return (
    <section className="pagina resultados">
      <div className="resultados__consulta">
        <div>
          <p className="resultados__frase">{titulo(entendida, nombres)}</p>
          {demas ? <p className="resultados__demas">{demas}</p> : null}
        </div>
        <Enlace href={enlaces.editar(consulta, vigente)} className="boton boton--secundario">
          <Icono nombre="editar" tamano={16} />
          Cambiar
        </Enlace>
      </div>

      <h1 tabIndex={-1} className="resultados__titulo">
        {pedido.cargando && respuesta === null
          ? "Armando tus viajes"
          : alDia
            ? (CUANTOS[rutas.length] ?? `${rutas.length} viajes para ti`)
            : "Tus viajes"}
      </h1>
      <p className="resultados__estado" role="status">
        {pedido.cargando
          ? "Estamos revisando las zonas del país. La primera vez puede tardar unos segundos."
          : alDia && rutas.length > 1
            ? `Del que más te conviene al que menos.${todosPocoTuristicos ? ` ${rutas.length === 2 ? "Los dos" : "Los tres"} están lejos del circuito de Lima y Cusco.` : ""}`
            : ""}
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
            Revisar el viaje
          </Enlace>
        </ErrorVista>
      ) : null}

      {respuesta === null && pedido.cargando ? <Cargando texto="Armando tus viajes…" /> : null}

      {avisoDeVersion}

      {respuesta !== null && rutas.length === 0 && alDia ? (
        <SinRutas respuesta={respuesta} consulta={consulta} />
      ) : null}

      {rutas.length > 0 ? (
        <ol className={`viajes${pedido.cargando ? " viajes--espera" : ""}`} aria-label="Viajes propuestos">
          {rutas.map((ruta, i) => (
            <li key={ruta.polo.id}>
              <TarjetaRuta
                ruta={ruta}
                enlace={enlaces.resultados(consulta, vigente, i + 1)}
                marcarPocoTuristico={!todosPocoTuristicos}
                foto={fotos ? fotoDelViaje(ruta, fotos) : null}
              />
            </li>
          ))}
        </ol>
      ) : null}

      {respuesta !== null && rutas.length > 0 ? (
        <p className="resultados__nota">
          Los precios y las horas son estimaciones con datos oficiales: DreemGO no vende ni reserva.{" "}
          <Enlace href={enlaces.acerca()}>Cómo se calcula</Enlace>
        </p>
      ) : null}
    </section>
  );
}

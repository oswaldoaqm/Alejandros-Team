// Ayuda breve para quien está preparando un viaje. Las respuestas salen de la
// explicación del producto; los mensajes se guardan para revisión del equipo.

import { type FormEvent, useEffect, useId, useRef, useState } from "react";
import { registrarEvento } from "../analitica";
import { ErrorApi, pedir } from "../api/cliente";
import type { Respuesta } from "../api/tipos";
import { consultaDeVista, pideRecomendacion, prepararConsulta } from "../ayuda/recomendacion";
import { aParametros, type Consulta, detalles, titulo } from "../consulta";
import { useApp } from "../estado/contexto";
import { soles } from "../formato";
import { enlaces, type Vista } from "../ruta";
import { Enlace } from "./Enlace";
import { Hoja } from "./Hoja";
import { Icono } from "./Icono";

type Tema =
  | "empezar"
  | "destino"
  | "comparar"
  | "costos"
  | "clima"
  | "eventos"
  | "disponibilidad"
  | "guardar"
  | "compartir";
type Seccion = "preguntas" | "mensaje";
type Categoria = "duda" | "sugerencia" | "problema";
type Busqueda =
  | { estado: "cargando"; consulta: Consulta; aviso: string | null }
  | { estado: "lista"; consulta: Consulta; aviso: string | null; respuesta: Respuesta }
  | { estado: "error"; consulta: Consulta | null; mensaje: string };
type Turno = { id: number; pregunta: string; tema: Tema | null; busqueda?: Busqueda };

const TEMAS: Record<Tema, { pregunta: string; respuesta: string; accion: string; href: string }> = {
  empezar: {
    pregunta: "¿Cómo empiezo a planear?",
    respuesta:
      "Elige desde dónde sales, cuándo viajas, cuántos días tienes y qué te gusta. DreemGO puede proponerte hasta tres viajes; si eliges una zona, prepara un viaje para ella.",
    accion: "Armar mi viaje",
    href: enlaces.planear(),
  },
  destino: {
    pregunta: "¿Puedo elegir un destino concreto?",
    respuesta:
      "Sí. Elige una zona en Planear; DreemGO prepara un viaje para ella. Si no cabe con tus días o límite de altura, muestra el motivo y posibles cambios.",
    accion: "Elegir una zona",
    href: enlaces.planear(),
  },
  comparar: {
    pregunta: "¿Cómo comparo los viajes?",
    respuesta:
      "Una búsqueda puede mostrar hasta tres viajes. Abre cada uno y compara el costo estimado, el tiempo de traslado, el clima y los avisos antes de elegir.",
    accion: "Ver mis opciones",
    href: enlaces.planear(),
  },
  costos: {
    pregunta: "¿El costo es un precio final?",
    respuesta:
      "No. El viaje muestra un rango estimado por persona para orientarte. Confirma transporte, alojamiento y entradas antes de reservar.",
    accion: "Ver cómo se calcula",
    href: enlaces.acerca(),
  },
  clima: {
    pregunta: "¿Cómo consideran el clima y la altura?",
    respuesta:
      "La información climática ayuda a elegir una época con base en datos históricos; no es un pronóstico diario. En el formulario puedes fijar la altura máxima de las paradas.",
    accion: "Ajustar mi viaje",
    href: enlaces.planear(),
  },
  eventos: {
    pregunta: "¿Hay fiestas en mi viaje?",
    respuesta:
      "El calendario reúne festividades y eventos publicados por municipios. Si coinciden con la zona y las fechas, pueden aparecer en el itinerario. No cambian el orden de los destinos recomendados.",
    accion: "Ver el calendario",
    href: enlaces.calendario(),
  },
  disponibilidad: {
    pregunta: "¿Puedo reservar desde la web?",
    respuesta:
      "DreemGO no vende pasajes ni consulta la disponibilidad de buses, vuelos o entradas en tiempo real. Los horarios y costos son estimados; verifica cada opción antes de viajar.",
    accion: "Ver los límites del plan",
    href: enlaces.acerca(),
  },
  guardar: {
    pregunta: "¿Dónde queda el viaje que guardé?",
    respuesta:
      "Abre una ruta y pulsa Guardar. La encontrarás en Guardados de este mismo navegador, sin crear una cuenta.",
    accion: "Ver mis guardados",
    href: enlaces.misViajes(),
  },
  compartir: {
    pregunta: "¿Cómo comparto o imprimo mi viaje?",
    respuesta:
      "Abre una ruta y usa Compartir para enviar o copiar su enlace. Con Imprimir o guardar en PDF puedes conservar el plan.",
    accion: "Abrir mis viajes",
    href: enlaces.misViajes(),
  },
};

const ORDEN: Tema[] = [
  "empezar",
  "destino",
  "comparar",
  "costos",
  "clima",
  "eventos",
  "disponibilidad",
  "guardar",
  "compartir",
];
const SIGUIENTES: Record<Tema, Tema[]> = {
  empezar: ["destino", "costos", "clima"],
  destino: ["comparar", "clima", "costos"],
  comparar: ["costos", "disponibilidad", "compartir"],
  costos: ["disponibilidad", "comparar", "clima"],
  clima: ["eventos", "destino", "costos"],
  eventos: ["clima", "comparar", "disponibilidad"],
  disponibilidad: ["costos", "compartir", "eventos"],
  guardar: ["compartir", "comparar", "empezar"],
  compartir: ["guardar", "comparar", "disponibilidad"],
};
const PALABRAS: { tema: Tema; patron: RegExp }[] = [
  { tema: "compartir", patron: /\b(compartir|enviar|mandar|imprimir|pdf|copiar|enlace)\b/ },
  { tema: "comparar", patron: /\b(comparar|comparacion|alternativas|propuestas|opciones|diferencia)\b/ },
  { tema: "eventos", patron: /\b(fiestas?|festividades|festivales?|eventos?|calendario)\b/ },
  {
    tema: "disponibilidad",
    patron: /\b(reservar|reserva|disponibilidad|pasajes|boletos|entradas|horarios?)\b/,
  },
  {
    tema: "costos",
    patron: /\b(costo|costos|costar|costara|cuesta|precio|precios|presupuesto|gasto|gastar|soles)\b/,
  },
  { tema: "clima", patron: /\b(clima|lluvia|lluvias|altura|altitud|temporada|pronostico)\b/ },
  { tema: "guardar", patron: /\b(guardar|guardado|guardados|guarde|recuperar)\b/ },
  { tema: "destino", patron: /\b(destino|zona|ciudad|lugar)\b/ },
  { tema: "empezar", patron: /\b(empezar|comenzar|planear|planificar|armar|origen|destino)\b/ },
];
const CLAVE_SESION = "dreemgo.comentarios.sesion.v1";
let sesionTemporal: string | null = null;

function temaDePregunta(texto: string): Tema | null {
  const sencilla = texto
    .toLocaleLowerCase("es-PE")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
  const exacta = ORDEN.find(
    (tema) =>
      sencilla.replace(/[^a-z0-9 ]/g, "").trim() ===
      TEMAS[tema].pregunta
        .toLocaleLowerCase("es-PE")
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9 ]/g, "")
        .trim(),
  );
  if (exacta) return exacta;
  return PALABRAS.find(({ patron }) => patron.test(sencilla))?.tema ?? null;
}

function sesionDeComentarios(): string {
  if (sesionTemporal) return sesionTemporal;
  try {
    const guardada = sessionStorage.getItem(CLAVE_SESION);
    if (guardada && /^[0-9a-f-]{36}$/i.test(guardada)) {
      sesionTemporal = guardada;
      return guardada;
    }
  } catch {
    // El formulario todavía puede enviarse si el navegador bloquea sessionStorage.
  }
  const nueva = crypto.randomUUID();
  sesionTemporal = nueva;
  try {
    sessionStorage.setItem(CLAVE_SESION, nueva);
  } catch {
    // Se conserva el ID durante esta visita.
  }
  return nueva;
}

function temaInicial(vista: Vista): Tema {
  if (vista.tipo === "planear") return "costos";
  if (vista.tipo === "resultados") return "comparar";
  if (vista.tipo === "polo" || vista.tipo === "mis-viajes") return "guardar";
  if (vista.tipo === "calendario") return "eventos";
  return "empezar";
}

function enlaceDelTema(tema: Tema, vista: Vista): string {
  if (tema === "comparar" && vista.tipo === "resultados") {
    return enlaces.resultados(vista.consulta, vista.version);
  }
  if (tema === "compartir" && vista.tipo === "resultados") {
    return enlaces.resultados(vista.consulta, vista.version, vista.ruta);
  }
  return TEMAS[tema].href;
}

export function AyudaViaje({ vista }: { vista: Vista }) {
  const { opciones, nombres } = useApp();
  const [abierta, ponerAbierta] = useState(false);
  const [seccion, ponerSeccion] = useState<Seccion>("preguntas");
  const [historial, ponerHistorial] = useState<Turno[]>([]);
  const [ultimoTema, ponerUltimoTema] = useState<Tema>("empezar");
  const [verTodos, ponerVerTodos] = useState(false);
  const [textoPregunta, ponerTextoPregunta] = useState("");
  const [errorPregunta, ponerErrorPregunta] = useState("");
  const [categoria, ponerCategoria] = useState<Categoria>("duda");
  const [mensaje, ponerMensaje] = useState("");
  const [enviando, ponerEnviando] = useState(false);
  const [aviso, ponerAviso] = useState("");
  const [error, ponerError] = useState("");
  const id = useId();
  const proximoId = useRef(0);
  const conversacion = useRef<HTMLDivElement>(null);
  const controles = useRef(new Map<number, AbortController>());

  useEffect(
    () => () => {
      for (const control of controles.current.values()) control.abort();
      controles.current.clear();
    },
    [],
  );

  useEffect(() => {
    if (!abierta || historial.length === 0) return;
    if (conversacion.current) conversacion.current.scrollTop = conversacion.current.scrollHeight;
  }, [abierta, historial]);

  const abrir = () => {
    ponerErrorPregunta("");
    ponerSeccion("preguntas");
    ponerError("");
    ponerAviso("");
    ponerAbierta(true);
  };

  const anotarPregunta = (texto: string, encontrada: Tema | null) => {
    // Solo registra el uso de la ayuda si el visitante aceptó las estadísticas.
    // El texto de la pregunta permanece en esta pantalla y nunca sale al panel.
    registrarEvento("ayuda_consultada");
    proximoId.current += 1;
    ponerHistorial((actual) => [...actual, { id: proximoId.current, pregunta: texto, tema: encontrada }]);
    if (encontrada) ponerUltimoTema(encontrada);
    ponerTextoPregunta("");
    ponerErrorPregunta("");
    ponerVerTodos(false);
  };

  const recomendar = async (texto: string) => {
    registrarEvento("ayuda_consultada");
    proximoId.current += 1;
    const idTurno = proximoId.current;
    const base = consultaDeVista(vista);
    const preparada = opciones.datos ? prepararConsulta(texto, base, opciones.datos) : null;
    if (!preparada || "error" in preparada) {
      const mensaje =
        preparada && "error" in preparada
          ? preparada.error
          : "Espera a que carguen las opciones del planificador y vuelve a intentarlo.";
      ponerHistorial((actual) => [
        ...actual,
        { id: idTurno, pregunta: texto, tema: null, busqueda: { estado: "error", consulta: base, mensaje } },
      ]);
      ponerTextoPregunta("");
      ponerErrorPregunta("");
      return;
    }
    const { consulta, aviso } = preparada;
    ponerHistorial((actual) => [
      ...actual,
      { id: idTurno, pregunta: texto, tema: null, busqueda: { estado: "cargando", consulta, aviso } },
    ]);
    ponerTextoPregunta("");
    ponerErrorPregunta("");
    const control = new AbortController();
    controles.current.set(idTurno, control);
    try {
      const respuesta = await pedir<Respuesta>("/v1/viajes", {
        parametros: aParametros(consulta),
        senal: control.signal,
      });
      if (control.signal.aborted) return;
      ponerHistorial((actual) =>
        actual.map((turno) =>
          turno.id === idTurno
            ? { ...turno, busqueda: { estado: "lista", consulta, aviso, respuesta } }
            : turno,
        ),
      );
    } catch (causa) {
      if (control.signal.aborted) return;
      const mensaje =
        causa instanceof ErrorApi
          ? causa.message
          : "No pudimos calcular los viajes ahora. Vuelve a intentarlo.";
      ponerHistorial((actual) =>
        actual.map((turno) =>
          turno.id === idTurno ? { ...turno, busqueda: { estado: "error", consulta, mensaje } } : turno,
        ),
      );
    } finally {
      controles.current.delete(idTurno);
    }
  };

  const preguntar = (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    const texto = textoPregunta.trim();
    if (!texto) {
      ponerErrorPregunta("Escribe una pregunta o elige una de las opciones.");
      return;
    }
    if (pideRecomendacion(texto)) void recomendar(texto);
    else anotarPregunta(texto, temaDePregunta(texto));
  };

  const borrarConversacion = () => {
    for (const control of controles.current.values()) control.abort();
    controles.current.clear();
    ponerHistorial([]);
    ponerUltimoTema(temaInicial(vista));
    ponerTextoPregunta("");
    ponerErrorPregunta("");
    ponerVerTodos(false);
  };

  const enviar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    if (enviando) return;
    const texto = mensaje.trim();
    ponerAviso("");
    if (texto.length < 10 || texto.length > 1000) {
      ponerError("Escribe entre 10 y 1000 caracteres para que podamos entender tu mensaje.");
      return;
    }
    ponerError("");
    ponerEnviando(true);
    try {
      const respuesta = await pedir<{ id: string; estado: "recibido" }>("/v1/comentarios", {
        metodo: "POST",
        cuerpo: { sesion: sesionDeComentarios(), categoria, mensaje: texto },
      });
      if (respuesta.estado !== "recibido") throw new Error("Respuesta inesperada");
      // El mensaje va al buzón; el panel solo recibe que se envió uno, sin texto.
      registrarEvento("comentario_enviado");
      ponerMensaje("");
      ponerAviso("Recibimos tu mensaje. Gracias por ayudarnos a mejorar DreemGO.");
    } catch (causa) {
      if (causa instanceof ErrorApi && causa.estado === 429) {
        ponerError("Ya recibimos tres mensajes de esta sesión. Puedes volver a escribirnos en una hora.");
      } else if (causa instanceof ErrorApi && causa.tipo === "validacion") {
        ponerError(causa.message);
      } else {
        ponerError("No pudimos guardar tu mensaje. Vuelve a intentarlo en un momento.");
      }
    } finally {
      ponerEnviando(false);
    }
  };

  const inicio = temaInicial(vista);
  const sugeridos = historial.length > 0 ? SIGUIENTES[ultimoTema] : [inicio, ...SIGUIENTES[inicio]];
  const preguntas = verTodos ? ORDEN : [...new Set(sugeridos)];
  const ultimo = historial.at(-1);

  return (
    <>
      <button
        type="button"
        className="ayuda-lanzador"
        onClick={abrir}
        aria-label="Abrir ayuda de viaje"
        aria-haspopup="dialog"
        aria-expanded={abierta}
      >
        <Icono nombre="ayuda" tamano={20} />
        <span>¿Te ayudamos?</span>
      </button>
      <Hoja abierta={abierta} alCerrar={() => ponerAbierta(false)} titulo="Te ayudamos a planear">
        <div className="ayuda-viaje">
          <p className="ayuda-viaje__intro">¿Qué necesitas saber de tu viaje?</p>
          <p className="ayuda-viaje__alcance">
            Dudas con respuestas preparadas y viajes calculados por DreemGO. Sin atención en vivo ni reservas.
          </p>
          <fieldset className="ayuda-viaje__pestanas">
            <legend className="solo-lector">Tipo de ayuda</legend>
            <button
              type="button"
              aria-pressed={seccion === "preguntas"}
              onClick={() => ponerSeccion("preguntas")}
            >
              Dudas rápidas
            </button>
            <button
              type="button"
              aria-label="Déjanos un mensaje"
              aria-pressed={seccion === "mensaje"}
              onClick={() => ponerSeccion("mensaje")}
            >
              Mensaje
            </button>
          </fieldset>
          {seccion === "preguntas" ? (
            <div className="ayuda-viaje__preguntas">
              <div
                className="ayuda-viaje__conversacion"
                ref={conversacion}
                role="log"
                aria-label="Conversación de ayuda"
                aria-live="off"
              >
                <p className="ayuda-viaje__bienvenida">
                  Hola. Puedo orientarte sobre destinos, costos y clima, o buscar viajes con el motor de
                  DreemGO.
                </p>
                {historial.map((turno) => (
                  <div className="ayuda-viaje__turno" key={turno.id}>
                    <p className="ayuda-viaje__pregunta-elegida">{turno.pregunta}</p>
                    <div
                      className="ayuda-viaje__mensaje-guia"
                      role={turno.id === ultimo?.id ? "status" : undefined}
                    >
                      <strong>Guía DreemGO</strong>
                      {turno.busqueda ? (
                        turno.busqueda.estado === "cargando" ? (
                          <p>Buscando opciones con el motor de viajes…</p>
                        ) : turno.busqueda.estado === "error" ? (
                          <>
                            <p>{turno.busqueda.mensaje}</p>
                            <Enlace
                              href={enlaces.planear(turno.busqueda.consulta)}
                              onClick={() => ponerAbierta(false)}
                            >
                              Ajustar el viaje <Icono nombre="flecha" tamano={16} />
                            </Enlace>
                          </>
                        ) : (
                          <>
                            <p>
                              <strong>Consulta usada:</strong> {titulo(turno.busqueda.consulta, nombres)}.
                            </p>
                            {detalles(turno.busqueda.consulta, nombres) ? (
                              <p>{detalles(turno.busqueda.consulta, nombres)}.</p>
                            ) : null}
                            {turno.busqueda.aviso ? <p>{turno.busqueda.aviso}</p> : null}
                            {turno.busqueda.respuesta.rutas.length > 0 ? (
                              <>
                                <p>
                                  Las opciones siguen el orden del motor. Revisa si cada una cumple tus
                                  intereses antes de elegir.
                                </p>
                                <ol className="ayuda-viaje__rutas">
                                  {turno.busqueda.respuesta.rutas.slice(0, 3).map((ruta, indice) => {
                                    if (turno.busqueda?.estado !== "lista") return null;
                                    const { consulta, respuesta } = turno.busqueda;
                                    const avisos = ruta.avisos ?? [];
                                    const avisoVisible =
                                      avisos.find((aviso) =>
                                        /no incluye paradas|sin paradas|ninguna parada/i.test(aviso.mensaje),
                                      ) ??
                                      avisos.find((aviso) => aviso.nivel === "advertencia") ??
                                      avisos[0];
                                    const masAvisos = avisos.filter((aviso) => aviso !== avisoVisible);
                                    const masMotivos = ruta.motivos.slice(1);
                                    return (
                                      <li key={ruta.polo.id}>
                                        <b>{ruta.polo.nombre}</b> · {ruta.polo.region}
                                        <span>
                                          Estimado por persona: {soles(ruta.costo.p20)}–
                                          {soles(ruta.costo.p80)}.
                                        </span>
                                        {ruta.motivos[0] ? <span>{ruta.motivos[0]}</span> : null}
                                        {avisoVisible ? (
                                          <span className="ayuda-viaje__aviso">
                                            Atención: {avisoVisible.mensaje}
                                          </span>
                                        ) : null}
                                        {masMotivos.length + masAvisos.length > 0 ? (
                                          <details>
                                            <summary>Ver más motivos y avisos</summary>
                                            <div>
                                              {masMotivos.map((motivo) => (
                                                <span key={motivo}>{motivo}</span>
                                              ))}
                                              {masAvisos.map((aviso) => (
                                                <span
                                                  className="ayuda-viaje__aviso"
                                                  key={`${aviso.tipo}-${aviso.mensaje}`}
                                                >
                                                  Atención: {aviso.mensaje}
                                                </span>
                                              ))}
                                            </div>
                                          </details>
                                        ) : null}
                                        <Enlace
                                          href={enlaces.resultados(
                                            consulta,
                                            respuesta.version_datos,
                                            indice + 1,
                                          )}
                                          onClick={() => ponerAbierta(false)}
                                        >
                                          Ver este itinerario <Icono nombre="flecha" tamano={16} />
                                        </Enlace>
                                      </li>
                                    );
                                  })}
                                </ol>
                              </>
                            ) : (
                              <p>
                                {turno.busqueda.respuesta.sin_resultado?.motivo ??
                                  "No salió un viaje con esos criterios."}
                              </p>
                            )}
                            <p className="ayuda-viaje__nota">
                              Son costos y tiempos estimados; confirma las condiciones antes de viajar.
                            </p>
                            <Enlace
                              href={enlaces.planear(turno.busqueda.consulta)}
                              onClick={() => ponerAbierta(false)}
                            >
                              Cambiar mis preferencias <Icono nombre="flecha" tamano={16} />
                            </Enlace>
                          </>
                        )
                      ) : turno.tema ? (
                        <>
                          <p>{TEMAS[turno.tema].respuesta}</p>
                          <Enlace href={enlaceDelTema(turno.tema, vista)} onClick={() => ponerAbierta(false)}>
                            {TEMAS[turno.tema].accion} <Icono nombre="flecha" tamano={16} />
                          </Enlace>
                        </>
                      ) : (
                        <>
                          <p>
                            Aún no tenemos una respuesta preparada para esa duda. Puedes dejársela al equipo.
                          </p>
                          <button
                            type="button"
                            className="ayuda-viaje__pasar-mensaje"
                            onClick={() => {
                              ponerMensaje(turno.pregunta);
                              ponerCategoria("duda");
                              ponerSeccion("mensaje");
                            }}
                          >
                            Dejar este mensaje <Icono nombre="flecha" tamano={16} />
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
              <form className="ayuda-viaje__consulta" onSubmit={preguntar}>
                <label htmlFor={`${id}-pregunta`}>Escribe tu pregunta</label>
                <div>
                  <input
                    id={`${id}-pregunta`}
                    type="text"
                    value={textoPregunta}
                    maxLength={180}
                    placeholder="Por ejemplo: ¿cuánto costará mi viaje?"
                    onChange={(evento) => ponerTextoPregunta(evento.target.value)}
                    aria-invalid={Boolean(errorPregunta)}
                  />
                  <button type="submit" className="boton boton--primario">
                    Preguntar
                  </button>
                </div>
                {errorPregunta ? (
                  <p role="alert" className="ayuda-viaje__error">
                    {errorPregunta}
                  </p>
                ) : null}
              </form>
              <div className="ayuda-viaje__tema-cabeza">
                <p className="ayuda-viaje__etiqueta">
                  {historial.length > 0 ? "También puedes preguntar" : "Empieza con una de estas preguntas"}
                </p>
                {historial.length > 0 ? (
                  <button type="button" className="ayuda-viaje__reiniciar" onClick={borrarConversacion}>
                    Borrar conversación
                  </button>
                ) : null}
              </div>
              <div className="ayuda-viaje__opciones">
                <button type="button" onClick={() => void recomendar("Recomiéndame viajes")}>
                  Recomiéndame viajes
                </button>
                {preguntas.map((clave) => (
                  <button
                    type="button"
                    key={clave}
                    onClick={() => anotarPregunta(TEMAS[clave].pregunta, clave)}
                  >
                    {TEMAS[clave].pregunta}
                  </button>
                ))}
              </div>
              <button
                type="button"
                className="ayuda-viaje__mas-temas"
                aria-expanded={verTodos}
                onClick={() => ponerVerTodos((actual) => !actual)}
              >
                {verTodos ? "Ver menos temas" : "Ver todos los temas"}
              </button>
            </div>
          ) : (
            <form className="ayuda-viaje__formulario" onSubmit={enviar}>
              <p>Tu comentario quedará disponible para el equipo de DreemGO. No incluyas datos personales.</p>
              <label htmlFor={`${id}-categoria`}>¿Sobre qué nos escribes?</label>
              <select
                id={`${id}-categoria`}
                value={categoria}
                onChange={(evento) => ponerCategoria(evento.target.value as Categoria)}
              >
                <option value="duda">Una duda</option>
                <option value="sugerencia">Una sugerencia</option>
                <option value="problema">Un problema</option>
              </select>
              <label htmlFor={`${id}-mensaje`}>Tu mensaje</label>
              <textarea
                id={`${id}-mensaje`}
                value={mensaje}
                onChange={(evento) => ponerMensaje(evento.target.value)}
                maxLength={1000}
                rows={5}
                placeholder="Cuéntanos qué pasó o qué te gustaría encontrar…"
                aria-describedby={`${id}-cuenta`}
                aria-invalid={Boolean(error)}
              />
              <p id={`${id}-cuenta`} className="ayuda-viaje__cuenta">
                {mensaje.length} de 1000 caracteres
              </p>
              {error ? (
                <p className="ayuda-viaje__error" role="alert">
                  {error}
                </p>
              ) : null}
              {aviso ? (
                <p className="ayuda-viaje__exito" role="status">
                  {aviso}
                </p>
              ) : null}
              <button type="submit" className="boton boton--primario" disabled={enviando}>
                {enviando ? "Enviando…" : "Enviar mensaje"}
              </button>
            </form>
          )}
        </div>
      </Hoja>
    </>
  );
}

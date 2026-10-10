// Para municipalidades y oficinas de destino: publicar un evento (POST /v1/eventos).
// Lo publicado sale en el calendario y, si se marca su lugar, en las rutas que pasan cerca.
// No cambia qué rutas se proponen ni en qué orden (docs/decisiones/0011).

import { type FormEvent, useEffect, useId, useMemo, useRef, useState } from "react";
import { ErrorApi, type ErrorDeCampo, pedir } from "../api/cliente";
import type { Evento, EventoNuevo } from "../api/tipos";
import { useApp } from "../estado/contexto";
import { olvidarPedidos } from "../estado/pedido";
import { useTitulo } from "../estado/titulo";
import { aIso, fechaLocal, mes } from "../formato";
import { llevarA } from "../movimiento";
import { ElegirLugar } from "../piezas/ElegirLugar";
import { Enlace } from "../piezas/Enlace";
import { Icono } from "../piezas/Icono";
import { ListaEventos } from "../piezas/Listas";
import type { Lugar } from "../piezas/MapaLugar";
import { REGIONES } from "../regiones";
import { enlaces } from "../ruta";
import { ventanaDelMes } from "./PaginaCalendario";

/** Lo mismo que valida el contrato (dreemgo/contrato.py), para avisar antes de enviar. */
const DURACION_MAX_DIAS = 60;
const DIA_MS = 24 * 60 * 60 * 1000;

interface Campos {
  nombre: string;
  tipo: string;
  fecha_inicio: string;
  fecha_fin: string;
  region: string;
  provincia: string;
  distrito: string;
  url: string;
  publicado_por: string;
  clave: string;
}

const VACIO: Campos = {
  nombre: "",
  tipo: "",
  fecha_inicio: "",
  fecha_fin: "",
  region: "",
  provincia: "",
  distrito: "",
  url: "",
  publicado_por: "",
  clave: "",
};

/** Con qué casilla va cada campo del contrato: las coordenadas son una sola, el lugar. */
const CASILLA: Record<string, keyof Campos | "lugar"> = {
  nombre: "nombre",
  tipo: "tipo",
  fecha_inicio: "fecha_inicio",
  fecha_fin: "fecha_fin",
  region: "region",
  provincia: "provincia",
  distrito: "distrito",
  lat: "lugar",
  lon: "lugar",
  url: "url",
  publicado_por: "publicado_por",
};

type Estado =
  | { tipo: "listo" }
  | { tipo: "enviando" }
  | { tipo: "publicado"; evento: Evento; conLugar: boolean }
  | { tipo: "error"; error: ErrorApi };

/** El último día en que puede empezar un evento que se publica hoy: doce meses, contando este. */
export function ultimoInicio(hoy: Date): string {
  return aIso(new Date(hoy.getFullYear() + 1, hoy.getMonth(), 0));
}

function masDias(iso: string, dias: number): string | undefined {
  const f = fechaLocal(iso);
  return f ? aIso(new Date(f.getTime() + dias * DIA_MS + DIA_MS / 2)) : undefined;
}

/** Los errores del API, cada uno con su casilla; los que son de todo el evento quedan sueltos. */
function repartir(campos: ErrorDeCampo[]): { porCasilla: Record<string, string>; sueltos: string[] } {
  const porCasilla: Record<string, string> = {};
  const sueltos: string[] = [];
  for (const c of campos) {
    const casilla = CASILLA[c.campo];
    if (casilla && !(casilla in porCasilla)) porCasilla[casilla] = c.mensaje;
    else if (!casilla) sueltos.push(c.mensaje);
  }
  return { porCasilla, sueltos };
}

export function Publicar() {
  const { opciones } = useApp();
  const id = useId();
  const [c, poner] = useState<Campos>(VACIO);
  const [lugar, ponerLugar] = useState<Lugar | null>(null);
  const [estado, ponerEstado] = useState<Estado>({ tipo: "listo" });
  const aviso = useRef<HTMLDivElement>(null);
  const hecho = useRef<HTMLHeadingElement>(null);
  const titulo = useRef<HTMLHeadingElement>(null);
  const venia = useRef<Estado["tipo"]>("listo");
  useTitulo("Publicar un evento");

  const hoy = useMemo(() => new Date(), []);
  const cambiar = (parte: Partial<Campos>) => poner((antes) => ({ ...antes, ...parte }));
  const region = REGIONES.find((r) => r.nombre === c.region);
  const cerca = useMemo(() => (region ? { lat: region.lat, lon: region.lon } : null), [region]);

  // Lo que pasó después de enviar se lleva a la vista y recibe el foco: no queda escondido
  // arriba. Y al volver al formulario para publicar otro, el foco va a su título.
  useEffect(() => {
    const vuelve = estado.tipo === "listo" && venia.current === "publicado";
    venia.current = estado.tipo;
    const destino =
      estado.tipo === "error"
        ? aviso.current
        : estado.tipo === "publicado"
          ? hecho.current
          : vuelve
            ? titulo.current
            : null;
    if (!destino) return;
    destino.focus({ preventScroll: true });
    llevarA(destino, "start");
  }, [estado]);

  const enviar = async (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    if (estado.tipo === "enviando") return;
    const clave = c.clave.trim();
    // Una cabecera solo lleva letras, números y signos comunes: con otra cosa el navegador ni la envía.
    if (!/^[\x21-\x7e]+$/.test(clave)) {
      const mensaje = "La clave no lleva espacios, tildes ni eñes. Revisa que esté completa.";
      ponerEstado({ tipo: "error", error: new ErrorApi("sin_permiso", mensaje, [], 401) });
      return;
    }
    ponerEstado({ tipo: "enviando" });
    const cuerpo: EventoNuevo = {
      nombre: c.nombre,
      tipo: c.tipo || null,
      fecha_inicio: c.fecha_inicio,
      fecha_fin: c.fecha_fin || c.fecha_inicio,
      distrito: c.distrito,
      provincia: c.provincia,
      region: c.region,
      lat: lugar?.lat ?? null,
      lon: lugar?.lon ?? null,
      url: c.url || null,
      publicado_por: c.publicado_por,
    };
    try {
      const publicado = await pedir<Evento>("/v1/eventos", {
        metodo: "POST",
        cuerpo,
        cabeceras: { "X-Clave-Publicador": clave },
      });
      // El calendario y las rutas ya pedidos pueden haber cambiado: se piden otra vez.
      olvidarPedidos();
      opciones.reintentar();
      ponerEstado({ tipo: "publicado", evento: publicado, conLugar: lugar !== null });
    } catch (causa) {
      const error = causa instanceof ErrorApi ? causa : new ErrorApi("servidor", "Algo falló al publicar.");
      ponerEstado({ tipo: "error", error });
    }
  };

  /** Para publicar otro de la misma entidad no hay que volver a escribir quién publica ni dónde. */
  const otro = () => {
    poner((antes) => ({ ...antes, nombre: "", tipo: "", fecha_inicio: "", fecha_fin: "", url: "" }));
    ponerLugar(null);
    ponerEstado({ tipo: "listo" });
  };

  if (estado.tipo === "publicado") {
    return (
      <section className="pagina pagina--angosta">
        <h1 tabIndex={-1} ref={hecho}>
          Evento publicado
        </h1>
        <Publicado evento={estado.evento} conLugar={estado.conLugar} hoy={hoy} otro={otro} />
      </section>
    );
  }

  const error = estado.tipo === "error" ? estado.error : null;
  const { porCasilla, sueltos } = repartir(error?.campos ?? []);
  // 401 es la clave; 403 es que el servidor no acepta publicaciones, y eso no se corrige en una casilla.
  if (error?.estado === 401) porCasilla.clave = error.message;
  const enviando = estado.tipo === "enviando";
  const finMinimo = c.fecha_inicio > aIso(hoy) ? c.fecha_inicio : aIso(hoy);

  /**
   * Lo que una casilla necesita para decir su error: el texto, y los atributos que lo enlazan
   * con ella junto a su ayuda, si la tiene.
   */
  const falla = (casilla: keyof Campos | "lugar", ayuda?: string) => {
    const mensaje = porCasilla[casilla];
    const descrita = [mensaje ? `${id}-${casilla}-error` : null, ayuda ?? null].filter(Boolean).join(" ");
    return {
      atributos: {
        ...(mensaje ? { "aria-invalid": true } : {}),
        ...(descrita ? { "aria-describedby": descrita } : {}),
      },
      texto: mensaje ? (
        <p className="campo__error" id={`${id}-${casilla}-error`}>
          {mensaje}
        </p>
      ) : null,
    };
  };

  return (
    <section className="pagina pagina--angosta">
      <h1 tabIndex={-1} ref={titulo} className="pagina__titulo">
        Publicar un evento
      </h1>
      <p className="pagina__bajada">
        Para municipalidades y oficinas de destino. Lo que publiques sale en el calendario de fiestas y, si
        marcas dónde es, en los viajes que pasan cerca en esas fechas, con el nombre de tu entidad. No cambia
        qué viajes se proponen ni en qué orden.
      </p>

      {error ? (
        <div className="aviso aviso--critico" role="alert" tabIndex={-1} ref={aviso}>
          <Icono nombre="critico" />
          <div>
            <p className="aviso__titulo">No se publicó</p>
            {error.tipo === "validacion" ? (
              sueltos.length > 0 ? (
                <ul className="lista-simple">
                  {sueltos.map((mensaje) => (
                    <li key={mensaje}>{mensaje}</li>
                  ))}
                </ul>
              ) : (
                <p>Hay algo que corregir: está marcado en su casilla.</p>
              )
            ) : (
              <p>{error.message}</p>
            )}
          </div>
        </div>
      ) : null}

      <form className="formulario" onSubmit={enviar} aria-label="Publicar un evento">
        <div className="campo">
          <label htmlFor={`${id}-nombre`}>Nombre del evento</label>
          <input
            id={`${id}-nombre`}
            type="text"
            required
            minLength={3}
            maxLength={120}
            value={c.nombre}
            onChange={(e) => cambiar({ nombre: e.target.value })}
            {...falla("nombre").atributos}
          />
          {falla("nombre").texto}
        </div>

        <div className="formulario__par">
          <div className="campo">
            <label htmlFor={`${id}-inicio`}>Empieza</label>
            <input
              id={`${id}-inicio`}
              type="date"
              required
              max={ultimoInicio(hoy)}
              value={c.fecha_inicio}
              onChange={(e) => cambiar({ fecha_inicio: e.target.value })}
              {...falla("fecha_inicio").atributos}
            />
            {falla("fecha_inicio").texto}
          </div>
          <div className="campo">
            <label htmlFor={`${id}-fin`}>
              Termina <span className="opcional">Opcional</span>
            </label>
            <input
              id={`${id}-fin`}
              type="date"
              min={finMinimo}
              max={c.fecha_inicio ? masDias(c.fecha_inicio, DURACION_MAX_DIAS) : undefined}
              value={c.fecha_fin}
              onChange={(e) => cambiar({ fecha_fin: e.target.value })}
              {...falla("fecha_fin", `${id}-fin-ayuda`).atributos}
            />
            {falla("fecha_fin").texto}
            <p className="ayuda" id={`${id}-fin-ayuda`}>
              Si dura un día, se deja en blanco.
            </p>
          </div>
        </div>

        <div className="formulario__par">
          <div className="campo">
            <label htmlFor={`${id}-region`}>Región</label>
            <select
              id={`${id}-region`}
              required
              value={c.region}
              onChange={(e) => cambiar({ region: e.target.value })}
              {...falla("region").atributos}
            >
              <option value="">Elige una</option>
              {REGIONES.map((r) => (
                <option key={r.nombre} value={r.nombre}>
                  {r.nombre}
                </option>
              ))}
            </select>
            {falla("region").texto}
          </div>
          <div className="campo">
            <label htmlFor={`${id}-provincia`}>Provincia</label>
            <input
              id={`${id}-provincia`}
              type="text"
              required
              minLength={2}
              maxLength={80}
              value={c.provincia}
              onChange={(e) => cambiar({ provincia: e.target.value })}
              {...falla("provincia").atributos}
            />
            {falla("provincia").texto}
          </div>
        </div>

        <div className="formulario__par">
          <div className="campo">
            <label htmlFor={`${id}-distrito`}>Distrito</label>
            <input
              id={`${id}-distrito`}
              type="text"
              required
              minLength={2}
              maxLength={80}
              value={c.distrito}
              onChange={(e) => cambiar({ distrito: e.target.value })}
              {...falla("distrito").atributos}
            />
            {falla("distrito").texto}
          </div>
          <div className="campo">
            <label htmlFor={`${id}-tipo`}>
              Tipo de evento <span className="opcional">Opcional</span>
            </label>
            <input
              id={`${id}-tipo`}
              type="text"
              maxLength={60}
              placeholder="Feria gastronómica"
              value={c.tipo}
              onChange={(e) => cambiar({ tipo: e.target.value })}
              {...falla("tipo").atributos}
            />
            {falla("tipo").texto}
          </div>
        </div>

        <fieldset className="campo">
          <legend>
            Dónde es <span className="opcional">Sin marcarlo, sale solo en el calendario</span>
          </legend>
          <p className="ayuda">
            Toca el mapa en el lugar del evento; la marca se puede arrastrar. Con la marca, el evento sale
            también en los viajes que pasan a 10 km o menos.
            {region ? "" : " Al elegir la región, el mapa se acerca a su ciudad principal."}
          </p>
          <ElegirLugar lugar={lugar} cerca={cerca} alElegir={ponerLugar} />
          {falla("lugar").texto}
        </fieldset>

        <div className="campo">
          <label htmlFor={`${id}-url`}>
            Enlace con más información <span className="opcional">Opcional</span>
          </label>
          <input
            id={`${id}-url`}
            type="url"
            inputMode="url"
            placeholder="https://"
            value={c.url}
            onChange={(e) => cambiar({ url: e.target.value })}
            {...falla("url").atributos}
          />
          {falla("url").texto}
        </div>

        <div className="campo">
          <label htmlFor={`${id}-entidad`}>Entidad que publica</label>
          <input
            id={`${id}-entidad`}
            type="text"
            required
            minLength={3}
            maxLength={120}
            autoComplete="organization"
            value={c.publicado_por}
            onChange={(e) => cambiar({ publicado_por: e.target.value })}
            {...falla("publicado_por", `${id}-entidad-ayuda`).atributos}
          />
          {falla("publicado_por").texto}
          <p className="ayuda" id={`${id}-entidad-ayuda`}>
            La municipalidad o la oficina, no una persona. Es lo que el viajero lee junto al evento:
            «Publicado por…».
          </p>
        </div>

        <div className="campo">
          <label htmlFor={`${id}-clave`}>Clave de publicador</label>
          <input
            id={`${id}-clave`}
            type="password"
            required
            autoComplete="off"
            value={c.clave}
            onChange={(e) => cambiar({ clave: e.target.value })}
            {...falla("clave", `${id}-clave-ayuda`).atributos}
          />
          {falla("clave").texto}
          <p className="ayuda" id={`${id}-clave-ayuda`}>
            La que el equipo de DreemGO le dio a tu entidad. No se guarda en este navegador.
          </p>
        </div>

        <div className="formulario__acciones">
          <button type="submit" className="boton boton--primario boton--grande" disabled={enviando}>
            {enviando ? "Publicando…" : "Publicar el evento"}
          </button>
        </div>
        <p className="ayuda ayuda--centrada">
          Si te equivocaste en la ubicación o en el enlace, publícalo otra vez con el mismo nombre, fechas,
          distrito y entidad: se corrige, no se duplica.
        </p>
      </form>
    </section>
  );
}

interface PropsDePublicado {
  evento: Evento;
  conLugar: boolean;
  hoy: Date;
  /** Volver al formulario para publicar otro. */
  otro: () => void;
}

function Publicado({ evento, conLugar, hoy, otro }: PropsDePublicado) {
  const inicio = evento.fecha_inicio ? fechaLocal(evento.fecha_inicio) : null;
  const numero = inicio ? inicio.getMonth() + 1 : null;
  // El calendario muestra cada mes en su próxima vez: el enlace va solo si el evento cae ahí.
  const ventana = numero ? ventanaDelMes(numero, hoy) : null;
  const seVe =
    ventana !== null &&
    evento.fecha_inicio != null &&
    evento.fecha_inicio <= ventana.hasta &&
    (evento.fecha_fin ?? evento.fecha_inicio) >= ventana.desde;
  return (
    <>
      <div className="aviso aviso--bien">
        <Icono nombre="bien" />
        <div>
          <p>
            Ya está en el calendario de fiestas.{" "}
            {conLugar
              ? "Como marcaste dónde es, sale también en los viajes que pasan a 10 km o menos en esas fechas."
              : "Como no marcaste dónde es, no sale en ningún viaje. Para ponerle el lugar, publícalo otra vez con el mismo nombre, fechas, distrito y entidad."}
          </p>
        </div>
      </div>
      <h2 className="viaje__titular">Así lo ve el viajero</h2>
      <ListaEventos eventos={[evento]} />
      <div className="formulario__acciones publicado__acciones">
        <button type="button" className="boton boton--secundario boton--grande" onClick={otro}>
          Publicar otro evento
        </button>
        {seVe && numero ? (
          <Enlace
            href={enlaces.calendario(null, null, numero)}
            className="boton boton--primario boton--grande"
          >
            Ver el calendario de {mes(numero)}
          </Enlace>
        ) : null}
      </div>
    </>
  );
}

// Lectura privada de los mensajes que llegan desde la ayuda del sitio.
// La clave solo vive en esta pantalla; no se guarda ni se añade a la URL.

import { type FormEvent, useState } from "react";
import { ErrorApi, pedir } from "../api/cliente";
import { useTitulo } from "../estado/titulo";

type Categoria = "duda" | "sugerencia" | "problema";

interface Comentario {
  id: string;
  categoria: Categoria;
  mensaje: string;
  instante: string;
}

interface Buzon {
  total: number;
  comentarios: Comentario[];
}

const CATEGORIAS: Record<Categoria, string> = {
  duda: "Duda",
  sugerencia: "Sugerencia",
  problema: "Problema",
};

function fechaEnPeru(valor: string): string {
  const fecha = new Date(valor);
  if (Number.isNaN(fecha.getTime())) return valor;
  return new Intl.DateTimeFormat("es-PE", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "America/Lima",
  }).format(fecha);
}

export function BuzonComentarios() {
  useTitulo("Buzón del equipo");
  const [clave, ponerClave] = useState("");
  const [abierto, ponerAbierto] = useState(false);
  const [buzon, ponerBuzon] = useState<Buzon | null>(null);
  const [cargando, ponerCargando] = useState(false);
  const [error, ponerError] = useState("");

  const cargar = async (claveActual: string) => {
    if (cargando) return;
    ponerError("");
    ponerCargando(true);
    try {
      const respuesta = await pedir<Buzon>("/v1/comentarios", {
        cabeceras: { "X-Clave-Comentarios": claveActual },
      });
      ponerBuzon(respuesta);
      ponerAbierto(true);
    } catch (causa) {
      ponerBuzon(null);
      ponerAbierto(false);
      if (causa instanceof ErrorApi && causa.estado === 401) {
        ponerClave("");
        ponerError("La clave no es correcta. Pide al equipo la clave de lectura y vuelve a intentarlo.");
      } else if (causa instanceof ErrorApi && causa.estado === 403) {
        ponerClave("");
        ponerError("Este servidor todavía no tiene habilitada la lectura de mensajes.");
      } else {
        ponerError("No pudimos leer los mensajes. Revisa la conexión y vuelve a intentarlo.");
      }
    } finally {
      ponerCargando(false);
    }
  };

  const entrar = (evento: FormEvent<HTMLFormElement>) => {
    evento.preventDefault();
    const limpia = clave.trim();
    if (!limpia) {
      ponerError("Escribe la clave de lectura del equipo.");
      return;
    }
    ponerClave(limpia);
    void cargar(limpia);
  };

  const salir = () => {
    ponerClave("");
    ponerBuzon(null);
    ponerAbierto(false);
    ponerError("");
  };

  return (
    <section className="pagina pagina--angosta buzon">
      <header className="buzon__cabeza">
        <p className="buzon__etiqueta">Solo para el equipo</p>
        <h1 tabIndex={-1}>Mensajes de DreemGO</h1>
        <p>
          Aquí llegan las dudas, sugerencias y problemas enviados desde la ayuda. Son comentarios para
          revisar, no una conversación en vivo.
        </p>
      </header>

      {!abierto ? (
        <form className="buzon__acceso" onSubmit={entrar}>
          <label htmlFor="buzon-clave">Clave de lectura del equipo</label>
          <div className="buzon__acceso-fila">
            <input
              id="buzon-clave"
              type="password"
              autoComplete="off"
              value={clave}
              onChange={(evento) => ponerClave(evento.target.value)}
            />
            <button className="boton boton--primario" type="submit" disabled={cargando}>
              {cargando ? "Abriendo…" : "Ver mensajes"}
            </button>
          </div>
          <p>La clave se usa solo mientras esta pantalla está abierta.</p>
        </form>
      ) : (
        <div className="buzon__contenido">
          <div className="buzon__acciones">
            <p role="status">
              {buzon?.total === 1 ? "1 mensaje recibido" : `${buzon?.total ?? 0} mensajes recibidos`}
              {(buzon?.total ?? 0) > 50 ? " · se muestran los 50 más recientes" : ""}
            </p>
            <div>
              <button
                type="button"
                className="boton boton--secundario"
                onClick={() => void cargar(clave)}
                disabled={cargando}
              >
                {cargando ? "Actualizando…" : "Actualizar"}
              </button>
              <button type="button" className="boton boton--secundario" onClick={salir}>
                Cerrar buzón
              </button>
            </div>
          </div>
          {buzon?.comentarios.length ? (
            <ol className="buzon__lista">
              {buzon.comentarios.map((comentario) => (
                <li key={comentario.id} className="buzon__mensaje">
                  <div className="buzon__mensaje-cabeza">
                    <span className="buzon__categoria">{CATEGORIAS[comentario.categoria]}</span>
                    <time dateTime={comentario.instante}>{fechaEnPeru(comentario.instante)}</time>
                  </div>
                  <p>{comentario.mensaje}</p>
                </li>
              ))}
            </ol>
          ) : (
            <p className="buzon__vacio">
              Todavía no hay mensajes. El formulario de ayuda está listo para recibirlos.
            </p>
          )}
        </div>
      )}
      {error ? (
        <p className="buzon__error" role="alert">
          {error}
        </p>
      ) : null}
    </section>
  );
}

// El marco de la app: cabecera, la pantalla que toca según la URL y el pie.

import { useEffect, useMemo, useRef } from "react";
import type { Opciones } from "./api/tipos";
import { clave } from "./consulta";
import { ContextoApp, nombresDe } from "./estado/contexto";
import { useNavegacion } from "./estado/navegacion";
import { usePedido } from "./estado/pedido";
import { Enlace } from "./piezas/Enlace";
import { Limite } from "./piezas/Limite";
import { enlaces, type Vista } from "./ruta";
import { Acerca } from "./vistas/Acerca";
import { Formulario } from "./vistas/Formulario";
import { MisViajes } from "./vistas/MisViajes";
import { PaginaCalendario } from "./vistas/PaginaCalendario";
import { PaginaPolo } from "./vistas/PaginaPolo";
import { Resultados } from "./vistas/Resultados";

/** La pantalla sin sus detalles: cambia cuando se pasa de una a otra, no al afinar la consulta. */
function pagina(vista: Vista): string {
  return vista.tipo === "polo" ? `polo/${vista.id}` : vista.tipo;
}

function Pantalla({ vista }: { vista: Vista }) {
  switch (vista.tipo) {
    case "inicio":
      // La llave rehace el formulario cuando cambia la consulta que se edita.
      return <Formulario key={vista.consulta ? clave(vista.consulta) : "nuevo"} inicial={vista.consulta} />;
    case "resultados":
      return <Resultados consulta={vista.consulta} version={vista.version} elegida={vista.ruta} />;
    case "polo":
      return <PaginaPolo key={vista.id} id={vista.id} consulta={vista.consulta} />;
    case "calendario":
      // La llave lo rehace si el enlace pide otro mes.
      return <PaginaCalendario key={vista.mes ?? "sin-mes"} consulta={vista.consulta} mes={vista.mes} />;
    case "mis-viajes":
      return <MisViajes />;
    case "acerca":
      return <Acerca />;
  }
}

export function App() {
  const [vista, navegar] = useNavegacion();
  const opciones = usePedido<Opciones>("/v1/opciones");
  const contexto = useMemo(
    () => ({ navegar, opciones, nombres: nombresDe(opciones.datos) }),
    [navegar, opciones],
  );

  // Al cambiar de pantalla, el foco va a su título: quien usa lector de pantalla o teclado
  // se entera del cambio y sigue desde ahí.
  const actual = pagina(vista);
  const anterior = useRef(actual);
  useEffect(() => {
    if (anterior.current === actual) return;
    anterior.current = actual;
    const titulo =
      document.querySelector<HTMLElement>("main h1") ?? document.querySelector<HTMLElement>("main");
    titulo?.focus({ preventScroll: true });
  }, [actual]);

  const en = (tipo: Vista["tipo"]) => (vista.tipo === tipo ? "page" : undefined);
  // Con una consulta abierta, el calendario se abre en su mes y ofrece volver a las rutas.
  const consulta = "consulta" in vista ? vista.consulta : null;

  return (
    <ContextoApp.Provider value={contexto}>
      {/* Un botón y no un enlace: el fragmento de la URL dice qué pantalla toca; aquí solo se mueve el foco. */}
      <button type="button" className="saltar" onClick={() => document.getElementById("contenido")?.focus()}>
        Saltar al contenido
      </button>
      <header className="cabecera">
        <div className="cabecera__ancho">
          <Enlace href={enlaces.inicio()} className="marca" aria-label="DreemGO, inicio">
            DreemGO
          </Enlace>
          <nav aria-label="Secciones">
            <Enlace href={enlaces.calendario(consulta)} aria-current={en("calendario")}>
              Fiestas
            </Enlace>
            <Enlace href={enlaces.misViajes()} aria-current={en("mis-viajes")}>
              Mis viajes
            </Enlace>
            {/* En celular este enlace queda en el pie: en la cabecera no cabe sin partirla en dos filas. */}
            <Enlace href={enlaces.acerca()} aria-current={en("acerca")} className="solo-ancho">
              Cómo funciona
            </Enlace>
          </nav>
        </div>
      </header>
      <main id="contenido" tabIndex={-1}>
        {/* Si una pantalla falla, el marco sigue en pie; al pasar a otra se vuelve a intentar. */}
        <Limite
          key={actual}
          respaldo={
            <section className="pagina pagina--angosta">
              <h1 tabIndex={-1}>Algo falló en esta pantalla</h1>
              <p className="bajada">
                No es tu conexión: es un error de la app. Vuelve al inicio o recarga la página.
              </p>
              <a href="./" className="boton boton--primario">
                Volver al inicio
              </a>
            </section>
          }
        >
          <Pantalla vista={vista} />
        </Limite>
      </main>
      <footer className="pie">
        <p>
          DreemGO · rutas por el Perú con datos oficiales de MINCETUR, clima de Open-Meteo y la red de
          OpenStreetMap. <Enlace href={enlaces.acerca()}>Fuentes y cómo funciona</Enlace>
        </p>
      </footer>
    </ContextoApp.Provider>
  );
}

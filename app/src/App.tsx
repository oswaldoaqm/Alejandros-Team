// El marco de la app: cabecera, la pantalla que toca según la URL y el pie.

import { useEffect, useMemo, useRef } from "react";
import type { Opciones } from "./api/tipos";
import { clave } from "./consulta";
import { ContextoApp, nombresDe } from "./estado/contexto";
import { useNavegacion } from "./estado/navegacion";
import { usePedido } from "./estado/pedido";
import { BotonTema } from "./piezas/BotonTema";
import { Enlace } from "./piezas/Enlace";
import { MarcaFlor } from "./piezas/Flor";
import { Icono } from "./piezas/Icono";
import { Limite } from "./piezas/Limite";
import { enlaces, type Vista } from "./ruta";
import { Acerca } from "./vistas/Acerca";
import { Formulario } from "./vistas/Formulario";
import { MisViajes } from "./vistas/MisViajes";
import { PaginaBlog } from "./vistas/PaginaBlog";
import { PaginaCalendario } from "./vistas/PaginaCalendario";
import { PaginaInicio } from "./vistas/PaginaInicio";
import { PaginaPolo } from "./vistas/PaginaPolo";
import { Publicar } from "./vistas/Publicar";
import { Resultados } from "./vistas/Resultados";

/**
 * La pantalla sin sus detalles: cambia cuando se pasa de una a otra, no al afinar la consulta.
 * Abrir un viaje es pasar a otra pantalla: la de los tres viajes queda atrás.
 */
function pagina(vista: Vista): string {
  if (vista.tipo === "polo") return `polo/${vista.id}`;
  if (vista.tipo === "resultados" && vista.ruta !== null) return `viaje/${vista.ruta}`;
  if (vista.tipo === "blog" && vista.slug !== null) return `blog/${vista.slug}`;
  return vista.tipo;
}

function Pantalla({ vista }: { vista: Vista }) {
  switch (vista.tipo) {
    case "inicio":
      return <PaginaInicio />;
    case "planear":
      // La llave rehace el formulario cuando cambia la consulta que se edita.
      return <Formulario key={vista.consulta ? clave(vista.consulta) : "nuevo"} inicial={vista.consulta} />;
    case "blog":
      return <PaginaBlog slug={vista.slug} />;
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
    case "publicar":
      return <Publicar />;
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
  const planeando = vista.tipo === "planear" || vista.tipo === "resultados" || vista.tipo === "polo";
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
            <MarcaFlor />
            DreemGO
          </Enlace>
          <div className="cabecera__acciones">
            <nav aria-label="Secciones" className="cabecera__nav">
              <Enlace href={enlaces.inicio()} aria-current={en("inicio")}>
                Inicio
              </Enlace>
              <Enlace href={enlaces.planear(consulta)} aria-current={planeando ? "page" : undefined}>
                Planear
              </Enlace>
              <Enlace href={enlaces.misViajes()} aria-current={en("mis-viajes")}>
                Guardados
              </Enlace>
              <Enlace href={enlaces.acerca()} aria-current={en("acerca")}>
                Cómo funciona
              </Enlace>
            </nav>
            <BotonTema />
          </div>
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
          Lugares del inventario oficial de MINCETUR, clima de Open-Meteo y caminos de OpenStreetMap.{" "}
          <Enlace href={enlaces.acerca()}>Cómo funciona</Enlace>
        </p>
        <p>
          ¿Eres de una municipalidad? <Enlace href={enlaces.publicar()}>Publica un evento</Enlace>
        </p>
      </footer>
      {/* En celular, las secciones van abajo, al alcance del pulgar. */}
      <nav aria-label="Secciones" className="barra-inferior">
        <Enlace href={enlaces.inicio()} aria-current={en("inicio")}>
          <Icono nombre="flor" tamano={22} />
          Inicio
        </Enlace>
        <Enlace href={enlaces.planear(consulta)} aria-current={planeando ? "page" : undefined}>
          <Icono nombre="mapa" tamano={22} />
          Planear
        </Enlace>
        <Enlace href={enlaces.misViajes()} aria-current={en("mis-viajes")}>
          <Icono nombre="guardar" tamano={22} />
          Guardados
        </Enlace>
        <Enlace href={enlaces.acerca()} aria-current={en("acerca")}>
          <Icono nombre="ayuda" tamano={22} />
          Cómo funciona
        </Enlace>
      </nav>
    </ContextoApp.Provider>
  );
}

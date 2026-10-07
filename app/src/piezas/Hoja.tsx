// Una hoja: lo que se abre encima de la pantalla para elegir algo. En celular sube desde abajo;
// en pantalla ancha aparece al centro. Es un <dialog> nativo: atrapa el foco, se cierra con
// Escape y devuelve el foco a quien la abrió.

import { type ReactNode, useEffect, useId, useRef } from "react";
import { Icono } from "./Icono";

interface Props {
  abierta: boolean;
  alCerrar: () => void;
  titulo: string;
  children: ReactNode;
  /** Lo que va fijo abajo: el botón que confirma. */
  pie?: ReactNode;
}

export function Hoja({ abierta, alCerrar, titulo, children, pie }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const id = useId();

  useEffect(() => {
    const dialogo = ref.current;
    if (!dialogo) return;
    if (abierta && !dialogo.open) {
      if (typeof dialogo.showModal === "function") dialogo.showModal();
      else dialogo.setAttribute("open", "");
    } else if (!abierta && dialogo.open) {
      if (typeof dialogo.close === "function") dialogo.close();
      else dialogo.removeAttribute("open");
    }
  }, [abierta]);

  return (
    // biome-ignore lint/a11y/useKeyWithClickEvents: con teclado se cierra con Escape (el «cancel» del diálogo) o con su botón
    <dialog
      ref={ref}
      className="hoja"
      aria-labelledby={id}
      onClose={alCerrar}
      onCancel={(evento) => {
        evento.preventDefault();
        alCerrar();
      }}
      // Un toque fuera de la hoja (en el velo) la cierra.
      onClick={(evento) => {
        if (evento.target === ref.current) alCerrar();
      }}
    >
      {abierta ? (
        <>
          <div className="hoja__cabeza">
            <h2 id={id} className="hoja__titulo">
              {titulo}
            </h2>
            <button
              type="button"
              className="boton boton--icono hoja__cerrar"
              aria-label="Cerrar"
              onClick={alCerrar}
            >
              <Icono nombre="cerrar" />
            </button>
          </div>
          <div className="hoja__cuerpo">{children}</div>
          {pie ? <div className="hoja__pie">{pie}</div> : null}
        </>
      ) : null}
    </dialog>
  );
}

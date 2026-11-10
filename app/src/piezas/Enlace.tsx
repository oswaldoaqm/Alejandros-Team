// Un enlace a otra pantalla de la app: es un <a> de verdad (se puede abrir en otra pestaña o
// copiar), pero un clic normal cambia de pantalla sin recargar.

import type { AnchorHTMLAttributes, MouseEvent } from "react";
import { useApp } from "../estado/contexto";
import { vinoDeLaApp } from "../estado/navegacion";

interface Props extends AnchorHTMLAttributes<HTMLAnchorElement> {
  href: string;
  reemplazar?: boolean;
  conservarPosicion?: boolean;
  /** Un enlace de «volver»: si se llegó desde la app, retrocede y deja la pantalla anterior como estaba. */
  volver?: boolean;
}

export function Enlace({ href, reemplazar, conservarPosicion, volver, onClick, children, ...resto }: Props) {
  const { navegar } = useApp();
  const alHacerClic = (evento: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(evento);
    const conTecla = evento.metaKey || evento.ctrlKey || evento.shiftKey || evento.altKey;
    if (evento.defaultPrevented || evento.button !== 0 || conTecla) return;
    evento.preventDefault();
    if (volver && vinoDeLaApp()) window.history.back();
    else navegar(href, { reemplazar, conservarPosicion });
  };
  return (
    <a href={href} onClick={alHacerClic} {...resto}>
      {children}
    </a>
  );
}

/** Un enlace que sale de la app. Solo acepta http y https: lo demás no se enlaza. */
export function EnlaceExterno({ href, children, ...resto }: AnchorHTMLAttributes<HTMLAnchorElement>) {
  const seguro = typeof href === "string" && /^https?:\/\//i.test(href);
  if (!seguro) return <span>{children}</span>;
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" {...resto}>
      {children}
    </a>
  );
}

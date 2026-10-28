// El movimiento en pantalla, con respeto por quien pidió a su sistema que no lo haya.

/** Si la persona prefiere que las cosas no se muevan (ajuste de accesibilidad del sistema). */
export function sinMovimiento(): boolean {
  return (
    typeof window.matchMedia === "function" && window.matchMedia("(prefers-reduced-motion: reduce)").matches
  );
}

/** Lleva la vista hasta un elemento: suave, salvo que se haya pedido sin movimiento. */
export function llevarA(elemento: Element | null | undefined, donde: ScrollLogicalPosition): void {
  elemento?.scrollIntoView({ behavior: sinMovimiento() ? "auto" : "smooth", block: donde });
}

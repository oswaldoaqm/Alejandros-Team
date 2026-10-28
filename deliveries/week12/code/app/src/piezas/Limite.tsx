// Si una parte de la pantalla falla (el mapa que no llega a descargarse, por ejemplo), se
// muestra un aviso en su lugar y el resto sigue funcionando.

import { Component, type ErrorInfo, type ReactNode } from "react";

interface Props {
  /** Qué mostrar en lugar de lo que falló. */
  respaldo: ReactNode;
  children: ReactNode;
}

export class Limite extends Component<Props, { fallo: boolean }> {
  override state = { fallo: false };

  static getDerivedStateFromError(): { fallo: boolean } {
    return { fallo: true };
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.warn("Una parte de la pantalla falló:", error.message, info.componentStack);
  }

  override render(): ReactNode {
    return this.state.fallo ? this.props.respaldo : this.props.children;
  }
}

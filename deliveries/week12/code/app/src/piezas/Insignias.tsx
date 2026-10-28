// El veredicto del mes, como etiqueta corta. El estado nunca va solo en el color: siempre
// lleva su ícono y su palabra.

import type { Veredicto as TipoVeredicto } from "../api/tipos";
import { Icono, type NombreDeIcono } from "./Icono";

const VEREDICTO: Record<TipoVeredicto, { icono: NombreDeIcono; texto: string }> = {
  viable: { icono: "bien", texto: "Buen mes" },
  advertencia: { icono: "aviso", texto: "Mes con advertencia" },
  desaconsejado: { icono: "critico", texto: "Mes desaconsejado" },
};

export function Veredicto({ veredicto }: { veredicto: TipoVeredicto }) {
  const { icono, texto } = VEREDICTO[veredicto];
  return (
    <span className={`insignia insignia--${veredicto}`}>
      <Icono nombre={icono} tamano={15} />
      {texto}
    </span>
  );
}

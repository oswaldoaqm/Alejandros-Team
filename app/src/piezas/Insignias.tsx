// Etiquetas cortas: el veredicto del mes, la jerarquía de una parada, con qué se viaja.
// El estado nunca va solo en el color: siempre lleva su ícono y su palabra.

import type { Medio, Veredicto as TipoVeredicto } from "../api/tipos";
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

export function Jerarquia({ valor }: { valor: number | null | undefined }) {
  if (valor == null) {
    return (
      <span className="jerarquia jerarquia--sin" title="MINCETUR no le asignó jerarquía">
        Sin jerarquía
      </span>
    );
  }
  return (
    <span className="jerarquia" title={`Jerarquía ${valor} de 4 según MINCETUR`}>
      <span aria-hidden="true">J{valor}</span>
      <span className="solo-lector">Jerarquía {valor} de 4</span>
    </span>
  );
}

const MEDIO: Record<Medio, { icono: NombreDeIcono; texto: string }> = {
  carretera: { icono: "carretera", texto: "Por carretera" },
  tren: { icono: "tren", texto: "En tren" },
  bote: { icono: "bote", texto: "En bote" },
};

/** Con qué se hace la ida. Solo se muestra lo que no es carretera: es lo que hay que saber. */
export function Medios({ medios }: { medios: Medio[] }) {
  const especiales = medios.filter((m) => m !== "carretera");
  return (
    <>
      {especiales.map((m) => (
        <span key={m} className="insignia insignia--medio">
          <Icono nombre={MEDIO[m].icono} tamano={15} />
          {MEDIO[m].texto}
        </span>
      ))}
    </>
  );
}

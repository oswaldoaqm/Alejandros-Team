// Íconos de trazo, dibujados aquí para no cargar una librería. Son decorativos: el texto de
// al lado dice lo mismo, así que van ocultos para los lectores de pantalla.

export const TRAZOS = {
  bien: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "m8.5 12.3 2.4 2.4 4.8-5.2"],
  aviso: ["M12 4 2.8 19.5h18.4L12 4Z", "M12 10v4.5", "M12 17.2v.3"],
  critico: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "m9 9 6 6", "m15 9-6 6"],
  info: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M12 11v5.5", "M12 7.6v.3"],
  carretera: [
    "M5 16.5V7a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v9.5",
    "M4 16.5h16",
    "M5 11h14",
    "M7.5 16.5V19",
    "M16.5 16.5V19",
  ],
  tren: [
    "M7 4h10a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2Z",
    "M5 11h14",
    "m8 17-2 3",
    "m16 17 2 3",
    "M9 14h.01",
    "M15 14h.01",
  ],
  bote: ["M3 14h18l-2.5 5h-13L3 14Z", "M12 14V4", "M12 5l6 6h-6"],
  compartir: ["M12 15V4", "m8 8 4-4 4 4", "M5 13v5a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-5"],
  guardar: ["M7 4h10a1 1 0 0 1 1 1v15l-6-4-6 4V5a1 1 0 0 1 1-1Z"],
  imprimir: [
    "M7 9V4h10v5",
    "M7 17H5a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-2",
    "M7 14h10v6H7z",
  ],
  externo: ["M14 5h5v5", "m19 5-8 8", "M18 14v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h4"],
  mas: ["M12 5v14", "M5 12h14"],
  menos: ["M5 12h14"],
  flecha: ["m9 6 6 6-6 6"],
  atras: ["M19 12H5", "m11 6-6 6 6 6"],
  cerrar: ["m6 6 12 12", "m18 6-12 12"],
  editar: ["M4 20h4L19 9l-4-4L4 16v4Z", "m13.5 6.5 4 4"],
  cama: [
    "M3 18V7",
    "M3 14h18v4",
    "M21 14v-2a3 3 0 0 0-3-3h-7v5",
    "M7 11.5a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3Z",
  ],
  calendario: [
    "M5 6h14a1 1 0 0 1 1 1v12a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1Z",
    "M4 10h16",
    "M8 4v4",
    "M16 4v4",
  ],
  pin: [
    "M12 21s6.5-5.6 6.5-11a6.5 6.5 0 1 0-13 0C5.5 15.4 12 21 12 21Z",
    "M12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z",
  ],
  copiar: ["M9 9h10v11H9z", "M5 15V4h10"],
  borrar: ["M5 7h14", "M9 7V4h6v3", "M7 7l1 13h8l1-13"],
  estrella: ["m12 3.6 2.6 5.3 5.8.8-4.2 4.1 1 5.8-5.2-2.7-5.2 2.7 1-5.8-4.2-4.1 5.8-.8L12 3.6Z"],
  ajustes: ["M4 7h9", "M17 7h3", "M15 5v4", "M4 17h3", "M11 17h9", "M9 15v4"],
  lupa: ["M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z", "m20 20-4-4"],
  bus: [
    "M6 4h12a2 2 0 0 1 2 2v11H4V6a2 2 0 0 1 2-2Z",
    "M4 12h16",
    "M7 20v-3",
    "M17 20v-3",
    "M8 14.5h.01",
    "M16 14.5h.01",
  ],
  sol: [
    "M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z",
    "M12 2.5v2",
    "M12 19.5v2",
    "m4.6 4.6 1.4 1.4",
    "m18 18 1.4 1.4",
    "M2.5 12h2",
    "M19.5 12h2",
    "m4.6 19.4 1.4-1.4",
    "m18 6 1.4-1.4",
  ],
  lluvia: [
    "M7 14.5a4 4 0 0 1 .4-8A5.5 5.5 0 0 1 18 8a3.3 3.3 0 0 1-.5 6.5H7Z",
    "m8 18-1 2",
    "m12 18-1 2",
    "m16 18-1 2",
  ],
  montana: ["M2.5 19 9 8l4 6.5L15.5 11l6 8h-19Z", "m7.6 10.4 1.4 1.3 1.6-1.3"],
  reloj: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "M12 7v5l3.2 2"],
  billete: ["M3 7h18v10H3z", "M12 14.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5Z", "M6.5 10v4", "M17.5 10v4"],
  corazon: ["M12 20s-7.5-4.6-9.2-9.4A4.9 4.9 0 0 1 12 6.6a4.9 4.9 0 0 1 9.2 4C19.5 15.4 12 20 12 20Z"],
  abajo: ["m6 9 6 6 6-6"],
  flor: [
    "M12 12c-1.6-2.4-1.6-5.6 0-8.5 1.6 2.9 1.6 6.1 0 8.5Z",
    "M12 12c2.7-1 5.9-.1 8.1 2.4-3.1.9-6.2.1-8.1-2.4Z",
    "M12 12c.3 2.9-1.4 5.7-4.3 7.2-.5-3.2 1.2-6 4.3-7.2Z",
    "M12 12c-2.9.1-5.6-1.7-6.9-4.6 3.2-.4 5.9 1.4 6.9 4.6Z",
    "M12 12c1.9-2.2 5-3 8-2.1-1.8 2.6-4.9 3.5-8 2.1Z",
  ],
  naturaleza: ["M5 19c0-9 6-14 14-14 0 8-5 14-14 14Z", "M5 19l8.5-8.5"],
  historia: [
    "M4 20h16",
    "M5 17h14",
    "M6.5 17V10",
    "M10 17V10",
    "M14 17V10",
    "M17.5 17V10",
    "M3.5 10h17L12 4.5 3.5 10Z",
  ],
  gastronomia: ["M7 3v18", "M4.5 3v5a2.5 2.5 0 0 0 5 0V3", "M17 21V3c-2.2 1.5-3.2 4-3.2 7.5H17"],
  caminatas: [
    "M8 11c-1.4 0-2.4-2-2.4-4.4S6.6 2.5 8 2.5s2.4 1.7 2.4 4.1S9.4 11 8 11Z",
    "M6 13.5h4V16a2 2 0 0 1-4 0v-2.5Z",
    "M16 15c-1.4 0-2.4-2-2.4-4.4S14.6 6.5 16 6.5s2.4 1.7 2.4 4.1S17.4 15 16 15Z",
    "M14 17.5h4V20a2 2 0 0 1-4 0v-2.5Z",
  ],
  playa: [
    "M3 16c2 0 2-1.5 4.5-1.5S10 16 12 16s2-1.5 4.5-1.5S19 16 21 16",
    "M3 20c2 0 2-1.5 4.5-1.5S10 20 12 20s2-1.5 4.5-1.5S19 20 21 20",
    "M15 8a3 3 0 1 0 6 0 3 3 0 0 0-6 0Z",
  ],
  fiestas: ["M9 18V6l11-2v12", "M9 18a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z", "M20 16a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"],
  arquitectura: ["M4 21h16", "M6 21V10l6-6 6 6v11", "M10 21v-5h4v5", "M12 7.5v2.5"],
  aventura: ["M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z", "m15.5 8.5-2 5-5 2 2-5 5-2Z"],
} as const;

export type NombreDeIcono = keyof typeof TRAZOS;

export function Icono({
  nombre,
  tamano = 18,
  relleno = false,
}: {
  nombre: NombreDeIcono;
  tamano?: number;
  /** Relleno con el color del texto: la estrella de los imperdibles. */
  relleno?: boolean;
}) {
  return (
    <svg
      className="icono"
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill={relleno ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
    >
      {TRAZOS[nombre].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  );
}

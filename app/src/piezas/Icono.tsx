// Íconos de trazo, dibujados aquí para no cargar una librería. Son decorativos: el texto de
// al lado dice lo mismo, así que van ocultos para los lectores de pantalla.

const TRAZOS = {
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
} as const;

export type NombreDeIcono = keyof typeof TRAZOS;

export function Icono({ nombre, tamano = 18 }: { nombre: NombreDeIcono; tamano?: number }) {
  return (
    <svg
      className="icono"
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill="none"
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

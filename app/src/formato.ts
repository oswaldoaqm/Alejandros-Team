// Cómo se escriben números, duraciones y fechas. Sigue a dreemgo/motor/textos.py, para que
// lo que arma la app se lea igual que las frases que ya vienen escritas del motor.

const ESPACIO = "\u00a0"; // espacio que no parte la línea: «1 250», «S/ 80»

export const MESES = [
  "enero",
  "febrero",
  "marzo",
  "abril",
  "mayo",
  "junio",
  "julio",
  "agosto",
  "setiembre",
  "octubre",
  "noviembre",
  "diciembre",
] as const;

export const MESES_CORTOS = [
  "ene",
  "feb",
  "mar",
  "abr",
  "may",
  "jun",
  "jul",
  "ago",
  "set",
  "oct",
  "nov",
  "dic",
] as const;

const DIAS_DE_LA_SEMANA = ["dom", "lun", "mar", "mié", "jue", "vie", "sáb"] as const;

/** El nombre del mes 1 a 12; vacío si no es un mes. */
export function mes(n: number | null | undefined): string {
  return n != null && n >= 1 && n <= 12 ? (MESES[n - 1] ?? "") : "";
}

export function mesCorto(n: number): string {
  return MESES_CORTOS[n - 1] ?? "";
}

export function mayuscula(texto: string): string {
  return texto.charAt(0).toUpperCase() + texto.slice(1);
}

/** 1250 → «1 250». */
export function miles(n: number): string {
  return Math.round(n)
    .toString()
    .replace(/\B(?=(\d{3})+(?!\d))/g, ESPACIO);
}

/** 1250 → «S/ 1 250». */
export function soles(n: number): string {
  return `S/${ESPACIO}${miles(n)}`;
}

/** Un monto que no se redondea, como la tarifa de una ficha: 10 → «S/ 10»; 2.5 → «S/ 2,50». */
export function solesExactos(n: number): string {
  return `S/${ESPACIO}${decimal(n, 2)}`;
}

/** 7.9 → «7,9»; 12 → «12». */
export function decimal(n: number, decimales = 1): string {
  const texto = n.toFixed(decimales).replace(".", ",");
  const [entero = "0", fraccion] = texto.split(",");
  const conMiles = miles(Number(entero));
  return fraccion === undefined || /^0+$/.test(fraccion) ? conMiles : `${conMiles},${fraccion}`;
}

/** Siempre con sus decimales, para comparar en columna: 2 → «2,0»; 1.83 → «1,8». */
export function fijo(n: number, decimales = 1): string {
  return n.toFixed(decimales).replace(".", ",");
}

/** 45 → «45 min»; 120 → «2 h»; 160 → «2 h 40». */
export function duracion(minutos: number): string {
  const m = Math.round(minutos);
  if (m < 60) return `${m}${ESPACIO}min`;
  const h = Math.floor(m / 60);
  const resto = m % 60;
  return resto === 0 ? `${h}${ESPACIO}h` : `${h}${ESPACIO}h${ESPACIO}${String(resto).padStart(2, "0")}`;
}

/** 6.05 horas → «6 h 03». */
export function horas(h: number): string {
  return duracion(h * 60);
}

/** 8.8 → «8,8 km»; 752.7 → «753 km». */
export function km(n: number): string {
  return `${n >= 100 ? miles(n) : decimal(n)}${ESPACIO}km`;
}

export function metros(n: number): string {
  return `${miles(n)}${ESPACIO}m`;
}

export function plural(n: number, uno: string, varios: string): string {
  return `${miles(n)}${ESPACIO}${n === 1 ? uno : varios}`;
}

/** ["a", "b", "c"] → «a, b y c». */
export function lista(cosas: string[], conjuncion = "y"): string {
  const llenas = cosas.filter(Boolean);
  if (llenas.length <= 1) return llenas.join("");
  return `${llenas.slice(0, -1).join(", ")} ${conjuncion} ${llenas[llenas.length - 1]}`;
}

/**
 * Los meses como tramos del calendario, sin importar el orden en que lleguen:
 * [6, 7, 8, 5, 9] → «de mayo a setiembre»; [12, 1, 2] → «de diciembre a febrero».
 */
export function rangosDeMeses(meses: readonly number[]): string {
  const hay = new Set(meses.filter((m) => Number.isInteger(m) && m >= 1 && m <= 12));
  if (hay.size === 0) return "";
  if (hay.size === 12) return "todo el año";
  const siguiente = (m: number) => (m === 12 ? 1 : m + 1);
  const anterior = (m: number) => (m === 1 ? 12 : m - 1);
  // Cada tramo empieza en un mes que no tiene al anterior: así el que cruza diciembre no se parte.
  const inicios = [...hay].filter((m) => !hay.has(anterior(m))).sort((a, b) => a - b);
  const partes = inicios.flatMap((inicio) => {
    let fin = inicio;
    let largo = 1;
    while (hay.has(siguiente(fin))) {
      fin = siguiente(fin);
      largo += 1;
    }
    if (largo === 1) return [mes(inicio)];
    return largo === 2 ? [mes(inicio), mes(fin)] : [`de ${mes(inicio)} a ${mes(fin)}`];
  });
  return lista(partes);
}

/** Una fecha AAAA-MM-DD como día local, sin que la zona horaria la corra un día. */
export function fechaLocal(iso: string): Date | null {
  const partes = /^(\d{4})-(\d{2})-(\d{2})$/.exec(iso);
  if (!partes) return null;
  const fecha = new Date(Number(partes[1]), Number(partes[2]) - 1, Number(partes[3]));
  return Number.isNaN(fecha.getTime()) ? null : fecha;
}

/** Date → AAAA-MM-DD, en hora local. */
export function aIso(fecha: Date): string {
  const mm = String(fecha.getMonth() + 1).padStart(2, "0");
  const dd = String(fecha.getDate()).padStart(2, "0");
  return `${fecha.getFullYear()}-${mm}-${dd}`;
}

/** «2027-07-20» → «20 de julio de 2027»; sin el año si `conAnio` es falso. */
export function fecha(iso: string, conAnio = true): string {
  const f = fechaLocal(iso);
  if (!f) return iso;
  const base = `${f.getDate()} de ${MESES[f.getMonth()]}`;
  return conAnio ? `${base} de ${f.getFullYear()}` : base;
}

/** «2027-07-20» → «mar 20 jul». */
export function fechaCorta(iso: string): string {
  const f = fechaLocal(iso);
  if (!f) return iso;
  return `${DIAS_DE_LA_SEMANA[f.getDay()]} ${f.getDate()} ${MESES_CORTOS[f.getMonth()]}`;
}

/** «16 de julio», «del 24 al 30 de julio», «del 28 de diciembre al 6 de enero». */
export function rangoDeFechas(inicio: string | null | undefined, fin: string | null | undefined): string {
  if (!inicio) return "";
  const a = fechaLocal(inicio);
  const b = fin ? fechaLocal(fin) : null;
  if (!a) return inicio;
  if (!b || b.getTime() === a.getTime()) return `${a.getDate()} de ${MESES[a.getMonth()]}`;
  if (a.getMonth() === b.getMonth() && a.getFullYear() === b.getFullYear()) {
    return `del ${a.getDate()} al ${b.getDate()} de ${MESES[a.getMonth()]}`;
  }
  return `del ${a.getDate()} de ${MESES[a.getMonth()]} al ${b.getDate()} de ${MESES[b.getMonth()]}`;
}

/** La letra de la ruta según su puesto: 0 → «A». */
export function letra(indice: number): string {
  return String.fromCharCode(65 + indice);
}

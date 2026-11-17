// Estadísticas de uso opcionales. Solo salen categorías y tipos de acciones;
// nunca nombres, correos, preguntas, comentarios ni el contenido de los viajes guardados.

import { URL_API } from "./api/cliente";
import { type Consulta, clave } from "./consulta";

export type TipoEvento =
  | "sesion_iniciada"
  | "formulario_abierto"
  | "busqueda_iniciada"
  | "busqueda_resultado"
  | "itinerario_abierto"
  | "viaje_guardado"
  | "viaje_compartido"
  | "viaje_impreso"
  | "ayuda_consultada"
  | "comentario_enviado"
  | "error_consulta";

export interface DatosEvento {
  origen?: string;
  polo?: number;
  intereses?: string[];
  dias?: number;
  mes?: number;
  presupuesto?: number;
  resultados?: number;
  duracion_ms?: number;
  codigo_error?: string;
}

const CLAVE_PERMISO = "dreemgo.analitica.permiso.v1";
const CLAVE_SESION = "dreemgo.analitica.sesion.v1";
export const CAMBIO_PERMISO = "dreemgo:permiso-estadisticas";
let sesionLocal: string | null = null;
let sesionAnotada = false;
const comienzos = new Map<string, number>();

export function estadisticasPermitidas(): boolean {
  try {
    return localStorage.getItem(CLAVE_PERMISO) === "si";
  } catch {
    return false;
  }
}

/** Si no se puede guardar el permiso, no se envía telemetría. */
export function permitirEstadisticas(permitir: boolean): boolean {
  try {
    localStorage.setItem(CLAVE_PERMISO, permitir ? "si" : "no");
  } catch {
    return false;
  }
  if (!permitir) {
    try {
      sessionStorage.removeItem(CLAVE_SESION);
    } catch {
      // El permiso ya se revocó; limpiar la sesión es solo una ayuda adicional.
    }
    sesionLocal = null;
    sesionAnotada = false;
    comienzos.clear();
  }
  window.dispatchEvent(new Event(CAMBIO_PERMISO));
  return true;
}

function sesion(): string | null {
  if (sesionLocal) return sesionLocal;
  try {
    const anterior = sessionStorage.getItem(CLAVE_SESION);
    if (anterior) {
      sesionLocal = anterior;
      return anterior;
    }
    const nueva = crypto.randomUUID();
    sessionStorage.setItem(CLAVE_SESION, nueva);
    sesionLocal = nueva;
    return nueva;
  } catch {
    // Si el navegador no puede crear una sesión anónima, no se envía nada.
    return null;
  }
}

function enviar(tipo: TipoEvento, datos: DatosEvento = {}): boolean {
  if (!estadisticasPermitidas()) return false;
  const id = sesion();
  if (!id) return false;
  try {
    // La apertura de una misma sesión conserva su ID al recargar. El API la deduplica.
    const idEvento = tipo === "sesion_iniciada" ? id : crypto.randomUUID();
    void fetch(`${URL_API}/v1/analitica/eventos`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_evento: idEvento, sesion: id, tipo, ...datos }),
      keepalive: true,
    }).catch(() => undefined);
    return true;
  } catch {
    // Un fallo de analítica no afecta al planificador.
    return false;
  }
}

export function iniciarEstadisticas(): void {
  if (sesionAnotada || !estadisticasPermitidas()) return;
  if (!sesion()) return;
  sesionAnotada = true;
  enviar("sesion_iniciada");
}

export function registrarEvento(tipo: TipoEvento, datos: DatosEvento = {}): boolean {
  if (!estadisticasPermitidas()) return false;
  iniciarEstadisticas();
  return enviar(tipo, datos);
}

export function iniciarMedicionBusqueda(c: Consulta): void {
  if (estadisticasPermitidas()) comienzos.set(clave(c), performance.now());
}

export function duracionBusqueda(c: Consulta): number | undefined {
  const llave = clave(c);
  const desde = comienzos.get(llave);
  comienzos.delete(llave);
  return desde === undefined ? undefined : Math.max(0, Math.round(performance.now() - desde));
}

/** Solo valores estructurados que el formulario ya conoce; omite los campos sin elección. */
export function datosDeConsulta(c: Consulta): DatosEvento {
  return {
    origen: c.origen,
    intereses: c.intereses,
    dias: c.dias,
    ...(c.mes === null ? {} : { mes: c.mes }),
    ...(c.presupuesto === null ? {} : { presupuesto: c.presupuesto }),
    ...(c.destino === null ? {} : { polo: c.destino }),
  };
}

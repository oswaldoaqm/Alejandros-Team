// La versión de datos tiene dos partes: la de los artefactos del motor y, cuando hay eventos
// publicados por los municipios, la huella de ese calendario: «2026.10.2-e3f9a1c».
// Publicar un evento no mueve ninguna ruta (docs/CONTRATO.md §3): si solo cambia la huella,
// el viaje es el mismo.

/** La parte de los artefactos. */
export function artefactosDe(version: string): string {
  return version.replace(/-e[0-9a-f]+$/, "");
}

export type CambioDeVersion = "ninguno" | "eventos" | "datos";

/** Qué cambió entre la versión que trae un enlace y la vigente. */
export function cambioDeVersion(delEnlace: string | null, vigente: string): CambioDeVersion {
  if (delEnlace === null || delEnlace === vigente) return "ninguno";
  return artefactosDe(delEnlace) === artefactosDe(vigente) ? "eventos" : "datos";
}

// La app escribe «S/ 1 250» y «6 días» con espacios que no parten la línea. Para comparar en
// las pruebas sin caracteres invisibles, se pasan a espacios comunes.

export function plano(texto: string | null | undefined): string {
  return (texto ?? "").replaceAll("\u00a0", " ");
}

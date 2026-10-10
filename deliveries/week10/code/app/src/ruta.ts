// Qué pantalla toca según la URL. La consulta va en los parámetros (es el enlace para
// compartir); las demás pantallas van en el fragmento, que GitHub Pages sirve sin configurar nada.

import { aEnlace, type Consulta, deParametros } from "./consulta";

export type Vista =
  | { tipo: "inicio"; consulta: Consulta | null }
  | {
      tipo: "resultados";
      consulta: Consulta;
      version: string | null;
      /** El viaje abierto: 1, 2 o 3. null: la lista de los tres, para comparar. */
      ruta: number | null;
    }
  | { tipo: "polo"; id: number; consulta: Consulta | null }
  | { tipo: "calendario"; consulta: Consulta | null; mes: number | null }
  | { tipo: "mis-viajes" }
  | { tipo: "acerca" }
  | { tipo: "publicar" };

/** La pantalla que corresponde a una URL. */
export function vistaDe(url: URL): Vista {
  const consulta = deParametros(url.searchParams);
  const fragmento = url.hash.replace(/^#\/?/, "");
  const [pagina = "", argumento = ""] = fragmento.split("/");
  switch (pagina) {
    case "editar":
      return { tipo: "inicio", consulta };
    case "polo": {
      const id = Number(argumento);
      if (argumento !== "" && Number.isInteger(id) && id >= 0) return { tipo: "polo", id, consulta };
      break;
    }
    case "calendario": {
      // «#/calendario/11» lo abre en noviembre; sin número, en el mes de la consulta o en el actual.
      const mes = Number(argumento);
      const vale = argumento !== "" && Number.isInteger(mes) && mes >= 1 && mes <= 12;
      return { tipo: "calendario", consulta, mes: vale ? mes : null };
    }
    case "mis-viajes":
      return { tipo: "mis-viajes" };
    case "acerca":
      return { tipo: "acerca" };
    case "publicar":
      return { tipo: "publicar" };
  }
  if (!consulta) return { tipo: "inicio", consulta: null };
  const elegida = pagina === "ruta" ? Number(argumento) : null;
  return {
    tipo: "resultados",
    consulta,
    version: url.searchParams.get("v"),
    ruta: elegida !== null && Number.isInteger(elegida) && elegida >= 1 && elegida <= 3 ? elegida : null,
  };
}

/** El enlace relativo de una pantalla. Con `consulta`, la conserva para poder volver. */
export const enlaces = {
  inicio: () => "./",
  editar: (c: Consulta, version?: string | null) => `${aEnlace(c, version)}#/editar`,
  /** Sin `ruta`, la lista de los tres viajes; con `ruta`, ese viaje abierto. */
  resultados: (c: Consulta, version?: string | null, ruta?: number | null) =>
    `${aEnlace(c, version)}${ruta ? `#/ruta/${ruta}` : ""}`,
  polo: (id: number, c?: Consulta | null, version?: string | null) =>
    `${c ? aEnlace(c, version) : "./"}#/polo/${id}`,
  calendario: (c?: Consulta | null, version?: string | null, mes?: number | null) =>
    `${c ? aEnlace(c, version) : "./"}#/calendario${mes ? `/${mes}` : ""}`,
  misViajes: () => "./#/mis-viajes",
  acerca: () => "./#/acerca",
  publicar: () => "./#/publicar",
};

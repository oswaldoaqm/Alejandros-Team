// Una foto de Wikimedia Commons, del tamaño que pide la pantalla, con su autor y su licencia.
// Si no carga, avisa con `alFallar` y quien la puso muestra otra cosa en su lugar.

import { useState } from "react";
import {
  creditoDeFoto,
  type Foto as DatosDeFoto,
  licenciaDeFoto,
  paginaDeFoto,
  srcsetDeFoto,
  urlDeFoto,
} from "../fotos";
import { EnlaceExterno } from "./Enlace";

/** «Foto: Autora, CC BY-SA 4.0», con la página de la foto y la de su licencia enlazadas. */
export function CreditoDeFoto({ foto }: { foto: DatosDeFoto }) {
  return (
    <>
      <EnlaceExterno
        href={paginaDeFoto(foto)}
        aria-label={`${foto.autor ? `Foto: ${foto.autor}` : "Foto"}, en Wikimedia Commons`}
      >
        {foto.autor ? `Foto: ${foto.autor}` : "Foto"}
      </EnlaceExterno>
      {", "}
      {foto.url_licencia ? (
        <EnlaceExterno href={foto.url_licencia}>{licenciaDeFoto(foto)}</EnlaceExterno>
      ) : (
        licenciaDeFoto(foto)
      )}
    </>
  );
}

interface Props {
  foto: DatosDeFoto;
  /** Qué muestra, para quien no la ve. Vacío si la foto acompaña a un texto que ya lo dice. */
  alt: string;
  /** Qué ancho ocupa en la pantalla (el `sizes` de la imagen). */
  sizes: string;
  /** El ancho más grande que se pide. */
  tope?: number;
  /** La foto principal de la pantalla: se pide antes que todo lo demás. */
  principal?: boolean;
  /** El crédito al pie: enlazado, en texto (dentro de un enlace no puede ir otro) o ninguno, si va aparte. */
  credito?: "enlace" | "texto" | null;
  alFallar?: () => void;
  className?: string;
}

export function Foto({
  foto,
  alt,
  sizes,
  tope = 1280,
  principal = false,
  credito = "enlace",
  alFallar,
  className = "",
}: Props) {
  const [lista, ponerLista] = useState(false);
  return (
    <figure className={`foto${lista ? " foto--lista" : ""} ${className}`}>
      <img
        // Si ya estaba en la memoria del navegador, puede cargar antes de escuchar `onLoad`.
        ref={(img) => {
          if (img?.complete && img.naturalWidth > 0) ponerLista(true);
        }}
        src={urlDeFoto(foto, 500)}
        srcSet={srcsetDeFoto(foto, tope)}
        sizes={sizes}
        alt={alt}
        width={foto.ancho}
        height={foto.alto}
        loading={principal ? "eager" : "lazy"}
        fetchPriority={principal ? "high" : "auto"}
        decoding="async"
        onLoad={() => ponerLista(true)}
        onError={alFallar}
      />
      {credito === "texto" ? <figcaption className="foto__credito">{creditoDeFoto(foto)}</figcaption> : null}
      {credito === "enlace" ? (
        <figcaption className="foto__credito">
          <CreditoDeFoto foto={foto} />
        </figcaption>
      ) : null}
    </figure>
  );
}

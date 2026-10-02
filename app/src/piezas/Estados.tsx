// Cómo se ve la espera y cómo se ve un error, igual en todas las pantallas.

import type { ReactNode } from "react";
import type { ErrorApi } from "../api/cliente";
import { Icono } from "./Icono";

export function Cargando({ texto }: { texto: string }) {
  return (
    <p className="cargando" role="status">
      <span className="cargando__punto" aria-hidden="true" />
      {texto}
    </p>
  );
}

const TITULOS: Record<ErrorApi["tipo"], string> = {
  red: "No hay conexión con el servidor",
  validacion: "Hay algo que corregir en la consulta",
  sin_datos: "El servidor está arrancando",
  no_encontrado: "No lo encontramos",
  sin_permiso: "No tienes permiso",
  servidor: "El servidor tuvo un problema",
};

const CAMPOS: Record<string, string> = {
  origen: "Punto de partida",
  mes: "Mes",
  fecha_inicio: "Fecha de salida",
  dias: "Días",
  intereses: "Intereses",
  presupuesto: "Presupuesto",
  altitud_max: "Altitud máxima",
  desde: "Desde",
  hasta: "Hasta",
};

export function nombreDeCampo(campo: string): string {
  return CAMPOS[campo] ?? CAMPOS[campo.split(".")[0] ?? ""] ?? campo;
}

interface PropsError {
  error: ErrorApi;
  reintentar?: () => void;
  children?: ReactNode;
}

export function ErrorVista({ error, reintentar, children }: PropsError) {
  return (
    <div className="aviso aviso--critico" role="alert">
      <Icono nombre="critico" />
      <div>
        <p className="aviso__titulo">{TITULOS[error.tipo]}</p>
        {error.campos.length > 0 ? (
          <ul className="lista-simple">
            {error.campos.map((c) => (
              <li key={`${c.campo}-${c.mensaje}`}>
                {c.campo ? <strong>{nombreDeCampo(c.campo)}: </strong> : null}
                {c.mensaje}
              </li>
            ))}
          </ul>
        ) : (
          <p>{error.message}</p>
        )}
        <div className="aviso__acciones">
          {reintentar && error.tipo !== "validacion" ? (
            <button type="button" className="boton boton--secundario" onClick={reintentar}>
              Volver a intentar
            </button>
          ) : null}
          {children}
        </div>
      </div>
    </div>
  );
}

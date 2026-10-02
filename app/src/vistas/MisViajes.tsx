// Los viajes guardados en este navegador. Cada uno es su enlace: al abrirlo, el motor lo
// vuelve a calcular con la misma consulta.

import { useState } from "react";
import { borrarViaje, leerViajes, type ViajeGuardado } from "../almacen";
import { clave } from "../consulta";
import { useTitulo } from "../estado/titulo";
import { aIso, fecha, mayuscula } from "../formato";
import { Enlace } from "../piezas/Enlace";
import { Icono } from "../piezas/Icono";
import { enlaces } from "../ruta";

function cuando(viaje: ViajeGuardado): string {
  const dia = new Date(viaje.guardado);
  return Number.isNaN(dia.getTime()) ? "" : `Guardado el ${fecha(aIso(dia))}`;
}

export function MisViajes() {
  const [viajes, ponerViajes] = useState(leerViajes);
  const [aviso, ponerAviso] = useState("");
  useTitulo("Mis viajes");

  const quitar = (viaje: ViajeGuardado) => {
    borrarViaje(viaje.consulta);
    ponerViajes(leerViajes());
    ponerAviso(`Quitamos «${viaje.titulo}».`);
  };

  return (
    <section className="pagina pagina--angosta">
      <h1 tabIndex={-1}>Mis viajes</h1>
      <p className="bajada">
        Los viajes que guardaste en este navegador. No hay cuentas: nada de esto sale de tu dispositivo, y si
        borras los datos del navegador se van con ellos.
      </p>
      <p className="solo-lector" role="status">
        {aviso}
      </p>
      {viajes.length === 0 ? (
        <div className="vacio">
          <p>Todavía no guardaste ningún viaje. En la pantalla de rutas, toca «Guardar».</p>
          <Enlace href={enlaces.inicio()} className="boton boton--primario">
            Armar un viaje
          </Enlace>
        </div>
      ) : (
        <ul className="viajes">
          {viajes.map((viaje) => (
            <li key={clave(viaje.consulta)} className="viaje">
              <Enlace href={enlaces.resultados(viaje.consulta, viaje.version)} className="viaje__enlace">
                <span className="viaje__titulo">{mayuscula(viaje.titulo)}</span>
                <span className="viaje__meta">
                  {[cuando(viaje), viaje.version ? `datos ${viaje.version}` : ""].filter(Boolean).join(" · ")}
                </span>
              </Enlace>
              <button
                type="button"
                className="boton boton--icono"
                aria-label={`Quitar ${viaje.titulo}`}
                onClick={() => quitar(viaje)}
              >
                <Icono nombre="borrar" />
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

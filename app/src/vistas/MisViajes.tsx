// Los viajes guardados en este navegador. Cada uno es su enlace: al abrirlo, el motor lo vuelve
// a calcular con la misma consulta. No hay cuentas: nada de esto sale del dispositivo.

import { useState } from "react";
import { borrarViaje, leerViajes, type ViajeGuardado } from "../almacen";
import { clave, detalles, titulo } from "../consulta";
import { useApp } from "../estado/contexto";
import { useTitulo } from "../estado/titulo";
import { aIso, fecha } from "../formato";
import { Enlace } from "../piezas/Enlace";
import { Icono } from "../piezas/Icono";
import { enlaces } from "../ruta";

function cuando(viaje: ViajeGuardado): string {
  const dia = new Date(viaje.guardado);
  return Number.isNaN(dia.getTime()) ? "" : `Guardado el ${fecha(aIso(dia))}`;
}

export function MisViajes() {
  const { nombres } = useApp();
  const [viajes, ponerViajes] = useState(leerViajes);
  const [aviso, ponerAviso] = useState("");
  useTitulo("Guardados");

  const quitar = (viaje: ViajeGuardado, nombre: string) => {
    borrarViaje(viaje.consulta);
    ponerViajes(leerViajes());
    ponerAviso(`Quitamos «${nombre}» de Guardados.`);
  };

  return (
    <section className="pagina pagina--angosta guardados-pagina">
      <h1 tabIndex={-1} className="pagina__titulo">
        Guardados
      </h1>
      <p className="pagina__bajada">
        Los viajes que guardaste en este navegador. No hay cuentas: nada sale de tu dispositivo, y si borras
        los datos del navegador, se borran con ellos.
      </p>
      <p className="solo-lector" role="status">
        {aviso}
      </p>
      {viajes.length === 0 ? (
        <div className="vacio-viajes">
          <h2>Todavía no guardaste ningún viaje</h2>
          <p>Abre uno de tus viajes y toca «Guardar»: queda aquí para volver a él.</p>
          <Enlace href={enlaces.inicio()} className="boton boton--primario">
            Armar un viaje
          </Enlace>
        </div>
      ) : (
        <ul className="guardados">
          {viajes.map((viaje) => {
            const nombre = titulo(viaje.consulta, nombres);
            const mas = detalles(viaje.consulta, nombres);
            return (
              <li key={clave(viaje.consulta)} className="guardado">
                <Enlace href={enlaces.resultados(viaje.consulta, viaje.version)} className="guardado__enlace">
                  <span className="guardado__titulo">{nombre}</span>
                  {mas ? <span className="guardado__detalle">{mas}</span> : null}
                  <span className="guardado__meta">{cuando(viaje)}</span>
                </Enlace>
                <button
                  type="button"
                  className="boton boton--icono guardado__quitar"
                  aria-label={`Quitar ${nombre}`}
                  onClick={() => quitar(viaje, nombre)}
                >
                  <Icono nombre="borrar" />
                </button>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}

// Los modelos del contrato con nombres cortos. Salen de esquema.d.ts, que se genera del
// OpenAPI del API (npm run tipos): un campo que no está en el contrato no existe aquí.
import type { components } from "./esquema";

type Modelo = components["schemas"];

export type Aviso = Modelo["Aviso"];
export type Costo = Modelo["Costo"];
export type Dia = Modelo["Dia"];
export type Estacionalidad = Modelo["Estacionalidad"];
export type Evento = Modelo["Evento"];
export type EventoNuevo = Modelo["EventoNuevo"];
export type Eventos = Modelo["Eventos"];
export type Indicadores = Modelo["Indicadores"];
export type Interes = Modelo["Interes"];
export type Opciones = Modelo["Opciones"];
export type Parada = Modelo["Parada"];
export type Polo = Modelo["Polo"];
export type PoloDetalle = Modelo["PoloDetalle"];
export type Recurso = Modelo["Recurso"];
export type Respuesta = Modelo["Respuesta"];
export type Ruta = Modelo["Ruta"];
export type Salud = Modelo["Salud"];
export type SinResultado = Modelo["SinResultado"];
export type Sugerencia = Modelo["Sugerencia"];
export type Traslado = Modelo["Traslado"];

export type Veredicto = Estacionalidad["veredicto"];
export type Medio = NonNullable<Traslado["medios"]>[number];

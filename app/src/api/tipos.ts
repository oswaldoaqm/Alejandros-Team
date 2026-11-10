// Los modelos del contrato con nombres cortos. Salen de esquema.d.ts, que se genera del
// OpenAPI del API (npm run tipos): un campo que no está en el contrato no existe aquí.
import type { components } from "./esquema";

type Modelo = components["schemas"];

export type Almuerzo = Modelo["Almuerzo"];
export type Aviso = Modelo["Aviso"];
export type BusDeNoche = Modelo["BusDeNoche"];
export type Cielo = Modelo["Cielo"];
export type CieloDeLaZona = Modelo["CieloDeLaZona"];
export type Costo = Modelo["Costo"];
export type Dia = Modelo["Dia"];
export type Estacionalidad = Modelo["Estacionalidad"];
export type Evento = Modelo["Evento"];
export type EventoNuevo = Modelo["EventoNuevo"];
export type Eventos = Modelo["Eventos"];
export type Indicadores = Modelo["Indicadores"];
export type Interes = Modelo["Interes"];
export type LugarDeEstrellas = Modelo["LugarDeEstrellas"];
export type LugarDeNoche = Modelo["LugarDeNoche"];
export type Luna = Modelo["Luna"];
export type Noche = Modelo["Noche"];
export type NocheDeLaZona = Modelo["NocheDeLaZona"];
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
export type TramoAereo = Modelo["TramoAereo"];

export type Veredicto = Estacionalidad["veredicto"];
export type Medio = NonNullable<Traslado["medios"]>[number];

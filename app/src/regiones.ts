// Las 25 regiones del país, cada una con su ciudad principal: al elegir la región, el mapa de
// «Publicar un evento» se acerca ahí. Las ciudades y sus coordenadas son las de
// pipeline/referencia/origenes.csv, más el Callao. Quien decide si una región vale es el API,
// que la compara con el inventario: esta lista solo ahorra escribirla.

export interface Region {
  nombre: string;
  ciudad: string;
  lat: number;
  lon: number;
}

export const REGIONES: readonly Region[] = [
  { nombre: "Amazonas", ciudad: "Chachapoyas", lat: -6.2294, lon: -77.8728 },
  { nombre: "Áncash", ciudad: "Huaraz", lat: -9.5278, lon: -77.5278 },
  { nombre: "Apurímac", ciudad: "Abancay", lat: -13.6339, lon: -72.8814 },
  { nombre: "Arequipa", ciudad: "Arequipa", lat: -16.3989, lon: -71.535 },
  { nombre: "Ayacucho", ciudad: "Ayacucho", lat: -13.1588, lon: -74.2239 },
  { nombre: "Cajamarca", ciudad: "Cajamarca", lat: -7.1638, lon: -78.5003 },
  { nombre: "Callao", ciudad: "Callao", lat: -12.0566, lon: -77.1181 },
  { nombre: "Cusco", ciudad: "Cusco", lat: -13.5226, lon: -71.9673 },
  { nombre: "Huancavelica", ciudad: "Huancavelica", lat: -12.7826, lon: -74.9727 },
  { nombre: "Huánuco", ciudad: "Huánuco", lat: -9.9306, lon: -76.2422 },
  { nombre: "Ica", ciudad: "Ica", lat: -14.0678, lon: -75.7286 },
  { nombre: "Junín", ciudad: "Huancayo", lat: -12.0651, lon: -75.2049 },
  { nombre: "La Libertad", ciudad: "Trujillo", lat: -8.1091, lon: -79.0215 },
  { nombre: "Lambayeque", ciudad: "Chiclayo", lat: -6.7714, lon: -79.8409 },
  { nombre: "Lima", ciudad: "Lima", lat: -12.0464, lon: -77.0282 },
  { nombre: "Loreto", ciudad: "Iquitos", lat: -3.7491, lon: -73.2443 },
  { nombre: "Madre de Dios", ciudad: "Puerto Maldonado", lat: -12.5933, lon: -69.1836 },
  { nombre: "Moquegua", ciudad: "Moquegua", lat: -17.1983, lon: -70.9357 },
  { nombre: "Pasco", ciudad: "Cerro de Pasco", lat: -10.6675, lon: -76.2567 },
  { nombre: "Piura", ciudad: "Piura", lat: -5.1945, lon: -80.6328 },
  { nombre: "Puno", ciudad: "Puno", lat: -15.8402, lon: -70.0219 },
  { nombre: "San Martín", ciudad: "Tarapoto", lat: -6.4878, lon: -76.3597 },
  { nombre: "Tacna", ciudad: "Tacna", lat: -18.0146, lon: -70.2536 },
  { nombre: "Tumbes", ciudad: "Tumbes", lat: -3.5669, lon: -80.4515 },
  { nombre: "Ucayali", ciudad: "Pucallpa", lat: -8.3791, lon: -74.5539 },
];

/** Los límites del país que acepta el contrato para la ubicación de un evento. */
export const PERU = { latMin: -18.4, latMax: 0.1, lonMin: -81.4, lonMax: -68.6 } as const;

export function dentroDelPeru(lat: number, lon: number): boolean {
  return lat >= PERU.latMin && lat <= PERU.latMax && lon >= PERU.lonMin && lon <= PERU.lonMax;
}

// node --test tests/tablero_finanzas.test.cjs
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const html = fs.readFileSync(path.join(__dirname, '../app/public/tablero-gerencial.html'), 'utf8');
const codigo = html.match(/<script id="calculos-tablero">([\s\S]*?)<\/script>/)[1];
const contexto = {module: {exports: {}}};
vm.runInNewContext(codigo, contexto);
const {finanzas, razon, notaSesiones, urlViajes, crearCSV} = contexto.module.exports;
const instantanea=JSON.parse(html.match(/<script id="datos-iniciales" type="application\/json">([\s\S]*?)<\/script>/)[1]);

test('escenario inicial: sin confundir costos e ingresos', () => {
  const f = finanzas(200,20,5,500,300,10);
  assert.equal(f.operaciones,20);
  assert.equal(f.ingresos,400);
  assert.equal(f.costoVariable,100);
  assert.equal(f.costos,900);
  assert.equal(f.resultado,-500);
  assert.equal(f.margen,-1.25);
  assert.equal(f.equilibrio,54);
  assert.equal(f.roi,-500/900);
});
test('denominadores cero se presentan sin dato', () => {
  const f = finanzas(0,20,5,0,0,10);
  assert.equal(f.margen,null);
  assert.equal(f.roi,null);
  assert.equal(razon(5,0),null);
  assert.equal(razon(null,200),null);
  assert.equal(razon(NaN,200),null);
  assert.equal(razon(100,Infinity),null);
});
test('margen unitario no positivo no promete equilibrio', () => {
  assert.equal(finanzas(200,5,5,500,300,10).equilibrio,null);
  assert.equal(finanzas(200,4,5,500,300,10).equilibrio,null);
});
test('los cambios de supuestos recalculan operaciones y resultado', () => {
  const f = finanzas(200,50,5,100,100,20);
  assert.equal(f.operaciones,40);
  assert.equal(f.ingresos,2000);
  assert.equal(f.costos,400);
  assert.equal(f.resultado,1600);
});
test('se rechazan supuestos imposibles', () => {
  for(const args of [[200,-1,5,0,0,10],[200,20,5,0,0,101],[200,20,NaN,0,0,10]]) {
    assert.throws(()=>finanzas(...args));
  }
});
test('el archivo lleva el escenario200 y contrato de gráficas', () => {
  assert.equal(instantanea.modo,'simulacion');
  assert.equal(instantanea.indicadores.find(i=>i.id==='sesiones').valor,200);
  assert.equal(instantanea.analisis.mapa_calor.length,168);
  assert.equal(instantanea.analisis.proyeccion.futuro.length,7);
});
test('los textos de sesiones distinguen simulación de actividad real', () => {
  assert.match(notaSesiones('simulacion'), /ficticio/);
  assert.equal(notaSesiones('actividad'), 'Sesiones anónimas con actividad; no personas únicas');
});
test('el enlace de viajes conserva el origen servido y tiene alternativa local', () => {
  assert.equal(urlViajes({protocol:'http:',origin:'http://localhost:5174'}), 'http://localhost:5174/');
  assert.equal(urlViajes({protocol:'https:',origin:'https://ejemplo.test'}), 'https://ejemplo.test/');
  assert.equal(urlViajes({protocol:'file:',origin:'null'}), 'http://localhost:5173/');
});
test('CSV contiene solo 22 indicadores de la fuente y periodo, sin secretos', () => {
  const csv=crearCSV({...instantanea,clave:'secreto-que-no-se-exporta'});
  assert.equal(csv.split('\r\n').length,23);
  assert.match(csv, /"simulacion";"2026-10-14";"2026-11-10";"sesiones";"Sesiones";"200"/);
  assert.ok(!csv.includes('secreto-que-no-se-exporta'));
  for(const indicador of instantanea.indicadores) assert.ok(csv.includes('"'+indicador.id+'"'));
});
test('CSV conserva decimales, escapa texto y evita fórmulas de etiquetas', () => {
  const csv=crearCSV({modo:'actividad',periodo:{desde:null,hasta:null},indicadores:[
    {id:'prueba',etiqueta:'=HYPERLINK("x")',valor:-12.5,unidad:'%',descripcion:'Texto; con "comillas"'}
  ]});
  assert.match(csv, /"'=HYPERLINK\(""x""\)"/);
  assert.match(csv, /"-12.5"/);
  assert.match(csv, /"Texto; con ""comillas"""/);
});
test('CSV incluye supuestos y resultados financieros actuales sin mezclarlos con uso', () => {
  const csv=crearCSV(instantanea,[20,5,500,300,20]);
  assert.equal(csv.split('\r\n').length,37);
  assert.match(csv, /"Escenario hipotético \(base: simulacion\)";"2026-10-14";"2026-11-10"/);
  assert.match(csv, /"escenario_conversion";"Conversión comercial supuesta";"20";"%"/);
  assert.match(csv, /"escenario_operaciones";"Operaciones estimadas";"40"/);
  assert.match(csv, /"escenario_resultado";"Resultado del escenario";"-200"/);
  assert.match(csv, /"simulacion";"2026-10-14";"2026-11-10";"sesiones";"Sesiones";"200"/);
});
test('todos los scripts del tablero tienen sintaxis válida', () => {
  for(const bloque of html.matchAll(/<script([^>]*)>([\s\S]*?)<\/script>/g)) {
    if(!bloque[1].includes('application/json')) new vm.Script(bloque[2]);
  }
});

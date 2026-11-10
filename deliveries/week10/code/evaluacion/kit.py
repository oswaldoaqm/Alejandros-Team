"""
El kit para que el equipo califique los viajes de las 40 consultas (semana 12, decisión 0021).

Por cada consulta de ``consultas.csv`` junta las zonas que proponen el motor, la guía (la línea de base,
``linea_base.py``) y la variante (``variante.py``): de tres a seis opciones, porque una zona que proponen
varios va una sola vez, con el viaje que le arma el motor. Las mezcla en un orden fijo que no dice de dónde
sale cada una y escribe en data/evaluacion/:

  cuadernillo.html   las consultas con sus opciones, para calificar en el navegador: guarda el avance y
                     descarga las calificaciones en un CSV. También se imprime
  planilla.csv       lo mismo para llenar en una hoja de cálculo, para quien la prefiera
  clave.csv          de dónde sale cada opción: el puesto que le da cada sistema. Es para el análisis
                     (``informe.py``); quien califica no lo abre

Las calificaciones son 2 (se lo recomendaría tal cual), 1 (podría servirle, con reparos) o 0 (no encaja),
como explica docs/evaluacion/anotar.md. Lo mismo con los mismos datos da siempre los mismos archivos.

Uso:  python -m evaluacion.kit
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import random
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from dreemgo.contrato import ETIQUETAS_INTERES, VERSION_CONTRATO, Consulta, Ruta
from dreemgo.motor import datos as artefactos
from dreemgo.motor import textos, viaje
from dreemgo.motor.datos import Datos
from evaluacion import consultas, linea_base, variante

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "evaluacion"
LETRAS = "ABCDEFGHI"  # tres sistemas con tres zonas cada uno, sin ninguna en común
SEMILLA = "dreemgo-semana-12"  # el orden de las opciones de cada consulta sale de aquí y de su número
COLUMNAS = ["consulta", "opcion", "zona", "calificacion", "comentario"]
CALIFICACIONES = (("2", "Sí, tal cual"), ("1", "Puede servirle, con reparos"), ("0", "No encaja"))
VEREDICTO = {"viable": "Buen mes", "advertencia": "Mes con advertencia", "desaconsejado": "Mes desaconsejado"}
# Lo que la tarjeta ya dice por otro lado: el mes, el presupuesto y, en el acceso, cómo se va.
YA_DICHOS = {"estacionalidad", "presupuesto"}
COMO_SE_VA = "La ida y la vuelta van en"


@dataclass(frozen=True)
class Opcion:
    letra: str
    ruta: Ruta
    puestos: dict[str, int]  # el puesto que le da cada sistema que la propone, de 1 a 3


def _del_motor(consulta: Consulta, datos: Datos) -> list[int]:
    return [r.polo.id for r in viaje.resolver(consulta, datos, sugerir=False).rutas]


# Lo que se compara: el motor desplegado, la guía (la línea de base) y la variante con más peso para lo que
# se pidió. Cada uno da hasta tres zonas, en su orden.
SISTEMAS: dict[str, Callable[[Consulta, Datos], list[int]]] = {
    "motor": _del_motor,
    "guia": linea_base.zonas,
    "variante": variante.zonas,
}


def opciones(id_consulta: int, consulta: Consulta, datos: Datos) -> list[Opcion]:
    """Las zonas que propone cada sistema, una vez cada una, en un orden que no dice de dónde sale. El viaje
    a una zona es el mismo la proponga quien la proponga: el del motor desplegado."""
    puestos: dict[int, dict[str, int]] = {}
    for nombre, proponer in SISTEMAS.items():
        for n, polo in enumerate(proponer(consulta, datos), 1):
            puestos.setdefault(polo, {})[nombre] = n
    del_motor = {r.polo.id: r for r in viaje.resolver(consulta, datos, sugerir=False).rutas}
    orden = sorted(puestos)
    random.Random(f"{SEMILLA}-{id_consulta}").shuffle(orden)
    return [
        Opcion(LETRAS[k], del_motor.get(polo) or linea_base.viaje_a(polo, consulta, datos), puestos[polo])
        for k, polo in enumerate(orden)
    ]


# ─────────────────────────────── lo que dice cada tarjeta ───────────────────────────────


def lo_que_pidio(consulta: Consulta, datos: Datos) -> list[str]:
    """Lo que la persona puso en el formulario, en el orden del formulario."""
    partes = [f"Desde {datos.origenes[consulta.origen].nombre}", f"{consulta.dias} días"]
    if consulta.fecha_inicio is not None:
        partes.append(f"desde el {textos.fechas(consulta.fecha_inicio, None)} de {consulta.fecha_inicio.year}")
    else:
        partes.append(textos.mes(consulta.mes))
    intereses = [ETIQUETAS_INTERES[i] for i in consulta.intereses]
    partes.append(", ".join(intereses) if intereses else "sin intereses marcados")
    if consulta.presupuesto is not None:
        partes.append(f"hasta {textos.soles(consulta.presupuesto)} por persona")
    if consulta.altitud_max is not None:
        partes.append(f"sin pasar de {textos.miles(consulta.altitud_max)} m")
    if consulta.solo_por_tierra:
        partes.append("solo por tierra")
    if consulta.sorpresa:
        partes.append("Sorpréndeme")
    return partes


def donde_se_duerme(ruta: Ruta) -> str:
    base = ruta.polo.base
    if base.altitud_m is None:
        return f"Se duerme en {base.nombre}."
    return f"Se duerme en {base.nombre}, a {textos.miles(base.altitud_m)} m."


def como_se_va(ruta: Ruta) -> str:
    t = ruta.traslado
    cuanto = f"{textos.duracion(t.horas * 60)} de puerta a puerta" if t.horas is not None else "sin dato de horas"
    if t.bus_de_noche is not None:
        b = t.bus_de_noche
        return f"En bus de noche: sale a las {b.sale} y llega a las {b.llega}, {cuanto}."
    if t.vuelos:
        tramos = ", ".join(f"{v.desde}–{v.hasta}" for v in t.vuelos)
        return f"En avión ({tramos}), {cuanto}."
    return f"{textos.por_medios(t.medios).capitalize()}, {cuanto}."


def dias(ruta: Ruta) -> list[tuple[str, str]]:
    """Cada día con sus lugares: con una estrella los imperdibles, que son los de jerarquía 3 o 4. Sin
    lugares, lo que dice su nota. Y la noche, si tiene plan."""
    salida = []
    for d in ruta.dias:
        cabeza = f"Día {d.numero}" + (" (tranquilo, por la altura)" if d.tranquilo else "")
        if d.paradas:
            texto = ", ".join(("★ " if (p.recurso.jerarquia or 0) >= 3 else "") + p.recurso.nombre for p in d.paradas)
        else:
            texto = (d.nota or "Sin visitas").rstrip(".")
        if d.noche is not None and d.noche.tipo != "descanso":
            texto += f". De noche: {d.noche.titulo}"
        salida.append((cabeza, texto.rstrip(".") + "."))
    return salida


def costo(ruta: Ruta) -> str:
    c = ruta.costo
    texto = f"De {textos.soles(c.p20)} a {textos.soles(c.p80)} por persona; lo más probable, {textos.soles(c.p50)}."
    if c.exceso:
        texto += f" Pasa el presupuesto por {textos.soles(c.exceso)}."
    elif c.dentro_del_presupuesto:
        texto += " Entra en el presupuesto."
    return texto


def mes(ruta: Ruta) -> str:
    e = ruta.estacionalidad
    return f"{VEREDICTO[e.veredicto]}. {e.explicacion}"


def fiestas(ruta: Ruta) -> str | None:
    nombres = list(dict.fromkeys(e.nombre for e in ruta.eventos))
    if not nombres:
        return None
    mas = f" y {len(nombres) - 3} más" if len(nombres) > 3 else ""
    return f"En esas fechas: {'; '.join(nombres[:3])}{mas}."


def avisos(ruta: Ruta) -> list[str]:
    return [
        a.mensaje
        for a in ruta.avisos
        if a.tipo not in YA_DICHOS and not (a.tipo == "acceso" and a.mensaje.startswith(COMO_SE_VA))
    ]


# ─────────────────────────────── el cuadernillo ───────────────────────────────

ESTILO = """
:root { color-scheme: light dark; --tinta: #13202b; --tinta-2: #4b5a66; --linea: #d5dde2; --fondo: #f4f6f7;
  --papel: #fff; --acento: #0b6e4f; --foco: #1d4ed8; }
@media (prefers-color-scheme: dark) {
  :root { --tinta: #e6edf1; --tinta-2: #a9b6bf; --linea: #33424d; --fondo: #0f171d; --papel: #172229;
    --acento: #5fd3a6; --foco: #93b4ff; }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--fondo); color: var(--tinta);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif; }
.barra { position: sticky; top: 0; z-index: 2; background: var(--papel); border-bottom: 1px solid var(--linea); }
.barra__dentro { max-width: 1040px; margin: 0 auto; padding: 8px 16px; display: flex; flex-wrap: wrap;
  gap: 6px 10px; align-items: center; }
#progreso { margin-right: auto; color: var(--tinta-2); font-size: .92rem; }
.tuyo { display: flex; flex-wrap: wrap; gap: 8px 12px; align-items: center; margin: 12px 0; }
.tuyo > label:first-child { font-weight: 600; }
#iniciales { width: 5.5em; font: inherit; padding: 4px 8px; border: 1px solid var(--linea); border-radius: 8px;
  background: var(--fondo); color: var(--tinta); text-transform: uppercase; }
@media (max-width: 600px) { .ancho { display: none; } }
button, .boton { font: inherit; font-size: .92rem; font-weight: 600; padding: 6px 12px; border-radius: 999px;
  cursor: pointer; border: 1px solid var(--acento); background: var(--papel); color: var(--acento);
  position: relative; }
button.principal { background: var(--acento); color: var(--papel); }
.boton input { position: absolute; inset: 0; opacity: 0; width: 100%; cursor: pointer; }
:focus-visible, .boton:focus-within { outline: 3px solid var(--foco); outline-offset: 2px; }
#mensaje { flex-basis: 100%; margin: 0; color: var(--tinta-2); font-size: .9rem; }
#mensaje:empty { display: none; }
main { max-width: 1040px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 1.6rem; margin: 0 0 8px; }
.guia { background: var(--papel); border-radius: 16px; padding: 4px 20px; margin-bottom: 24px; }
.consulta { margin: 40px 0; scroll-margin-top: 110px; }
.consulta h2 { font-size: 1.15rem; margin: 0 0 4px; }
.pidio { color: var(--tinta-2); margin: 0 0 12px; }
.opciones { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(300px, 100%), 1fr)); gap: 12px; }
.opcion { background: var(--papel); border: 1px solid var(--linea); border-radius: 14px; padding: 14px 16px;
  display: flex; flex-direction: column; scroll-margin-top: 110px; }
.opcion.calificada { border-color: var(--acento); box-shadow: inset 4px 0 0 var(--acento); }
.opcion h3 { font-size: 1.05rem; margin: 0 0 6px; }
.opcion p, .opcion li { font-size: .92rem; margin: 4px 0; }
.opcion ul { padding-left: 18px; margin: 6px 0; }
.nota { color: var(--tinta-2); }
fieldset { margin: auto 0 0; padding: 4px 0 0; border: 0; border-top: 1px solid var(--linea); }
legend { font-weight: 600; font-size: .92rem; padding: 10px 0 2px; float: left; width: 100%; }
fieldset label { display: flex; gap: 10px; align-items: center; padding: 5px 0; font-size: .95rem; clear: left;
  cursor: pointer; }
fieldset input[type=radio] { width: 20px; height: 20px; margin: 0; flex: none; accent-color: var(--acento); }
fieldset textarea { width: 100%; font: inherit; font-size: .9rem; padding: 6px 8px; margin-top: 4px;
  border: 1px solid var(--linea); border-radius: 8px; background: var(--fondo); color: var(--tinta); }
fieldset label.comentario { flex-direction: column; align-items: stretch; gap: 0; color: var(--tinta-2);
  font-size: .9rem; cursor: auto; }
@media print {
  .barra { display: none; }
  body { background: #fff; color: #000; }
  .opcion { break-inside: avoid; }
  .consulta h2 { break-after: avoid; }
}
"""

SCRIPT = r"""
(function () {
  "use strict";
  var kit = JSON.parse(document.getElementById("kit").textContent);
  var CLAVE = "dreemgo-calificaciones-" + kit.huella;
  var campos = Array.prototype.slice.call(document.querySelectorAll("fieldset[data-opcion]"));
  var iniciales = document.getElementById("iniciales");
  var progreso = document.getElementById("progreso");
  var mensaje = document.getElementById("mensaje");
  var estado = { iniciales: "", notas: {} };

  function id(f) { return f.dataset.consulta + "-" + f.dataset.opcion; }
  function leer() {
    try { var e = JSON.parse(localStorage.getItem(CLAVE) || "null"); if (e && e.notas) estado = e; } catch (err) {}
  }
  function guardar() { try { localStorage.setItem(CLAVE, JSON.stringify(estado)); } catch (err) {} }
  function nota(f) { return estado.notas[id(f)] || { calificacion: "", comentario: "" }; }
  function pintar(f) {
    var n = nota(f);
    f.querySelectorAll("input[type=radio]").forEach(function (r) { r.checked = r.value === n.calificacion; });
    f.querySelector("textarea").value = n.comentario;
    f.closest(".opcion").classList.toggle("calificada", n.calificacion !== "");
  }
  function contar() {
    var hechas = campos.filter(function (f) { return nota(f).calificacion !== ""; }).length;
    progreso.textContent = hechas + " de " + campos.length + " calificados";
    return hechas;
  }
  var reloj = null;
  function avisar(texto) {
    mensaje.textContent = texto;
    clearTimeout(reloj);
    reloj = setTimeout(function () { mensaje.textContent = ""; }, 12000);
  }
  function viajes(n) { return n === 1 ? "1 viaje" : n + " viajes"; }
  function cambiar(f) {
    var marcada = f.querySelector("input[type=radio]:checked");
    estado.notas[id(f)] = { calificacion: marcada ? marcada.value : "", comentario: f.querySelector("textarea").value };
    f.closest(".opcion").classList.toggle("calificada", !!marcada);
    guardar();
    contar();
  }
  function celda(v) { v = String(v); return /[;"\n\r]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
  function csv() {
    var filas = [kit.columnas.join(";")];
    campos.forEach(function (f) {
      var n = nota(f);
      filas.push([f.dataset.consulta, f.dataset.opcion, f.dataset.zona, n.calificacion, n.comentario.trim()]
        .map(celda).join(";"));
    });
    return "﻿" + filas.join("\n") + "\n";
  }
  function quien() { return (estado.iniciales || "").replace(/[^A-Za-z]/g, "").toUpperCase(); }
  function descargar() {
    if (!quien()) {
      avisar("Escribe tus iniciales, arriba de todo: van en el nombre del archivo.");
      iniciales.scrollIntoView({ behavior: "smooth", block: "center" });
      iniciales.focus({ preventScroll: true });
      return;
    }
    var url = URL.createObjectURL(new Blob([csv()], { type: "text/csv;charset=utf-8" }));
    var a = document.createElement("a");
    a.href = url;
    a.download = "calificaciones_" + quien() + ".csv";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    var faltan = campos.length - contar();
    avisar(faltan
      ? "Descargado. Falta" + (faltan === 1 ? " " : "n ") + viajes(faltan) + " por calificar: cuando termines, " +
        "descárgalo otra vez."
      : "Descargado, con todos los viajes calificados. Mándale el archivo a quien junta las planillas.");
  }
  function siguiente() {
    var f = campos.find(function (c) { return nota(c).calificacion === ""; });
    if (!f) { avisar("Ya calificaste todos los viajes."); return; }
    f.closest(".opcion").scrollIntoView({ behavior: "smooth", block: "start" });
    f.querySelector("input[type=radio]").focus({ preventScroll: true });
  }
  function filas(texto) {
    var salida = [], fila = [], v = "", entre = false;
    texto = texto.replace(/^﻿/, "");
    for (var i = 0; i < texto.length; i++) {
      var ch = texto[i];
      if (entre) {
        if (ch === '"' && texto[i + 1] === '"') { v += '"'; i++; }
        else if (ch === '"') entre = false;
        else v += ch;
      } else if (ch === '"') entre = true;
      else if (ch === ";") { fila.push(v); v = ""; }
      else if (ch === "\n" || ch === "\r") {
        if (ch === "\r" && texto[i + 1] === "\n") i++;
        fila.push(v); salida.push(fila); fila = []; v = "";
      } else v += ch;
    }
    if (v !== "" || fila.length) { fila.push(v); salida.push(fila); }
    return salida;
  }
  function cargar(archivo) {
    var lector = new FileReader();
    lector.onload = function () {
      var t = filas(String(lector.result));
      var col = {};
      (t.shift() || []).forEach(function (c, k) { col[c.trim()] = k; });
      if (!kit.columnas.every(function (c) { return c in col; })) {
        avisar("Ese archivo no es una planilla de este kit: le faltan columnas.");
        return;
      }
      var zonas = {}, puestas = 0, distintas = 0;
      campos.forEach(function (f) { zonas[id(f)] = f.dataset.zona; });
      t.forEach(function (fila) {
        var clave = (fila[col.consulta] || "").trim() + "-" + (fila[col.opcion] || "").trim();
        if (!(clave in zonas)) return;
        if (zonas[clave] !== (fila[col.zona] || "").trim()) { distintas++; return; }
        var c = (fila[col.calificacion] || "").trim();
        if (c !== "" && ["0", "1", "2"].indexOf(c) < 0) return;
        estado.notas[clave] = { calificacion: c, comentario: fila[col.comentario] || "" };
        if (c !== "") puestas++;
      });
      guardar();
      campos.forEach(pintar);
      contar();
      var otros = distintas === 1 ? " no coincide y no se cargó." : " no coinciden y no se cargaron.";
      avisar(distintas
        ? "Ese archivo es de otro kit: " + viajes(distintas) + otros
        : "Listo: " + (puestas === 1 ? "1 calificación cargada." : puestas + " calificaciones cargadas."));
    };
    lector.readAsText(archivo, "utf-8");
  }

  leer();
  iniciales.value = estado.iniciales || "";
  campos.forEach(function (f) {
    pintar(f);
    f.addEventListener("change", function () { cambiar(f); });
    f.querySelector("textarea").addEventListener("input", function () { cambiar(f); });
  });
  iniciales.addEventListener("input", function () { estado.iniciales = iniciales.value.trim(); guardar(); });
  document.getElementById("descargar").addEventListener("click", descargar);
  document.getElementById("siguiente").addEventListener("click", siguiente);
  document.getElementById("cargar").addEventListener("change", function (e) {
    if (e.target.files[0]) cargar(e.target.files[0]);
    e.target.value = "";
  });
  contar();
})();
"""


def huella(filas: list[tuple[consultas.ConsultaAnotada, list[Opcion]]], version_datos: str) -> str:
    """Doce caracteres que cambian si cambia cualquier opción del kit: el avance guardado en el navegador
    es de un kit y no se mezcla con el de otro."""
    texto = version_datos + "".join(f"|{c.id}{op.letra}{op.ruta.polo.id}" for c, ops in filas for op in ops)
    return hashlib.sha256(texto.encode()).hexdigest()[:12]


def _tarjeta(id_consulta: int, op: Opcion) -> list[str]:
    e = html.escape
    r = op.ruta
    nombre = f"c{id_consulta}-{op.letra}"
    partes = [
        f"<article class='opcion' id='{nombre}'>",
        f"<h3>{op.letra} · {e(r.polo.nombre)} <span class='nota'>({e(r.polo.region)})</span></h3>",
        f"<p>{e(donde_se_duerme(r))} {e(como_se_va(r))}</p><ul>",
        *(f"<li><b>{e(cabeza)}</b>: {e(texto)}</li>" for cabeza, texto in dias(r)),
        f"</ul><p>{e(costo(r))}</p><p>{e(mes(r))}</p>",
    ]
    if (f := fiestas(r)) is not None:
        partes.append(f"<p>{e(f)}</p>")
    partes.extend(f"<p class='nota'>{e(a)}</p>" for a in avisos(r))
    partes.append(
        f"<fieldset data-consulta='{id_consulta}' data-opcion='{op.letra}' data-zona='{e(r.polo.nombre)}'>"
        "<legend>¿Se lo recomendarías?</legend>"
    )
    partes.extend(
        f"<label><input type='radio' name='{nombre}' value='{valor}'> <b>{valor}</b> · {texto}</label>"
        for valor, texto in CALIFICACIONES
    )
    partes.append("<label class='comentario'>Comentario, si quieres<textarea rows='2'></textarea></label>")
    partes.append("</fieldset></article>")
    return partes


def cuadernillo(filas: list[tuple[consultas.ConsultaAnotada, list[Opcion]]], datos: Datos) -> str:
    e = html.escape
    total = sum(len(ops) for _, ops in filas)
    minimo, maximo = min(len(ops) for _, ops in filas), max(len(ops) for _, ops in filas)
    kit = {"huella": huella(filas, datos.version), "columnas": COLUMNAS}
    partes = [
        "<!doctype html>",
        "<html lang='es'><head><meta charset='utf-8'>",
        "<meta name='viewport' content='width=device-width, initial-scale=1'>",
        f"<title>Calificar los viajes · DreemGO</title><style>{ESTILO}</style></head><body>",
        "<header class='barra'><div class='barra__dentro'>",
        f"<span id='progreso' role='status'>0 de {total} calificados</span>",
        "<button type='button' id='siguiente'>Siguiente<span class='ancho'> sin calificar</span></button>",
        "<button type='button' id='descargar' class='principal'>Descargar"
        "<span class='ancho'> mis calificaciones</span></button>",
        "<p id='mensaje' role='status'></p>",
        "</div></header><main>",
        "<h1>Calificar los viajes</h1>",
        "<div class='guia'>",
        f"<p>Son {len(filas)} personas con un viaje en mente y, para cada una, de {minimo} a {maximo} viajes"
        f" posibles: {total} en total. Lee quién viaja y lo que pidió, y califica cada viaje por separado,"
        " pensando en esa persona: <b>2</b> si se lo recomendarías tal cual, <b>1</b> si podría servirle pero"
        " con reparos, <b>0</b> si no encaja. Las instrucciones completas, con ejemplos, están en"
        " <code>docs/evaluacion/anotar.md</code>.</p>",
        "<p>Califica por tu cuenta: sin abrir la app, sin mirar <code>clave.csv</code> y sin comentarlo con el"
        " equipo hasta que los cuatro hayan terminado. El avance se guarda en este navegador; para seguir en"
        " otra computadora, descarga tus calificaciones y cárgalas allá. Cuando termines, descárgalas y"
        " mándale el archivo a quien junta las planillas.</p>",
        "<div class='tuyo'><label for='iniciales'>Tus iniciales</label>",
        "<input id='iniciales' maxlength='4' autocomplete='off' spellcheck='false'>",
        "<label class='boton'>Cargar un archivo<input type='file' id='cargar' accept='.csv,text/csv'></label>",
        "</div>",
        f"<p class='nota'>★ imperdible: un lugar de jerarquía 3 o 4. Datos {e(datos.version)}, contrato"
        f" {e(VERSION_CONTRATO)}, kit {kit['huella']}.</p>",
        "</div>",
    ]
    for anotada, ops in filas:
        partes.append(f"<section class='consulta' id='c{anotada.id}'>")
        partes.append(f"<h2>{anotada.id}. {e(anotada.perfil)}</h2>")
        partes.append(f"<p class='pidio'>{e(' · '.join(lo_que_pidio(anotada.consulta, datos)))}</p>")
        partes.append("<div class='opciones'>")
        for op in ops:
            partes.extend(_tarjeta(anotada.id, op))
        partes.append("</div></section>")
    datos_kit = json.dumps(kit, ensure_ascii=False).replace("</", "<\\/")
    partes.append(f"</main><script type='application/json' id='kit'>{datos_kit}</script>")
    partes.append(f"<script>{SCRIPT}</script></body></html>")
    return "\n".join(partes) + "\n"


# ─────────────────────────────── las tablas ───────────────────────────────


def escribir_csv(ruta: Path, columnas: list[str], filas: list[list]) -> None:
    """Separado por «;» y con BOM, como el resto de las tablas del proyecto y como el CSV que descarga el
    cuadernillo: Excel lo abre con sus tildes."""
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh, delimiter=";", lineterminator="\n")
        w.writerow(columnas)
        w.writerows(filas)


def main() -> None:
    ap = argparse.ArgumentParser(description="Arma el kit para calificar los viajes de la semana 12.")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    a = ap.parse_args()
    datos = artefactos.cargar()
    filas = [(c, opciones(c.id, c.consulta, datos)) for c in consultas.leer()]
    marca = huella(filas, datos.version)
    a.salida.mkdir(parents=True, exist_ok=True)
    (a.salida / "cuadernillo.html").write_text(cuadernillo(filas, datos), encoding="utf-8")
    escribir_csv(
        a.salida / "planilla.csv",
        COLUMNAS,
        [[c.id, op.letra, op.ruta.polo.nombre, "", ""] for c, ops in filas for op in ops],
    )
    escribir_csv(
        a.salida / "clave.csv",
        ["consulta", "opcion", "polo", "zona", *(f"puesto_{s}" for s in SISTEMAS), "version_datos", "kit"],
        [
            [c.id, op.letra, op.ruta.polo.id, op.ruta.polo.nombre, *(op.puestos.get(s, "") for s in SISTEMAS)]
            + [datos.version, marca]
            for c, ops in filas
            for op in ops
        ],
    )
    total = sum(len(ops) for _, ops in filas)
    por_sistema = ", ".join(f"{s} {sum(1 for _, ops in filas for op in ops if s in op.puestos)}" for s in SISTEMAS)
    print(f"{len(filas)} consultas y {total} viajes para calificar ({por_sistema}).")


if __name__ == "__main__":
    main()

const { test } = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("../app/node_modules/jsdom");

const html = fs.readFileSync(path.join(__dirname, "../app/public/tablero-negocio.html"), "utf8");
const data = JSON.parse(html.match(/<script id="datos-negocio" type="application\/json">([\s\S]*?)<\/script>/)[1]);

function page() {
  const dom = new JSDOM(html, { url: "http://localhost:5173/tablero-negocio.html", runScripts: "dangerously" });
  const doc = dom.window.document;
  const values = () => [...doc.querySelectorAll("#kpis .kpi-value")].map((e) => e.textContent);
  return { dom, doc, values };
}

test("instantánea de 300 reproduce el recorrido y el resultado del escenario", () => {
  const { dom, doc, values } = page();
  assert.equal(data.registros.length, 300);
  assert.deepEqual(values(), ["300", "283", "95", "40", "S/ 800", "S/ -200"]);
  assert.match(doc.querySelector("#funnel").textContent, /Vio A y B213/);
  assert.match(doc.querySelector("#funnel").textContent, /Compró \(sim\.\)40/);
  assert.match(doc.querySelector("#finances").textContent, /S\/ -200/);
  assert.equal(doc.querySelectorAll("#definitions tbody tr").length, 27);
  dom.window.close();
});

test("alternativa A filtra todos los gráficos por las 93 aperturas", () => {
  const { dom, doc, values } = page();
  const selector = doc.querySelector("#variante");
  selector.value = "A";
  selector.dispatchEvent(new dom.window.Event("change"));
  assert.equal(values()[0], "93");
  assert.equal(values()[2], "52");
  assert.equal(values()[3], "24");
  assert.equal(values()[4], "S/ 480");
  assert.match(doc.querySelector("#timeline svg").getAttribute("aria-label"), /visitas, interacciones y compras simuladas por día/i);
  dom.window.close();
});

test("al avanzar desde cero se actualizan tarjetas y gráficos sin mezclar usuarios", () => {
  const { dom, doc, values } = page();
  const range = doc.querySelector("#shown");
  range.value = "0";
  range.dispatchEvent(new dom.window.Event("input"));
  assert.equal(values()[0], "0");
  assert.equal(values()[5], "S/ -800");
  assert.match(doc.querySelector("#finances").textContent, /S\/ -800/);
  doc.querySelector("#step").click();
  assert.equal(values()[0], "25");
  assert.match(doc.querySelector("#shown-value").textContent, /25 \/ 300/);
  dom.window.close();
});

test("un canal cambia de forma coherente la base y el escenario económico", () => {
  const { dom, doc, values } = page();
  const selector = doc.querySelector("#canal");
  selector.value = "Redes sociales";
  selector.dispatchEvent(new dom.window.Event("change"));
  const rows = data.registros.filter((r) => r.canal_simulado === "Redes sociales");
  const bought = rows.filter((r) => r.compra_simulada).length;
  assert.equal(Number(values()[0]), rows.length);
  assert.equal(Number(values()[3]), bought);
  assert.equal(values()[4], `S/ ${bought * 20}`);
  assert.equal(values()[5], `S/ ${bought * 15 - 800}`);
  assert.match(doc.querySelector("#finances").textContent, /periodo completo/);
  dom.window.close();
});

test("reproducir reinicia desde cero y pausar conserva el avance", () => {
  const { dom, doc, values } = page();
  doc.querySelector("#play").click();
  assert.equal(values()[0], "0");
  doc.querySelector("#pause").click();
  doc.querySelector("#step").click();
  assert.equal(values()[0], "25");
  doc.querySelector("#restart").click();
  assert.equal(values()[0], "0");
  dom.window.close();
});

test("el Pareto cuenta una sola vez a cada perfil sin compra del filtro", () => {
  const { dom, doc, values } = page();
  const rows = [...doc.querySelectorAll("#pareto tbody tr")];
  const counts = rows.map((row) => Number(row.cells[1].textContent));
  assert.equal(counts.reduce((sum, count) => sum + count, 0), 300 - 40);
  assert.deepEqual(counts, [...counts].sort((a, b) => b - a));
  assert.match(rows.at(-1).cells[3].textContent, /^100[,.]0 %$/);
  const channel = doc.querySelector("#canal");
  channel.value = "Redes sociales";
  channel.dispatchEvent(new dom.window.Event("change"));
  const filtered = [...doc.querySelectorAll("#pareto tbody tr")]
    .reduce((sum, row) => sum + Number(row.cells[1].textContent), 0);
  assert.equal(filtered, Number(values()[0]) - Number(values()[3]));
  dom.window.close();
});

test("el mapa de calor suma visitas y una celda filtra el tablero y se puede desmarcar", () => {
  const { dom, doc, values } = page();
  const cells = [...doc.querySelectorAll("#heatmap button[data-day][data-hour]")];
  assert.equal(cells.length, 28);
  assert.equal(cells.reduce((sum, cell) => sum + Number(cell.textContent), 0), 300);
  const chosen = cells.find((cell) => Number(cell.textContent) > 0);
  const expected = Number(chosen.textContent);
  chosen.click();
  assert.equal(Number(values()[0]), expected);
  assert.equal(doc.querySelector("#dia").value, chosen.dataset.day);
  assert.equal(doc.querySelector("#franja").value, chosen.dataset.hour);
  assert.equal([...doc.querySelectorAll("#heatmap button[data-day][data-hour]")]
    .reduce((sum, cell) => sum + Number(cell.textContent), 0), 300);
  assert.equal(doc.querySelector("#heatmap button[aria-pressed=true]").textContent, String(expected));
  doc.querySelector(`#heatmap button[data-day="${chosen.dataset.day}"][data-hour="${chosen.dataset.hour}"]`).click();
  assert.equal(Number(values()[0]), 300);
  assert.equal(doc.querySelector("#dia").value, "");
  assert.equal(doc.querySelector("#franja").value, "");
  dom.window.close();
});

test("los enlaces externos conservan la subruta en GitHub Pages y tienen respaldo local en file://", () => {
  const gh = new JSDOM(html, {
    url: "https://oswaldoaqm.github.io/Alejandros-Team/tablero-negocio.html",
    runScripts: "dangerously",
  });
  assert.equal(gh.window.document.querySelector("#web-link").href, "https://oswaldoaqm.github.io/Alejandros-Team/");
  assert.equal(
    gh.window.document.querySelector("#activity-link").href,
    "https://oswaldoaqm.github.io/Alejandros-Team/#/indicadores",
  );
  gh.window.close();

  const local = new JSDOM(html, { url: "file:///tmp/tablero-negocio.html", runScripts: "dangerously" });
  assert.equal(local.window.document.querySelector("#web-link").href, "http://localhost:5173/");
  assert.equal(local.window.document.querySelector("#activity-link").href, "http://localhost:5173/#/indicadores");
  local.window.close();
});

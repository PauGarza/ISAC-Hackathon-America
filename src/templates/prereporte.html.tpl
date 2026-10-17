<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Prerreporte ADN del Entrenador</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Layout: una sola columna de lectura (documento de trabajo); gráficas a todo el ancho y hallazgos en tarjetas de dos columnas. */
:root {
  --bg: #f4f6f8; --surface: #ffffff; --ink: #14181d; --ink-2: #48505b; --muted: #6f7782; --rule: #dde2e8;
  --accent: #1d4e89; --accent-soft: #e6eef8;
  --good: #0b7a0b; --good-soft: #e3f3e3; --warn: #8a5a00; --warn-soft: #fbf0d6;
  --bad: #b42f2f; --bad-soft: #f8e3e3; --neutral: #4a515c; --neutral-soft: #eceff3;
  --note: #fff8e6; --note-rule: #e9c46a;
  --display: "Barlow Condensed", "Arial Narrow", "Roboto Condensed", sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, "Cascadia Mono", Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #101317; --surface: #171b21; --ink: #eef1f4; --ink-2: #bcc4ce; --muted: #8b94a1; --rule: #2a3039;
    --accent: #8db6ee; --accent-soft: #1b2a3f;
    --good: #6fd36f; --good-soft: #15301a; --warn: #f3c25a; --warn-soft: #33290f;
    --bad: #f08a8a; --bad-soft: #3a1c1c; --neutral: #c2c9d2; --neutral-soft: #232932;
    --note: #2a2410; --note-rule: #8a6d1f; color-scheme: dark;
  }
}
:root[data-theme="dark"] {
  --bg: #101317; --surface: #171b21; --ink: #eef1f4; --ink-2: #bcc4ce; --muted: #8b94a1; --rule: #2a3039;
  --accent: #8db6ee; --accent-soft: #1b2a3f;
  --good: #6fd36f; --good-soft: #15301a; --warn: #f3c25a; --warn-soft: #33290f;
  --bad: #f08a8a; --bad-soft: #3a1c1c; --neutral: #c2c9d2; --neutral-soft: #232932;
  --note: #2a2410; --note-rule: #8a6d1f; color-scheme: dark;
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); font: 16px/1.55 var(--body); margin: 0; }
.wrap { max-width: 980px; margin: 0 auto; padding-block: 40px 64px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 48px; }
h1, h2, h3 { font-family: var(--display); font-weight: 600; text-wrap: balance; margin: 0; line-height: 1.1; }
h1 { font-size: clamp(2.2rem, 6vw, 3.4rem); letter-spacing: 0.005em; }
h2 { font-size: 1.9rem; }
h3 { font-size: 1.45rem; display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 12px; }
h4 { margin: 0; font-size: 1.05rem; line-height: 1.35; }
p { margin: 0; }
.prose { max-width: 68ch; display: grid; gap: 12px; color: var(--ink-2); }
.eyebrow { font: 600 0.78rem/1 var(--body); letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); }
header.top { display: grid; gap: 16px; border-bottom: 3px solid var(--ink); padding-bottom: 24px; }
section.parte { display: grid; gap: 20px; }
section.parte > header { display: grid; gap: 6px; }
.lectura { display: flex; flex-wrap: wrap; gap: 8px 16px; align-items: center; font-size: 0.9rem; color: var(--muted); }
.tiles { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.tile { background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 14px 16px; display: grid; gap: 4px; }
.tile .num { font: 700 2.2rem/1 var(--display); font-variant-numeric: tabular-nums; }
.tile .lab { font-size: 0.9rem; color: var(--ink-2); }
.tile.good .num { color: var(--good); } .tile.neutral .num { color: var(--neutral); }
.tile.bad .num { color: var(--bad); } .tile.warn .num { color: var(--warn); }
.dos { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: 16px; align-items: start; }
ol.decisiones { list-style: none; counter-reset: d; margin: 0; padding: 0; display: grid; gap: 10px; }
ol.decisiones li { counter-increment: d; background: var(--surface); border: 1px solid var(--rule); border-radius: 6px;
  padding: 14px 16px 14px 56px; position: relative; display: grid; gap: 4px; }
ol.decisiones li::before { content: counter(d); position: absolute; left: 18px; top: 12px; font: 700 1.6rem/1 var(--display); color: var(--accent); }
.decidido { background: var(--good-soft); border: 1px solid var(--good); border-radius: 6px; padding: 14px 18px; display: grid; gap: 8px; }
.decidido h3 { font-size: 1.2rem; color: var(--good); }
.decidido ul { margin: 0; padding-left: 20px; display: grid; gap: 6px; color: var(--ink); }
.pregunta { border-left: 4px solid var(--accent); background: var(--accent-soft); padding: 14px 18px; border-radius: 0 6px 6px 0;
  font-style: italic; color: var(--ink); max-width: 75ch; }
.tabla { overflow-x: auto; background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; }
table { border-collapse: collapse; width: 100%; font-size: 0.95rem; min-width: 620px; }
th, td { text-align: left; padding: 10px 14px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font: 600 0.78rem/1.2 var(--body); letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted); background: var(--bg); }
tbody tr:last-child td { border-bottom: 0; }
td.num { font-variant-numeric: tabular-nums; white-space: nowrap; }
ul.desvios { margin: 0; padding-left: 20px; display: grid; gap: 10px; max-width: 75ch; color: var(--ink-2); }
ul.desvios strong { color: var(--ink); }
.chip { display: inline-flex; align-items: center; gap: 5px; font-size: 0.8rem; font-weight: 600; padding: 2px 9px; border-radius: 999px;
  border: 1px solid transparent; line-height: 1.5; }
.chip.good { background: var(--good-soft); color: var(--good); border-color: var(--good); }
.chip.warn { background: var(--warn-soft); color: var(--warn); border-color: var(--warn); }
.chip.bad { background: var(--bad-soft); color: var(--bad); border-color: var(--bad); }
.chip.neutral { background: var(--neutral-soft); color: var(--neutral); border-color: var(--rule); }
.ids { font: 500 0.8rem/1 var(--mono); color: var(--muted); }
.bloque { display: grid; gap: 16px; padding-top: 8px; border-top: 1px solid var(--rule); }
.tarjetas { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.hallazgo { background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 14px 16px; display: grid; gap: 8px; align-content: start; min-width: 0; }
.hallazgo header { display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.hallazgo p { color: var(--ink-2); font-size: 0.95rem; }
.hid { font: 500 0.8rem/1 var(--mono); color: var(--accent); margin-right: 4px; }
.nota { background: var(--note); border-left: 3px solid var(--note-rule); padding: 8px 12px; border-radius: 0 4px 4px 0; display: grid; gap: 2px; }
.nota-tag { font: 600 0.72rem/1.3 var(--body); letter-spacing: 0.06em; text-transform: uppercase; color: var(--warn); }
.nota p { color: var(--ink); font-size: 0.92rem; }
figure.viz { margin: 0; background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 12px 12px 10px; display: grid; gap: 6px; min-width: 0; }
figure.viz figcaption { font-size: 0.85rem; color: var(--muted); padding: 0 4px; max-width: 80ch; }
.plot { width: 100%; }
ol.estructura { margin: 0; padding-left: 22px; display: grid; gap: 8px; max-width: 75ch; color: var(--ink-2); }
ol.estructura strong { color: var(--ink); }
footer.pie { color: var(--muted); font-size: 0.85rem; border-top: 1px solid var(--rule); padding-top: 16px; display: grid; gap: 6px; max-width: 80ch; }
code { font: 500 0.85em var(--mono); }
a { color: var(--accent); }
a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
nav.indice { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 0.92rem; }
abbr[title] { text-decoration: underline dotted; text-underline-offset: 3px; cursor: help; }
.exp { color: var(--muted); font-size: 0.92em; }
.siglas { background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 14px 18px; display: grid; gap: 10px; }
.siglas h3 { font-size: 1.2rem; }
.siglas ul { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px 24px; }
.siglas li { display: grid; grid-template-columns: 9.5em minmax(0, 1fr); gap: 10px; font-size: 0.9rem; color: var(--ink-2); }
.siglas li strong { color: var(--ink); font-family: var(--mono); font-size: 0.85rem; font-weight: 500; }
@media (max-width: 760px) { .siglas ul { grid-template-columns: minmax(0, 1fr); } }
@media (max-width: 760px) {
  .tiles { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .tarjetas, .dos { grid-template-columns: minmax(0, 1fr); }
}
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <span class="eyebrow">Prerreporte del equipo · $fecha</span>
    <h1>ADN del Entrenador: lo que tenemos y lo que falta decidir</h1>
    <div class="prose">
      <p>Juntamos todo lo que hemos trabajado: la historia de Jardine, el ADN del Entrenador, el ADN del club, el ADN ganador y la revisión con ojos de entrenador. Probamos cada idea con la misma regla antes de decidir si entra al reporte final. Aquí están los resultados con sus gráficas, las dudas que tenemos que discutir y una revisión de si seguimos respondiendo lo que pide el reto.</p>
      <p>El <strong>reporte HTML es nuestro producto principal</strong>; la app queda como complemento para explorar. Las notas amarillas <strong>"Para revisar"</strong> son los puntos para la discusión. Entrega: <strong>jueves 22 de octubre</strong>.</p>
    </div>
    <nav class="indice" aria-label="Secciones">
      <a href="#decidir">Qué decidir</a><a href="#reto">¿Vamos alineados con el reto?</a><a href="#framework">Dos marcos</a>
      <a href="#hallazgos">Lo que encontramos</a><a href="#estructura">Estructura del reporte</a>
    </nav>
  </header>

  <section class="parte" aria-labelledby="t-resumen">
    <header><h2 id="t-resumen">En una mirada</h2></header>
    <p class="prose">$resumen</p>
    <div class="tiles">
      <div class="tile good"><span class="num">$c_good</span><span class="lab">✓ se sostienen</span></div>
      <div class="tile neutral"><span class="num">$c_neutral</span><span class="lab">= no cambian el resultado</span></div>
      <div class="tile bad"><span class="num">$c_bad</span><span class="lab">✕ no se sostienen</span></div>
      <div class="tile warn"><span class="num">$c_warn</span><span class="lab">? no alcanzan los datos</span></div>
    </div>
    <div class="lectura">
      <span>Cómo probamos: siempre <strong>con el mismo técnico y el mismo nivel de rival</strong>; el plan de juego, <strong>con el partido empatado</strong>. Cifras de Apertura 2021 – Clausura 2025.</span>
      <span>"Se sostiene" = diferencia clara (p &lt; 0.10) y de tamaño relevante, con 8 partidos o más por grupo.</span>
    </div>
    <div class="siglas" id="siglas">
      <h3>Siglas que usamos</h3>
      <ul>$siglas</ul>
      <p class="lectura">En el texto, la primera vez que aparece cada sigla lleva su significado entre paréntesis; las demás están subrayadas y lo muestran al pasar el cursor.</p>
    </div>
  </section>

  <section class="parte" id="decidir" aria-labelledby="t-decidir">
    <header><span class="eyebrow">Antes de escribir el reporte</span><h2 id="t-decidir">Lo que tenemos que decidir</h2></header>
    <div class="dos">
      <ol class="decisiones">$decisiones</ol>
      <div class="decidido"><h3>Ya decidimos</h3><ul>$decidido</ul></div>
    </div>
  </section>

  <section class="parte" id="reto" aria-labelledby="t-reto">
    <header><span class="eyebrow">Revisión de rumbo</span><h2 id="t-reto">¿Vamos alineados con el reto?</h2></header>
    <p class="pregunta">"¿Cuáles son los principios que definen a su equipo en fase ofensiva y defensiva, cómo se manifiestan estos patrones a lo largo del tiempo, y de qué manera el entrenador ajusta su comportamiento en función del contexto del partido (rival, marcador, localía o momento del juego)?"</p>
    <div class="prose"><p><strong>En corto:</strong> el contenido cubre todos los componentes del reto. Los riesgos están en la forma: dos marcos que no coinciden y demasiadas ideas para un reporte que debe entender alguien que no vio los partidos.</p></div>
    <h3>Componentes del reto</h3>
    <div class="tabla"><table><thead><tr><th>Componente</th><th>Dónde lo respondemos</th><th>Estado</th></tr></thead><tbody>$alineacion</tbody></table></div>
    <h3>Criterios de evaluación</h3>
    <div class="tabla"><table><thead><tr><th>Criterio</th><th>Peso</th><th>Cómo lo respondemos</th><th>Riesgo</th></tr></thead><tbody>$criterios</tbody></table></div>
    <h3>Dónde nos podemos desviar</h3>
    <ul class="desvios">$desvios</ul>
  </section>

  <section class="parte" id="framework" aria-labelledby="t-fw">
    <header><span class="eyebrow">Coherencia interna</span><h2 id="t-fw">Dos marcos, una sola entrega</h2></header>
    <div class="prose"><p>El reto pide que cada cifra se pueda trazar a una definición escrita y que nada se contradiga. Hoy medimos varias cosas de dos formas: una en el marco de Python y otra en el de R. Ninguna está mal, pero el reporte debe usar una sola.</p></div>
    $frameworks
  </section>

  <section class="parte" id="hallazgos" aria-labelledby="t-hall">
    <header><span class="eyebrow">Registro de hipótesis · $n ideas</span><h2 id="t-hall">Lo que encontramos</h2>
      <div class="lectura">
        <span class="chip good"><span aria-hidden="true">✓</span> se sostiene</span>
        <span class="chip neutral"><span aria-hidden="true">=</span> no cambia</span>
        <span class="chip bad"><span aria-hidden="true">✕</span> no se sostiene</span>
        <span class="chip warn"><span aria-hidden="true">?</span> no alcanza</span>
        <span>Pasa el cursor sobre las gráficas para ver cada valor.</span>
      </div>
    </header>
    $secciones
  </section>

  <section class="parte" id="estructura" aria-labelledby="t-est">
    <header><span class="eyebrow">Propuesta</span><h2 id="t-est">Cómo quedaría el reporte final</h2></header>
    <div class="prose"><p>El reporte es el producto principal. Jardine es el protagonista; el ADN del club es la base para ver qué es suyo; el ADN ganador es el clímax. Cada sección abre con una pregunta de fútbol y un hallazgo con número. El método va en un anexo plegado y el glosario al final.</p></div>
    <ol class="estructura">$estructura</ol>
    <div class="prose"><p><strong>Calendario:</strong> 17–18 oct discusión y decisiones · 19–20 oct textos y reporte · 21 oct video y prueba de lectura con alguien de fuera de datos · 22 oct entrega.</p></div>
  </section>

  <footer class="pie">
    <p>Todo sale de resúmenes por partido, por serie o por torneo; no hay datos crudos de StatsBomb en esta página. Cifras de Apertura 2021 – Clausura 2025 salvo el epílogo.</p>
  </footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>
<script>
var D = $data;
function tok(n) { return getComputedStyle(document.documentElement).getPropertyValue(n).trim(); }
function merge(a, b) { for (var k in b) { if (b[k] && typeof b[k] === "object" && !Array.isArray(b[k]) && a[k] && typeof a[k] === "object") merge(a[k], b[k]); else a[k] = b[k]; } return a; }
function axis() { return { gridcolor: tok("--rule"), zerolinecolor: tok("--muted"), linecolor: tok("--rule"), tickfont: { color: tok("--muted") }, automargin: true, title: { font: { color: tok("--muted"), size: 12 } } }; }
function base(extra) {
  var l = { paper_bgcolor: "rgba(0,0,0,0)", plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "Source Sans 3, Segoe UI, sans-serif", size: 13, color: tok("--ink") },
    margin: { l: 10, r: 16, t: 40, b: 44 }, hoverlabel: { bgcolor: tok("--surface"), bordercolor: tok("--rule"), font: { color: tok("--ink") } },
    legend: { orientation: "h", y: 1.14, x: 0, font: { color: tok("--ink") } }, xaxis: axis(), yaxis: axis() };
  l.yaxis.tickfont = { color: tok("--ink") };
  return merge(l, extra || {});
}
var CFG = { displayModeBar: false, responsive: true };
var CC = D.coach_color, SC = D.stage_color, COACHES = ["Solari", "Ortiz", "Jardine"];
function el(id) { return document.getElementById(id); }
function hexA(h, a) { var n = parseInt(h.slice(1), 16); return "rgba(" + (n >> 16) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")"; }
function ciTrace(x, y, lo, hi, color, opts) {
  return merge({ type: "scatter", mode: "markers", x: x, y: y, marker: { size: 11, color: color },
    error_x: { type: "data", symmetric: false, array: x.map(function (v, i) { return hi[i] - v; }), arrayminus: x.map(function (v, i) { return v - lo[i]; }), color: tok("--muted"), thickness: 1.5, width: 0 } }, opts || {});
}

function gRadar() {
  var a = D.adn, th = a.rasgos.concat([a.rasgos[0]]);
  var tr = COACHES.map(function (c) {
    return { type: "scatterpolar", name: c, r: a[c].concat([a[c][0]]), theta: th, fill: "toself", fillcolor: hexA(CC[c], 0.12),
      line: { color: CC[c], width: 2 }, marker: { size: 6, color: CC[c] }, hovertemplate: "%{theta}<br>" + c + ": %{r:.0f} de 100<extra></extra>" };
  });
  Plotly.react("g-radar", tr, base({ height: 440, margin: { t: 50, b: 30, l: 60, r: 60 },
    polar: { bgcolor: "rgba(0,0,0,0)", radialaxis: { range: [0, 100], tickvals: [25, 50, 75], gridcolor: tok("--rule"), linecolor: tok("--rule"), tickfont: { color: tok("--muted"), size: 10 } },
      angularaxis: { gridcolor: tok("--rule"), linecolor: tok("--rule"), tickfont: { color: tok("--ink"), size: 12 } } } }), CFG);
}

function gAdn() {
  var a = D.adn, y = a.rasgos.map(function (r, i) { return a.club[i] === "siempre arriba de la liga" ? r + " · del club" : r; });
  var rng = { type: "scatter", mode: "lines", x: [], y: [], line: { color: tok("--rule"), width: 9 }, hoverinfo: "skip", showlegend: false };
  y.forEach(function (lab, i) { rng.x.push(a.min[i], a.max[i], null); rng.y.push(lab, lab, null); });
  var tr = [rng].concat(COACHES.map(function (c) {
    return { type: "scatter", mode: "markers", name: c, x: a[c], y: y, marker: { size: 12, color: CC[c], line: { color: tok("--surface"), width: 2 } },
      hovertemplate: "%{y}<br>" + c + ": %{x:.0f} de 100<extra></extra>" };
  }));
  Plotly.react("g-adn", tr, base({ height: 380, margin: { l: 215 }, xaxis: { range: [0, 102], title: { text: "de 0 a 100 frente a los técnicos de la liga (50 = típico)" } },
    yaxis: { autorange: "reversed", gridcolor: "rgba(0,0,0,0)" },
    shapes: [{ type: "line", x0: 50, x1: 50, yref: "paper", y0: 0, y1: 1, line: { color: tok("--muted"), dash: "dot", width: 1 } }] }), CFG);
}

function gEvol() {
  var e = D.evol, z = e.filas.map(function (_, i) { return e.z.map(function (col) { return col[i]; }); });
  var dark = tok("--surface").toLowerCase() !== "#ffffff";
  var scale = dark ? [[0, "#1c2533"], [0.5, "#256abf"], [1, "#9ec5f4"]] : [[0, "#eef4fc"], [0.5, "#5598e7"], [1, "#104281"]];
  Plotly.react("g-evol", [{ type: "heatmap", z: z, x: e.rasgos, y: e.filas, zmin: 0, zmax: 100, colorscale: scale, xgap: 2, ygap: 2,
    text: z.map(function (r) { return r.map(function (v) { return v === null ? "" : String(v); }); }), texttemplate: "%{text}",
    textfont: { size: 11 }, colorbar: { thickness: 10, len: 0.8, tickfont: { color: tok("--muted") }, outlinewidth: 0 },
    hovertemplate: "%{y}<br>%{x}: %{z:.0f} de 100<extra></extra>" }],
    base({ height: 420, margin: { t: 16, b: 90, l: 160 }, xaxis: { side: "bottom", tickangle: -30, gridcolor: "rgba(0,0,0,0)", tickfont: { color: tok("--ink") } },
      yaxis: { autorange: "reversed", gridcolor: "rgba(0,0,0,0)" } }), CFG);
}

function gPierna() {
  var p = D.pierna;
  Plotly.react("g-pierna", [{ type: "bar", x: p.coach, y: p.ext, marker: { color: p.coach.map(function (c) { return CC[c]; }) }, width: 0.5,
    text: p.ext.map(function (v) { return v.toFixed(1) + " de 2"; }), textposition: "outside", textfont: { color: tok("--ink") }, cliponaxis: false,
    hovertemplate: "%{x}: %{y:.1f} extremos a pierna cambiada por partido<extra></extra>" }],
    base({ height: 300, showlegend: false, margin: { t: 24 }, yaxis: { range: [0, 2.3], title: { text: "extremos a pierna cambiada por partido" } } }), CFG);
}

function gLocalia() {
  var L = D.localia, tr = [], lay = base({ height: 300, showlegend: true, margin: { t: 60 }, annotations: [] });
  var C = [tok("--accent"), tok("--muted")];
  L.forEach(function (m, i) {
    var ax = i ? String(i + 1) : "", dom = [i / 3 + 0.03, (i + 1) / 3 - 0.03];
    tr.push({ type: "bar", x: ["Local", "Visita"], y: [m.local, m.visita], xaxis: "x" + ax, yaxis: "y" + ax, showlegend: false,
      marker: { color: C }, text: [m.local, m.visita].map(function (v) { return v.toFixed(v < 10 ? 2 : 0); }), textposition: "outside",
      textfont: { color: tok("--ink") }, cliponaxis: false, hovertemplate: m.metrica + "<br>%{x}: %{y}<extra></extra>" });
    lay["xaxis" + ax] = merge(axis(), { domain: dom, anchor: "y" + ax, tickfont: { color: tok("--ink") } });
    lay["yaxis" + ax] = merge(axis(), { anchor: "x" + ax, range: [0, Math.max(m.local, m.visita) * 1.25], showticklabels: false });
    var titulo = { "Puntos por partido": "Puntos por partido", "Dominio territorial (%)": "Dominio territorial (%)",
      "Acciones defensivas en campo rival (%)": "Defiende en campo rival (%)" }[m.metrica] || m.metrica;
    lay.annotations.push({ text: titulo, xref: "paper", yref: "paper", x: (dom[0] + dom[1]) / 2, y: 1.18, showarrow: false, font: { size: 12, color: tok("--ink") } });
  });
  Plotly.react("g-localia", tr, lay, CFG);
}

function gCambios() {
  var c = D.cambios;
  Plotly.react("g-cambios", [ciTrace(c.map(function (r) { return r.dif; }), c.map(function (r) { return r.g + " (" + r.n + ")"; }),
    c.map(function (r) { return r.lo; }), c.map(function (r) { return r.hi; }), tok("--accent"),
    { hovertemplate: "%{y}<br>%{x:+.2f} xG por 100 posesiones<extra></extra>", showlegend: false })],
    base({ height: 340, margin: { t: 16, l: 300 }, xaxis: { zeroline: true, title: { text: "cambio en las ocasiones a favor después del cambio (xG por 100 posesiones)" } },
      yaxis: { autorange: "reversed", gridcolor: "rgba(0,0,0,0)" } }), CFG);
}

function gTorneos() {
  var t = D.torneos, col = t.llego.map(function (l) { return SC[l] || tok("--muted"); });
  var sym = t.llego.map(function (l) { return l === "Campeón" ? "star" : "circle"; });
  var size = t.llego.map(function (l) { return l === "Campeón" ? 20 : 13; });
  var hov = "%{x}<br>%{customdata}<br>%{y:.1f}<extra></extra>";
  var tr = [
    { type: "scatter", mode: "lines+markers", name: "Fase regular", x: t.t, y: t.ppda_reg, line: { color: tok("--rule"), width: 2 }, marker: { size: 7, color: tok("--muted") }, hovertemplate: "%{x}<br>fase regular: %{y:.1f}<extra></extra>" },
    { type: "scatter", mode: "markers", name: "Liguilla", x: t.t, y: t.ppda, customdata: t.llego, marker: { size: size, symbol: sym, color: col, line: { width: 1, color: tok("--surface") } }, hovertemplate: hov },
    { type: "scatter", mode: "lines+markers", name: "Fase regular", showlegend: false, x: t.t, y: t.pos_reg, xaxis: "x2", yaxis: "y2", line: { color: tok("--rule"), width: 2 }, marker: { size: 7, color: tok("--muted") }, hovertemplate: "%{x}<br>fase regular: %{y:.1f} %<extra></extra>" },
    { type: "scatter", mode: "markers", name: "Liguilla", showlegend: false, x: t.t, y: t.pos, xaxis: "x2", yaxis: "y2", customdata: t.llego, marker: { size: size, symbol: sym, color: col, line: { width: 1, color: tok("--surface") } }, hovertemplate: hov }];
  var lay = base({ height: 360, margin: { t: 60, b: 90 },
    xaxis: { domain: [0, 0.47], tickangle: -40, tickfont: { size: 10 } }, yaxis: { title: { text: "pases que deja dar antes de presionar" } },
    annotations: [{ text: "Presión (arriba = espera más)", xref: "paper", yref: "paper", x: 0, y: 1.16, showarrow: false, xanchor: "left", font: { size: 12, color: tok("--ink") } },
                  { text: "Posesión (%)", xref: "paper", yref: "paper", x: 0.53, y: 1.16, showarrow: false, xanchor: "left", font: { size: 12, color: tok("--ink") } }] });
  lay.legend.y = 1.32;
  lay.xaxis2 = merge(axis(), { domain: [0.53, 1], anchor: "y2", tickangle: -40, tickfont: { size: 10, color: tok("--muted") } });
  lay.yaxis2 = merge(axis(), { anchor: "x2", tickfont: { color: tok("--ink") } });
  Plotly.react("g-torneos", tr, lay, CFG);
}

function gSeries() {
  var tr = [];
  COACHES.forEach(function (c) {
    [true, false].forEach(function (av) {
      var s = D.series.filter(function (d) { return d.tecnico === c && d.avanzo === av; });
      if (!s.length) return;
      tr.push({ type: "scatter", mode: "markers", name: c + (av ? " · avanzó" : " · eliminado"), legendgroup: c,
        x: s.map(function (d) { return d.posesion; }), y: s.map(function (d) { return d.ppda; }),
        marker: { size: 13, symbol: av ? "circle" : "circle-open", color: CC[c], line: { width: 2, color: CC[c] } },
        customdata: s.map(function (d) { return [d.serie, d.rival, d.global]; }),
        hovertemplate: "%{customdata[0]} vs %{customdata[1]}<br>global %{customdata[2]}<br>posesión %{x:.0f} % · deja dar %{y:.0f} pases<extra></extra>" });
    });
  });
  Plotly.react("g-series", tr, base({ height: 440, margin: { t: 96 }, legend: { y: 1.3 },
    xaxis: { title: { text: "posesión en la serie (%)" } }, yaxis: { title: { text: "pases que deja dar antes de presionar (PPDA)" } },
    annotations: [{ xref: "paper", yref: "paper", x: 0.01, y: 0.98, showarrow: false, xanchor: "left", text: "↑ presiona menos (espera)", font: { color: tok("--muted"), size: 12 } },
                  { xref: "paper", yref: "paper", x: 0.99, y: 0.02, showarrow: false, xanchor: "right", text: "más balón y más presión →", font: { color: tok("--muted"), size: 12 } }] }), CFG);
}

function gMinuto() {
  var m = D.minuto, red = CC.Ortiz, blue = CC.Solari;
  Plotly.react("g-minuto", [
    { type: "scatter", mode: "lines", x: m.tramo, y: m.hi, line: { width: 0 }, hoverinfo: "skip", showlegend: false },
    { type: "scatter", mode: "lines", x: m.tramo, y: m.lo, fill: "tonexty", fillcolor: hexA(red, 0.16), line: { width: 0 }, hoverinfo: "skip", showlegend: false },
    { type: "scatter", mode: "lines+markers", name: "En contra", x: m.tramo, y: m.contra, line: { color: red, width: 2 }, marker: { size: 8, color: red },
      customdata: m.minutos, hovertemplate: "%{x}: %{y:.2f} xG en contra por 90'<br>%{customdata:,.0f} minutos<extra></extra>" },
    { type: "scatter", mode: "lines+markers", name: "A favor", x: m.tramo, y: m.favor, line: { color: blue, width: 2 }, marker: { size: 8, color: blue },
      hovertemplate: "%{x}: %{y:.2f} xG a favor por 90'<extra></extra>" }],
    base({ height: 340, xaxis: { title: { text: "tramo del partido (minutos)" }, type: "category" }, yaxis: { title: { text: "ocasiones (xG) por 90'" }, rangemode: "tozero" } }), CFG);
}

function gDerrotas() {
  var d = D.derrotas;
  Plotly.react("g-derrotas", [{ type: "bar", orientation: "h", y: d.map(function (r) { return r.metrica; }), x: d.map(function (r) { return r.dif_sd; }),
    marker: { color: d.map(function (r) { return r.veredicto === "se sostiene" ? tok("--accent") : hexA(tok("--muted"), 0.45); }) },
    customdata: d.map(function (r) { return [r.no, r.si, r.veredicto]; }),
    hovertemplate: "%{y}<br>victorias %{customdata[0]:.2f} · derrotas %{customdata[1]:.2f}<br>%{customdata[2]}<extra></extra>" }],
    base({ height: 460, showlegend: false, bargap: 0.35, margin: { t: 16, l: 340 },
      xaxis: { title: { text: "← menos en derrotas · más en derrotas → (desviaciones estándar)" }, zeroline: true }, yaxis: { gridcolor: "rgba(0,0,0,0)" } }), CFG);
}

function gFuertes() {
  var F = D.fuertes, mets = ["Toques en el área rival (por 100 posesiones)", "Ocasiones en contra (xG por 90')", "Posesión (%)"];
  var tr = [], lay = base({ height: 320, showlegend: false, margin: { t: 50, l: 120 }, annotations: [] });
  mets.forEach(function (m, i) {
    var ax = i ? String(i + 1) : "", dom = [i / 3 + 0.04, (i + 1) / 3 - 0.02];
    var rows = F.filter(function (r) { return r.metrica === m; });
    tr.push(ciTrace(rows.map(function (r) { return r.dif; }), rows.map(function (r) { return r.grupo; }),
      rows.map(function (r) { return r.lo; }), rows.map(function (r) { return r.hi; }),
      rows.map(function (r) { return r.grupo === "4-4-2" ? CC.Jardine : CC.Ortiz; }),
      { xaxis: "x" + ax, yaxis: "y" + ax, marker: { symbol: rows.map(function (r) { return r.veredicto === "se sostiene" ? "circle" : "circle-open"; }), line: { width: 2, color: rows.map(function (r) { return r.grupo === "4-4-2" ? CC.Jardine : CC.Ortiz; }) } },
        customdata: rows.map(function (r) { return [r.lo, r.hi, r.veredicto]; }),
        hovertemplate: "%{y} vs 4-2-3-1<br>" + m + ": %{x:+.2f} (%{customdata[0]:+.2f} a %{customdata[1]:+.2f})<br>%{customdata[2]}<extra></extra>" }));
    lay["xaxis" + ax] = merge(axis(), { domain: dom, anchor: "y" + ax, zeroline: true });
    lay["yaxis" + ax] = merge(axis(), { anchor: "x" + ax, showticklabels: i === 0, gridcolor: "rgba(0,0,0,0)", tickfont: { color: tok("--ink") } });
    lay.annotations.push({ text: m.replace(" (por 100 posesiones)", "").replace(" (xG por 90')", " (xG)"), xref: "paper", yref: "paper", x: (dom[0] + dom[1]) / 2, y: 1.16, showarrow: false, font: { size: 12, color: tok("--ink") } });
  });
  Plotly.react("g-fuertes", tr, lay, CFG);
}

function gFormaciones() {
  var f = D.formaciones, tr = [];
  ["Ocasiones a favor (xG por 90')", "Ocasiones en contra (xG por 90')"].forEach(function (met, k) {
    var rows = f.orden.map(function (o) { return f.filas.filter(function (r) { return r.formacion === o && r.metrica === met; })[0]; }).filter(Boolean);
    var NOM = { "Línea de 3": "3 centrales vs 4", "2": "2 delanteros vs 1" };
    var lab = rows.map(function (r) { return (NOM[r.formacion] || r.formacion) + " (" + r.min.toLocaleString("es-MX") + "')"; });
    var col = rows.map(function (r) { return r.veredicto === "no alcanza" ? tok("--muted") : (k ? CC.Ortiz : CC.Solari); });
    tr.push(ciTrace(rows.map(function (r) { return r.dif; }), lab, rows.map(function (r) { return r.lo; }), rows.map(function (r) { return r.hi; }), col,
      { xaxis: k ? "x2" : "x", yaxis: "y", showlegend: false,
        marker: { symbol: rows.map(function (r) { return r.veredicto === "se sostiene" ? "circle" : "circle-open"; }), line: { width: 2, color: col } },
        customdata: rows.map(function (r) { return [r.lo, r.hi, r.veredicto]; }),
        hovertemplate: "%{y}<br>" + met + ": %{x:+.2f} (%{customdata[0]:+.2f} a %{customdata[1]:+.2f})<br>%{customdata[2]}<extra></extra>" }));
  });
  var lay = base({ height: 440, margin: { t: 44, l: 230 }, yaxis: { autorange: "reversed", gridcolor: "rgba(0,0,0,0)" },
    xaxis: { domain: [0, 0.47], zeroline: true, title: { text: "a favor: diferencia vs 4-2-3-1" } },
    annotations: [{ text: "Ocasiones a favor", xref: "paper", yref: "paper", x: 0, y: 1.08, showarrow: false, xanchor: "left", font: { size: 13, color: tok("--ink") } },
                  { text: "Ocasiones en contra", xref: "paper", yref: "paper", x: 0.53, y: 1.08, showarrow: false, xanchor: "left", font: { size: 13, color: tok("--ink") } }] });
  lay.xaxis2 = merge(axis(), { domain: [0.53, 1], zeroline: true, anchor: "y", title: { text: "en contra: diferencia vs 4-2-3-1" } });
  Plotly.react("g-formaciones", tr, lay, CFG);
}

function gPlantilla() {
  var p = D.plantilla;
  Plotly.react("g-plantilla", [{ type: "bar", x: p.t, y: p.v, marker: { color: p.llego.map(function (l) { return SC[l] || tok("--muted"); }) },
    customdata: p.llego, text: p.llego, textposition: "inside", insidetextanchor: "start", textangle: -90, textfont: { size: 10, color: "#ffffff" },
    hovertemplate: "%{x}<br>aporte del once: %{y:.3f} por 90'<br>llegó a: %{customdata}<extra></extra>" }],
    base({ height: 340, showlegend: false, margin: { t: 16, b: 90 }, xaxis: { tickangle: -40, tickfont: { size: 10 } },
      yaxis: { title: { text: "aporte por 90' (OBV)" } } }), CFG);
}

function gEpilogo() {
  var e = D.epilogo;
  Plotly.react("g-epilogo", [{ type: "scatter", mode: "lines+markers", x: e.t, y: e.xg, line: { color: CC.Jardine, width: 2 },
    marker: { size: 11, symbol: e.reciente.map(function (r) { return r ? "circle-open" : "circle"; }), color: CC.Jardine, line: { width: 2, color: CC.Jardine } },
    customdata: e.pos, hovertemplate: "%{x}<br>%{y:.2f} xG por partido · posesión %{customdata:.0f} %<extra></extra>" }],
    base({ height: 300, showlegend: false, margin: { t: 16 }, yaxis: { title: { text: "ocasiones (xG) por partido, fase regular" }, rangemode: "tozero" } }), CFG);
}

var CHARTS = { "g-radar": gRadar, "g-adn": gAdn, "g-evol": gEvol, "g-pierna": gPierna, "g-localia": gLocalia, "g-cambios": gCambios,
  "g-torneos": gTorneos, "g-series": gSeries, "g-minuto": gMinuto, "g-derrotas": gDerrotas, "g-fuertes": gFuertes,
  "g-formaciones": gFormaciones, "g-plantilla": gPlantilla, "g-epilogo": gEpilogo };
function drawAll() {
  if (!window.Plotly) return;
  for (var id in CHARTS) { if (el(id)) { try { CHARTS[id](); } catch (e) { console.error(id, e); } } }
}
drawAll();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawAll);   // medir etiquetas con la tipografía ya cargada
try { window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", drawAll); } catch (e) {}
new MutationObserver(drawAll).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
</script>
</body>
</html>

<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>El ADN de André Jardine · Club América</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&family=IBM+Plex+Mono:wght@500&display=swap">
<style>
/* Reporte de lectura: una columna, tema claro fijo (también se imprime); cada sección abre con una pregunta de fútbol. */
:root {
  --bg: #ffffff; --paper: #f5f7f9; --ink: #14181d; --ink-2: #3f4752; --muted: #6f7782; --rule: #dde2e8;
  --accent: #1d4e89; --accent-soft: #e8eff8; --gold: #b8860b; --gold-soft: #fbf3dc;
  --display: "Barlow Condensed", "Arial Narrow", "Roboto Condensed", sans-serif;
  --body: "Source Sans 3", "Segoe UI", system-ui, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Consolas, monospace;
  color-scheme: light;
}
* { box-sizing: border-box; }
body { background: var(--bg); color: var(--ink); font: 17px/1.6 var(--body); margin: 0; }
.wrap { max-width: 900px; margin: 0 auto; padding-block: 0 72px;
  padding-left: max(18px, env(safe-area-inset-left, 0px)); padding-right: max(18px, env(safe-area-inset-right, 0px)); }
h1, h2, h3 { font-family: var(--display); font-weight: 600; margin: 0; line-height: 1.08; text-wrap: balance; }
h1 { font-size: clamp(2.6rem, 8vw, 4.4rem); letter-spacing: 0.005em; }
h2 { font-size: clamp(1.9rem, 4.5vw, 2.5rem); }
h3 { font-size: 1.4rem; }
p { margin: 0; }
.hero { padding-block: 56px 36px; border-bottom: 4px solid var(--ink); display: grid; gap: 18px; }
.eyebrow { font: 600 0.8rem/1 var(--body); letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
.lead { font-size: 1.2rem; color: var(--ink-2); max-width: 60ch; }
.meta { display: flex; flex-wrap: wrap; gap: 6px 22px; color: var(--muted); font-size: 0.92rem; }
nav.toc { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 0.95rem; padding-top: 4px; }
nav.toc a { color: var(--accent); text-decoration: none; border-bottom: 1px solid var(--accent-soft); }
section.s { padding-block: 44px 8px; display: grid; gap: 18px; }
section.s > header { display: grid; gap: 8px; }
.num-s { font: 700 1rem/1 var(--mono); color: var(--accent); }
.q { font-size: 1.15rem; color: var(--ink-2); font-style: italic; }
.prose { display: grid; gap: 14px; max-width: 68ch; }
.prose p { color: var(--ink); }
.prose strong { font-weight: 700; }
ol.minuto { list-style: none; margin: 0; padding: 0; display: grid; gap: 12px; }
ol.minuto li { display: grid; grid-template-columns: 54px minmax(0, 1fr); gap: 14px; background: var(--paper); border-radius: 8px; padding: 16px 18px; }
ol.minuto .num { font: 700 2.4rem/1 var(--display); color: var(--accent); }
ol.minuto h3 { font-size: 1.35rem; margin-bottom: 4px; }
ol.minuto p { color: var(--ink-2); }
figure.viz { margin: 4px 0; border-top: 1px solid var(--rule); border-bottom: 1px solid var(--rule); padding-block: 12px 10px; display: grid; gap: 6px; min-width: 0; }
figure.viz figcaption { font-size: 0.88rem; color: var(--muted); max-width: 80ch; }
.plot { width: 100%; }
.reco { background: var(--paper); border-radius: 8px; padding: 18px 20px; display: grid; gap: 10px; border-left: 4px solid var(--accent); }
.reco dl { margin: 0; display: grid; grid-template-columns: 9.5em minmax(0, 1fr); gap: 6px 14px; }
.reco dt { font: 600 0.78rem/1.6 var(--body); letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); }
.reco dd { margin: 0; color: var(--ink); }
.recos { display: grid; gap: 14px; }
.tabla { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-size: 0.95rem; min-width: 560px; }
th, td { text-align: left; padding: 10px 12px; border-bottom: 1px solid var(--rule); vertical-align: top; }
th { font: 600 0.78rem/1.2 var(--body); letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); }
details.anexo { border-top: 1px solid var(--rule); padding-block: 18px; }
details.anexo summary { cursor: pointer; font: 600 1.6rem/1.2 var(--display); }
details.anexo summary:focus-visible { outline: 2px solid var(--accent); outline-offset: 4px; }
details.anexo .prose { margin-top: 14px; }
details.anexo h3 { margin-top: 10px; }
dl.glosario { display: grid; grid-template-columns: 12em minmax(0, 1fr); gap: 8px 16px; margin: 14px 0 0; }
dl.glosario dt { font-weight: 700; }
dl.glosario dd { margin: 0; color: var(--ink-2); }
abbr[title] { text-decoration: underline dotted; text-underline-offset: 3px; cursor: help; }
.exp { color: var(--muted); font-size: 0.92em; }
.nota { background: var(--gold-soft); border-left: 3px solid var(--gold); padding: 10px 14px; border-radius: 0 6px 6px 0; color: var(--ink); font-size: 0.95rem; max-width: 70ch; }
.autores { font-weight: 600; color: var(--ink); font-size: 1.02rem; }
.importa { background: var(--accent-soft); border-radius: 8px; padding: 16px 18px; display: grid; gap: 10px; }
.importa-t { font: 600 0.8rem/1 var(--body); letter-spacing: 0.1em; text-transform: uppercase; color: var(--accent); }
.cifras { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.cifras div { display: grid; gap: 4px; }
.cifras b { font: 700 2.1rem/1 var(--display); color: var(--accent); font-variant-numeric: tabular-nums; }
.cifras span { font-size: 0.92rem; color: var(--ink-2); }
ol.flujo { list-style: none; margin: 0; padding: 0; display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 8px; counter-reset: f; }
ol.flujo li { counter-increment: f; background: var(--paper); border-radius: 8px; padding: 12px; display: grid; gap: 6px; align-content: start; position: relative; }
ol.flujo li::before { content: counter(f); font: 700 1.3rem/1 var(--display); color: var(--accent); }
ol.flujo li:not(:last-child)::after { content: "→"; position: absolute; right: -9px; top: 12px; color: var(--muted); font-weight: 700; }
ol.flujo strong { font-size: 0.98rem; }
ol.flujo span { font-size: 0.86rem; color: var(--ink-2); }
.ideas { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.ideas article { border: 1px solid var(--rule); border-radius: 8px; padding: 14px 16px; display: grid; gap: 6px; }
.ideas .de { font: 600 0.78rem/1.2 var(--body); letter-spacing: 0.07em; text-transform: uppercase; color: var(--gold); }
.ideas p { font-size: 0.95rem; color: var(--ink-2); }
ol.refs { margin: 14px 0 0; padding-left: 22px; display: grid; gap: 8px; color: var(--ink-2); font-size: 0.92rem; overflow-wrap: anywhere; }
@media (max-width: 760px) {
  .cifras, .ideas { grid-template-columns: minmax(0, 1fr); }
  ol.flujo { grid-template-columns: minmax(0, 1fr); }
  ol.flujo li:not(:last-child)::after { content: "↓"; right: 12px; top: auto; bottom: 6px; }
}
footer { margin-top: 40px; padding-top: 16px; border-top: 1px solid var(--rule); color: var(--muted); font-size: 0.88rem; display: grid; gap: 6px; }
a { color: var(--accent); }
@media (max-width: 640px) {
  .reco dl, dl.glosario { grid-template-columns: minmax(0, 1fr); }
  ol.minuto li { grid-template-columns: 40px minmax(0, 1fr); }
}
@media print { details.anexo { display: block; } .plot { break-inside: avoid; } }
</style>
</head>
<body>
<div class="wrap">
<header class="hero">
  <span class="eyebrow">Hackathon ISAC 2026 · Club América · La historia de un entrenador a través de los datos</span>
  <h1>El ADN de André Jardine</h1>
  <p class="lead">Entre 2023 y 2024 el América de André Jardine ganó tres torneos seguidos, el primer tricampeonato de la era de torneos cortos. Aquí contamos cómo juega, qué conserva del club, cómo ajusta según el partido y qué lo hizo campeón, con datos y para quien no vio los partidos.</p>
  <p class="autores">Emilio Villalobos García Padilla · Othoniel Reyes Camacho · Paulina Garza Allende</p>
  <div class="meta"><span>22 de octubre de 2026</span><span>Liga MX · Apertura 2021 – Clausura 2025</span><span>Jardine 91 partidos · Ortiz 55 · Solari 27</span><span>Datos: StatsBomb (eventos y 360)</span></div>
  <nav class="toc" aria-label="Contenido">
    <a href="#minuto">En un minuto</a><a href="#s1">El ADN del club</a><a href="#s2">Lo que puso Jardine</a><a href="#s3">Cómo ajusta</a>
    <a href="#s4">El ADN ganador</a><a href="#s5">Puntos críticos</a><a href="#s6">Recomendaciones</a><a href="#s7">Lo que probamos</a>
    <a href="#s8">Nuestro aporte</a><a href="#metodo">Metodología</a><a href="#glosario">Glosario</a><a href="#referencias">Referencias</a>
  </nav>
</header>

<section class="s" id="minuto" aria-labelledby="t-min">
  <header><h2 id="t-min">En un minuto</h2></header>
  <ol class="minuto">$minuto</ol>
  <aside class="importa" aria-label="Por qué importa">
    <p class="importa-t">¿Por qué importa?</p>
    <div class="cifras">$importa</div>
  </aside>
</section>

<section class="s" id="s1">
  <header><span class="num-s">1</span><h2>El ADN del América</h2><p class="q">¿Qué es del club y qué es del técnico?</p></header>
  <div class="prose">$adn</div>
  $g_radar
</section>

<section class="s" id="s2">
  <header><span class="num-s">2</span><h2>Lo que puso Jardine</h2><p class="q">¿Cómo sale, cómo ataca y cómo defiende su América?</p></header>
  <h3>Con balón</h3>
  <div class="prose">$jardine_con</div>
  $g_tipos
  $g_mapas
  <h3>Sin balón</h3>
  <div class="prose">$jardine_sin</div>
  <h3>Balón parado y jugadores</h3>
  <div class="prose">$jardine_bp</div>
</section>

<section class="s" id="s3">
  <header><span class="num-s">3</span><h2>Cómo ajusta</h2><p class="q">¿Qué cambia según el marcador, el rival, la cancha y el banco?</p></header>
  <div class="prose">$ajusta</div>
  $g_marcador
</section>

<section class="s" id="s4">
  <header><span class="num-s">4</span><h2>El ADN ganador</h2><p class="q">¿Qué hizo distinto el América campeón?</p></header>
  <div class="prose">$ganador</div>
  $g_torneos
  $g_series
</section>

<section class="s" id="s5">
  <header><span class="num-s">5</span><h2>Puntos críticos</h2><p class="q">¿Dónde se le escapan los partidos?</p></header>
  <div class="prose">$criticos</div>
  $g_minuto
  $g_derrotas
  $g_fuertes
</section>

<section class="s" id="s6">
  <header><span class="num-s">6</span><h2>Recomendaciones</h2><p class="q">¿Qué repetir y qué cambiar?</p></header>
  <div class="prose"><p>Cada recomendación sale de un patrón que se repite en los datos, con un indicador para seguirla partido a partido. Describen lo que pasó; no garantizan resultados.</p></div>
  <div class="recos">$recos</div>
</section>

<section class="s" id="s7">
  <header><span class="num-s">7</span><h2>Lo que probamos y no cambia el resultado</h2><p class="q">¿Qué ideas no se sostienen con los datos?</p></header>
  <div class="prose"><p>Probamos más ideas de las que contamos. Estas no se sostienen o los datos no alcanzan para afirmarlas; también son información para el cuerpo técnico.</p></div>
  <div class="tabla"><table><thead><tr><th>Idea</th><th>Lo que encontramos</th></tr></thead><tbody>$probamos</tbody></table></div>
</section>

<section class="s" id="s8">
  <header><span class="num-s">8</span><h2>Nuestro aporte</h2><p class="q">¿Cómo se usa esto más allá de Jardine?</p></header>
  <div class="prose">$aporte<p>Para explorar cualquier periodo, técnico o partido con las mismas gráficas está $app.</p></div>
  $g_encaje
  <h3>Cómo lo hicimos</h3>
  <ol class="flujo" aria-label="Del dato a la recomendación">
    <li><strong>Datos</strong><span>Eventos y 360 de StatsBomb del América y estadísticas por partido de toda la Liga MX, Apertura 2021 – Clausura 2025.</span></li>
    <li><strong>Un solo marco</strong><span>Cada objeto (posesión, transición, presión, balón parado…) definido una vez y usado en todo el reporte.</span></li>
    <li><strong>Indicadores por partido</strong><span>41 indicadores de juego y 8 rasgos del ADN para cada partido y cada técnico de la liga.</span></li>
    <li><strong>Comparaciones justas</strong><span>Mismo técnico, mismo nivel de rival y, para el plan de juego, el partido empatado. Cada idea se prueba antes de contarla.</span></li>
    <li><strong>Historia y recomendaciones</strong><span>Lo que se sostiene se cuenta en lenguaje de cancha, con un indicador para seguirlo.</span></li>
  </ol>
  <h3>De dónde tomamos las ideas</h3>
  <div class="ideas">
    <article><p class="de">Béisbol · OPS+ y ERA+</p><p>Las estadísticas del béisbol se ajustan por estadio y por época para comparar jugadores de distintos años. El ADN del Entrenador hace lo mismo: compara cada rasgo con la liga del mismo torneo y descuenta rival y localía.</p></article>
    <article><p class="de">Medicina · ensayos clínicos</p><p>Un tratamiento se compara contra pacientes parecidos, no contra cualquiera. Nosotros comparamos con el mismo técnico y el mismo nivel de rival, y medimos el plan con el partido empatado para no confundir causa y consecuencia.</p></article>
    <article><p class="de">Recomendadores · Spotify y Amazon</p><p>"Si te gusta esto, te gustará aquello": la distancia entre perfiles. El Índice de Encaje mide qué tan cerca está un técnico del ADN del club.</p></article>
    <article><p class="de">Física y finanzas · Monte Carlo</p><p>Repetir un experimento miles de veces para ver qué tan probable fue un resultado. Simulamos cada partido con sus ocasiones para saber qué tanto mereció el América sus puntos.</p></article>
  </div>
</section>

<section class="s" id="epilogo">
  <header><span class="num-s">+</span><h2>Epílogo: 2025–26</h2><p class="q">¿Qué pasó después?</p></header>
  <div class="prose">$epilogo</div>
  $g_epilogo
</section>

<section class="s" id="metodo">
<details class="anexo">
  <summary>Anexo A · Metodología</summary>
  <div class="prose">
    <h3>Datos y ventana</h3>
    <p>Eventos y 360 de StatsBomb de los partidos del América en la Liga MX (unas 3,500 acciones por partido) y estadísticas por equipo y partido de toda la liga para el ADN del Entrenador. Toda cifra sale de la ventana del reto, Apertura 2021 – Clausura 2025 (175 partidos del América); lo de 2025–26 aparece solo en el epílogo. El reporte usa solo resúmenes; no publica datos crudos.</p>
    <h3>Marco analítico: cada objeto definido una sola vez</h3>
    <p>Todas las cifras, gráficas y comparaciones salen de las mismas definiciones, escritas en un solo archivo de código (<code>src/framework.py</code>). Las principales:</p>
    <div class="tabla"><table><thead><tr><th>Objeto</th><th>Definición</th></tr></thead><tbody>
      <tr><td>Cancha</td><td>120 × 80 yardas; el América siempre ataca hacia la derecha. Tercios: propio (x &lt; 40), medio y último (x ≥ 80).</td></tr>
      <tr><td>Posesión</td><td>La de StatsBomb: termina cuando el rival toma el control del balón.</td></tr>
      <tr><td>Secuencia ofensiva</td><td>Posesión con 3 pases o más, o que llega al último tercio.</td></tr>
      <tr><td>Construcción (salida)</td><td>Posesión que empieza en el tercio propio desde juego, saque de meta o portero.</td></tr>
      <tr><td>Pase o conducción progresiva</td><td>Completo, de juego abierto, acerca el balón 25 % o más a la portería y termina en x ≥ 48.</td></tr>
      <tr><td>Pase largo</td><td>32 yardas o más.</td></tr>
      <tr><td>Transición</td><td>Recuperación que llega al último tercio o a tiro en 15 segundos o menos.</td></tr>
      <tr><td>Recuperación tras pérdida</td><td>Después de perder el balón en juego, el equipo lo gana o lo vuelve a jugar en 5 segundos o menos (medida por evento).</td></tr>
      <tr><td>Presión</td><td>Altura de cada acción defensiva: alta x ≥ 60, media 40–60, baja x &lt; 40. PPDA: pases rivales en su 60 % del campo entre acciones defensivas propias en nuestro 60 % alto.</td></tr>
      <tr><td>Balón parado</td><td>Posesión que abre el saque del propio equipo: córner, tiro libre o saque de banda en el último tercio.</td></tr>
      <tr><td>Marcador</td><td>Diferencia de goles antes de cada acción, en cinco estados (pierde por 2+, pierde por 1, empate, gana por 1, gana por 2+).</td></tr>
      <tr><td>Fuerza del rival</td><td>Puntos por partido del rival en sus 17 partidos previos de liga, en tres niveles (débil, medio, fuerte).</td></tr>
      <tr><td>Bloque (360)</td><td>Con el rival en posesión: última línea = los 4 jugadores de campo más retrasados; bloque = los 8 más retrasados; solo tomas con 8 o más jugadores visibles.</td></tr>
      <tr><td>Ocasión clara</td><td>Tiro sin penal con xG de 0.30 o más.</td></tr>
      <tr><td>Formación en el campo</td><td>La titular y cada cambio táctico registrado; cada minuto lleva la formación vigente, propia y del rival.</td></tr>
    </tbody></table></div>
    <h3>Cómo comparamos (para no engañarnos)</h3>
    <p>Un estilo solo se ve comparando, y una comparación injusta engaña. Por eso: (1) todo se compara <strong>con el mismo técnico y el mismo nivel de rival</strong>; (2) el plan de juego (posesión, presión) se mide <strong>con el partido empatado</strong>, porque con el marcador movido el plan es consecuencia del resultado; (3) el efecto del marcador se mide dentro del mismo partido; (4) el ADN se compara con la liga del mismo torneo, porque la liga y la forma de registrar los datos cambiaron con los años.</p>
    <p>Para decir que una diferencia "se sostiene" pedimos que sea clara (que el azar la explique menos de 1 de cada 10 veces, con una prueba de permutación dentro de cada técnico y nivel de rival), de tamaño relevante y con al menos 8 partidos por grupo. Con menos, lo contamos como pista.</p>
    <h3>ADN del Entrenador e Índice de Encaje</h3>
    <p>Ocho rasgos (control del balón, verticalidad, llegada al área, presión alta, reacción tras pérdida, peligro generado, solidez defensiva y balón parado), cada uno promedio de 2 a 4 estadísticas de StatsBomb, estandarizado contra la liga del mismo torneo, ajustado por rival y localía y expresado de 0 a 100 frente a 70 técnicos con 15 partidos o más. El Índice de Encaje es la cercanía de cada técnico al ADN promedio del América 2021–2025.</p>
    <h3>Tipos de gol</h3>
    <p>Cada gol sin penal se describe con su jugada completa (dónde empieza, duración, pases, conducciones, jugadores, avance, velocidad, pases largos y progresivos). Los de balón parado van aparte; el resto se resume con un análisis de componentes principales y se agrupa en tres tipos.</p>
    <h3>Simulación: ¿merecía sus resultados?</h3>
    <p>Repetimos cada partido con las ocasiones que tuvo cada equipo (cada posesión con tiros es gol con su probabilidad) para obtener los puntos que "merecía". El América de Jardine sumó más o menos lo que mereció: la simulación sirve para explicar, no para predecir.</p>
    <h3>Límites</h3>
    <p>No hay datos físicos (cuánto corre, ritmo) ni de lesiones. El 360 solo ve a los jugadores dentro de la toma. Son tres títulos y pocas series de liguilla: el ADN ganador es un patrón que se repite, no una ley. Las sustituciones se describen antes y después; no aíslan el efecto del cambio. Solo hay eventos del América: el resto de la liga entra por sus estadísticas por partido.</p>
  </div>
</details>
</section>

<section class="s" id="glosario">
<details class="anexo" open>
  <summary>Anexo B · Glosario</summary>
  <dl class="glosario">
    <dt>xG (goles esperados)</dt><dd>Qué tan clara fue cada ocasión: la probabilidad de que ese tiro sea gol, según desde dónde y cómo se tiró. Sumados, cuántos goles "merecía" un equipo.</dd>
    <dt>Ocasión clara</dt><dd>Tiro con xG de 0.30 o más (entra más o menos 1 de cada 3).</dd>
    <dt>PPDA</dt><dd>Pases que el rival puede dar antes de que intentemos robar. Más pases = presiona menos (espera); menos = presiona más.</dd>
    <dt>OBV (aporte)</dt><dd>Cuánto mejora o empeora cada acción con balón las opciones de marcar o de recibir gol.</dd>
    <dt>Dominio territorial</dt><dd>De los pases en el último tercio, qué porcentaje son del América (en inglés, field tilt).</dd>
    <dt>Transición</dt><dd>Robo que llega al último tercio o a tiro en 15 segundos o menos.</dd>
    <dt>Recuperación tras pérdida</dt><dd>Volver a tener el balón en los 5 segundos después de perderlo.</dd>
    <dt>360</dt><dd>Posición de los jugadores que se ven en la toma de TV en el momento de cada acción.</dd>
    <dt>Bloque medio / bajo</dt><dd>Dónde defiende el equipo: con el balón rival en el medio campo o cerca de su área.</dd>
    <dt>De 0 a 100</dt><dd>Lugar frente a los técnicos de la liga: 50 es el típico y 100 el que más lo hace.</dd>
    <dt>x</dt><dd>Distancia a nuestra portería, en yardas (la cancha mide 120; 60 es la media cancha).</dd>
    <dt>Ap / Cl</dt><dd>Apertura / Clausura.</dd>
  </dl>
</details>
</section>

<section class="s" id="referencias">
<details class="anexo">
  <summary>Anexo C · Referencias</summary>
  <ol class="refs">
    <li>Hudl StatsBomb. Datos de eventos y 360 de la Liga MX, Apertura 2021 – Clausura 2025. Proporcionados para el Hackathon ISAC 2026.</li>
    <li>StatsBomb (2021). <em>Introducing On-Ball Value (OBV)</em>. https://blogarchive.statsbomb.com/news/introducing-on-ball-value-obv/</li>
    <li>StatsBomb. <em>Set-pieces remain an under-utilised game-changer</em>. https://blogarchive.statsbomb.com/articles/soccer/set-pieces-remain-an-underutilised-gamechanger/</li>
    <li>Clijmans, J., Van Roy, M. y Davis, J. (2022). <em>Looking Beyond the Past: Analyzing the Intrinsic Playing Style of Soccer Teams</em>. ECML PKDD.</li>
    <li>Baseball-Reference. Glosario de estadísticas ajustadas por estadio y liga (OPS+, ERA+). https://www.baseball-reference.com/about/bat_glossary.shtml</li>
  </ol>
</details>
</section>

<footer>
  <p>Emilio Villalobos García Padilla · Othoniel Reyes Camacho · Paulina Garza Allende</p>
  <p>Hackathon ISAC 2026 · ITAM Sports Analytics Conference · reto presentado por Club América. Datos de StatsBomb usados solo para la competencia; el reporte muestra resultados, no datos crudos.</p>
</footer>
</div>

<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>
<script>
var FIGS = $figs;
var CFG = { displayModeBar: false, responsive: true };
function drawAll() {
  if (!window.Plotly) return;
  for (var id in FIGS) {
    var el = document.getElementById(id);
    if (el) { try { Plotly.react(el, FIGS[id].data, FIGS[id].layout, CFG); } catch (e) { console.error(id, e); } }
  }
}
drawAll();
if (document.fonts && document.fonts.ready) document.fonts.ready.then(drawAll);
</script>
</body>
</html>

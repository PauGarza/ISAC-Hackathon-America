"""Prerreporte para el equipo (Pau, Otho, Emi): qué encontramos, qué hay que revisar y si vamos alineados con el reto.

Lee SOLO agregados de data/gold/analysis/hipotesis_*.parquet (notebook 06) y escribe un HTML autocontenido en
reports/prereporte/prereporte_equipo.html. Las gráficas usan Plotly.js (cdnjs) con los colores de src/viz.py.

Uso: python -m src.prereporte   (después de correr el notebook 06)
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from string import Template

import pandas as pd

from src.pipeline.config import GOLD
from src.viz import COACH_COLOR

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "prereporte" / "prereporte_equipo.html"
A = GOLD / "analysis"
FECHA = "16 oct 2026"

SECCIONES = ["1 · El ADN del América", "2 · Lo que agregó Jardine", "3 · Cómo ajusta", "4 · Por qué ganó",
             "5 · Puntos críticos", "7 · Recomendaciones", "6 · Lo que probamos", "8 · Nuestro aporte", "Anexo · Límites"]
TITULO_SECCION = {
    "1 · El ADN del América": "El ADN del América: qué es del club y qué del técnico",
    "2 · Lo que agregó Jardine": "Lo que agregó Jardine",
    "3 · Cómo ajusta": "Cómo ajusta: rival, marcador, localía, minuto y cambios",
    "4 · Por qué ganó": "Por qué ganó y por qué no ganaron",
    "5 · Puntos críticos": "Puntos críticos",
    "7 · Recomendaciones": "Candidatas a recomendación",
    "6 · Lo que probamos": "Lo que probamos y no cambia el resultado",
    "8 · Nuestro aporte": "Nuestro aporte: el ADN del Entrenador",
    "Anexo · Límites": "Límites",
}

# Notas de revisión: quién decide y qué. Texto del equipo, no del análisis.
NOTAS = {
    "A1": ("Otho", "Tu tabla de 7 rasgos (promedios de temporada) y nuestro ADN de 8 rasgos (ajustado por rival y localía) "
                   "dicen casi lo mismo. Propuesta: contar una sola versión, la ajustada, y usar tus valores reales como apoyo."),
    "B1": ("Pau", "Contradice la nota de que la localía no distinguía. En el reporte: ¿lo contamos como ajuste del técnico "
                  "(presiona más arriba en casa) o solo como dato de contexto?"),
    "B4": ("Emi", "¿Te sirve como el 'momento crítico' que pedías? Recomendación candidata: un ajuste antes del descanso, "
                  "no solo en el medio tiempo."),
    "C1": ("Otho", "Con 3 títulos la diferencia en fase regular no alcanza para afirmarla. Propuesta: contarla como pista, "
                   "no como parte de la receta."),
    "C2": ("Todos", "Usa los 10 torneos, incluidos Ap 2025 y Cl 2026, que están fuera de los datos del reto. Solo con "
                    "Ap 2021 – Cl 2025 la presión de espera se sostiene (p = 0.07) y la posesión se debilita (p = 0.14). "
                    "Decidir si las temporadas recientes entran o quedan como epílogo."),
    "C3": ("Emi, Otho", "¿Usamos las semifinales de Ortiz como el contraejemplo central del ADN ganador?"),
    "C4": ("Otho", "Tu lectura en goles es correcta. Propuesta: añadir que en ocasiones (xG) no hubo diferencia, así que lo "
                   "decidió definir y atajar."),
    "C6": ("Emi", "Base para 'patrones cuando pierde'. Falta saber dónde nacen los contragolpes que le hacen daño "
                  "(requiere eventos; se puede hacer)."),
    "D1": ("Emi", "Tus ejemplos (4-4-2, 3-4-3) se revisaron junto con todas las formaciones, medidas por minutos en el campo."),
    "D1b": ("Otho", "Coincide con tu lectura de los tres centrales, ahora con el mismo técnico, rival y marcador."),
    "D1e": ("Todos", "Recomendación candidata: 4-4-2 contra rivales fuertes. Describe lo que pasó, no prueba causa: "
                     "hay que decirlo así en el reporte."),
    "D3": ("Emi", "No hay datos físicos (cuánto corre, ritmo). ¿Lo dejamos en 'lo que probamos' con ese límite?"),
    "D4": ("Otho, Emi", "Los extremos a pierna cambiada empezaron con Ortiz. ¿Va en 'lo que agregó Jardine' o en el ADN del club?"),
    "D5": ("Todos", "Descriptivo. ¿Lo convertimos en recomendación ('perdiendo, meter un perfil ofensivo pronto')?"),
    "D8": ("Pau", "Usa temporadas recientes (Ap 2025, Cl 2026). Entra solo si decidimos incluirlas."),
}

VER_CLASS = [("no se sostiene", "bad", "✕"), ("no alcanza", "warn", "?"), ("se sostiene", "good", "✓"), ("no cambia", "neutral", "=")]


def ver_chip(v: str) -> str:
    for key, cls, icon in VER_CLASS:
        if v.lower().startswith(key):
            return f'<span class="chip {cls}"><span aria-hidden="true">{icon}</span> {html.escape(v)}</span>'
    return f'<span class="chip neutral">{html.escape(v)}</span>'


def origen_chips(o: str) -> str:
    out = []
    for name in ["Pau", "Otho", "Emi"]:
        if name in o:
            out.append(f'<span class="who who-{name.lower()}">{name}</span>')
    return "".join(out)


def tarjeta(r) -> str:
    nota = NOTAS.get(r.id)
    nota_html = (f'<div class="nota"><span class="nota-tag">Para revisar · {html.escape(nota[0])}</span>'
                 f'<p>{html.escape(nota[1])}</p></div>') if nota else ""
    return f"""<article class="hallazgo" id="h-{r.id}">
  <header><span class="hid">{r.id}</span>{origen_chips(r.origen)}{ver_chip(r.veredicto)}</header>
  <h4>{html.escape(r.hipotesis)}</h4>
  <p>{html.escape(r.evidencia)}</p>
  {nota_html}
</article>"""


# ------------------------------------------------------------------ datos de las gráficas (solo agregados)
def datos_graficas() -> dict:
    adn = pd.read_parquet(A / "hipotesis_adn_comun.parquet")
    series = pd.read_parquet(A / "hipotesis_series_liguilla.parquet")
    minuto = pd.read_parquet(A / "hipotesis_minuto.parquet")
    fvs = pd.read_parquet(A / "hipotesis_formacion_vs.parquet")
    der = pd.read_parquet(A / "hipotesis_derrotas.parquet")
    forms = pd.read_parquet(A / "hipotesis_formaciones.parquet").set_index("formacion")

    fv = fvs[fvs.metrica.isin(["Ocasiones a favor (xG por 90')", "Ocasiones en contra (xG por 90')"])].copy()
    fv["etiqueta"] = fv.apply(lambda r: f"{r.formacion} ({r.minutos_comparables:,.0f}')", axis=1)
    orden = (fv[fv.metrica.str.contains("a favor")].sort_values("dif").formacion.tolist())
    j = minuto[minuto.tecnico == "Jardine"]
    return {
        "coach_color": {c: COACH_COLOR[c] for c in ["Solari", "Ortiz", "Jardine"]},
        "adn": {"rasgos": adn.rasgo.tolist(), **{c: adn[c].round(0).tolist() for c in ["Solari", "Ortiz", "Jardine"]},
                "min": adn.torneo_min.round(0).tolist(), "max": adn.torneo_max.round(0).tolist(),
                "club": adn.del_club.tolist()},
        "series": [{"serie": r.serie, "tecnico": r.tecnico, "rival": r.rival, "global": r["global"],
                    "posesion": round(r.posesion, 1), "ppda": round(r.ppda, 1), "avanzo": bool(r.avanzo),
                    "reciente": r.torneo in ("Apertura 2025", "Clausura 2026")} for _, r in series.iterrows()],
        "minuto": {"tramo": j.tramo.tolist(), "favor": j.xg_favor_90.round(2).tolist(), "contra": j.xg_contra_90.round(2).tolist(),
                   "lo": j.xg_contra_90_lo.round(2).tolist(), "hi": j.xg_contra_90_hi.round(2).tolist(),
                   "minutos": j.minutos.round(0).tolist()},
        "formaciones": {"orden": orden, "filas": [{"formacion": r.formacion, "frente_a": r.frente_a, "metrica": r.metrica,
                                                    "dif": round(r.dif, 2), "lo": round(r.lo, 2), "hi": round(r.hi, 2),
                                                    "min": round(r.minutos_comparables), "veredicto": r.veredicto}
                                                   for _, r in fv.iterrows()]},
        "derrotas": [{"metrica": r.metrica, "dif_sd": round(r.dif_sd, 2), "si": round(r.si, 2), "no": round(r.no, 2),
                      "veredicto": r.veredicto} for _, r in der.sort_values("dif_sd").iterrows()],
        "uso_formaciones": [{"formacion": f, "minutos": round(r.minutos), "fuertes": round(r["% minutos contra rivales fuertes"])}
                            for f, r in forms.iterrows()],
    }


# ------------------------------------------------------------------ contenido fijo del prerreporte
ALINEACION = [  # componente del reto → dónde lo respondemos → estado
    ("Construcción, progresión y ocasiones", "Historia §3.2 (salida corta, carriles, pase atrás); tipos de gol de Otho", "Cubierto"),
    ("Presión, organización defensiva y transiciones", "§3.3 y §3.4 (360: altura y compactación del bloque); defensa bajo ataque de Otho", "Cubierto"),
    ("¿Mantiene una identidad clara?", "ADN del club (A1) y ADN por torneo (§3.6)", "Cubierto"),
    ("Cambios según rival, marcador, localía y momento", "§3.5, B1, B4, H4; liguilla (C2)", "Cubierto"),
    ("Roles, alineaciones e impacto de sustituciones", "§3.7, formaciones por minutos (D1), cambios (D5)", "Cubierto; sustituciones solo descriptivo"),
    ("Balón parado ofensivo y defensivo", "§3.8 (con 360 en el saque); balón parado en liguilla (C4)", "Cubierto"),
    ("Métricas existentes y propias", "xG, OBV, PPDA, field tilt; propias: ADN del Entrenador, Índice de Encaje, ocasión clara, valor de recuperar", "Cubierto"),
    ("Framework analítico (definiciones, supuestos, coherencia, límites)", "src/framework.py y el de Otho", "Riesgo: hoy hay dos frameworks"),
    ("Simulación (opcional)", "Puntos esperados: cada partido repetido con sus ocasiones", "Cubierto"),
]
CRITERIOS = [
    ("Innovación", "25 %", "ADN del Entrenador para 70 técnicos, formaciones por minutos en el campo, plan medido con el partido "
     "empatado, explorador interactivo", "Que el reporte lo explique en simple; si no, no suma"),
    ("Comunicación y engagement", "25 %", "Lenguaje de cancha (Emi), 5 ideas, glosario al final", "Hoy hay 31 hipótesis: el reporte debe "
     "contar 5–6 ideas y mandar el resto a un anexo"),
    ("Accionabilidad", "25 %", "Recomendaciones: plan de liguilla, 4-4-2 contra fuertes, cierre del primer tiempo, primer palo, relevo de Fidalgo",
     "Cada recomendación con su evidencia y su límite"),
    ("Metodología y visualización", "25 %", "Un solo framework, comparaciones justas (mismo técnico, rival y marcador), gráficas que se leen solas",
     "Unificar las definiciones de Pau y Otho"),
]
DESVIOS = [
    ("Dos frameworks", "Las definiciones de Otho y las nuestras no coinciden (tabla abajo). El reto pide que todo salga de los "
     "mismos objetos. Propuesta: una sola definición por concepto; lo de Otho que no tenemos (tipos de gol, recuperación "
     "tras pérdida por evento, episodios de presión) se recalcula con ella o se adopta en el marco."),
    ("Datos fuera de la ventana", "El reto da Ap 2021 – Cl 2025. Otho usa 2021/22 – 2025/26 (Jardine 129 partidos) y la "
     "liguilla incluye Ap 2025 y Cl 2026. Propuesta: cifras titulares solo con la ventana; lo reciente, como epílogo marcado."),
    ("De 'cómo juega' a 'qué da puntos'", "El reto pregunta cómo juega el entrenador. Varias hipótesis (plantilla, tiempo efectivo, "
     "ida y vuelta, pierna) miran resultados. Sirven para accionabilidad, pero en el reporte van cortas, en 'lo que probamos'."),
    ("El protagonista", "El reto pide la historia de un entrenador. El ADN del club (Otho) es la base para ver qué es de Jardine, "
     "no el protagonista."),
    ("La rúbrica", "Las bases que tenemos (PDF) califican 4 criterios de 25 %: innovación, comunicación, accionabilidad y "
     "metodología. El bloque de ROI, activación y escalabilidad del todo.md venía de otra versión: propuesta, sacarlo del reporte."),
]
FRAMEWORKS = [  # concepto, Pau (src/framework.py), Otho (framework.md)
    ("Ventana de datos", "Ap 2021 – Cl 2025 (175 partidos); 2025–26 aparte", "2021/22 – 2025/26 (213 partidos)"),
    ("Transición", "Recuperación que llega al último tercio o tira en ≤ 15 s", "Primeros 10 s tras recuperar"),
    ("Presión alta", "Acción defensiva con x ≥ 60", "Episodio de presión con x ≥ 80"),
    ("Recuperación tras pérdida", "Por posesión (subestima; pendiente)", "Por evento, ≤ 5 s (mejor)"),
    ("Pase largo", "≥ 32 yd", "≥ 35 yd"),
    ("Pase progresivo", "−25 % de distancia, termina en x ≥ 48", "−25 % de distancia, termina en x ≥ 60"),
    ("Línea defensiva (360)", "Promedio de los 4 más retrasados", "2.º jugador más retrasado"),
    ("Nivel del rival", "Puntos de sus 17 partidos previos, en terciles", "Índice de Fuerza del Rival (IFR) de la temporada"),
    ("Balón parado", "Posesión que abre el saque propio, en cualquier zona", "Córner, o tiro libre o banda con x ≥ 80"),
    ("PPDA", "x ≥ 48 / pases rivales x ≤ 72", "Igual"),
    ("Tramos de minuto", "15', con 90+ aparte", "15', el añadido va al último tramo"),
]
DECISIONES = [
    ("Un solo framework", "¿Adoptamos src/framework.py como base y le sumamos lo de Otho que no tiene (recuperación tras pérdida "
     "por evento, tipos de secuencia, episodios de presión)?", "Pau, Otho"),
    ("Ventana de datos", "¿Cifras titulares solo con Ap 2021 – Cl 2025 y lo reciente como epílogo?", "Todos"),
    ("Las 5–6 ideas del reporte", "¿Cuáles de los hallazgos de abajo son la historia? Propuesta en la sección 5.", "Todos"),
    ("Recomendaciones", "¿Qué candidatas entran y cómo las decimos en lenguaje de cancha?", "Emi"),
    ("Material de Otho", "¿Qué tablas y figuras suyas entran (tipos y recetas de gol, defensa bajo ataque, finales, rivales)?", "Otho"),
]
ESTRUCTURA = [
    ("En un minuto", "5 frases y el enlace a la app"),
    ("El ADN del América", "Control, peligro y solidez con cualquier técnico (A1)"),
    ("Lo que agregó Jardine", "Salida corta, paciencia, pase atrás, presión de espera, balón parado (H7, H8, D4)"),
    ("Cómo ajusta", "Rival, marcador, localía, minuto y cambios (H4, B1, B4, D5)"),
    ("Por qué ganó y por qué no ganaron", "Liguilla de copa, semifinales de Ortiz, finales (C2, C3, C4)"),
    ("Puntos críticos", "Cierre del primer tiempo, contragolpes al perder, tres centrales, primer palo, final de etapa (B4, C6, D1b, H8, D8)"),
    ("Lo que probamos y no cambia", "Visita defensiva, presión pasiva, ida y vuelta, plantilla, tiempo efectivo, formaciones (B2, B3, C5, D3, D7, D1)"),
    ("Recomendaciones", "Qué repetir y qué cambiar, con su evidencia y su límite (D1e y las que decidamos)"),
    ("Nuestro aporte", "ADN del Entrenador, Índice de Encaje y el explorador (H1, H9, H10)"),
    ("Anexos", "Marco analítico (plegado) y glosario con enlaces desde el texto"),
]


def tabla(filas, cabeza, clases=None) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in cabeza)
    body = []
    for f in filas:
        tds = "".join(f'<td{(" class=" + chr(34) + clases[i] + chr(34)) if clases and clases[i] else ""}>{html.escape(str(c))}</td>'
                      for i, c in enumerate(f))
        body.append(f"<tr>{tds}</tr>")
    return f'<div class="tabla"><table><thead><tr>{th}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'


def estado_chip(s: str) -> str:
    cls, icon = ("good", "✓") if s == "Cubierto" else (("warn", "!") if s.startswith("Riesgo") else ("neutral", "~"))
    return f'<span class="chip {cls}"><span aria-hidden="true">{icon}</span> {html.escape(s)}</span>'


def build() -> str:
    R = pd.read_parquet(A / "hipotesis_equipo.parquet")
    data = datos_graficas()
    n = R.veredicto.str.lower()
    conteo = {"se sostiene": int(n.str.startswith("se sostiene").sum()), "no cambia": int(n.str.startswith("no cambia").sum()),
              "no se sostiene": int(n.str.startswith("no se sostiene").sum()), "no alcanza": int(n.str.startswith("no alcanza").sum())}
    graf = {"1 · El ADN del América": '<figure class="viz"><div id="g-adn" class="plot" role="img" aria-label="Rasgos del ADN por técnico, de 0 a 100 frente a la liga"></div><figcaption>Cada rasgo de 0 a 100 frente a los 70 técnicos de la liga (50 = típico). La barra gris es el rango entre torneos. Ap 2021 – Cl 2025.</figcaption></figure>',
            "4 · Por qué ganó": '<figure class="viz"><div id="g-series" class="plot" role="img" aria-label="Series de liguilla: posesión frente a presión"></div><figcaption>Cada punto es una serie de liguilla. Arriba = presiona menos (deja dar más pases antes de presionar). Relleno = el América avanzó. Los círculos con borde punteado son Ap 2025 y Cl 2026, fuera de los datos del reto.</figcaption></figure>',
            "5 · Puntos críticos": '<figure class="viz"><div id="g-minuto" class="plot" role="img" aria-label="Ocasiones a favor y en contra por tramo de 15 minutos, Jardine"></div><figcaption>Jardine, Ap 2023 – Cl 2025. Ocasiones (xG) por 90 minutos en cada tramo; la banda es el margen del 90 % de las ocasiones en contra.</figcaption></figure>'
                                     '<figure class="viz"><div id="g-derrotas" class="plot" role="img" aria-label="Diferencia entre derrotas y victorias por indicador"></div><figcaption>Derrotas frente a victorias, con el mismo técnico y el mismo nivel de rival, en desviaciones estándar. Lo del plan (posesión, dominio, presión, pases largos) se mide con el partido empatado.</figcaption></figure>',
            "6 · Lo que probamos": '<figure class="viz"><div id="g-formaciones" class="plot" role="img" aria-label="Cada formación frente al 4-2-3-1: ocasiones a favor y en contra"></div><figcaption>Diferencia frente al 4-2-3-1 en ocasiones por 90 minutos, con el mismo técnico, rival y marcador; la línea es el margen del 90 %. Entre paréntesis, los minutos comparables (con menos de 450 no alcanza para concluir).</figcaption></figure>'}
    secciones = []
    for s in SECCIONES:
        rs = R[R.seccion == s]
        if rs.empty:
            continue
        ids = ", ".join(rs.id)
        secciones.append(f"""<section class="bloque" id="s-{SECCIONES.index(s)}">
  <h3>{html.escape(TITULO_SECCION[s])} <span class="ids">{ids}</span></h3>
  {graf.get(s, "")}
  <div class="tarjetas">{"".join(tarjeta(r) for r in rs.itertuples())}</div>
</section>""")
    alin = "".join(f"<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td>{estado_chip(c)}</td></tr>" for a, b, c in ALINEACION)
    crit = "".join(f"<tr><td><strong>{html.escape(a)}</strong></td><td class='num'>{b}</td><td>{html.escape(c)}</td><td>{html.escape(d)}</td></tr>"
                   for a, b, c, d in CRITERIOS)
    desv = "".join(f"<li><strong>{html.escape(a)}.</strong> {html.escape(b)}</li>" for a, b in DESVIOS)
    dec = "".join(f'<li><div><strong>{html.escape(a)}</strong><span class="quien">{html.escape(c)}</span></div><p>{html.escape(b)}</p></li>'
                  for a, b, c in DECISIONES)
    est = "".join(f"<li><strong>{html.escape(a)}.</strong> {html.escape(b)}</li>" for a, b in ESTRUCTURA)
    resumen = (f"{len(R)} hipótesis de los tres probadas con la misma regla: {conteo['se sostiene']} se sostienen, "
               f"{conteo['no cambia']} no cambian el resultado, {conteo['no se sostiene']} no se sostienen y {conteo['no alcanza']} no alcanzan.")
    page = Template((Path(__file__).with_name("templates") / "prereporte.html").read_text(encoding="utf-8"))
    return page.substitute(fecha=FECHA, resumen=html.escape(resumen), decisiones=dec, alineacion=alin, criterios=crit,
                           desvios=desv, frameworks=tabla(FRAMEWORKS, ["Concepto", "Pau (src/framework.py)", "Otho (framework.md)"]),
                           secciones="\n".join(secciones), estructura=est,
                           data=json.dumps(data, ensure_ascii=False).replace("</", "<\\/"), n=len(R),
                           c_good=conteo["se sostiene"], c_neutral=conteo["no cambia"], c_bad=conteo["no se sostiene"],
                           c_warn=conteo["no alcanza"])


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT} · {OUT.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()

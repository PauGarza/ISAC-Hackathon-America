"""Prerreporte para el equipo: qué encontramos, qué falta decidir y si vamos alineados con el reto.

Lee SOLO agregados (data/gold/analysis/hipotesis_*.parquet del notebook 06, la evolución del ADN del notebook 05 y
el cubo por partido) y escribe un HTML autocontenido en reports/prereporte/prereporte_equipo.html. Las gráficas
usan Plotly.js (jsDelivr) con los colores de src/viz.py. La plantilla es src/templates/prereporte.html.tpl.

Uso: python -m src.prereporte   (después de correr el notebook 06)
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from string import Template

import pandas as pd

from src import cube as K
from src.pipeline.config import GOLD
from src.viz import COACH_COLOR, STAGE_COLOR, torneo_short

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "prereporte" / "prereporte_equipo.html"
TPL = Path(__file__).with_name("templates") / "prereporte.html.tpl"
A = GOLD / "analysis"
FECHA = "17 oct 2026"
COACHES = ["Solari", "Ortiz", "Jardine"]

SECCIONES = ["1 · El ADN del América", "2 · Lo que agregó Jardine", "3 · Cómo ajusta", "4 · Por qué ganó",
             "5 · Puntos críticos", "7 · Recomendaciones", "6 · Lo que probamos", "Epílogo · 2025–26",
             "8 · Nuestro aporte", "Anexo · Límites"]
TITULO_SECCION = {
    "1 · El ADN del América": "El ADN del América: qué es del club y qué del técnico",
    "2 · Lo que agregó Jardine": "Lo que agregó Jardine",
    "3 · Cómo ajusta": "Cómo ajusta: rival, marcador, localía, minuto y cambios",
    "4 · Por qué ganó": "Por qué ganó y por qué no ganaron",
    "5 · Puntos críticos": "Puntos críticos",
    "7 · Recomendaciones": "Candidatas a recomendación",
    "6 · Lo que probamos": "Lo que probamos y no cambia el resultado",
    "Epílogo · 2025–26": "Epílogo: 2025–26, fuera de la ventana",
    "8 · Nuestro aporte": "Nuestro aporte: el ADN del Entrenador",
    "Anexo · Límites": "Límites",
}

# Notas de revisión para la discusión del equipo.
NOTAS = {
    "A1": "Tenemos dos versiones que dicen casi lo mismo: los rasgos con promedios de temporada y el ADN de 8 rasgos ajustado "
          "por rival y localía. Propuesta: contar una sola, la ajustada, y usar los valores reales como apoyo.",
    "B1": "Creíamos que la localía no distinguía. ¿La contamos como un ajuste del técnico (presiona más arriba en casa) o solo como contexto?",
    "B4": "¿Es el 'momento crítico' que buscábamos? Recomendación candidata: un ajuste antes del descanso, no solo en el medio tiempo.",
    "C1": "Con 3 títulos la diferencia no alcanza para afirmarla. Propuesta: contarla como pista, no como parte de la receta.",
    "C2": "Ya con la ventana decidida (Ap 2021 – Cl 2025). La presión se sostiene; la posesión queda como pista. ¿Cómo lo contamos?",
    "C3": "¿Usamos las semifinales de Ortiz como el contraejemplo central del ADN ganador?",
    "C4": "Falta recalcular los goles de balón parado en liguilla con la ventana y nuestro marco.",
    "C6": "Base para 'patrones cuando pierde'. Falta ver dónde nacen los contragolpes que le hacen daño (se puede con eventos).",
    "D1": "Los ejemplos de la revisión (4-4-2, 3-4-3) los probamos junto con todas las formaciones, medidas por minutos en el campo.",
    "D1e": "Recomendación candidata: 4-4-2 contra rivales fuertes. Describe lo que pasó, no prueba causa: hay que decirlo así.",
    "D3": "No hay datos físicos (cuánto corre, ritmo). ¿Lo dejamos en 'lo que probamos' con ese límite?",
    "D4": "Los extremos a pierna cambiada empezaron con Ortiz. ¿Va en 'lo que agregó Jardine' o en el ADN del club?",
    "D5": "Descriptivo. ¿Lo convertimos en recomendación ('perdiendo, meter un perfil ofensivo pronto')?",
    "D8": "Depende de 2025–26: entra solo como epílogo, si decidimos incluirlo.",
}

# Siglas: la primera vez que aparecen en cada bloque de texto llevan su significado entre paréntesis; las demás,
# subrayadas con el significado al pasar el cursor. Ap / Cl y yd se escriben completos.
SIGLAS = [  # (patrón, sigla, significado corto, significado largo para el cursor y el recuadro)
    (r"\bxG\b", "xG", "goles esperados",
     "Goles esperados: qué tan clara fue cada ocasión (probabilidad de que el tiro sea gol). Sumados, cuántos goles 'merecía' el equipo."),
    (r"\bPPDA\b", "PPDA", "pases que deja dar al rival antes de presionar",
     "Pases que el rival puede dar antes de que intentemos robar. Más = presiona menos (espera); menos = presiona más."),
    (r"\bOBV\b", "OBV", "aporte de cada acción con balón",
     "On-Ball Value de StatsBomb: cuánto mejora o empeora cada acción con balón las opciones de marcar o de recibir gol."),
    (r"\bIFR\b", "IFR", "Índice de Fuerza del Rival",
     "Índice de Fuerza del Rival: diferencia de ocasiones, de goles y de aporte del rival en su temporada."),
    (r"(?<![\d.])360\b", "360", "posición de los jugadores visibles en la toma",
     "Datos 360 de StatsBomb: dónde estaban los jugadores que se ven en la toma de TV en el momento de cada acción."),
    (r"\bp = ", "p", "probabilidad de que la diferencia sea azar",
     "Probabilidad de ver una diferencia así solo por azar. Menos de 0.10 = diferencia clara."),
    (r"\bx ≥ ", "x", "distancia a nuestra portería, en yardas",
     "x = qué tan lejos de nuestra portería ocurre la acción, en yardas (la cancha mide 120; 60 es la media cancha)."),
]
SIGLAS_EXTRA = [("Ap / Cl", "Apertura / Clausura (en las gráficas)"), ("90'", "por cada 90 minutos de juego"),
                ("Desviaciones estándar", "cuánto se separa algo de su variación normal; 0.5 ya es una diferencia notable")]


def siglas(texto: str, seen: set | None = None) -> str:
    """Recibe texto YA escapado (puede traer etiquetas HTML); expande la primera aparición de cada sigla y marca las
    demás con <abbr>. `seen` (opcional) comparte el registro entre bloques: una sigla ya explicada en la misma sección
    no se vuelve a explicar. Dentro de un paréntesis, "(xG)" queda "(xG: goles esperados)"."""
    import re
    seen = set() if seen is None else seen
    t = re.sub(r"\bAp (\d{4})", r"Apertura \1", texto)
    t = re.sub(r"\bCl (\d{4})", r"Clausura \1", t)
    t = re.sub(r"(\d) yd\b", r"\1 yardas", t)
    for pat, sig, corto, largo in SIGLAS:
        def sub(m, sig=sig, corto=corto, largo=largo):
            tag = f'<abbr title="{html.escape(largo)}">{sig}</abbr>'
            rest = m.group(0)[len(sig):]                                   # conserva " = " o " ≥ "
            if sig in seen:
                return tag + rest
            seen.add(sig)
            s, i, j = m.string, m.start(), m.end()
            if i > 0 and s[i - 1] == "(" and j < len(s) and s[j] == ")":
                return f'{tag}<span class="exp">: {html.escape(corto)}</span>{rest}'
            return f'{tag} <span class="exp">({html.escape(corto)})</span>{rest}'
        t = re.sub(pat, sub, t)
    return t


def recuadro_siglas() -> str:
    filas = "".join(f"<li><strong>{s}</strong> <span>{html.escape(largo)}</span></li>" for _, s, _, largo in SIGLAS)
    filas += "".join(f"<li><strong>{html.escape(s)}</strong> <span>{html.escape(d)}</span></li>" for s, d in SIGLAS_EXTRA)
    return filas


VER_CLASS = [("no se sostiene", "bad", "✕"), ("no alcanza", "warn", "?"), ("se sostiene", "good", "✓"), ("no cambia", "neutral", "=")]


def ver_chip(v: str) -> str:
    for key, cls, icon in VER_CLASS:
        if v.lower().startswith(key):
            return f'<span class="chip {cls}"><span aria-hidden="true">{icon}</span> {siglas(html.escape(v))}</span>'
    return f'<span class="chip neutral">{html.escape(v)}</span>'


def tarjeta(r) -> str:
    nota = NOTAS.get(r.id)
    nota_html = (f'<div class="nota"><span class="nota-tag">Para revisar</span><p>{siglas(html.escape(nota))}</p></div>') if nota else ""
    return f"""<article class="hallazgo" id="h-{r.id}">
  <header><span class="hid">{r.id}</span>{ver_chip(r.veredicto)}</header>
  <h4>{siglas(html.escape(r.hipotesis))}</h4>
  <p>{siglas(html.escape(r.evidencia))}</p>
  {nota_html}
</article>"""


def fig(gid: str, alto: int, aria: str, pie: str) -> str:
    return (f'<figure class="viz"><div id="{gid}" class="plot" style="min-height:{alto}px" role="img" aria-label="{html.escape(aria)}"></div>'
            f'<figcaption>{siglas(html.escape(pie))}</figcaption></figure>')


# Gráficas de cada sección (ids que dibuja el script de la plantilla).
GRAFICAS = {
    "1 · El ADN del América": [
        ("g-radar", 440, "Radar del ADN de Solari, Ortiz y Jardine",
         "Así se ve el ADN de cada técnico: 8 rasgos de 0 a 100 frente a los 70 técnicos de la liga (50 = típico). Ap 2021 – Cl 2025."),
        ("g-adn", 380, "Rasgos del ADN por técnico con el rango entre torneos",
         "Los mismos rasgos en una línea: la barra gris es el rango entre torneos. 'Del club' = arriba de la liga con los tres técnicos y en todos los torneos."),
        ("g-evol", 420, "ADN torneo a torneo",
         "El ADN torneo a torneo (0 a 100 frente a la liga de ese torneo). Cada celda trae su valor; el azul más intenso es más de ese rasgo. "
         "Se ve qué se mantiene y qué cambia con cada técnico."),
    ],
    "2 · Lo que agregó Jardine": [
        ("g-pierna", 300, "Extremos a pierna cambiada por técnico",
         "Extremos titulares a pierna cambiada por partido (diestro por la izquierda o zurdo por la derecha), de 2 posibles."),
    ],
    "3 · Cómo ajusta": [
        ("g-localia", 300, "Local frente a visita",
         "Promedios por partido de local y de visita. La diferencia se confirma comparando con el mismo técnico y el mismo nivel de rival."),
        ("g-cambios", 340, "Qué pasa después de los cambios",
         "Cambio en las ocasiones a favor (xG por 100 posesiones) después de una ventana de cambios, según el marcador y quién sale. La línea es el margen del 90 %."),
    ],
    "4 · Por qué ganó": [
        ("g-torneos", 360, "Torneo a torneo: presión y posesión en liguilla",
         "Cada torneo: cuántos pases deja dar antes de presionar (arriba = espera más) y la posesión en la liguilla. La estrella marca el título."),
        ("g-series", 420, "Series de liguilla: posesión frente a presión",
         "Cada punto es una serie de liguilla. Arriba = presiona menos. Relleno = el América avanzó; vacío = quedó eliminado."),
    ],
    "5 · Puntos críticos": [
        ("g-minuto", 340, "Ocasiones a favor y en contra por tramo de 15 minutos",
         "Jardine. Ocasiones (xG) por 90 minutos en cada tramo; la banda es el margen del 90 % de las ocasiones en contra."),
        ("g-derrotas", 460, "Derrotas frente a victorias por indicador",
         "Derrotas frente a victorias, con el mismo técnico y nivel de rival, en desviaciones estándar. En azul, las diferencias claras. "
         "Posesión, dominio, presión y pases largos se miden con el partido empatado."),
    ],
    "7 · Recomendaciones": [
        ("g-fuertes", 320, "Contra rivales fuertes: cada dibujo frente al 4-2-3-1",
         "Contra rivales fuertes, con el mismo técnico y marcador: diferencia frente al 4-2-3-1. La línea es el margen del 90 %; si no cruza el cero, la diferencia es clara."),
    ],
    "6 · Lo que probamos": [
        ("g-formaciones", 440, "Cada formación frente al 4-2-3-1: ocasiones a favor y en contra",
         "Diferencia frente al 4-2-3-1 en ocasiones por 90 minutos, con el mismo técnico, rival y marcador. Punto relleno = diferencia clara; "
         "gris = menos de 450 minutos, no alcanza. Entre paréntesis, los minutos comparables."),
        ("g-plantilla", 340, "Aporte del once más usado por torneo",
         "Aporte (OBV) por 90 minutos del once más usado en cada torneo, coloreado por hasta dónde llegó."),
    ],
    "Epílogo · 2025–26": [
        ("g-epilogo", 300, "Ocasiones por partido de Jardine en cada torneo",
         "Jardine en fase regular: ocasiones (xG) por partido y posesión. Los puntos vacíos son 2025–26, fuera de la ventana del reto."),
    ],
}


# ------------------------------------------------------------------ datos de las gráficas (solo agregados)
def datos_graficas() -> dict:
    rd = lambda s, n=2: [None if pd.isna(v) else round(float(v), n) for v in s]
    adn = pd.read_parquet(A / "hipotesis_adn_comun.parquet")
    series = pd.read_parquet(A / "hipotesis_series_liguilla.parquet")
    minuto = pd.read_parquet(A / "hipotesis_minuto.parquet")
    fvs = pd.read_parquet(A / "hipotesis_formacion_vs.parquet")
    der = pd.read_parquet(A / "hipotesis_derrotas.parquet")
    loc = pd.read_parquet(A / "hipotesis_localia.parquet").set_index("metrica")
    cam = pd.read_parquet(A / "hipotesis_cambios.parquet")
    pie = pd.read_parquet(A / "hipotesis_pierna_por_tecnico.parquet")
    pla = pd.read_parquet(A / "hipotesis_plantilla.parquet")
    fue = pd.read_parquet(A / "hipotesis_formacion_fuertes.parquet")
    evo = pd.read_parquet(A / "story_evolucion_adn_torneo.parquet")
    P = K.load()["partidos"]

    evo = evo[(evo.muestra_torneo == "ventana") & evo.coach.isin(COACHES)].sort_values("inicio")
    rasgos = adn.rasgo.tolist()
    TT = K.torneos(P)
    TTv = TT[TT.torneo.isin(P[P.muestra == "ventana"].torneo.unique()) & TT.tecnico.isin(COACHES) & TT.partidos_liguilla.gt(0)]
    jt = TT[TT.tecnico == "Jardine"]
    recientes = set(P[P.muestra != "ventana"].torneo)

    fv = fvs[fvs.metrica.isin(["Ocasiones a favor (xG por 90')", "Ocasiones en contra (xG por 90')"])]
    orden = fv[fv.metrica.str.contains("a favor")].sort_values("dif").formacion.tolist()
    fk = ["Toques en el área rival (por 100 posesiones)", "Ocasiones en contra (xG por 90')", "Posesión (%)"]
    pla = pla.sort_values("torneo", key=lambda s: s.map({t: i for i, t in enumerate(P.drop_duplicates("torneo").sort_values("match_date").torneo)}))
    return {
        "coach_color": {c: COACH_COLOR[c] for c in COACHES},
        "stage_color": STAGE_COLOR,
        "adn": {"rasgos": rasgos, **{c: rd(adn[c], 0) for c in COACHES}, "min": rd(adn.torneo_min, 0),
                "max": rd(adn.torneo_max, 0), "club": adn.del_club.tolist()},
        "evol": {"filas": [f"{torneo_short(r.torneo)} · {r.coach}" for r in evo.itertuples()], "rasgos": rasgos,
                 "z": [rd(evo[r], 0) for r in rasgos]},
        "series": [{"serie": r.serie, "tecnico": r.tecnico, "rival": r.rival, "global": r["global"],
                    "posesion": round(r.posesion, 1), "ppda": round(r.ppda, 1), "avanzo": bool(r.avanzo)} for _, r in series.iterrows()],
        "torneos": {"t": [f"{torneo_short(r.torneo)} · {r.tecnico}" for r in TTv.itertuples()], "llego": TTv.llego.tolist(),
                    "ppda": rd(TTv.ppda_liguilla, 1), "pos": rd(TTv.posesion_liguilla, 1),
                    "ppda_reg": rd(TTv.ppda_regular, 1), "pos_reg": rd(TTv.posesion_regular, 1)},
        "minuto": (lambda j: {"tramo": j.tramo.tolist(), "favor": rd(j.xg_favor_90), "contra": rd(j.xg_contra_90),
                              "lo": rd(j.xg_contra_90_lo), "hi": rd(j.xg_contra_90_hi), "minutos": rd(j.minutos, 0)})(minuto[minuto.tecnico == "Jardine"]),
        "formaciones": {"orden": orden, "filas": [{"formacion": r.formacion, "frente_a": r.frente_a, "metrica": r.metrica,
                                                    "dif": round(r.dif, 2), "lo": round(r.lo, 2), "hi": round(r.hi, 2),
                                                    "min": int(r.minutos_comparables), "veredicto": r.veredicto} for _, r in fv.iterrows()]},
        "derrotas": [{"metrica": r.metrica, "dif_sd": round(r.dif_sd, 2), "si": round(r.si, 2), "no": round(r.no, 2),
                      "veredicto": r.veredicto} for _, r in der.sort_values("dif_sd").iterrows()],
        "localia": [{"metrica": m, "local": round(loc.loc[m, "si"], 2), "visita": round(loc.loc[m, "no"], 2), "veredicto": loc.loc[m, "veredicto"]}
                    for m in ["Puntos por partido", "Dominio territorial (%)", "Acciones defensivas en campo rival (%)"]],
        "cambios": [{"g": f"{r.marcador} · {r.sale.lower()}", "dif": round(r.cambio_xg_favor, 2), "lo": round(r.cambio_xg_favor_lo, 2),
                     "hi": round(r.cambio_xg_favor_hi, 2), "n": int(r.ventanas)} for r in cam.itertuples() if r.ventanas >= 20],
        "pierna": {"coach": pie.coach.tolist(), "ext": rd(pie.extremos_invertidos), "lat": rd(pie.laterales_invertidos)},
        "plantilla": {"t": [f"{torneo_short(r.torneo)} · {r.tecnico}" for r in pla.itertuples()], "v": rd(pla.aporte90_once, 3),
                      "llego": pla.llego.tolist()},
        "fuertes": [{"grupo": "4-4-2" if r.formacion == "4-4-2" else "Tres centrales", "metrica": r.metrica, "dif": round(r.dif, 2),
                     "lo": round(r.lo, 2), "hi": round(r.hi, 2), "veredicto": r.veredicto} for r in fue.itertuples() if r.metrica in fk],
        "epilogo": {"t": [torneo_short(t) for t in jt.torneo], "xg": rd(jt.xg_favor_regular), "pos": rd(jt.posesion_regular, 1),
                    "reciente": [t in recientes for t in jt.torneo]},
    }


# ------------------------------------------------------------------ contenido fijo del prerreporte
ALINEACION = [  # componente del reto → dónde lo respondemos → estado
    ("Construcción, progresión y ocasiones", "Salida corta, carriles, pase atrás; tipos y recetas de gol", "Cubierto"),
    ("Presión, organización defensiva y transiciones", "Presión frente a la liga, 360 (altura y compactación del bloque), defensa bajo ataque", "Cubierto"),
    ("¿Mantiene una identidad clara?", "ADN del club (A1) y ADN torneo a torneo", "Cubierto"),
    ("Cambios según rival, marcador, localía y momento", "Marcador (H4), localía (B1), minuto (B4), liguilla (C2)", "Cubierto"),
    ("Roles, alineaciones e impacto de sustituciones", "Roles y uso de jugadores, formaciones por minutos (D1), cambios (D5)", "Cubierto; sustituciones solo descriptivo"),
    ("Balón parado ofensivo y defensivo", "Segunda jugada, córner en corto, primer palo, 360 en el saque; balón parado en liguilla (C4)", "Cubierto"),
    ("Métricas existentes y propias", "xG, OBV, PPDA, field tilt; propias: ADN del Entrenador, Índice de Encaje, ocasión clara, valor de recuperar", "Cubierto"),
    ("Framework analítico (definiciones, supuestos, coherencia, límites)", "Hoy tenemos dos marcos, uno en Python y otro en R", "Riesgo: hay que unificarlos"),
    ("Simulación (opcional)", "Puntos esperados: cada partido repetido con sus ocasiones", "Cubierto"),
]
CRITERIOS = [
    ("Innovación", "25 %", "ADN del Entrenador para 70 técnicos, formaciones por minutos en el campo, plan medido con el partido "
     "empatado; el explorador interactivo como complemento", "Que el reporte lo explique en simple; si no, no suma"),
    ("Comunicación y engagement", "25 %", "Lenguaje de cancha, 5–6 ideas, glosario al final", "Tenemos 31 hipótesis: el reporte "
     "debe contar 5–6 ideas y mandar el resto a un anexo"),
    ("Accionabilidad", "25 %", "Recomendaciones: plan de liguilla, 4-4-2 contra fuertes, cierre del primer tiempo, primer palo, relevo de Fidalgo",
     "Cada recomendación con su evidencia y su límite"),
    ("Metodología y visualización", "25 %", "Un solo marco, comparaciones justas (mismo técnico, rival y marcador), gráficas que se leen solas",
     "Unificar los dos marcos"),
]
DESVIOS = [
    ("Dos marcos", "Los marcos en Python y en R no definen igual varios conceptos (tabla de abajo). El reto pide que todo salga de los "
     "mismos objetos. Propuesta: una sola definición por concepto; lo que solo está en R (tipos de secuencia, episodios de "
     "presión, tipos de gol) se recalcula con ella."),
    ("Datos fuera de la ventana (resuelto)", "El reto da Ap 2021 – Cl 2025. Decidimos que las cifras salgan solo de esa ventana; "
     "2025–26 queda como epílogo marcado. Ya recalculamos la liguilla con la ventana."),
    ("De 'cómo juega' a 'qué da puntos'", "El reto pregunta cómo juega el entrenador. Varias hipótesis (plantilla, tiempo efectivo, "
     "ida y vuelta, pierna) miran resultados. Sirven para las recomendaciones, pero en el reporte van cortas, en 'lo que probamos'."),
    ("El protagonista", "El reto pide la historia de un entrenador. El ADN del club es la base para ver qué es de Jardine, no el protagonista."),
    ("La rúbrica", "Las bases (PDF) califican 4 criterios de 25 %: innovación, comunicación, accionabilidad y metodología. El bloque de "
     "ROI, activación y escalabilidad venía de otra versión: proponemos sacarlo del reporte."),
]
FRAMEWORKS = [  # concepto, marco en Python, marco en R, estado
    ("Ventana de datos", "Ap 2021 – Cl 2025 (175 partidos); 2025–26 aparte", "2021/22 – 2025/26 (213 partidos)",
     "Decidido: Ap 2021 – Cl 2025; 2025–26 aparte"),
    ("Recuperación tras pérdida", "Por posesión (subestima)", "Por evento, ≤ 5 s", "Decidido: por evento, ≤ 5 s (falta llevarlo al marco en Python)"),
    ("Transición", "Recuperación que llega al último tercio o tira en ≤ 15 s", "Primeros 10 s tras recuperar", "Por decidir"),
    ("Presión alta", "Acción defensiva con x ≥ 60", "Episodio de presión con x ≥ 80", "Por decidir"),
    ("Pase largo", "≥ 32 yd", "≥ 35 yd", "Por decidir"),
    ("Pase progresivo", "−25 % de distancia, termina en x ≥ 48", "−25 % de distancia, termina en x ≥ 60", "Por decidir"),
    ("Línea defensiva (360)", "Promedio de los 4 más retrasados", "2.º jugador más retrasado", "Por decidir"),
    ("Nivel del rival", "Puntos de sus 17 partidos previos, en terciles", "Índice de Fuerza del Rival (IFR) de la temporada", "Por decidir"),
    ("Balón parado", "Posesión que abre el saque propio, en cualquier zona", "Córner, o tiro libre o banda con x ≥ 80", "Por decidir"),
    ("PPDA", "x ≥ 48 / pases rivales x ≤ 72", "Igual", "Igual en los dos"),
    ("Tramos de minuto", "15', con 90+ aparte", "15', el añadido va al último tramo", "Por decidir"),
]
DECISIONES = [
    ("Un solo marco", "¿Usamos el marco en Python como base y le sumamos lo que solo está en R (tipos de secuencia, episodios de presión, "
     "tipos de gol)? Faltan 8 definiciones por elegir (tabla de marcos)."),
    ("Las 5–6 ideas del reporte", "¿Cuáles de los hallazgos de abajo son la historia? Propuesta en 'Cómo quedaría el reporte final'."),
    ("Recomendaciones", "¿Qué candidatas entran y cómo las decimos en lenguaje de cancha?"),
    ("Material del análisis en R", "¿Qué tablas y figuras entran (tipos y recetas de gol, defensa bajo ataque, finales, rivales)? "
     "Se recalculan con la ventana y el marco que elijamos."),
]
DECIDIDO = [
    ("Ventana de datos", "Cifras de Ap 2021 – Cl 2025; lo de 2025–26 va como epílogo marcado."),
    ("Recuperación tras pérdida", "Se mide por evento, en los 5 s después de perder el balón."),
    ("Producto", "El reporte es el producto principal; la app es un complemento para explorar."),
]
ESTRUCTURA = [
    ("En un minuto", "5 frases con lo esencial"),
    ("El ADN del América", "Control, peligro y solidez con cualquier técnico (A1)"),
    ("Lo que agregó Jardine", "Salida corta, paciencia, pase atrás, presión de espera, balón parado (H7, H8, D4)"),
    ("Cómo ajusta", "Rival, marcador, localía, minuto y cambios (H4, B1, B4, D5)"),
    ("Por qué ganó y por qué no ganaron", "Liguilla de copa, semifinales de Ortiz, finales (C2, C3, C4)"),
    ("Puntos críticos", "Cierre del primer tiempo, contragolpes al perder, tres centrales, primer palo (B4, C6, D1b, H8)"),
    ("Lo que probamos y no cambia", "Visita defensiva, presión pasiva, ida y vuelta, plantilla, tiempo efectivo, formaciones (B2, B3, C5, D3, D7, D1)"),
    ("Recomendaciones", "Qué repetir y qué cambiar, con su evidencia y su límite (D1e y las que decidamos)"),
    ("Nuestro aporte", "ADN del Entrenador e Índice de Encaje (H1, H9, H10)"),
    ("Epílogo", "2025–26: qué cambió después (D8), marcado como fuera de la ventana"),
    ("Anexos", "Marco analítico (plegado) y glosario con enlaces desde el texto"),
    ("Complemento", "El explorador interactivo para ver cualquier periodo con las mismas gráficas"),
]


def tabla(filas, cabeza) -> str:
    th = "".join(f"<th>{html.escape(h)}</th>" for h in cabeza)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in f) + "</tr>" for f in filas)
    return f'<div class="tabla"><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div>'


def estado_chip(s: str) -> str:
    if s.startswith("Decidido") or s == "Cubierto" or s.startswith("Igual"):
        cls, icon = "good", "✓"
    elif s.startswith("Riesgo"):
        cls, icon = "warn", "!"
    elif s.startswith("Por decidir"):
        cls, icon = "warn", "?"
    else:
        cls, icon = "neutral", "~"
    return f'<span class="chip {cls}"><span aria-hidden="true">{icon}</span> {siglas(html.escape(s))}</span>'


def build() -> str:
    R = pd.read_parquet(A / "hipotesis_equipo.parquet")
    data = datos_graficas()
    n = R.veredicto.str.lower()
    conteo = {"se sostiene": int(n.str.startswith("se sostiene").sum()), "no cambia": int(n.str.startswith("no cambia").sum()),
              "no se sostiene": int(n.str.startswith("no se sostiene").sum()), "no alcanza": int(n.str.startswith("no alcanza").sum())}
    secciones = []
    for s in SECCIONES:
        rs = R[R.seccion == s]
        if rs.empty:
            continue
        figs = "".join(fig(*g) for g in GRAFICAS.get(s, []))
        secciones.append(f"""<section class="bloque">
  <h3>{html.escape(TITULO_SECCION[s])} <span class="ids">{", ".join(rs.id)}</span></h3>
  {figs}
  <div class="tarjetas">{"".join(tarjeta(r) for r in rs.itertuples())}</div>
</section>""")
    e = lambda s: siglas(html.escape(s))
    resumen = (f"Probamos {len(R)} ideas con la misma regla: {conteo['se sostiene']} se sostienen, {conteo['no cambia']} no cambian "
               f"el resultado, {conteo['no se sostiene']} no se sostienen y {conteo['no alcanza']} no alcanzan con los datos que hay.")
    return Template(TPL.read_text(encoding="utf-8")).substitute(
        fecha=FECHA, resumen=e(resumen),
        decisiones="".join(f"<li><strong>{e(a)}</strong><p>{e(b)}</p></li>" for a, b in DECISIONES),
        decidido="".join(f"<li><strong>{e(a)}.</strong> {e(b)}</li>" for a, b in DECIDIDO),
        alineacion="".join(f"<tr><td>{e(a)}</td><td>{e(b)}</td><td>{estado_chip(c)}</td></tr>" for a, b, c in ALINEACION),
        criterios="".join(f"<tr><td><strong>{e(a)}</strong></td><td class='num'>{b}</td><td>{e(c)}</td><td>{e(d)}</td></tr>"
                          for a, b, c, d in CRITERIOS),
        desvios="".join(f"<li><strong>{e(a)}.</strong> {e(b)}</li>" for a, b in DESVIOS),
        frameworks=tabla([(e(a), e(b), e(c), estado_chip(d)) for a, b, c, d in FRAMEWORKS],
                         ["Concepto", "Marco en Python (src/framework.py)", "Marco en R", "Estado"]),
        secciones="\n".join(secciones), estructura="".join(f"<li><strong>{e(a)}.</strong> {e(b)}</li>" for a, b in ESTRUCTURA),
        data=json.dumps(data, ensure_ascii=False).replace("</", "<\\/"), n=len(R), siglas=recuadro_siglas(),
        c_good=conteo["se sostiene"], c_neutral=conteo["no cambia"], c_bad=conteo["no se sostiene"], c_warn=conteo["no alcanza"])


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT} · {OUT.stat().st_size / 1e3:.0f} KB")


if __name__ == "__main__":
    main()

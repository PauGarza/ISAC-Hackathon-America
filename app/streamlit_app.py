"""ADN del Entrenador · Club América — explorador por periodo, congruente con el reporte.

Flujo: en la barra lateral se elige el técnico y el periodo (toda su etapa, un torneo, unas fechas o un partido);
las pestañas siguen las secciones del reporte. Dos tipos de gráfica:
- del periodo: se recalculan con el filtro (cubo por partido, src/cube.py);
- "del reporte": las mismas de src/final_report.py, fijas en Ap 2021 – Cl 2025, con su "Cómo leerla" y "Lo que muestra".
Datos: app/data (cubo y tablas de las gráficas del reporte; ver app/export_data.py). La app no lleva eventos.

Correr: streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import cube as K  # noqa: E402
from src import final_report as FR  # noqa: E402
from src.viz import COACH_COLOR, MUTED, RESULT_COLOR, RESULT_LABEL, TIER_COLOR, pitch_heat, radar  # noqa: E402

DATA = ROOT / "app" / "data"
CFG = {"displayModeBar": False}
BLOCKS = {
    "Con balón": ["Construcción", "Progresión", "Ocasiones", "Dominio"],
    "Sin balón": ["Presión", "Organización defensiva", "Transiciones"],
}
CSS = """<style>
.pie { color: #4b5563; font-size: 0.95rem; margin: -0.5rem 0 0.6rem; }
.muestra { font-size: 0.97rem; border-left: 3px solid #1d4e89; background: #f4f6f9; padding: 8px 12px;
           border-radius: 0 6px 6px 0; margin-bottom: 1.5rem; }
.rep { display: inline-block; font-size: 0.8rem; color: #1d4e89; border: 1px solid #1d4e89; border-radius: 4px;
       padding: 1px 8px; margin-top: 0.8rem; }
abbr[title] { text-decoration: underline dotted; text-underline-offset: 3px; cursor: help; }
.exp { color: #6f7782; font-size: 0.92em; }
</style>"""

st.set_page_config(page_title="ADN del Entrenador · Club América", page_icon="⚽", layout="wide")
st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ datos
@st.cache_data
def load() -> tuple[dict, dict, dict]:
    C = K.load(DATA)
    C["partidos"]["match_date"] = pd.to_datetime(C["partidos"].match_date)
    N = FR.base(DATA / "reporte", C)
    return C, N, FR.lecturas(N)


C, N, LEC = load()
P, CAT, EJES = C["partidos"], C["catalogo"].set_index("variable"), C["ejes"].eje.tolist()
FRIENDLY = {  # nombre para la marca (el catálogo técnico queda en "Cómo lo medimos")
    "gk_short_goal_kick_pct": "Saques de meta en corto (%)",
    "buildup_passes_per_seq": "Pases por jugada de salida",
    "buildup_success_pct": "Salidas que llegan a campo rival (%)",
    "press_resistance_own_third": "Precisión de pase presionado en su campo (%)",
    "prog_passes_per100": "Pases que hacen avanzar (por cada 100 pases)",
    "prog_carries_per100": "Conducciones que hacen avanzar (por cada 100 pases)",
    "prog_lane_left_pct": "Avanza por la izquierda (%)", "prog_lane_center_pct": "Avanza por el centro (%)",
    "prog_lane_right_pct": "Avanza por la derecha (%)",
    "progression_rate": "Jugadas que llegan al último tercio (%)",
    "pass_x_mean": "Altura media de sus pases (yd)", "long_pass_pct": "Pases largos (%)",
    "np_xg_per100poss": "Peligro creado (goles esperados, xG, por 100 posesiones)",
    "np_xg_per_shot": "Calidad de cada tiro (goles esperados, xG, por tiro)",
    "shots_per100poss": "Tiros por 100 posesiones", "box_touches_per100poss": "Toques en el área rival por 100 posesiones",
    "xg_share_open_play": "Peligro que nace del juego elaborado (%)", "xg_share_transition": "Peligro que nace de contragolpes (%)",
    "xg_share_set_piece": "Peligro que nace del balón parado (%)", "cross_xg_share": "Peligro que nace de centros (%)",
    "ppda": "Pases que deja dar al rival antes de presionar (PPDA; menos = presiona más)",
    "def_action_x_mean": "Altura a la que defiende (yd desde su portería)",
    "high_press_pct": "Acciones defensivas en campo rival (%)",
    "high_regains_per100opp": "Robos en campo rival (por 100 posesiones rivales)",
    "counterpress_per_loss": "Presión inmediata tras perder el balón",
    "opp_np_xg_per100poss": "Peligro que concede (goles esperados del rival, xG, por 100 posesiones)",
    "opp_shots_per100poss": "Tiros que concede por 100 posesiones rivales",
    "opp_f3_entry_pct": "Jugadas rivales que llegan a su último tercio (%)",
    "block_x_mean": "Altura del bloque defensivo (yd)",
    "transition_poss_pct": "Jugadas de contragolpe (%)",
    "transition_xg_per100poss": "Peligro al contragolpe (por 100 posesiones)",
    "opp_transition_xg_per100poss": "Peligro que concede al contragolpe (por 100 posesiones rivales)",
    "quick_regain_pct": "Balones perdidos que recupera en 5 s o menos (%)",
    "possession_time_pct": "Posesión (% del tiempo)",
    "field_tilt": "Dominio territorial (field tilt: % de los pases en el último tercio)",
    "obv_net": "Aporte generado menos aporte concedido (OBV)",
    "np_xg_diff": "Goles esperados (xG) a favor menos en contra",
}
CAT["etiqueta"] = [FRIENDLY.get(v, e) for v, e in zip(CAT.index, CAT.etiqueta)]


def marcador(r) -> str:
    return f"{r.goals_for:.0f}-{r.goals_against:.0f}"


# ------------------------------------------------------------------ selector (barra lateral)
def selector():
    sb = st.sidebar
    sb.markdown("## ADN del Entrenador\n**Club América · Liga MX**")
    coach = sb.selectbox("Técnico", [c for c in ["Jardine", "Ortiz", "Solari", "Almada"] if c in set(P.coach)])
    tipo = sb.radio("Periodo", ["Toda su etapa", "Un torneo", "Rango de fechas", "Un partido"])
    with sb.expander("Más filtros"):
        recientes = st.checkbox("Incluir temporadas recientes (2025–26)", value=coach == "Almada",
                                help="Por defecto, Apertura 2021 – Clausura 2025, como el reporte.")
        fase = st.radio("Fase del torneo", ["Todo", "Fase regular", "Liguilla"], horizontal=True,
                        help="Liguilla = cuartos, semifinal y final (y el play-in).")
        loc = st.multiselect("Localía", ["Local", "Visita"])
        riv = st.multiselect("Fuerza del rival", K.RIVAL_TIERS,
                             help="Puntos por partido del rival en sus 17 partidos previos, en tres grupos.")
    base = K.select(P, coach=coach, muestras=None if recientes else "ventana")
    if base.empty:   # p. ej. Almada: todos sus partidos son de 2026
        base = K.select(P, coach=coach)
    if tipo == "Un torneo":
        tor = base.drop_duplicates("torneo").sort_values("match_date").torneo.tolist()
        base = K.select(base, torneos=sb.selectbox("Torneo", tor[::-1]))
    elif tipo == "Rango de fechas" and len(base):
        d0, d1 = base.match_date.min().date(), base.match_date.max().date()
        rng = sb.date_input("Del … al …", (d0, d1), min_value=d0, max_value=d1)
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            base = K.select(base, desde=rng[0], hasta=rng[1])
    elif tipo == "Un partido" and len(base):
        opts = {f"{r.match_date:%d %b %Y} · {'vs' if r.localia == 'Local' else 'en'} {r.opponent} ({marcador(r)})": r.match_id
                for r in base.sort_values("match_date", ascending=False).itertuples()}
        base = K.select(base, match_ids=opts[sb.selectbox("Partido", list(opts))])
    if tipo != "Un partido":
        base = K.select(base, localia=loc or None, rival=riv or None, fase=None if fase == "Todo" else fase)
    others = [c for c in ["Jardine", "Ortiz", "Solari"] if c != coach] + ["América típico"]
    comp = sb.selectbox("Comparar con", others, help="Toda la etapa de otro técnico, o el América promedio de 2021 a 2025.")
    return base, coach, tipo, comp


def comparison(comp: str) -> tuple[pd.DataFrame, str]:
    if comp == "América típico":
        return K.select(P, muestras="ventana"), "América típico 2021–2025"
    return K.select(P, coach=comp, muestras="ventana"), f"{comp} (toda su etapa)"


# ------------------------------------------------------------------ piezas visuales
def show(fig: go.Figure) -> None:
    st.plotly_chart(fig, theme=None, config=CFG, width="stretch")


def del_reporte(gid: str) -> None:
    """Gráfica del reporte, idéntica y fija (Ap 2021 – Cl 2025), con su 'Cómo leerla' y 'Lo que muestra'."""
    st.markdown('<span class="rep">Del reporte · Apertura 2021 – Clausura 2025 · no cambia con los filtros</span>',
                unsafe_allow_html=True)
    show(FR.FIGURAS[gid](N))
    s = set()
    st.markdown(f'<p class="pie"><b>Cómo leerla.</b> {FR.e(FR.pie(gid, N), s)}</p>'
                f'<p class="muestra"><b>Lo que muestra.</b> {FR.e(LEC[gid], s)}</p>', unsafe_allow_html=True)


def indicator_panel(sel, base, base_label, criterios):
    """Cada indicador del periodo frente a los partidos de la comparación (más que X de cada 100 partidos)."""
    cols = [v for v in CAT.index if CAT.loc[v, "criterio"] in criterios]
    t = K.indicadores(sel, cols, base=base).join(CAT[["etiqueta", "criterio", "dirección"]]).dropna(subset=["valor"])
    if t.empty:
        st.info("Sin datos para estos indicadores en la selección.")
        return
    for crit in criterios:
        d = t[t.criterio == crit]
        if d.empty:
            continue
        fig = go.Figure(go.Scatter(
            x=d.pct_partidos_base, y=d.etiqueta, mode="markers", marker=dict(size=12, color=COACH_COLOR.get(sel.coach.iat[0], MUTED)),
            customdata=np.c_[d.valor, d.base, d["dirección"]],
            hovertemplate="%{y}<br>periodo %{customdata[0]:.2f} · comparación %{customdata[1]:.2f}"
                          "<br>supera a %{x:.0f} de cada 100 partidos de la comparación<br>%{customdata[2]}<extra></extra>"))
        fig.add_vline(x=50, line=dict(color=MUTED, dash="dot"))
        show(FR.lay(fig, 60 + 38 * len(d), title=dict(text=crit, font=dict(size=14)), showlegend=False,
                    margin=dict(l=10, r=16, t=40, b=44),
                    xaxis=dict(range=[0, 100], tickvals=[0, 25, 50, 75, 100], title=f"frente a los partidos de {base_label} (50 = igual)"),
                    yaxis=dict(autorange="reversed", gridcolor="white")))


# ------------------------------------------------------------------ página
sel, coach, tipo, comp = selector()
base, base_label = comparison(comp)
info = K.nivel_muestra(len(sel))
periodo = {"Toda su etapa": "toda su etapa", "Un torneo": sel.torneo.iat[0] if len(sel) else "",
           "Rango de fechas": "rango de fechas", "Un partido": "un partido"}[tipo]

st.title("ADN del Entrenador · Club América")
st.caption(f"Viendo: **{coach} · {periodo}** · comparado con: **{base_label}** · Datos: StatsBomb · "
           "Pasa el cursor sobre las gráficas y sobre las siglas subrayadas.")
if info["nivel"] == "vacio":
    st.warning(info["aviso"])
    st.stop()

r, xp = K.resumen(sel), K.puntos_esperados(sel)
c1, c2, c3, c4 = st.columns(4)
c1.metric("Partidos", r["partidos"])
c2.metric("Ganados · empatados · perdidos", f"{r['ganados']} · {r['empatados']} · {r['perdidos']}")
c3.metric("Puntos por partido", f"{r['puntos_por_partido']:.2f}",
          delta=f"{xp['diferencia']:+.2f} frente a lo que merecía" if xp else None,
          help="Lo que 'merecía': repetimos cada partido miles de veces con las ocasiones que tuvo cada equipo "
               "y promediamos los puntos. Positivo = sacó más de lo que merecía.")
c4.metric("Ocasiones (xG) a favor / en contra", f"{r['xg_favor']:.2f} / {r['xg_contra']:.2f}",
          help="xG = goles esperados: qué tan claras fueron las ocasiones de cada equipo (sin penales), por partido.")
if info["nivel"] not in ("era", "torneo"):
    st.warning(info["aviso"])
if len(sel) == 1:
    m1 = sel.iloc[0]
    st.markdown(f"**¿Merecía el resultado?** Con las ocasiones que tuvo cada equipo, el América ganaba este partido "
                f"**{m1.p_victoria:.0%}** de las veces, empataba {m1.p_empate:.0%} y perdía {m1.p_derrota:.0%}.")

with st.expander(f"Partidos del periodo ({len(sel)})"):
    fig = go.Figure()
    for res, g in sel.groupby("result"):
        fig.add_trace(go.Scatter(
            x=g.match_date, y=g.xg_favor - g.xg_contra, mode="markers", name=RESULT_LABEL[res],
            marker=dict(size=11, color=RESULT_COLOR[res], symbol=["circle" if l == "Local" else "diamond" for l in g.localia],
                        line=dict(width=1, color="white")),
            customdata=np.c_[g.opponent, g.localia, [marcador(x) for x in g.itertuples()]],
            hovertemplate="%{x|%d %b %Y} · %{customdata[1]} vs %{customdata[0]} · %{customdata[2]}"
                          "<br>ocasiones (xG) a favor − en contra %{y:+.2f}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    show(FR.lay(fig, 280, yaxis=dict(title="xG a favor − en contra")))
    st.caption("Círculo = local · rombo = visita. Arriba de la línea, el América tuvo mejores ocasiones que su rival.")
    st.dataframe(sel.sort_values("match_date", ascending=False).assign(
        fecha=lambda d: d.match_date.dt.strftime("%d %b %Y"), marcador=lambda d: [marcador(x) for x in d.itertuples()],
        xg_favor=lambda d: d.xg_favor.round(2), xg_contra=lambda d: d.xg_contra.round(2))
        [["fecha", "torneo", "localia", "opponent", "rival_nivel", "marcador", "xg_favor", "xg_contra", "sistema"]]
        .rename(columns={"localia": "localía", "opponent": "rival", "rival_nivel": "nivel del rival",
                         "xg_favor": "xG a favor", "xg_contra": "xG en contra"}),
        hide_index=True, width="stretch", height=min(400, 40 + 35 * len(sel)))

T = st.tabs(["El ADN", "Con balón", "Sin balón", "Balón parado y jugadores", "Cómo ajusta", "El ADN ganador",
             "Puntos críticos", "Cómo lo medimos"])

# --- 1 · El ADN
with T[0]:
    st.markdown("#### ¿Qué es del club y qué es del técnico?")
    left, right = st.columns(2)
    with left:
        series = {f"{coach} · {periodo}": K.adn_percentil(sel, C["adn_ref"], EJES),
                  base_label: K.adn_percentil(base, C["adn_ref"], EJES)}
        show(radar(series, "ADN del periodo: de 0 a 100 frente a los técnicos de la Liga MX"))
        st.markdown('<p class="pie"><b>Cómo leerla.</b> 50 = el técnico típico de la liga. Cada rasgo se compara con la liga '
                    'del mismo torneo y descuenta la fuerza del rival y la localía.'
                    + ("" if info["rankings"] else " <b>Con pocos partidos es solo orientativo.</b>") + "</p>",
                    unsafe_allow_html=True)
        sis = sel.sistema.value_counts()
        st.caption("Sistemas titulares: " + " · ".join(f"{k} ({v} partidos)" for k, v in sis.head(4).items()))
    with right:
        del_reporte("g-radar")
    del_reporte("g-encaje")

# --- 2 · Con balón
with T[1]:
    st.markdown("#### ¿De dónde vienen sus ocasiones y hasta dónde progresa?")
    ids = sel.match_id
    a, b = st.columns(2)
    with a:
        show(pitch_heat(K.rejilla(C["zonas"], ids, "tiros", "xg"), "Ocasiones (xG) por partido, según dónde se tiró", "{:.2f}", "Greens"))
    with b:
        show(pitch_heat(K.rejilla(C["zonas"], ids, "pases_progresivos"), "Pases que hacen avanzar, por partido (donde terminan)"))
    st.caption("Canchas del periodo, en el sentido del América: ataca hacia la derecha.")
    del_reporte("g-tipos")
    with st.expander("Todos los indicadores con balón"):
        indicator_panel(sel, base, base_label, BLOCKS["Con balón"])

# --- 3 · Sin balón
with T[2]:
    st.markdown("#### ¿Dónde roba el balón y desde dónde le hacen daño?")
    ids = sel.match_id
    a, b = st.columns(2)
    with a:
        show(pitch_heat(K.rejilla(C["zonas"], ids, "recuperaciones"), "Robos por partido"))
    with b:
        show(pitch_heat(K.rejilla(C["zonas"], ids, "tiros_rival", "xg"), "Ocasiones del rival (xG) por partido", "{:.2f}", "Reds"))
    st.caption("Canchas del periodo, en el sentido del América: su portería está a la izquierda.")
    rv = K.recuperacion_valor(C["recuperaciones"], ids)
    fig = go.Figure(go.Bar(x=rv.zona, y=rv.por_partido, marker_color=COACH_COLOR.get(coach, MUTED),
                           text=[f"{v:.1f} robos · {t:.0f} % acaban en tiro" for v, t in zip(rv.por_partido, rv.pct_tiro.fillna(0))],
                           textposition="outside", cliponaxis=False, hovertemplate="%{x}: %{y:.1f} robos por partido<extra></extra>"))
    show(FR.lay(fig, 320, title=dict(text="¿Cuánto vale robar en cada zona?", font=dict(size=14)), showlegend=False,
                yaxis=dict(title="robos por partido", range=[0, rv.por_partido.max() * 1.3])))
    with st.expander("Todos los indicadores sin balón"):
        indicator_panel(sel, base, base_label, BLOCKS["Sin balón"])

# --- 4 · Balón parado y jugadores
with T[3]:
    st.markdown("#### ¿Cuánto peligro da y concede a balón parado?")
    bp = K.balon_parado(C["balon_parado"], sel.match_id, ["lado", "kind"])
    fig = go.Figure([go.Bar(x=d.kind, y=d.xg_por_partido, name=lado, marker_color=col,
                            customdata=np.c_[d.por_partido, d.pct_tiro],
                            hovertemplate="%{x}: %{y:.2f} xG por partido<br>%{customdata[0]:.1f} jugadas · %{customdata[1]:.0f} % con tiro<extra>" + lado + "</extra>")
                     for lado, col in [("A favor", "#1baf7a"), ("En contra", "#e34948")] for d in [bp[bp.lado == lado]]])
    show(FR.lay(fig, 320, barmode="group", yaxis=dict(title="ocasiones (xG) por partido")))
    st.caption("Jugadas que abre el saque del propio equipo (córner, tiro libre, saque de banda).")
    st.markdown("#### ¿Con quién juega y quién genera el valor?")
    j = K.jugadores_periodo(C["jugadores"], sel)
    top = j.head(15).iloc[::-1]
    fig = go.Figure(go.Bar(x=top.pct_minutos, y=top.jugador, orientation="h", marker_color=COACH_COLOR.get(coach, MUTED),
                           customdata=np.c_[top.titularidades, top.pct_obv_pos, top.rol.fillna("—")],
                           hovertemplate="%{y}: %{x:.0f} % de los minutos<br>%{customdata[0]} de titular · "
                                         "%{customdata[1]:.1f} % del aporte del equipo · rol: %{customdata[2]}<extra></extra>"))
    a, b = st.columns([1.2, 1])
    with a:
        show(FR.lay(fig, 520, showlegend=False, title=dict(text="% de los minutos posibles", font=dict(size=14)),
                    xaxis=dict(range=[0, 105]), yaxis=dict(gridcolor="white")))
    with b:
        st.caption("Aporte = cuánto mejora cada acción con balón las opciones de gol del equipo. "
                   "Se cuentan los torneos completos que toca el periodo.")
        st.dataframe(j.nlargest(10, "pct_obv_pos")[["jugador", "linea", "pct_obv_pos"]]
                     .rename(columns={"linea": "línea", "pct_obv_pos": "% del aporte del equipo"}).round(1),
                     hide_index=True, width="stretch")

# --- 5 · Cómo ajusta
with T[4]:
    st.markdown("#### ¿Qué cambia cuando va ganando o perdiendo?")
    if tipo == "Toda su etapa" and coach in FR.COACHES and len(sel) == len(K.select(P, coach=coach, muestras="ventana")):
        d = None   # sin filtros: la misma cifra del reporte
    else:
        d = pd.concat([K.efecto_marcador(C["tramos"], sel.match_id, v).assign(variable=v)
                       for v in ["field_tilt", "possession_time_pct"]])
    if d is not None and d.dropna(subset=["efecto"]).empty:
        st.info(f"Hacen falta al menos {K.MIN_TORNEO} partidos para comparar marcadores.")
    else:
        show(FR.f_marcador(N, coach, d))
        s = set()
        st.markdown(f'<p class="pie"><b>Cómo leerla.</b> {FR.e(FR.pie("g-marcador", N, coach), s)}</p>', unsafe_allow_html=True)
    st.markdown("#### ¿Juega igual de local y de visita, contra fuertes y débiles?")
    rows = [{"contexto": f"{dim}: {v}", "partidos": len(g), "puntos por partido": g.puntos.mean(),
             "posesión (%)": g.possession_time_pct.mean(), "dominio territorial (%)": g.field_tilt.mean(),
             "pases que deja dar antes de presionar": g.ppda.mean(), "xG a favor": g.xg_favor.mean(), "xG en contra": g.xg_contra.mean()}
            for dim, key in [("Localía", "localia"), ("Rival", "rival_nivel")] for v, g in sel.groupby(key)]
    st.dataframe(pd.DataFrame(rows).set_index("contexto").round(2), width="stretch")
    st.markdown("#### Rivales fuertes, medios y débiles")
    st.markdown('<span class="rep">Del reporte · Apertura 2021 – Clausura 2025 · no cambia con los filtros</span>',
                unsafe_allow_html=True)
    txt, niv = FR.niveles_rival(N)
    st.markdown(f'<div class="pie">{FR.siglas(txt, set())}</div>', unsafe_allow_html=True)
    st.dataframe(niv, hide_index=True, width="stretch", column_config={
        c: st.column_config.NumberColumn(format="%.2f") for c in ["Puntos por partido", "Según sus ocasiones", "Jardine: puntos por partido"]}
        | {c: st.column_config.NumberColumn(format="%.0f %%") for c in ["Victorias (%)", "Posesión (%)"]})
    st.caption(FR.NIVELES_NOTA)
    fc, fcb = sel.primer_cambio_descanso.mean() * 100, base.primer_cambio_descanso.mean() * 100
    st.metric("Primer cambio en el descanso", f"{fc:.0f} % de los partidos",
              delta=f"{fc - fcb:+.0f} puntos frente a {base_label} ({fcb:.0f} %)", delta_color="off")

# --- 6 · El ADN ganador
with T[5]:
    st.markdown("#### ¿Qué hizo distinto el América campeón?")
    del_reporte("g-torneos")
    del_reporte("g-series")
    st.markdown(f"#### {coach}, torneo a torneo")
    show(FR.f_epilogo(N, coach))
    st.markdown(f'<p class="pie"><b>Cómo leerla.</b> {FR.e(FR.pie("g-epilogo", N, coach), set())}</p>', unsafe_allow_html=True)

# --- 7 · Puntos críticos
with T[6]:
    st.markdown("#### ¿Dónde se le escapan los partidos?")
    for gid in ["g-minuto", "g-derrotas", "g-fuertes"]:
        del_reporte(gid)
    st.markdown("#### ¿Contra quién le fue mejor (o peor) de lo que jugó?")
    rv = K.rivales(sel)
    rv = rv[rv.partidos >= (3 if len(sel) >= 40 else 1)]
    if rv.empty:
        st.info("No hay rivales con suficientes partidos en este periodo.")
    else:
        fig = go.Figure(go.Scatter(
            x=rv.xpts, y=rv.puntos, mode="markers+text", text=rv.opponent, textposition="top center", textfont=dict(size=10),
            marker=dict(size=8 + rv.partidos * 1.5, color=[TIER_COLOR.get(n, MUTED) for n in rv.nivel], opacity=0.8,
                        line=dict(width=1, color="white")),
            customdata=np.c_[rv.partidos, rv.nivel.fillna("—"), rv.pct_victorias],
            hovertemplate="%{text} (%{customdata[1]})<br>%{customdata[0]} partidos · %{customdata[2]:.0f} % victorias"
                          "<br>sacó %{y:.2f} puntos por partido · por sus ocasiones, %{x:.2f}<extra></extra>"))
        fig.add_shape(type="line", x0=0, y0=0, x1=3, y1=3, line=dict(color=MUTED, dash="dot"))
        ejes = dict(range=[-0.15, 3.15], tickvals=[0, 1, 2, 3])
        show(FR.lay(fig, 520, showlegend=False,
                    xaxis=dict(ejes, title="puntos por partido que le daban sus ocasiones (xG)"),
                    yaxis=dict(ejes, title="puntos por partido que sacó de verdad", ticktext=["0 perdió todo", "1 empató todo", "2", "3 ganó todo"])))
        st.markdown('<p class="pie"><b>Cómo leerla.</b> Cada punto es un rival. Los dos ejes son puntos <b>por partido</b> '
                    '(no acumulados), de 0 a 3: 3 es ganarle todos los partidos, 1 empatarlos todos. '
                    'Arriba de la línea punteada sacó más puntos de los que le daban sus ocasiones: fue muy efectivo o tuvo suerte; '
                    'abajo, jugó para más y no le alcanzó. Color = nivel del rival (rojo fuerte, gris medio, verde débil); '
                    'tamaño = partidos.</p>', unsafe_allow_html=True)

# --- 8 · Cómo lo medimos
with T[7]:
    st.markdown("""
**De dónde salen los datos.** StatsBomb registra cada acción con balón de cada partido (unas 3,500 por partido). Aquí están todos los partidos del América desde el Apertura 2021; por defecto, del Apertura 2021 al Clausura 2025, como el reporte.

**Un mismo diccionario para todo.** Cada concepto (posesión, transición, presionar arriba, balón parado) se define una sola vez, y todas las cifras usan esas mismas definiciones.

**El ADN del Entrenador** resume el estilo en 8 rasgos. Cada rasgo se compara con la liga **del mismo torneo**, descuenta la fuerza del rival y la localía, y va de 0 a 100 frente a los técnicos de la Liga MX (50 es el típico).

**Cuántos partidos hacen falta.** Un partido suelto dice si se pareció al ADN del técnico; con menos de 5 se ven tendencias; con un torneo, el estilo de ese torneo; con toda una etapa, el ADN del técnico.

| Sigla | Qué quiere decir |
|---|---|
| xG (goles esperados) | Qué tan clara fue cada ocasión: la probabilidad de que ese tiro sea gol. Sumado, cuántos goles "merecía" un equipo |
| Aporte (OBV) | Cuánto mejora o empeora cada acción con balón las opciones de marcar o de recibir gol |
| PPDA | Pases que deja dar al rival antes de intentar robar. Menos = presiona más |
| Dominio territorial (field tilt) | De los pases en el último tercio, qué % son del América |
""")
    with st.expander("Diccionario de indicadores"):
        st.dataframe(CAT[["etiqueta", "criterio", "definición", "dirección"]], width="stretch")

"""ADN del Entrenador · Club América — explorador por periodo.

Flujo: primero se elige el periodo (técnico, torneo, fechas o un partido) y el contexto (localía, fuerza del
rival); después se despliega el análisis. Selección inicial: Jardine, Ap 2021 – Cl 2025.
Todo sale del cubo de agregados por partido (src/cube.py → app/data/): la app no lleva eventos.
La app no lleva conclusiones escritas a mano: todo texto se calcula con la selección. La historia fija vive en el
reporte (reports/final/).

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
from src.viz import (MUTED, RESULT_COLOR, RESULT_LABEL, STAGE_COLOR, LINE, TIER_COLOR,  # noqa: E402
                     pitch_heat, radar, torneo_short)

DATA = ROOT / "app" / "data"
BLOCKS = {
    "Con balón": ["Construcción", "Progresión", "Ocasiones", "Dominio"],
    "Sin balón": ["Presión", "Organización defensiva", "Transiciones"],
}

st.set_page_config(page_title="ADN del Entrenador · Club América", page_icon="⚽", layout="wide")


# ------------------------------------------------------------------ datos
@st.cache_data
def load() -> dict[str, pd.DataFrame]:
    d = K.load(DATA)
    d["partidos"]["match_date"] = pd.to_datetime(d["partidos"].match_date)
    return d


C = load()
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


# ------------------------------------------------------------------ selector (barra lateral)
def selector():
    sb = st.sidebar
    sb.markdown("## ADN del Entrenador\n**Club América · Liga MX**")
    coaches = [c for c in ["Jardine", "Ortiz", "Solari", "Almada", "Cervantes"] if c in set(P.coach)]
    coach = sb.multiselect("Técnico", coaches, default=["Jardine"])
    otras = sb.checkbox("Incluir temporadas recientes (Ap 2025 y 2026)", value=False,
                        help="Por defecto se analizan los torneos Ap 2021 – Cl 2025.")
    base = K.select(P, coach=coach or None, muestras=None if otras else "ventana")
    if base.empty and not otras:   # p. ej. Almada: todos sus partidos son de 2026
        base = K.select(P, coach=coach or None)
        sb.caption("Se muestran sus partidos más recientes (2025–2026).")
    tipo = sb.radio("Periodo", ["Toda la era", "Torneo", "Rango de fechas", "Un partido"])
    if tipo == "Torneo":
        tor = base.drop_duplicates("torneo").sort_values("match_date").torneo.tolist()
        pick = sb.multiselect("Torneo(s)", tor, default=tor[-1:] if tor else [])
        base = K.select(base, torneos=pick or None)
    elif tipo == "Rango de fechas" and len(base):
        d0, d1 = base.match_date.min().date(), base.match_date.max().date()
        rng = sb.date_input("Del … al …", (d0, d1), min_value=d0, max_value=d1)
        if isinstance(rng, (tuple, list)) and len(rng) == 2:
            base = K.select(base, desde=rng[0], hasta=rng[1])
    elif tipo == "Un partido" and len(base):
        opts = {f"{r.match_date:%d %b %Y} · {'vs' if r.localia == 'Local' else 'en'} {r.opponent} "
                f"({r.goals_for}-{r.goals_against})": r.match_id for r in base.sort_values("match_date", ascending=False).itertuples()}
        mid = opts[sb.selectbox("Partido", list(opts))]
        base = K.select(base, match_ids=mid)
    if tipo != "Un partido":
        sb.markdown("**Contexto**")
        fase = sb.radio("Fase del torneo", ["Todo", "Fase regular", "Liguilla"], horizontal=True,
                        help="Liguilla = cuartos, semifinal y final (y el play-in).")
        loc = sb.multiselect("Localía", ["Local", "Visita"], default=[])
        riv = sb.multiselect("Fuerza del rival", K.RIVAL_TIERS, default=[],
                             help="Puntos por partido del rival en sus 17 partidos previos, en terciles de la liga.")
        base = K.select(base, localia=loc or None, rival=riv or None, fase=None if fase == "Todo" else fase)
    others = [c for c in ["Ortiz", "Jardine", "Solari", "Almada"] if c not in coach] + ["América típico"]
    comp = sb.selectbox("Comparar con", others,
                        help="Toda la etapa del técnico elegido, o el América promedio de 2021 a 2025.")
    label = f"{', '.join(coach) or 'Todos'} · {tipo.lower()}"
    return base, label, comp


def comparison(comp: str) -> tuple[pd.DataFrame, str]:
    if comp == "América típico":
        return K.select(P, muestras="ventana"), "América típico 2021–2025"
    if comp == "Almada":
        return K.select(P, coach="Almada"), "Almada (2026)"
    return K.select(P, coach=comp, muestras="ventana"), f"{comp} (toda su etapa)"


# ------------------------------------------------------------------ piezas visuales (las de cancha y radar: src/viz.py)
def indicator_panel(sel, base, base_label, criterios):
    """Para cada indicador: valor del periodo, valor de la comparación y dónde cae el periodo entre los partidos
    de la comparación (más que X de cada 10 partidos)."""
    cols = [v for v in CAT.index if CAT.loc[v, "criterio"] in criterios]
    t = K.indicadores(sel, cols, base=base).join(CAT[["etiqueta", "criterio", "dirección"]])
    t = t.dropna(subset=["valor"])
    if t.empty:
        st.info("Sin datos para estos indicadores en la selección.")
        return
    for crit in criterios:
        d = t[t.criterio == crit]
        if d.empty:
            continue
        fig = go.Figure()
        fig.add_vline(x=50, line=dict(color=MUTED, dash="dot"))
        fig.add_trace(go.Scatter(x=d.pct_partidos_base, y=d.etiqueta, mode="markers+text",
                                 marker=dict(size=12, color="#1baf7a"),
                                 text=[f"{v:.2f}".rstrip("0").rstrip(".") + f"  (comp. {b:.2f}".rstrip("0").rstrip(".") + ")"
                                       for v, b in zip(d.valor, d.base)],
                                 textposition="middle right", textfont=dict(size=11),
                                 customdata=np.c_[d.valor, d.base, d["dirección"]],
                                 hovertemplate="%{y}<br>periodo %{customdata[0]:.2f} · comparación %{customdata[1]:.2f}"
                                               "<br>supera a %{x:.0f} de cada 100 partidos de la comparación"
                                               "<br>%{customdata[2]}<extra></extra>"))
        fig.update_layout(title=dict(text=crit, font=dict(size=13)), height=60 + 38 * len(d),
                          margin=dict(l=10, r=10, t=35, b=25), showlegend=False,
                          xaxis=dict(range=[0, 135], tickvals=[0, 25, 50, 75, 100],
                                     title=f"0–100: el periodo frente a los partidos de {base_label} (50 = igual)"),
                          yaxis=dict(autorange="reversed"), plot_bgcolor="white")
        st.plotly_chart(fig, width="stretch")


# ------------------------------------------------------------------ página
sel, label, comp = selector()
base, base_label = comparison(comp)
info = K.nivel_muestra(len(sel))

st.title("ADN del Entrenador · Club América")
st.caption(f"Viendo: **{label}** · comparado con: **{base_label}** · Datos: StatsBomb")

if info["nivel"] == "vacio":
    st.warning(info["aviso"])
    st.stop()

r = K.resumen(sel)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Partidos", r["partidos"])
c2.metric("Récord (G-E-P)", f"{r['ganados']}-{r['empatados']}-{r['perdidos']}")
xp = K.puntos_esperados(sel)
c3.metric("Puntos por partido", f"{r['puntos_por_partido']:.2f}",
          delta=f"{xp['diferencia']:+.2f} frente a lo que merecía" if xp else None,
          help="Lo que 'merecía': repetimos cada partido miles de veces con las ocasiones que tuvo cada equipo "
               f"y promediamos los puntos ({xp.get('xpts', float('nan')):.2f} por partido). Positivo = sacó más de lo que merecía.")
c4.metric("Goles a favor / en contra", f"{r['goles_favor']:.1f} / {r['goles_contra']:.1f}")
c5.metric("Goles esperados (xG) a favor / en contra", f"{r['xg_favor']:.2f} / {r['xg_contra']:.2f}",
          help="xG = calidad de las ocasiones: cuántos goles 'merecía' cada equipo por las oportunidades que tuvo (sin penales).")
(st.info if info["nivel"] in ("era", "torneo") else st.warning)(info["aviso"])
if len(sel) == 1:
    m1 = sel.iloc[0]
    st.markdown(f"**¿Merecía el resultado?** Con las ocasiones que tuvo cada equipo, el América ganaba este partido "
                f"**{m1.p_victoria:.0%}** de las veces, empataba {m1.p_empate:.0%} y perdía {m1.p_derrota:.0%}.")

# --- calendario de rivales
with st.expander(f"Calendario: contra quién jugó ({len(sel)} partidos)", expanded=info["nivel"] != "era"):
    fig = go.Figure()
    for res, g in sel.groupby("result"):
        fig.add_trace(go.Scatter(
            x=g.match_date, y=g.xg_favor - g.xg_contra, mode="markers", name=RESULT_LABEL[res],
            marker=dict(size=11, color=RESULT_COLOR[res], symbol=["circle" if l == "Local" else "diamond" for l in g.localia],
                        line=dict(width=1, color="white")),
            customdata=np.c_[g.opponent, g.rival_nivel.fillna("—"), g.localia, g.goals_for, g.goals_against, g.torneo],
            hovertemplate="%{x|%d %b %Y} · %{customdata[2]} vs %{customdata[0]} (rival %{customdata[1]})"
                          "<br>%{customdata[3]}-%{customdata[4]} · ocasiones (xG) a favor − en contra %{y:+.2f}<br>%{customdata[5]}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="¿Quién tuvo mejores ocasiones? (xG a favor − en contra)",
                      legend=dict(orientation="h", y=1.15), plot_bgcolor="white")
    st.plotly_chart(fig, width="stretch")
    st.caption("Círculo = local · rombo = visita. Arriba de la línea, el América tuvo mejores ocasiones que su rival. "
               "Antes de leer un cambio de estilo, revisa contra quién jugó en ese tramo.")
    lv = sel.rival_nivel.value_counts().reindex(K.RIVAL_TIERS).fillna(0).astype(int)
    st.caption("Rivales del periodo: " + " · ".join(f"{k} {v}" for k, v in lv.items()))
    st.dataframe(sel.sort_values("match_date", ascending=False).assign(
        fecha=lambda d: d.match_date.dt.strftime("%d %b %Y"), marcador=lambda d: d.goals_for.astype(str) + "-" + d.goals_against.astype(str))
        [["fecha", "torneo", "coach", "localia", "opponent", "rival_nivel", "marcador", "xg_favor", "xg_contra", "sistema"]]
        .rename(columns={"coach": "técnico", "localia": "localía", "opponent": "rival", "rival_nivel": "nivel del rival",
                         "xg_favor": "xG a favor", "xg_contra": "xG en contra"}),
        hide_index=True, width="stretch", height=min(400, 40 + 35 * len(sel)))

TAB_NAMES = ["Identidad", "Torneo a torneo", "Con balón", "Sin balón", "Balón parado", "Contexto", "Rivales",
             "Jugadores", "Cómo lo medimos"]
T = dict(zip(TAB_NAMES, st.tabs(TAB_NAMES)))

# --- Identidad
with T["Identidad"]:
    ref = C["adn_ref"]
    adn = K.adn_percentil(sel, ref, EJES)
    adn_b = K.adn_percentil(base, ref, EJES)
    who = sel.coach.mode().iat[0]
    left, right = st.columns([1.1, 1])
    with left:
        series = {f"{who} · selección": adn, base_label: adn_b}
        if info["nivel"] != "era":
            era = K.select(P, coach=who, muestras="ventana" if who != "Almada" else None)
            series[f"{who} · toda su etapa"] = K.adn_percentil(era, ref, EJES)
        st.plotly_chart(radar(series, "ADN del técnico: de 0 a 100 frente a los técnicos de la Liga MX"), width="stretch")
        st.caption("100 = el técnico de la liga que más lo hace; 50 = el promedio. Cada rasgo se compara con la liga del "
                   "mismo torneo y descuenta la fuerza del rival y la localía. "
                   + ("" if info["rankings"] else "**Con pocos partidos es solo orientativo.**"))
    with right:
        t = pd.DataFrame({"selección": adn.round(0), base_label: adn_b.round(0)})
        t["diferencia"] = t.iloc[:, 0] - t.iloc[:, 1]
        st.markdown("#### Rasgos del ADN (de 0 a 100 frente a la liga)")
        st.dataframe(t, width="stretch")
        top = t.diferencia.abs().sort_values(ascending=False).index[:3]
        st.markdown("**Lo que más lo distingue de la comparación:** " + "; ".join(
            f"{e.lower()} {t.loc[e, 'diferencia']:+.0f}" for e in top))
        sis = sel.sistema.value_counts()
        st.caption("Sistemas titulares: " + " · ".join(f"{k} ({v} partidos)" for k, v in sis.head(4).items()))

# --- Torneo a torneo
with T["Torneo a torneo"]:
    TT = K.torneos(P)
    st.markdown("#### ¿Cómo jugó cada torneo, en la fase regular y en la liguilla?")
    st.caption("Todos los torneos del América, sin importar el filtro de la izquierda.")
    TT["t"] = TT.torneo.map(torneo_short) + " · " + TT.tecnico
    a, b = st.columns(2)
    for col, (reg, lig, title, ytitle) in zip([a, b], [
            ("posesion_regular", "posesion_liguilla", "Posesión: fase regular frente a liguilla", "% del tiempo"),
            ("ppda_regular", "ppda_liguilla", "Presión: pases que deja dar al rival antes de presionar",
             "más alto = presiona menos")]):
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=TT.t, y=TT[reg], mode="lines+markers", name="Fase regular",
                                 line=dict(color=LINE, width=2), marker=dict(size=7, color=MUTED)))
        fig.add_trace(go.Scatter(x=TT.t, y=TT[lig], mode="markers", name="Liguilla",
                                 marker=dict(size=[18 if l == "Campeón" else 12 for l in TT.llego],
                                             symbol=["star" if l == "Campeón" else "circle" for l in TT.llego],
                                             color=[STAGE_COLOR.get(l, MUTED) for l in TT.llego], line=dict(width=1, color="white")),
                                 customdata=TT.llego, hovertemplate="%{x}<br>liguilla: %{y:.1f}<br>%{customdata}<extra></extra>"))
        fig.update_layout(title=dict(text=title, font=dict(size=13)), height=360, margin=dict(l=10, r=10, t=45, b=10),
                          yaxis_title=ytitle, plot_bgcolor="white", legend=dict(orientation="h", y=1.12),
                          xaxis=dict(tickangle=-45, tickfont=dict(size=10)))
        col.plotly_chart(fig, width="stretch")
    st.caption("★ dorada = liguilla que terminó en título. Liguilla: cuartos, semifinal y final.")
    lg = K.liguilla_ganadora(P, C["tramos"], C["balon_parado"])
    if {True, False} <= set(lg.index):
        _tt = TT[TT.llego != "En curso"].groupby(TT.llego.eq("Campeón"))[["posesion_regular", "xg_favor_regular"]].mean()
        cmp_ = pd.DataFrame({
            "Torneos": lg.torneos, "Partidos de liguilla": lg.partidos,
            "Posesión en liguilla (%)": lg.posesion, "Posesión en liguilla con el partido empatado (%)": lg.posesion_empate,
            "Pases que deja dar antes de presionar (PPDA), liguilla": lg.ppda,
            "% de los minutos de liguilla ganando": lg.pct_min_ganando,
            "Posesión en fase regular (%)": _tt.posesion_regular,
            "Goles esperados (xG) por partido, fase regular": _tt.xg_favor_regular,
            "Balón parado: xG a favor por partido, liguilla": lg.bp_xg_favor,
            "Balón parado: xG en contra por partido, liguilla": lg.bp_xg_contra,
        }).rename(index={True: "Torneos que ganó", False: "Torneos que no ganó"}).T
        st.markdown("#### Torneos que ganó frente a los que no ganó")
        st.dataframe(cmp_[["Torneos que ganó", "Torneos que no ganó"]].round(2), width="stretch")
        st.caption(f"Son {int(lg.loc[True].torneos)} torneos ganados y {int(lg.loc[False].torneos)} no ganados: "
                   "con tan pocos torneos, una diferencia es una pista, no una regla.")
    show = TT.rename(columns={"torneo": "Torneo", "tecnico": "Técnico", "llego": "Hasta dónde llegó",
                              "puntos_regular": "Puntos por partido (regular)", "xpts_regular": "Lo que merecía (regular)",
                              "xg_favor_regular": "Goles esperados por partido (regular)",
                              "posesion_regular": "Posesión regular (%)", "posesion_liguilla": "Posesión liguilla (%)",
                              "ppda_regular": "Presión regular*", "ppda_liguilla": "Presión liguilla*"})
    st.dataframe(show[["Torneo", "Técnico", "Hasta dónde llegó", "Puntos por partido (regular)", "Lo que merecía (regular)",
                       "Goles esperados por partido (regular)", "Posesión regular (%)", "Posesión liguilla (%)",
                       "Presión regular*", "Presión liguilla*"]].round(2), hide_index=True, width="stretch")
    st.caption("*Presión = pases que deja dar al rival antes de presionar (más alto = presiona menos). "
               "'Lo que merecía' = puntos esperados según las ocasiones de cada partido.")

# --- Con balón
with T["Con balón"]:
    ids = sel.match_id
    a, b = st.columns(2)
    a.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "tiros", "xg"), "¿De dónde vienen sus ocasiones? Goles esperados (xG) por partido",
                              "{:.2f}", "Greens"), width="stretch")
    b.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "pases_progresivos"), "¿Hasta dónde progresa? Pases progresivos por partido (donde terminan)"),
                   width="stretch")
    indicator_panel(sel, base, base_label, BLOCKS["Con balón"])

# --- Sin balón
with T["Sin balón"]:
    ids = sel.match_id
    a, b, c = st.columns(3)
    a.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "recuperaciones"), "¿Dónde recupera? Robos por partido"),
                   width="stretch")
    b.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "acciones_defensivas"), "¿Dónde defiende? Acciones defensivas por partido",
                              "{:.0f}"), width="stretch")
    c.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "tiros_rival", "xg"), "¿Desde dónde le generan peligro? xG del rival por partido",
                              "{:.2f}", "Reds"), width="stretch")
    st.caption("Todas las canchas en el sentido del América: ataca hacia la derecha; su portería está a la izquierda.")
    rv, rvb = K.recuperacion_valor(C["recuperaciones"], sel.match_id), K.recuperacion_valor(C["recuperaciones"], base.match_id)
    fig = go.Figure()
    fig.add_trace(go.Bar(x=rv.zona, y=rv.por_partido, name="Robos por partido", marker_color="#1baf7a",
                         text=[f"{v:.1f} robos · {t:.0f} % acaban en tiro" for v, t in zip(rv.por_partido, rv.pct_tiro.fillna(0))],
                         textposition="outside"))
    fig.add_trace(go.Scatter(x=rvb.zona, y=rvb.por_partido, mode="markers", name=base_label,
                             marker=dict(size=12, color=MUTED, symbol="line-ew-open", line=dict(width=3))))
    fig.update_layout(title="¿Cuánto vale robar en cada zona? Robos por partido y % que termina en tiro", height=340,
                      margin=dict(l=10, r=10, t=45, b=10), plot_bgcolor="white", legend=dict(orientation="h", y=1.12),
                      yaxis=dict(range=[0, max(rv.por_partido.max(), rvb.por_partido.max()) * 1.35]))
    st.plotly_chart(fig, width="stretch")
    if rv.pct_tiro.notna().all() and rv.pct_tiro.iloc[1] > 0:
        st.caption(f"Robar en el último tercio vale {rv.pct_tiro.iloc[2] / rv.pct_tiro.iloc[1]:.1f} veces más que robar en el medio: "
                   f"el {rv.pct_tiro.iloc[2]:.0f} % de esas jugadas termina en tiro, frente a {rv.pct_tiro.iloc[1]:.0f} %.")
    indicator_panel(sel, base, base_label, BLOCKS["Sin balón"])

# --- Balón parado
with T["Balón parado"]:
    bp = K.balon_parado(C["balon_parado"], sel.match_id, ["lado", "kind"])
    bpb = K.balon_parado(C["balon_parado"], base.match_id, ["lado", "kind"])
    t = bp.merge(bpb, on=["lado", "kind"], suffixes=("", "_comp"))
    for lado in ["A favor", "En contra"]:
        d = t[t.lado == lado].set_index("kind")
        st.markdown(f"#### {lado}")
        st.dataframe(pd.DataFrame({
            "por partido": d.por_partido.round(1), "con tiro (%)": d.pct_tiro.round(0),
            "peligro por jugada (xG)": d.xg_por_jugada.round(3), "peligro por partido (xG)": d.xg_por_partido.round(2),
            f"peligro por partido · {base_label}": d.xg_por_partido_comp.round(2)}), width="stretch")
    z = K.balon_parado(C["balon_parado"], sel.match_id, ["lado", "kind", "target_zone"])
    zc = z[(z.kind == "Córner")]
    if len(zc):
        fig = go.Figure()
        for lado, col in [("A favor", "#1baf7a"), ("En contra", "#e34948")]:
            d = zc[zc.lado == lado]
            fig.add_trace(go.Bar(x=d.target_zone, y=d.jugadas / d.jugadas.sum() * 100, name=lado, marker_color=col,
                                 hovertemplate="%{x}: %{y:.0f} % de los córners<extra>" + lado + "</extra>"))
        fig.update_layout(title="Córners: ¿a qué zona van?", barmode="group", height=300, yaxis_title="% de los córners",
                          margin=dict(l=10, r=10, t=40, b=10), plot_bgcolor="white")
        st.plotly_chart(fig, width="stretch")
    st.caption("Definición del marco: jugadas que abre el saque del propio equipo (córner, tiro libre, saque de banda).")

# --- Contexto
with T["Contexto"]:
    labels = {"field_tilt": "Dominio territorial (% de los pases en el último tercio)", "possession_time_pct": "Posesión (% del tiempo)",
              "ppda": "Pases que deja dar al rival antes de presionar (menos = presiona más)"}
    var = st.radio("Métrica", list(labels), format_func=labels.get, horizontal=True)
    e = K.efecto_marcador(C["tramos"], sel.match_id, var)
    if e.empty:
        st.info("Hacen falta al menos 5 partidos para estimar el efecto del marcador.")
    else:
        fig = go.Figure(go.Scatter(x=e.efecto, y=e.estado, mode="markers", marker=dict(size=13, color="#1baf7a"),
                                   error_x=dict(type="data", symmetric=False, array=e.hi - e.efecto,
                                                arrayminus=e.efecto - e.lo, color="#1baf7a"),
                                   customdata=e.minutos,
                                   hovertemplate="%{y}: %{x:+.1f} frente al empate<br>%{customdata:.0f} min<extra></extra>"))
        fig.add_vline(x=0, line=dict(color=MUTED))
        fig.update_layout(title=f"¿Cómo cambia {labels[var].lower()} con el marcador? (mismo partido, frente al empate)",
                          height=320, margin=dict(l=10, r=10, t=45, b=10), plot_bgcolor="white",
                          yaxis=dict(autorange="reversed"), xaxis_title="diferencia con el mismo partido empatado (la línea es el margen de error)")
        st.plotly_chart(fig, width="stretch")
    cols = ["possession_time_pct", "field_tilt", "ppda", "high_press_pct", "np_xg_per100poss", "opp_np_xg_per100poss"]
    rows = []
    for dim, key in [("Localía", "localia"), ("Rival", "rival_nivel")]:
        for v, g in sel.groupby(key):
            rows.append({"contexto": f"{dim}: {v}", "partidos": len(g), "puntos por partido": g.puntos.mean(),
                         **{CAT.loc[c, "etiqueta"]: g[c].mean() for c in cols}})
    st.markdown("#### Según la localía y la fuerza del rival")
    st.dataframe(pd.DataFrame(rows).set_index("contexto").round(2), width="stretch")
    st.caption("La presión de toda la liga cambió con los años: compara la presión dentro del mismo técnico, no entre épocas.")

# --- Rivales
with T["Rivales"]:
    rv = K.rivales(sel)
    mn = 3 if len(sel) >= 40 else 1
    rv = rv[rv.partidos >= mn]
    if rv.empty:
        st.info("No hay rivales con suficientes partidos en esta selección.")
    else:
        fig = go.Figure(go.Scatter(
            x=rv.xpts, y=rv.puntos, mode="markers+text", text=rv.opponent, textposition="top center", textfont=dict(size=10),
            marker=dict(size=8 + rv.partidos * 1.5, color=[TIER_COLOR.get(n, MUTED) for n in rv.nivel],
                        opacity=0.8, line=dict(width=1, color="white")),
            customdata=np.c_[rv.partidos, rv.nivel.fillna("—"), rv.pct_victorias],
            hovertemplate="%{text} (%{customdata[1]})<br>%{customdata[0]} partidos · %{customdata[2]:.0f} % victorias"
                          "<br>sacó %{y:.2f} puntos por partido · merecía %{x:.2f}<extra></extra>"))
        lo, hi = min(rv.xpts.min(), rv.puntos.min()) - 0.1, max(rv.xpts.max(), rv.puntos.max()) + 0.1
        fig.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi, line=dict(color=MUTED, dash="dot"))
        fig.update_layout(title="¿Contra quién saca más (o menos) de lo que merece?", height=480, plot_bgcolor="white",
                          margin=dict(l=10, r=10, t=45, b=10), xaxis_title="puntos que merecía por partido (según sus ocasiones)",
                          yaxis_title="puntos que sacó por partido")
        st.plotly_chart(fig, width="stretch")
        st.caption("Arriba de la línea punteada: sacó más de lo que merecía. Color = nivel del rival (rojo fuerte, gris medio, "
                   f"verde débil); tamaño = partidos. Rivales con {mn} partido(s) o más.")
        st.dataframe(rv.rename(columns={
            "opponent": "Rival", "nivel": "Nivel", "partidos": "Partidos", "puntos": "Puntos por partido",
            "xpts": "Lo que merecía", "diferencia": "Diferencia", "pct_victorias": "% victorias", "posesion": "Posesión (%)",
            "ppda": "Pases que deja dar antes de presionar (PPDA)", "xg_favor": "Goles esperados (xG) a favor",
            "xg_contra": "Goles esperados (xG) en contra"})
            [["Rival", "Nivel", "Partidos", "Puntos por partido", "Lo que merecía", "Diferencia", "% victorias", "Posesión (%)",
              "Pases que deja dar antes de presionar (PPDA)", "Goles esperados (xG) a favor", "Goles esperados (xG) en contra"]].round(2),
            hide_index=True, width="stretch")

# --- Jugadores
with T["Jugadores"]:
    j = K.jugadores_periodo(C["jugadores"], sel)
    st.caption("Se cuentan los torneos completos que toca la selección.")
    top = j.head(18).iloc[::-1]
    fig = go.Figure(go.Bar(x=top.pct_minutos, y=top.jugador + " · " + top.linea.fillna("").str.lower(), orientation="h",
                           marker_color="#1baf7a", customdata=np.c_[top.titularidades, top.pct_obv_pos, top.rol.fillna("—")],
                           hovertemplate="%{y}: %{x:.0f} % de los minutos<br>%{customdata[0]} de titular · "
                                         "%{customdata[1]:.1f} % del aporte del equipo · rol: %{customdata[2]}<extra></extra>"))
    fig.add_vline(x=50, line=dict(color=MUTED, dash="dot"))
    fig.update_layout(title="¿Con quién juega? % de los minutos posibles", height=560, margin=dict(l=10, r=10, t=40, b=10),
                      xaxis=dict(range=[0, 105]), plot_bgcolor="white")
    a, b = st.columns([1.2, 1])
    a.plotly_chart(fig, width="stretch")
    with b:
        st.markdown("#### ¿Quién genera el valor?")
        st.caption("Aporte = cuánto mejora cada acción con balón las opciones de gol del equipo (OBV de StatsBomb).")
        st.dataframe(j.nlargest(10, "pct_obv_pos")[["jugador", "linea", "rol", "pct_obv_pos", "obv_pos_p90"]]
                     .rename(columns={"linea": "línea", "pct_obv_pos": "% del aporte del equipo", "obv_pos_p90": "aporte por 90'"}).round(2),
                     hide_index=True, width="stretch")
        roles = j[j.minutos >= 270].groupby("rol").minutos.sum()
        st.caption("Roles (minutos): " + " · ".join(f"{k} {v / roles.sum():.0%}" for k, v in roles.sort_values(ascending=False).items()))
        fc, fcb = sel.primer_cambio_descanso.mean() * 100, base.primer_cambio_descanso.mean() * 100
        st.metric("Primer cambio en el descanso", f"{fc:.0f} % de los partidos",
                  delta=f"{fc - fcb:+.0f} puntos frente a {base_label} ({fcb:.0f} %)", delta_color="off",
                  help="Partidos en los que el primer cambio entra al minuto 45, al empezar el segundo tiempo.")
        st.metric("Minuto medio del primer cambio", f"{sel.primer_cambio_min.mean():.0f}'",
                  delta=f"{base_label}: {base.primer_cambio_min.mean():.0f}'", delta_color="off")

# --- Cómo lo medimos
with T["Cómo lo medimos"]:
    st.markdown("""
**De dónde salen los datos.** StatsBomb registra cada acción con balón de cada partido (unas 3,500 por partido). En algunas jugadas también registra la posición de todos los jugadores que se ven en la toma (360). Aquí están todos los partidos del América desde el Apertura 2021.

**Un mismo diccionario para todo.** Antes de medir, definimos cada concepto una sola vez, y todas las cifras de esta página usan esas mismas definiciones:
- qué es una posesión;
- qué es una transición;
- qué es presionar arriba;
- qué cuenta como balón parado.

**El ADN del Entrenador** resume el estilo en 8 rasgos. Cada rasgo:
- se compara con la liga **del mismo torneo**, porque la liga cambia con los años;
- descuenta la fuerza del rival y si se jugó en casa o fuera;
- se expresa de 0 a 100 frente a todos los técnicos de la Liga MX: 50 es el promedio y 100 el que más lo hace.

**Cuántos partidos hacen falta.** Un partido suelto cuenta poco: el estilo se ve con varios partidos.

| Partidos elegidos | Qué se puede decir |
|---|---|
| 1 | Si ese partido se pareció al ADN del técnico |
| Menos de 5 | Tendencias |
| Un torneo | El estilo de ese torneo |
| Toda una etapa | El ADN del técnico |

**Privacidad de los datos.** La aplicación solo usa resúmenes por partido, nunca los datos originales.

**Siglas**

| Sigla | Qué quiere decir |
|---|---|
| xG (goles esperados) | Qué tan clara fue cada ocasión: la probabilidad de que ese tiro sea gol, según desde dónde y cómo se tiró. Sumado, cuántos goles "merecía" un equipo |
| OBV (aporte) | Cuánto mejora o empeora cada acción con balón las opciones de marcar o de recibir gol |
| PPDA | Pases que deja dar al rival antes de intentar robar. Menos = presiona más |
| Field tilt (dominio territorial) | De los pases en el último tercio, qué % son del América |
| 360 | Posición de los jugadores que se ven en la toma de TV en el momento de cada acción |
""")
    with st.expander("Diccionario de indicadores"):
        st.dataframe(CAT[["etiqueta", "criterio", "definición", "dirección"]], width="stretch")

"""ADN del Entrenador · Club América — explorador de la historia de un entrenador.

Flujo: primero se elige el periodo (técnico, torneo, fechas o un partido) y el contexto (localía, fuerza del
rival); después se despliega el análisis. La historia de Jardine es la selección predeterminada.
Todo sale del cubo de agregados por partido (src/cube.py → app/data/): la app no lleva eventos.

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

DATA = ROOT / "app" / "data"
FIGS = ROOT / "reports" / "figures"
COACH_COLOR = {"Solari": "#2a78d6", "Ortiz": "#eb6834", "Jardine": "#1baf7a", "Almada": "#4a3aa7",
               "Cervantes": "#898781"}
INK, MUTED, GRID, LINE = "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7"
RESULT_COLOR = {"W": "#1baf7a", "D": "#c3c2b7", "L": "#e34948"}
RESULT_LABEL = {"W": "Victoria", "D": "Empate", "L": "Derrota"}
TORNEO_SHORT = lambda t: t.replace("Apertura ", "Ap ").replace("Clausura ", "Cl ")  # noqa: E731
BLOCKS = {
    "Con balón": ["Construcción", "Progresión", "Ocasiones", "Dominio"],
    "Sin balón": ["Presión", "Organización defensiva", "Transiciones"],
}
STORY_BLOCKS = {  # bloque de la app -> prefijos de hallazgos de la historia (notebook 05)
    "Con balón": ["3.2"], "Sin balón": ["3.3", "3.4"], "Balón parado": ["3.8"], "Contexto": ["3.5"],
    "Jugadores": ["3.7"], "Identidad": ["3.6"],
}

st.set_page_config(page_title="ADN del Entrenador · Club América", page_icon="⚽", layout="wide")


# ------------------------------------------------------------------ datos
@st.cache_data
def load() -> dict[str, pd.DataFrame]:
    d = K.load(DATA)
    d["partidos"]["match_date"] = pd.to_datetime(d["partidos"].match_date)
    return d


@st.cache_data
def textos() -> dict[str, str]:
    """Secciones de reports/final/textos.md por encabezado '## clave · título'."""
    f = DATA / "textos.md"
    out, key, buf = {}, None, []
    for line in f.read_text(encoding="utf-8").splitlines() if f.exists() else []:
        if line.startswith("## "):
            if key:
                out[key] = "\n".join(buf).strip()
            key, buf = line[3:].split(" · ")[0].strip(), []
        elif key:
            buf.append(line)
    if key:
        out[key] = "\n".join(buf).strip()
    return out


C = load()
P, CAT, EJES = C["partidos"], C["catalogo"].set_index("variable"), C["ejes"].eje.tolist()
HALL = pd.read_parquet(DATA / "hallazgos.parquet") if (DATA / "hallazgos.parquet").exists() else pd.DataFrame()
TX = textos()


# ------------------------------------------------------------------ selector (barra lateral)
def selector():
    sb = st.sidebar
    sb.markdown("## ADN del Entrenador\n**Club América · Liga MX**")
    modo = sb.radio("¿Qué quieres ver?", ["La historia de Jardine", "Explorar"], horizontal=True,
                    help="La historia es la selección por defecto: Jardine en la ventana oficial (Ap 2023 – Cl 2025).")
    if modo == "La historia de Jardine":
        sel = K.select(P, coach="Jardine", muestras="ventana")
        return sel, "Jardine · ventana oficial", modo, "Ortiz"
    coaches = [c for c in ["Jardine", "Ortiz", "Solari", "Almada", "Cervantes"] if c in set(P.coach)]
    coach = sb.multiselect("Técnico", coaches, default=["Jardine"])
    otras = sb.checkbox("Incluir partidos de validación y prueba (Ap 2025 y 2026)", value=False,
                        help="Las cifras titulares salen solo de la ventana oficial (Ap 2021 – Cl 2025).")
    base = K.select(P, coach=coach or None, muestras=None if otras else "ventana")
    if base.empty and not otras:   # p. ej. Almada: todos sus partidos son de prueba (2026)
        base = K.select(P, coach=coach or None)
        sb.caption("Este técnico no tiene partidos en la ventana oficial: se muestran sus partidos de validación o prueba.")
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
        loc = sb.multiselect("Localía", ["Local", "Visita"], default=[])
        riv = sb.multiselect("Fuerza del rival", K.RIVAL_TIERS, default=[],
                             help="Puntos por partido del rival en sus 17 partidos previos, en terciles de la liga.")
        base = K.select(base, localia=loc or None, rival=riv or None)
    others = [c for c in ["Ortiz", "Jardine", "Solari", "Almada"] if c not in coach] + ["América típico"]
    comp = sb.selectbox("Comparar con", others,
                        help="Era completa del técnico elegido (Almada: 2026, prueba) o todos los partidos del América en la ventana.")
    label = f"{', '.join(coach) or 'Todos'} · {tipo.lower()}"
    return base, label, modo, comp


def comparison(comp: str) -> tuple[pd.DataFrame, str]:
    if comp == "América típico":
        return K.select(P, muestras="ventana"), "América típico (ventana)"
    if comp == "Almada":
        return K.select(P, coach="Almada"), "Almada (2026, prueba)"
    return K.select(P, coach=comp, muestras="ventana"), f"{comp} (ventana)"


# ------------------------------------------------------------------ piezas visuales
def pitch_shapes(fig, row=None, col=None):
    kw = dict(line=dict(color=LINE, width=1), layer="above")
    shapes = [dict(type="rect", x0=0, y0=0, x1=120, y1=80), dict(type="line", x0=60, y0=0, x1=60, y1=80),
              dict(type="rect", x0=0, y0=18, x1=18, y1=62), dict(type="rect", x0=102, y0=18, x1=120, y1=62),
              dict(type="rect", x0=0, y0=30, x1=6, y1=50), dict(type="rect", x0=114, y0=30, x1=120, y1=50),
              dict(type="circle", x0=50, y0=30, x1=70, y1=50)]
    for s in shapes:
        fig.add_shape(**s, **kw)


def pitch_heat(m: np.ndarray, title: str, fmt: str = "{:.1f}", scale="Blues", zmax=None) -> go.Figure:
    xs = np.arange(K.CELL / 2, 120, K.CELL)
    ys = np.arange(K.CELL / 2, 80, K.CELL)
    text = [[fmt.format(v) if v >= (np.nanmax(m) * 0.15 if np.nanmax(m) > 0 else 1) else "" for v in row] for row in m]
    fig = go.Figure(go.Heatmap(z=m, x=xs, y=ys, colorscale=scale, zmin=0, zmax=zmax, showscale=False,
                               text=text, texttemplate="%{text}", textfont=dict(size=10),
                               hovertemplate="x %{x} · y %{y}<br>%{z:.2f} por partido<extra></extra>"))
    pitch_shapes(fig)
    fig.update_layout(title=dict(text=title, font=dict(size=13)), height=300, margin=dict(l=5, r=5, t=40, b=5),
                      xaxis=dict(visible=False, range=[-2, 122]), yaxis=dict(visible=False, range=[82, -2], scaleanchor="x"),
                      plot_bgcolor="white")
    fig.add_annotation(x=118, y=81.5, text="ataca →", showarrow=False, font=dict(size=10, color=MUTED), xanchor="right")
    return fig


def radar(series: dict[str, pd.Series], title: str) -> go.Figure:
    fig = go.Figure()
    for name, s in series.items():
        coach = name.split(" ")[0]
        r = list(s.values) + [s.values[0]]
        th = list(s.index) + [s.index[0]]
        fig.add_trace(go.Scatterpolar(r=r, theta=th, name=name, fill="toself", opacity=0.55,
                                      line=dict(color=COACH_COLOR.get(coach, MUTED), width=2),
                                      hovertemplate="%{theta}: percentil %{r:.0f}<extra>" + name + "</extra>"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], tickvals=[25, 50, 75], gridcolor=GRID),
                                 angularaxis=dict(gridcolor=GRID)),
                      title=dict(text=title, font=dict(size=13)), height=430, margin=dict(l=40, r=40, t=60, b=30),
                      legend=dict(orientation="h", y=-0.08))
    return fig


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
                                               "<br>más que %{x:.0f} de cada 100 partidos de la comparación"
                                               "<br>%{customdata[2]}<extra></extra>"))
        fig.update_layout(title=dict(text=crit, font=dict(size=13)), height=60 + 38 * len(d),
                          margin=dict(l=10, r=10, t=35, b=25), showlegend=False,
                          xaxis=dict(range=[0, 135], tickvals=[0, 25, 50, 75, 100],
                                     title=f"percentil del periodo entre los partidos de: {base_label}"),
                          yaxis=dict(autorange="reversed"), plot_bgcolor="white")
        st.plotly_chart(fig, width="stretch")


def story_notes(block: str, show: bool):
    """Hallazgos y figuras fijas de la historia (era completa de la ventana oficial) para un bloque."""
    if not show or HALL.empty:
        return
    pref = tuple(STORY_BLOCKS.get(block, []))
    h = HALL[HALL.bloque.str.startswith(pref)] if pref else HALL.iloc[0:0]
    if h.empty:
        return
    with st.expander("La historia de Jardine en este bloque (era completa, ventana oficial · figuras fijas)", expanded=True):
        for r in h.itertuples():
            st.markdown(f"**{r.pregunta}**  \n{r.hallazgo}")
            for f in [x.strip() for x in str(r.figuras).split(",") if x.strip()]:
                path = next((p for p in [FIGS / "story" / f, FIGS / "coach" / f] if p.exists()), None)
                if path:
                    st.image(str(path), width="stretch")


# ------------------------------------------------------------------ página
sel, label, modo, comp = selector()
base, base_label = comparison(comp)
info = K.nivel_muestra(len(sel))
story_mode = modo == "La historia de Jardine"

st.title("ADN del Entrenador · Club América")
if story_mode and "resumen" in TX:
    st.markdown(TX["resumen"].split("**Por qué importa")[0])
st.caption(f"Selección: **{label}** · comparación: **{base_label}** · Datos: StatsBomb (eventos y 360)")

if info["nivel"] == "vacio":
    st.warning(info["aviso"])
    st.stop()

r = K.resumen(sel)
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Partidos", r["partidos"], help=", ".join(r["muestras"]))
c2.metric("Récord (G-E-P)", f"{r['ganados']}-{r['empatados']}-{r['perdidos']}")
c3.metric("Puntos por partido", f"{r['puntos_por_partido']:.2f}")
c4.metric("Goles a favor / en contra", f"{r['goles_favor']:.1f} / {r['goles_contra']:.1f}")
c5.metric("xG a favor / en contra", f"{r['xg_favor']:.2f} / {r['xg_contra']:.2f}", help="xG sin penales por partido")
(st.info if info["nivel"] in ("era", "torneo") else st.warning)(info["aviso"])
if set(r["muestras"]) - {"ventana"}:
    st.caption("⚠ La selección incluye partidos de validación o prueba (fuera de la ventana oficial).")

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
                          "<br>%{customdata[3]}-%{customdata[4]} · diferencia de xG %{y:+.2f}<br>%{customdata[5]}<extra></extra>"))
    fig.add_hline(y=0, line=dict(color=MUTED, width=1))
    fig.update_layout(height=260, margin=dict(l=10, r=10, t=10, b=10), yaxis_title="xG a favor − en contra",
                      legend=dict(orientation="h", y=1.15), plot_bgcolor="white")
    st.plotly_chart(fig, width="stretch")
    st.caption("Círculo = local · rombo = visita. El rival pesa más que la localía: un tramo con rivales grandes "
               "no es un cambio de estilo.")
    lv = sel.rival_nivel.value_counts().reindex(K.RIVAL_TIERS).fillna(0).astype(int)
    st.caption("Rivales del periodo: " + " · ".join(f"{k} {v}" for k, v in lv.items()))
    st.dataframe(sel.sort_values("match_date", ascending=False).assign(
        fecha=lambda d: d.match_date.dt.strftime("%d %b %Y"), marcador=lambda d: d.goals_for.astype(str) + "-" + d.goals_against.astype(str))
        [["fecha", "torneo", "coach", "localia", "opponent", "rival_nivel", "marcador", "xg_favor", "xg_contra", "sistema", "muestra"]]
        .rename(columns={"coach": "técnico", "localia": "localía", "opponent": "rival", "rival_nivel": "nivel del rival",
                         "xg_favor": "xG a favor", "xg_contra": "xG en contra"}),
        hide_index=True, width="stretch", height=min(400, 40 + 35 * len(sel)))

tabs = st.tabs(["Identidad", "Con balón", "Sin balón", "Balón parado", "Contexto", "Jugadores", "Método"])

# --- Identidad
with tabs[0]:
    ref = C["adn_ref"]
    adn = K.adn_percentil(sel, ref, EJES)
    adn_b = K.adn_percentil(base, ref, EJES)
    who = sel.coach.mode().iat[0]
    left, right = st.columns([1.1, 1])
    with left:
        series = {f"{who} · selección": adn, base_label: adn_b}
        if info["nivel"] != "era":
            era = K.select(P, coach=who, muestras="ventana" if who != "Almada" else "prueba")
            series[f"{who} · era completa"] = K.adn_percentil(era, ref, EJES)
        st.plotly_chart(radar(series, "ADN: percentil frente a los técnicos de la Liga MX"), width="stretch")
        st.caption("Cada rasgo se compara con la liga del mismo torneo y se ajusta por rival y localía. "
                   + ("" if info["rankings"] else "**Muestra chica: el percentil es solo orientativo.**"))
    with right:
        if story_mode and "3.1" in TX:
            st.markdown("#### Jardine en 5 ideas")
            st.markdown(TX["3.1"])
        else:
            t = pd.DataFrame({"selección": adn.round(0), base_label: adn_b.round(0)})
            t["diferencia"] = t.iloc[:, 0] - t.iloc[:, 1]
            st.markdown("#### Rasgos del ADN (percentil de liga)")
            st.dataframe(t, width="stretch")
            top = t.diferencia.abs().sort_values(ascending=False).index[:3]
            st.markdown("**Lo que más lo distingue de la comparación:** " + "; ".join(
                f"{e.lower()} {t.loc[e, 'diferencia']:+.0f}" for e in top))
        sis = sel.sistema.value_counts()
        st.caption("Sistemas titulares: " + " · ".join(f"{k} ({v})" for k, v in sis.head(4).items()))
    story_notes("Identidad", story_mode)

# --- Con balón
with tabs[1]:
    ids = sel.match_id
    a, b = st.columns(2)
    a.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "tiros", "xg"), "¿De dónde vienen sus ocasiones? xG por partido",
                              "{:.2f}", "Greens"), width="stretch")
    b.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "pases_progresivos"), "¿Hasta dónde progresa? Pases progresivos por partido (donde terminan)"),
                   width="stretch")
    indicator_panel(sel, base, base_label, BLOCKS["Con balón"])
    story_notes("Con balón", story_mode)

# --- Sin balón
with tabs[2]:
    ids = sel.match_id
    a, b, c = st.columns(3)
    a.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "recuperaciones"), "¿Dónde recupera? Robos por partido"),
                   width="stretch")
    b.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "acciones_defensivas"), "¿Dónde defiende? Acciones defensivas por partido",
                              "{:.0f}"), width="stretch")
    c.plotly_chart(pitch_heat(K.rejilla(C["zonas"], ids, "tiros_rival", "xg"), "¿Desde dónde le tiran? xG rival por partido",
                              "{:.2f}", "Reds"), width="stretch")
    st.caption("Todas las canchas en el sentido del América: ataca hacia la derecha; su portería está a la izquierda.")
    indicator_panel(sel, base, base_label, BLOCKS["Sin balón"])
    story_notes("Sin balón", story_mode)

# --- Balón parado
with tabs[3]:
    bp = K.balon_parado(C["balon_parado"], sel.match_id, ["lado", "kind"])
    bpb = K.balon_parado(C["balon_parado"], base.match_id, ["lado", "kind"])
    t = bp.merge(bpb, on=["lado", "kind"], suffixes=("", "_comp"))
    for lado in ["A favor", "En contra"]:
        d = t[t.lado == lado].set_index("kind")
        st.markdown(f"#### {lado}")
        st.dataframe(pd.DataFrame({
            "por partido": d.por_partido.round(1), "con tiro (%)": d.pct_tiro.round(0),
            "xG por jugada": d.xg_por_jugada.round(3), "xG por partido": d.xg_por_partido.round(2),
            f"xG por partido · {base_label}": d.xg_por_partido_comp.round(2)}), width="stretch")
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
    story_notes("Balón parado", story_mode)

# --- Contexto
with tabs[4]:
    labels = {"field_tilt": "Field tilt (%)", "possession_time_pct": "Posesión (% del tiempo)", "ppda": "PPDA"}
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
                          yaxis=dict(autorange="reversed"), xaxis_title="diferencia con el empate (IC 90 %)")
        st.plotly_chart(fig, width="stretch")
    cols = ["possession_time_pct", "field_tilt", "ppda", "high_press_pct", "np_xg_per100poss", "opp_np_xg_per100poss"]
    rows = []
    for dim, key in [("Localía", "localia"), ("Rival", "rival_nivel")]:
        for v, g in sel.groupby(key):
            rows.append({"contexto": f"{dim}: {v}", "partidos": len(g), "puntos por partido": g.puntos.mean(),
                         **{CAT.loc[c, "etiqueta"]: g[c].mean() for c in cols}})
    st.markdown("#### Según la localía y la fuerza del rival")
    st.dataframe(pd.DataFrame(rows).set_index("contexto").round(2), width="stretch")
    st.caption("El PPDA de la liga sube con los años: compáralo dentro del mismo técnico, no entre técnicos de épocas distintas.")
    story_notes("Contexto", story_mode)

# --- Jugadores
with tabs[5]:
    j = K.jugadores_periodo(C["jugadores"], sel)
    st.caption("Granularidad: técnico × torneo (los torneos que toca la selección).")
    top = j.head(18).iloc[::-1]
    fig = go.Figure(go.Bar(x=top.pct_minutos, y=top.jugador + " · " + top.linea.fillna("").str.lower(), orientation="h",
                           marker_color="#1baf7a", customdata=np.c_[top.titularidades, top.pct_obv_pos, top.rol.fillna("—")],
                           hovertemplate="%{y}: %{x:.0f} % de los minutos<br>%{customdata[0]} de titular · "
                                         "%{customdata[1]:.1f} % del valor (OBV+) · rol: %{customdata[2]}<extra></extra>"))
    fig.add_vline(x=50, line=dict(color=MUTED, dash="dot"))
    fig.update_layout(title="¿Con quién juega? % de los minutos posibles", height=560, margin=dict(l=10, r=10, t=40, b=10),
                      xaxis=dict(range=[0, 105]), plot_bgcolor="white")
    a, b = st.columns([1.2, 1])
    a.plotly_chart(fig, width="stretch")
    with b:
        st.markdown("#### ¿Quién genera el valor?")
        st.dataframe(j.nlargest(10, "pct_obv_pos")[["jugador", "linea", "rol", "pct_obv_pos", "obv_pos_p90"]]
                     .rename(columns={"linea": "línea", "pct_obv_pos": "% del OBV+", "obv_pos_p90": "OBV+ por 90'"}).round(2),
                     hide_index=True, width="stretch")
        roles = j[j.minutos >= 270].groupby("rol").minutos.sum()
        st.caption("Roles (minutos): " + " · ".join(f"{k} {v / roles.sum():.0%}" for k, v in roles.sort_values(ascending=False).items()))
        fc = sel.primer_cambio_descanso.mean() * 100
        st.metric("Primer cambio en el descanso", f"{fc:.0f} % de los partidos",
                  help="Minuto 45 del segundo tiempo. Jardine en su era: 26 %; Ortiz 13 %; Solari 11 %.")
        st.metric("Minuto medio del primer cambio", f"{sel.primer_cambio_min.mean():.0f}'")
    story_notes("Jugadores", story_mode)

# --- Método
with tabs[6]:
    st.markdown("""
**Marco analítico**: `src/framework.py` es la fuente única de las definiciones y los supuestos:
- posesión, secuencia ofensiva, transición, fase de presión y balón parado;
- umbrales y zonas en `ASSUMPTIONS`.

Todas las cifras de esta página salen de esas definiciones.

**Ventana de datos**:

| Muestra | Periodo |
|---|---|
| Ventana oficial | Ap 2021 – Cl 2025 |
| Validación | Ap 2025 |
| Prueba | 2026 |

Las cifras titulares solo usan la ventana oficial.

**ADN del Entrenador**: 8 rasgos. Cada uno:
- se calcula con métricas de equipo de toda la Liga MX;
- se estandariza contra la liga **del mismo torneo**, porque la liga cambia con los años;
- se ajusta por rival y localía;
- se expresa en percentil frente a los técnicos de la liga con 15 partidos o más.

**Regla de muestra**:

| Partidos | Qué se puede afirmar |
|---|---|
| 1 | Se compara con el ADN; no define un estilo |
| Menos de 5 | Tendencias |
| Un torneo | Identidad aproximada |
| La era completa | Cifras titulares |

**Datos**: la app solo lleva agregados por partido (`src/cube.py`); nunca eventos ni frames 360.
""")
    st.dataframe(CAT[["etiqueta", "criterio", "definición", "dirección"]], width="stretch")

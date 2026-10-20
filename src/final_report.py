"""Reporte final (entregable del reto): la historia del América de André Jardine contada con datos.

Lee SOLO agregados (data/gold/analysis: notebooks 04–07; cubo por partido) y escribe un HTML autocontenido en
reports/final/reporte_america.html. Las gráficas son Plotly (jsDelivr) con la paleta de src/viz.py; las siglas se
explican en el texto con src.prereporte.siglas. Ventana: Apertura 2021 – Clausura 2025 (2025–26 solo en el epílogo).

Uso: python -m src.final_report   (después de los notebooks 05, 06 y 07)
"""
from __future__ import annotations

import html
import json
from pathlib import Path
from string import Template

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src import cube as K
from src.pipeline.config import GOLD
from src.prereporte import siglas
from src.viz import COACH_COLOR, STAGE_COLOR, pitch_shapes, torneo_short

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "final" / "reporte_america.html"
TPL = Path(__file__).with_name("templates") / "final_report.html.tpl"
A = GOLD / "analysis"
APP_URL = ""          # enlace al explorador (app) cuando esté publicado
COACHES = ["Solari", "Ortiz", "Jardine"]
INK, MUTED, RULE, ACCENT = "#14181d", "#6f7782", "#dde2e8", "#1d4e89"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]


def rd(name: str) -> pd.DataFrame:
    return pd.read_parquet(A / f"{name}.parquet")


def e(s: str, seen: set | None = None) -> str:
    """Texto plano → HTML con las siglas explicadas (una vez por `seen`, p. ej. por sección)."""
    return siglas(html.escape(s), seen)


# ------------------------------------------------------------------ cifras (todas salen de los agregados)
def cifras() -> dict:
    N: dict = {}
    adn = rd("hipotesis_adn_comun").set_index("rasgo")
    N["adn"] = adn
    sal = rd("story_salida_resumen").query("kind == 'Saque de meta'").set_index("coach").pct_corto
    rec = rd("story_salida_receptor").query("kind == 'Saque de meta' and length == 'Corto' and receiver_group == 'Medio defensivo'").set_index("coach").share * 100
    N.update(corto=sal, mc_baja=rec)
    tot = rd("story_ocasiones_total").set_index("coach")
    N["xg_tiro"], N["tiros_pp"], N["xg_pp"] = tot.xg_por_tiro, tot.tiros_por_partido, tot.np_xg_por_partido
    ori = rd("story_ocasiones_origen").query("coach == 'Jardine'").set_index("origin").pct_xg
    N["xg_bp_pct"], N["xg_tr_pct"] = ori["Balón parado"], ori["Transición"]
    pp = rd("story_ocasiones_pase_previo").set_index(["coach", "assist"]).pct_xg
    N["pase_atras"] = {c: pp.get((c, "Pase atrás al área"), np.nan) for c in COACHES}
    pr = rd("story_presion_liga_rank").query("metrica == 'team_match_ppda'").set_index("coach")
    N["ppda_liga"], N["ppda_lugar"] = pr.valor, pr.lugar
    fo = rd("story_forma_fase").query("fase == 'Bloque medio'").set_index("coach")
    N["bloque"], N["linea"] = fo.largo_bloque, fo.altura_linea
    cp = rd("story_contrapresion_evento").set_index("coach")
    N["recup5"] = cp.pct_recuperadas
    dba = rd("story_defensa_bajo_ataque").set_index("coach")
    N["dba_llegadas"], N["dba_sin_tiro"] = dba.llegadas_por_partido, dba.pct_sin_tiro
    tr = rd("story_transiciones").set_index(["coach", "lado"])
    N["tr_ratio"] = {c: tr.loc[(c, "A favor"), "xg_por_partido"] / tr.loc[(c, "En contra"), "xg_por_partido"] for c in COACHES}
    bp = rd("story_bp_resumen").query("lado == 'A favor' and kind == 'Córner'").set_index("coach")
    N["corner_corto"], N["xg_corner"] = bp.pct_corto, bp.xg_por_jugada
    bpd = rd("story_bp_defensa_corner").set_index("coach")
    N["def_area"], N["pegados"], N["azar"] = bpd.defensores_area_media, bpd.pct_pegados, bpd.pct_pegados_azar
    z = rd("story_bp_zonas_remate").query("coach == 'Jardine' and lado == 'En contra' and dimension == 'palo'").set_index("valor")
    N["primer_palo"] = z.loc["Primer palo", "pct_xg"]
    mar = rd("story_contexto_marcador").query("coach == 'Jardine'").set_index(["variable", "estado"]).efecto
    N["mar"] = mar
    rl = rd("story_contexto_rival_localia").query("coach == 'Jardine'").set_index("contexto")
    N["pos_debil"], N["pos_fuerte"] = rl.loc["Débil", "possession_time_pct"], rl.loc["Fuerte", "possession_time_pct"]
    loc = rd("hipotesis_localia").set_index("metrica")
    N["loc"] = loc
    mi = rd("hipotesis_minuto").query("tecnico == 'Jardine'").set_index("tramo")
    N["min"] = mi
    cam = rd("hipotesis_cambios").set_index(["marcador", "sale"])
    N["cam_perd"] = cam.loc[("Perdiendo", "Sale un defensor")]
    P = K.load()["partidos"]
    W = P[(P.muestra == "ventana") & P.coach.isin(COACHES)]
    N["descanso"] = W.groupby("coach").primer_cambio_descanso.mean() * 100
    N["P"], N["W"] = P, W
    ser = rd("hipotesis_series_avanzo_todas").set_index("metrica")
    N["ser"] = ser
    N["series"] = rd("hipotesis_series_liguilla")
    der = rd("hipotesis_derrotas").set_index("metrica")
    N["der"] = der
    fue = rd("hipotesis_formacion_fuertes")
    N["fue"] = fue
    N["forms"] = rd("hipotesis_formaciones").set_index("formacion")
    N["fvs"] = rd("hipotesis_formacion_vs")
    N["tipos"], N["reparto"] = rd("story_goles_tipos").set_index("tipo"), rd("story_goles_reparto").set_index("coach")
    N["recetas"] = rd("story_goles_recetas")
    N["finales"] = rd("story_finales")
    N["rivales"] = rd("story_rivales").set_index("opponent")
    N["encaje"] = rd("coach_fit_top15")
    N["hip"] = rd("hipotesis_equipo").set_index("id")
    jug = K.jugadores_periodo(K.load()["jugadores"], W[W.coach == "Jardine"]).set_index("jugador")
    N["fidalgo"] = jug.loc[[j for j in jug.index if "Fidalgo" in j][0], "pct_obv_pos"]
    N["xpts"] = W.groupby("coach").agg(puntos=("puntos", "mean"), xpts=("xpts", "mean"))
    return N


# ------------------------------------------------------------------ gráficas (tema claro fijo)
def lay(fig: go.Figure, h: int, **kw) -> go.Figure:
    base = dict(height=h, paper_bgcolor="white", plot_bgcolor="white",
                font=dict(family="Source Sans 3, Segoe UI, sans-serif", size=13, color=INK),
                margin=dict(l=10, r=16, t=40, b=44), hoverlabel=dict(bgcolor="white", bordercolor=RULE, font=dict(color=INK)),
                legend=dict(orientation="h", y=1.12, x=0))
    base.update(kw)
    fig.update_layout(**base)
    fig.update_xaxes(gridcolor=RULE, zerolinecolor=MUTED, linecolor=RULE, tickfont=dict(color=MUTED), automargin=True,
                     title_font=dict(color=MUTED, size=12))
    fig.update_yaxes(gridcolor=RULE, zerolinecolor=MUTED, linecolor=RULE, automargin=True, title_font=dict(color=MUTED, size=12))
    return fig


def f_radar(N) -> go.Figure:
    adn = N["adn"]
    th = list(adn.index) + [adn.index[0]]
    fig = go.Figure()
    for c in COACHES:
        r = list(adn[c]) + [adn[c].iloc[0]]
        fig.add_trace(go.Scatterpolar(r=r, theta=th, name=c, fill="toself", opacity=0.75, line=dict(color=COACH_COLOR[c], width=2),
                                      hovertemplate="%{theta}: %{r:.0f} de 100<extra>" + c + "</extra>"))
    return lay(fig, 460, margin=dict(l=70, r=70, t=50, b=30),
               polar=dict(bgcolor="white", radialaxis=dict(range=[0, 100], tickvals=[25, 50, 75], gridcolor=RULE, tickfont=dict(size=10, color=MUTED)),
                          angularaxis=dict(gridcolor=RULE, tickfont=dict(size=12, color=INK))))


def f_mapas(N) -> go.Figure:
    """Dos canchas lado a lado (Jardine): de dónde vienen sus ocasiones y dónde roba el balón."""
    from plotly.subplots import make_subplots
    C = K.load()
    ids = N["W"].query("coach == 'Jardine'").match_id
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.04,
                        subplot_titles=("¿De dónde vienen sus ocasiones? (xG por partido)", "¿Dónde roba el balón? (robos por partido)"))
    xs, ys = np.arange(K.CELL / 2, 120, K.CELL), np.arange(K.CELL / 2, 80, K.CELL)
    for col, (capa, val, scale, fmt) in enumerate([("tiros", "xg", "Greens", "{:.2f}"), ("recuperaciones", "n", "Blues", "{:.1f}")], start=1):
        m = K.rejilla(C["zonas"], ids, capa, val)
        top = np.nanmax(m)
        txt = [[fmt.format(v) if v >= top * 0.2 else "" for v in row] for row in m]
        fig.add_trace(go.Heatmap(z=m, x=xs, y=ys, colorscale=scale, zmin=0, showscale=False, text=txt, texttemplate="%{text}",
                                 textfont=dict(size=10), hovertemplate="%{z:.2f} por partido<extra></extra>"), row=1, col=col)
        for s in pitch_shapes(go.Figure()).layout.shapes:
            fig.add_shape(s.to_plotly_json(), row=1, col=col)
    fig.update_xaxes(visible=False, range=[-2, 122])
    fig.update_yaxes(visible=False, range=[82, -2], scaleanchor="x")
    fig.update_yaxes(scaleanchor="x2", row=1, col=2)
    fig.add_annotation(x=0.5, y=-0.06, xref="paper", yref="paper", showarrow=False, text="El América ataca hacia la derecha →",
                       font=dict(size=11, color=MUTED))
    return lay(fig, 330, margin=dict(l=5, r=5, t=50, b=30))


def f_tipos_gol(N) -> go.Figure:
    rep = N["reparto"]
    tipos = ["Ataque rápido tras recuperar", "Ataque corto en campo rival", "Ataque elaborado", "Balón parado"]
    fig = go.Figure()
    for t, col in zip(tipos, SERIES):
        fig.add_trace(go.Bar(y=[f"{c} ({int(rep.loc[c, 'goles'])} goles)" for c in COACHES], x=[rep.loc[c, t] for c in COACHES],
                             name=t, orientation="h", marker=dict(color=col, line=dict(color="white", width=2)),
                             text=[f"{rep.loc[c, t]:.0f} %" for c in COACHES], textposition="inside", insidetextanchor="middle",
                             textfont=dict(color="white", size=12), hovertemplate="%{y}<br>" + t + ": %{x:.0f} %<extra></extra>"))
    return lay(fig, 280, barmode="stack", margin=dict(l=150, r=16, t=80, b=30), legend=dict(orientation="h", y=1.42, x=0, font=dict(size=11)),
               xaxis=dict(range=[0, 100], ticksuffix=" %"), yaxis=dict(autorange="reversed"))


def f_marcador(N) -> go.Figure:
    est = ["Pierde por 2+", "Pierde por 1", "Gana por 1", "Gana por 2+"]
    d = rd("story_contexto_marcador").query("coach == 'Jardine' and estado in @est")
    fig = go.Figure()
    for var, lab, col in [("field_tilt", "Dominio territorial", SERIES[0]), ("possession_time_pct", "Posesión", SERIES[1])]:
        s = d[d.variable == var].set_index("estado").reindex(est)
        fig.add_trace(go.Scatter(x=s.efecto, y=[f"{x}" for x in est], mode="markers", name=lab, marker=dict(size=12, color=col),
                                 error_x=dict(type="data", symmetric=False, array=s.hi - s.efecto, arrayminus=s.efecto - s.lo,
                                              color=col, thickness=1.5, width=0),
                                 hovertemplate="%{y}: %{x:+.0f} puntos frente al empate<extra>" + lab + "</extra>"))
    fig.add_vline(x=0, line=dict(color=MUTED, width=1))
    return lay(fig, 300, xaxis=dict(title="diferencia frente al mismo partido empatado (puntos de %)"),
               yaxis=dict(autorange="reversed", gridcolor="white"), margin=dict(l=120, r=16, t=50, b=50))


def f_minuto(N) -> go.Figure:
    m = N["min"].reset_index()
    fig = go.Figure([
        go.Scatter(x=m.tramo, y=m.xg_contra_90_hi, mode="lines", line=dict(width=0), hoverinfo="skip", showlegend=False),
        go.Scatter(x=m.tramo, y=m.xg_contra_90_lo, mode="lines", fill="tonexty", fillcolor="rgba(235,104,52,0.15)", line=dict(width=0),
                   hoverinfo="skip", showlegend=False),
        go.Scatter(x=m.tramo, y=m.xg_contra_90, mode="lines+markers", name="En contra", line=dict(color=SERIES[1], width=2),
                   marker=dict(size=8), hovertemplate="%{x}: %{y:.2f} xG en contra por 90'<extra></extra>"),
        go.Scatter(x=m.tramo, y=m.xg_favor_90, mode="lines+markers", name="A favor", line=dict(color=SERIES[0], width=2),
                   marker=dict(size=8), hovertemplate="%{x}: %{y:.2f} xG a favor por 90'<extra></extra>")])
    fig.add_vrect(x0=1.5, x1=2.5, fillcolor="rgba(235,104,52,0.06)", line_width=0)
    return lay(fig, 320, xaxis=dict(title="tramo del partido (minutos)", type="category"),
               yaxis=dict(title="ocasiones (xG) por 90'", rangemode="tozero"))


def f_torneos(N) -> go.Figure:
    P = N["P"]
    TT = K.torneos(P)
    TT = TT[TT.torneo.isin(P[P.muestra == "ventana"].torneo.unique()) & TT.tecnico.isin(COACHES) & TT.partidos_liguilla.gt(0)]
    t = TT.torneo.map(torneo_short) + " · " + TT.tecnico
    col = [STAGE_COLOR.get(x, MUTED) for x in TT.llego]
    sym = ["star" if x == "Campeón" else "circle" for x in TT.llego]
    size = [20 if x == "Campeón" else 12 for x in TT.llego]
    fig = go.Figure([
        go.Scatter(x=t, y=TT.ppda_regular, mode="lines+markers", name="Fase regular", line=dict(color=RULE, width=2),
                   marker=dict(size=7, color=MUTED), hovertemplate="%{x}<br>fase regular: %{y:.1f} pases<extra></extra>"),
        go.Scatter(x=t, y=TT.ppda_liguilla, mode="markers", name="Liguilla", customdata=TT.llego,
                   marker=dict(size=size, symbol=sym, color=col, line=dict(width=1, color="white")),
                   hovertemplate="%{x}<br>liguilla: %{y:.1f} pases<br>%{customdata}<extra></extra>")])
    return lay(fig, 340, xaxis=dict(tickangle=-35, tickfont=dict(size=11)),
               yaxis=dict(title="pases que deja dar antes de presionar (PPDA)"), margin=dict(l=10, r=16, t=50, b=80))


def f_series(N) -> go.Figure:
    s = N["series"]
    fig = go.Figure()
    for c in COACHES:
        for av in [True, False]:
            d = s[(s.tecnico == c) & (s.avanzo == av)]
            if d.empty:
                continue
            fig.add_trace(go.Scatter(x=d.posesion, y=d.ppda, mode="markers", name=f"{c} · {'pasó' if av else 'eliminado'}",
                                     marker=dict(size=13, symbol="circle" if av else "circle-open", color=COACH_COLOR[c],
                                                 line=dict(width=2, color=COACH_COLOR[c])),
                                     customdata=np.c_[d.serie, d.rival, d["global"]],
                                     hovertemplate="%{customdata[0]} vs %{customdata[1]}<br>global %{customdata[2]}<br>"
                                                   "posesión %{x:.0f} % · deja dar %{y:.0f} pases<extra></extra>"))
    fig.add_annotation(xref="paper", yref="paper", x=0.01, y=0.99, showarrow=False, xanchor="left", text="↑ espera más",
                       font=dict(size=12, color=MUTED))
    return lay(fig, 440, margin=dict(l=10, r=16, t=100, b=50), legend=dict(orientation="h", y=1.3, x=0, font=dict(size=11)),
               xaxis=dict(title="posesión en la serie (%)"), yaxis=dict(title="pases que deja dar antes de presionar (PPDA)"))


def f_derrotas(N) -> go.Figure:
    d = N["der"].reset_index()
    d = d[d.veredicto == "se sostiene"].sort_values("dif_sd")
    fig = go.Figure(go.Bar(y=d.metrica, x=d.dif_sd, orientation="h", marker=dict(color=[SERIES[1] if v > 0 else SERIES[0] for v in d.dif_sd]),
                           customdata=np.c_[d.no, d.si], hovertemplate="%{y}<br>victorias %{customdata[0]:.2f} · derrotas %{customdata[1]:.2f}<extra></extra>"))
    return lay(fig, 340, showlegend=False, bargap=0.35, margin=dict(l=320, r=16, t=20, b=50),
               xaxis=dict(title="← menos cuando pierde · más cuando pierde → (desviaciones estándar)", zeroline=True),
               yaxis=dict(gridcolor="white"))


def f_fuertes(N) -> go.Figure:
    from plotly.subplots import make_subplots
    f = N["fue"]
    mets = [("Toques en el área rival (por 100 posesiones)", "Llegadas al área rival"), ("Ocasiones en contra (xG por 90')", "Ocasiones en contra (xG por 90')"),
            ("Posesión (%)", "Posesión (%)")]
    fig = make_subplots(rows=1, cols=3, shared_yaxes=True, subplot_titles=[m[1] for m in mets], horizontal_spacing=0.05)
    for i, (m, _) in enumerate(mets, start=1):
        d = f[f.metrica == m].assign(g=lambda x: np.where(x.formacion == "4-4-2", "4-4-2", "Tres centrales"))
        cols = [COACH_COLOR["Jardine"] if g == "4-4-2" else COACH_COLOR["Ortiz"] for g in d.g]
        fig.add_trace(go.Scatter(x=d.dif, y=d.g, mode="markers", showlegend=False,
                                 marker=dict(size=12, color=cols, symbol=["circle" if v == "se sostiene" else "circle-open" for v in d.veredicto],
                                             line=dict(width=2, color=cols)),
                                 error_x=dict(type="data", symmetric=False, array=d.hi - d.dif, arrayminus=d.dif - d.lo, color=MUTED, thickness=1.5, width=0),
                                 hovertemplate="%{y} frente al 4-2-3-1<br>%{x:+.2f}<extra></extra>"), row=1, col=i)
        fig.add_vline(x=0, line=dict(color=MUTED, width=1), row=1, col=i)
    return lay(fig, 260, margin=dict(l=110, r=16, t=50, b=40))


def f_encaje(N) -> go.Figure:
    d = N["encaje"].head(10).iloc[::-1]
    cols = [COACH_COLOR["Jardine"] if "América" in i else MUTED for i in d.index]
    fig = go.Figure(go.Bar(x=d.indice_encaje, y=d.index, orientation="h", marker=dict(color=cols),
                           text=[f"{v:.0f}" for v in d.indice_encaje], textposition="outside", cliponaxis=False,
                           customdata=d.partidos, hovertemplate="%{y}<br>Índice de Encaje %{x:.0f} de 100 · %{customdata} partidos<extra></extra>"))
    return lay(fig, 380, showlegend=False, margin=dict(l=200, r=40, t=20, b=40), xaxis=dict(range=[0, 108], title="Índice de Encaje (0 a 100)"),
               yaxis=dict(gridcolor="white"))


def f_epilogo(N) -> go.Figure:
    jt = K.torneos(N["P"]).query("tecnico == 'Jardine'")
    rec = ~jt.torneo.isin(N["P"][N["P"].muestra == "ventana"].torneo.unique())
    fig = go.Figure(go.Scatter(x=jt.torneo.map(torneo_short), y=jt.xg_favor_regular, mode="lines+markers",
                               line=dict(color=COACH_COLOR["Jardine"], width=2),
                               marker=dict(size=11, color=COACH_COLOR["Jardine"], symbol=["circle-open" if r else "circle" for r in rec],
                                           line=dict(width=2, color=COACH_COLOR["Jardine"])),
                               customdata=jt.posesion_regular, hovertemplate="%{x}<br>%{y:.2f} xG por partido · posesión %{customdata:.0f} %<extra></extra>"))
    return lay(fig, 280, showlegend=False, yaxis=dict(title="ocasiones (xG) por partido", rangemode="tozero"))


FIGURAS = {"g-radar": f_radar, "g-mapas": f_mapas, "g-tipos": f_tipos_gol, "g-marcador": f_marcador, "g-minuto": f_minuto,
           "g-torneos": f_torneos, "g-series": f_series, "g-derrotas": f_derrotas, "g-fuertes": f_fuertes, "g-encaje": f_encaje,
           "g-epilogo": f_epilogo}


def fig_html(gid: str, pie: str, alto: int) -> str:
    return (f'<figure class="viz"><div id="{gid}" class="plot" style="min-height:{alto}px"></div>'
            f'<figcaption>{e(pie)}</figcaption></figure>')


# ------------------------------------------------------------------ texto
def cuerpo(N) -> dict:
    adn, c, x = N["adn"], N["corto"], N["xg_tiro"]
    L, ser, der, mi = N["loc"], N["ser"], N["der"], N["min"]
    m_ft, m_pos = N["mar"].loc["field_tilt"], N["mar"].loc["possession_time_pct"]
    t = N["tipos"]; rep = N["reparto"]
    pp_s, po_s = ser.loc["Pases que deja dar antes de presionar (PPDA)"], ser.loc["Posesión (%)"]
    bpf = ser.loc["Balón parado a favor (xG)"]
    o = N["series"].query("tecnico == 'Ortiz' and ronda == 'Semifinal'")
    jw = N["series"].query("tecnico == 'Jardine' and avanzo")
    fin = N["finales"].query("torneo != 'Referencia'")
    ref = N["finales"].query("torneo == 'Referencia'").set_index("rival")
    fue = N["fue"].set_index(["formacion", "metrica"])
    l3 = N["fvs"].query("formacion == 'Línea de 3'").set_index("metrica")
    u3 = N["forms"]
    piv = N["rivales"]
    cp = N["cam_perd"]
    S = {}
    m442 = int(N["fue"].query("formacion == '4-4-2'").minutos_comparables.iloc[0])
    S["minuto"] = [
        ("El América tiene un ADN que no depende del técnico",
         f"Con Solari, Ortiz y Jardine, el América tuvo más balón, generó más peligro y concedió menos que la liga: "
         f"control del balón {adn.loc['Control del balón', 'Solari']:.0f}, {adn.loc['Control del balón', 'Ortiz']:.0f} y "
         f"{adn.loc['Control del balón', 'Jardine']:.0f} de 100. Ese es el piso del club."),
        ("Jardine lo pulió: sale jugando, espera y remata mejor",
         f"Saca en corto el {c['Jardine']:.0f} % de sus saques de meta (Ortiz {c['Ortiz']:.0f} %), presiona menos que la liga y "
         f"tira mejor: {x['Jardine']:.2f} xG por tiro (Ortiz {x['Ortiz']:.2f}). El balón parado da el {N['xg_bp_pct']:.0f} % de su peligro."),
        ("Lee el partido",
         f"Perdiendo por un gol empuja ({m_ft['Pierde por 1']:+.0f} puntos de dominio); ganando por uno guarda el balón lejos del área "
         f"({m_ft['Gana por 1']:+.0f}). En casa suma {L.loc['Puntos por partido', 'dif']:+.2f} puntos por partido y presiona más arriba."),
        ("En liguilla, el campeón juega de copa",
         f"En las series que pasó dejó dar {pp_s.si:.0f} pases al rival antes de presionar; en las que perdió, {pp_s.no:.0f}. "
         f"Ortiz perdió sus tres semifinales presionando como nunca."),
        ("Dónde se le escapa",
         f"El cierre del primer tiempo es su momento más vulnerable ({mi.loc['30-45+', 'xg_contra_90']:.2f} xG en contra por 90'), "
         f"cuando pierde le hacen el doble de daño al contragolpe y con tres centrales se repliega sin protegerse más."),
    ]
    S["adn"] = (
        f"<p>Comparamos al América con los 70 técnicos de la Liga MX que dirigieron 15 partidos o más entre 2021 y 2025, rasgo por rasgo, "
        f"de 0 a 100 (50 es el técnico típico). Cada rasgo se compara con la liga <strong>del mismo torneo</strong> y descuenta "
        f"la fuerza del rival y la localía, para que el perfil sea del técnico y no de su calendario.</p>"
        f"<p><strong>Tres rasgos quedan arriba de la liga con los tres técnicos y en todos los torneos:</strong> control del balón, "
        f"peligro generado y solidez defensiva. Eso es del club. Lo que cambia con cada técnico es cómo presiona "
        f"(presión alta: Solari {adn.loc['Presión alta', 'Solari']:.0f}, Ortiz {adn.loc['Presión alta', 'Ortiz']:.0f}, Jardine "
        f"{adn.loc['Presión alta', 'Jardine']:.0f}), qué tan directo va al arco y cuánto reacciona tras perder.</p>")
    S["jardine_con"] = (
        f"<p><strong>Sale jugando.</strong> Saca en corto el {c['Jardine']:.0f} % de sus saques de meta (Ortiz {c['Ortiz']:.0f} %, "
        f"Solari {c['Solari']:.0f} %) y el pase corto lo recibe un mediocentro que baja en el {N['mc_baja']['Jardine']:.0f} % de las "
        f"veces (Ortiz {N['mc_baja']['Ortiz']:.0f} %): antes iba casi siempre al central.</p>"
        f"<p><strong>No tira más, tira mejor.</strong> {N['tiros_pp']['Jardine']:.1f} tiros por partido, como sus antecesores, pero "
        f"{x['Jardine']:.2f} xG por tiro (Ortiz {x['Ortiz']:.2f}, Solari {x['Solari']:.2f}). Su jugada distintiva es el pase atrás al "
        f"área: {N['pase_atras']['Jardine']:.0f} % de su peligro (Ortiz {N['pase_atras']['Ortiz']:.0f} %).</p>"
        f"<p><strong>Cómo llegan los goles.</strong> Separamos los {int(t.goles.sum())} goles sin penal en cuatro tipos según cómo fue la "
        f"jugada: {t.loc['Balón parado', 'pct']:.0f} % de balón parado, {t.loc['Ataque rápido tras recuperar', 'pct']:.0f} % ataque rápido "
        f"tras recuperar, {t.loc['Ataque corto en campo rival', 'pct']:.0f} % ataque corto en campo rival y "
        f"{t.loc['Ataque elaborado', 'pct']:.0f} % ataque elaborado (unos {t.loc['Ataque elaborado', 'mediana_pases']:.0f} pases). "
        f"Jardine y Ortiz reparten casi igual; Solari dependía del ataque rápido "
        f"({rep.loc['Solari', 'Ataque rápido tras recuperar']:.0f} % de sus goles).</p>")
    S["jardine_sin"] = (
        f"<p><strong>No asfixia: espera y se junta.</strong> Deja dar {N['ppda_liga']['Jardine']:.1f} pases más que la liga antes de "
        f"intentar robar (el {int(N['ppda_lugar']['Jardine'])}.º que más deja de 70 técnicos). En bloque medio su equipo mide "
        f"{N['bloque']['Jardine']:.0f} yardas de largo (Ortiz {N['bloque']['Ortiz']:.0f}): no adelanta la defensa para asfixiar, la junta.</p>"
        f"<p><strong>Gana las transiciones.</strong> Genera {N['tr_ratio']['Jardine']:.1f} veces más peligro al contragolpe del que "
        f"concede (Ortiz {N['tr_ratio']['Ortiz']:.1f}, Solari {N['tr_ratio']['Solari']:.1f}). Tras perder el balón lo recupera en 5 "
        f"segundos o menos el {N['recup5']['Jardine']:.0f} % de las veces, igual que con Ortiz y Solari.</p>"
        f"<p><strong>Defiende el área.</strong> El rival llega {N['dba_llegadas']['Jardine']:.0f} veces por partido a nuestras últimas "
        f"30 yardas y el América corta el {N['dba_sin_tiro']['Jardine']:.0f} % de esas jugadas sin permitir un tiro.</p>")
    S["jardine_bp"] = (
        f"<p><strong>El balón parado es un arma.</strong> Juega en corto el {N['corner_corto']['Jardine']:.0f} % de sus córners "
        f"(Ortiz {N['corner_corto']['Ortiz']:.0f} %) y cada córner vale {N['xg_corner']['Jardine']:.3f} xG. La mayor parte del "
        f"peligro llega en la segunda jugada, no en el remate directo del envío.</p>"
        f"<p><strong>En contra, el primer palo.</strong> Defiende los córners con {N['def_area']['Jardine']:.0f} jugadores en el área "
        f"y un esquema mixto ({N['pegados']['Jardine']:.0f} % pegados a un rival, frente a {N['azar']['Jardine']:.0f} % si fuera al azar). "
        f"El {N['primer_palo']:.0f} % del peligro que concede en córners nace en el primer palo.</p>"
        f"<p><strong>El juego pasa por el doble pivote.</strong> Fidalgo genera el {N['fidalgo']:.0f} % del aporte con balón del "
        f"equipo y es el eje de la red de pases. Los extremos juegan a pierna cambiada (diestro por la izquierda, zurdo por la derecha), "
        f"una marca que empezó con Ortiz.</p>")
    S["ajusta"] = (
        f"<p><strong>El marcador cambia el plan.</strong> Comparado con el mismo partido empatado: perdiendo por uno, el América de "
        f"Jardine tiene {m_pos['Pierde por 1']:+.0f} puntos de posesión y {m_ft['Pierde por 1']:+.0f} de dominio territorial; ganando por "
        f"uno, el dominio baja {abs(m_ft['Gana por 1']):.0f} puntos: guarda el balón lejos del área en vez de buscar el segundo.</p>"
        f"<p><strong>El rival y la localía.</strong> Contra rivales débiles tiene {N['pos_debil']:.0f} % de posesión; contra fuertes, "
        f"{N['pos_fuerte']:.0f} %. En casa suma {L.loc['Puntos por partido', 'si']:.2f} puntos por partido y de visita "
        f"{L.loc['Puntos por partido', 'no']:.2f}, y además juega distinto: {L.loc['Dominio territorial (%)', 'dif']:+.0f} puntos de "
        f"dominio y {L.loc['Acciones defensivas en campo rival (%)', 'dif']:+.0f} de acciones defensivas en campo rival.</p>"
        f"<p><strong>Mueve el banco pronto.</strong> Hace su primer cambio en el descanso en el {N['descanso']['Jardine']:.0f} % de los "
        f"partidos (Ortiz {N['descanso']['Ortiz']:.0f} %, Solari {N['descanso']['Solari']:.0f} %). Perdiendo, cuando entra alguien más "
        f"ofensivo por un defensor, las ocasiones a favor suben {cp.cambio_xg_favor:+.2f} xG por cada 100 posesiones sin que suban las "
        f"del rival.</p>")
    S["ganador"] = (
        f"<p>Ocho torneos en la ventana del reto, tres títulos, todos con Jardine. ¿Qué hizo distinto el campeón? <strong>En la fase regular jugó como el "
        f"América de siempre; en la liguilla, como un equipo de copa.</strong></p>"
        f"<p>En las {int(pp_s.n_si)} series de liguilla que el América pasó dejó dar {pp_s.si:.1f} pases al rival antes de presionar; "
        f"en las {int(pp_s.n_no)} que perdió, {pp_s.no:.1f}. También tuvo menos balón ({po_s.si:.0f} % frente a {po_s.no:.0f} %) y no "
        f"concedió más ocasiones. Y generó más a balón parado: {bpf.si:.2f} xG por serie frente a {bpf.no:.2f}.</p>"
        f"<p><strong>Ortiz es el contraejemplo.</strong> Perdió sus tres semifinales queriendo dominar: "
        + "; ".join(f"{r.rival} {r['global']} (dejó dar {r.ppda:.0f} pases)" for _, r in o.iterrows())
        + f". En las series que pasó Jardine, la mediana fue de {jw.ppda.median():.0f}. En dos de esas semifinales Ortiz tuvo ocasiones "
        f"iguales o mejores que el rival: el plan, no la calidad, marcó la diferencia.</p>"
        f"<p><strong>Las finales.</strong> En fase regular Jardine tuvo {ref.loc['Fase regular (todos)', 'posesion']:.0f} % de posesión y "
        f"{ref.loc['Fase regular contra rivales fuertes', 'posesion']:.0f} % contra rivales fuertes. En sus finales: "
        + "; ".join(f"{r.torneo.replace('Apertura', 'Ap').replace('Clausura', 'Cl')} vs {r.rival} {r['global']} ({r.posesion:.0f} % de posesión)"
                    for _, r in fin.iterrows())
        + ". Las dos últimas que ganó las jugó con menos balón que nunca; la que perdió, contra Toluca, la jugó dominando.</p>")
    claras = der.loc["Calidad de cada tiro (xG por tiro)"]
    contra = der.loc["Peligro que concede al contragolpe"]
    dom = der.loc["Dominio territorial con el partido empatado (%)"]
    S["criticos"] = (
        f"<p><strong>El cierre del primer tiempo.</strong> Entre el minuto 30 y el descanso le generan {mi.loc['30-45+', 'xg_contra_90']:.2f} "
        f"xG por 90 minutos; al volver del descanso, {mi.loc['45-60', 'xg_contra_90']:.2f}. Es su tramo más vulnerable, y el arranque "
        f"del segundo tiempo, el más sólido.</p>"
        f"<p><strong>Cuando pierde, pierde igual.</strong> En las derrotas tira peor ({claras.si:.2f} frente a {claras.no:.2f} xG por "
        f"tiro), le hacen casi el doble de daño al contragolpe ({contra.si:.2f} frente a {contra.no:.2f}) y, con el partido empatado, "
        f"domina menos el campo ({dom.si:.0f} % frente a {dom.no:.0f} %). La presión es la misma: no pierde por presionar menos.</p>"
        f"<p><strong>Tres centrales no lo protegen.</strong> Jardine usó línea de 3 sobre todo contra rivales fuertes. Comparado con "
        f"la línea de 4, con el mismo rival y marcador, el equipo cede el balón ({l3.loc['Posesión (%)', 'dif']:+.0f} puntos de posesión), "
        f"pisa menos el área y concede más tiros ({l3.loc[chr(84) + 'iros en contra por 90' + chr(39), 'dif']:+.1f} por 90'), sin conceder "
        f"menos ocasiones.</p>"
        f"<p><strong>Pachuca.</strong> Es el rival contra el que más puntos deja ir: {piv.loc['Pachuca', 'puntos']:.2f} por partido "
        f"cuando sus ocasiones daban para {piv.loc['Pachuca', 'xpts']:.2f}, con {piv.loc['Pachuca', 'pct_victorias']:.0f} % de victorias.</p>")
    g442 = fue.loc[("4-4-2", "Toques en el área rival (por 100 posesiones)")]
    g442c = fue.loc[("4-4-2", "Ocasiones en contra (xG por 90')")]
    S["recos"] = [
        ("Plan de liguilla: esperar, no asfixiar",
         "En eliminación directa, jugar con bloque medio y presión de espera; ceder la iniciativa contra rivales fuertes en vez de dominar a toda costa.",
         f"Así pasó el América {int(pp_s.n_si)} de {int(pp_s.n_si + pp_s.n_no)} series: dejó dar {pp_s.si:.0f} pases antes de presionar "
         f"(en las que perdió, {pp_s.no:.0f}) sin conceder más ocasiones. Ortiz perdió sus tres semifinales presionando.",
         "PPDA en cada partido de liguilla: 15 o más. La posesión no es meta.",
         "Son 20 series: es un patrón que se repite, no una garantía."),
        ("Contra los grandes, 4-4-2 en lugar de tres centrales",
         "Contra los rivales fuertes, cerrar los partidos con 4-4-2; dejar la línea de 3 como recurso puntual.",
         f"Contra fuertes, el 4-4-2 llega más al área que el 4-2-3-1 ({g442.dif:+.0f} toques por 100 posesiones) y concede lo mismo "
         f"({g442c.dif:+.2f} xG por 90'). La línea de 3 cede el balón sin conceder menos.",
         "Toques en el área rival por cada 100 posesiones y ocasiones en contra (xG) por 90' en partidos contra rivales fuertes.",
         f"Son {m442:,} minutos de 4-4-2 contra fuertes; describe lo que pasó, no prueba que el dibujo lo cause."),
        ("Cerrar el primer tiempo y mover el banco a tiempo",
         "Un ajuste de orden y de salida a partir del minuto 30, no solo en el descanso; perdiendo, meter un perfil ofensivo antes del 60'.",
         f"Del 30' al descanso le generan {mi.loc['30-45+', 'xg_contra_90']:.2f} xG por 90' (después del descanso, {mi.loc['45-60', 'xg_contra_90']:.2f}). "
         f"Perdiendo, cambiar un defensor por alguien más ofensivo sube las ocasiones {cp.cambio_xg_favor:+.2f} xG por 100 posesiones sin conceder más.",
         "Ocasiones en contra (xG) entre el 30' y el 45'; minuto del primer cambio cuando va perdiendo.",
         "Los cambios se miden antes y después: no separan el efecto del cambio de lo que el partido ya venía haciendo."),
        ("Primer palo y relevo del organizador",
         "Ajustar la marca zonal del área chica hacia el primer palo en los córners rivales y preparar un relevo para el organizador del doble pivote.",
         f"El {N['primer_palo']:.0f} % del peligro que concede en córners nace en el primer palo. Fidalgo genera el {N['fidalgo']:.0f} % del "
         f"aporte con balón del equipo y la salida corta pasa por él.",
         "Porcentaje del xG de córner rival que llega por el primer palo; minutos del relevo en el rol de organizador.",
         "Los córners son pocos por partido: el indicador se lee por torneo, no por partido."),
    ]
    probamos = N["hip"].reset_index()
    probamos = probamos[probamos.seccion == "6 · Lo que probamos"]
    limpia = lambda s: s.replace(" (ver C2)", " (sección 4)").replace("no se puede medir con el cubo", "no se puede medir con los datos resumidos")
    sp = set()
    S["probamos"] = "".join(f"<tr><td>{e(r.hipotesis, sp)}</td><td>{e(limpia(r.evidencia), sp)}</td></tr>" for r in probamos.itertuples())
    enc = N["encaje"]
    S["aporte"] = (
        f"<p><strong>El ADN del Entrenador</strong> es nuestra forma de leer a cualquier técnico de la Liga MX con 8 rasgos de juego, "
        f"comparados con la liga del mismo torneo y descontando rival y localía. Lo probamos con partidos de 2025–26 que no usó para "
        f"aprender: en el 31 % de esos partidos el técnico correcto queda entre los 5 más parecidos de la liga (por azar sería 16 %), "
        f"y reconoció a Almada en el América sin haberlo visto ahí (lo ubica 2.º de 31 técnicos posibles).</p>"
        f"<p><strong>El Índice de Encaje</strong> mide qué tan cerca está un técnico del ADN del club (100 = el más parecido). Fuera del "
        f"América, los perfiles más cercanos son {', '.join(f'{i.split(' (')[0]} ({v:.0f})' for i, v in enc[~enc.index.str.contains('América')].indice_encaje.head(3).items())}. "
        f"Sirve para elegir técnico con datos y para revisar, torneo a torneo, si el técnico en turno se aleja de la identidad del club.</p>")
    S["epilogo"] = (
        f"<p>Fuera de la ventana del reto, en 2025–26, el América de Jardine mantuvo el balón pero dejó de convertirlo en ocasiones: "
        f"{(lambda s: s[0].lower() + s[1:])(N['hip'].loc['D8', 'evidencia'].split(' Depende')[0])} Con Almada (2026) cambió el estilo con casi la misma plantilla: "
        f"el estilo sigue al técnico.</p>")
    return S


def build() -> str:
    N = cifras()
    S = cuerpo(N)
    figs = {gid: json.loads(fn(N).to_json()) for gid, fn in FIGURAS.items()}
    sm = set()
    minuto = "".join(f'<li><span class="num">{i}</span><div><h3>{e(t, sm)}</h3><p>{e(p, sm)}</p></div></li>'
                     for i, (t, p) in enumerate(S["minuto"], start=1))
    sj = set()
    for k in ["adn", "jardine_con", "jardine_sin", "jardine_bp", "ajusta", "ganador", "criticos", "aporte", "epilogo"]:
        S[k] = siglas(S[k], sj if k.startswith("jardine") else set())
    sr = set()
    recos = "".join(f"""<article class="reco"><h3>{e(t, sr)}</h3>
  <dl><dt>Qué hacer</dt><dd>{e(q, sr)}</dd><dt>Por qué</dt><dd>{e(p, sr)}</dd><dt>Cómo medirlo</dt><dd>{e(k, sr)}</dd><dt>Ojo</dt><dd>{e(o, sr)}</dd></dl>
</article>""" for t, q, p, k, o in S["recos"])
    app = (f'<a href="{APP_URL}">{APP_URL}</a>' if APP_URL else "el explorador interactivo que acompaña este reporte")
    return Template(TPL.read_text(encoding="utf-8")).substitute(
        minuto=minuto, adn=S["adn"], jardine_con=S["jardine_con"], jardine_sin=S["jardine_sin"], jardine_bp=S["jardine_bp"],
        ajusta=S["ajusta"], ganador=S["ganador"], criticos=S["criticos"], recos=recos, probamos=S["probamos"],
        aporte=S["aporte"], epilogo=S["epilogo"], app=app,
        g_radar=fig_html("g-radar", "El ADN de cada técnico: 8 rasgos de 0 a 100 frente a los 70 técnicos de la liga (50 = típico). Apertura 2021 – Clausura 2025.", 460),
        g_mapas=fig_html("g-mapas", "Jardine, Apertura 2023 – Clausura 2025. Izquierda: ocasiones (xG) por partido según dónde se tiró. Derecha: robos por partido según dónde recuperó el balón.", 330),
        g_tipos=fig_html("g-tipos", "Goles sin penal de cada técnico según cómo fue la jugada. El balón parado sigue la definición de nuestro marco.", 260),
        g_marcador=fig_html("g-marcador", "Jardine: cómo cambian el dominio territorial y la posesión según el marcador, frente al mismo partido empatado. La línea es el margen del 90 %.", 300),
        g_minuto=fig_html("g-minuto", "Jardine: ocasiones (xG) a favor y en contra por 90 minutos en cada tramo. La banda es el margen del 90 % de las ocasiones en contra; el tramo sombreado es el cierre del primer tiempo.", 320),
        g_torneos=fig_html("g-torneos", "Cada torneo: cuántos pases deja dar al rival antes de presionar en la fase regular (gris) y en la liguilla (color según hasta dónde llegó; estrella = título).", 340),
        g_series=fig_html("g-series", "Cada punto es una serie de liguilla. Arriba = espera más antes de presionar. Relleno = el América pasó; vacío = quedó eliminado.", 420),
        g_derrotas=fig_html("g-derrotas", "Lo que cambia en las derrotas frente a las victorias, con el mismo técnico y el mismo nivel de rival (solo diferencias claras). Dominio y presión se miden con el partido empatado.", 340),
        g_fuertes=fig_html("g-fuertes", "Contra rivales fuertes, con el mismo técnico y marcador: cada dibujo frente al 4-2-3-1. Punto relleno = diferencia clara; la línea es el margen del 90 %.", 260),
        g_encaje=fig_html("g-encaje", "Índice de Encaje: los 10 técnicos de la Liga MX más cercanos al ADN del América (2021–2025, 15 partidos o más).", 380),
        g_epilogo=fig_html("g-epilogo", "Epílogo. Jardine en fase regular: ocasiones (xG) por partido. Los puntos vacíos (2025–26) están fuera de la ventana del reto.", 280),
        figs=json.dumps(figs, ensure_ascii=False).replace("</", "<\\/"))


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(), encoding="utf-8")
    print(f"{OUT} · {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()

"""Piezas visuales Plotly compartidas por la app (app/streamlit_app.py) y el reporte final.

Una sola paleta y una sola cancha: lo que se ve en el explorador y en el reporte sale de las mismas funciones.
Cancha StatsBomb 120 × 80 yd, siempre en el sentido del América (ataca hacia la derecha).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from src import cube as K

COACH_COLOR = {"Solari": "#2a78d6", "Ortiz": "#eb6834", "Jardine": "#1baf7a", "Almada": "#4a3aa7",
               "Cervantes": "#898781"}
INK, MUTED, GRID, LINE = "#0b0b0b", "#898781", "#e1e0d9", "#c3c2b7"
RESULT_COLOR = {"W": "#1baf7a", "D": "#c3c2b7", "L": "#e34948"}
RESULT_LABEL = {"W": "Victoria", "D": "Empate", "L": "Derrota"}
TIER_COLOR = {"Fuerte": "#e34948", "Medio": "#c3c2b7", "Débil": "#1baf7a"}
STAGE_COLOR = {"Campeón": "#d4a017", "Final perdida": "#eb6834", "Semifinal": "#2a78d6", "Cuartos": "#8fb8ea",
               "Play-in": "#c3c2b7", "No clasificó": "#c3c2b7", "En curso": "#c3c2b7"}


def torneo_short(t: str) -> str:
    return t.replace("Apertura ", "Ap ").replace("Clausura ", "Cl ")


def pitch_shapes(fig: go.Figure) -> go.Figure:
    kw = dict(line=dict(color=LINE, width=1), layer="above")
    shapes = [dict(type="rect", x0=0, y0=0, x1=120, y1=80), dict(type="line", x0=60, y0=0, x1=60, y1=80),
              dict(type="rect", x0=0, y0=18, x1=18, y1=62), dict(type="rect", x0=102, y0=18, x1=120, y1=62),
              dict(type="rect", x0=0, y0=30, x1=6, y1=50), dict(type="rect", x0=114, y0=30, x1=120, y1=50),
              dict(type="circle", x0=50, y0=30, x1=70, y1=50)]
    for s in shapes:
        fig.add_shape(**s, **kw)
    return fig


def pitch_heat(m: np.ndarray, title: str, fmt: str = "{:.1f}", scale="Blues", zmax=None) -> go.Figure:
    """Mapa de calor sobre la cancha (rejilla de K.CELL yd): valor por partido en cada celda."""
    xs = np.arange(K.CELL / 2, 120, K.CELL)
    ys = np.arange(K.CELL / 2, 80, K.CELL)
    top = np.nanmax(m) if np.size(m) else 0
    text = [[fmt.format(v) if v >= (top * 0.15 if top > 0 else 1) else "" for v in row] for row in m]
    fig = go.Figure(go.Heatmap(z=m, x=xs, y=ys, colorscale=scale, zmin=0, zmax=zmax, showscale=False,
                               text=text, texttemplate="%{text}", textfont=dict(size=10),
                               hovertemplate="%{z:.2f} por partido<extra></extra>"))
    pitch_shapes(fig)
    fig.update_layout(title=dict(text=title, font=dict(size=13)), height=300, margin=dict(l=5, r=5, t=40, b=5),
                      xaxis=dict(visible=False, range=[-2, 122]), yaxis=dict(visible=False, range=[82, -2], scaleanchor="x"),
                      plot_bgcolor="white")
    fig.add_annotation(x=118, y=81.5, text="ataca →", showarrow=False, font=dict(size=10, color=MUTED), xanchor="right")
    return fig


def radar(series: dict[str, pd.Series], title: str) -> go.Figure:
    """Rasgos del ADN de 0 a 100; el color sale del técnico (primera palabra del nombre de la serie)."""
    fig = go.Figure()
    for name, s in series.items():
        coach = name.split(" ")[0]
        r = list(s.values) + [s.values[0]]
        th = list(s.index) + [s.index[0]]
        fig.add_trace(go.Scatterpolar(r=r, theta=th, name=name, fill="toself", opacity=0.55,
                                      line=dict(color=COACH_COLOR.get(coach, MUTED), width=2),
                                      hovertemplate="%{theta}: %{r:.0f} de 100<extra>" + name + "</extra>"))
    fig.update_layout(polar=dict(radialaxis=dict(range=[0, 100], tickvals=[25, 50, 75], gridcolor=GRID),
                                 angularaxis=dict(gridcolor=GRID)),
                      title=dict(text=title, font=dict(size=13)), height=430, margin=dict(l=40, r=40, t=60, b=30),
                      legend=dict(orientation="h", y=-0.08))
    return fig

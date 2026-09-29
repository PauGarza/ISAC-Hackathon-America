"""Visuales de cancha de la historia de Jardine (§3.2 y §3.3). Estilo común de src/eda.py y colores fijos por
técnico de src/coach_viz.py (paleta validada: el color sigue al técnico, nunca al orden).

Convenciones: cancha StatsBomb 120 × 80, el América ataca hacia la derecha y su banda izquierda queda arriba
(eje y invertido). Magnitudes en una sola rampa secuencial (azul claro → oscuro, con la MISMA escala en los
paneles que se comparan). Texto siempre en tinta. Cada figura lleva al pie la muestra de la que sale.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize
from matplotlib.patches import Arc, Circle, FancyArrow, Rectangle

from src import eda
from src.coach_viz import COACH_COLOR, LEAGUE
from src.story import COACHES, PROTAGONIST

eda.set_style()
LINE = eda.AXIS
# vistas de cancha: (x_min, x_max, y_abajo, y_arriba); el eje y está invertido (banda izquierda arriba)
VIEWS = {"full": (-3, 123, 83, -3), "half": (57, 123, 83, -3), "box": (77, 123, 72, 8)}


def sample_note(scope: pd.DataFrame) -> str:
    n = scope.groupby("coach").size()
    parts = " · ".join(f"{c} {n.get(c, 0)}" for c in COACHES if c in n)
    return f"Ventana oficial Ap 2021 – Cl 2025 · partidos: {parts} · Datos: StatsBomb · el América ataca hacia la derecha"


def _footer(fig, text: str, y: float = 0.012):
    fig.text(0.01, y, text, fontsize=6.5, color=eda.MUTED, ha="left", va="bottom")


def _panels(n: int, w: float = 11.5, h: float = 4.0, top: float = 0.8, bottom: float = 0.2):
    """n canchas en fila con márgenes ajustados (la altura se elige para que la cancha llene el panel)."""
    fig, axes = plt.subplots(1, n, figsize=(w, h))
    fig.subplots_adjust(left=0.01, right=0.99, top=top, bottom=bottom, wspace=0.08)
    return fig, np.atleast_1d(axes)


def _suptitle(fig, title: str):
    fig.suptitle(title, x=0.01, y=0.975, ha="left", va="top", fontsize=11, fontweight="bold")


# ------------------------------------------------------------------ cancha
def draw_pitch(ax, view: str = "full", arrow: bool = True):
    """Cancha 120 × 80 con líneas recesivas. view = 'full', 'half' (mitad rival) o 'box' (último tercio y área)."""
    kw = dict(color=LINE, lw=0.8, zorder=3, fill=False)
    ax.add_patch(Rectangle((0, 0), 120, 80, **kw))
    ax.plot([60, 60], [0, 80], color=LINE, lw=0.8, zorder=3)
    ax.add_patch(Circle((60, 40), 10, **kw))
    for x0, w in [(0, 18), (102, 18)]:
        ax.add_patch(Rectangle((x0, 18), w, 44, **kw))
    for x0, w in [(0, 6), (114, 6)]:
        ax.add_patch(Rectangle((x0, 30), w, 20, **kw))
    for x0 in (-2, 120):
        ax.add_patch(Rectangle((x0, 36), 2, 8, **kw))
    for x, a0 in [(12, 308), (108, 128)]:
        ax.add_patch(Arc((x, 40), 20, 20, theta1=a0, theta2=a0 + 104, color=LINE, lw=0.8, zorder=3))
        ax.scatter([x], [40], s=3, color=LINE, zorder=3)
    x0, x1, yb, yt = VIEWS[view]
    ax.set_xlim(x0, x1)
    ax.set_ylim(yb, yt)
    ax.set_aspect("equal")
    ax.axis("off")
    if arrow:
        xa = x0 + 0.45 * (x1 - x0)
        ax.annotate("", xy=(xa + 14, yb + 1.8), xytext=(xa, yb + 1.8), annotation_clip=False,
                    arrowprops=dict(arrowstyle="->", color=eda.MUTED, lw=0.8))
        ax.text(xa - 1, yb + 1.8, "ataque", fontsize=6, color=eda.MUTED, ha="right", va="center")
    return ax


def _text_color(rgba) -> str:
    r, g, b = rgba[:3]
    return eda.SURFACE if 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.45 else eda.INK


def zone_heat(ax, grid: pd.DataFrame, value: str, vmax: float, fmt: str = "{:.0%}", min_label: float = 0.0,
              cmap=eda.SEQ):
    """Pinta celdas (x0, x1, y0, y1) de una rejilla agregada; 2 px de separación entre celdas; rótulos selectivos."""
    norm = Normalize(0, vmax)
    for r in grid.itertuples():
        v = getattr(r, value)
        if not np.isfinite(v):
            continue
        c = cmap(norm(v))
        ax.add_patch(Rectangle((r.x0, r.y0), r.x1 - r.x0, r.y1 - r.y0, facecolor=c, edgecolor=eda.SURFACE,
                               lw=2, zorder=1))
        if v >= min_label:
            ax.text((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, fmt.format(v), ha="center", va="center",
                    fontsize=7, color=_text_color(c), zorder=4,
                    bbox=dict(boxstyle="round,pad=0.1", fc=c, ec="none"))
    return norm


def _colorbar(fig, norm, label: str, fmt=None, rect=(0.33, 0.075, 0.34, 0.022)):
    sm = plt.cm.ScalarMappable(norm=norm, cmap=eda.SEQ)
    cb = fig.colorbar(sm, cax=fig.add_axes(rect), orientation="horizontal", format=fmt)
    cb.outline.set_visible(False)
    cb.set_label(label, fontsize=7, color=eda.INK_2)
    cb.ax.xaxis.set_label_position("top")
    cb.ax.tick_params(labelsize=6)
    return cb


def _coach_title(ax, coach: str, text: str, view: str = "full"):
    """Título del panel: marca del color del técnico + nombre (tinta, negritas) y, debajo, el dato clave."""
    x0, _, _, yt = VIEWS[view]
    ax.text(x0 + 1, yt - 8, "●", color=COACH_COLOR[coach], fontsize=10, va="center", ha="left")
    ax.text(x0 + 1 + 0.035 * (VIEWS[view][1] - x0), yt - 8, coach, fontsize=9, fontweight="bold", color=eda.INK,
            va="center", ha="left")
    ax.text(x0 + 1, yt - 3, text, fontsize=7, color=eda.INK_2, va="center", ha="left")


# ------------------------------------------------------------------ §3.2a salida
def fig_goal_kicks(grid: pd.DataFrame, summary: pd.DataFrame, scope: pd.DataFrame, title: str):
    """Dónde cae el saque de meta (% de los saques de cada técnico por zona), un panel por técnico."""
    fig, axes = _panels(3)
    vmax = grid.share.max()
    sk = summary[summary.kind == "Saque de meta"].set_index("coach")
    for ax, c in zip(axes, COACHES):
        draw_pitch(ax)
        norm = zone_heat(ax, grid[grid.coach == c], "share", vmax, min_label=0.04)
        _coach_title(ax, c, f"{sk.loc[c, 'pct_corto']:.0f} % en corto · {sk.loc[c, 'por_partido']:.1f} saques por partido")
    _colorbar(fig, norm, "% de los saques de meta del técnico que caen en cada zona", fmt=lambda v, _: f"{v:.0%}")
    _suptitle(fig, title)
    _footer(fig, sample_note(scope) + " · corto = menos de 32 yd")
    return fig


# ------------------------------------------------------------------ §3.2b progresión
def fig_lanes(prog: pd.DataFrame, entries_sum: pd.DataFrame, scope: pd.DataFrame, title: str):
    """Por carril: flecha con grosor = % de las acciones progresivas (pases + conducciones) que terminan en él;
    a la derecha, entradas al último tercio por partido por ese carril."""
    lanes = ["Izquierdo", "Central", "Derecho"]
    yc = dict(zip(lanes, [80 / 6, 40, 80 - 80 / 6]))
    tot = prog.groupby(["coach", "lane"]).n.sum()
    share = tot / tot.groupby("coach").transform("sum")
    f3 = entries_sum[entries_sum.entrada == "Último tercio"].groupby(["coach", "lane"]).por_partido.sum()
    ppm = prog.groupby("coach").por_partido.sum()
    fig, axes = _panels(3, h=3.9)
    for ax, c in zip(axes, COACHES):
        draw_pitch(ax)
        ax.set_xlim(-3, 142)
        for l in lanes:
            w = share[(c, l)] * 32
            ax.add_patch(FancyArrow(30, yc[l], 78, 0, width=w, head_width=w * 1.5, head_length=7,
                                    length_includes_head=True, color=COACH_COLOR[c], alpha=0.85, lw=0, zorder=4))
            ax.text(28, yc[l], f"{share[(c, l)]:.0%}", fontsize=8, color=eda.INK, ha="right", va="center", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.12", fc=eda.SURFACE, ec="none", alpha=0.85))
            ax.text(124, yc[l], f"{f3[(c, l)]:.1f}", fontsize=8, color=eda.INK, ha="left", va="center")
        ax.text(124, -2, "entradas al\núltimo tercio\npor partido", fontsize=5.5, color=eda.MUTED, ha="left", va="bottom")
        _coach_title(ax, c, f"{ppm[c]:.0f} acciones progresivas por partido")
    _suptitle(fig, title)
    fig.text(0.01, 0.1, "Grosor de la flecha y % = parte de los pases y conducciones progresivas que terminan en ese "
             "carril (arriba, el carril izquierdo del América).", fontsize=7, color=eda.INK_2)
    _footer(fig, sample_note(scope) + " · progresiva = acerca el balón ≥ 25 % a la portería (marco)")
    return fig


def fig_box_entries(grid: pd.DataFrame, entries_sum: pd.DataFrame, scope: pd.DataFrame, title: str):
    """Dónde entra al área (celdas del área, entradas por partido), una vista del área por técnico."""
    fig, axes = _panels(3, w=9.5, h=4.7, top=0.8, bottom=0.16)
    vmax = grid.por_partido.max()
    box = entries_sum[entries_sum.entrada == "Área"]
    tot = box.groupby("coach").por_partido.sum()
    carry = box[box.method == "Conducción"].groupby("coach").por_partido.sum()
    for ax, c in zip(axes, COACHES):
        draw_pitch(ax, view="box")
        norm = zone_heat(ax, grid[grid.coach == c], "por_partido", vmax, fmt="{:.1f}", min_label=0.5)
        _coach_title(ax, c, f"{tot[c]:.1f} por partido · {carry[c] / tot[c]:.0%} conduciendo", view="box")
    _colorbar(fig, norm, "entradas al área por partido que terminan en cada zona", rect=(0.33, 0.07, 0.34, 0.02))
    _suptitle(fig, title)
    _footer(fig, sample_note(scope) + " · entrada = pase completo o conducción que entra al área desde fuera")
    return fig


# ------------------------------------------------------------------ §3.2c ocasiones
def fig_shot_map(s: pd.DataFrame, origin_sum: pd.DataFrame, scope: pd.DataFrame, title: str, coach: str = PROTAGONIST):
    """Mapa de tiros (sin penales) por origen de la jugada: tamaño = xG; relleno oscuro = gol."""
    fig, axes = _panels(3, h=5.0, top=0.84, bottom=0.14)
    color = COACH_COLOR[coach]
    o = origin_sum[origin_sum.coach == coach].set_index("origin")
    for ax, origin in zip(axes, ["Juego posicional", "Transición", "Balón parado"]):
        draw_pitch(ax, view="half")
        d = s[(s.coach == coach) & (s.origin == origin) & (s.x >= 58)]
        miss, goal = d[~d.goal], d[d.goal]
        ax.scatter(miss.x, miss.y, s=miss.xg * 500 + 6, color=color, alpha=0.35, lw=0, zorder=5)
        ax.scatter(goal.x, goal.y, s=goal.xg * 500 + 6, color=eda.INK, alpha=0.85, edgecolor=eda.SURFACE, lw=0.8,
                   zorder=6)
        r = o.loc[origin]
        ax.text(58, -11, origin, fontsize=9, fontweight="bold", color=eda.INK, va="center")
        ax.text(58, -5, f"{r.tiros_por_partido:.1f} tiros y {r.xg_por_partido:.2f} xG por partido · "
                f"{r.pct_xg:.0f} % del xG", fontsize=7, color=eda.INK_2, va="center")
    handles = [plt.scatter([], [], s=x * 500 + 6, color=color, alpha=0.35, lw=0) for x in (0.05, 0.2, 0.5)]
    handles.append(plt.scatter([], [], s=0.2 * 500 + 6, color=eda.INK, edgecolor=eda.SURFACE))
    fig.legend(handles, ["xG 0.05", "xG 0.20", "xG 0.50", "gol"], loc="lower center", ncol=4,
               bbox_to_anchor=(0.5, 0.04), fontsize=7)
    _suptitle(fig, title)
    _footer(fig, f"Ventana oficial Ap 2021 – Cl 2025 · {coach}, {int((scope.coach == coach).sum())} partidos · "
            "sin penales · balón parado = posesión que nace de córner o tiro libre (marco) · Datos: StatsBomb")
    return fig


def fig_assists(assist_sum: pd.DataFrame, scope: pd.DataFrame, title: str, order: list[str]):
    """% del xG (sin penales) según la jugada previa al tiro: un punto por técnico, rótulo directo en Jardine."""
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    piv = assist_sum.pivot(index="assist", columns="coach", values="pct_xg").reindex(order[::-1])
    y = np.arange(len(piv))
    ax.hlines(y, piv.min(axis=1), piv.max(axis=1), color=eda.GRID, lw=2, zorder=1)
    for c in COACHES:
        ax.scatter(piv[c], y, s=48 if c == PROTAGONIST else 34, color=COACH_COLOR[c], edgecolor=eda.SURFACE,
                   lw=1.5, zorder=3, label=c)
    for yi, v in zip(y, piv[PROTAGONIST]):
        ax.text(v, yi + 0.3, f"{v:.0f} %", fontsize=7, color=eda.INK, ha="center")
    ax.set_yticks(y, piv.index)
    ax.set_xlabel("% del xG del técnico (sin penales)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="center right", bbox_to_anchor=(1.0, 0.3), ncol=1)
    ax.set_title(title, loc="left")
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    _footer(fig, sample_note(scope).split(" · el América")[0])
    return fig


# ------------------------------------------------------------------ §3.2d red de pases
def fig_pass_network(nodes: pd.DataFrame, edges: pd.DataFrame, xi: pd.DataFrame, title: str, note: str,
                     min_edge: float = 3.0, coach: str = PROTAGONIST):
    fig, ax = plt.subplots(figsize=(8.6, 6.4))
    fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.06)
    draw_pitch(ax)
    pos = nodes.set_index("player_id")
    e = edges[edges.pases_por_partido >= min_edge]
    wmax = e.pases_por_partido.max()
    for r in e.itertuples():
        a, b = pos.loc[r.a], pos.loc[r.b]
        ax.plot([a.x_media, b.x_media], [a.y_media, b.y_media], color=eda.INK_2,
                alpha=0.25 + 0.5 * r.pases_por_partido / wmax, lw=0.6 + 5 * r.pases_por_partido / wmax, zorder=4,
                solid_capstyle="round")
    smax = nodes.pases_por_partido.max()
    ax.scatter(nodes.x_media, nodes.y_media, s=120 + 700 * nodes.pases_por_partido / smax, color=COACH_COLOR[coach],
               edgecolor=eda.SURFACE, lw=2, zorder=5)
    placed = []
    for r in nodes.sort_values("pases_por_partido", ascending=False).itertuples():
        near = any(np.hypot(r.x_media - x, r.y_media - y) < 9 for x, y in placed)
        dy, va = (-5.2, "bottom") if near else (5.2, "top")  # si otro nodo está cerca, rótulo arriba
        placed.append((r.x_media, r.y_media))
        ax.text(r.x_media, r.y_media + dy, r.nombre, fontsize=7, color=eda.INK, ha="center", va=va, zorder=6,
                bbox=dict(boxstyle="round,pad=0.15", fc=eda.SURFACE, ec="none", alpha=0.8))
    fig.suptitle(title, x=0.01, y=0.975, ha="left", va="top", fontsize=11, fontweight="bold")
    fig.text(0.01, 0.905, f"Sistema {'-'.join(xi.formation.iat[0])}, el más usado ({xi.partidos_sistema.iat[0]} partidos), "
             f"hasta el primer cambio · tamaño = pases por partido · líneas = parejas con ≥ {min_edge:.0f} pases por "
             "partido juntos", fontsize=7, color=eda.INK_2)
    _footer(fig, note)
    return fig


# ------------------------------------------------------------------ §3.3 sin balón
def fig_recoveries(grid: pd.DataFrame, summary: pd.DataFrame, scope: pd.DataFrame, title: str):
    fig, axes = _panels(3)
    vmax = grid.por_partido.max()
    sm = summary.set_index("coach")
    for ax, c in zip(axes, COACHES):
        draw_pitch(ax)
        norm = zone_heat(ax, grid[grid.coach == c], "por_partido", vmax, fmt="{:.1f}", min_label=1)
        h = sm.loc[c, "altura_media_x"]
        ax.plot([h, h], [0, 80], color=eda.INK, lw=1.2, zorder=5)
        ax.text(h + 1, 78, f"altura media {h:.0f} yd", fontsize=6.5, color=eda.INK, zorder=6, va="bottom",
                bbox=dict(boxstyle="round,pad=0.15", fc=eda.SURFACE, ec="none", alpha=0.85))
        _coach_title(ax, c, f"{sm.loc[c, 'por_partido']:.0f} por partido · {sm.loc[c, 'pct_campo_rival']:.0f} % en campo rival")
    _colorbar(fig, norm, "recuperaciones por partido en cada zona")
    _suptitle(fig, title)
    _footer(fig, sample_note(scope) + " · recuperación = posesión propia que nace de un robo, intercepción o bloqueo (marco)")
    return fig


def fig_press_league(bench: pd.DataFrame, metrics: dict[str, tuple[str, str, float]], title: str, note: str):
    """Tira por métrica: cada punto gris = un técnico de la liga (≥ 15 partidos en la ventana); en color, los del
    América. Eje = diferencia con la media de la liga en el mismo torneo (0 = liga)."""
    fig, axes = plt.subplots(len(metrics), 1, figsize=(8.2, 1.25 * len(metrics) + 1.0))
    rng = np.random.default_rng(0)
    for ax, (col, (lab, better, scale)) in zip(axes, metrics.items()):
        v = bench[col] * scale
        lg = bench.coach.isna()
        ax.scatter(v[lg], rng.uniform(-0.25, 0.25, lg.sum()), s=16, color=LEAGUE, alpha=0.45, lw=0)
        ax.axvline(0, color=eda.INK_2, lw=0.8)
        for c in COACHES:
            x = v[bench.coach == c].iat[0]
            ax.scatter([x], [0], s=70, color=COACH_COLOR[c], edgecolor=eda.SURFACE, lw=1.5, zorder=3)
            ax.annotate(c, (x, 0), xytext=(0, 9 if c != "Ortiz" else -13), textcoords="offset points", ha="center",
                        fontsize=7, color=eda.INK, fontweight="bold" if c == PROTAGONIST else "normal")
        ax.set_yticks([])
        ax.set_ylim(-0.6, 0.6)
        ax.grid(axis="y", visible=False)
        ax.spines["left"].set_visible(False)
        ax.set_title(f"{lab}  ·  {better}", loc="left", fontsize=8, fontweight="normal", color=eda.INK)
    axes[-1].set_xlabel("diferencia con la media de la liga en el mismo torneo (0 = liga)")
    fig.suptitle(title, x=0.01, ha="left", fontsize=11, fontweight="bold")
    fig.tight_layout(rect=(0, 0.04, 1, 0.97))
    _footer(fig, note)
    return fig


def fig_transitions(grid: pd.DataFrame, summary: pd.DataFrame, scope: pd.DataFrame, title: str, coach: str = PROTAGONIST):
    """Dónde nacen las transiciones de Jardine: a favor (donde recupera) y en contra (donde pierde)."""
    fig, axes = _panels(2, w=10.5, h=4.9, top=0.78, bottom=0.19)
    g = grid[grid.coach == coach]
    vmax = g.por_partido.max()
    sm = summary[summary.coach == coach].set_index("lado")
    labels = {"A favor": "A favor: dónde recupera el América", "En contra": "En contra: dónde pierde el balón el América"}
    for ax, side in zip(axes, ["A favor", "En contra"]):
        draw_pitch(ax)
        norm = zone_heat(ax, g[g.lado == side], "por_partido", vmax, fmt="{:.1f}", min_label=0.8)
        r = sm.loc[side]
        ax.text(-2, -14, labels[side], fontsize=9, fontweight="bold", color=eda.INK)
        ax.text(-2, -4, f"{r.por_partido:.1f} por partido · llegan en {r.segundos_mediana:.0f} s (mediana)\n"
                f"{r.pct_tiro:.0f} % termina en tiro · {r.xg_por_partido:.2f} xG por partido", fontsize=7,
                color=eda.INK_2)
    _colorbar(fig, norm, "transiciones por partido que nacen en cada zona", rect=(0.33, 0.08, 0.34, 0.022))
    _suptitle(fig, title)
    _footer(fig, f"Ventana oficial Ap 2021 – Cl 2025 · {coach}, {int((scope.coach == coach).sum())} partidos · "
            "transición = robo que llega al último tercio o al tiro en ≤ 15 s (marco) · coordenadas del América")
    return fig


# ------------------------------------------------------------------ §3.4 forma defensiva (360)
def fig_block_shape(by_phase: pd.DataFrame, by_situation: pd.DataFrame, scope: pd.DataFrame, title: str):
    """El bloque defensivo a lo largo de la cancha (yd desde la portería del América; ataca a la derecha). Una fila por
    técnico dentro de cada situación: la barra va de la última línea (borde izquierdo) al jugador más adelantado de
    los 8 del bloque; la marca blanca es la segunda línea y el punto de tinta, la mediana de dónde está el balón."""
    groups = [(p, by_phase[by_phase.fase == p].set_index("coach"), f"{p}: balón {lab}") for p, lab in
              zip(["Bloque alto", "Bloque medio", "Bloque bajo"], ["en campo rival", "entre 40 y 60 yd", "en su tercio"])]
    groups.append(("Tras pérdida", by_situation[by_situation.situacion == "Tras pérdida"].set_index("coach"),
                   "Tras pérdida: primeros 5 s de la posesión rival"))
    fig, ax = plt.subplots(figsize=(9.6, 6.6))
    fig.subplots_adjust(left=0.1, right=0.99, top=0.88, bottom=0.12)
    for x in (0, 18, 40, 60, 80, 102, 120):
        ax.axvline(x, color=LINE, lw=0.8 if x in (0, 60, 120) else 0.5, ls="-" if x in (0, 60, 120) else ":", zorder=0)
    y, ticks, labels = 0, [], []
    for name, d, header in groups:
        ax.text(-1, y - 0.15, header, fontsize=8, fontweight="bold", color=eda.INK, va="bottom", ha="left")
        y += 1
        for c in COACHES:
            r = d.loc[c]
            ax.barh(y, r.largo_bloque, left=r.altura_linea, height=0.62, color=COACH_COLOR[c], alpha=0.9,
                    edgecolor=eda.SURFACE, lw=2, zorder=2)
            ax.plot([r.altura_linea + r.distancia_lineas] * 2, [y - 0.31, y + 0.31], color=eda.SURFACE, lw=1.6, zorder=3)
            ax.scatter([r.ball_x], [y], s=34, color=eda.INK, edgecolor=eda.SURFACE, lw=1, zorder=4)
            ax.text(r.altura_linea + r.largo_bloque + 1.2, y, f"línea {r.altura_linea:.0f} yd · bloque {r.largo_bloque:.0f} yd",
                    fontsize=6.8, color=eda.INK_2, va="center", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.1", fc=eda.SURFACE, ec="none", alpha=0.8))
            ticks.append(y)
            labels.append(c)
            y += 1
        y += 0.6
    ax.set_yticks(ticks, labels, fontsize=7.5)
    for t, c in zip(ax.get_yticklabels(), labels):
        t.set_fontweight("bold" if c == PROTAGONIST else "normal")
        t.set_color(eda.INK)
    ax.set_ylim(y - 0.4, -0.9)
    ax.set_xlim(-2, 122)
    ax.set_xticks([0, 18, 40, 60, 80, 102, 120], ["su portería", "área", "40", "medio campo", "80", "área rival", "120"])
    ax.grid(False)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("yardas desde la portería del América → ataque")
    handles = [Rectangle((0, 0), 1, 1, color=LEAGUE, alpha=0.9),
               plt.Line2D([], [], color=eda.INK_2, lw=1.6), plt.scatter([], [], s=34, color=eda.INK)]
    ax.legend(handles, ["bloque: de la última línea al más adelantado de los 8", "segunda línea (marca blanca)",
                        "balón (mediana)"], loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7)
    _suptitle(fig, title)
    sit = by_situation.groupby("coach")[["frames_utiles", "pases_rivales"]].sum()
    util, tot = sit.frames_utiles, sit.pases_rivales
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · 360 en pases rivales de juego abierto (sin balón parado)\n"
            "Frames útiles (≥ 8 jugadores de campo visibles y la toma ve ≥ 5 yd detrás del último): "
            + ", ".join(f"{c} {util[c] / tot[c]:.0%}" for c in COACHES) + " · solo cuenta lo que se ve en la toma")
    return fig

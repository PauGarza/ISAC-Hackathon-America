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
    return f"Ap 2021 – Cl 2025 · partidos: {parts} · Datos: StatsBomb · el América ataca hacia la derecha"


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
    _footer(fig, f"Ap 2021 – Cl 2025 · {coach}, {int((scope.coach == coach).sum())} partidos · "
            "sin penales · balón parado = posesión que abre el saque propio de córner o tiro libre (marco) · Datos: StatsBomb")
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
    _footer(fig, f"Ap 2021 – Cl 2025 · {coach}, {int((scope.coach == coach).sum())} partidos · "
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


# ------------------------------------------------------------------ §3.8 balón parado
ZONE_RECTS = {"Área chica": [(114, 30, 6, 20)], "Zona de penal": [(102, 30, 12, 20)],
              "Área (costados)": [(102, 18, 18, 12), (102, 50, 18, 12)]}


def _sp_shots(ax, d: pd.DataFrame, color: str):
    miss, goal = d[~d.goal], d[d.goal]
    ax.scatter(miss.x, miss.y, s=miss.xg * 500 + 6, color=color, alpha=0.4, lw=0, zorder=5)
    ax.scatter(goal.x, goal.y, s=goal.xg * 500 + 6, color=eda.INK, alpha=0.85, edgecolor=eda.SURFACE, lw=0.8, zorder=6)


def _panel_title(ax, title: str, text: str, view: str = "box"):
    x0, _, _, yt = VIEWS[view]
    ax.text(x0 + 1, yt - 8.5, title, fontsize=9, fontweight="bold", color=eda.INK, va="center")
    ax.text(x0 + 1, yt - 3.5, text, fontsize=6.8, color=eda.INK_2, va="center")


def fig_set_pieces(deliv: pd.DataFrame, summary: pd.DataFrame, shots: pd.DataFrame, scope: pd.DataFrame, title: str,
                   coach: str = PROTAGONIST):
    """Balón parado de un técnico en tres vistas del área (la portería atacada, a la derecha):
    (1) dónde cae el envío de sus córners (% por zona del marco); (2) remates a favor y (3) remates en contra en
    córners, tiros libres y saques de banda del último tercio (tamaño = xG; relleno de tinta = gol)."""
    fig, axes = _panels(3, w=11.5, h=4.9, top=0.8, bottom=0.17)
    sm = summary.set_index(["coach", "lado", "kind"])
    z = deliv[(deliv.coach == coach) & (deliv.lado == "A favor") & (deliv.kind == "Córner")
              & (deliv.dimension == "Zona de entrega")].set_index("valor").share
    norm = Normalize(0, max(z.max(), 0.01))
    ax = axes[0]
    draw_pitch(ax, view="box", arrow=False)
    for zone, rects in ZONE_RECTS.items():
        v = z.get(zone, 0.0)
        c = eda.SEQ(norm(v))
        for i, (x, y, w, h) in enumerate(rects):
            ax.add_patch(Rectangle((x, y), w, h, facecolor=c, edgecolor=eda.SURFACE, lw=2, zorder=1))
            if i == 0:
                ax.text(x + w / 2, y + h / 2, f"{v:.0%}", ha="center", va="center", fontsize=8, color=_text_color(c),
                        zorder=4)
    ax.text(79, 66, f"en corto: {z.get('Corto', 0):.0%} · fuera del área: {z.get('Fuera del área', 0):.0%}", fontsize=7,
            color=eda.INK, va="center")
    c = sm.loc[(coach, "A favor", "Córner")]
    _panel_title(ax, "Córners a favor: dónde cae el envío", f"{c.por_partido:.1f} por partido · {c.pct_tiro:.0f} % termina "
                 f"en tiro · {c.xg_por_jugada:.3f} xG por córner")
    for ax, side, color in [(axes[1], "A favor", COACH_COLOR[coach]), (axes[2], "En contra", LEAGUE)]:
        draw_pitch(ax, view="box", arrow=False)
        _sp_shots(ax, shots[(shots.coach == coach) & (shots.lado == side) & (shots.x >= 77)], color)
        t = sm.loc[(coach, side, "Total")]
        _panel_title(ax, f"Remates {side.lower()}", f"{t.por_partido:.1f} jugadas y {t.xg_por_partido:.2f} xG por partido · "
                     f"{t.goles:.0f} goles")
    handles = [plt.scatter([], [], s=x * 500 + 6, color=eda.MUTED, alpha=0.5, lw=0) for x in (0.05, 0.2, 0.5)]
    handles.append(plt.scatter([], [], s=0.2 * 500 + 6, color=eda.INK, edgecolor=eda.SURFACE))
    fig.legend(handles, ["xG 0.05", "xG 0.20", "xG 0.50", "gol"], loc="lower center", ncol=4,
               bbox_to_anchor=(0.66, 0.05), fontsize=7)
    _suptitle(fig, title)
    _footer(fig, f"Ap 2021 – Cl 2025 · {coach}, {int((scope.coach == coach).sum())} partidos · córners, tiros "
            "libres y saques de banda desde el último tercio (toda la jugada, sin penales) · la portería atacada, a la derecha "
            "(en contra: la del América) · Datos: StatsBomb")
    return fig


def fig_corner_defense(grid: pd.DataFrame, cd_sum: pd.DataFrame, marking: pd.DataFrame, scope: pd.DataFrame, title: str):
    """Córners en contra con 360 en el momento del saque: dónde se paran los defensores del América en su área
    (promedio por córner en cada celda), un panel por técnico; el saque, siempre desde la esquina de arriba."""
    fig, axes = _panels(3, w=11.5, h=5.2, top=0.78, bottom=0.24)
    vmax = grid.por_corner.max()
    cs, mk = cd_sum.set_index("coach"), marking.set_index("coach")
    for ax, c in zip(axes, COACHES):
        draw_pitch(ax, view="box", arrow=False)
        norm = zone_heat(ax, grid[grid.coach == c], "por_corner", vmax, fmt="{:.1f}", min_label=np.inf)
        ax.annotate("saque", xy=(120, 8.4), xytext=(113, 11), fontsize=6.5, color=eda.INK_2, ha="right", va="center",
                    arrowprops=dict(arrowstyle="->", color=eda.INK_2, lw=0.7))
        r, m = cs.loc[c], mk.loc[c]
        x0, _, _, yt = VIEWS["box"]
        ax.text(x0 + 1, yt - 12, "●", color=COACH_COLOR[c], fontsize=10, va="center", ha="left")
        ax.text(x0 + 4, yt - 12, c, fontsize=9, fontweight="bold", color=eda.INK, va="center", ha="left")
        ax.text(x0 + 1, yt - 4.5, f"{r.defensores_area_media:.1f} en el área · {r.defensores_chica:.1f} en el área chica\n"
                f"{m.pct_pegados:.0f} % pegados a un rival (azar: {m.pct_pegados_azar:.0f} %)", fontsize=7,
                color=eda.INK_2, va="center", ha="left")
    _colorbar(fig, norm, "defensores del América por córner en cada zona", rect=(0.33, 0.12, 0.34, 0.022))
    _suptitle(fig, title)
    util = ", ".join(f"{c} {int(cs.loc[c, 'utiles'])} de {int(cs.loc[c, 'corners'])}" for c in COACHES)
    _footer(fig, "Ap 2021 – Cl 2025 · córners rivales no jugados en corto, con 360 que ve ≥ 90 % del área y toda el "
            f"área chica: {util}\npegado = a ≤ 2 yd de un atacante; azar = mismo cálculo con los atacantes de otro córner · "
            "solo cuenta lo que se ve en la toma · Datos: StatsBomb")
    return fig


# ------------------------------------------------------------------ §3.7 jugadores
def _dot_rows(ax, piv: pd.DataFrame, fmt: str = "{:.0f}", label_coach: str = PROTAGONIST, offset: float = 0.3):
    """Un renglón por categoría (índice de piv) y un punto por técnico (columnas); rango en gris y rótulo en el técnico."""
    y = np.arange(len(piv))
    ax.hlines(y, piv.min(axis=1), piv.max(axis=1), color=eda.GRID, lw=2, zorder=1)
    for c in COACHES:
        if c in piv:
            ax.scatter(piv[c], y, s=48 if c == label_coach else 34, color=COACH_COLOR[c], edgecolor=eda.SURFACE, lw=1.5,
                       zorder=3, label=c)
    for yi, v in zip(y, piv[label_coach]):
        ax.text(v, yi + offset, fmt.format(v), fontsize=7, color=eda.INK, ha="center",
                va="bottom" if offset < 0 else "top")  # eje y invertido: offset < 0 = encima del punto
    ax.set_yticks(y, piv.index)
    ax.grid(axis="y", visible=False)
    ax.set_ylim(len(piv) - 0.4, -0.6)
    return y


def fig_player_usage(usage: pd.DataFrame, rot: pd.DataFrame, scope: pd.DataFrame, title: str, n: int = 18,
                     coach: str = PROTAGONIST):
    """Izquierda: % de los minutos posibles de los `n` jugadores más usados por el técnico (línea de 50 % = núcleo de
    confianza). Derecha: rotación frente a sus antecesores (titulares que cambian de un partido al siguiente y
    jugadores con ≥ 50 % de los minutos)."""
    u = usage[usage.coach == coach].nlargest(n, "minutos").iloc[::-1]
    fig = plt.figure(figsize=(10.5, 6.2))
    gs = fig.add_gridspec(2, 2, width_ratios=[1.55, 1], hspace=0.7, wspace=0.45, left=0.2, right=0.97, top=0.86,
                          bottom=0.11)
    ax = fig.add_subplot(gs[:, 0])
    y = np.arange(len(u))
    ax.barh(y, u.pct_minutos, color=COACH_COLOR[coach], height=0.72, edgecolor=eda.SURFACE, lw=1)
    for yi, v, t in zip(y, u.pct_minutos, u.titularidades):
        ax.text(v + 1, yi, f"{v:.0f} % · {t} de titular", fontsize=6.5, color=eda.INK_2, va="center")
    ax.set_yticks(y, [f"{j}  ·  {str(l).lower()}" for j, l in zip(u.jugador, u.linea)], fontsize=7)
    ax.axvline(50, color=eda.INK_2, lw=0.8, ls="--")
    ax.text(50.5, len(u) - 0.3, "50 %: núcleo de confianza", fontsize=6.5, color=eda.INK_2, va="bottom")
    ax.set_xlim(0, 118)
    ax.set_xticks([0, 25, 50, 75, 100])
    ax.set_xlabel("% de los minutos posibles en sus partidos")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"Los {n} jugadores más usados por {coach}", loc="left", fontsize=9)
    r = rot.set_index("coach")
    for k, (col, lab, fmt) in enumerate([("cambios_xi_media", "Titulares que cambian de un partido al siguiente", "{:.1f}"),
                                         ("nucleo_confianza", "Jugadores con ≥ 50 % de los minutos", "{:.0f}")]):
        a2 = fig.add_subplot(gs[k, 1])
        for i, c in enumerate(COACHES):
            a2.scatter([r.loc[c, col]], [i], s=60, color=COACH_COLOR[c], edgecolor=eda.SURFACE, lw=1.5, zorder=3)
            a2.text(r.loc[c, col] + r[col].max() * 0.05, i, fmt.format(r.loc[c, col]), fontsize=7, color=eda.INK,
                    va="center")
        a2.set_yticks(range(len(COACHES)), COACHES, fontsize=7.5)
        a2.set_ylim(len(COACHES) - 0.5, -0.5)
        a2.set_xlim(0, r[col].max() * 1.3)
        a2.grid(axis="y", visible=False)
        a2.set_title(lab, loc="left", fontsize=8)
    _suptitle(fig, title)
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · minutos posibles = minutos de juego de sus partidos · "
            "titular = en el XI inicial")
    return fig


def fig_obv_share(usage: pd.DataFrame, dist: pd.DataFrame, scope: pd.DataFrame, title: str, n: int = 12,
                  coach: str = PROTAGONIST):
    """Izquierda: % del OBV positivo del equipo que genera cada jugador (los `n` primeros del técnico). Derecha: % del
    OBV positivo de toda la era por línea, un punto por técnico."""
    u = usage[usage.coach == coach].nlargest(n, "pct_obv_pos").iloc[::-1]
    fig, (ax, a2) = plt.subplots(1, 2, figsize=(10.5, 4.9), gridspec_kw={"width_ratios": [1.3, 1]})
    fig.subplots_adjust(left=0.2, right=0.97, top=0.82, bottom=0.16, wspace=0.5)
    y = np.arange(len(u))
    ax.barh(y, u.pct_obv_pos, color=COACH_COLOR[coach], height=0.72, edgecolor=eda.SURFACE, lw=1)
    for yi, v, p90 in zip(y, u.pct_obv_pos, u.obv_pos_p90):
        ax.text(v + 0.2, yi, f"{v:.1f} % · {p90:.2f} por 90'", fontsize=6.5, color=eda.INK_2, va="center")
    ax.set_yticks(y, [f"{j}  ·  {str(l).lower()}" for j, l in zip(u.jugador, u.linea)], fontsize=7)
    ax.set_xlim(0, u.pct_obv_pos.max() * 1.6)
    ax.set_xlabel("% del OBV positivo del equipo")
    ax.grid(axis="y", visible=False)
    ax.set_title(f"¿Quién genera el valor con {coach}?", loc="left", fontsize=9)
    order = ["Defensa", "Carrilero", "Medio defensivo", "Medio", "Banda", "Medio ofensivo", "Delantero", "Portero"]
    lines = [l for l in order if f"pct_era_{l}" in dist]
    piv = dist.set_index("coach")[[f"pct_era_{l}" for l in lines]].T
    piv.index = lines
    _dot_rows(a2, piv, "{:.0f} %", offset=-0.18)
    a2.set_xlabel("% del OBV positivo de toda la era")
    a2.set_title("¿Qué línea lo genera?", loc="left", fontsize=9)
    a2.legend(loc="lower right", fontsize=7)
    _suptitle(fig, title)
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · OBV positivo = valor que suma cada jugador en cada partido "
            "(OBV de StatsBomb, recortado en 0) · línea = la más habitual del jugador")
    return fig


def fig_roles(roles_tab: pd.DataFrame, names: pd.DataFrame, scope: pd.DataFrame, title: str, coach: str = PROTAGONIST):
    """Roles U3 con nombre de fútbol: % de los partidos (≥ 30') de los jugadores del técnico en cada rol y los jugadores
    que más veces lo ocupan (partidos en el rol y % de sus partidos)."""
    t = roles_tab.reset_index(drop=True)
    what = names.drop_duplicates("rol").set_index("rol").que_hace
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    fig.subplots_adjust(left=0.02, right=0.99, top=0.82, bottom=0.1)
    y = np.arange(len(t)) * 1.4
    ax.barh(y, t.pct, color=COACH_COLOR[coach], height=0.55, left=0, edgecolor=eda.SURFACE, lw=1)
    for yi, r in zip(y, t.itertuples()):
        ax.text(-1.5, yi - 0.18, r.rol, fontsize=8.5, fontweight="bold", color=eda.INK, ha="right", va="center")
        ax.text(-1.5, yi + 0.32, what.get(r.rol, ""), fontsize=6.5, color=eda.INK_2, ha="right", va="center")
        ax.text(r.pct + 0.8, yi - 0.18, f"{r.pct:.0f} %", fontsize=7.5, color=eda.INK, va="center")
        ax.text(r.pct + 0.8, yi + 0.32, r.jugadores.replace("; ", " · "), fontsize=6.5, color=eda.INK_2, va="center")
    ax.set_xlim(-62, 105)
    ax.set_ylim(y.max() + 0.9, -0.9)
    ax.axis("off")
    _suptitle(fig, title)
    fig.text(0.01, 0.885, "Barra = % de los partidos de sus jugadores (≥ 30', sin porteros) en cada rol · a la derecha, quién lo "
             "ocupa más: partidos en el rol y % de sus partidos", fontsize=7, color=eda.INK_2)
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · roles = grupos de jugadores con el mismo perfil de acciones "
            "por 90'; cada rol se nombra por su rasgo más marcado")
    return fig


def fig_substitutions(subs: pd.DataFrame, summ: dict, scope: pd.DataFrame, title: str, coach: str = PROTAGONIST):
    """Tres paneles: (1) % acumulado de partidos con el primer cambio hecho, por minuto (un escalón por técnico);
    (2) cambios por cada 90' jugados en cada estado del marcador (segundo tiempo); (3) del técnico, % de cambios que
    meten a un jugador de una línea más ofensiva o más defensiva (línea habitual), según el marcador."""
    fig, axes = plt.subplots(1, 3, figsize=(11.5, 4.3), gridspec_kw={"width_ratios": [1.25, 1, 1.1]})
    fig.subplots_adjust(left=0.06, right=0.98, top=0.8, bottom=0.2, wspace=0.45)
    ax = axes[0]
    first = subs.groupby("match_id").agg(coach=("coach", "first"), minute=("minute", "min"))
    grid = np.arange(0, 96)
    for c in COACHES:
        m = first[first.coach == c].minute.values
        ax.step(grid, [(m <= x).mean() * 100 for x in grid], where="post", color=COACH_COLOR[c], lw=2, label=c)
    ax.axvline(45, color=eda.INK_2, lw=0.8, ls=":")
    g = summ["general"].set_index("coach")
    ax.annotate(f"{coach}, al descanso: {g.loc[coach, 'pct_primer_cambio_descanso']:.0f} %",
                (45, g.loc[coach, "pct_primer_cambio_descanso"]), xytext=(6, 10), textcoords="offset points", fontsize=7,
                color=eda.INK, va="center", arrowprops=dict(arrowstyle="-", color=eda.INK_2, lw=0.6))
    ax.set_xlim(30, 95)
    ax.set_ylim(0, 102)
    ax.set_xlabel("minuto")
    ax.set_ylabel("% de partidos con el primer cambio hecho")
    ax.legend(loc="lower right", fontsize=7)
    ax.set_title("¿Cuándo hace el primer cambio?", loc="left", fontsize=9)
    st = summ["estado"]
    piv = st.pivot(index="estado", columns="coach", values="cambios_por_90").reindex(["Perdiendo", "Empatando", "Ganando"])
    _dot_rows(axes[1], piv, "{:.1f}", offset=-0.15)
    axes[1].set_xlabel("cambios por cada 90' con ese marcador")
    axes[1].set_title("¿Con qué marcador cambia más?", loc="left", fontsize=9)
    ax = axes[2]
    s = st[st.coach == coach].set_index("estado").reindex(["Perdiendo", "Empatando", "Ganando"])
    yy = np.arange(len(s))
    lo, hi = eda.DIV(0.12), eda.DIV(0.88)
    ax.barh(yy, -s.pct_mas_defensivo, color=lo, height=0.6, edgecolor=eda.SURFACE, lw=1)
    ax.barh(yy, s.pct_mas_ofensivo, color=hi, height=0.6, edgecolor=eda.SURFACE, lw=1)
    for yi, d, o in zip(yy, s.pct_mas_defensivo, s.pct_mas_ofensivo):
        ax.text(-d - 1.5, yi, f"{d:.0f} %", fontsize=7, color=eda.INK, ha="right", va="center")
        ax.text(o + 1.5, yi, f"{o:.0f} %", fontsize=7, color=eda.INK, ha="left", va="center")
    ax.axvline(0, color=eda.INK_2, lw=0.8)
    lim = max(s.pct_mas_defensivo.max(), s.pct_mas_ofensivo.max()) * 1.5
    ax.set_xlim(-lim, lim)
    ax.set_yticks(yy, s.index)
    ax.set_ylim(len(s) - 0.4, -1.0)
    ax.set_xticks([])
    ax.text(-lim * 0.97, -0.8, "← entra alguien más defensivo", fontsize=6.5, color=eda.INK_2, va="center")
    ax.text(lim * 0.97, -0.8, "más ofensivo →", fontsize=6.5, color=eda.INK_2, va="center", ha="right")
    ax.grid(False)
    ax.set_title(f"¿Qué perfil mete {coach}?", loc="left", fontsize=9)
    _suptitle(fig, title)
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · paneles 2 y 3: cambios tácticos (sin lesiones) desde el "
            "segundo tiempo · perfil = línea habitual del que entra frente a la del que sale")
    return fig


# ------------------------------------------------------------------ §3.5 contexto
def fig_game_state(effects: pd.DataFrame, scope: pd.DataFrame, title: str, labels: dict[str, str],
                   states=("Pierde por 2+", "Pierde por 1", "Empate", "Gana por 1", "Gana por 2+")):
    """Un panel por variable: efecto del marcador frente al empate (mismo partido y mismo tramo de 15'), punto e IC 90 %
    por técnico. effects = concat de story.game_state_effect (una variable por bloque)."""
    vars_ = list(dict.fromkeys(effects.variable))
    fig, axes = plt.subplots(1, len(vars_), figsize=(11.5, 4.2), sharey=True)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.74, bottom=0.2, wspace=0.12)
    y = np.arange(len(states))
    for ax, v in zip(np.atleast_1d(axes), vars_):
        e = effects[(effects.variable == v) & effects.coach.isin(COACHES)]
        for k, c in enumerate(COACHES):
            d = e[e.coach == c].set_index("estado").reindex(states)
            yy = y + (k - 1) * 0.22
            ax.hlines(yy, d.lo, d.hi, color=COACH_COLOR[c], lw=1.6, alpha=0.8)
            ax.scatter(d.efecto, yy, s=46 if c == PROTAGONIST else 30, color=COACH_COLOR[c], edgecolor=eda.SURFACE,
                       lw=1.2, zorder=3, label=c)
            if c == PROTAGONIST:
                for yi, val, hi in zip(yy, d.efecto, d.hi):
                    if pd.notna(val) and round(val) != 0:
                        ax.text(hi + 0.8, yi, f"{val:+.0f}", fontsize=7, color=eda.INK, ha="left", va="center")
        ax.axvline(0, color=eda.INK_2, lw=0.8)
        ax.set_yticks(y, states)
        ax.set_ylim(len(states) - 0.5, -0.6)
        ax.grid(axis="y", visible=False)
        ax.set_title(labels.get(v, v), loc="left", fontsize=8.5)
        ax.set_xlabel("diferencia con el empate")
    np.atleast_1d(axes)[0].legend(loc="lower left", bbox_to_anchor=(0, 1.08), ncol=3, fontsize=7, frameon=False)
    _suptitle(fig, title)
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · tramos de 15' ponderados por minutos de juego, mismo partido "
            "(efecto fijo) · línea = IC 90 % con errores agrupados por partido · describe, no predice")
    return fig


def fig_context(cm: pd.DataFrame, scope: pd.DataFrame, title: str, labels: dict[str, str]):
    """Un panel por métrica: media por partido según localía y fuerza del rival (terciles de la liga), un punto por
    técnico. cm = story.context_metrics."""
    rows = [("Localía", "Local"), ("Localía", "Visita"), ("Rival", "Débil"), ("Rival", "Medio"), ("Rival", "Fuerte")]
    names = ["Local", "Visita", "Rival débil", "Rival medio", "Rival fuerte"]
    fig, axes = plt.subplots(1, len(labels), figsize=(11.5, 3.9), sharey=True)
    fig.subplots_adjust(left=0.09, right=0.98, top=0.78, bottom=0.2, wspace=0.15)
    c_ = cm.set_index(["dimension", "contexto", "coach"])
    for ax, (col, lab) in zip(np.atleast_1d(axes), labels.items()):
        piv = pd.DataFrame({c: [c_.loc[(d, k, c), col] for d, k in rows] for c in COACHES}, index=names)
        _dot_rows(ax, piv, "{:.0f}" if piv.abs().max().max() > 5 else "{:.2f}", offset=-0.12)
        ax.axhline(1.5, color=eda.GRID, lw=0.8)
        ax.set_title(lab, loc="left", fontsize=8.5)
    np.atleast_1d(axes)[-1].legend(loc="lower right", fontsize=7)
    _suptitle(fig, title)
    pts = c_.xs("Jardine", level="coach").puntos_por_partido
    n = c_.xs("Jardine", level="coach").partidos
    _footer(fig, sample_note(scope).split(" · el América")[0] + " · rival = puntos por partido en sus 17 previos, terciles de la "
            "liga · el PPDA de la liga sube con los años: compárese dentro de cada técnico, no entre técnicos\n"
            "Jardine, puntos por partido: " + " · ".join(f"{k} {pts[(d, k)]:.2f} ({n[(d, k)]})" for d, k in rows))
    return fig


# ------------------------------------------------------------------ §3.6 evolución
def fig_adn_evolution(pt: pd.DataFrame, axes_: list[str], title: str, changes: pd.DataFrame | None = None):
    """Mapa de calor: percentil de liga de cada eje del ADN (filas) por técnico × torneo (columnas, cronológico).
    Validación y prueba con borde punteado y su etiqueta. pt = story.adn_by_coach_torneo (sin interinos de < 5 partidos)."""
    d = pt[pt.partidos >= 5].reset_index(drop=True)
    m = d[axes_].T.values.astype(float)
    fig, ax = plt.subplots(figsize=(11.5, 4.9))
    fig.subplots_adjust(left=0.15, right=0.99, top=0.74, bottom=0.12)
    ax.imshow(m, cmap=eda.DIV.reversed(), vmin=0, vmax=100, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m[i, j]:.0f}", ha="center", va="center", fontsize=7.5,
                    color=eda.SURFACE if abs(m[i, j] - 50) > 32 else eda.INK)
    ax.set_yticks(range(len(axes_)), axes_, fontsize=8)
    tor = [t.replace("Apertura ", "Ap ").replace("Clausura ", "Cl ") for t in d.torneo]
    ax.set_xticks(range(len(d)), [f"{t}\n{n} p." for t, n in zip(tor, d.partidos)], fontsize=7)
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    # banda del técnico encima
    for c, g in d.groupby("coach", sort=False):
        j0, j1 = g.index.min(), g.index.max()
        ax.add_patch(Rectangle((j0 - 0.45, -1.35), j1 - j0 + 0.9, 0.55, color=COACH_COLOR[c], clip_on=False))
        ax.text((j0 + j1) / 2, -1.07, c, ha="center", va="center", fontsize=8, color=eda.SURFACE, fontweight="bold")
    for j, mu in enumerate(d.muestra):
        if mu != "ventana":
            ax.add_patch(Rectangle((j - 0.5, -0.5), 1, len(axes_), fill=False, ls=":", lw=1.2, ec=eda.INK_2))
            ax.text(j, len(axes_) - 0.3, "reciente", ha="center", va="top", fontsize=6.5, color=eda.INK_2, style="italic")
    ax.set_ylim(len(axes_) - 0.5 + 0.5, -1.5)
    _suptitle(fig, title)
    if changes is not None:
        lines = []
        for rel, g in changes[changes.titular].groupby("relevo", sort=False):
            lines.append(f"{rel}: " + ", ".join(f"{r.eje.lower()} {r.cambio:+.0f}" for r in g.itertuples()))
        fig.text(0.01, 0.885, "Lo que más cambia en cada relevo (escala de 0 a 100, toda la etapa): " + "  ·  ".join(lines),
                 fontsize=7, color=eda.INK_2)
    _footer(fig, "De 0 a 100 frente a los técnicos de la Liga MX (50 = promedio) · cada rasgo comparado con la "
            "liga del mismo torneo y ajustado por rival y localía · azul = alto, rojo = bajo · un torneo ≈ 20 partidos: "
            "cifra aproximada · borde punteado = torneos recientes (2025–2026) · Datos: StatsBomb")
    return fig

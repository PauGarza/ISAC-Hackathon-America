"""Visualizaciones del ADN del entrenador (matplotlib, estilo común de src/eda.py).

Reglas (skill dataviz): color fijo por entrenador (nunca por rango), paleta validada con validate_palette.js
(Solari/Ortiz/Jardine/Almada pasan todos los pares; el aqua exige etiqueta directa → siempre se rotula),
la liga en gris neutro, marcas delgadas y texto en tinta, no en el color de la serie.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src import eda
from src.coach_profile import AXES, label, short

eda.set_style()
COACH_COLOR = {"Solari": "#2a78d6", "Ortiz": "#eb6834", "Jardine": "#1baf7a", "Almada": "#4a3aa7",
               "Cervantes": "#898781"}
LEAGUE = "#898781"
BAND = "#e1e0d9"


def _angles(n):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    return a + a[:1]


def radar(ax, values: pd.Series, color: str, name: str, ci: pd.DataFrame | None = None, bench=(50, 90)):
    """Radar en percentiles de liga: anillos de referencia (mediana y P90 de la liga) + perfil del entrenador."""
    ang = _angles(len(AXES))
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 100)
    ax.set_yticks([25, 50, 75, 100])
    ax.set_yticklabels(["", "50", "", "100"], fontsize=6, color=eda.MUTED)
    ax.set_xticks(ang[:-1])
    ax.set_xticklabels([a.replace(" ", "\n", 1) if len(a) > 12 else a for a in AXES], fontsize=7, color=eda.INK_2)
    ax.grid(color=BAND, lw=0.6)
    ax.spines["polar"].set_color(BAND)
    for b, ls in zip(bench, ["-", "--"]):
        ax.plot(ang, [b] * len(ang), color=LEAGUE, lw=0.9, ls=ls, zorder=1)
    v = values[AXES].tolist()
    v += v[:1]
    if ci is not None:
        lo, hi = ci.lo[AXES].tolist(), ci.hi[AXES].tolist()
        ax.fill_between(ang, lo + lo[:1], hi + hi[:1], color=color, alpha=0.15, lw=0, zorder=2)
    ax.plot(ang, v, color=color, lw=2, zorder=3)
    ax.scatter(ang[:-1], v[:-1], s=14, color=color, edgecolor=eda.SURFACE, lw=0.8, zorder=4)
    ax.set_title(name, loc="center", fontsize=10, color=eda.INK, pad=14)


def fig_radars(pcts: dict[str, pd.Series], cis: dict[str, pd.DataFrame] | None = None, ncols: int = 4,
               title: str = "ADN del entrenador: percentil frente a los técnicos de la Liga MX"):
    n = len(pcts)
    fig, axes = plt.subplots(1 if n <= ncols else int(np.ceil(n / ncols)), min(n, ncols),
                             figsize=(3.6 * min(n, ncols), 3.9 * (1 if n <= ncols else int(np.ceil(n / ncols)))),
                             subplot_kw={"polar": True})
    axes = np.atleast_1d(axes).ravel()
    for ax, (name, v) in zip(axes, pcts.items()):
        radar(ax, v, COACH_COLOR.get(name.split(" ")[0], eda.BLUE), name, (cis or {}).get(name))
    for ax in axes[n:]:
        ax.set_visible(False)
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold", fontsize=11)
    fig.tight_layout(rect=(0, 0.07, 1, 0.95))
    fig.text(0.01, 0.01, "Línea continua gris = técnico mediano de la liga (percentil 50) · punteada = percentil 90. "
             "Banda = incertidumbre (IC 90 %). Perfil ajustado por rival y localía.", fontsize=7, color=eda.MUTED)
    return fig


def fig_radar_compare(pcts: dict[str, pd.Series], title: str):
    """Dos o tres entrenadores superpuestos (máximo 3 series: la paleta valida todos los pares con 4)."""
    fig, ax = plt.subplots(figsize=(5.6, 5.6), subplot_kw={"polar": True})
    for name, v in pcts.items():
        radar(ax, v, COACH_COLOR.get(name.split(" ")[0], eda.BLUE), "")
    handles = [plt.Line2D([], [], color=COACH_COLOR.get(n.split(" ")[0], eda.BLUE), lw=2) for n in pcts]
    handles += [plt.Line2D([], [], color=LEAGUE, lw=0.9), plt.Line2D([], [], color=LEAGUE, lw=0.9, ls="--")]
    ax.legend(handles, list(pcts) + ["mediana de la liga", "P90 de la liga"], loc="upper center",
              bbox_to_anchor=(0.5, -0.06), ncol=3, fontsize=7)
    ax.set_title(title, loc="left", fontsize=10, pad=18)
    return fig


def fig_league_heatmap(pct: pd.DataFrame, highlight: list[str], top: int = 40):
    """Mapa de calor periodo de entrenador × eje (percentiles), ordenado por similitud (orden jerárquico)."""
    from scipy.cluster.hierarchy import leaves_list, linkage
    d = pct.sort_values("partidos", ascending=False)
    d = pd.concat([d.head(top), d[d.index.isin(highlight)]]).loc[lambda x: ~x.index.duplicated()]
    d = d.iloc[leaves_list(linkage(d[AXES].values, "ward"))]
    fig, ax = plt.subplots(figsize=(8.2, 0.24 * len(d) + 1.4))
    im = ax.imshow(d[AXES].values, cmap=eda.DIV, vmin=0, vmax=100, aspect="auto")
    ax.set_xticks(range(len(AXES)), AXES, rotation=35, ha="right")
    labels = [label(i) for i in d.index]
    ax.set_yticks(range(len(d)), labels, fontsize=6.5)
    for t, idx in zip(ax.get_yticklabels(), d.index):
        if idx in highlight:
            t.set_fontweight("bold")
            t.set_color(eda.INK)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.6)
    cb.set_label("percentil en la liga (50 = técnico típico)")
    ax.set_title("ADN de los técnicos de la Liga MX (≥ 15 partidos, 2021–2025) · en negritas, los del América",
                 loc="left", fontsize=9)
    return fig


def fig_style_map(prof: pd.DataFrame, highlight: dict[str, str], moves: list[tuple[str, str]]):
    """Mapa de estilo de la liga: PCA de los ejes. Flechas = mismo entrenador en dos clubes."""
    from sklearn.decomposition import PCA
    X = (prof[AXES] - prof[AXES].mean()) / prof[AXES].std()
    pca = PCA(2).fit(X)
    Z = pd.DataFrame(pca.transform(X), index=prof.index, columns=["PC1", "PC2"])
    fig, ax = plt.subplots(figsize=(7.8, 5.6))
    ax.scatter(Z.PC1, Z.PC2, s=18, color=LEAGUE, alpha=0.45, lw=0)
    placed = []
    for idx, coach in sorted(highlight.items(), key=lambda kv: -Z.loc[kv[0], "PC2"] if kv[0] in Z.index else 0):
        if idx in Z.index:
            x, y = Z.loc[idx, "PC1"], Z.loc[idx, "PC2"]
            ax.scatter(x, y, s=70, color=COACH_COLOR.get(coach, eda.BLUE), edgecolor=eda.SURFACE, lw=1.5, zorder=3)
            dy = 4
            while any(abs(x - px) < 1.6 and abs((y + dy / 40) - py) < 0.22 for px, py in placed):
                dy -= 11  # etiqueta cercana ya colocada: bajar esta
            placed.append((x, y + dy / 40))
            ax.annotate(label(idx), (x, y), xytext=(6, dy), textcoords="offset points", fontsize=7.5, color=eda.INK)
    for a, b in moves:
        if a in Z.index and b in Z.index:
            ax.annotate("", xy=Z.loc[b], xytext=Z.loc[a],
                        arrowprops=dict(arrowstyle="->", color=eda.INK_2, lw=1, shrinkA=6, shrinkB=6))
    for i, pc in enumerate(["PC1", "PC2"]):
        load = pd.Series(pca.components_[i], index=AXES)
        top = load.abs().nlargest(3).index
        txt = ", ".join(f"{'+' if load[t] > 0 else '−'}{t}" for t in top)
        (ax.set_xlabel if i == 0 else ax.set_ylabel)(f"{pc} ({pca.explained_variance_ratio_[i]:.0%}): {txt}", fontsize=7)
    ax.set_title("Mapa de estilo de los técnicos de la Liga MX · flecha = mismo técnico en otro club", loc="left")
    return fig, Z


def fig_consistency(cons: dict[str, pd.DataFrame]):
    """Punto (mediana) + rango P25–P75 por eje y entrenador: rangos cortos = identidad estable."""
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    names = list(cons)
    off = np.linspace(-0.27, 0.27, len(names))
    for j, name in enumerate(names):
        c = cons[name].reindex(AXES)
        y = np.arange(len(AXES)) + off[j]
        col = COACH_COLOR.get(name, eda.BLUE)
        ax.hlines(y, c.p25, c.p75, color=col, lw=2.2)
        ax.scatter(c.mediana, y, s=22, color=col, edgecolor=eda.SURFACE, lw=0.8, zorder=3, label=name)
    ax.axvline(0, color=LEAGUE, lw=0.8, ls="--")
    ax.set_yticks(range(len(AXES)), AXES)
    ax.invert_yaxis()
    ax.set_xlabel("desviaciones estándar respecto al equipo-partido típico de la liga (0 = liga)")
    ax.set_title("Consistencia: ¿qué tan parecido juega partido a partido? (mediana y rango P25–P75)", loc="left")
    ax.legend(ncol=len(names), loc="lower center", bbox_to_anchor=(0.5, -0.28))
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    return fig


def fig_context(ctx: dict[str, pd.DataFrame], a: str, b: str, title: str):
    """Mancuernas: valor del eje en el contexto a vs b para cada entrenador (una fila por eje × entrenador)."""
    names = list(ctx)
    fig, axes = plt.subplots(1, len(names), figsize=(3.2 * len(names), 4.2), sharey=True)
    axes = np.atleast_1d(axes)
    for ax, name in zip(axes, names):
        c = ctx[name].reindex(columns=AXES)
        col = COACH_COLOR.get(name, eda.BLUE)
        y = np.arange(len(AXES))
        if a in c.index and b in c.index:
            ax.hlines(y, c.loc[a], c.loc[b], color=BAND, lw=3)
            ax.scatter(c.loc[a], y, s=26, color=col, zorder=3, label=a)
            ax.scatter(c.loc[b], y, s=26, facecolor=eda.SURFACE, edgecolor=col, lw=1.5, zorder=3, label=b)
        ax.axvline(0, color=LEAGUE, lw=0.8, ls="--")
        ax.set_title(name, loc="left")
        ax.set_yticks(y, AXES)
        ax.grid(axis="y", visible=False)
    axes[0].invert_yaxis()
    axes[-1].legend(loc="lower right", fontsize=7)
    fig.suptitle(title, x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.text(0.01, 0.005, "Eje x: desviaciones estándar frente a la liga. Relleno = " + a + " · hueco = " + b + ".",
             fontsize=7, color=eda.MUTED)
    fig.tight_layout(rect=(0, 0.03, 1, 0.94))
    return fig


def fig_evolution(ev: pd.DataFrame, axes_show: list[str]):
    fig, axs = plt.subplots(1, len(axes_show), figsize=(3.3 * len(axes_show), 3.4), sharey=True)
    x = np.arange(len(ev))
    for ax, a in zip(np.atleast_1d(axs), axes_show):
        ax.axhline(0, color=LEAGUE, lw=0.8, ls="--")
        coach = ev.entrenador.str.split(", ").str[-1]
        for name, g in ev.assign(_x=x, _c=coach).groupby("_c", sort=False):
            ax.plot(g._x, g[a], marker="o", ms=4, lw=2, color=COACH_COLOR.get(name, eda.BLUE), label=name)
        ax.set_title(a, loc="left")
        ax.set_xticks(x, [t.replace("Apertura ", "A").replace("Clausura ", "C") for t in ev.index], rotation=60, fontsize=6.5)
    np.atleast_1d(axs)[0].set_ylabel("desv. est. frente a la liga")
    np.atleast_1d(axs)[-1].legend(fontsize=7)
    fig.suptitle("Evolución del ADN del América por torneo (color = entrenador)", x=0.01, ha="left", fontweight="bold", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return fig


def fig_coach_change(val: pd.DataFrame, a: str, b: str):
    """Validación: por partido, ¿se parece más al ADN de `a` o al de `b`? (log-odds del clasificador de liga).
    Puntos = partidos (color = técnico real); línea = media móvil de 5 partidos."""
    fig, ax = plt.subplots(figsize=(9.5, 3.8))
    ax.axhline(0, color=LEAGUE, lw=0.8)
    for coach, g in val.groupby("coach_short"):
        ax.scatter(g.match_date, g.logodds, s=24, color=COACH_COLOR.get(coach, eda.BLUE), label=f"partido dirigido por {coach}",
                   edgecolor=eda.SURFACE, lw=0.6, zorder=3)
    ax.plot(val.match_date, val.logodds.rolling(5, min_periods=3).mean(), color=eda.INK, lw=1.6, label="media móvil (5 partidos)")
    for d, txt in [(pd.Timestamp("2025-07-01"), "validación →"), (pd.Timestamp("2026-01-01"), "prueba →")]:
        ax.axvline(d, color=LEAGUE, lw=0.8, ls="--")
        ax.text(d, ax.get_ylim()[1], " " + txt, fontsize=7, va="top", color=eda.INK_2)
    ax.set_ylabel(f"← más {b}        más {a} →")
    ax.set_title(f"¿A quién se parece cada partido del América: al ADN de {b} o al de {a}? "
                 f"(modelo entrenado solo con 2021–2025)", loc="left", fontsize=9)
    ax.legend(ncol=3, fontsize=7, loc="upper left", bbox_to_anchor=(0, -0.12))
    fig.tight_layout()
    return fig

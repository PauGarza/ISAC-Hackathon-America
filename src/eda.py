"""Funciones de perfilado para el análisis exploratorio (EDA) de las tablas StatsBomb.

- classify_columns: asigna a cada columna un tipo analítico (numérica, booleana, categórica, ...)
- profile_numeric / profile_categorical / profile_boolean: tablas de estadísticas por columna
- profile_events_by_type: perfila columnas de eventos *dentro* del tipo al que aplican
- plot_*: histogramas, barras de frecuencia y mapas de correlación con un estilo común
"""
from __future__ import annotations

import ast
import json

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

# ---------------------------------------------------------------- estilo
SURFACE, INK, INK_2, MUTED, GRID, AXIS = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
BLUE, ORANGE, RED = "#2a78d6", "#eb6834", "#e34948"
SEQ = LinearSegmentedColormap.from_list("seq_blue", ["#f4f8fd", "#9ec5f4", "#3987e5", "#1c5cab", "#0d366b"])
DIV = LinearSegmentedColormap.from_list("div_blue_red", ["#104281", "#3987e5", "#f0efec", "#e66767", "#9e2a2a"])


def set_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS, "axes.labelcolor": INK_2, "axes.titlecolor": INK,
        "axes.titlesize": 10, "axes.titleweight": "bold", "axes.labelsize": 8,
        "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 7, "ytick.labelsize": 7,
        "axes.grid": True, "axes.axisbelow": True, "grid.color": GRID, "grid.linewidth": 0.6,
        "axes.spines.top": False, "axes.spines.right": False,
        "font.size": 8, "legend.fontsize": 7, "legend.frameon": False,
    })


# ------------------------------------------------------- clasificación
ID_COLS = {"id", "index", "account_id"}
DATE_HINTS = ("date", "timestamp", "kick_off", "last_updated", "birth")

# prefijo de columna de eventos -> tipo de evento al que aplica
EVENT_PREFIX_TYPE = {
    "pass_": "Pass", "shot_": "Shot", "carry_": "Carry", "duel_": "Duel", "dribble_": "Dribble",
    "clearance_": "Clearance", "goalkeeper_": "Goal Keeper", "foul_committed_": "Foul Committed",
    "foul_won_": "Foul Won", "ball_receipt_": "Ball Receipt*", "ball_recovery_": "Ball Recovery",
    "interception_": "Interception", "block_": "Block", "substitution_": "Substitution",
    "bad_behaviour_": "Bad Behaviour", "miscontrol_": "Miscontrol", "50_50": "50/50",
    "injury_": "Injury Stoppage",
}


def _first_valid(s: pd.Series):
    s = s.dropna()
    return s.iloc[0] if len(s) else None


def classify_columns(df: pd.DataFrame, max_categories: int = 60) -> pd.DataFrame:
    """Devuelve una tabla columna -> kind:
    id | numeric | boolean | categorical | categorical_high | datetime | coordinates | json | empty."""
    rows = []
    for col in df.columns:
        s = df[col]
        v = _first_valid(s)
        nun = s.nunique(dropna=True) if v is None or not isinstance(v, (list, np.ndarray)) else np.nan
        if v is None:
            kind = "empty"
        elif col in ID_COLS or col.endswith("_id"):
            kind = "id"
        elif pd.api.types.is_bool_dtype(s) or isinstance(v, (bool, np.bool_)):
            kind = "boolean"
        elif pd.api.types.is_numeric_dtype(s):
            kind = "numeric"
        elif isinstance(v, (list, np.ndarray)):
            kind = "coordinates"
        elif isinstance(v, str) and v[:1] in "{[":
            kind = "json"
        elif any(h in col for h in DATE_HINTS):
            kind = "datetime"
        elif isinstance(v, (int, float, np.number)):
            kind = "numeric"
        else:
            kind = "categorical" if nun <= max_categories else "categorical_high"
        rows.append({"column": col, "kind": kind, "dtype": str(s.dtype), "n_unique": nun,
                     "pct_null": round(100 * s.isna().mean(), 2), "example": str(v)[:60]})
    return pd.DataFrame(rows)


def cols_of(kinds: pd.DataFrame, *kind: str) -> list[str]:
    return kinds.loc[kinds.kind.isin(kind), "column"].tolist()


# ---------------------------------------------------------- perfiles
def _mode(s: pd.Series):
    vc = s.value_counts(dropna=True)
    if vc.empty:
        return np.nan, np.nan
    return vc.index[0], round(100 * vc.iloc[0] / s.notna().sum(), 2)


def profile_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """count, % nulos, únicos, min, p5, p25, mediana, media, p75, p95, max, desv. est., moda,
    % de la moda, % ceros, asimetría (skew)."""
    out = []
    for c in cols:
        s = pd.to_numeric(df[c], errors="coerce")
        nn = s.dropna()
        mode, mode_pct = _mode(nn)
        q = nn.quantile([.05, .25, .5, .75, .95]) if len(nn) else pd.Series([np.nan] * 5, index=[.05, .25, .5, .75, .95])
        out.append({
            "column": c, "count": int(nn.size), "pct_null": round(100 * s.isna().mean(), 2),
            "n_unique": int(nn.nunique()), "min": nn.min(), "p5": q[.05], "p25": q[.25],
            "median": q[.5], "mean": nn.mean(), "p75": q[.75], "p95": q[.95], "max": nn.max(),
            "std": nn.std(), "mode": mode, "mode_pct": mode_pct,
            "pct_zero": round(100 * (nn == 0).mean(), 2) if len(nn) else np.nan,
            "skew": nn.skew() if len(nn) > 2 else np.nan,
        })
    return pd.DataFrame(out).set_index("column")


def profile_categorical(df: pd.DataFrame, cols: list[str], top: int = 5) -> pd.DataFrame:
    """count, % nulos, n categorías, moda y su %, y el top-k con porcentajes."""
    out = []
    for c in cols:
        s = df[c]
        vc = s.value_counts(dropna=True)
        pct = 100 * vc / vc.sum() if vc.sum() else vc
        out.append({
            "column": c, "count": int(s.notna().sum()), "pct_null": round(100 * s.isna().mean(), 2),
            "n_categories": int(vc.size), "mode": vc.index[0] if vc.size else np.nan,
            "mode_pct": round(pct.iloc[0], 2) if vc.size else np.nan,
            "top_pct_cumulative": round(pct.head(top).sum(), 2) if vc.size else np.nan,
            f"top_{top}": " | ".join(f"{k} ({p:.1f}%)" for k, p in pct.head(top).items()),
        })
    return pd.DataFrame(out).set_index("column")


def profile_boolean(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    """En StatsBomb los flags vienen como True / NaN: NaN = False.
    pct_true = % de filas con True sobre todas las filas de `df`."""
    out = []
    for c in cols:
        s = df[c]
        n_true = int((s == True).sum())  # noqa: E712 (queremos comparar contra True, no truthiness)
        n_false = int((s == False).sum())  # noqa: E712
        out.append({"column": c, "rows": len(s), "n_true": n_true, "n_false_explicit": n_false,
                    "n_null": int(s.isna().sum()), "pct_true": round(100 * n_true / max(len(s), 1), 2)})
    return pd.DataFrame(out).set_index("column")


def frequency_table(s: pd.Series, top: int | None = None) -> pd.DataFrame:
    vc = s.value_counts(dropna=False)
    t = pd.DataFrame({"count": vc, "pct": (100 * vc / vc.sum()).round(2)})
    t["pct_cum"] = t.pct.cumsum().round(2)
    return t.head(top) if top else t


def column_type_owner(col: str) -> str | None:
    for prefix, etype in EVENT_PREFIX_TYPE.items():
        if col.startswith(prefix):
            return etype
    return None


def profile_events_by_type(events: pd.DataFrame, kinds: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Perfila cada columna específica de un tipo (pass_*, shot_*, …) SOLO sobre las filas de ese
    tipo; así el % de nulos y las estadísticas son interpretables. Devuelve numeric/categorical/boolean."""
    num, cat, boo = [], [], []
    kind_of = kinds.set_index("column").kind
    for col in events.columns:
        etype = column_type_owner(col)
        sub = events[events.type == etype] if etype else events
        k = kind_of.get(col)
        if k == "numeric":
            num.append(profile_numeric(sub, [col]).assign(event_type=etype or "(todas)"))
        elif k in ("categorical", "categorical_high"):
            cat.append(profile_categorical(sub, [col]).assign(event_type=etype or "(todas)"))
        elif k == "boolean":
            boo.append(profile_boolean(sub, [col]).assign(event_type=etype or "(todas)"))
    return {"numeric": pd.concat(num), "categorical": pd.concat(cat), "boolean": pd.concat(boo)}


def null_matrix_by_type(events: pd.DataFrame, cols: list[str], min_rows: int = 500) -> pd.DataFrame:
    """% de filas NO nulas de cada columna por tipo de evento (qué columna vive en qué evento)."""
    types = events.type.value_counts()
    types = types[types >= min_rows].index
    return (events[events.type.isin(types)].groupby("type")[cols]
            .agg(lambda s: 100 * s.notna().mean()).T.round(1))


# ---------------------------------------------------------- coordenadas
def expand_xy(df: pd.DataFrame, cols=("location", "pass_end_location", "carry_end_location", "shot_end_location")) -> pd.DataFrame:
    """location [x, y] -> location_x, location_y (cancha 120 x 80)."""
    df = df.copy()
    for c in cols:
        if c not in df:
            continue
        arr = df[c].map(lambda v: v if isinstance(v, (list, np.ndarray)) and len(v) >= 2 else [np.nan, np.nan])
        df[f"{c}_x"] = arr.map(lambda v: float(v[0]))
        df[f"{c}_y"] = arr.map(lambda v: float(v[1]))
    return df


def _parse_nested(v):
    if not isinstance(v, str):
        return v
    try:
        return json.loads(v)
    except json.JSONDecodeError:  # algunas columnas de lineups vienen como repr de Python
        try:
            return ast.literal_eval(v)
        except (ValueError, SyntaxError):  # texto plano (p. ej. country = "Mexico")
            return v


def parse_json_col(s: pd.Series) -> pd.Series:
    return s.map(_parse_nested)


# --------------------------------------------------------- correlación
def correlation(df: pd.DataFrame, cols: list[str], method: str = "spearman", min_std: float = 1e-9) -> pd.DataFrame:
    x = df[cols].apply(pd.to_numeric, errors="coerce")
    x = x.loc[:, x.std() > min_std]  # quitar constantes
    return x.corr(method=method)


def top_correlations(corr: pd.DataFrame, n: int = 25, exclude_self_family: bool = False) -> pd.DataFrame:
    """Pares con |r| más alto (sin duplicados ni diagonal)."""
    m = corr.where(np.triu(np.ones(corr.shape, dtype=bool), k=1)).stack()
    t = m.rename("r").reset_index().rename(columns={"level_0": "var_1", "level_1": "var_2"})
    t["abs_r"] = t.r.abs()
    return t.sort_values("abs_r", ascending=False).head(n).drop(columns="abs_r").reset_index(drop=True)


def cramers_v(x: pd.Series, y: pd.Series) -> float:
    """Asociación entre dos categóricas (0 = nada, 1 = total), con corrección de sesgo."""
    ct = pd.crosstab(x, y)
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        return np.nan
    n = ct.values.sum()
    expected = np.outer(ct.sum(1), ct.sum(0)) / n
    chi2 = ((ct.values - expected) ** 2 / expected).sum()
    phi2 = chi2 / n
    r, k = ct.shape
    phi2c = max(0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rc, kc = r - (r - 1) ** 2 / (n - 1), k - (k - 1) ** 2 / (n - 1)
    return float(np.sqrt(phi2c / max(min(kc - 1, rc - 1), 1e-9)))


def cramers_v_matrix(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    m = pd.DataFrame(np.eye(len(cols)), index=cols, columns=cols)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            m.loc[a, b] = m.loc[b, a] = cramers_v(df[a], df[b])
    return m


# -------------------------------------------------------------- plots
def _grid(n: int, ncols: int, w: float = 3.2, h: float = 2.3):
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(w * ncols, h * nrows), squeeze=False)
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    return fig, axes.flat


def plot_numeric_grid(df: pd.DataFrame, cols: list[str], ncols: int = 4, bins: int = 40,
                      clip: tuple[float, float] = (0.005, 0.995), title: str | None = None):
    """Histograma por columna (recortado a p0.5–p99.5 para que las colas no aplasten la forma),
    con media (naranja) y mediana (azul oscuro)."""
    fig, axes = _grid(len(cols), ncols)
    for ax, c in zip(axes, cols):
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if s.empty:
            ax.set_title(f"{c}\n(sin datos)")
            continue
        lo, hi = s.quantile(clip[0]), s.quantile(clip[1])
        sc = s[(s >= lo) & (s <= hi)] if hi > lo else s
        discrete = s.nunique() <= 25
        integer = bool((sc == sc.round()).all()) and (hi - lo) <= 150
        if discrete:
            vc = s.value_counts().sort_index()
            ax.bar(vc.index, vc.values, width=0.8 * (np.diff(vc.index).min() if len(vc) > 1 else 1), color=BLUE)
        else:
            # enteros: un bin por valor (evita barras alternadas por aliasing)
            b = np.arange(lo, hi + 2) - 0.5 if integer else bins
            ax.hist(sc, bins=b, color=BLUE, edgecolor=SURFACE, linewidth=0.3 if integer else 0.5)
        ax.axvline(s.mean(), color=ORANGE, lw=1.5, label="media")
        ax.axvline(s.median(), color="#0d366b", lw=1.5, ls="--", label="mediana")
        ax.set_title(c, loc="left")
        ax.text(0.99, 0.97, f"n={len(s):,}\nμ={s.mean():.3g}  med={s.median():.3g}",
                transform=ax.transAxes, ha="right", va="top", fontsize=6.5, color=INK_2)
        ax.grid(axis="x", visible=False)
    handles, labels = axes[0].get_legend_handles_labels()
    if title:
        fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    fig.legend(handles, labels, loc="upper right", ncol=2, bbox_to_anchor=(0.99, 1.0))
    return fig


def plot_categorical_grid(df: pd.DataFrame | dict, cols: list[str], ncols: int = 3, top: int = 10,
                          title: str | None = None):
    """Barras horizontales con el % de cada categoría (top-k; el resto se agrupa en 'Otras').
    `df` puede ser un dict columna -> DataFrame para perfilar cada columna sobre su propio
    subconjunto (p. ej. duel_type solo sobre duelos), así el % de nulos es el correcto."""
    fig, axes = _grid(len(cols), ncols, w=4.6, h=0.28 * (top + 2) + 0.6)
    for ax, c in zip(axes, cols):
        d = df[c] if isinstance(df, dict) else df
        vc = d[c].value_counts(dropna=True)
        pct = 100 * vc / vc.sum()
        if len(pct) > top:
            pct = pd.concat([pct.head(top), pd.Series({"Otras": pct.iloc[top:].sum()})])
        pct = pct.iloc[::-1]
        ax.barh([str(i)[:38] for i in pct.index], pct.values, color=BLUE, height=0.7)
        for y, v in enumerate(pct.values):
            ax.text(v, y, f" {v:.1f}%", va="center", fontsize=6.5, color=INK_2)
        ax.set_title(f"{c}  ({vc.size} cat., {100 * d[c].isna().mean():.0f}% nulos)", loc="left")
        ax.set_xlim(0, pct.max() * 1.25)
        ax.grid(axis="y", visible=False)
        ax.set_xlabel("% de filas no nulas")
    if title:
        fig.suptitle(title, x=0.01, ha="left", fontsize=12, fontweight="bold", color=INK)
    fig.tight_layout()
    return fig


def plot_heatmap(m: pd.DataFrame, title: str, cmap=DIV, vmin=-1, vmax=1, annot: bool = True,
                 fmt: str = "{:.2f}", size: float | None = None, cbar_label: str = ""):
    n = max(m.shape)
    size = size or max(5, 0.38 * n + 2)
    fig, ax = plt.subplots(figsize=(size * m.shape[1] / n + 1.5, size * m.shape[0] / n))
    im = ax.imshow(m.values.astype(float), cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")
    ax.set_xticks(range(m.shape[1]), m.columns, rotation=90)
    ax.set_yticks(range(m.shape[0]), m.index)
    ax.grid(False)
    if annot and n <= 30:
        for i in range(m.shape[0]):
            for j in range(m.shape[1]):
                v = m.values[i, j]
                if pd.notna(v):
                    r, g, b, _ = plt.get_cmap(cmap)((v - vmin) / (vmax - vmin))
                    dark = 0.2126 * r + 0.7152 * g + 0.0722 * b < 0.5  # luminancia de la celda
                    ax.text(j, i, fmt.format(v), ha="center", va="center", fontsize=6,
                            color="white" if dark else INK)
    cb = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label(cbar_label, color=INK_2)
    cb.outline.set_visible(False)
    ax.set_title(title, loc="left")
    fig.tight_layout()
    return fig

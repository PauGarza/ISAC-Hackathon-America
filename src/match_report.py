"""FICHA AUTOMÁTICA POR PARTIDO (implementación del ciclo de vida: el "producto").

build_match_report(match_id) → reports/match_reports/<fecha>_<rival>.html

Lee SOLO de Gold, de los scores y de las model cards. Secciones: contexto · el partido en números por
criterio (percentil vs histórico de entrenamiento) · uso de jugadores · comparación histórica (mapa de estilo,
tipo de partido, partidos similares) · momentos · balón parado · proyección (esperado vs observado,
siguiente partido, simulación) · crónica automática · monitoreo de drift.
"""
from __future__ import annotations

import base64
import io
import json

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from jinja2 import Environment, FileSystemLoader  # noqa: E402
from mplsoccer import VerticalPitch  # noqa: E402

from src import eda  # noqa: E402
from src import features as F  # noqa: E402
from src import framework as fw  # noqa: E402
from src import modeling as M  # noqa: E402
from src.pipeline.config import GOLD, MODELS, REPORTS, ROOT, get_logger  # noqa: E402
from src.pipeline.monitoring import drift_report  # noqa: E402
from src.pipeline.silver import load_events  # noqa: E402

log = get_logger("report")
eda.set_style()
CRITERIA_ORDER = ["Construcción", "Progresión", "Ocasiones", "Presión", "Organización defensiva", "Transiciones",
                  "Dominio", "Balón parado", "Uso de jugadores"]
GROUP_COLOR = {"Portero": "#898781", "Defensa": "#2a78d6", "Carrilero": "#1baf7a", "Medio defensivo": "#4a3aa7",
               "Medio": "#e87ba4", "Medio ofensivo": "#eda100", "Banda": "#eb6834", "Delantero": "#e34948"}


def _b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=110, bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def _catalog() -> pd.DataFrame:
    cat = {**F.FEATURES, **F.PLAYER_FEATURES}
    return pd.DataFrame([(k, *v) for k, v in cat.items()], columns=["var", "criterio", "definicion", "direccion"]).set_index("var")


def percentiles(mf: pd.DataFrame, split: pd.Series, match_id: int) -> pd.DataFrame:
    """Percentil del partido frente a la distribución de ENTRENAMIENTO (sin leakage)."""
    cat = _catalog()
    train = mf[mf.match_id.map(split) == "train"]
    row = mf.set_index("match_id").loc[match_id]
    rows = []
    for v in cat.index:
        if v not in mf or pd.isna(row.get(v)):
            continue
        ref = train[v].dropna()
        rows.append({"var": v, "valor": row[v], "percentil": (ref < row[v]).mean() * 100 + (ref == row[v]).mean() * 50,
                     "mediana_hist": ref.median(), **cat.loc[v].to_dict()})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ figuras
def fig_percentiles(pct: pd.DataFrame) -> str:
    pct = pct.assign(o=pct.criterio.map({c: i for i, c in enumerate(CRITERIA_ORDER)})).sort_values(["o", "var"], ascending=[False, False])
    fig, ax = plt.subplots(figsize=(8.5, 0.24 * len(pct) + 1))
    colors = np.where(pct.percentil >= 80, eda.BLUE, np.where(pct.percentil <= 20, eda.ORANGE, "#c3c2b7"))
    ax.barh(range(len(pct)), pct.percentil, color=colors, height=0.7)
    ax.axvline(50, color=eda.INK_2, lw=0.8, ls="--")
    ax.set_yticks(range(len(pct)), [f"{c} · {F.label(v)}" for c, v in zip(pct.criterio, pct["var"])], fontsize=6.5)
    for y, (p, v) in enumerate(zip(pct.percentil, pct.valor)):
        ax.text(min(p, 97) + 1, y, f"{v:.2f}", va="center", fontsize=6, color=eda.INK_2)
    ax.set_xlim(0, 105)
    ax.set_xlabel("percentil frente a los partidos de entrenamiento (50 = partido típico)")
    ax.set_title("El partido en números: percentil por métrica y criterio", loc="left")
    ax.grid(axis="y", visible=False)
    return _b64(fig)


def short_name(full: str) -> str:
    """Nombre + primer apellido (convención hispana: 'Luis Ángel Malagón Velázquez' → 'Luis Malagón')."""
    t = str(full).split()
    return " ".join(t) if len(t) <= 2 else f"{t[0]} {t[-2]}"


def fig_players(pm: pd.DataFrame) -> str:
    d = pm.sort_values("obv", ascending=True).assign(short=lambda x: x.player_short if "player_short" in x else x.player_name.map(short_name))
    fig, axes = plt.subplots(1, 2, figsize=(11, 0.28 * len(d) + 1.2), gridspec_kw={"width_ratios": [1.3, 1]})
    ax = axes[0]
    ax.barh(d.short, d.obv, color=d.position_group.map(GROUP_COLOR).fillna("#898781"))
    ax.axvline(0, color=eda.AXIS)
    ax.set_title("OBV por jugador (color = línea)", loc="left"); ax.set_xlabel("OBV del partido")
    ax.grid(axis="y", visible=False)
    ax = axes[1]
    r = d.dropna(subset=["obv_p90_resid"])
    ax.barh(r.short, r.obv_p90_resid,
            color=np.where(r.obv_p90_resid > 0, eda.BLUE, eda.ORANGE))
    ax.axvline(0, color=eda.AXIS)
    ax.set_title("¿Rindió por encima de su referencia previa?", loc="left"); ax.set_xlabel("OBV p90 − referencia (≥30')")
    ax.grid(axis="y", visible=False)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in GROUP_COLOR.values()]
    fig.legend(handles, GROUP_COLOR.keys(), loc="lower center", ncol=8, bbox_to_anchor=(0.5, -0.02), fontsize=7)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    return _b64(fig)


def fig_style_map(scores: pd.DataFrame, match_id: int, similar: list[int], loadings: pd.DataFrame,
                  type_names: dict) -> str:
    fig, ax = plt.subplots(figsize=(7, 5))
    cmap = plt.get_cmap("tab10")
    for k, dd in scores.groupby("tipo_partido"):
        ax.scatter(dd.PC1, dd.PC2, s=14, color=cmap(k), alpha=.35, lw=0, label=type_names.get(k, f"tipo {k}"))
    s = scores.set_index("match_id")
    ax.scatter(s.loc[similar, "PC1"], s.loc[similar, "PC2"], s=60, facecolor="none", edgecolor=eda.INK, lw=1.2, label="similares")
    ax.scatter([s.loc[match_id, "PC1"]], [s.loc[match_id, "PC2"]], s=160, marker="*", color=eda.RED, edgecolor=eda.INK, zorder=5, label="este partido")
    for i, pc in enumerate(["PC1", "PC2"]):
        top = loadings[pc].abs().nlargest(3).index
        lab = ", ".join(f"{'+' if loadings.loc[t, pc] > 0 else '−'}{F.label(t)}" for t in top)
        (ax.set_xlabel if i == 0 else ax.set_ylabel)(f"{pc}: {lab}", fontsize=7)
    ax.legend(fontsize=7, loc="best")
    ax.set_title("Mapa de estilo (PCA de métricas núcleo) — todos los partidos", loc="left")
    return _b64(fig)


def fig_timeline(ev: pd.DataFrame, seg_features: pd.DataFrame) -> str:
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True, gridspec_kw={"height_ratios": [1.1, 1]})
    e = ev[ev.period < 5]
    shots = e[e.type == "Shot"]
    ax = axes[0]
    for team, color in [(fw.TEAM, eda.BLUE), ("rival", eda.ORANGE)]:
        s = shots[(shots.team == fw.TEAM) if team == fw.TEAM else (shots.team != fw.TEAM)]
        t = np.r_[0, s.minute.values + s.second.values / 60, e.minute.max() + 1]
        c = np.r_[0, s.shot_statsbomb_xg.cumsum().values, s.shot_statsbomb_xg.sum()]
        ax.step(t, c, where="post", color=color, lw=2, label="América" if team == fw.TEAM else "Rival")
        g = s[s.shot_outcome == "Goal"]
        ax.scatter(g.minute + g.second / 60, np.interp(g.minute + g.second / 60, t, c), color=color, s=60, zorder=5, edgecolor=eda.INK)
    subs = e[(e.type == "Substitution") & (e.team == fw.TEAM)].minute.unique()
    for m in subs:
        for a in axes:
            a.axvline(m, color=eda.MUTED, lw=0.8, ls=":")
    ax.set_ylabel("xG acumulado"); ax.legend(loc="upper left")
    ax.set_title("Momentos: xG acumulado (● gol) y cambios del América (líneas punteadas)", loc="left")
    ax = axes[1]
    mids = {"0-15": 7.5, "15-30": 22.5, "30-45+": 37.5, "45-60": 52.5, "60-75": 67.5, "75-90": 82.5, "90+": 93}
    sf = seg_features.groupby("minute_bin", observed=True)[["field_tilt", "def_action_x_mean"]].mean()
    x = [mids[str(b)] for b in sf.index]
    ax.plot(x, sf.field_tilt, marker="o", color=eda.BLUE, label="field tilt (%)")
    ax.plot(x, sf.def_action_x_mean, marker="s", color=eda.ORANGE, label="altura acciones defensivas (x)")
    ax.set_xlabel("minuto"); ax.legend(loc="lower left", fontsize=7)
    fig.tight_layout()
    return _b64(fig)


def fig_set_pieces(sp: pd.DataFrame) -> str:
    pitch = VerticalPitch(pitch_type="statsbomb", half=True, pitch_color=eda.SURFACE, line_color=eda.AXIS)
    fig, axes = pitch.draw(nrows=1, ncols=2, figsize=(9, 4.6))
    for ax, own, title in [(axes[0], True, "A favor"), (axes[1], False, "En contra")]:
        d = sp[sp.is_team == own].dropna(subset=["pass_end_location_x"])
        pitch.scatter(d.pass_end_location_x, d.pass_end_location_y, ax=ax, s=40,
                      c=np.where(d.shot, eda.RED, eda.BLUE), edgecolors=eda.SURFACE, alpha=.8)
        ax.set_title(f"{title}: {len(d)} envíos · {int(d.shot.sum())} con tiro (rojo) · xG {d.xg.sum():.2f}", fontsize=8)
    return _b64(fig)


# ------------------------------------------------------------------ texto
def chronicle(pct: pd.DataFrame, proj: pd.DataFrame, ctx: pd.Series, sim: pd.Series) -> list[str]:
    s = [f"{'Local' if ctx.is_home else 'Visita'} ante {ctx.opponent} ({ctx.fase.lower()}, {ctx.torneo}); "
         f"resultado {int(ctx.goals_for)}-{int(ctx.goals_against)}."]
    hi = pct[pct.percentil >= 85].sort_values("percentil", ascending=False).head(4)
    lo = pct[pct.percentil <= 15].sort_values("percentil").head(4)
    for r, nivel in [*((r, "alto") for r in hi.itertuples()), *((r, "bajo") for r in lo.itertuples())]:
        s.append(f"<b>{F.label(r.var)}</b> muy {nivel}: {r.valor:.2f} frente a una mediana de {r.mediana_hist:.2f} "
                 f"(percentil {r.percentil:.0f})." + (f" <span class='note'>Lectura: {r.direccion}.</span>" if "=" in r.direccion else ""))
    big = proj.assign(z=lambda d: d.desvio_z.abs()).sort_values("z", ascending=False).head(2)
    for r in big.itertuples():
        if abs(r.desvio_z) >= 1:
            s.append(f"Dado el contexto previo, se esperaba <b>{F.label(r.variable)}</b> ≈ {r.esperado:.2f} y fue {r.observado:.2f}: "
                     f"el plan se desvió de lo habitual ({'+' if r.desvio_z > 0 else '−'}{abs(r.desvio_z):.1f} desv. est.).")
    s.append(f"Con los tiros que hubo, el resultado más probable era "
             f"{max(['victoria', 'empate', 'derrota'], key=lambda k: sim[{'victoria': 'P(G)', 'empate': 'P(E)', 'derrota': 'P(P)'}[k]])} "
             f"(G {sim['P(G)']:.0%} · E {sim['P(E)']:.0%} · P {sim['P(P)']:.0%}).")
    return s


# ------------------------------------------------------------------ ficha
def build_match_report(match_id: int) -> str:
    g = M.load_gold()
    dim, mf, split = g["dim_match"], g["match_features"], g["split"]
    ctx = dim.set_index("match_id").loc[match_id]
    scores = pd.read_parquet(GOLD / "scores" / "match_scores.parquet")
    sc = scores.set_index("match_id").loc[match_id]
    space = joblib.load(MODELS / "U1U2_style_space.joblib")
    loadings = pd.DataFrame(space["pca"].components_.T, index=space["cols"],
                            columns=[f"PC{i + 1}" for i in range(space["pca"].n_components_)])

    ev = load_events()
    ev = ev[ev.match_id == match_id]
    ev = F.event_flags(fw.add_game_state(ev))
    poss = g["fct_possession"][g["fct_possession"].match_id == match_id]
    seg_f = F.aggregate(ev, poss, ["minute_bin"])
    pm = g["fct_player_match"][g["fct_player_match"].match_id == match_id]
    sp = g["fct_set_piece"][g["fct_set_piece"].match_id == match_id]
    pct = percentiles(mf, split, match_id)

    # proyección: esperado (T1, contexto previo) vs observado + siguiente partido
    tr = mf[mf.match_id.map(split) == "train"]
    proj = pd.DataFrame([{"variable": v, "etiqueta": F.label(v), "fuente": sc.get(f"{v}__fuente", ""),
                          "esperado": sc[f"{v}__esperado"], "observado": sc[f"{v}__observado"],
                          "desvio_z": (sc[f"{v}__observado"] - sc[f"{v}__esperado"]) / tr[v].std()}
                         for v in M.STYLE_TARGETS if f"{v}__esperado" in sc.index])
    nxt = dim[dim.match_order == ctx.match_order + 1]
    next_proj = None
    if len(nxt):
        nid = nxt.match_id.iloc[0]
        if nid in scores.match_id.values:
            ns = scores.set_index("match_id").loc[nid]
            next_proj = {"rival": nxt.opponent.iloc[0], "fecha": str(nxt.match_date.iloc[0])[:10],
                         "localia": "Local" if nxt.is_home.iloc[0] else "Visita",
                         "tabla": [{"variable": F.label(v), "esperado": f"{ns[f'{v}__esperado']:.2f}"} for v in M.STYLE_TARGETS
                                   if f"{v}__esperado" in ns.index]}
    similar = sc["similares"] if isinstance(sc["similares"], (list, np.ndarray)) else []
    sim_tab = dim[dim.match_id.isin(similar)][["match_date", "opponent", "is_home", "goals_for", "goals_against", "torneo"]]
    drift = drift_report(mf, split, M.STYLE_TARGETS, until_order=int(ctx.match_order))
    drift.index = [F.label(v) for v in drift.index]
    # nombre descriptivo de cada tipo de partido (clúster U2): perfil medio en entrenamiento
    prof = (scores.merge(mf[["match_id", "possession_time_pct", "field_tilt", "ppda"]], on="match_id")
            .loc[lambda d: d.match_id.map(split) == "train"].groupby("tipo_partido")[["possession_time_pct", "field_tilt", "ppda"]].mean())
    type_names = {k: f"Tipo {k + 1}: posesión {r.possession_time_pct:.0f}% · tilt {r.field_tilt:.0f}% · PPDA {r.ppda:.1f}"
                  for k, r in prof.iterrows()}
    cards = {}
    for f in sorted(MODELS.glob("*.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        cards[c["name"]] = c

    env = Environment(loader=FileSystemLoader(ROOT / "src" / "templates"), autoescape=False)
    html = env.get_template("match_report.html.j2").render(
        ctx=ctx, match_id=match_id, fecha=str(ctx.match_date)[:10],
        sim=sc, tipo=type_names.get(int(sc.tipo_partido), int(sc.tipo_partido)),
        cronica=chronicle(pct, proj, ctx, sc),
        fig_pct=fig_percentiles(pct), fig_players=fig_players(pm), fig_map=fig_style_map(scores, match_id, list(similar), loadings, type_names),
        fig_time=fig_timeline(ev, seg_f), fig_sp=fig_set_pieces(sp),
        players=pm.assign(player_name=pm.get("player_short", pm.player_name)).sort_values("obv", ascending=False)[["player_name", "position_group", "minutes", "obv", "obv_p90_ref_prev", "obv_p90_resid"]].round(2).to_dict("records"),
        dist={F.label(k): v for k, v in mf.set_index("match_id").loc[match_id, list(F.PLAYER_FEATURES)].round(2).items()},
        proj=proj.round(2).to_dict("records"), next_proj=next_proj,
        similares=sim_tab.assign(match_date=sim_tab.match_date.astype(str).str[:10]).to_dict("records"),
        drift=drift.round(3).reset_index().rename(columns={"index": "variable"}).head(8).to_dict("records"),
        n_cards=len(cards), cards=cards, assumptions=fw.ASSUMPTIONS)
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / f"{str(ctx.match_date)[:10]}_{ctx.opponent.replace(' ', '_')}.html"
    path.write_text(html, encoding="utf-8")
    log.info(f"Ficha generada: {path}")
    return str(path)


def build_many(match_ids=None):
    if not match_ids:
        dim = pd.read_parquet(GOLD / "dim_match.parquet")
        match_ids = [int(dim.sort_values("match_order").match_id.iloc[-1])]  # último partido
    return [build_match_report(m) for m in match_ids]

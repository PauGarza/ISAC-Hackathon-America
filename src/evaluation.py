"""EVALUACIÓN DEL MARCO Y DE LAS VARIABLES COMO CRITERIOS (etapa 2 del ciclo de vida).

- framework_validations: ¿las definiciones propias coinciden con las de StatsBomb y con la realidad?
- half_features + variable_evaluation: cada variable por partido se evalúa como criterio medible:
    1. fiabilidad intra-partido  (correlación 1er vs 2º tiempo, corregida con Spearman-Brown)
    2. discriminación entre partidos (ICC(1) con los dos tiempos como mediciones repetidas)
    3. estabilidad temporal       (autocorrelación lag-1 entre partidos consecutivos)
    4. sensibilidad al contexto   (R² de localía + fuerza del rival + fase)
    5. redundancia                (máx |ρ| con otra variable y VIF → supuesto de no multicolinealidad)
    6. validez                    (ρ de Spearman con OBV neto y diferencial de np xG)
- select_core: reglas explícitas → variables núcleo.
- threshold_sensitivity: ¿cambian los rankings de partidos si se mueven los umbrales de ASSUMPTIONS?

Los resultados se guardan en data/gold/analysis/ (los lee reports/framework/make_tables.py).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src import features as F
from src import framework as fw
from src.pipeline.config import BRONZE, GOLD, MANIFEST, SILVER

ANALYSIS = GOLD / "analysis"
OUTCOME_VARS = ["obv_net", "np_xg_diff"]


# ------------------------------------------------------------------ estado de las capas
def layer_status() -> dict[str, pd.DataFrame]:
    m = pd.read_parquet(MANIFEST)
    bronze = m.groupby("endpoint").agg(recursos=("key", "size"), MB=("bytes", lambda b: b.sum() / 1e6),
                                       status_200=("status", lambda s: (s == 200).mean() * 100),
                                       vacios=("bytes", lambda b: (b < 100).sum()))
    silver = {}
    for p in sorted(SILVER.glob("*.parquet")):
        silver[p.stem] = pd.read_parquet(p).shape
    for d in ["events", "frames360"]:
        parts = sorted((SILVER / d).glob("season=*/part.parquet"))
        silver[d] = (sum(pd.read_parquet(p, columns=["match_id"]).shape[0] for p in parts), len(parts))
    silver = pd.DataFrame(silver, index=["filas", "columnas / particiones"]).T
    gold = pd.DataFrame({p.stem: pd.read_parquet(p).shape for p in sorted(GOLD.glob("*.parquet"))},
                        index=["filas", "columnas"]).T
    return {"bronze": bronze, "silver": silver, "gold": gold}


# ------------------------------------------------------------------ validaciones del marco
def framework_validations(mf: pd.DataFrame, poss: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    from src.pipeline.quality import score_from_events
    from src.pipeline.silver import load_events
    rows = []
    # transición propia vs is_transition de StatsBomb (ambos equipos)
    t = poss[poss.transition]
    sb = poss[poss.is_transition_sb > 0.5]
    rows.append(("Transición ofensiva (propia) marcada también por StatsBomb (%)", (t.is_transition_sb > 0).mean() * 100, "≥ 70", None))
    rows.append(("Posesiones is_transition de StatsBomb detectadas por la definición propia (%)",
                 sb.transition.mean() * 100, "informativo", None))
    for mine, theirs, name, thr in [("ppda", "sb_ppda", "PPDA propio vs PPDA StatsBomb (ρ Spearman)", 0.8),
                                    ("possession_time_pct", "sb_possession", "Posesión (tiempo) vs posesión StatsBomb (ρ)", 0.8),
                                    ("np_xg_per100poss", "sb_np_xg", "np xG/100 pos. vs np xG StatsBomb (ρ)", 0.8),
                                    ("def_action_x_mean", "sb_defensive_distance", "Altura acciones def. vs defensive distance SB (ρ)", 0.6)]:
        if theirs in mf:
            rows.append((name, mf[[mine, theirs]].corr("spearman").iloc[0, 1], f"> {thr}", None))
    ev = load_events(columns=["match_id", "period", "minute", "second", "type", "team", "shot_outcome"])
    rec = score_from_events(ev).join(dim.set_index("match_id")[["goals_for", "goals_against"]])
    rows.append(("Marcador reconstruido == oficial (% partidos)",
                 ((rec.gf == rec.goals_for) & (rec.ga == rec.goals_against)).mean() * 100, "= 100", None))
    # minutos: fct_player_match vs alineaciones (lineup_positions)
    pm = pd.read_parquet(GOLD / "fct_player_match.parquet")
    lp = pd.read_parquet(SILVER / "lineup_positions.parquet")
    lp = lp[lp.team == fw.TEAM]
    e = ev[ev.period < 5]
    ends = (e.minute + e.second / 60).groupby(e.match_id).max()  # final real del partido (reloj de eventos)
    lp = lp.assign(to_min=lp.to_min.fillna(lp.match_id.map(ends)))
    lu_min = (lp.to_min - lp.from_min).clip(lower=0).groupby(lp.match_id).sum()
    pm_min = pm.groupby("match_id").minutes.sum()
    rel = (pm_min / lu_min).dropna()
    rows.append(("Minutos fct_player_match / minutos por alineaciones (mediana)", rel.median(), "≈ 1", None))
    out = pd.DataFrame(rows, columns=["validación", "valor", "criterio", "_"]).drop(columns="_")

    def ok(r):
        c = r.criterio
        if c.startswith("≥"):
            return r.valor >= float(c[1:])
        if c.startswith(">"):
            return r.valor > float(c[1:])
        if c.startswith("="):
            return r.valor == float(c[1:])
        if c.startswith("≈"):
            return abs(r.valor - float(c[1:])) < 0.1
        return None
    out["cumple"] = out.apply(ok, axis=1)
    return out


# ------------------------------------------------------------------ variables por tiempo (fiabilidad)
def half_features(ev: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    """Mismas métricas de FEATURES, calculadas por separado en el 1er y 2º tiempo de cada partido."""
    e = ev[ev.period.isin([1, 2])]
    p = poss[poss.period.isin([1, 2])]
    return F.aggregate(e, p, ["match_id", "period"])


def _icc1(a: pd.Series, b: pd.Series) -> float:
    """ICC(1) de dos mediciones por partido (1er y 2º tiempo): varianza entre partidos / total."""
    x = pd.concat([a, b], axis=1).dropna().values
    n, k = x.shape
    if n < 10:
        return np.nan
    grand = x.mean()
    msb = k * ((x.mean(1) - grand) ** 2).sum() / (n - 1)
    msw = ((x - x.mean(1, keepdims=True)) ** 2).sum() / (n * (k - 1))
    return float((msb - msw) / (msb + (k - 1) * msw))


def variable_evaluation(mf: pd.DataFrame, halves: pd.DataFrame, variables: list[str] | None = None) -> pd.DataFrame:
    variables = variables or [v for v in {**F.FEATURES, **F.PLAYER_FEATURES} if v in mf]
    d = mf.sort_values("match_order").reset_index(drop=True)
    h1 = halves.xs(1, level="period") if "period" in halves.index.names else None
    h2 = halves.xs(2, level="period") if "period" in halves.index.names else None
    ctx = pd.get_dummies(d[["is_home", "fase"]].astype(str), drop_first=True).astype(float)
    ctx["rival_ppg_prev"] = d.rival_ppg_prev.fillna(d.rival_ppg_prev.median())
    ctx = sm.add_constant(ctx)
    cat = {**F.FEATURES, **F.PLAYER_FEATURES}
    rows = []
    for v in variables:
        y = d[v]
        r = {"variable": v, "etiqueta": F.label(v), "criterio": cat[v][0], "n": int(y.notna().sum()),
             "media": y.mean(), "cv": y.std() / abs(y.mean()) if y.mean() else np.nan}
        if h1 is not None and v in h1:
            a, b = h1[v].reindex(d.match_id), h2[v].reindex(d.match_id)
            rho = pd.concat([a, b], axis=1).corr("spearman").iloc[0, 1]
            r["r_mitades"] = rho
            r["fiabilidad_SB"] = 2 * rho / (1 + rho) if pd.notna(rho) and rho > -1 else np.nan
            r["ICC1"] = _icc1(a, b)
        r["lag1"] = y.autocorr(1)
        m = y.notna()
        if m.sum() > 30:
            fit = sm.OLS(y[m], ctx[m]).fit()
            r["R2_contexto"], r["p_contexto"] = fit.rsquared, fit.f_pvalue
        for o in OUTCOME_VARS:
            r[f"rho_{o}"] = d[[v, o]].corr("spearman").iloc[0, 1] if v != o else np.nan
        rows.append(r)
    out = pd.DataFrame(rows).set_index("variable")
    cm = d[variables].corr("spearman").abs()
    cm = cm.mask(np.eye(len(cm), dtype=bool))
    out["max_abs_rho"] = cm.max()
    out["mas_parecida"] = cm.idxmax()
    return out


def vif(mf: pd.DataFrame, cols: list[str]) -> pd.Series:
    X = mf[cols].apply(lambda s: s.fillna(s.median()))
    X = (X - X.mean()) / X.std()
    X = sm.add_constant(X)
    return pd.Series([variance_inflation_factor(X.values, i) for i in range(1, X.shape[1])], index=cols, name="VIF")


def select_core(ev_tab: pd.DataFrame, mf: pd.DataFrame, min_reliability: float = 0.30, max_rho: float = 0.85,
                max_vif: float = 10.0) -> pd.DataFrame:
    """Reglas (en orden):
    1. Se excluyen las variables de resultado (obv_net, np_xg_diff): son objetivo (y), no criterio de estilo.
    2. Fiabilidad intra-partido (Spearman-Brown) ≥ min_reliability, o variable de nivel partido sin mitades
       (uso de jugadores) con estabilidad lag-1 > 0 → la métrica mide algo del partido y no ruido.
    3. Redundancia: recorriendo por fiabilidad descendente, se descarta la que tenga |ρ| > max_rho con una ya elegida.
    4. VIF iterativo: mientras alguna supere max_vif, se descarta la de mayor VIF (supuesto de no multicolinealidad).
    """
    t = ev_tab.drop(index=[v for v in OUTCOME_VARS if v in ev_tab.index]).copy()
    rel = t.fiabilidad_SB
    t["pasa_fiabilidad"] = (rel >= min_reliability) | (rel.isna() & (t.lag1 > 0))
    t["motivo"] = np.select([t.pasa_fiabilidad, rel.isna()], ["", "sin estabilidad (lag-1 ≤ 0)"], "fiabilidad baja")
    cand = t[t.pasa_fiabilidad].assign(_o=lambda x: x.fiabilidad_SB.fillna(x.lag1)).sort_values("_o", ascending=False).index
    cm = mf[list(cand)].corr("spearman").abs()
    keep = []
    for v in cand:
        clash = [k for k in keep if cm.loc[v, k] > max_rho]
        if clash:
            t.loc[v, "motivo"] = f"redundante con {clash[0]}"
        else:
            keep.append(v)
    while True:
        vf = vif(mf, keep)
        if vf.max() <= max_vif:
            break
        worst = vf.idxmax()
        t.loc[worst, "motivo"] = f"VIF {vf.max():.1f}"
        keep.remove(worst)
    t["nucleo"] = t.index.isin(keep)
    t.loc[t.nucleo, "VIF"] = vif(mf, keep)
    return t.drop(columns=["_o"], errors="ignore")


# ------------------------------------------------------------------ sensibilidad de umbrales
SENSITIVITY = {  # supuesto -> (valores, métrica afectada)
    "transition_window_s": ([10, 15, 20], "transition_poss_pct"),
    "press_high_x": ([55, 60, 65], "high_press_pct"),
    "progressive_min_gain": ([0.20, 0.25, 0.30], "prog_passes_per100"),
    "offensive_sequence_min_passes": ([2, 3, 4], None),
}


def threshold_sensitivity(ev_raw: pd.DataFrame) -> pd.DataFrame:
    """Para cada umbral, recalcula la métrica con valores alternativos y mide cuánto cambia el ORDEN de los
    partidos (ρ de Spearman con la versión base) y el nivel medio. ρ alto = la conclusión no depende del umbral."""
    rows = []
    for key, (values, metric) in SENSITIVITY.items():
        if metric is None:
            continue
        base_val = fw.A[key]
        res = {}
        try:
            for v in values:
                fw.A[key] = v
                e = F.event_flags(ev_raw)
                p = fw.possessions(e)
                res[v] = F.aggregate(e, p, ["match_id"])[metric]
        finally:
            fw.A[key] = base_val
        for v in values:
            rows.append({"supuesto": key, "valor": v, "base": v == base_val, "métrica": metric,
                         "media": res[v].mean(), "rho_vs_base": res[v].corr(res[base_val], method="spearman")})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ supuestos del modelo lineal
def linear_assumptions(mf: pd.DataFrame, split: pd.Series, targets: list[str]) -> pd.DataFrame:
    """Diagnóstico de supuestos de la regresión lineal de T1 (OLS con las mismas x, ajustado en train+val):
    - independencia de errores: Durbin-Watson (≈2 sin autocorrelación; datos temporales → riesgo)
    - homocedasticidad: Breusch-Pagan (p < 0.05 → varianza no constante)
    - normalidad de residuos: Jarque-Bera (p < 0.05 → no normal; afecta inferencia, no la predicción)
    - no multicolinealidad: VIF máximo de las x
    - linealidad: R² en entrenamiento como referencia."""
    from statsmodels.stats.diagnostic import het_breuschpagan
    from statsmodels.stats.stattools import durbin_watson, jarque_bera
    from src.modeling import CONTEXT_CAT, CONTEXT_NUM, add_inertia
    d = add_inertia(mf, targets).assign(split=lambda x: x.match_id.map(split))
    d = d[d.split != "test"]
    rows = []
    for y in targets:
        dd = d.dropna(subset=[y, f"{y}__prev5"])
        X = pd.get_dummies(dd[CONTEXT_CAT].astype(str), drop_first=True).astype(float)
        X = pd.concat([X, dd[CONTEXT_NUM + [f"{y}__prev5"]].apply(lambda s: s.fillna(s.median()))], axis=1)
        Xc = sm.add_constant(X)
        fit = sm.OLS(dd[y], Xc).fit()
        vifs = [variance_inflation_factor(Xc.values, i) for i in range(1, Xc.shape[1])]
        rows.append({"variable": y, "etiqueta": F.label(y), "R2_train": fit.rsquared,
                     "Durbin_Watson": durbin_watson(fit.resid), "BP_p": het_breuschpagan(fit.resid, Xc)[1],
                     "JB_p": jarque_bera(fit.resid)[1], "VIF_max": max(vifs),
                     "coef_local": fit.params.get("is_home_True", np.nan), "p_local": fit.pvalues.get("is_home_True", np.nan),
                     "coef_rival": fit.params["rival_ppg_prev"], "p_rival": fit.pvalues["rival_ppg_prev"],
                     "coef_inercia": fit.params[f"{y}__prev5"], "p_inercia": fit.pvalues[f"{y}__prev5"]})
    return pd.DataFrame(rows).set_index("variable")


def save(obj: dict[str, pd.DataFrame]) -> None:
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    for name, df in obj.items():
        df.to_parquet(ANALYSIS / f"{name}.parquet")

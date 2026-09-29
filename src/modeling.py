"""MODELADO — formulaciones T1–T7 (supervisadas) y U1–U3 (no supervisadas) sobre las tablas Gold.

Principios (Aprendizaje_supervisado.pdf):
- Partición TEMPORAL OFICIAL por partido: ventana del hackathon (Ap. 2021–Cl. 2025) = train, Apertura 2025 =
  validación, 2026 = prueba (incluye el cambio de entrenador). Nunca aleatoria (datos temporales,
  no independientes) y nunca por fila (posesiones/segmentos de un partido quedan juntos) → sin leakage.
- Todo preprocesamiento (escalado, one-hot, PCA, clustering) vive dentro de un Pipeline de sklearn y se
  ajusta solo con entrenamiento.
- Hiperparámetros con validación cruzada de ventana creciente (TimeSeriesSplit) dentro de train (ventana oficial);
  la familia de modelo se elige en validación (Apertura 2025) y la prueba (2026) se usa una sola vez.
- Siempre se compara contra baselines (media histórica, media móvil de 5 partidos, tasa base).
- Model card por modelo: features, hiperparámetros, fechas de entrenamiento, métricas vs baseline, hash de datos.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNetCV, Lasso, LogisticRegression, Ridge
from sklearn.metrics import (brier_score_loss, confusion_matrix, f1_score, mean_absolute_error,
                             mean_squared_error, r2_score, roc_auc_score, silhouette_score, accuracy_score)
from sklearn.model_selection import GridSearchCV, TimeSeriesSplit
from sklearn.neighbors import KNeighborsClassifier, KNeighborsRegressor, NearestNeighbors
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

from src.pipeline.config import GOLD, MODELS, OFFICIAL_END, VAL_END, get_logger

log = get_logger("modeling")

RNG = 42

# ---------------------------------------------------------------- variables
CONTEXT_NUM = ["rival_ppg_prev", "rest_days", "match_order"]
CONTEXT_CAT = ["is_home", "fase"]
STYLE_TARGETS = ["possession_time_pct", "field_tilt", "ppda", "def_action_x_mean", "high_press_pct", "pass_x_mean",
                 "prog_passes_per100", "long_pass_pct", "gk_short_goal_kick_pct", "transition_poss_pct",
                 "np_xg_per100poss", "opp_np_xg_per100poss"]
PLAYER_TARGETS = ["gini_touches", "gini_prog", "top3_obv_share", "boost_mean"]
# T3: solo métricas de PROCESO (sin xG, tiros, OBV ni derivados de resultado → evita "objetivo disfrazado")
PROCESS_X = ["gk_short_goal_kick_pct", "buildup_passes_per_seq", "buildup_success_pct", "press_resistance_own_third",
             "prog_passes_per100", "prog_carries_per100", "progression_rate", "pass_x_mean", "long_pass_pct",
             "box_touches_per100poss", "ppda", "def_action_x_mean", "high_press_pct", "high_regains_per100opp",
             "counterpress_per_loss", "opp_f3_entry_pct", "block_x_mean", "transition_poss_pct", "quick_regain_pct",
             "possession_time_pct", "field_tilt", "gini_touches", "gini_prog", "tactical_shifts"]
LEAKY_FOR_T3 = {"np_xg_per100poss", "np_xg_per_shot", "shots_per100poss", "opp_np_xg_per100poss", "opp_shots_per100poss",
                "transition_xg_per100poss", "opp_transition_xg_per100poss", "sp_xg", "opp_sp_xg", "obv_net", "np_xg_diff",
                "gini_obv", "top1_obv_share", "top3_obv_share", "boost_pct", "boost_mean", "goals_for", "goals_against"}


# ---------------------------------------------------------------- formulaciones (Cuadro tipo T/E/P)
TASKS = pd.DataFrame([
    ("T1", "Ajuste al contexto previo", "5.2", "match_features + dim_match", "12 variables de estilo",
     "localía, fuerza del rival previa, fase, descanso, orden, inercia (5 previos)", "Regresión",
     "Baseline → Ridge / LASSO → Árbol → KNN", "MAE, RMSE, R²"),
    ("T2", "Ajuste intra-partido", "5.2", "fct_segment", "estilo en el tramo",
     "estado del marcador, tramo de 15', localía, fase, fuerza del rival", "Regresión", "Baseline → Ridge → Árbol", "MAE, R²"),
    ("T3", "Principios que generan dominio", "5.1, 5.5", "match_features", "OBV neto, diferencial np xG",
     "24 métricas de proceso (sin resultado)", "Regresión", "Baseline → LASSO (+bootstrap) → Árbol → KNN", "MAE, RMSE, R²"),
    ("T3b", "Resultado", "5.5", "match_features", "G / E / P", "24 métricas de proceso", "Multiclase",
     "Clase mayoritaria → Logística softmax → Árbol", "F1 macro, exactitud, matriz de confusión"),
    ("T4", "Posesión → ocasión", "5.1", "fct_possession", "la posesión termina en tiro",
     "inicio (x, y), patrón, recuperación, marcador, minuto, localía, rival", "Binaria desbalanceada",
     "Tasa base → Logística → Árbol → KNN", "ROC-AUC, F1, Brier"),
    ("T5", "Balón parado", "5.4", "fct_set_piece", "el balón parado termina en tiro",
     "tipo, entrega, zona de destino, lado, altura", "Binaria", "Tasa base → Logística → Árbol", "ROC-AUC, Brier"),
    ("T6", "Impacto de sustituciones", "5.3", "fct_substitution", "Δ OBV neto, Δ field tilt, Δ np xG (15' después − antes)",
     "minuto, marcador, n.º de cambios, líneas que salen, localía, rival", "Regresión", "Δ=0 / Δ medio → Ridge → Árbol", "MAE, R²"),
    ("T7", "Distribución del juego", "5.3, 5.2", "match_features", "Gini de toques/progresión, top-3 OBV, potenciación",
     "contexto previo + inercia", "Regresión", "Baseline → Ridge / LASSO → Árbol → KNN", "MAE, R²"),
    ("U1", "Ejes de estilo", "5.1, 5.2", "match_features", "—", "12 variables de estilo", "Reducción de dimensión", "PCA (70 % varianza)", "varianza explicada"),
    ("U2", "Tipos de partido", "5.2", "componentes U1", "—", "—", "Clustering", "K-means (k por silhouette)", "silhouette"),
    ("U3", "Roles de jugador", "5.3", "fct_player_match (≥30')", "—", "14 acciones p90", "Clustering", "K-means (k por silhouette)", "silhouette, interpretabilidad"),
], columns=["tarea", "nombre", "reto", "unidad (Gold)", "y", "x", "tipo", "modelos", "P"]).set_index("tarea")


# ---------------------------------------------------------------- partición y utilidades
def split_by_date(dates: pd.Series) -> np.ndarray:
    """Partición oficial por fecha: ventana del hackathon (≤ OFFICIAL_END) = train; Apertura 2025 = val; 2026 = test."""
    d = pd.to_datetime(dates)
    return np.select([d <= pd.Timestamp(OFFICIAL_END), d <= pd.Timestamp(VAL_END)], ["train", "val"], "test")


def temporal_split(dim: pd.DataFrame) -> pd.Series:
    """match_id -> 'train' | 'val' | 'test' con los cortes oficiales (src/pipeline/config.py)."""
    d = dim.sort_values("match_order")
    return pd.Series(split_by_date(d.match_date), index=d.match_id.values, name="split")


def data_hash(df: pd.DataFrame) -> str:
    return hashlib.sha256(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()[:16]


def add_inertia(mf: pd.DataFrame, cols: list[str], window: int = 5) -> pd.DataFrame:
    """Media móvil de los `window` partidos ANTERIORES (shift(1)) → información disponible antes del partido."""
    mf = mf.sort_values("match_order").copy()
    for c in cols:
        mf[f"{c}__prev{window}"] = mf[c].shift(1).rolling(window, min_periods=2).mean()
    return mf


def reg_metrics(y, p) -> dict:
    y, p = np.asarray(y, float), np.asarray(p, float)
    m = ~np.isnan(y) & ~np.isnan(p)
    return {"MAE": mean_absolute_error(y[m], p[m]), "RMSE": float(np.sqrt(mean_squared_error(y[m], p[m]))),
            "R2": r2_score(y[m], p[m]), "n": int(m.sum())}


def _as_str(X):
    """Categóricas (bool, category, object) → texto; NaN se conserva para que lo impute el paso siguiente."""
    X = pd.DataFrame(X).astype(object)
    return X.where(X.isna(), X.astype(str))


def preprocessor(num: list[str], cat: list[str]) -> ColumnTransformer:
    """Estandarización + one-hot (drop='first' evita la dummy trap). Imputación con mediana de TRAIN."""
    return ColumnTransformer([
        ("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num),
        ("cat", Pipeline([("str", FunctionTransformer(_as_str, feature_names_out="one-to-one")),
                          ("imp", SimpleImputer(strategy="most_frequent")),
                          ("oh", OneHotEncoder(drop="first", handle_unknown="ignore"))]), cat),
    ])


REG_CANDIDATES = {
    "Ridge": (Ridge(), {"m__alpha": [0.1, 1, 10, 30, 100]}),
    "LASSO": (Lasso(max_iter=20000), {"m__alpha": [0.01, 0.05, 0.1, 0.5, 1.0]}),
    "Árbol": (DecisionTreeRegressor(random_state=RNG), {"m__max_depth": [2, 3, 4], "m__min_samples_leaf": [10, 20]}),
    "KNN": (KNeighborsRegressor(), {"m__n_neighbors": [5, 10, 20]}),
}
CLF_CANDIDATES = {
    "Logística": (LogisticRegression(max_iter=5000, class_weight="balanced"), {"m__C": [0.01, 0.1, 1, 10]}),
    "Árbol": (DecisionTreeClassifier(random_state=RNG, class_weight="balanced"),
              {"m__max_depth": [2, 3, 4, 6], "m__min_samples_leaf": [20, 50]}),
    "KNN": (KNeighborsClassifier(), {"m__n_neighbors": [15, 51, 101]}),
}


@dataclass
class TaskResult:
    task: str
    target: str
    table: pd.DataFrame                 # métricas por modelo y conjunto
    best_name: str
    best: object = None
    extra: dict = field(default_factory=dict)


def _fit_select(X, y, num, cat, candidates, scoring, groups_order=None):
    """Ajusta cada candidato con GridSearch + TimeSeriesSplit (X ya ordenado cronológicamente)."""
    fitted = {}
    for name, (est, grid) in candidates.items():
        pipe = Pipeline([("pre", preprocessor(num, cat)), ("m", est)])
        gs = GridSearchCV(pipe, grid, cv=TimeSeriesSplit(n_splits=4), scoring=scoring, n_jobs=-1)
        gs.fit(X, y)
        fitted[name] = gs
    return fitted


# ---------------------------------------------------------------- T1 / T7: estilo esperado según contexto previo
def task_context(mf: pd.DataFrame, split: pd.Series, targets: list[str], task="T1") -> dict[str, TaskResult]:
    mf = add_inertia(mf, targets).assign(split=lambda d: d.match_id.map(split))
    out = {}
    for y_col in targets:
        num = CONTEXT_NUM + [f"{y_col}__prev5"]
        d = mf.dropna(subset=[y_col]).sort_values("match_order")
        d["fase"] = d.fase.astype(str)
        tv, va, te = d[d.split == "train"], d[d.split == "val"], d[d.split == "test"]
        # hiperparámetros: CV temporal dentro de la ventana oficial; familia de modelo: la mejor en validación
        fitted = _fit_select(tv[num + CONTEXT_CAT], tv[y_col], num, CONTEXT_CAT, REG_CANDIDATES, "neg_mean_absolute_error")
        rows = []
        tr_mean = tv[y_col].mean()
        for part, dd in [("val", va), ("test", te)]:
            rows.append({"modelo": "Baseline: media histórica (train)", "conjunto": part, **reg_metrics(dd[y_col], np.full(len(dd), tr_mean))})
            rows.append({"modelo": "Baseline: media móvil 5", "conjunto": part,
                         **reg_metrics(dd[y_col], dd[f"{y_col}__prev5"].fillna(tr_mean))})
        val_mae = {}
        for name, gs in fitted.items():
            rows.append({"modelo": name, "conjunto": "cv(train)", "MAE": -gs.best_score_, "RMSE": np.nan, "R2": np.nan, "n": len(tv)})
            vm = reg_metrics(va[y_col], gs.predict(va[num + CONTEXT_CAT]))
            val_mae[name] = vm["MAE"]
            rows.append({"modelo": name, "conjunto": "val", **vm})
            rows.append({"modelo": name, "conjunto": "test", **reg_metrics(te[y_col], gs.predict(te[num + CONTEXT_CAT]))})
        tab = pd.DataFrame(rows)
        best = min(val_mae, key=val_mae.get)
        out[y_col] = TaskResult(task, y_col, tab, best, fitted[best].best_estimator_,
                                {"features": num + CONTEXT_CAT, "params": fitted[best].best_params_,
                                 "coef": _linear_coefs(fitted["Ridge"].best_estimator_)})
    return out


def _linear_coefs(pipe) -> pd.Series:
    names = pipe.named_steps["pre"].get_feature_names_out()
    return pd.Series(pipe.named_steps["m"].coef_, index=[n.split("__", 1)[1] for n in names])


def _linear_coefs_clf(pipe) -> pd.Series:
    names = pipe.named_steps["pre"].get_feature_names_out()
    return pd.Series(pipe.named_steps["m"].coef_[0], index=[n.split("__", 1)[1] for n in names])


# ---------------------------------------------------------------- T2: ajuste intra-partido (segmentos)
SEG_TARGETS = ["possession_time_pct", "field_tilt", "pass_x_mean", "def_action_x_mean", "high_press_pct", "long_pass_pct"]


def task_segments(seg: pd.DataFrame, split: pd.Series) -> dict[str, TaskResult]:
    seg = seg.assign(split=seg.match_id.map(split), minute_bin=seg.minute_bin.astype(str), fase=seg.fase.astype(str))
    seg = seg[seg.duration_min >= 3].sort_values(["match_order", "minute_bin"])
    num, cat = ["rival_ppg_prev"], ["game_state", "minute_bin", "is_home", "fase"]
    out = {}
    for y_col in SEG_TARGETS:
        d = seg.dropna(subset=[y_col])
        tv, te = d[d.split == "train"], d[d.split == "test"]
        cands = {k: REG_CANDIDATES[k] for k in ["Ridge", "Árbol"]}
        fitted = _fit_select(tv[num + cat], tv[y_col], num, cat, cands, "neg_mean_absolute_error")
        base = tv[y_col].mean()
        rows = [{"modelo": "Baseline: media", "conjunto": "test", **reg_metrics(te[y_col], np.full(len(te), base))}]
        for name, gs in fitted.items():
            rows.append({"modelo": name, "conjunto": "test", **reg_metrics(te[y_col], gs.predict(te[num + cat]))})
        out[y_col] = TaskResult("T2", y_col, pd.DataFrame(rows), "Ridge", fitted["Ridge"].best_estimator_,
                                {"coef": _linear_coefs(fitted["Ridge"].best_estimator_), "tree": fitted["Árbol"].best_estimator_,
                                 "features": num + cat})
    return out


# ---------------------------------------------------------------- T3: principios que generan dominio
def task_dominance(mf: pd.DataFrame, split: pd.Series, targets=("obv_net", "np_xg_diff")) -> dict[str, TaskResult]:
    assert not set(PROCESS_X) & LEAKY_FOR_T3, "T3 contiene variables derivadas del resultado"
    d = mf.assign(split=mf.match_id.map(split)).sort_values("match_order")
    out = {}
    for y_col in targets:
        dd = d.dropna(subset=[y_col])
        tv, te = dd[dd.split == "train"], dd[dd.split == "test"]
        cands = {"LASSO": REG_CANDIDATES["LASSO"], "Árbol": REG_CANDIDATES["Árbol"], "KNN": REG_CANDIDATES["KNN"]}
        fitted = _fit_select(tv[PROCESS_X], tv[y_col], PROCESS_X, [], cands, "neg_mean_absolute_error")
        rows = [{"modelo": "Baseline: media", "conjunto": "test", **reg_metrics(te[y_col], np.full(len(te), tv[y_col].mean()))}]
        for name, gs in fitted.items():
            rows.append({"modelo": name, "conjunto": "test", **reg_metrics(te[y_col], gs.predict(te[PROCESS_X]))})
        # estabilidad de la selección LASSO (bootstrap sobre train+val)
        rng = np.random.default_rng(RNG)
        lasso = fitted["LASSO"].best_estimator_
        sel = []
        for _ in range(100):
            idx = rng.integers(0, len(tv), len(tv))
            m = clone(lasso)
            m.fit(tv.iloc[idx][PROCESS_X], tv.iloc[idx][y_col])
            sel.append(_linear_coefs(m) != 0)
        stab = pd.concat(sel, axis=1).mean(1).rename("pct_seleccion")
        out[y_col] = TaskResult("T3", y_col, pd.DataFrame(rows), "LASSO", lasso,
                                {"coef": _linear_coefs(lasso), "stability": stab, "features": PROCESS_X})
    return out


def task_result(mf: pd.DataFrame, split: pd.Series) -> TaskResult:
    """T3b: G/E/P con métricas de proceso (softmax multinomial vs árbol)."""
    d = mf.assign(split=mf.match_id.map(split)).dropna(subset=["result"]).sort_values("match_order")
    tv, te = d[d.split == "train"], d[d.split == "test"]
    cands = {"Logística softmax": (LogisticRegression(max_iter=5000, class_weight="balanced"), {"m__C": [0.01, 0.1, 1]}),
             "Árbol": CLF_CANDIDATES["Árbol"]}
    fitted = _fit_select(tv[PROCESS_X], tv.result, PROCESS_X, [], cands, "f1_macro")
    maj = tv.result.mode()[0]
    rows = [{"modelo": f"Baseline: clase mayoritaria ({maj})", "accuracy": accuracy_score(te.result, [maj] * len(te)),
             "F1_macro": f1_score(te.result, [maj] * len(te), average="macro")}]
    cms = {}
    for name, gs in fitted.items():
        p = gs.predict(te[PROCESS_X])
        rows.append({"modelo": name, "accuracy": accuracy_score(te.result, p), "F1_macro": f1_score(te.result, p, average="macro")})
        cms[name] = pd.DataFrame(confusion_matrix(te.result, p, labels=["W", "D", "L"]), index=["W", "D", "L"], columns=["W", "D", "L"])
    return TaskResult("T3b", "result", pd.DataFrame(rows), "Logística softmax", fitted["Logística softmax"].best_estimator_,
                      {"confusion": cms, "n_test": len(te)})


# ---------------------------------------------------------------- T4 / T5: clasificación binaria
POSS_NUM = ["start_x", "start_y_abs", "rival_ppg_prev", "score_diff_c"]
POSS_CAT = ["play_pattern", "regain", "minute_bin", "is_home", "start_type_c"]


def _binary_eval(fitted, te_X, te_y, base_rate) -> pd.DataFrame:
    rows = [{"modelo": "Baseline: tasa base", "ROC_AUC": 0.5, "PR_AUC(prevalencia)": base_rate,
             "F1": np.nan, "Brier": brier_score_loss(te_y, np.full(len(te_y), base_rate))}]
    for name, gs in fitted.items():
        pr = gs.predict_proba(te_X)[:, 1]
        rows.append({"modelo": name, "ROC_AUC": roc_auc_score(te_y, pr), "PR_AUC(prevalencia)": np.nan,
                     "F1": f1_score(te_y, pr >= 0.5), "Brier": brier_score_loss(te_y, pr)})
    return pd.DataFrame(rows)


def task_possession(poss: pd.DataFrame, dim: pd.DataFrame, split: pd.Series) -> TaskResult:
    """T4: ¿la posesión del América termina en tiro? Solo información AL INICIO de la posesión."""
    p = poss[poss.is_team].merge(dim[["match_id", "match_order", "is_home", "rival_ppg_prev"]], on="match_id")
    p = p.assign(split=p.match_id.map(split), start_y_abs=(p.start_y - 40).abs(), score_diff_c=p.score_diff.clip(-2, 2),
                 minute_bin=p.minute_bin.astype(str), regain=p.regain.astype(str),
                 start_type_c=p.start_type.where(p.start_type.isin(["Pass", "Ball Recovery", "Carry", "Interception", "Duel", "Ball Receipt*"]), "Otro"))
    p = p.dropna(subset=["start_x"]).sort_values(["match_order", "possession"])
    tv, te = p[p.split == "train"], p[p.split == "test"]
    fitted = _fit_select(tv[POSS_NUM + POSS_CAT], tv.shot, POSS_NUM, POSS_CAT, CLF_CANDIDATES, "roc_auc")
    tab = _binary_eval(fitted, te[POSS_NUM + POSS_CAT], te.shot, tv.shot.mean())
    return TaskResult("T4", "shot", tab, "Logística", fitted["Logística"].best_estimator_,
                      {"coef": _linear_coefs_clf(fitted["Logística"].best_estimator_),
                       "fitted": fitted, "test": te, "features": POSS_NUM + POSS_CAT})


SP_CAT = ["kind", "delivery", "target_zone", "side", "pass_height"]


def task_set_pieces(sp: pd.DataFrame, split: pd.Series, own: bool = True) -> TaskResult:
    """T5: ¿el balón parado termina en tiro? own=True a favor, False en contra."""
    s = sp[sp.is_team == own].assign(split=lambda d: d.match_id.map(split), pass_height=lambda d: d.pass_height.fillna("NA"))
    s = s.merge(pd.Series(split).rename("s2"), left_on="match_id", right_index=True)
    s = s.assign(order=s.match_id.map(pd.Series(range(len(split)), index=split.index))).sort_values(["order", "possession"])
    tv, te = s[s.split == "train"], s[s.split == "test"]
    cands = {k: CLF_CANDIDATES[k] for k in ["Logística", "Árbol"]}
    fitted = _fit_select(tv[SP_CAT], tv.shot, [], SP_CAT, cands, "roc_auc")
    tab = _binary_eval(fitted, te[SP_CAT], te.shot, tv.shot.mean())
    rates = s.groupby(["kind", "target_zone"]).agg(jugadas=("shot", "size"), pct_tiro=("shot", "mean"), xg=("xg", "sum"))
    return TaskResult("T5" + ("_favor" if own else "_contra"), "shot", tab, "Logística", fitted["Logística"].best_estimator_,
                      {"rates": rates})


# ---------------------------------------------------------------- T6: impacto de sustituciones
SUB_TARGETS = ["d_obv_net", "d_field_tilt", "d_np_xg_diff"]


def task_substitutions(subs: pd.DataFrame, dim: pd.DataFrame, split: pd.Series) -> dict[str, TaskResult]:
    s = subs.merge(dim[["match_id", "match_order", "is_home", "rival_ppg_prev"]], on="match_id")
    s = s.assign(split=s.match_id.map(split), score_diff_c=s.score_diff.clip(-2, 2)).sort_values(["match_order", "minute"])
    s = s[(s.dur_antes_min >= 5) & (s.dur_despues_min >= 5)]
    num, cat = ["minute", "score_diff_c", "n_subs", "n_off_att", "n_off_def", "rival_ppg_prev"], ["is_home"]
    out = {}
    for y_col in SUB_TARGETS:
        d = s.dropna(subset=[y_col])
        tv, te = d[d.split == "train"], d[d.split == "test"]
        cands = {k: REG_CANDIDATES[k] for k in ["Ridge", "Árbol"]}
        fitted = _fit_select(tv[num + cat], tv[y_col], num, cat, cands, "neg_mean_absolute_error")
        rows = [{"modelo": "Baseline: sin cambio (Δ=0)", "conjunto": "test", **reg_metrics(te[y_col], np.zeros(len(te)))},
                {"modelo": "Baseline: Δ medio", "conjunto": "test", **reg_metrics(te[y_col], np.full(len(te), tv[y_col].mean()))}]
        for name, gs in fitted.items():
            rows.append({"modelo": name, "conjunto": "test", **reg_metrics(te[y_col], gs.predict(te[num + cat]))})
        out[y_col] = TaskResult("T6", y_col, pd.DataFrame(rows), "Ridge", fitted["Ridge"].best_estimator_,
                                {"coef": _linear_coefs(fitted["Ridge"].best_estimator_),
                                 "by_state": d.groupby("game_state")[y_col].agg(["mean", "median", "size"])})
    return out


# ---------------------------------------------------------------- U1 / U2 / U3
def style_space(mf: pd.DataFrame, split: pd.Series, cols: list[str], k_range=range(2, 7)) -> dict:
    """U1: PCA sobre variables núcleo (ajustado en train). U2: K-means sobre componentes (k por silhouette)."""
    d = mf.assign(split=mf.match_id.map(split))
    tr = d[d.split == "train"]
    pre = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]).fit(tr[cols])
    pca = PCA(random_state=RNG).fit(pre.transform(tr[cols]))
    n_comp = int(np.searchsorted(np.cumsum(pca.explained_variance_ratio_), 0.70) + 1)
    pca = PCA(n_components=n_comp, random_state=RNG).fit(pre.transform(tr[cols]))
    Z = pca.transform(pre.transform(d[cols]))
    sil = {k: silhouette_score(Z[d.split == "train"], KMeans(k, n_init=20, random_state=RNG).fit_predict(Z[d.split == "train"]))
           for k in k_range}
    k_best = max(sil, key=sil.get)
    km = KMeans(k_best, n_init=20, random_state=RNG).fit(Z[d.split == "train"])
    scores = pd.DataFrame(Z, columns=[f"PC{i + 1}" for i in range(n_comp)], index=d.match_id)
    scores["tipo_partido"] = km.predict(Z)
    loadings = pd.DataFrame(pca.components_.T, index=cols, columns=scores.columns[:n_comp])
    nn = NearestNeighbors(n_neighbors=4).fit(Z)
    return {"pre": pre, "pca": pca, "kmeans": km, "scores": scores, "loadings": loadings,
            "explained": pca.explained_variance_ratio_, "silhouette": sil, "k": k_best, "nn": nn, "cols": cols}


ROLE_COLS = ["np_xg_p90", "xa_p90", "touches_p90", "pressures_p90", "prog_actions_p90", "deep_progressions_p90",
             "passes_p90", "ball_recoveries_p90", "tackles_p90", "interceptions_p90", "dribbles_p90",
             "obv_pass_p90", "obv_dribble_carry_p90", "obv_def_p90"]


def player_roles(pm: pd.DataFrame, split: pd.Series, k_range=range(4, 10)) -> dict:
    """U3: roles de jugador = clusters de perfiles p90 (jugador-partido, ≥30', sin porteros), ajustado en train."""
    d = pm[(pm.minutes >= 30) & (pm.position_group != "Portero")].assign(split=lambda x: x.match_id.map(split))
    tr = d[d.split == "train"]
    pre = Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]).fit(tr[ROLE_COLS])
    Xtr = pre.transform(tr[ROLE_COLS])
    sil = {k: silhouette_score(Xtr, KMeans(k, n_init=10, random_state=RNG).fit_predict(Xtr), sample_size=3000, random_state=RNG)
           for k in k_range}
    k = max(sil, key=sil.get)
    km = KMeans(k, n_init=20, random_state=RNG).fit(Xtr)
    d = d.assign(role=km.predict(pre.transform(d[ROLE_COLS])))
    centroids = pd.DataFrame(km.cluster_centers_, columns=ROLE_COLS)
    comp = pd.crosstab(d.role, d.position_group, normalize="index").round(2)
    return {"pre": pre, "kmeans": km, "k": k, "silhouette": sil, "assign": d, "centroids": centroids, "composition": comp}


# ---------------------------------------------------------------- simulación del resultado (reto §6)
def simulate_match(shots: pd.DataFrame, team: str, n: int = 10000, seed: int = RNG) -> dict:
    """Cada tiro es un Bernoulli(xG); se simulan n repeticiones del partido 'con lo ocurrido'."""
    rng = np.random.default_rng(seed)
    s = shots[shots.period < 5]
    xa, xb = s[s.team == team].shot_statsbomb_xg.values, s[s.team != team].shot_statsbomb_xg.values
    ga = (rng.random((n, len(xa))) < xa).sum(1) if len(xa) else np.zeros(n)
    gb = (rng.random((n, len(xb))) < xb).sum(1) if len(xb) else np.zeros(n)
    return {"P(G)": float((ga > gb).mean()), "P(E)": float((ga == gb).mean()), "P(P)": float((ga < gb).mean()),
            "xG_propio": float(xa.sum()), "xG_rival": float(xb.sum())}


# ---------------------------------------------------------------- model cards
def save_card(name: str, model, meta: dict, data: pd.DataFrame) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODELS / f"{name}.joblib")
    card = {"name": name, "created_at": datetime.now(timezone.utc).isoformat(), "data_hash": data_hash(data), **meta}
    (MODELS / f"{name}.json").write_text(json.dumps(card, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load_gold():
    g = {n: pd.read_parquet(GOLD / f"{n}.parquet") for n in
         ["dim_match", "match_features", "fct_possession", "fct_segment", "fct_set_piece", "fct_substitution", "fct_player_match"]}
    g["split"] = temporal_split(g["dim_match"])
    return g


def _mae(tab: pd.DataFrame, model: str) -> float:
    r = tab[(tab.modelo == model) & (tab.get("conjunto", "test") == "test")]
    return float(r.MAE.iloc[0])


def _reg_card(name: str, r: TaskResult, baseline: str | list[str], data: pd.DataFrame, dates: list[str]) -> None:
    """Model card de regresión. `beats_baseline` se evalúa en la prueba temporal (usada una sola vez) contra el
    MEJOR de los baselines indicados (criterio conservador: el modelo debe ganarle al más difícil)."""
    baselines = [baseline] if isinstance(baseline, str) else baseline
    maes = {b: _mae(r.table, b) for b in baselines}
    baseline = min(maes, key=maes.get)
    best, base = _mae(r.table, r.best_name), maes[baseline]
    save_card(name, r.best, {"task": r.task, "target": r.target, "model": r.best_name,
                             "features": r.extra.get("features"), "params": r.extra.get("params"),
                             "train_dates": dates, "baseline": baseline, "test_MAE": best, "baseline_MAE": base,
                             "beats_baseline": bool(best < base)}, data)


def train_all() -> dict:
    """Entrena las versiones base de T1–T7 y U1–U3 y guarda una model card por modelo.

    El registro es deliberadamente mínimo (joblib + json): la ficha usa T1 y U1/U2; el resto documenta la
    formulación y su desempeño frente al baseline para el reporte. Un modelo que NO supera al baseline se
    guarda igual pero marcado (beats_baseline=false) y la ficha debe preferir el baseline en ese caso."""
    g = load_gold()
    mf, split, dim = g["match_features"], g["split"], g["dim_match"]
    fit_ids = split[split == "train"].index
    dates = [str(dim.match_date.min().date()), str(dim[dim.match_id.isin(fit_ids)].match_date.max().date())]
    out = {}

    out["T1"] = task_context(mf, split, STYLE_TARGETS)
    for y_col, r in out["T1"].items():
        _reg_card(f"T1_{y_col}", r, ["Baseline: media móvil 5", "Baseline: media histórica (train)"], mf, dates)
    out["T7"] = task_context(mf, split, PLAYER_TARGETS, task="T7")
    for y_col, r in out["T7"].items():
        _reg_card(f"T7_{y_col}", r, ["Baseline: media móvil 5", "Baseline: media histórica (train)"], mf, dates)
    out["T2"] = task_segments(g["fct_segment"], split)
    for y_col, r in out["T2"].items():
        _reg_card(f"T2_{y_col}", r, "Baseline: media", g["fct_segment"], dates)
    out["T3"] = task_dominance(mf, split)
    for y_col, r in out["T3"].items():
        _reg_card(f"T3_{y_col}", r, "Baseline: media", mf, dates)
    out["T6"] = task_substitutions(g["fct_substitution"], dim, split)
    for y_col, r in out["T6"].items():
        _reg_card(f"T6_{y_col}", r, "Baseline: Δ medio", g["fct_substitution"], dates)

    r = out["T3b"] = task_result(mf, split)
    t = r.table.set_index("modelo")
    save_card("T3b_result", r.best, {"task": "T3b", "target": "result", "model": r.best_name, "features": PROCESS_X,
                                     "train_dates": dates, "test_F1_macro": float(t.loc[r.best_name, "F1_macro"]),
                                     "baseline_F1_macro": float(t.F1_macro.iloc[0]),
                                     "beats_baseline": bool(t.loc[r.best_name, "F1_macro"] > t.F1_macro.iloc[0])}, mf)
    for key, r in [("T4", task_possession(g["fct_possession"], dim, split)),
                   ("T5_favor", task_set_pieces(g["fct_set_piece"], split, True)),
                   ("T5_contra", task_set_pieces(g["fct_set_piece"], split, False))]:
        out[key] = r
        t = r.table.set_index("modelo")
        auc = float(t.loc[r.best_name, "ROC_AUC"])
        save_card(f"{key}_shot", r.best, {"task": r.task, "target": "shot", "model": r.best_name, "train_dates": dates,
                                          "test_ROC_AUC": auc, "baseline_ROC_AUC": 0.5,
                                          "test_Brier": float(t.loc[r.best_name, "Brier"]),
                                          "baseline_Brier": float(t.Brier.iloc[0]),
                                          # discrimina mejor que el azar; el Brier peor que la tasa base se debe a
                                          # class_weight="balanced" (probabilidades no calibradas) → no usar como probabilidad cruda
                                          "beats_baseline": bool(auc > 0.55),
                                          "calibrated": bool(t.loc[r.best_name, "Brier"] < t.Brier.iloc[0])}, g["fct_set_piece"])

    space = out["U1U2"] = style_space(mf, split, STYLE_TARGETS)
    save_card("U1U2_style_space", {k: space[k] for k in ["pre", "pca", "kmeans", "nn", "cols"]},
              {"task": "U1/U2", "train_dates": dates, "k": space["k"], "explained": list(space["explained"]),
               "silhouette": space["silhouette"]}, mf)
    roles = out["U3"] = player_roles(g["fct_player_match"], split)
    save_card("U3_player_roles", {k: roles[k] for k in ["pre", "kmeans"]},
              {"task": "U3", "train_dates": dates, "k": roles["k"], "features": ROLE_COLS,
               "silhouette": roles["silhouette"]}, g["fct_player_match"])
    log.info(f"Modelos base entrenados: {len(list(MODELS.glob('*.json')))} model cards")
    return out


def score(match_ids=None) -> pd.DataFrame:
    """Scoring en batch: estilo esperado (T1) vs observado, posición en el mapa de estilo, tipo de partido,
    partidos similares y probabilidad simulada del resultado. Escribe data/gold/scores/match_scores.parquet."""
    from src.pipeline.silver import load_events
    g = load_gold()
    mf = add_inertia(g["match_features"], STYLE_TARGETS)
    mf["fase"] = mf.fase.astype(str)
    ids = match_ids or mf.match_id.tolist()
    out = mf[mf.match_id.isin(ids)][["match_id"]].copy().set_index("match_id")
    for y_col in STYLE_TARGETS:
        f = MODELS / f"T1_{y_col}.joblib"
        if f.exists():
            card = json.loads((MODELS / f"T1_{y_col}.json").read_text(encoding="utf-8"))
            model = joblib.load(f)
            sub = mf[mf.match_id.isin(ids)]
            if card.get("beats_baseline", True):
                pred, src = model.predict(sub[card["features"]]), card["model"]
            else:  # el modelo no supera al mejor baseline en prueba → la ficha usa ese baseline
                train_mean = mf[mf.match_id.map(g["split"]) == "train"][y_col].mean()
                src = card.get("baseline", "Baseline: media móvil 5")
                pred = (np.full(len(sub), train_mean) if "histórica" in src
                        else sub[f"{y_col}__prev5"].fillna(train_mean).values)
            out[f"{y_col}__esperado"] = pd.Series(pred, index=sub.match_id)
            out[f"{y_col}__fuente"] = src
            out[f"{y_col}__observado"] = sub.set_index("match_id")[y_col]
    space = joblib.load(MODELS / "U1U2_style_space.joblib")
    Z = space["pca"].transform(space["pre"].transform(mf[space["cols"]]))
    zdf = pd.DataFrame(Z, index=mf.match_id, columns=[f"PC{i + 1}" for i in range(Z.shape[1])])
    out = out.join(zdf).join(pd.Series(space["kmeans"].predict(Z), index=mf.match_id, name="tipo_partido"))
    dist, idx = space["nn"].kneighbors(Z)
    sim = pd.Series([[mf.match_id.iloc[j] for j in row[1:]] for row in idx], index=mf.match_id, name="similares")
    out = out.join(sim)
    ev = load_events(columns=["match_id", "team", "type", "period", "shot_statsbomb_xg"])
    shots = ev[ev.type == "Shot"]
    simu = pd.DataFrame({m: simulate_match(shots[shots.match_id == m], "América") for m in out.index}).T
    out = out.join(simu).reset_index()
    (GOLD / "scores").mkdir(exist_ok=True)
    path = GOLD / "scores" / "match_scores.parquet"
    if path.exists() and match_ids:  # incremental: reemplaza solo los partidos re-evaluados
        prev = pd.read_parquet(path)
        out = pd.concat([prev[~prev.match_id.isin(out.match_id)], out], ignore_index=True)
    out.to_parquet(path, index=False)
    log.info(f"Scores: {len(out)} partidos")
    return out

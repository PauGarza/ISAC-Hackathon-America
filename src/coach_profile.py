"""ADN DEL ENTRENADOR — perfil de estilo de cualquier entrenador de la Liga MX frente a la liga.

Unidad: entrenador × equipo (un "periodo"; p. ej. Almada-Pachuca y Almada-América son dos periodos).
Fuente: data/gold/fct_team_match_league.parquet (team-match-stats de TODA la liga + contexto sin leakage).

1. Ejes del ADN (PROFILE_AXES): 8 rasgos de juego; cada eje = media de z-scores de 2–4 métricas con signo
   orientado a "más = más de ese rasgo". Los z se calculan con la liga en la ventana oficial (train).
2. Perfil AJUSTADO por contexto: a cada eje se le quita el efecto del rival y de la localía (OLS con efectos
   fijos del rival, ajustado en train). Así el perfil es el estilo del entrenador, no a quién enfrentó.
3. Percentil de liga: el promedio de un entrenador en cada eje se ubica entre los periodos de la liga con
   ≥ MIN_MATCHES partidos en la ventana oficial (0–100; 50 = entrenador típico de la liga).
4. Consistencia, contexto, evolución, similitud, Índice de Encaje con la identidad del América y validación
   (¿el ADN reconoce al entrenador en partidos que nunca vio?).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.pipeline.config import GOLD, TEAM

MIN_MATCHES = 15
RNG = 42

# eje -> (métricas con signo, explicación en lenguaje de juego)
PROFILE_AXES = {
    "Control del balón": ({"possession": 1, "pass_completion": 1, "time_in_control": 1},
                          "Cuánto tiempo tiene el balón y qué tan seguro lo circula."),
    "Verticalidad": ({"directness": 1, "pace_towards_goal": 1, "avg_team_possession_directness": 1},
                     "Qué tan rápido y directo va hacia la portería rival en lugar de elaborar."),
    "Llegada al área": ({"deep_progressions": 1, "deep_completions": 1, "passes_inside_box": 1},
                        "Cuántas veces pisa el último tercio y el área rival con el balón."),
    "Presión alta": ({"ppda": -1, "fhalf_pressures_ratio": 1, "defensive_distance": 1, "aggression": 1},
                     "Qué tan arriba y qué tan intenso intenta recuperar (menos pases permite al rival)."),
    "Reacción tras pérdida": ({"counterpressures": 1, "counterpressure_regains": 1},
                              "Cuánto presiona justo después de perder el balón y cuánto recupera así."),
    "Peligro generado": ({"np_xg": 1, "np_xg_per_shot": 1, "obv": 1},
                         "Calidad y cantidad de las ocasiones que crea."),
    "Solidez defensiva": ({"np_xg_conceded": -1, "deep_progressions_conceded": -1, "obv_conceded": -1},
                          "Qué tan poco peligro y qué tan pocas llegadas concede."),
    "Balón parado": ({"sp_xg": 1, "xg_per_sp": 1, "sp_xg_conceded": -1},
                     "Peligro a favor en jugadas a balón parado, menos el que concede."),
}
AXES = list(PROFILE_AXES)
SHORT_COACH = {"Santiago Hernán Solari Poggio": "Solari", "Fernando Ortiz": "Ortiz", "André Soares Jardine": "Jardine",
               "Diego Alberto Cervantes Chávez": "Cervantes", "Jorge Guillermo Almada Álves": "Almada"}


KNOWN_AS = {"Renato Manuel Alves Paiva": "Renato Paiva"}  # nombres portugueses: se conoce por el último apellido


def short(name: str) -> str:
    """Nombre corto: los técnicos del América por apellido; el resto, nombre + primer apellido."""
    if name in SHORT_COACH:
        return SHORT_COACH[name]
    return display_name(name)


def display_name(name: str) -> str:
    """'Víctor Manuel Vucetich Rojas' → 'Víctor Vucetich'; 'Ariel Enrique Holan' → 'Ariel Holan'."""
    if name in KNOWN_AS:
        return KNOWN_AS[name]
    t = str(name).split()
    if len(t) <= 2:
        return " ".join(t)
    return f"{t[0]} {t[-2]}" if len(t) >= 4 else f"{t[0]} {t[-1]}"


def label(coach_team: str) -> str:
    m, _, team = coach_team.partition(" · ")
    return f"{short(m)} ({team})"


# ------------------------------------------------------------------ ejes
def load_league() -> pd.DataFrame:
    return pd.read_parquet(GOLD / "fct_team_match_league.parquet")


def axis_scores(tml: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """z-score de cada métrica con la liga en train; eje = media de z con signo. Devuelve ejes por fila y refs."""
    tr = tml[tml.split == "train"]
    refs, out = {}, pd.DataFrame(index=tml.index)
    for ax, (metrics, _) in PROFILE_AXES.items():
        zs = []
        for m, sign in metrics.items():
            col = f"team_match_{m}"
            mu, sd = tr[col].mean(), tr[col].std()
            refs[col] = (mu, sd)
            zs.append(sign * (tml[col] - mu) / sd)
        out[ax] = pd.concat(zs, axis=1).mean(axis=1)
    return out, refs


def adjust_context(tml: pd.DataFrame, axes: pd.DataFrame) -> pd.DataFrame:
    """Quita a cada eje el efecto del rival (efecto fijo) y de la localía, estimado SOLO con train.
    Rivales sin partidos en train (ascendidos) → efecto 0."""
    tr = tml.split == "train"
    enc = OneHotEncoder(handle_unknown="ignore", drop=None).fit(tml.loc[tr, ["opponent"]])
    X = np.hstack([enc.transform(tml[["opponent"]]).toarray(), tml[["is_home"]].astype(float).values])
    adj = pd.DataFrame(index=axes.index)
    for ax in AXES:
        ok = tr & axes[ax].notna()
        lr = LinearRegression().fit(X[ok.values], axes.loc[ok, ax])
        effect = X @ lr.coef_  # efecto del contexto (sin intercepto)
        adj[ax] = axes[ax] - (effect - effect[ok.values].mean())
    return adj


def build_match_axes(tml: pd.DataFrame | None = None) -> pd.DataFrame:
    """Tabla por equipo-partido con ejes crudos (raw__) y ajustados (adj__) + contexto."""
    tml = load_league() if tml is None else tml
    raw, _ = axis_scores(tml)
    adj = adjust_context(tml, raw)
    keep = ["match_id", "match_date", "torneo", "fase", "split", "team_name", "opponent", "is_home", "manager",
            "coach_team", "rival_ppg_prev", "goals_for", "goals_against"]
    return pd.concat([tml[keep], raw.add_prefix("raw__"), adj.add_prefix("adj__")], axis=1)


# ------------------------------------------------------------------ perfiles
def coach_profiles(ma: pd.DataFrame, kind: str = "adj", period: str | None = "train",
                   min_matches: int = MIN_MATCHES) -> pd.DataFrame:
    """Media por entrenador × equipo de cada eje (periodo = 'train', 'val', 'test' o None = todo)."""
    d = ma[ma.manager != ""]
    if period:
        d = d[d.split == period]
    cols = [f"{kind}__{a}" for a in AXES]
    g = d.groupby("coach_team")
    prof = g[cols].mean().set_axis(AXES, axis=1)
    prof["partidos"] = g.size()
    prof["manager"], prof["team"] = g.manager.first(), g.team_name.first()
    return prof[prof.partidos >= min_matches]


def to_percentile(prof: pd.DataFrame, reference: pd.DataFrame) -> pd.DataFrame:
    """Percentil de cada eje frente a los periodos de referencia (liga, train, ≥ MIN_MATCHES)."""
    out = prof.copy()
    for ax in AXES:
        ref = reference[ax].dropna().values
        out[ax] = [(ref < v).mean() * 100 + (ref == v).mean() * 50 for v in prof[ax]]
    return out


def america_profile(ma: pd.DataFrame, kind: str = "adj", min_matches: int = 5) -> pd.DataFrame:
    """Perfil de cada entrenador del América con TODOS sus partidos (incluye 2026) + n por conjunto."""
    d = ma[ma.team_name == TEAM]
    cols = [f"{kind}__{a}" for a in AXES]
    g = d.groupby("manager")
    prof = g[cols].mean().set_axis(AXES, axis=1)
    prof["partidos"] = g.size()
    prof["desde"], prof["hasta"] = g.match_date.min(), g.match_date.max()
    prof.index = [short(m) for m in prof.index]
    return prof[prof.partidos >= min_matches].sort_values("desde")


def bootstrap_ci(ma: pd.DataFrame, rows: pd.Series, kind: str = "adj", n: int = 1000, seed: int = RNG) -> pd.DataFrame:
    """IC 90 % de la media de cada eje (remuestreo de partidos). rows = máscara de los partidos del periodo."""
    rng = np.random.default_rng(seed)
    x = ma.loc[rows, [f"{kind}__{a}" for a in AXES]].values
    idx = rng.integers(0, len(x), (n, len(x)))
    means = np.nanmean(x[idx], axis=1)
    return pd.DataFrame({"lo": np.nanpercentile(means, 5, axis=0), "hi": np.nanpercentile(means, 95, axis=0)}, index=AXES)


def consistency(ma: pd.DataFrame, rows: pd.Series, kind: str = "adj") -> pd.DataFrame:
    """Rango intercuartílico por eje: bajo = identidad estable; alto = cambia mucho entre partidos."""
    x = ma.loc[rows, [f"{kind}__{a}" for a in AXES]].set_axis(AXES, axis=1)
    return pd.DataFrame({"p25": x.quantile(.25), "mediana": x.median(), "p75": x.quantile(.75),
                         "iqr": x.quantile(.75) - x.quantile(.25)})


def context_profile(ma: pd.DataFrame, rows: pd.Series, by: str, kind: str = "adj") -> pd.DataFrame:
    """Media de cada eje por contexto (is_home, fase o tercil de fuerza del rival)."""
    d = ma.loc[rows].copy()
    if by == "rival":
        q = ma[ma.split == "train"].rival_ppg_prev.quantile([1 / 3, 2 / 3]).values
        d["rival"] = np.select([d.rival_ppg_prev < q[0], d.rival_ppg_prev < q[1]], ["Débil", "Medio"], "Fuerte")
    elif by == "is_home":
        d["is_home"] = np.where(d.is_home, "Local", "Visita")
    cols = [f"{kind}__{a}" for a in AXES]
    return d.groupby(by)[cols].mean().set_axis(AXES, axis=1)


def evolution(ma: pd.DataFrame, team: str = TEAM, kind: str = "adj") -> pd.DataFrame:
    d = ma[ma.team_name == team]
    order = d.groupby("torneo").match_date.min().sort_values().index
    cols = [f"{kind}__{a}" for a in AXES]
    ev = d.groupby("torneo")[cols].mean().set_axis(AXES, axis=1).reindex(order)
    ev["entrenador"] = d.groupby("torneo").manager.agg(lambda s: ", ".join(short(m) for m in dict.fromkeys(s))).reindex(order)
    ev["partidos"] = d.groupby("torneo").size().reindex(order)
    return ev


# ------------------------------------------------------------------ similitud e identidad
def similar_coaches(prof: pd.DataFrame, target: str, k: int = 5) -> pd.DataFrame:
    """Los k periodos de entrenador más parecidos a `target` (distancia euclidiana en los ejes estandarizados)."""
    Z = (prof[AXES] - prof[AXES].mean()) / prof[AXES].std()
    d = np.sqrt(((Z - Z.loc[target]) ** 2).sum(axis=1)).drop(target).sort_values()
    return pd.DataFrame({"distancia": d.head(k), "partidos": prof.partidos.reindex(d.head(k).index)})


def club_identity(ma: pd.DataFrame, team: str = TEAM, kind: str = "adj") -> pd.Series:
    """ADN histórico del club: media de sus partidos en la ventana oficial (todos sus entrenadores)."""
    d = ma[(ma.team_name == team) & (ma.split == "train")]
    return d[[f"{kind}__{a}" for a in AXES]].mean().set_axis(AXES)


def fit_index(prof: pd.DataFrame, identity: pd.Series) -> pd.DataFrame:
    """Índice de Encaje (0–100): qué tan parecido es cada periodo de entrenador a la identidad del club.
    100 = el más parecido de la liga; se calcula como 100 × (1 − percentil de su distancia a la identidad)."""
    sd = prof[AXES].std()
    dist = np.sqrt((((prof[AXES] - identity) / sd) ** 2).sum(axis=1))
    out = pd.DataFrame({"distancia": dist, "partidos": prof.partidos})
    out["indice_encaje"] = (1 - dist.rank(pct=True)) * 100
    return out.sort_values("indice_encaje", ascending=False)


# ------------------------------------------------------------------ validación: ¿el ADN reconoce al entrenador?
def coach_classifier(ma: pd.DataFrame, min_train: int = 30, kind: str = "adj"):
    """Logística multinomial: ejes del partido → entrenador. Se entrena con TODA la liga en la ventana oficial
    (entrenadores con ≥ min_train partidos). La etiqueta es el entrenador, no el equipo: si reconoce a un
    técnico que cambió de club, el estilo sigue al entrenador y no a la plantilla."""
    cols = [f"{kind}__{a}" for a in AXES]
    tr = ma[(ma.split == "train") & (ma.manager != "")].dropna(subset=cols)
    keep = tr.manager.value_counts()
    tr = tr[tr.manager.isin(keep[keep >= min_train].index)]
    clf = Pipeline([("sc", StandardScaler()), ("m", LogisticRegression(max_iter=5000, C=1.0))]).fit(tr[cols], tr.manager)
    return clf, cols


def rank_of_true_coach(clf, cols, d: pd.DataFrame) -> pd.DataFrame:
    """Para cada partido: probabilidad del entrenador real y su posición en el ranking (1 = el más probable)."""
    d = d.dropna(subset=cols)
    P = pd.DataFrame(clf.predict_proba(d[cols]), columns=clf.classes_, index=d.index)
    known = d.manager.isin(clf.classes_)
    rank = P.rank(axis=1, ascending=False)
    out = d[["match_id", "match_date", "torneo", "split", "team_name", "manager"]].copy()
    out["conocido"] = known
    out["p_real"] = [P.loc[i, m] if k else np.nan for i, m, k in zip(d.index, d.manager, known)]
    out["rank_real"] = [rank.loc[i, m] if k else np.nan for i, m, k in zip(d.index, d.manager, known)]
    out["mas_probable"] = P.idxmax(axis=1)
    return out.join(P.add_prefix("p__"))


def topk_accuracy(ranks: pd.DataFrame, ks=(1, 3, 5)) -> pd.Series:
    r = ranks[ranks.conocido].rank_real
    return pd.Series({f"top-{k}": (r <= k).mean() for k in ks} | {"partidos": len(r),
                      "azar top-1": 1 / max(1, ranks.filter(like="p__").shape[1])})


def style_distance(ma: pd.DataFrame, reference_rows: pd.Series, rows: pd.Series, kind: str = "adj") -> pd.Series:
    """Distancia de Mahalanobis de cada partido al ADN de un entrenador (sus partidos de referencia).
    Alta = el partido no se parece a cómo juega ese entrenador (alerta de cambio de estilo)."""
    cols = [f"{kind}__{a}" for a in AXES]
    ref = ma.loc[reference_rows, cols].dropna()
    mu, cov = ref.mean().values, np.cov(ref.values.T) + np.eye(len(cols)) * 1e-6
    inv = np.linalg.inv(cov)
    x = ma.loc[rows, cols]
    diff = x.values - mu
    return pd.Series(np.sqrt(np.einsum("ij,jk,ik->i", diff, inv, diff)), index=x.index)


def coach_logodds(clf, cols, d: pd.DataFrame, a: str, b: str) -> pd.Series:
    """log(P(a) / P(b)) por partido: > 0 = el partido se parece más al ADN de `a` que al de `b`."""
    P = pd.DataFrame(clf.predict_proba(d[cols]), columns=clf.classes_, index=d.index)
    return np.log(P[a] / P[b])

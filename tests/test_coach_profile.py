"""Tests sintéticos de src/coach_profile.py (estandarización del ADN y deriva de la liga). No requieren Gold."""
import numpy as np
import pandas as pd
import pytest

from src import coach_profile as C

METRICS = [f"team_match_{m}" for mets, _ in C.PROFILE_AXES.values() for m in mets]


def league(shift: float = 0.0, seed: int = 0) -> pd.DataFrame:
    """Dos torneos de train y uno de prueba; en el 2.º y el 3.º todas las métricas suben `shift` (deriva de época)."""
    rng = np.random.default_rng(seed)
    rows = []
    for k, (torneo, split, date) in enumerate([("Apertura 2021", "train", "2021-08-01"),
                                               ("Clausura 2022", "train", "2022-02-01"),
                                               ("Clausura 2026", "test", "2026-02-01")]):
        for team in ["A", "B", "C", "D"]:
            for j in range(5):
                r = {"torneo": torneo, "split": split, "match_date": pd.Timestamp(date) + pd.Timedelta(days=j),
                     "team_name": team, "opponent": "X", "is_home": j % 2 == 0}
                r |= {m: rng.normal(10 + (shift if k else 0), 1) for m in METRICS}
                rows.append(r)
    return pd.DataFrame(rows)


def test_axis_scores_torneo_centers_each_tournament():
    t = league(shift=5.0)
    ax, refs = C.axis_scores(t, norm="torneo")
    means = ax.groupby(t.torneo).mean()
    assert np.allclose(means.values, 0, atol=1e-9)             # la deriva desaparece: cada torneo centrado en 0
    assert set(refs[METRICS[0]].index) == set(t.torneo)        # refs = media y desviación por torneo
    axv, _ = C.axis_scores(t, norm="ventana")
    # con la ventana, la prueba (época nueva) queda desplazada por la deriva
    assert axv["Peligro generado"][t.split == "test"].mean() > 1


def test_axis_scores_rejects_unknown_norm():
    with pytest.raises(ValueError):
        C.axis_scores(league(), norm="liga")


def test_league_drift_step_is_simultaneous():
    t = league(shift=5.0)
    d = C.league_drift(t, ["team_match_ppda"]).set_index("torneo")
    assert d.loc["Clausura 2022", "pct_equipos_suben"] == 100  # escalón: todos los equipos suben a la vez
    assert np.isnan(d.loc["Apertura 2021", "pct_equipos_suben"])
    assert d.loc["Clausura 2026", "muestra"] == "prueba"
    assert d.media_liga.is_monotonic_increasing

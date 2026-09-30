"""Tests del marco analítico, de las reglas anti-leakage y de la partición. Ejecutar: pytest -q"""
import numpy as np
import pandas as pd
import pytest

from src import framework as fw
from src import modeling as M
from src.pipeline.config import GOLD

GOLD_READY = (GOLD / "match_features.parquet").exists()


# ------------------------------------------------------------------ definiciones puras
def test_zones():
    assert list(fw.third(np.array([10, 50, 100]))) == ["Propio", "Medio", "Último"]
    assert list(fw.lane(np.array([5, 40, 75]))) == ["Izquierdo", "Central", "Derecho"]
    assert fw.in_box(np.array([110]), np.array([40]))[0] and not fw.in_box(np.array([95]), np.array([40]))[0]


def test_gini():
    assert fw.gini([1, 1, 1, 1]) == pytest.approx(0)
    assert fw.gini([0, 0, 0, 10]) == pytest.approx(0.75)


def test_game_state_counts_goal_after_event():
    ev = pd.DataFrame({"match_id": 1, "index": [1, 2, 3], "minute": [10, 20, 30], "second": 0, "period": 1,
                       "team": [fw.TEAM, fw.TEAM, "Rival"], "type": ["Shot", "Pass", "Pass"],
                       "shot_outcome": ["Goal", None, None]})
    out = fw.add_game_state(ev)
    assert list(out.score_diff) == [0, 1, 1]  # el gol cuenta DESPUÉS del tiro, no antes


def test_progressive_pass():
    ev = pd.DataFrame({"type": ["Pass", "Pass"], "pass_outcome": [None, None], "pass_type": [None, None],
                       "location_x": [40, 40], "location_y": [40, 40],
                       "pass_end_location_x": [80, 45], "pass_end_location_y": [40, 40]})
    assert list(fw.progressive_pass(ev)) == [True, False]


def _poss_events(rows):
    base = {"match_id": 1, "period": 1, "second": 0, "location_x": 60.0, "location_y": 40.0, "pass_type": None,
            "shot_type": None, "shot_outcome": None, "shot_statsbomb_xg": np.nan, "obv_total_net": 0.0,
            "is_transition": None}
    ev = pd.DataFrame([{**base, **r} for r in rows])
    ev["index"] = np.arange(1, len(ev) + 1)
    return ev


def test_set_piece_only_when_own_restart_opens_possession():
    """Balón parado = la posesión la abre el saque del propio equipo. La posesión del América que nace de atrapar un
    córner rival hereda "From Corner", pero no es balón parado: es una transición si llega rápido."""
    R = "Rival"
    ev = _poss_events([
        # 1: córner del rival
        {"possession": 1, "possession_team": R, "team": R, "minute": 10, "type": "Pass", "pass_type": "Corner",
         "play_pattern": "From Corner", "location_x": 120.0, "location_y": 0.0},
        # 2: el América recupera y contragolpea (hereda "From Corner") hasta tirar en 8 s
        {"possession": 2, "possession_team": fw.TEAM, "team": fw.TEAM, "minute": 10, "second": 5,
         "type": "Ball Recovery", "play_pattern": "From Corner", "location_x": 5.0},
        {"possession": 2, "possession_team": fw.TEAM, "team": fw.TEAM, "minute": 10, "second": 13, "type": "Shot",
         "play_pattern": "From Corner", "location_x": 105.0, "shot_type": "Open Play", "shot_statsbomb_xg": 0.2},
        # 3: córner del América (su propio saque abre la posesión)
        {"possession": 3, "possession_team": fw.TEAM, "team": fw.TEAM, "minute": 20, "type": "Pass",
         "pass_type": "Corner", "play_pattern": "From Corner", "location_x": 120.0, "location_y": 80.0},
        {"possession": 3, "possession_team": fw.TEAM, "team": fw.TEAM, "minute": 20, "second": 3, "type": "Shot",
         "play_pattern": "From Corner", "location_x": 112.0, "shot_type": "Open Play", "shot_statsbomb_xg": 0.1},
        # 4: tiro libre directo del América
        {"possession": 4, "possession_team": fw.TEAM, "team": fw.TEAM, "minute": 30, "type": "Shot",
         "play_pattern": "From Free Kick", "location_x": 95.0, "shot_type": "Free Kick", "shot_statsbomb_xg": 0.05},
        # 5: saque de banda del América en campo propio (no es balón parado de peligro)
        {"possession": 5, "possession_team": fw.TEAM, "team": fw.TEAM, "minute": 40, "type": "Pass",
         "pass_type": "Throw-in", "play_pattern": "From Throw In", "location_x": 30.0},
    ])
    p = fw.possessions(ev).set_index("possession")
    assert list(p.is_set_piece) == [True, False, True, True, False]
    assert p.loc[2, "transition"] and not p.loc[3, "transition"]
    assert p.loc[4, "start_shot_type"] == "Free Kick"


# ------------------------------------------------------------------ leakage y partición (requieren Gold)
@pytest.mark.skipif(not GOLD_READY, reason="Gold no construido")
def test_rival_strength_uses_only_past():
    from src.pipeline.config import SILVER
    dim = pd.read_parquet(GOLD / "dim_match.parquet")
    league = pd.read_parquet(SILVER / "league_matches.parquet")
    r = dim.sort_values("match_order").iloc[len(dim) // 2]
    later = league[(league.match_date >= r.match_date) & ((league.home_team == r.opponent) | (league.away_team == r.opponent))]
    assert len(later) > 0  # hay partidos posteriores del rival...
    assert r.rival_n_prev <= fw.A["rival_strength_window"]  # ...pero la ventana solo usa previos


@pytest.mark.skipif(not GOLD_READY, reason="Gold no construido")
def test_player_reference_is_shifted():
    pm = pd.read_parquet(GOLD / "fct_player_match.parquet").sort_values(["player_id", "match_date"])
    first = pm.groupby("player_id").head(1)
    assert first.obv_p90_ref_prev.isna().all()  # el primer partido de cada jugador no tiene referencia


@pytest.mark.skipif(not GOLD_READY, reason="Gold no construido")
def test_temporal_split_no_overlap_and_ordered():
    dim = pd.read_parquet(GOLD / "dim_match.parquet")
    s = M.temporal_split(dim)
    assert s.index.is_unique
    d = dim.set_index("match_id").join(s)
    assert d[d.split == "train"].match_date.max() < d[d.split == "val"].match_date.min()
    assert d[d.split == "val"].match_date.max() < d[d.split == "test"].match_date.min()


@pytest.mark.skipif(not GOLD_READY, reason="Gold no construido")
def test_official_split_cutoffs():
    """Entrenamiento = ventana oficial del hackathon; nada posterior al Clausura 2025 entra a train."""
    from src.pipeline.config import OFFICIAL_END, VAL_END
    dim = pd.read_parquet(GOLD / "dim_match.parquet")
    d = dim.set_index("match_id").join(M.temporal_split(dim))
    assert d[d.split == "train"].match_date.max() <= pd.Timestamp(OFFICIAL_END)
    assert d[d.split == "val"].match_date.min() > pd.Timestamp(OFFICIAL_END)
    assert d[d.split == "test"].match_date.min() > pd.Timestamp(VAL_END)


@pytest.mark.skipif(not GOLD_READY, reason="Gold no construido")
def test_inertia_is_lagged():
    mf = pd.read_parquet(GOLD / "match_features.parquet")
    d = M.add_inertia(mf, ["field_tilt"]).sort_values("match_order")
    expected = d.field_tilt.shift(1).rolling(5, min_periods=2).mean()
    assert np.allclose(d["field_tilt__prev5"].fillna(-1), expected.fillna(-1))


def test_t3_has_no_outcome_features():
    assert not set(M.PROCESS_X) & M.LEAKY_FOR_T3

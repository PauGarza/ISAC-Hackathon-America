"""Hipótesis del equipo (src/hipotesis.py) con datos sintéticos."""
import numpy as np
import pandas as pd

from src import hipotesis as H


def _df(n=60, effect=0.0, confound=False, seed=0):
    rng = np.random.default_rng(seed)
    coach = np.repeat(["A", "B"], n // 2)
    g = rng.random(n) < (np.where(coach == "A", 0.8, 0.2) if confound else 0.5)
    y = rng.normal(0, 1, n) + effect * g + (np.where(coach == "A", 3.0, 0.0) if confound else 0)
    return pd.DataFrame({"coach": coach, "rival_nivel": "Medio", "g": g, "y": y})


def test_strat_perm_detects_real_effect():
    r = H.strat_perm(_df(effect=1.5), "y", "g", n=500)
    assert r["dif"] > 1 and r["p"] < 0.01 and r["dif_sd"] > 0.5


def test_strat_perm_removes_coach_confounding():
    d = _df(n=200, effect=0.0, confound=True, seed=1)
    raw = d[d.g].y.mean() - d[~d.g].y.mean()
    r = H.strat_perm(d, "y", "g", n=500)
    assert raw > 1.0                       # sin estratos parece un efecto enorme…
    assert abs(r["dif"]) < 0.4             # …que desaparece dentro de cada técnico
    assert r["p"] > 0.05


def test_veredicto_rules():
    assert H.veredicto({"n_si": 5, "n_no": 40, "p": 0.001, "dif_sd": 1.0}) == "no alcanza"
    assert H.veredicto({"n_si": 30, "n_no": 40, "p": 0.01, "dif_sd": 0.5}) == "se sostiene"
    assert H.veredicto({"n_si": 30, "n_no": 40, "p": 0.01, "dif_sd": 0.1}) == "no cambia"   # significativo pero diminuto
    assert H.veredicto({"n_si": 30, "n_no": 40, "p": 0.40, "dif_sd": 0.5}) == "no cambia"


def test_lineas_parses_formations():
    assert H.lineas("4-2-3-1") == (4, 5, 1)
    assert H.lineas("4-4-2") == (4, 4, 2)
    assert H.lineas("3-4-3") == (3, 4, 3)


def test_formacion_str():
    assert H.formacion_str(4231) == "4-2-3-1"
    assert H.formacion_str(41212) == "4-1-2-1-2"
    assert H.formacion_str(np.nan) is None


def test_comparar_formacion_same_stratum_effect():
    """Dos formaciones en los mismos estratos: la diferencia de ocasiones por 90' es la que se construyó."""
    rows = []
    for m in range(20):
        for f, xg in [("4-4-2", 1.5), ("4-2-3-1", 1.0)]:
            rows.append({"match_id": m, "formacion": f, "coach": "A", "rival_nivel": "Medio", "game_state3": "Empatando",
                         "minutos": 45.0, "xg_f": xg / 2, "xg_c": 0.4, "tiros_f": 6, "tiros_c": 4, "claras_f": 1, "claras_c": 0,
                         "possession_time_pct": 55.0, "field_tilt": 60.0, "ppda": 12.0, "high_press_pct": 40.0,
                         "box_touches_per100poss": 50.0, "opp_f3_entry_pct": 50.0})
    r = H.comparar_formacion(pd.DataFrame(rows), "4-4-2", n_boot=50).set_index("metrica")
    assert abs(r.loc["Ocasiones a favor (xG por 90')", "dif"] - 0.5) < 1e-9
    assert r.loc["Ocasiones a favor (xG por 90')", "veredicto"] == "se sostiene"
    assert r.loc["Posesión (%)", "dif"] == 0


def test_series_liguilla_advance_and_home_leg():
    p = pd.DataFrame({
        "match_id": [1, 2, 3, 4], "match_date": pd.to_datetime(["2024-05-01", "2024-05-04", "2024-05-08", "2024-05-11"]),
        "torneo": "Clausura 2024", "fase": "Liguilla", "ronda": ["Cuartos", "Cuartos", "Semifinal", "Semifinal"],
        "coach": "Jardine", "opponent": ["X", "X", "Y", "Y"], "rival_nivel": "Fuerte", "localia": ["Visita", "Local"] * 2,
        "goals_for": [1, 2, 0, 1], "goals_against": [1, 0, 1, 1], "llego": "Semifinal",
        "xg_favor": [1.0, 1.5, 0.5, 0.8], "xg_contra": [0.7, 0.4, 1.2, 1.0], "possession_time_pct": 50.0, "ppda": 15.0,
        "field_tilt": 55.0, "xpts": 1.5})
    bp = pd.DataFrame({"match_id": [1, 3], "lado": ["A favor", "En contra"], "xg": [0.2, 0.3]})
    s = H.series_liguilla(p, bp).set_index("ronda")
    assert bool(s.loc["Cuartos", "avanzo"]) and not bool(s.loc["Semifinal", "avanzo"])
    assert s.loc["Cuartos", "global"] == "3-1" and s.loc["Cuartos", "ida"] == "1-1"
    assert bool(s.loc["Cuartos", "vuelta_en_casa"])
    assert s.loc["Cuartos", "bp_xg_favor"] == 0.2 and s.loc["Semifinal", "bp_xg_contra"] == 0.3
    assert bool(s.loc["Cuartos", "merecia"]) and not bool(s.loc["Semifinal", "merecia"])

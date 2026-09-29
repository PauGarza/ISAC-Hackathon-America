"""Tests sintéticos de src/story.py (historia de Jardine, §3.2 y §3.3). No requieren Gold. Ejecutar: pytest -q"""
import json

import numpy as np
import pandas as pd
import pytest

from src import features as F
from src import framework as fw
from src import story as S

AM, RIV = fw.TEAM, "Rival"
EV_DEFAULTS = {"match_id": 1, "period": 1, "minute": 10, "second": 0, "team": AM, "possession": 1, "possession_team": AM,
               "type": "Pass", "player_id": 10.0, "position": "Center Back", "location_x": 50.0, "location_y": 40.0,
               "pass_end_location_x": np.nan, "pass_end_location_y": np.nan, "carry_end_location_x": np.nan,
               "carry_end_location_y": np.nan, "pass_length": 10.0, "pass_type": None, "pass_outcome": None,
               "pass_recipient_id": np.nan, "pass_cross": None, "pass_cut_back": None, "pass_through_ball": None,
               "pass_technique": None, "pass_height": "Ground Pass", "under_pressure": None, "duel_type": None,
               "shot_type": None, "shot_outcome": None, "shot_statsbomb_xg": np.nan, "shot_key_pass_id": None,
               "shot_follows_dribble": None, "shot_body_part": None, "counterpress": None, "tactics": None,
               "coach": "Jardine"}


def make_ev(rows):
    """Eventos sintéticos con las columnas que usan framework/features/story; pasan por event_flags como los reales."""
    ev = pd.DataFrame([{**EV_DEFAULTS, **r} for r in rows])
    ev["index"] = np.arange(1, len(ev) + 1)
    ev["id"] = [f"e{i}" for i in ev["index"]]
    ev["t"] = ev.minute * 60 + ev.second
    return F.event_flags(ev)


def scope(n=None):
    n = n or {"Solari": 1, "Ortiz": 1, "Jardine": 2}
    return pd.DataFrame([{"match_id": i, "coach": c} for i, c in enumerate(
        [c for c, k in n.items() for _ in range(k)], start=1)])


# ------------------------------------------------------------------ utilidades
def test_zone_grid_counts_and_shares():
    d = pd.DataFrame({"coach": ["Jardine"] * 3 + ["Ortiz"], "x": [10, 15, 110, 50], "y": [5, 6, 70, 40], "xg": [.1, .2, .3, .4]})
    g = S.zone_grid(d, "x", "y", ["coach"], ("xg",))
    j = g[(g.coach == "Jardine") & (g.n > 0)].set_index(["x0", "y0"])
    assert j.loc[(0.0, 0.0), "n"] == 2 and j.loc[(0.0, 0.0), "xg"] == pytest.approx(.3)
    assert j[(j.index.get_level_values("x0") == 100) & np.isclose(j.index.get_level_values("y0"), 160 / 3)].n.iat[0] == 1
    assert g[g.coach == "Jardine"].share.sum() == pytest.approx(1)
    assert len(g) == 2 * 6 * 3  # celdas vacías incluidas (mapa completo para el HTML)


def test_per_match_and_grid_per_match():
    sc = scope({"Solari": 1, "Ortiz": 1, "Jardine": 4})
    s = pd.Series([8, 3], index=pd.Index(["Jardine", "Ortiz"], name="coach"))
    assert list(S.per_match(s, sc)) == [2, 3]
    g = pd.DataFrame({"coach": ["Jardine", "Solari"], "n": [4, 1]})
    assert list(S.grid_per_match(g, sc).por_partido) == [1, 1]


# ------------------------------------------------------------------ §3.2a salida
def test_restarts_short_long_and_receiver_group():
    ev = make_ev([
        {"pass_type": "Goal Kick", "pass_length": 12, "location_x": 6, "pass_end_location_x": 18, "pass_end_location_y": 40,
         "pass_recipient_id": 20.0, "player_id": 1.0, "position": "Goalkeeper"},
        {"type": "Ball Receipt*", "player_id": 20.0, "position": "Center Defensive Midfield"},
        {"pass_type": "Goal Kick", "pass_length": 60, "location_x": 6, "pass_end_location_x": 66, "pass_end_location_y": 10,
         "pass_outcome": "Incomplete", "player_id": 1.0, "position": "Goalkeeper"},
        {"pass_length": 40, "location_x": 10, "pass_end_location_x": 50, "pass_end_location_y": 70,
         "pass_recipient_id": 30.0, "player_id": 1.0, "position": "Goalkeeper"},
        {"type": "Ball Receipt*", "player_id": 30.0, "position": "Right Back"},
        {"pass_length": 40, "player_id": 30.0, "position": "Right Back", "pass_end_location_x": 90, "pass_end_location_y": 70},
        {"team": RIV, "pass_type": "Goal Kick", "pass_length": 10, "pass_end_location_x": 16, "pass_end_location_y": 40},
    ])
    r = S.restarts(ev)
    assert len(r) == 3  # 2 saques de meta + 1 pase del portero; no el del lateral ni el del rival
    assert list(r.kind) == ["Saque de meta", "Saque de meta", "Portero en juego"]
    assert list(r.length) == ["Corto", "Largo", "Largo"]
    assert list(r.receiver_group) == ["Medio defensivo", "Sin receptor", "Defensa"]
    rs = S.restart_summary(r, scope({"Jardine": 1})).set_index("kind")
    assert rs.loc["Saque de meta", "pct_corto"] == 50
    assert rs.loc["Saque de meta", "pct_completo_largo"] == 0


def test_restart_outcomes_join_possession():
    r = pd.DataFrame({"match_id": [1, 1], "possession": [1, 2], "coach": "Jardine", "kind": "Saque de meta",
                      "length": ["Corto", "Largo"]})
    poss = pd.DataFrame({"match_id": [1, 1], "possession": [1, 2], "max_x": [70, 40], "shot": [True, False], "xg": [.2, 0]})
    o = S.restart_outcomes(r, poss).set_index("length")
    assert o.loc["Corto", "pct_llega_campo_rival"] == 100 and o.loc["Largo", "pct_llega_campo_rival"] == 0
    assert o.loc["Corto", "xg_por_100"] == pytest.approx(20)


# ------------------------------------------------------------------ §3.2b progresión
def test_entries_final_third_and_box():
    ev = make_ev([
        {"location_x": 70, "pass_end_location_x": 85, "pass_end_location_y": 10},                  # entra al último tercio
        {"location_x": 95, "location_y": 10, "pass_end_location_x": 110, "pass_end_location_y": 40,
         "pass_cross": True},                                                                         # centro al área
        {"type": "Carry", "location_x": 98, "location_y": 40, "carry_end_location_x": 105, "carry_end_location_y": 40},
        {"location_x": 105, "location_y": 40, "pass_end_location_x": 110, "pass_end_location_y": 40},  # ya estaba en el área
        {"location_x": 70, "pass_end_location_x": 90, "pass_end_location_y": 40, "pass_outcome": "Incomplete"},
        {"team": RIV, "location_x": 70, "pass_end_location_x": 85, "pass_end_location_y": 10},
    ])
    en = S.entries(ev)
    assert en.final_third.sum() == 1 and en.box.sum() == 2
    assert set(en[en.box].method) == {"Centro", "Conducción"}
    assert en[en.final_third].lane.iat[0] == "Izquierdo"
    es = S.entry_summary(en, scope({"Jardine": 1}))
    assert es[es.entrada == "Área"].por_partido.sum() == 2


def test_progression_by_lane_shares():
    pa = pd.DataFrame({"coach": "Jardine", "action": "Pase progresivo", "end_y": [5, 40, 42, 75], "match_id": 1})
    t = S.progression_by_lane(pa, scope({"Jardine": 2})).set_index("lane")
    assert t.loc["Central", "share"] == 0.5 and t.loc["Central", "por_partido"] == 1


# ------------------------------------------------------------------ §3.2c ocasiones
def _assist_case(key: dict | None, shot: dict | None = None, prev: dict | None = None) -> str:
    kcols = ["type", "pass_type", "location_x", "pass_end_location_x", "pass_end_location_y", "pass_height",
             "pass_cut_back", "pass_cross", "pass_through_ball", "pass_technique"]
    k = pd.DataFrame([{c: None for c in kcols} | {"location_x": np.nan, "pass_end_location_x": np.nan,
                                                  "pass_end_location_y": np.nan} | (key or {})])
    sh = pd.DataFrame([{"shot_type": "Open Play", "shot_follows_dribble": None, "player_id": 9.0} | (shot or {})])
    p = pd.DataFrame([{"type": None, "player_id": np.nan, "location_x": np.nan, "location_y": np.nan,
                       "carry_end_location_x": np.nan, "carry_end_location_y": np.nan} | (prev or {})])
    return S.classify_assist(sh, k, p).iat[0]


def test_classify_assist_priorities():
    P = {"type": "Pass", "location_x": 90, "pass_end_location_x": 100, "pass_end_location_y": 40}
    assert _assist_case(None, {"shot_type": "Free Kick"}) == "Tiro libre directo"
    assert _assist_case(P | {"pass_type": "Corner", "pass_cross": True}) == "Servicio a balón parado"
    assert _assist_case(P | {"pass_cross": True}) == "Centro"
    assert _assist_case(P | {"pass_through_ball": True}) == "Filtrado"
    assert _assist_case(P) == "Otro pase"
    # pase atrás: desde la línea del área hacia atrás, raso, a la zona de peligro (aunque no tenga la bandera)
    assert _assist_case({"type": "Pass", "location_x": 115, "pass_end_location_x": 106, "pass_end_location_y": 38,
                         "pass_height": "Ground Pass"}) == "Pase atrás al área"
    assert _assist_case(P | {"pass_cut_back": True, "pass_cross": True}) == "Pase atrás al área"
    assert _assist_case(None, {"shot_follows_dribble": True}) == "Jugada individual"
    long_carry = {"type": "Carry", "player_id": 9.0, "location_x": 80, "location_y": 40, "carry_end_location_x": 95,
                  "carry_end_location_y": 40}
    assert _assist_case(None, prev=long_carry) == "Jugada individual"
    assert _assist_case(None, prev=long_carry | {"player_id": 7.0}) == "Rebote o balón suelto"  # conducción de otro
    assert _assist_case(None) == "Rebote o balón suelto"


def test_shots_origin_and_no_penalties():
    ev = make_ev([
        {"possession": 1, "location_x": 90, "pass_end_location_x": 105, "pass_end_location_y": 40, "pass_cross": True},
        {"possession": 1, "type": "Shot", "location_x": 105, "shot_statsbomb_xg": .3, "shot_outcome": "Goal",
         "shot_type": "Open Play", "shot_key_pass_id": "e1", "player_id": 9.0},
        {"possession": 2, "type": "Shot", "location_x": 108, "shot_statsbomb_xg": .78, "shot_type": "Penalty"},
        {"possession": 3, "type": "Shot", "location_x": 100, "shot_statsbomb_xg": .05, "shot_type": "Open Play"},
    ])
    poss = pd.DataFrame({"match_id": 1, "possession": [1, 2, 3], "is_set_piece": [False, False, True],
                         "transition": [True, False, False]})
    s = S.shots(ev, poss)
    assert len(s) == 2  # el penal no cuenta
    assert list(s.origin) == ["Transición", "Balón parado"]
    assert s.assist.iat[0] == "Centro" and bool(s.goal.iat[0])
    tot = S.shot_totals(s, scope({"Jardine": 1})).set_index("coach")
    assert tot.loc["Jardine", "np_xg_por_partido"] == pytest.approx(.35)
    cs = S.chance_summary(s, scope({"Jardine": 1}), "origin")
    assert cs.pct_xg.sum() == pytest.approx(100)
    g = S.shot_grid(s)
    assert g.n.sum() == 2 and g.goles.sum() == 1 and g.xg.sum() == pytest.approx(.35)


# ------------------------------------------------------------------ §3.2d red de pases
def _xi_event(mid, formation, players):
    lineup = [{"player": {"id": pid, "name": f"P{pid}"}, "position": {"id": i, "name": pos}}
              for i, (pid, pos) in enumerate(players)]
    return {"match_id": mid, "type": "Starting XI", "tactics": json.dumps({"formation": formation, "lineup": lineup})}


def test_most_used_xi_and_pass_network():
    a = [(1, "Goalkeeper"), (2, "Center Back"), (3, "Center Forward")]
    b = [(1, "Goalkeeper"), (4, "Center Back"), (3, "Center Forward")]
    rows = [_xi_event(1, 433, a), _xi_event(2, 433, a), _xi_event(3, 433, b), _xi_event(4, 352, b)]
    # partido 1: 1→2 dos veces y 2→3 una, luego un cambio; el pase posterior al cambio no cuenta
    rows += [{"match_id": 1, "minute": 5, "player_id": 1.0, "pass_recipient_id": 2.0, "location_x": 10, "pass_end_location_x": 30, "pass_end_location_y": 40},
             {"match_id": 1, "minute": 6, "player_id": 1.0, "pass_recipient_id": 2.0, "location_x": 10, "pass_end_location_x": 30, "pass_end_location_y": 40},
             {"match_id": 1, "minute": 7, "player_id": 2.0, "pass_recipient_id": 3.0, "location_x": 30, "pass_end_location_x": 90, "pass_end_location_y": 40},
             {"match_id": 1, "minute": 60, "type": "Substitution"},
             {"match_id": 1, "minute": 70, "player_id": 1.0, "pass_recipient_id": 2.0, "location_x": 10, "pass_end_location_x": 30, "pass_end_location_y": 40}]
    ev = make_ev(rows)
    lu = S.starting_lineups(ev)
    assert lu.match_id.nunique() == 4 and len(lu) == 12
    xi = S.most_used_xi(lu)
    assert xi.formation.iat[0] == "433" and xi.partidos_sistema.iat[0] == 3
    assert set(xi.player_id) == {1.0, 2.0, 3.0}  # el central 2 (2 titularidades) gana al 4 (1)
    assert not xi.position.duplicated().any() and not xi.player_id.duplicated().any()
    nodes, edges = S.pass_network(ev, lu, xi, names=pd.Series({1.0: "Portero"}))
    e = edges.set_index(["a", "b"])
    assert e.loc[(1.0, 2.0), "pases"] == 2 and e.loc[(1.0, 2.0), "partidos_juntos"] == 2
    assert e.loc[(1.0, 2.0), "pases_por_partido"] == 1
    n = nodes.set_index("player_id")
    assert n.loc[1.0, "x_media"] == pytest.approx(10) and n.loc[3.0, "x_media"] == pytest.approx(90)
    assert n.loc[1.0, "nombre"] == "Portero" and n.loc[2.0, "nombre"] == "P2"  # sin nombre corto: el completo
    assert not {"x", "y"} & set(nodes.columns)  # nodos agregados: se pueden guardar


# ------------------------------------------------------------------ §3.3 sin balón
def _poss():
    """Partido 1 del América (Jardine): pérdida → robo rival → robo propio en 3 s → transición propia."""
    return pd.DataFrame({
        "match_id": 1, "possession": [1, 2, 3, 4], "coach": "Jardine",
        "team": [AM, RIV, AM, RIV], "is_team": [True, False, True, False],
        "play_pattern": ["Regular Play"] * 4, "t_start": [0, 11, 14, 40], "t_end": [10, 13, 30, 50],
        "regain": [False, True, True, True], "transition": [False, True, True, False],
        "start_x": [30, 70, 65, 50], "start_y": [40, 20, 60, 40], "shot": [False, True, True, False],
        "xg": [0, .1, .3, 0], "t_reach_f3": [np.nan, 4, 6, np.nan], "is_set_piece": False})


def test_recoveries_and_summary():
    p = _poss()
    rec = S.recoveries(p)
    assert list(rec.x) == [65]
    rs = S.recovery_summary(rec, p, scope({"Jardine": 1})).set_index("coach")
    assert rs.loc["Jardine", "pct_campo_rival"] == 100 and rs.loc["Jardine", "por_100_pos_rivales"] == 50
    assert rs.loc["Jardine", "pct_a_transicion"] == 100


def test_transitions_and_counterpress():
    p = _poss()
    sc = scope({"Jardine": 1})
    t = S.transition_summary(p, sc).set_index(["coach", "lado"])
    assert t.loc[("Jardine", "A favor"), "transiciones"] == 1 and t.loc[("Jardine", "A favor"), "xg_por_partido"] == pytest.approx(.3)
    assert t.loc[("Jardine", "En contra"), "segundos_mediana"] == 4
    assert t.loc[("Jardine", "En contra"), "pct_de_recuperaciones"] == 50
    cp = S.counterpress_summary(p, sc).set_index("coach")
    assert cp.loc["Jardine", "losses"] == 2 and cp.loc["Jardine", "quick_regains"] == 1  # 10 → 14 s: ≤ 5 s
    st = S.transition_starts(p)
    against = st[st.lado == "En contra"]
    assert against.x.iat[0] == 50 and against.y.iat[0] == 60  # volteado a coordenadas del América


def test_league_benchmark_relative_to_tournament_and_rank():
    rows = []
    for torneo, base in [("T1", 8.0), ("T2", 12.0)]:  # la liga sube 4 pases de un torneo a otro
        for coach, delta in [("A", 0), ("B", 1), ("C", -1)]:
            rows += [{"torneo": torneo, "split": "train", "manager": coach, "team_name": AM if coach == "A" else f"E{coach}",
                      "coach_team": f"{coach} · x", "team_match_ppda": base + delta} for _ in range(2)]
    tml = pd.DataFrame(rows)
    b = S.league_benchmark(tml, cols=("team_match_ppda",), min_matches=1).set_index("manager")
    assert b.loc["A", "team_match_ppda"] == pytest.approx(0)  # igual a la liga de su torneo, pese a la época
    assert b.loc["B", "team_match_ppda"] == pytest.approx(1)
    assert b.loc["A", "coach"] == "A" and pd.isna(b.loc["B", "coach"])
    raw = S.league_benchmark(tml, cols=("team_match_ppda",), min_matches=1, relative=False).set_index("manager")
    assert raw.loc["A", "team_match_ppda"] == pytest.approx(10)
    r = S.league_rank(b.reset_index(), "team_match_ppda", coach="A")
    assert r["lugar"] == 2 and r["de"] == 3 and r["percentil"] == pytest.approx(100 / 3 + 100 / 6)
    assert S.league_rank(b.reset_index(), "team_match_ppda", coach="A", higher_is_more=False)["lugar"] == 2


# ------------------------------------------------------------------ guardar solo agregados
def test_save_story_rejects_event_level_columns(tmp_path, monkeypatch):
    monkeypatch.setattr(S, "ANALYSIS", tmp_path)
    with pytest.raises(ValueError):
        S.save_story(pd.DataFrame({"coach": ["Jardine"], "x": [10.0], "y": [40.0]}), "malo")
    with pytest.raises(ValueError):
        S.save_story(pd.DataFrame({"id": ["e1"], "xg": [.1]}), "malo")
    path = S.save_story(pd.DataFrame({"coach": ["Jardine"], "x0": [0.0], "n": [3]}), "bueno")
    out = pd.read_parquet(path)
    assert out.muestra.iat[0] == "ventana" and path.endswith("story_bueno.parquet")

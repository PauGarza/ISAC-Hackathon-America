"""Compuertas de calidad (Silver/Gold). Si una validación falla, el pipeline se detiene con un
mensaje explícito: nunca se escriben datos corruptos en silencio."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import TEAM, get_logger

log = get_logger("quality")


class QualityError(AssertionError):
    pass


def _check(cond: bool, msg: str):
    if not cond:
        log.error(f"FALLA calidad: {msg}")
        raise QualityError(msg)
    log.info(f"ok  {msg}")


def check_events(ev: pd.DataFrame, match_ids: list[int]) -> None:
    _check(set(ev.match_id.unique()) == set(match_ids), f"events cubre los {len(match_ids)} partidos de la temporada")
    _check(ev.id.is_unique, "events: id único")
    x, y = ev.get("location_x"), ev.get("location_y")
    _check(bool(((x.dropna() >= 0) & (x.dropna() <= 120)).all() and ((y.dropna() >= 0) & (y.dropna() <= 80)).all()),
           "events: coordenadas dentro de la cancha 120x80")
    shots = ev[ev.type == "Shot"]
    _check(shots.shot_statsbomb_xg.notna().all(), "events: todo tiro tiene xG")
    _check(ev.groupby("match_id").type.apply(lambda t: (t == "Starting XI").sum() == 2).all(),
           "events: cada partido tiene 2 alineaciones iniciales")


def score_from_events(ev: pd.DataFrame, team: str = TEAM) -> pd.DataFrame:
    """Goles reconstruidos (tiros convertidos + autogoles a favor), sin tanda de penales."""
    e = ev[ev.period < 5]
    goal = ((e.type == "Shot") & (e.shot_outcome == "Goal")) | (e.type == "Own Goal For")
    return pd.DataFrame({"gf": (goal & (e.team == team)).groupby(e.match_id).sum(),
                         "ga": (goal & (e.team != team)).groupby(e.match_id).sum()})


def check_silver(silver, played: pd.DataFrame) -> None:
    from .silver import load_events
    ev = load_events(columns=["id", "match_id", "period", "type", "team", "shot_outcome"])
    _check(ev.match_id.nunique() == len(played), f"events: {len(played)} partidos jugados en Silver")
    rec = score_from_events(ev).join(played.set_index("match_id")[["goals_for", "goals_against"]])
    ok = ((rec.gf == rec.goals_for) & (rec.ga == rec.goals_against)).mean()
    _check(ok == 1.0, f"marcador reconstruido == oficial en {ok:.0%} de partidos")
    lu = pd.read_parquet(silver / "lineups.parquet", columns=["match_id", "team"])
    _check((lu.groupby("match_id").team.nunique() == 2).all(), "lineups: 2 equipos por partido")
    ts = pd.read_parquet(silver / "team_match_stats.parquet", columns=["match_id", "team_name", "team_match_pass_completion"])
    _check((ts.groupby("match_id").size() == 2).all(), "team_match_stats: 2 filas por partido")
    _check(ts.team_match_pass_completion.between(0.4, 1).all(), "team_match_stats: pass_completion en [0.4, 1]")
    ps = pd.read_parquet(silver / "player_match_stats.parquet", columns=["match_id", "player_match_minutes"])
    _check(bool((ps.player_match_minutes.dropna() >= 0).all()), "player_match_stats: minutos no negativos")


def check_league(ts: pd.DataFrame, league: pd.DataFrame) -> None:
    played = league[league.match_status == "available"]
    _check(ts.match_id.nunique() == played.match_id.nunique(),
           f"league_team_match_stats cubre los {played.match_id.nunique():,} partidos jugados de la liga")
    _check(bool((ts.groupby("match_id").size() == 2).all()), "league_team_match_stats: 2 equipos por partido")
    _check(ts.team_match_pass_completion.between(0.4, 1).all(), "league_team_match_stats: pass_completion en [0.4, 1]")
    _check(bool((ts.manager != "").mean() > 0.9), "league_team_match_stats: >90 % de filas con entrenador")


def check_gold_no_future(dim_match: pd.DataFrame) -> None:
    """Contexto sin leakage: la fuerza del rival solo usa partidos ANTERIORES a la fecha."""
    _check("rival_ppg_prev" in dim_match and "rival_n_prev" in dim_match, "dim_match: fuerza del rival previa presente")
    _check(bool((dim_match.rival_n_prev >= 0).all()), "dim_match: n de partidos previos del rival >= 0")

"""GOLD: tablas por caso de uso (el contrato con modelos y fichas), construidas SOLO desde Silver y con
las definiciones de src/framework.py y src/features.py.

  dim_match          contexto del partido sin leakage (fuerza del rival previa, descanso, orden, fase)
  fct_possession     una fila por posesión (ambos equipos) con objetos del marco
  fct_segment        partido × tramo de 15' × estado del marcador (mismas métricas que match_features)
  fct_set_piece      una fila por balón parado (a favor y en contra)
  fct_substitution   una fila por intervención (cambios simultáneos) con Δ métricas 15' antes/después
  fct_player_match   jugador × partido (América): posición, p90, referencia previa, residuo
  match_features     una fila por partido: variables por criterio del reto + uso de jugadores
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import features as F
from src import framework as fw

from .config import GOLD, SILVER, TEAM, get_logger
from .silver import load_events
from . import quality

log = get_logger("gold")


# ------------------------------------------------------------------ contexto
def build_dim_match() -> pd.DataFrame:
    m = pd.read_parquet(SILVER / "matches.parquet")
    m = m[m.match_status == "available"].copy()
    league = pd.read_parquet(SILVER / "league_matches.parquet")
    lg = league[league.match_status == "available"]
    long = pd.concat([
        pd.DataFrame({"date": lg.match_date, "team": lg.home_team,
                      "pts": np.select([lg.home_score > lg.away_score, lg.home_score == lg.away_score], [3, 1], 0)}),
        pd.DataFrame({"date": lg.match_date, "team": lg.away_team,
                      "pts": np.select([lg.away_score > lg.home_score, lg.home_score == lg.away_score], [3, 1], 0)}),
    ]).sort_values("date")
    w = fw.A["rival_strength_window"]
    ppg, n = [], []
    for opp, date in zip(m.opponent, m.match_date):
        prev = long[(long.team == opp) & (long.date < date)].tail(w)   # SOLO partidos anteriores (sin leakage)
        ppg.append(prev.pts.mean() if len(prev) else np.nan)
        n.append(len(prev))
    m["rival_ppg_prev"], m["rival_n_prev"] = ppg, n
    m = m.sort_values("match_date").reset_index(drop=True)
    m["match_order"] = np.arange(len(m))
    m["rest_days"] = m.match_date.diff().dt.days
    keep = ["match_id", "match_date", "match_order", "season", "season_id", "torneo", "fase", "competition_stage",
            "match_week", "is_home", "opponent", "rival_ppg_prev", "rival_n_prev", "rest_days", "team_manager",
            "goals_for", "goals_against", "result"]
    return m[keep]


# ------------------------------------------------------------------ jugadores
def build_player_match(ev: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    ps = pd.read_parquet(SILVER / "player_match_stats.parquet")
    ps = ps[ps.team_name == TEAM].copy()
    lp = pd.read_parquet(SILVER / "lineup_positions.parquet")
    lp = lp[lp.team == TEAM].copy()
    end = ev.groupby("match_id").minute.max()
    lp["to_min"] = lp.to_min.fillna(lp.match_id.map(end))
    lp["mins"] = (lp.to_min - lp.from_min).clip(lower=0)
    main = (lp.sort_values("mins").groupby(["match_id", "player_id"]).tail(1)
            .set_index(["match_id", "player_id"])[["position"]].rename(columns={"position": "main_position"}))
    starter = lp[lp.start_reason == "Starting XI"][["match_id", "player_id"]].drop_duplicates().assign(starter=True)
    am = ev[ev.am & ev.player_id.notna()].assign(player_id=lambda d: d.player_id.astype(int))
    prog = (am.prog_pass | am.prog_carry).groupby([am.match_id, am.player_id]).sum().rename("prog_actions")
    touches = am[am.type.isin({"Pass", "Carry", "Ball Receipt*", "Shot", "Dribble"})].groupby(["match_id", "player_id"]).size().rename("touches_ev")
    cols = {"player_match_minutes": "minutes", "player_match_obv": "obv", "player_match_obv_pass": "obv_pass",
            "player_match_obv_dribble_carry": "obv_dribble_carry", "player_match_obv_defensive_action": "obv_def",
            "player_match_np_xg": "np_xg", "player_match_xa": "xa", "player_match_touches": "touches",
            "player_match_pressures": "pressures", "player_match_deep_progressions": "deep_progressions",
            "player_match_passes": "passes", "player_match_ball_recoveries": "ball_recoveries",
            "player_match_tackles": "tackles", "player_match_interceptions": "interceptions",
            "player_match_dribbles": "dribbles", "player_match_xgbuildup": "xgbuildup"}
    p = ps[["match_id", "player_id", "player_name", *[c for c in cols if c in ps]]].rename(columns=cols)
    p = (p.set_index(["match_id", "player_id"]).join(main).join(prog).join(touches).reset_index()
         .merge(starter, on=["match_id", "player_id"], how="left"))
    p["starter"] = p.starter.fillna(False).astype(bool)
    # jugadores con pocos minutos sin acciones registradas: el valor correcto es 0, no NaN
    for c in ["obv", "obv_pass", "obv_dribble_carry", "obv_def", "np_xg", "xa", "prog_actions", "touches_ev"]:
        if c in p:
            p[c] = p[c].fillna(0)
    p["position_group"] = p.main_position.map(fw.POSITION_GROUP)
    # nombre corto para gráficas y fichas: apodo oficial de StatsBomb, o el nombre completo si no existe
    nick = (pd.read_parquet(SILVER / "lineups.parquet", columns=["player_id", "player_nickname"])
            .dropna().drop_duplicates("player_id").set_index("player_id").player_nickname)
    p["player_short"] = p.player_id.map(nick).fillna(p.player_name)
    p = p.merge(dim[["match_id", "match_date", "match_order"]], on="match_id")
    for c in ["obv", "np_xg", "xa", "touches", "pressures", "prog_actions", "deep_progressions", "passes",
              "ball_recoveries", "tackles", "interceptions", "dribbles", "obv_pass", "obv_dribble_carry", "obv_def"]:
        if c in p:
            p[f"{c}_p90"] = np.where(p.minutes >= fw.A["player_min_minutes"], p[c] / p.minutes * 90, np.nan)
    # referencia PREVIA del jugador (shift(1): solo partidos anteriores → sin leakage)
    p = p.sort_values(["player_id", "match_date"])
    win = fw.A["player_reference_window"]
    p["obv_p90_ref_prev"] = (p.groupby("player_id").obv_p90
                             .transform(lambda s: s.shift(1).rolling(win, min_periods=3).mean()))
    p["obv_p90_resid"] = p.obv_p90 - p.obv_p90_ref_prev
    return p.sort_values(["match_order", "player_id"]).reset_index(drop=True)


def player_match_features(pm: pd.DataFrame, ev: pd.DataFrame, dim: pd.DataFrame) -> pd.DataFrame:
    """Uso de jugadores y distribución del juego, agregado por partido."""
    field = pm[pm.position_group != "Portero"]
    g = pm.groupby("match_id")
    pos_obv = pm.assign(o=pm.obv.clip(lower=0))
    tot = pos_obv.groupby("match_id").o.sum()

    def share(groups):
        s = pos_obv[pos_obv.position_group.isin(groups)].groupby("match_id").o.sum()
        return s.reindex(tot.index).fillna(0) / tot * 100  # sin jugadores en esa línea → 0 %

    out = pd.DataFrame({
        "gini_obv": g.obv.apply(fw.gini),
        "gini_touches": field.groupby("match_id").touches.apply(fw.gini),
        "gini_prog": field.groupby("match_id").prog_actions.apply(fw.gini),
        "top1_obv_share": pos_obv.groupby("match_id").o.apply(lambda s: s.max() / s.sum() * 100 if s.sum() else np.nan),
        "top3_obv_share": pos_obv.groupby("match_id").o.apply(lambda s: s.nlargest(3).sum() / s.sum() * 100 if s.sum() else np.nan),
        "obv_share_def": share(["Defensa", "Carrilero"]),
        "obv_share_mid": share(["Medio defensivo", "Medio", "Medio ofensivo"]),
        "obv_share_wide": share(["Banda"]),
        "obv_share_fwd": share(["Delantero"]),
        "boost_pct": pm[pm.obv_p90_resid.notna()].groupby("match_id").obv_p90_resid.apply(lambda s: (s > 0).mean() * 100),
        "boost_mean": pm.groupby("match_id").obv_p90_resid.mean(),
    })
    starters = pm[pm.starter].groupby("match_id").player_id.apply(frozenset)
    order = dim.set_index("match_id").match_order.sort_values()
    st = starters.reindex(order.index)
    out["xi_rotation"] = pd.Series([np.nan] + [len(b - a) if isinstance(a, frozenset) and isinstance(b, frozenset) else np.nan
                                               for a, b in zip(st.values[:-1], st.values[1:])], index=st.index)
    am = ev[ev.am & (ev.period < 5)]
    out["tactical_shifts"] = am[am.type == "Tactical Shift"].groupby("match_id").size().reindex(out.index).fillna(0)
    out["first_sub_minute"] = am[am.type == "Substitution"].groupby("match_id").minute.min()
    return out


# ------------------------------------------------------------------ balón parado y cambios
def build_set_pieces(ev: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    sp = poss[poss.is_set_piece].copy()
    own_pass = ev[(ev.team == ev.possession_team) & ev.is_pass]
    first_pass = own_pass.groupby(["match_id", "possession"]).head(1).set_index(["match_id", "possession"])
    sp = sp.set_index(["match_id", "possession"]).join(first_pass[[
        "pass_technique", "pass_height", "pass_length", "pass_end_location_x", "pass_end_location_y",
        "pass_inswinging", "pass_outswinging", "pass_body_part", "player", "location_y"]]).reset_index()
    sp["kind"] = sp.play_pattern.map(fw.SET_PIECE_PATTERNS)
    sp["target_zone"] = fw.set_piece_target_zone(sp.pass_end_location_x, sp.pass_end_location_y, sp.pass_length.fillna(0))
    sp["delivery"] = np.select([sp.pass_inswinging == True, sp.pass_outswinging == True, sp.pass_length < 15],  # noqa: E712
                               ["Cerrado", "Abierto", "Corto"], "Otro")
    sp["side"] = np.where(sp.location_y < 40, "Izquierda", "Derecha")
    first_shot = ev[ev.type == "Shot"].groupby(["match_id", "possession"]).head(1).set_index(["match_id", "possession"])
    sp = sp.set_index(["match_id", "possession"]).join(first_shot[["location_x", "location_y"]].rename(
        columns={"location_x": "shot_x", "location_y": "shot_y"})).reset_index()
    return sp


def build_substitutions(ev: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    """Intervención = cambios del América en el mismo minuto. Δ = métricas 15' después − 15' antes."""
    subs = ev[ev.am & (ev.type == "Substitution") & (ev.period < 5)]
    inter = (subs.groupby(["match_id", "minute"])
             .agg(t=("t", "min"), n_subs=("id", "size"), players_off=("player", list),
                  players_on=("substitution_replacement", list), positions_off=("position", list),
                  score_diff=("score_diff", "first"), game_state=("game_state", "first"))
             .reset_index())
    inter["sub_id"] = inter.match_id.astype(str) + "_" + inter.minute.astype(str)
    W = fw.A["sub_window_min"] * 60
    parts, pparts = [], []
    ev_by, poss_by = dict(tuple(ev.groupby("match_id"))), dict(tuple(poss.groupby("match_id")))
    for r in inter.itertuples():
        em, pm_ = ev_by[r.match_id], poss_by[r.match_id]
        for label, lo, hi in [("antes", r.t - W, r.t), ("despues", r.t, r.t + W)]:
            parts.append(em[(em.t >= lo) & (em.t < hi)].assign(sub_id=r.sub_id, window=label))
            pparts.append(pm_[(pm_.t_start >= lo) & (pm_.t_start < hi)].assign(sub_id=r.sub_id, window=label))
    agg = F.aggregate(pd.concat(parts), pd.concat(pparts), ["sub_id", "window"])[F.SEGMENT_FEATURES + ["duration_min"]]
    wide = agg.unstack("window")
    delta = pd.DataFrame({f"d_{c}": wide[(c, "despues")] - wide[(c, "antes")] for c in F.SEGMENT_FEATURES})
    delta["dur_antes_min"], delta["dur_despues_min"] = wide[("duration_min", "antes")], wide[("duration_min", "despues")]
    pos_off = inter.positions_off.map(lambda ps: [fw.POSITION_GROUP.get(p, "?") for p in ps])
    inter["groups_off"] = pos_off.map(lambda g: ",".join(sorted(set(g))))
    inter = inter.drop(columns=["players_off", "players_on", "positions_off"]).assign(
        n_off_att=pos_off.map(lambda g: sum(x in {"Delantero", "Banda", "Medio ofensivo"} for x in g)),
        n_off_def=pos_off.map(lambda g: sum(x in {"Defensa", "Carrilero", "Medio defensivo"} for x in g)))
    return inter.merge(delta, left_on="sub_id", right_index=True, how="left")


# ------------------------------------------------------------------ run
def run() -> None:
    GOLD.mkdir(parents=True, exist_ok=True)
    dim = build_dim_match()
    quality.check_gold_no_future(dim)
    dim.to_parquet(GOLD / "dim_match.parquet", index=False)
    log.info(f"Gold dim_match: {len(dim)} partidos")

    ev = load_events()
    ev = ev[ev.match_id.isin(dim.match_id)]
    ev = fw.add_game_state(ev)
    ev = F.event_flags(ev)
    poss = fw.possessions(ev)
    poss.to_parquet(GOLD / "fct_possession.parquet", index=False)
    log.info(f"Gold fct_possession: {len(poss):,} posesiones")

    mf = F.aggregate(ev, poss, ["match_id"])
    ts = pd.read_parquet(SILVER / "team_match_stats.parquet")
    ts = ts[ts.team_name == TEAM].set_index("match_id")
    for c in ["directness", "pace_towards_goal", "defensive_distance", "ppda", "possession", "obv", "np_xg",
              "np_xg_conceded", "pass_completion", "gk_long_pass_ratio", "deep_progressions", "aggression"]:
        mf[f"sb_{c}"] = ts.get(f"team_match_{c}")
    pm = build_player_match(ev, dim)
    pm.to_parquet(GOLD / "fct_player_match.parquet", index=False)
    mf = mf.join(player_match_features(pm, ev, dim))
    mf = dim.set_index("match_id").join(mf).reset_index()
    mf.to_parquet(GOLD / "match_features.parquet", index=False)
    log.info(f"Gold match_features: {mf.shape}")

    seg = F.aggregate(ev, poss, ["match_id", "minute_bin", "game_state"])
    seg = seg[seg.duration_min > 0].reset_index().merge(dim[["match_id", "match_order", "is_home", "rival_ppg_prev", "fase"]],
                                                       on="match_id")
    seg.to_parquet(GOLD / "fct_segment.parquet", index=False)
    log.info(f"Gold fct_segment: {len(seg):,} segmentos")

    build_set_pieces(ev, poss).to_parquet(GOLD / "fct_set_piece.parquet", index=False)
    subs = build_substitutions(ev, poss)
    subs.to_parquet(GOLD / "fct_substitution.parquet", index=False)
    log.info(f"Gold fct_substitution: {len(subs)} intervenciones")
    log.info("Gold listo")

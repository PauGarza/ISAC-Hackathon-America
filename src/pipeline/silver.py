"""SILVER: Bronze (JSON crudo) → tablas Parquet tipadas, aplanadas y validadas.

Para garantizar exactamente el mismo aplanado que usamos en el EDA, se reutilizan las funciones
de statsbombpy pero leyendo de Bronze (se intercepta `api_client.get_resource`): no hay red.

Tablas (data/silver/):
  league_matches.parquet        todos los partidos de Liga MX (para fuerza del rival)
  matches.parquet               partidos del América con contexto básico
  events/season=<id>/part.parquet
  frames360/season=<id>/part.parquet
  lineups.parquet, lineup_positions.parquet
  player_match_stats.parquet, team_match_stats.parquet
"""
from __future__ import annotations

import contextlib
import json
import re
import warnings

import numpy as np
import pandas as pd

from .bronze import load_manifest, read_bronze
from .config import COMPETITION_ID, SEASONS, SILVER, TEAM, get_logger
from . import quality

warnings.filterwarnings("ignore")
log = get_logger("silver")

_ROUTES = [  # regex de URL de statsbombpy -> (endpoint bronze, función que arma la key)
    (re.compile(r"/competitions/(\d+)/seasons/(\d+)/matches$"), "matches", lambda m: f"{m[1]}_{m[2]}"),
    (re.compile(r"/events/(\d+)$"), "events", lambda m: m[1]),
    (re.compile(r"/360-frames/(\d+)$"), "360-frames", lambda m: m[1]),
    (re.compile(r"/lineups/(\d+)$"), "lineups", lambda m: m[1]),
    (re.compile(r"/matches/(\d+)/player-stats$"), "player-match-stats", lambda m: m[1]),
    (re.compile(r"/matches/(\d+)/team-stats$"), "team-match-stats", lambda m: m[1]),
]


@contextlib.contextmanager
def offline_statsbomb():
    """statsbombpy lee de Bronze en lugar de la API."""
    from statsbombpy import api_client
    original = api_client.get_resource

    def from_bronze(url, creds):
        if url.endswith("/endpoint-versions"):
            return []  # statsbombpy usa sus versiones por defecto; la versión no afecta el aplanado
        for rx, endpoint, key in _ROUTES:
            m = rx.search(url)
            if m:
                try:
                    return read_bronze(endpoint, key(m))
                except FileNotFoundError:
                    return []
        raise ValueError(f"URL sin ruta Bronze: {url}")

    api_client.get_resource = from_bronze
    try:
        yield {"user": "bronze", "passwd": "bronze"}
    finally:
        api_client.get_resource = original


def to_parquet_safe(df: pd.DataFrame, path) -> None:
    """Parquet (Snappy) serializando a JSON columnas con dicts o listas de dicts."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype != object:
            continue
        s = df[col].dropna()
        if s.empty:
            continue
        nested = s.map(lambda v: isinstance(v, dict) or (isinstance(v, list) and any(isinstance(x, (dict, list)) for x in v)))
        if nested.any():
            df[col] = df[col].map(lambda v: json.dumps(v, ensure_ascii=False, default=str)
                                  if isinstance(v, (dict, list)) else (None if v is None or (isinstance(v, float) and np.isnan(v)) else v))
        elif (is_str := s.map(lambda v: isinstance(v, str))).any() and not is_str.all():  # tipos mixtos (p. ej. manager_id "2947, 4450" junto a enteros) → texto
            df[col] = df[col].map(lambda v: None if v is None or (isinstance(v, float) and np.isnan(v)) else str(v))
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False, compression="snappy")


def _xy(df: pd.DataFrame, cols) -> pd.DataFrame:
    for c in cols:
        if c in df:
            arr = df[c].map(lambda v: v if isinstance(v, (list, np.ndarray)) and len(v) >= 2 else (np.nan, np.nan))
            df[f"{c}_x"] = arr.map(lambda v: float(v[0]))
            df[f"{c}_y"] = arr.map(lambda v: float(v[1]))
    return df


# ------------------------------------------------------------------ matches
def build_matches(creds) -> tuple[pd.DataFrame, pd.DataFrame]:
    from statsbombpy import sb
    league = pd.concat([sb.matches(competition_id=COMPETITION_ID, season_id=s, creds=creds) for s in SEASONS],
                       ignore_index=True)
    league["match_date"] = pd.to_datetime(league.match_date)
    am = league[(league.home_team == TEAM) | (league.away_team == TEAM)].copy()
    home = am.home_team == TEAM
    am["is_home"] = home
    am["opponent"] = am.away_team.where(home, am.home_team)
    am["team_manager"] = am.home_managers.where(home, am.away_managers)
    am["goals_for"] = am.home_score.where(home, am.away_score)
    am["goals_against"] = am.away_score.where(home, am.home_score)
    played = am.match_status == "available"
    am["result"] = np.select([am.goals_for > am.goals_against, am.goals_for == am.goals_against],
                             ["W", "D"], "L")
    am.loc[~played, "result"] = None
    am["torneo"] = np.where(am.match_date.dt.month >= 7, "Apertura ", "Clausura ") + am.match_date.dt.year.astype(str)
    am["fase"] = np.where(am.competition_stage.isin(["Apertura", "Clausura", "Regular Season"]), "Fase regular", "Liguilla")
    am = am.sort_values(["match_date", "kick_off"]).reset_index(drop=True)
    return league, am


# ------------------------------------------------------------------ por partido
def _events(match_id: int, creds) -> pd.DataFrame:
    from statsbombpy import sb
    e = sb.events(match_id=match_id, creds=creds)
    return _xy(e, ["location", "pass_end_location", "carry_end_location", "shot_end_location", "goalkeeper_end_location"])


def _frames(match_id: int, creds) -> pd.DataFrame:
    from statsbombpy import sb
    try:
        f = sb.frames(match_id=match_id, creds=creds)
    except Exception:  # partidos sin 360 (la API devuelve vacío)
        return pd.DataFrame()
    return _xy(f, ["location"]) if len(f) else f


def _lineups(match_id: int, creds) -> pd.DataFrame:
    from statsbombpy import sb
    lu = sb.lineups(match_id=match_id, creds=creds)
    return pd.concat([d.assign(team=t, match_id=match_id) for t, d in lu.items()], ignore_index=True)


def _stats(kind: str, match_id: int, creds) -> pd.DataFrame:
    from statsbombpy import sb
    fn = sb.player_match_stats if kind == "player" else sb.team_match_stats
    d = fn(match_id=match_id, creds=creds)
    if "match_id" not in d:
        d["match_id"] = match_id
    return d


def lineup_positions(lineups: pd.DataFrame) -> pd.DataFrame:
    """Una fila por tramo de posición (jugador × posición × partido) con minutos jugados."""
    rows = []
    for r in lineups.itertuples():
        pos = r.positions if isinstance(r.positions, list) else json.loads(r.positions) if isinstance(r.positions, str) else []
        for p in pos:
            rows.append({"match_id": r.match_id, "team": r.team, "player_id": r.player_id, "player_name": r.player_name,
                         **{k: p.get(k) for k in ["position_id", "position", "from", "to", "from_period", "to_period",
                                                  "start_reason", "end_reason"]}})
    lp = pd.DataFrame(rows)

    def _min(ts):
        """Reloj del partido "MM:SS" (o "H:MM:SS") → minutos."""
        if not isinstance(ts, str):
            return np.nan
        parts = [float(x) for x in ts.split(":")]
        while len(parts) < 3:
            parts.insert(0, 0.0)
        h, m, s = parts
        return h * 60 + m + s / 60

    lp["from_min"] = lp["from"].map(_min)
    lp["to_min"] = lp["to"].map(_min)
    return lp


# ------------------------------------------------------------------ run
def run() -> None:
    SILVER.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    with offline_statsbomb() as creds:
        league, am = build_matches(creds)
        played = am[am.match_status == "available"]
        to_parquet_safe(league, SILVER / "league_matches.parquet")
        to_parquet_safe(am, SILVER / "matches.parquet")
        log.info(f"Silver matches: liga {len(league)} | América {len(am)} ({len(played)} jugados)")

        lineups, pstats, tstats = [], [], []
        for sid in SEASONS:
            ids = played[played.season_id == sid].match_id.astype(int).tolist()
            if not ids:
                continue
            ev = pd.concat([_events(m, creds) for m in ids], ignore_index=True)
            quality.check_events(ev, ids)
            to_parquet_safe(ev, SILVER / "events" / f"season={sid}" / "part.parquet")
            fr = [f for f in (_frames(m, creds) for m in ids) if len(f)]
            if fr:
                to_parquet_safe(pd.concat(fr, ignore_index=True), SILVER / "frames360" / f"season={sid}" / "part.parquet")
            lineups += [_lineups(m, creds) for m in ids]
            pstats += [_stats("player", m, creds) for m in ids]
            tstats += [_stats("team", m, creds) for m in ids if ("team-match-stats", str(m)) in
                       set(zip(manifest.endpoint, manifest.key.astype(str)))]
            log.info(f"Silver season {sid}: {len(ids)} partidos, {len(ev):,} eventos, {sum(len(f) for f in fr):,} filas 360")
            del ev, fr

        lu = pd.concat(lineups, ignore_index=True)
        to_parquet_safe(lu, SILVER / "lineups.parquet")
        to_parquet_safe(lineup_positions(lu), SILVER / "lineup_positions.parquet")
        ps = pd.concat(pstats, ignore_index=True)
        to_parquet_safe(ps, SILVER / "player_match_stats.parquet")
        ts = pd.concat([t for t in tstats if len(t)], ignore_index=True)
        # anomalía documentada en el EDA: passing_ratio de la API == opp_final_third_pass_ratio
        ts["team_match_pass_completion"] = ts.team_match_successful_passes / ts.team_match_passes
        to_parquet_safe(ts, SILVER / "team_match_stats.parquet")

    quality.check_silver(SILVER, played)
    log.info("Silver listo y validado")


def load_events(columns=None) -> pd.DataFrame:
    """Carga events de todas las temporadas (con season_id)."""
    parts = sorted((SILVER / "events").glob("season=*/part.parquet"))
    return pd.concat([pd.read_parquet(p, columns=columns).assign(season_id=int(p.parent.name.split("=")[1]))
                      for p in parts], ignore_index=True)


def load_frames(match_ids=None) -> pd.DataFrame:
    parts = sorted((SILVER / "frames360").glob("season=*/part.parquet"))
    df = pd.concat([pd.read_parquet(p) for p in parts], ignore_index=True)
    return df[df.match_id.isin(match_ids)] if match_ids is not None else df

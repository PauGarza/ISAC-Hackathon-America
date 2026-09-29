"""Helpers para descargar datos de StatsBomb (API con credenciales) con caché en parquet.

Uso:
    from src.sb_client import get_creds, get_team_matches, download_match
"""
from __future__ import annotations

import json
import os
import warnings
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from statsbombpy import sb

# statsbombpy avisa en cada llamada que usamos credenciales; no aporta nada
warnings.filterwarnings("ignore", module="statsbombpy")

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

LIGA_MX = 73
LIGA_MX_FEMENIL = 1438
# season_id -> nombre de temporada (Liga MX, comp 73)
SEASONS_LIGA_MX = {
    108: "2021/2022",
    235: "2022/2023",
    281: "2023/2024",
    317: "2024/2025",
    318: "2025/2026",
    351: "2026/2027",
}


def get_creds() -> dict:
    """Lee SB_USERNAME / SB_PASSWORD de .env (raíz del repo)."""
    load_dotenv(ROOT / ".env")
    user, passwd = os.getenv("SB_USERNAME"), os.getenv("SB_PASSWORD")
    if not user or not passwd:
        raise RuntimeError("Faltan SB_USERNAME / SB_PASSWORD en .env (ver .env.example)")
    return {"user": user, "passwd": passwd}


def to_parquet_safe(df: pd.DataFrame, path: Path) -> None:
    """Guarda en parquet serializando a JSON las columnas con dicts o listas de dicts
    (p. ej. tactics, shot_freeze_frame, positions), que pyarrow no maneja bien."""
    df = df.copy()
    for col in df.columns:
        if df[col].dtype != object:
            continue
        sample = df[col].dropna()
        if sample.empty:
            continue
        nested = sample.map(
            lambda v: isinstance(v, dict)
            or (isinstance(v, list) and any(isinstance(x, (dict, list)) for x in v))
        )
        if nested.any():
            df[col] = df[col].map(lambda v: json.dumps(v, ensure_ascii=False) if v is not None and not (isinstance(v, float) and pd.isna(v)) else None)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def get_team_matches(team: str, creds: dict, competition_id: int = LIGA_MX,
                     seasons: dict = SEASONS_LIGA_MX) -> pd.DataFrame:
    """Todos los partidos de `team` en las temporadas dadas, con columnas de contexto
    (local/visita, rival, entrenador propio, goles a favor/en contra)."""
    frames = []
    for season_id in seasons:
        m = sb.matches(competition_id=competition_id, season_id=season_id, creds=creds)
        frames.append(m)
    m = pd.concat(frames, ignore_index=True)
    m = m[(m.home_team == team) | (m.away_team == team)].copy()

    is_home = m.home_team == team
    m["is_home"] = is_home
    m["opponent"] = m.away_team.where(is_home, m.home_team)
    m["team_manager"] = m.home_managers.where(is_home, m.away_managers)
    m["opponent_manager"] = m.away_managers.where(is_home, m.home_managers)
    m["goals_for"] = m.home_score.where(is_home, m.away_score)
    m["goals_against"] = m.away_score.where(is_home, m.home_score)
    m["result"] = pd.Series(pd.NA, index=m.index, dtype="object")
    played = m.match_status == "available"
    m.loc[played & (m.goals_for > m.goals_against), "result"] = "W"
    m.loc[played & (m.goals_for == m.goals_against), "result"] = "D"
    m.loc[played & (m.goals_for < m.goals_against), "result"] = "L"
    return m.sort_values(["match_date", "kick_off"]).reset_index(drop=True)


def _lineups_df(match_id: int, creds: dict) -> pd.DataFrame:
    lu = sb.lineups(match_id=match_id, creds=creds)
    return pd.concat([df.assign(team=t, match_id=match_id) for t, df in lu.items()], ignore_index=True)


# nombre de carpeta -> función que descarga un DataFrame para un partido
DATASETS = {
    "events": lambda mid, c: sb.events(match_id=mid, creds=c),
    "frames360": lambda mid, c: sb.frames(match_id=mid, creds=c),
    "lineups": _lineups_df,
    "player_match_stats": lambda mid, c: sb.player_match_stats(match_id=mid, creds=c),
    "team_match_stats": lambda mid, c: sb.team_match_stats(match_id=mid, creds=c),
}


def download_match(match_id: int, creds: dict, datasets=DATASETS, overwrite: bool = False) -> dict:
    """Descarga los datasets de un partido a data/raw/<dataset>/<match_id>.parquet.
    Salta los que ya existen (reanudable). Devuelve {dataset: 'ok'|'cached'|'error: ...'}."""
    status = {}
    for name, fetch in datasets.items():
        path = RAW / name / f"{match_id}.parquet"
        if path.exists() and not overwrite:
            status[name] = "cached"
            continue
        try:
            df = fetch(match_id, creds)
            if "match_id" not in df.columns:
                df["match_id"] = match_id
            to_parquet_safe(df, path)
            status[name] = "ok"
        except Exception as exc:  # un endpoint caído no debe detener toda la descarga
            status[name] = f"error: {type(exc).__name__}: {exc}"[:200]
    return status


def load_dataset(name: str, match_ids=None) -> pd.DataFrame:
    """Concatena data/raw/<name>/*.parquet (opcionalmente solo match_ids dados)."""
    files = sorted((RAW / name).glob("*.parquet"))
    if match_ids is not None:
        wanted = {int(m) for m in match_ids}
        files = [f for f in files if int(f.stem) in wanted]
    return pd.concat((pd.read_parquet(f) for f in files), ignore_index=True)

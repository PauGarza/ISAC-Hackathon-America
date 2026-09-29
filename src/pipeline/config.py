"""Rutas y parámetros del pipeline medallion (Bronze → Silver → Gold)."""
from __future__ import annotations

import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
BRONZE = DATA / "bronze" / "statsbomb"
SILVER = DATA / "silver"
GOLD = DATA / "gold"
MODELS = ROOT / "models"
LOGS = ROOT / "logs"
REPORTS = ROOT / "reports" / "match_reports"

MANIFEST = BRONZE / "_manifest.parquet"

TEAM = "América"
COMPETITION_ID = 73  # Liga MX
SEASONS = {  # season_id -> nombre
    108: "2021/2022",
    235: "2022/2023",
    281: "2023/2024",
    317: "2024/2025",
    318: "2025/2026",
    351: "2026/2027",
}
# endpoints por partido: nombre en bronze -> plantilla de URL (la versión se resuelve en vivo)
MATCH_ENDPOINTS = {
    "events": "/api/{v}/events/{match_id}",
    "360-frames": "/api/{v}/360-frames/{match_id}",
    "lineups": "/api/{v}/lineups/{match_id}",
    "player-match-stats": "/api/{v}/matches/{match_id}/player-stats",
    "team-match-stats": "/api/{v}/matches/{match_id}/team-stats",
}
N_WORKERS = 4


def get_logger(name: str = "pipeline") -> logging.Logger:
    LOGS.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
        fh = logging.FileHandler(LOGS / "pipeline.log", encoding="utf-8")
        fh.setFormatter(fmt)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(fh)
        logger.addHandler(sh)
    return logger

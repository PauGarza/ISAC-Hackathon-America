"""BRONZE: extracción de la API de StatsBomb tal cual (JSON crudo, comprimido), inmutable.

- Cada respuesta se guarda en data/bronze/statsbomb/<endpoint>/[season=<id>/]<key>.json.gz
- _manifest.parquet registra endpoint, key, url, versión, fecha de extracción, status, bytes y sha256.
- Incremental: si (endpoint, key) ya está en el manifest con status 200 se salta.
- Idempotente: re-correr no duplica nada.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import pandas as pd
import requests

from src.sb_client import get_creds

from .config import BRONZE, COMPETITION_ID, MANIFEST, MATCH_ENDPOINTS, N_WORKERS, SEASONS, TEAM, get_logger

HOST = "https://data.statsbombservices.com"
log = get_logger("bronze")


def _versions(auth) -> dict:
    """Mapa endpoint -> versión vigente (mismo servicio que usa statsbombpy)."""
    from statsbombpy.config import API_VERSION_KEYS, VERSIONS
    r = requests.get(f"{HOST}/api/endpoint-versions", auth=auth, timeout=60)
    live = {API_VERSION_KEYS[k]: f"v{v}" for k, v in r.json().items() if k in API_VERSION_KEYS} if r.ok else {}
    return {**VERSIONS, **live}


def bronze_path(endpoint: str, key: str, season_id: int | None = None):
    part = f"season={season_id}/" if season_id is not None else ""
    return BRONZE / endpoint / f"{part}{key}.json.gz"


def load_manifest() -> pd.DataFrame:
    if MANIFEST.exists():
        return pd.read_parquet(MANIFEST)
    return pd.DataFrame(columns=["endpoint", "key", "season_id", "url", "version", "extracted_at",
                                 "status", "bytes", "sha256", "path"])


_INDEX: dict = {"mtime": None, "paths": {}}


def _index() -> dict:
    """(endpoint, key) -> ruta, cacheado mientras el manifest no cambie en disco."""
    mtime = MANIFEST.stat().st_mtime if MANIFEST.exists() else None
    if _INDEX["mtime"] != mtime:
        m = load_manifest()
        m = m[m.status == 200]
        _INDEX.update(mtime=mtime, paths=dict(zip(zip(m.endpoint, m.key.astype(str)), m.path)))
    return _INDEX["paths"]


def read_bronze(endpoint: str, key: str):
    """Lee el JSON crudo de un recurso Bronze (usado por Silver)."""
    path = _index().get((endpoint, str(key)))
    if path is None:
        raise FileNotFoundError(f"Bronze sin {endpoint}/{key}")
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def _get(url, auth, retries: int = 4):
    """GET con reintentos y backoff exponencial ante cortes de conexión o 5xx."""
    for attempt in range(retries):
        try:
            r = requests.get(url, auth=auth, timeout=180)
            if r.status_code < 500:
                return r
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                log.warning(f"{url} -> {type(e).__name__} tras {retries} intentos")
                return None
        time.sleep(2 ** attempt * 3)
    return r


def _fetch(endpoint, key, url, version, season_id, auth) -> dict:
    r = _get(url, auth)
    if r is None:  # fallo de red persistente: queda registrado y se reintenta en la próxima corrida
        return {"endpoint": endpoint, "key": str(key), "season_id": season_id, "url": url, "version": version,
                "extracted_at": datetime.now(timezone.utc).isoformat(), "status": -1, "bytes": 0,
                "sha256": None, "path": None}
    rec = {"endpoint": endpoint, "key": str(key), "season_id": season_id, "url": url, "version": version,
           "extracted_at": datetime.now(timezone.utc).isoformat(), "status": r.status_code,
           "bytes": len(r.content), "sha256": hashlib.sha256(r.content).hexdigest(), "path": None}
    if r.ok:
        path = bronze_path(endpoint, key, season_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(path, "wb") as f:  # contenido exacto de la respuesta
            f.write(r.content)
        rec["path"] = str(path)
    return rec


def _write_manifest(new: list[dict]):
    if not new:
        return
    m = pd.concat([load_manifest(), pd.DataFrame(new)], ignore_index=True)
    m = m.drop_duplicates(["endpoint", "key"], keep="last")  # re-extracción reemplaza, no duplica
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    m.to_parquet(MANIFEST, index=False)


def run(seasons: dict = SEASONS, match_ids: list[int] | None = None, force: bool = False) -> pd.DataFrame:
    creds = get_creds()
    auth = requests.auth.HTTPBasicAuth(creds["user"], creds["passwd"])
    v = _versions(auth)
    manifest = load_manifest()
    done = set(zip(manifest.endpoint, manifest.key.astype(str))) if not force else set()
    done = {d for d in done if d in set(zip(manifest[manifest.status == 200].endpoint,
                                             manifest[manifest.status == 200].key.astype(str)))}
    new = []

    # 1) calendario de toda la liga por temporada (siempre se refresca: cambia durante la temporada en curso)
    for sid in seasons:
        url = f"{HOST}/api/{v['matches']}/competitions/{COMPETITION_ID}/seasons/{sid}/matches"
        new.append(_fetch("matches", f"{COMPETITION_ID}_{sid}", url, v["matches"], sid, auth))
    _write_manifest(new)

    # 2) partidos del América jugados → endpoints por partido (incremental)
    tasks = []
    for sid in seasons:
        for m in read_bronze("matches", f"{COMPETITION_ID}_{sid}"):
            teams = (m["home_team"]["home_team_name"], m["away_team"]["away_team_name"])
            if TEAM not in teams or m.get("match_status") != "available":
                continue
            if match_ids and m["match_id"] not in match_ids:
                continue
            for ep, tpl in MATCH_ENDPOINTS.items():
                if (ep, str(m["match_id"])) in done:
                    continue
                ver = v.get(ep, v.get(ep.replace("-match-stats", "-match-stats")))
                tasks.append((ep, m["match_id"], HOST + tpl.format(v=ver, match_id=m["match_id"]), ver, sid))
    log.info(f"Bronze: {len(tasks)} recursos por descargar ({len(done)} ya en manifest)")

    batch = []
    with ThreadPoolExecutor(max_workers=N_WORKERS) as pool:
        futs = [pool.submit(_fetch, ep, mid, url, ver, sid, auth) for ep, mid, url, ver, sid in tasks]
        for i, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()
            batch.append(rec)
            if rec["status"] != 200:
                log.warning(f"{rec['endpoint']}/{rec['key']} -> HTTP {rec['status']}")
            if i % 100 == 0:
                _write_manifest(batch); batch = []
                log.info(f"Bronze: {i}/{len(tasks)}")
    _write_manifest(batch)
    m = load_manifest()
    log.info(f"Bronze listo: {len(m)} recursos en manifest; status≠200: {(m.status != 200).sum()}")
    return m

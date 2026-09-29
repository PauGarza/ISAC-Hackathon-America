"""CLI del pipeline.

    python -m src.pipeline run --stages bronze,silver,gold,train,score,report [--match-id 123]

Cada etapa lee solo de la capa anterior; todas son idempotentes.
"""
from __future__ import annotations

import argparse
import sys
import time

from .config import get_logger

STAGES = ["bronze", "silver", "gold", "train", "score", "report"]


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m src.pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="ejecuta etapas del pipeline")
    r.add_argument("--stages", default="bronze,silver,gold", help=f"subconjunto de {STAGES}")
    r.add_argument("--match-id", type=int, action="append", help="limita a uno o varios partidos")
    r.add_argument("--force", action="store_true", help="re-extrae Bronze aunque exista")
    a = p.parse_args(argv)

    log = get_logger("cli")
    stages = [s.strip() for s in a.stages.split(",")]
    for s in stages:
        if s not in STAGES:
            sys.exit(f"etapa desconocida: {s}")
    for s in STAGES:  # orden canónico
        if s not in stages:
            continue
        t0 = time.time()
        log.info(f"== etapa {s} ==")
        if s == "bronze":
            from . import bronze
            bronze.run(match_ids=a.match_id, force=a.force)
        elif s == "silver":
            from . import silver
            silver.run()
        elif s == "gold":
            from . import gold
            gold.run()
        elif s == "train":
            from src import modeling
            modeling.train_all()
        elif s == "score":
            from src import modeling
            modeling.score(match_ids=a.match_id)
        elif s == "report":
            from src import match_report
            match_report.build_many(a.match_id)
        log.info(f"== etapa {s} terminada en {time.time() - t0:.0f}s ==")


if __name__ == "__main__":
    main()

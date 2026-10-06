"""Copia a app/data/ SOLO lo que la app necesita, todo agregado:
- el cubo por partido (src/cube.py → data/gold/cube/), que ya pasó la guarda contra columnas crudas;
- los hallazgos de la historia (notebook 05) y los textos del reporte (reports/final/textos.md).

Uso: python -m app.export_data   (después de `python -m src.cube`)
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from src import cube as K

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "data"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cube = K.load()
    if not cube:
        raise SystemExit("No hay cubo: corre primero `python -m src.cube`.")
    for name, df in cube.items():
        K._guard(df, name).to_parquet(OUT / f"{name}.parquet", index=False)
    h = pd.read_parquet(ROOT / "data" / "gold" / "analysis" / "story_hallazgos.parquet")
    h.to_parquet(OUT / "hallazgos.parquet", index=False)
    shutil.copy(ROOT / "reports" / "final" / "textos.md", OUT / "textos.md")
    size = sum(f.stat().st_size for f in OUT.iterdir()) / 1e6
    print(f"app/data: {len(list(OUT.iterdir()))} archivos, {size:.1f} MB")


if __name__ == "__main__":
    main()

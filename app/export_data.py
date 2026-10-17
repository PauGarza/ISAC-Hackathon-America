"""Copia a app/data/ SOLO lo que la app necesita, todo agregado: el cubo por partido
(src/cube.py → data/gold/cube/), que ya pasó la guarda contra columnas crudas.

La app no lleva textos ni hallazgos de la historia: esos viven en el reporte (reports/final/).

Uso: python -m app.export_data   (después de `python -m src.cube`)
"""
from __future__ import annotations

from pathlib import Path

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
    for old in ["hallazgos.parquet", "textos.md"]:   # restos de cuando la app contaba la historia
        (OUT / old).unlink(missing_ok=True)
    size = sum(f.stat().st_size for f in OUT.iterdir()) / 1e6
    print(f"app/data: {len(list(OUT.iterdir()))} archivos, {size:.1f} MB")


if __name__ == "__main__":
    main()

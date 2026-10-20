"""Copia a app/data/ SOLO lo que la app necesita, todo agregado: el cubo por partido
(src/cube.py → data/gold/cube/), que ya pasó la guarda contra columnas crudas, y en app/data/reporte las tablas
con las que se dibujan las gráficas del reporte (src/final_report.TABLAS_GRAFICAS).

Uso: python -m app.export_data   (después de `python -m src.cube` y de los notebooks 05–07)
"""
from __future__ import annotations

from pathlib import Path

from src import cube as K
from src import final_report as FR

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "data"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cube = K.load()
    if not cube:
        raise SystemExit("No hay cubo: corre primero `python -m src.cube`.")
    for name, df in cube.items():
        K._guard(df, name).to_parquet(OUT / f"{name}.parquet", index=False)
    rep = OUT / "reporte"                              # tablas de las gráficas del reporte (ya agregadas)
    rep.mkdir(exist_ok=True)
    for name in FR.TABLAS_GRAFICAS:
        K._guard(FR.rd(name), name).to_parquet(rep / f"{name}.parquet")   # con su índice (p. ej. el técnico en el encaje)
    for old in ["hallazgos.parquet", "textos.md"]:   # restos de cuando la app contaba la historia
        (OUT / old).unlink(missing_ok=True)
    files = [f for f in OUT.rglob("*.parquet")]
    print(f"app/data: {len(files)} archivos, {sum(f.stat().st_size for f in files) / 1e6:.1f} MB")


if __name__ == "__main__":
    main()

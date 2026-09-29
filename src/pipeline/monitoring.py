"""Monitoreo de drift: ¿las variables núcleo de partidos recientes salen de la distribución de entrenamiento?

PSI (Population Stability Index) por variable, con bins por cuantiles de TRAIN.
Los umbrales clásicos (0.10 / 0.25) suponen muestras grandes; con una ventana de 10 partidos el PSI esperado
SIN drift ya ronda (bins-1)/n. Por eso los umbrales se calibran con una distribución nula por remuestreo:
PSI de muestras de tamaño n extraídas de train. Moderado > p90 nulo · fuerte > p99 nulo.
No requiere etiquetas: detecta cambios en los inputs antes de que el error de los modelos lo muestre.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def psi(reference: pd.Series, current: pd.Series, bins: int = 5) -> float:
    """PSI con bins por quintiles de la referencia y suavizado de Laplace (+0.5 por bin).
    Con ventanas cortas (10 partidos) un bin vacío dispararía el PSI sin suavizado; 5 bins mantienen
    ~2 partidos esperados por bin."""
    ref, cur = reference.dropna().values, current.dropna().values
    if len(ref) < 4 * bins or len(cur) < 5:
        return np.nan
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    edges[0], edges[-1] = -np.inf, np.inf
    rc, cc = np.histogram(ref, edges)[0] + 0.5, np.histogram(cur, edges)[0] + 0.5
    r, c = rc / rc.sum(), cc / cc.sum()
    return float(np.sum((c - r) * np.log(c / r)))


def drift_report(mf: pd.DataFrame, split: pd.Series, cols: list[str], window: int = 10,
                 until_order: int | None = None, n_null: int = 1000, seed: int = 42) -> pd.DataFrame:
    """PSI de los `window` partidos que terminan en `until_order` (por defecto, los últimos) frente a train."""
    d = mf.assign(split=mf.match_id.map(split)).sort_values("match_order")
    ref = d[d.split == "train"]
    cur = (d[d.match_order <= until_order] if until_order is not None else d).tail(window)
    rng = np.random.default_rng(seed)
    rows = {}
    for c in cols:
        r, n = ref[c].dropna(), cur[c].notna().sum()
        null = np.array([psi(r, pd.Series(rng.choice(r.values, n, replace=True))) for _ in range(n_null)])
        v = psi(r, cur[c])
        rows[c] = {"PSI": v, "p90_nulo": np.nanquantile(null, .90), "p99_nulo": np.nanquantile(null, .99),
                   "media_train": r.mean(), "media_reciente": cur[c].mean()}
    out = pd.DataFrame(rows).T
    out["estado"] = np.select([out.PSI > out.p99_nulo, out.PSI > out.p90_nulo], ["fuerte", "moderado"], "estable")
    out["ratio"] = out.PSI / out.p90_nulo
    return out.sort_values("ratio", ascending=False).drop(columns="ratio")

"""Utilidades para exportar tablas y cifras a LaTeX (reportes en reports/*/).

Mismo formato que reports/eda/make_tables.py: booktabs, enteros solo si toda la columna es entera,
escape de caracteres especiales y tablas que se ajustan al ancho de página.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_ESC = [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"), ("_", r"\_"),
        ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}"), ("≈", r"$\approx$"),
        ("↑", r"$\uparrow$"), ("≥", r"$\geq$"), ("≤", r"$\leq$"), ("μ", r"$\mu$"), ("ρ", r"$\rho$"),
        ("²", r"$^2$"), ("→", r"$\rightarrow$"), ("Δ", r"$\Delta$"), ("−", "--"), ("×", r"$\times$"),
        ("α", r"$\alpha$"), ("η", r"$\eta$"), ("|", r"$|$")]


def esc(v) -> str:
    s = str(v)
    for a, b in _ESC:
        s = s.replace(a, b)
    return s


def fmt_val(v, digits: int = 2, as_int: bool = True) -> str:
    if isinstance(v, (bool, np.bool_)):
        return "sí" if v else "no"
    if isinstance(v, (float, np.floating)):
        if pd.isna(v):
            return "--"
        if as_int and float(v).is_integer():
            return f"{int(v):,}"
        if abs(v) >= 1000:
            return f"{v:,.0f}"
        return f"{v:.{digits}f}"
    if isinstance(v, (int, np.integer)):
        return f"{v:,}"
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "--"
    return esc(v)


def write_table(df: pd.DataFrame, out_dir: Path, name: str, caption: str, label: str, colspec: str | None = None,
                index: bool = True, size: str = r"\small", digits: int = 2, long: bool = False,
                header: list[str] | None = None, note: str | None = None) -> None:
    df = df.copy()
    cols = ([esc(df.index.name or "")] if index else []) + [esc(c) for c in df.columns]
    if header:
        cols = header
    colspec = colspec or ("l" + "r" * (len(cols) - 1))
    as_int = [bool(pd.api.types.is_numeric_dtype(df[c]) and not pd.api.types.is_bool_dtype(df[c])
                   and df[c].dropna().apply(lambda v: float(v).is_integer()).all()) for c in df.columns]
    rows = []
    for idx, r in df.iterrows():
        cells = ([esc(idx if not isinstance(idx, tuple) else " · ".join(map(str, idx)))] if index else [])
        cells += [fmt_val(v, digits, ai) for v, ai in zip(r.values, as_int)]
        rows.append(" & ".join(cells) + r" \\")
    head = " & ".join(rf"\textbf{{{c}}}" for c in cols) + r" \\"
    note_tex = [rf"\par\smallskip\parbox{{\linewidth}}{{\footnotesize\textit{{Nota:}} {note}}}"] if note else []
    if long:
        body = [rf"{{{size}", rf"\begin{{longtable}}{{{colspec}}}", rf"\caption{{{caption}}}\label{{{label}}}\\",
                r"\toprule", head, r"\midrule", r"\endfirsthead", r"\toprule", head, r"\midrule", r"\endhead",
                r"\bottomrule", r"\endfoot", *rows, r"\end{longtable}", *note_tex, "}"]
    else:
        body = [r"\begin{table}[H]", r"\centering", size, rf"\caption{{{caption}}}", rf"\label{{{label}}}",
                r"\resizebox{\ifdim\width>\linewidth\linewidth\else\width\fi}{!}{%",
                rf"\begin{{tabular}}{{{colspec}}}", r"\toprule", head, r"\midrule", *rows, r"\bottomrule",
                r"\end{tabular}}", *note_tex, r"\end{table}"]
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f"{name}.tex").write_text("\n".join(body), encoding="utf-8")


def write_numbers(values: dict[str, str], path: Path) -> None:
    """Macros \\newcommand para citar en el texto cifras calculadas (el texto nunca se desincroniza de los datos)."""
    lines = [rf"\newcommand{{\{k}}}{{{v}}}" for k, v in values.items()]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

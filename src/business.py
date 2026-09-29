"""VALOR PARA EL CLUB — rotación de entrenadores (dato) y ROI por escenarios (supuestos explícitos).

La parte de datos sale de fct_team_match_league (quién dirigió cada partido de la liga). La parte monetaria
son SUPUESTOS parametrizables: no hay cifras públicas verificadas de costos del América, así que el modelo
se presenta con tres escenarios y análisis de sensibilidad, y cada supuesto se documenta en ASSUMPTIONS.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ------------------------------------------------------------------ supuestos (MXN) — ajustar con el club
SCENARIOS = {
    #                       conservador  base    optimista
    "costo_cambio_tecnico": (15e6, 30e6, 50e6),   # indemnización + salario remanente + nuevo cuerpo técnico
    "prob_cambio_fallido": (0.30, 0.40, 0.50),    # prob. de que una contratación se revierta antes de 2 torneos
    "reduccion_error": (0.05, 0.10, 0.20),        # reducción relativa de esa prob. al evaluar con el ADN
    "decisiones_por_anio": (0.5, 1.0, 1.0),       # contrataciones/evaluaciones de técnico por año
    "horas_ahorradas_partido": (2, 4, 6),         # horas de analista ahorradas por partido (ficha automática)
    "partidos_por_anio": (40, 45, 50),            # partidos propios + rivales analizados
    "costo_hora_analista": (400, 600, 800),       # MXN por hora
    "costo_anual_herramienta": (400e3, 300e3, 200e3),  # mantenimiento (analista parcial); stack local sin licencias
}
ASSUMPTIONS_TEXT = {
    "costo_cambio_tecnico": "Costo de cambiar de técnico antes de tiempo: indemnización, salario remanente y nuevo cuerpo técnico.",
    "prob_cambio_fallido": "Probabilidad de que una contratación termine antes de dos torneos (se contrasta con la rotación observada).",
    "reduccion_error": "Reducción relativa de esa probabilidad al elegir con el ADN y el Índice de Encaje.",
    "decisiones_por_anio": "Evaluaciones de técnico por año (contratación o renovación).",
    "horas_ahorradas_partido": "Horas de analista ahorradas por partido gracias a la ficha automática.",
    "partidos_por_anio": "Partidos analizados por año (propios y de rivales).",
    "costo_hora_analista": "Costo por hora de un analista.",
    "costo_anual_herramienta": "Costo anual de mantener la herramienta (sin licencias: Python local).",
}


def scenario_table() -> pd.DataFrame:
    rows = []
    for i, name in enumerate(["Conservador", "Base", "Optimista"]):
        p = {k: v[i] for k, v in SCENARIOS.items()}
        ahorro_decision = p["costo_cambio_tecnico"] * p["prob_cambio_fallido"] * p["reduccion_error"] * p["decisiones_por_anio"]
        ahorro_horas = p["horas_ahorradas_partido"] * p["partidos_por_anio"] * p["costo_hora_analista"]
        beneficio = ahorro_decision + ahorro_horas
        costo = p["costo_anual_herramienta"]
        rows.append({"escenario": name, "ahorro por mejores decisiones de técnico": ahorro_decision,
                     "ahorro en horas de análisis": ahorro_horas, "beneficio anual": beneficio,
                     "costo anual": costo, "ROI": (beneficio - costo) / costo,
                     "punto de equilibrio (reducción de error)": max(0.0, (costo - ahorro_horas) / (
                         p["costo_cambio_tecnico"] * p["prob_cambio_fallido"] * p["decisiones_por_anio"]))})
    return pd.DataFrame(rows).set_index("escenario")


def sensitivity(var_a: str = "reduccion_error", var_b: str = "costo_cambio_tecnico",
                grid_a=(0.0, 0.05, 0.10, 0.15, 0.20), grid_b=(10e6, 20e6, 30e6, 50e6)) -> pd.DataFrame:
    """ROI del escenario base variando dos supuestos (tabla de sensibilidad)."""
    base = {k: v[1] for k, v in SCENARIOS.items()}
    out = pd.DataFrame(index=[f"{a:.0%}" for a in grid_a], columns=[f"{b / 1e6:.0f} M" for b in grid_b], dtype=float)
    for a in grid_a:
        for b in grid_b:
            p = {**base, var_a: a, var_b: b}
            ben = (p["costo_cambio_tecnico"] * p["prob_cambio_fallido"] * p["reduccion_error"] * p["decisiones_por_anio"]
                   + p["horas_ahorradas_partido"] * p["partidos_por_anio"] * p["costo_hora_analista"])
            out.loc[f"{a:.0%}", f"{b / 1e6:.0f} M"] = (ben - p["costo_anual_herramienta"]) / p["costo_anual_herramienta"]
    out.index.name = f"{var_a} \\ {var_b}"
    return out


# ------------------------------------------------------------------ dato: rotación de entrenadores en la Liga MX
def coach_stints(tml: pd.DataFrame) -> pd.DataFrame:
    """Periodos contiguos entrenador × equipo (un cambio de técnico abre un periodo nuevo)."""
    d = tml[tml.manager != ""].sort_values(["team_name", "match_date"])
    new = (d.manager != d.groupby("team_name").manager.shift()).astype(int)
    d = d.assign(stint=new.groupby(d.team_name).cumsum())
    pts = np.select([d.goals_for > d.goals_against, d.goals_for == d.goals_against], [3, 1], 0)
    d = d.assign(pts=pts)
    return (d.groupby(["team_name", "stint"])
            .agg(manager=("manager", "first"), desde=("match_date", "min"), hasta=("match_date", "max"),
                 partidos=("match_id", "size"), puntos_por_partido=("pts", "mean"))
            .reset_index())


def turnover_summary(stints: pd.DataFrame, official_end: str = "2025-06-30") -> pd.Series:
    s = stints[stints.desde <= pd.Timestamp(official_end)]
    torneos = 8  # ventana oficial: Apertura 2021 – Clausura 2025
    cambios = (s.groupby("team_name").size() - 1).sum()
    cortos = (s.partidos < 34).mean()  # menos de ~2 torneos
    return pd.Series({"periodos de entrenador": len(s), "equipos": s.team_name.nunique(),
                      "cambios de técnico": int(cambios), "cambios por torneo (liga)": cambios / torneos,
                      "partidos por periodo (mediana)": s.partidos.median(),
                      "% de periodos de menos de 2 torneos": cortos * 100})

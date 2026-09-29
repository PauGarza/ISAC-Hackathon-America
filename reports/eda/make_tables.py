"""Genera las tablas LaTeX del reporte de EDA a partir de los CSV de data/processed/eda
(salida del notebook 02). Uso:  python reports/eda/make_tables.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.eda_dictionary import EVENT_COLUMNS, TEAM_FAMILIES, TEAM_KEY, PLAYER_KEY  # noqa: E402

EDA = ROOT / "data" / "processed" / "eda"
OUT = Path(__file__).resolve().parent / "tables"
OUT.mkdir(exist_ok=True)

COACH_SHORT = {"Santiago Hernán Solari Poggio": "Solari", "Fernando Ortiz": "Ortiz", "André Soares Jardine": "Jardine",
               "Diego Alberto Cervantes Chávez": "Cervantes", "Jorge Guillermo Almada Álves": "Almada"}


def esc(v) -> str:
    s = str(v)
    for a, b in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}"),
                 ("≈", r"$\approx$"), ("↑", r"$\uparrow$"), ("≥", r"$\geq$"), ("μ", r"$\mu$"), ("ρ", r"$\rho$")]:
        s = s.replace(a, b)
    return s


def fmt_val(v, digits=2, as_int=True):
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
    return esc(v)


def write_table(df: pd.DataFrame, name: str, caption: str, label: str, colspec: str | None = None,
                index: bool = True, size: str = r"\small", digits: int = 2, long: bool = False,
                header: list[str] | None = None, note: str | None = None, rename_coaches: bool = True):
    df = df.copy()
    if rename_coaches:
        df = df.rename(index=COACH_SHORT, columns=COACH_SHORT)
    cols = ([esc(df.index.name or "")] if index else []) + [esc(c) for c in df.columns]
    if header:
        cols = header
    ncol = len(cols)
    colspec = colspec or ("l" + "r" * (ncol - 1))
    # formato consistente por columna: entero solo si TODA la columna es entera
    as_int = [bool(pd.api.types.is_numeric_dtype(df[c]) and df[c].dropna().apply(lambda v: float(v).is_integer()).all())
              for c in df.columns]
    rows = []
    for idx, r in df.iterrows():
        cells = ([esc(idx if not isinstance(idx, tuple) else " · ".join(map(str, idx)))] if index else [])
        cells += [fmt_val(v, digits, ai) for v, ai in zip(r.values, as_int)]
        rows.append(" & ".join(cells) + r" \\")
    head = " & ".join(rf"\textbf{{{c}}}" for c in cols) + r" \\"
    if long:
        body = "\n".join([
            rf"{{{size}", rf"\begin{{longtable}}{{{colspec}}}",
            rf"\caption{{{caption}}}\label{{{label}}}\\", r"\toprule", head, r"\midrule", r"\endfirsthead",
            r"\toprule", head, r"\midrule", r"\endhead", r"\bottomrule", r"\endfoot",
            *rows, r"\end{longtable}", "}"])
    else:
        body = "\n".join([
            r"\begin{table}[H]", r"\centering", size, rf"\caption{{{caption}}}", rf"\label{{{label}}}",
            r"\resizebox{\ifdim\width>\linewidth\linewidth\else\width\fi}{!}{%",
            rf"\begin{{tabular}}{{{colspec}}}", r"\toprule", head, r"\midrule", *rows, r"\bottomrule",
            r"\end{tabular}}",
            *( [rf"\par\smallskip\parbox{{\linewidth}}{{\footnotesize\textit{{Nota:}} {note}}}"] if note else []),
            r"\end{table}"])
    (OUT / f"{name}.tex").write_text(body, encoding="utf-8")


def rd(name, **kw):
    return pd.read_csv(EDA / f"{name}.csv", **kw)


# ------------------------------------------------------------------ inventario
def n_rows(folder):
    return sum(pq.ParquetFile(f).metadata.num_rows for f in (ROOT / "data/raw" / folder).glob("*.parquet"))


def n_cols(path):
    return len(pq.ParquetFile(path).schema_arrow.names)


P = ROOT / "data" / "processed"
inv = pd.DataFrame([
    ["matches", "1 partido del América", 222, n_cols(ROOT / "data/raw/matches_america.parquet"), 222],
    ["events", "1 evento (ambos equipos)", pq.ParquetFile(P / "events_america.parquet").metadata.num_rows, n_cols(P / "events_america.parquet"), 222],
    ["team\\_match\\_stats", "1 equipo × partido", pq.ParquetFile(P / "team_match_stats_america.parquet").metadata.num_rows, n_cols(P / "team_match_stats_america.parquet"), 221],
    ["player\\_match\\_stats", "1 jugador × partido", pq.ParquetFile(P / "player_match_stats_america.parquet").metadata.num_rows, n_cols(P / "player_match_stats_america.parquet"), 222],
    ["lineups", "1 convocado × partido", pq.ParquetFile(P / "lineups_america.parquet").metadata.num_rows, n_cols(P / "lineups_america.parquet"), 222],
    ["frames360", "1 jugador visible × evento", n_rows("frames360"), 8, len(list((ROOT / "data/raw/frames360").glob("*.parquet")))],
], columns=["Tabla", "Granularidad (1 fila =)", "Filas", "Columnas", "Partidos"]).set_index("Tabla")
inv.index = inv.index.map(lambda s: s.replace("\\_", "_"))
inv["Granularidad (1 fila =)"] = inv["Granularidad (1 fila =)"].str.replace("×", "x")
write_table(inv, "inventario", "Inventario de tablas descargadas.", "tab:inventario", colspec="llrrr")

# ------------------------------------------------------------------ cobertura
cov = rd("cobertura")
cov["team_manager"] = cov.team_manager.map(COACH_SHORT)
cov = cov.set_index(["season", "team_manager"])
cov.index.names = ["Temporada · entrenador", None]
cov.columns = ["Jugados", "Con eventos", "Con 360", "Desde", "Hasta"]
write_table(cov, "cobertura", "Cobertura por temporada y entrenador.", "tab:cobertura", colspec="lrrrll",
            header=["Temporada · entrenador", "Jugados", "Con eventos", "Con 360", "Desde", "Hasta"])

# ------------------------------------------------------------------ partidos
res = rd("matches_resultado_por_entrenador", index_col=0)
res.columns = ["\\% G", "\\% E", "\\% P", "Partidos", "GF/p", "GC/p"]
res.index.name = "Entrenador"
write_table(res, "resultado_entrenador", "Resultados del América por entrenador (todas las fases).", "tab:resultado",
            header=["Entrenador", r"\% G", r"\% E", r"\% P", "Partidos", "GF/p", "GC/p"])

mc = rd("matches_categoricas", index_col=0)[["n_categories", "mode", "mode_pct", "top_5"]]
mc["top_5"] = mc.top_5.str.replace("Santiago Hernán Solari Poggio", "Solari").str.replace("André Soares Jardine", "Jardine") \
    .str.replace("Jorge Guillermo Almada Álves", "Almada").str.replace("Diego Alberto Cervantes Chávez", "Cervantes")
mc["mode"] = mc["mode"].replace(COACH_SHORT)
write_table(mc, "matches_categoricas", "Variables categóricas de partidos: número de categorías, moda y top-5 (\\%).",
            "tab:matches_cat", colspec="lrlrp{8.3cm}", size=r"\scriptsize",
            header=["Columna", "Cat.", "Moda", r"\% moda", "Top-5 (\\% de partidos)"])
mn = rd("matches_numericas", index_col=0)[["count", "pct_null", "min", "median", "mean", "max", "std", "mode", "mode_pct", "pct_zero"]]
write_table(mn, "matches_numericas", "Variables numéricas de partidos.", "tab:matches_num", size=r"\small",
            header=["Columna", "n", r"\% nulos", "Mín", "Mediana", "Media", "Máx", "Desv.", "Moda", r"\% moda", r"\% ceros"])

# ------------------------------------------------------------------ eventos
tc = rd("events_tipos_columnas", index_col=0)
tc.index.name = "Tipo analítico"
tc.columns = ["Columnas"]
write_table(tc, "events_tipos", "Clasificación de las 162 columnas de eventos por tipo analítico.", "tab:events_tipos",
            header=["Tipo analítico", "Columnas"], colspec="lr")

ft = rd("events_frecuencia_type", index_col=0).head(20)
ft.index.name = "type"
write_table(ft, "events_type", "Frecuencia de los 20 tipos de evento más comunes (ambos equipos).", "tab:events_type",
            header=["Tipo de evento", "Eventos", r"\%", r"\% acum."], colspec="lrrr")

ecg = rd("events_categoricas_generales", index_col=0)[["pct_null", "n_categories", "mode", "mode_pct", "top_5"]]
write_table(ecg, "events_cat_generales", "Variables categóricas generales de eventos.", "tab:events_cat", colspec="lrrlrp{7cm}",
            size=r"\scriptsize", header=["Columna", r"\% nulos", "Cat.", "Moda", r"\% moda", "Top-5 (\\%)"])

en = rd("events_numericas", index_col=0)
keep = ["minute", "duration", "location_x", "location_y", "obv_total_net", "control_degree",
        "pass_length", "pass_angle", "pass_pass_success_probability", "pass_xclaim",
        "shot_statsbomb_xg", "shot_shot_execution_xg", "shot_gk_save_difficulty_xg",
        "duel_duel_win_probability", "clearance_duel_win_probability"]
en = en.loc[[k for k in keep if k in en.index], ["event_type", "count", "pct_null", "min", "p25", "median", "mean", "p75", "max", "std", "skew"]]
write_table(en, "events_numericas", "Variables numéricas de eventos, cada una perfilada sobre el tipo de evento al que aplica.",
            "tab:events_num", size=r"\scriptsize", digits=3,
            header=["Columna", "Aplica a", "n", r"\% nulos", "Mín", "P25", "Mediana", "Media", "P75", "Máx", "Desv.", "Asim."],
            colspec="llrrrrrrrrrr")

eb = rd("events_booleanas", index_col=0)
eb = eb[eb.pct_true >= 1].sort_values(["event_type", "pct_true"], ascending=[True, False])[["event_type", "rows", "n_true", "pct_true"]]
write_table(eb, "events_booleanas", "Flags booleanos (\\% de filas con \\texttt{True} dentro del tipo de evento; NaN = False). Se muestran los que superan 1\\%.",
            "tab:events_bool", size=r"\scriptsize", long=True, colspec="llrrr",
            header=["Flag", "Aplica a", "Filas", "True", r"\% True"])

po = rd("posesiones_numericas", index_col=0)[["count", "min", "p25", "median", "mean", "p75", "p95", "max", "pct_zero", "skew"]]
po.index = po.index.map({"n_events": "eventos", "n_passes": "pases", "start_x": "x inicial", "max_x": "x máxima",
                         "dur_s": "duración (s)", "xg": "xG"}.get)
write_table(po, "posesiones", "Perfil de las 47,033 posesiones (ambos equipos).", "tab:posesiones", digits=2,
            header=["Variable", "n", "Mín", "P25", "Mediana", "Media", "P75", "P95", "Máx", r"\% ceros", "Asim."])

# ------------------------------------------------------------------ team stats
tn = rd("team_numericas", index_col=0)
tn = tn.loc[[k for k in TEAM_KEY if k in tn.index], ["min", "p25", "median", "mean", "p75", "max", "std", "skew"]]
write_table(tn, "team_numericas", "Métricas clave del América por partido (221 partidos).", "tab:team_num", size=r"\scriptsize",
            header=["Métrica", "Mín", "P25", "Mediana", "Media", "P75", "Máx", "Desv.", "Asim."])
tt = rd("team_top_correlaciones", index_col=0).head(15)
write_table(tt, "team_top_corr", "Pares de métricas de equipo con mayor correlación de Spearman: redundancias por construcción.",
            "tab:team_top_corr", index=False, size=r"\scriptsize", header=["Variable 1", "Variable 2", r"$\rho$"], colspec="llr")
gd = rd("team_correlacion_con_gd", index_col=0).head(18)
write_table(gd, "team_corr_gd", "Métricas de equipo más asociadas a la diferencia de goles del partido (Spearman).", "tab:team_gd",
            size=r"\small", header=["Métrica", r"$\rho$ con diferencia de goles"], colspec="lr")

# ------------------------------------------------------------------ jugadores
pn = rd("player_numericas", index_col=0)
pn = pn.loc[[k for k in PLAYER_KEY if k in pn.index], ["count", "median", "mean", "p95", "max", "pct_zero", "skew"]]
write_table(pn, "player_numericas", "Métricas clave por jugador y partido (América).", "tab:player_num", size=r"\scriptsize",
            header=["Métrica", "n", "Mediana", "Media", "P95", "Máx", r"\% ceros", "Asim."])
pm = rd("player_minutos_totales", index_col=0).head(15)
write_table(pm, "player_minutos", "Jugadores con más minutos (2021--2026) y su OBV por 90 minutos.", "tab:player_min",
            header=["Jugador", "Partidos", "Minutos", "OBV/90"], colspec="lrrr")

# ------------------------------------------------------------------ alineaciones / formaciones / 360
fo = rd("formaciones_por_entrenador", index_col=0)
fo = fo.rename(columns=COACH_SHORT)
fo.index = fo.index.map(lambda f: "-".join(str(f)) if f != "All" else "Total")
fo.index.name = "Formación inicial"
write_table(fo, "formaciones", "Formación inicial (evento \\texttt{Starting XI}) por entrenador.", "tab:formaciones",
            header=["Formación"] + list(fo.columns))
lp = rd("lineups_posiciones_categoricas", index_col=0)[["count", "n_categories", "mode", "mode_pct", "top_8"]]
write_table(lp, "lineups_pos", "Posiciones jugadas y razones de entrada/salida (América).", "tab:lineups_pos",
            colspec="lrrlrp{7.2cm}", size=r"\scriptsize", header=["Columna", "n", "Cat.", "Moda", r"\% moda", "Top-8 (\\%)"])
f3 = rd("frames360_por_evento", index_col=0)[["count", "min", "p25", "median", "mean", "p75", "max", "std"]]
f3.index = f3.index.map({"visibles": "jugadores visibles", "companeros": "compañeros", "rivales": "rivales"}.get)
write_table(f3, "frames360", "Jugadores visibles por evento en StatsBomb 360 (muestra de 20 partidos).", "tab:frames360",
            header=["Variable", "Eventos", "Mín", "P25", "Mediana", "Media", "P75", "Máx", "Desv."])

# ------------------------------------------------------------------ contexto
cm = rd("contexto_metricas_nuevas", index_col=0)[["count", "min", "p25", "median", "mean", "p75", "max", "std"]]
write_table(cm, "ctx_metricas_nuevas", "Métricas derivadas de eventos (definiciones en la Sección~\\ref{sec:metodologia}).",
            "tab:ctx_new", header=["Métrica", "n", "Mín", "P25", "Mediana", "Media", "P75", "Máx", "Desv."])
bc = rd("contexto_por_entrenador", index_col=0)
write_table(bc, "ctx_entrenador", "Métricas por partido según entrenador: mediana [P25--P75].", "tab:ctx_coach",
            size=r"\scriptsize", colspec="lllll", header=["Métrica"] + list(bc.columns))
to = rd("contexto_por_torneo", index_col=[0, 1])
to = to[["possession", "field_tilt", "ppda", "pressure_x_mean", "progressive_passes", "pass_completion",
         "gk_long_pass_ratio", "np_xg", "np_xg_conceded", "partidos", "% victorias"]]
to.index = to.index.map(lambda t: (t[0], COACH_SHORT.get(t[1], t[1])))
write_table(to, "ctx_torneo", "Evolución por torneo (medianas por partido).", "tab:ctx_torneo", size=r"\scriptsize",
            header=["Torneo · entrenador", "Posesión", "Field tilt", "PPDA", "x presión", "Pases prog.", "Precisión",
                    "Saque largo GK", "np xG", "np xG c.", "n", r"\% G"])


def ctx_long(name, keycols, metrics):
    d = rd(name, index_col=0, header=[0, 1]).T
    d = d[metrics]
    d.index = d.index.map(lambda t: (COACH_SHORT.get(t[0], t[0]), t[1]))
    return d


MET = ["possession", "field_tilt", "ppda", "pressure_x_mean", "progressive_passes", "pass_completion", "np_xg", "np_xg_conceded", "partidos"]
HDR = ["Posesión", "Field tilt", "PPDA", "x presión", "Pases prog.", "Precisión", "np xG", "np xG c.", "n"]
write_table(ctx_long("contexto_localia", 2, MET).astype(float), "ctx_localia", "Medianas por partido según localía.", "tab:ctx_localia",
            size=r"\scriptsize", header=["Entrenador · localía"] + HDR)
nr = ctx_long("contexto_nivel_rival", 2, MET).astype(float)
nr = nr.reindex([(c, t) for c in ["Solari", "Ortiz", "Jardine", "Almada"] for t in ["Alto", "Medio", "Bajo"] if (c, t) in nr.index])
write_table(nr, "ctx_rival", "Medianas por partido según el nivel del rival (tercil de puntos por partido en la temporada).",
            "tab:ctx_rival", size=r"\scriptsize", header=["Entrenador · rival"] + HDR)
rr = rd("contexto_resultado_nivel_rival", index_col=[0, 1])
rr = rr.reindex([(c, t) for c in ["Solari", "Ortiz", "Jardine", "Almada"] for t in ["Alto", "Medio", "Bajo"] if (c, t) in rr.index])
write_table(rr, "ctx_rival_resultado", "Distribución de resultados según nivel del rival (\\% de partidos).", "tab:ctx_rival_res",
            header=["Entrenador · rival", r"\% G", r"\% E", r"\% P", "n"])
fz = ctx_long("contexto_fase_torneo", 2, MET).astype(float)
write_table(fz, "ctx_fase", "Medianas por partido en fase regular y liguilla.", "tab:ctx_fase", size=r"\scriptsize",
            header=["Entrenador · fase"] + HDR)
em = rd("contexto_estado_marcador", index_col=[0, 1])
write_table(em, "ctx_marcador", "Comportamiento según el estado del marcador (diferencia de goles antes de cada evento).",
            "tab:ctx_marcador", size=r"\scriptsize",
            header=["Entrenador · estado", r"\% eventos", r"\% pases AME", "x pases", "x presiones", r"\% presión campo rival",
                    "xG/100 pases", "xG rival/100 pases"])
sp = rd("contexto_balon_parado_xg_share", index_col=[0, 1])
sp.columns = [c.replace("From ", "").replace("Regular Play", "Juego abierto") for c in sp.columns]
write_table(sp, "ctx_balon_parado", "Origen del xG (\\% del total) por patrón de juego: América y sus rivales.", "tab:ctx_bp",
            size=r"\scriptsize", digits=1, header=["Lado · entrenador"] + list(sp.columns))
su = rd("contexto_sustituciones", index_col=0)
write_table(su, "ctx_sustituciones", "Sustituciones del América por entrenador.", "tab:ctx_subs", size=r"\scriptsize",
            header=["Entrenador", "Cambios", "Min. mediano", r"\% al descanso", "Por partido", "1.er cambio (min)",
                    r"\% empatando", r"\% ganando", r"\% perdiendo"])
sh = rd("contexto_cambios_tacticos", index_col=0)
write_table(sh, "ctx_tacticos", "Cambios tácticos en vivo (evento \\texttt{Tactical Shift}) del América.", "tab:ctx_tacticos",
            header=["Entrenador", "Por partido", r"\% empatando", r"\% ganando", r"\% perdiendo"])

# ------------------------------------------------------------------ diccionarios
dic = pd.DataFrame(EVENT_COLUMNS, columns=["Columna", "Aplica a", "Significado"]).set_index("Columna")
write_table(dic, "dic_eventos", "Diccionario de columnas de eventos.", "tab:dic_eventos", long=True, size=r"\scriptsize",
            colspec="p{4.3cm}p{2.2cm}p{8.8cm}", header=["Columna", "Aplica a", "Significado"])
fam = pd.DataFrame(TEAM_FAMILIES, columns=["Familia / prefijo", "Significado"]).set_index("Familia / prefijo")
write_table(fam, "dic_familias", "Familias de métricas agregadas (\\texttt{team\\_match\\_*} y \\texttt{player\\_match\\_*}).",
            "tab:dic_familias", long=True, size=r"\scriptsize", colspec="p{4.3cm}p{11.2cm}", header=["Familia / prefijo", "Significado"])
print("tablas:", len(list(OUT.glob("*.tex"))))

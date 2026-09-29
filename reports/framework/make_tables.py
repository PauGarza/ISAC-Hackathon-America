"""Genera las tablas LaTeX y las cifras (numbers.tex) del reporte del marco analítico a partir de
data/gold/analysis/ (salida del notebook 03), de las model cards y de las fichas generadas.

Uso:  python reports/framework/make_tables.py
"""
from __future__ import annotations

import base64
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src import features as F  # noqa: E402
from src.latex import esc, write_numbers, write_table  # noqa: E402
from src.pipeline.config import GOLD, MODELS, REPORTS  # noqa: E402

A = GOLD / "analysis"
HERE = Path(__file__).resolve().parent
OUT = HERE / "tables"
FIG = ROOT / "reports" / "figures" / "framework"


def rd(name: str) -> pd.DataFrame:
    return pd.read_parquet(A / f"{name}.parquet")


def t(df, name, caption, label, **kw):
    write_table(df, OUT, name, caption, label, **kw)


N = {}  # cifras citadas en el texto

# ------------------------------------------------------------------ 1. problema
tasks = rd("tasks")
t(tasks[["nombre", "reto", "unidad (Gold)", "y", "x", "tipo", "modelos", "P"]], "tareas",
  "Formulación de las tareas: variable objetivo ($y$), explicativas ($x$), tipo de problema, modelos (del baseline a los candidatos) y medida de desempeño ($P$).",
  "tab:tareas", colspec="l p{2.1cm} p{0.9cm} p{1.8cm} p{2.1cm} p{3.2cm} p{1.5cm} p{2.6cm} p{1.5cm}", size=r"\scriptsize")

# ------------------------------------------------------------------ 2. arquitectura y marco
b = rd("layers_bronze")
b.index.name = "endpoint"
t(b.rename(columns={"status_200": "% status 200", "vacios": "respuestas vacías"}), "bronze",
  "Capa Bronze: recursos extraídos por endpoint (manifest).", "tab:bronze", digits=1)
N.update(nRecursos=f"{int(b.recursos.sum()):,}", mbBronze=f"{b.MB.sum():,.0f}")
s = rd("layers_silver")
s.index.name = "tabla"
t(s, "silver", "Capa Silver: tablas Parquet (para \\texttt{events} y \\texttt{frames360}, filas totales y número de particiones por temporada).",
  "tab:silver", header=["tabla", "filas", "columnas / particiones"])
N.update(nEventos=f"{int(s.loc['events', 'filas']):,}", nFilasTresSesenta=f"{int(s.loc['frames360', 'filas']):,}",
         nLiga=f"{int(s.loc['league_matches', 'filas']):,}")
gd = rd("layers_gold")
gd.index.name = "tabla"
t(gd, "gold", "Capa Gold: tablas por caso de uso.", "tab:gold")
N.update(nPosesiones=f"{int(gd.loc['fct_possession', 'filas']):,}", nSegmentos=f"{int(gd.loc['fct_segment', 'filas']):,}",
         nCambios=f"{int(gd.loc['fct_substitution', 'filas']):,}", nJugPartido=f"{int(gd.loc['fct_player_match', 'filas']):,}",
         nPartidos=f"{int(gd.loc['dim_match', 'filas']):,}", nVarPartido=f"{int(gd.loc['match_features', 'columnas'])}")

asm = rd("assumptions")
asm.index.name = "supuesto"
t(asm, "assumptions", "Supuestos y umbrales del marco (\\texttt{framework.ASSUMPTIONS}).", "tab:assumptions",
  colspec="l p{9cm}", size=r"\footnotesize")

v = rd("validations").set_index("validación")
t(v, "validations", "Validación del marco analítico contra StatsBomb y contra datos oficiales.", "tab:validations",
  colspec="p{8.5cm}rrc", digits=3)
vv = v.valor
N.update(rhoPPDA=f"{vv.filter(like='PPDA').iloc[0]:.2f}", rhoPos=f"{vv.filter(like='Posesión').iloc[0]:.2f}",
         rhoXG=f"{vv.filter(like='np xG').iloc[0]:.2f}", rhoDef=f"{vv.filter(like='Altura').iloc[0]:.2f}",
         pctTransSB=f"{vv.filter(like='detectadas').iloc[0]:.0f}", ratioMin=f"{vv.filter(like='Minutos').iloc[0]:.2f}")

sens = rd("sensitivity")
sens = sens.assign(supuesto=sens.supuesto + np.where(sens.base, " (base)", ""))
t(sens.set_index("supuesto")[["valor", "métrica", "media", "rho_vs_base"]], "sensitivity",
  "Sensibilidad de las métricas a los umbrales: nivel medio y correlación de Spearman del ranking de partidos con la versión base.",
  "tab:sensitivity", header=["supuesto", "valor", "métrica", "media", r"$\rho$ vs base"], digits=3)
N["rhoSensMin"] = f"{sens.rho_vs_base.min():.2f}"

# ------------------------------------------------------------------ 3. variables
cat = rd("catalog")
t(cat[["etiqueta", "criterio", "definición", "dirección"]], "catalog",
  "Catálogo de variables por partido (\\texttt{features.FEATURES} y \\texttt{PLAYER\\_FEATURES}).", "tab:catalog",
  colspec="p{3.4cm} p{3.3cm} p{2.2cm} p{5.2cm} p{2.6cm}", size=r"\scriptsize", long=True)
N["nVariables"] = str(len(cat))

ev = rd("variable_evaluation")
ev_tab = ev[["etiqueta", "criterio", "fiabilidad_SB", "ICC1", "lag1", "R2_contexto", "max_abs_rho", "rho_np_xg_diff", "nucleo", "motivo"]]
t(ev_tab.set_index("etiqueta"), "variable_evaluation",
  "Evaluación de las variables como criterios. Fiab.\\ = fiabilidad intra-partido (Spearman-Brown); ICC = ICC(1) con dos tiempos; "
  "lag-1 = autocorrelación entre partidos; $R^2$ ctx = variación explicada por localía, rival y fase; máx $|\\rho|$ = redundancia; "
  "$\\rho$ xG = validez frente al diferencial de np xG.", "tab:varEval",
  header=["variable", "criterio", "fiab.", "ICC", "lag-1", r"$R^2$ ctx", r"máx $|\rho|$", r"$\rho$ xG", "núcleo", "motivo"],
  colspec="p{4.2cm} p{2.3cm} rrrrrrc p{2.9cm}", size=r"\scriptsize", long=True)
core = ev[ev.nucleo]
N.update(nNucleo=str(len(core)), nFiabBaja=str((ev.motivo == "fiabilidad baja").sum()))
cc = core.groupby("criterio").size().rename("núcleo").to_frame().join(ev.groupby("criterio").size().rename("evaluadas"))
t(cc[["evaluadas", "núcleo"]], "core_by_criterion", "Variables evaluadas y seleccionadas como núcleo por criterio.", "tab:coreCrit")

# ------------------------------------------------------------------ 4. partición
sp = rd("split")
sp["desde"], sp["hasta"] = sp.desde.astype(str).str[:10], sp.hasta.astype(str).str[:10]
t(sp, "split", "Partición temporal por partido.", "tab:split", colspec="lrll p{7cm}", size=r"\footnotesize")
N.update(nTrain=str(int(sp.loc["train", "partidos"])), nVal=str(int(sp.loc["val", "partidos"])), nTest=str(int(sp.loc["test", "partidos"])),
         testDesde=sp.loc["test", "desde"])

# ------------------------------------------------------------------ 5. modelos
t1 = rd("t1_results")
t(t1.set_index("etiqueta")[["mejor (CV)", "MAE media histórica", "MAE media móvil 5", "MAE mejor", "R2 mejor", "mejora vs mejor baseline (%)"]],
  "t1", "T1 -- MAE en la prueba temporal: mejor modelo (elegido por validación cruzada) frente a los dos baselines.", "tab:t1",
  header=["variable", "modelo", "media hist.", "media móvil 5", "modelo", r"$R^2$", r"mejora (\%)"], digits=2)
N.update(nTunoSupera=str(int(t1.supera.sum())), nTuno=str(len(t1)),
         tunoMejoraMax=f"{t1['mejora vs mejor baseline (%)'].max():.0f}")
la = rd("t1_assumptions")
t(la.set_index("etiqueta")[["R2_train", "Durbin_Watson", "BP_p", "JB_p", "VIF_max"]], "t1_assumptions",
  "T1 -- Diagnóstico de supuestos del modelo lineal (OLS en entrenamiento + validación).", "tab:t1Assump",
  header=["variable", r"$R^2$ train", "Durbin-Watson", "BP (p)", "JB (p)", "VIF máx"], digits=3)
N.update(rivalPos=f"{la.loc['possession_time_pct', 'coef_rival']:.1f}", rivalTilt=f"{la.loc['field_tilt', 'coef_rival']:.1f}",
         localTilt=f"{la.loc['field_tilt', 'coef_local']:.1f}", localPress=f"{la.loc['high_press_pct', 'coef_local']:.1f}",
         rivalLong=f"{la.loc['long_pass_pct', 'coef_rival']:.1f}")

t2 = rd("t2_results")
t(t2.set_index("etiqueta"), "t2", "T2 -- MAE en prueba por tramo de 15' y estado del marcador.", "tab:t2",
  header=["variable", "baseline", "Ridge", "Árbol", r"$R^2$ Ridge"], digits=2)
gs = rd("t2_game_state_coefs")
gs.index.name = "variable"
t(gs, "t2_coefs", "T2 -- Coeficientes de Ridge del estado del marcador (diferencia respecto al empate, en unidades de la variable).",
  "tab:t2Coefs", digits=1)
N.update(tiltPierde=f"{gs.loc['Field tilt (%)', 'Pierde por 1']:+.1f}", tiltGana=f"{gs.loc['Field tilt (%)', 'Gana por 1']:+.1f}",
         posPierde=f"{gs.loc['Posesión (% del tiempo)', 'Pierde por 1']:+.1f}", posGana=f"{gs.loc['Posesión (% del tiempo)', 'Gana por 1']:+.1f}")

t3 = rd("t3_results")
t(t3.rename(index={"obv_net": "OBV neto", "np_xg_diff": "Diferencial np xG"}), "t3",
  "T3 -- MAE en prueba de los modelos de dominio con métricas de proceso.", "tab:t3", digits=3)
N.update(tresRdos=f"{t3.loc['np_xg_diff', 'R2 LASSO']:.2f}", tresNvar=str(int(t3.loc['np_xg_diff', 'variables elegidas'])))
l3 = rd("t3_lasso_np_xg_diff")
t(l3.set_index("etiqueta")[["coef", "estabilidad"]], "t3_lasso",
  "T3 -- Variables elegidas por LASSO para el diferencial de np xG: coeficiente (x estandarizadas) y estabilidad (\\% de 100 remuestreos bootstrap en que se elige).",
  "tab:t3Lasso", digits=3)
t3b = rd("t3b_results")
t(t3b, "t3b", "T3b -- Resultado del partido (G/E/P) en prueba.", "tab:t3b", header=["modelo", "exactitud", "F1 macro"], digits=3)
cm = rd("t3b_confusion")
cm.index.name = "real \\textbackslash{} predicho"
t4 = rd("t4_results")
t(t4, "t4", "T4 -- ¿La posesión termina en tiro? Métricas en prueba.", "tab:t4",
  header=["modelo", "ROC-AUC", "prevalencia", "F1", "Brier"], digits=3)
N.update(cuatroAUC=f"{t4.loc['Logística', 'ROC_AUC']:.2f}", cuatroPrev=f"{t4.loc['Baseline: tasa base', 'PR_AUC(prevalencia)'] * 100:.0f}")
c4 = rd("t4_coefs")
c4.index.name = "variable (one-hot)"
t(c4, "t4_coefs", "T4 -- Coeficientes de la regresión logística (log-odds, x estandarizadas): los 6 más negativos y los 6 más positivos.",
  "tab:t4Coefs", digits=3)
t5 = pd.concat({"A favor": rd("t5_favor_results"), "En contra": rd("t5_contra_results")})
t(t5, "t5", "T5 -- ¿El balón parado termina en tiro? Métricas en prueba.", "tab:t5",
  header=["conjunto · modelo", "ROC-AUC", "prevalencia", "F1", "Brier"], digits=3)
r5 = rd("t5_rates")
t(r5, "t5_rates", "T5 -- Balón parado a favor: \\% que termina en tiro por tipo y zona de destino (grupos con $\\geq$ 20 jugadas).",
  "tab:t5Rates", header=["tipo · zona", "jugadas", r"\% tiro", "xG"], digits=2)
t6 = rd("t6_results")
t(t6.rename(index={"d_obv_net": r"$\Delta$ OBV neto", "d_field_tilt": r"$\Delta$ field tilt", "d_np_xg_diff": r"$\Delta$ np xG"}),
  "t6", "T6 -- Impacto de las sustituciones: MAE en prueba frente a dos baselines.", "tab:t6", digits=3)
t7 = rd("t7_results")
t(t7.set_index("etiqueta"), "t7", "T7 -- Distribución del juego según el contexto: MAE en prueba.", "tab:t7",
  header=["variable", "modelo", "MAE modelo", "media móvil 5", "media hist."], digits=3)

u1 = rd("u1_explained")
t(u1, "u1", "U1 -- Varianza explicada por las componentes retenidas (PCA ajustado con train).", "tab:u1", digits=3)
N.update(pcUnoVar=f"{u1.varianza.iloc[0] * 100:.0f}", nPC=str(len(u1)))
ld = rd("u1_loadings")
ld.index.name = "variable"
t(ld, "u1_loadings", "U1 -- Cargas de las componentes principales.", "tab:u1Load", digits=2, size=r"\footnotesize")
pr = rd("u2_profiles")
dom_order = pr.iloc[0].sort_values(ascending=False).index  # el número de clúster es arbitrario: Tipo 1 = más posesión
pr = pr[dom_order]
pr.columns = ["Tipo 1 (dominante)", "Tipo 2 (reactivo)"][:len(pr.columns)]
pr.index.name = "variable (media en train)"
t(pr, "u2_profiles", "U2 -- Perfil medio de cada tipo de partido (entrenamiento).", "tab:u2", digits=2)
N.update(tipoUnoPos=f"{pr.iloc[0, 0]:.0f}", tipoDosPos=f"{pr.iloc[0, 1]:.0f}", tipoUnoTilt=f"{pr.iloc[1, 0]:.0f}",
         tipoDosTilt=f"{pr.iloc[1, 1]:.0f}", tipoUnoPPDA=f"{pr.iloc[2, 0]:.1f}", tipoDosPPDA=f"{pr.iloc[2, 1]:.1f}")
bt = rd("u2_by_torneo")[dom_order]
bt.columns = ["Tipo 1 dominante (\\%)", "Tipo 2 reactivo (\\%)"][:len(bt.columns)]
t(bt, "u2_torneo", "U2 -- Porcentaje de partidos de cada tipo por torneo.", "tab:u2Torneo", digits=0)
sil = rd("u2_silhouette")
N["silDos"] = f"{sil.silhouette.max():.2f}"
ro = rd("u3_roles").set_index("rol")
t(ro, "u3", "U3 -- Roles de jugador (K-means sobre perfiles p90, ajustado con train).", "tab:u3", digits=0)
N.update(nRoles=str(len(ro)), silRoles=f"{rd('u3_silhouette').silhouette.max():.2f}")

# ------------------------------------------------------------------ 6. evaluación y monitoreo
mc = rd("model_cards")
mc.index.name = "model card"
show = mc[[c for c in ["task", "model", "test_MAE", "baseline_MAE", "test_ROC_AUC", "test_F1_macro", "beats_baseline"] if c in mc]]
t(show, "model_cards", "Resumen de las model cards: métrica en la prueba temporal frente al mejor baseline.", "tab:cards",
  header=["model card", "tarea", "modelo", "MAE", "MAE baseline", "ROC-AUC", "F1 macro", "supera"], digits=3, size=r"\scriptsize", long=True)
sup = mc.beats_baseline.dropna().astype(bool)
N.update(nCards=str(len(mc)), nSupervisados=str(len(sup)), nSupera=str(int(sup.sum())))
ov = rd("overfitting")
t(ov, "overfitting", "Diagnóstico de sobreajuste (T1): MAE del modelo elegido en cada conjunto.", "tab:overfit", digits=2)
dr = rd("drift_latest")
t(dr, "drift", "Monitoreo de drift: PSI de los últimos 10 partidos frente a entrenamiento, con umbrales calibrados por remuestreo.",
  "tab:drift", header=["variable", "PSI", "p90 nulo", "p99 nulo", "media train", "media reciente", "estado"], digits=3)

# ------------------------------------------------------------------ ADN del entrenador (notebook 04)
cp = rd("coach_america_percentiles")
cp.index.name = "técnico"
t(cp, "coach_percentiles", "ADN de los técnicos del América: percentil de cada rasgo frente a los técnicos de la Liga MX "
  "(ajustado por rival y localía). Almada, con sus partidos de 2026 (prueba).", "tab:coachPct", digits=0,
  size=r"\footnotesize")
axt = rd("coach_axes")
t(axt, "coach_axes", r"Los 8 rasgos del ADN del entrenador y sus métricas de StatsBomb.", "tab:coachAxes",
  colspec="l p{5.2cm} p{6.4cm}", size=r"\footnotesize")
eta = rd("coach_identity_eta")
eta.index.name = "rasgo"
t(eta, "coach_identity", r"Identidad del club frente a identidad del técnico: proporción de la variación entre partidos "
  r"del América (2021--2025) explicada por el técnico ($\eta^2$).", "tab:coachEta", digits=2)
fit = rd("coach_fit_top15").head(10)
t(fit, "coach_fit", "Índice de Encaje: los 10 técnicos-club de la liga más parecidos a la identidad histórica del América.",
  "tab:coachFit", header=["técnico (club)", "Índice de Encaje", "distancia", "partidos"], digits=1)
acc = rd("coach_classifier_topk")
acc_show = acc.copy()
acc_show.index = ["validación (Apertura 2025)", "prueba (2026)"]
t(acc_show, "coach_topk", "¿El ADN reconoce al técnico en partidos que nunca vio? Proporción de partidos de la liga en que el "
  "técnico real está entre los k más probables (31 técnicos posibles).", "tab:coachTopk", digits=2)
ca = rd("coach_classifier_america")
t(ca, "coach_america_rank", "Partidos del América fuera de la ventana oficial: posición del técnico real en el ranking.",
  "tab:coachAmRank", header=["técnico · conjunto", "partidos", "posición mediana", r"\% en top 3"], digits=1)
N.update(almadaRank=f"{ca.loc[('Almada', 'test'), 'posicion_mediana']:.0f}",
         almadaTopTres=f"{ca.loc[('Almada', 'test'), 'en_top3']:.0f}",
         topCincoTest=f"{acc.loc['test', 'top-5'] * 100:.0f}",
         azarCinco=f"{acc.loc['test', 'azar top-1'] * 500:.0f}",
         nTecnicos=str(pd.read_parquet(GOLD / "fct_team_match_league.parquet").manager.replace("", np.nan).nunique()))
to = rd("coach_turnover")
to.index.name = "indicador"
t(to, "coach_turnover", "Rotación de técnicos en la Liga MX (ventana oficial, 2021--2025).", "tab:turnover", digits=1)
N.update(cambiosTecnico=f"{int(to.loc['cambios de técnico', 'valor'])}",
         pctCortos=f"{to.loc['% de periodos de menos de 2 torneos', 'valor']:.0f}")
roi = rd("coach_roi_scenarios")
roi_show = roi.copy()
money = [c for c in roi.columns if c not in ("ROI", "punto de equilibrio (reducción de error)")]
roi_show[money] = roi_show[money] / 1e6
roi_show = roi_show.rename(columns={c: c + " (M MXN)" for c in money})
t(roi_show.T, "roi", r"ROI anual por escenario (montos en millones de pesos; supuestos en la Tabla~\ref{tab:roiAssump}).",
  "tab:roi", digits=2)
N.update(roiBase=f"{roi.loc['Base', 'ROI']:.1f}", roiCons=f"{roi.loc['Conservador', 'ROI']:.1f}",
         equilibrioBase=f"{roi.loc['Base', 'punto de equilibrio (reducción de error)'] * 100:.0f}")
ra = rd("coach_roi_assumptions")
ra.index.name = "supuesto"
t(ra, "roi_assumptions", "Supuestos del modelo de ROI (a validar con el club).", "tab:roiAssump",
  colspec="l r r r p{5.8cm}", size=r"\scriptsize", digits=2)
hy = rd("coach_hypotheses")
t(hy, "coach_hypotheses", "Veredicto preliminar de hipótesis del EDA con el ADN del entrenador y la partición oficial.",
  "tab:coachHyp", colspec="l p{4.6cm} p{9.2cm}", size=r"\footnotesize")

# ------------------------------------------------------------------ cifras de jugadores y fichas
mf = pd.read_parquet(GOLD / "match_features.parquet")
N.update(medTopTres=f"{mf.top3_obv_share.median():.0f}", medTopUno=f"{mf.top1_obv_share.median():.0f}",
         medBoost=f"{mf.boost_pct.median():.0f}", medShareDef=f"{mf.obv_share_def.median():.0f}",
         medShareMid=f"{mf.obv_share_mid.median():.0f}", medShareFwd=f"{mf.obv_share_fwd.median():.0f}",
         medShareWide=f"{mf.obv_share_wide.median():.0f}", medGiniTouch=f"{mf.gini_touches.median():.2f}")
card = json.loads((MODELS / "T1_field_tilt.json").read_text(encoding="utf-8"))
card_txt = json.dumps({k: card[k] for k in ["name", "task", "target", "model", "features", "params", "train_dates",
                                            "baseline", "test_MAE", "baseline_MAE", "beats_baseline", "data_hash"]},
                      indent=1, ensure_ascii=False, default=lambda x: round(x, 3))
card_txt = re.sub(r"(\d+\.\d{3})\d+", r"\1", card_txt)
(OUT / "card_example.txt").write_text(card_txt, encoding="utf-8")

# figuras de la ficha de ejemplo (final Apertura 2024) para el reporte
ficha = REPORTS / "2024-12-16_Monterrey.html"
if ficha.exists():
    imgs = re.findall(r'base64,([A-Za-z0-9+/=]+)"', ficha.read_text(encoding="utf-8"))
    for i, name in enumerate(["ficha_percentiles", "ficha_players", "ficha_style_map", "ficha_timeline", "ficha_dna",
                              "ficha_set_pieces"]):
        (FIG / f"{name}.png").write_bytes(base64.b64decode(imgs[i]))

write_numbers(N, OUT / "numbers.tex")
print(f"{len(list(OUT.glob('*.tex')))} archivos .tex · {len(N)} cifras")

"""HIPÓTESIS DEL EQUIPO (comentarios de Emi, 16 oct) — se prueban antes de entrar al reporte.

Notebook 06 (`06_hipotesis_equipo.ipynb`) consume estas funciones. Reglas:
- Casi todo sale del cubo por partido (src/cube.py). Lo que necesita tramos de 15' con número de posesiones o
  posesiones sueltas usa Gold (fct_segment, fct_possession, fct_substitution), siempre agregado.
- Comparar SIEMPRE dentro del mismo técnico y del mismo nivel de rival (`strat_perm`): así una diferencia no es
  "Jardine contra Solari" ni "partidos contra Puebla contra partidos contra Tigres".
- Para el plan de juego (posesión, presión) se mide con el partido EMPATADO (`plan_empate`): con el marcador
  movido, el plan es consecuencia del resultado, no causa.
- Veredicto (`veredicto`): "se sostiene" / "no cambia" / "no alcanza" con reglas fijas, escritas antes de mirar.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src import cube as K

COACHES = ["Solari", "Ortiz", "Jardine"]
STRATA = ["coach", "rival_nivel"]
ALPHA = 0.10            # umbral de evidencia (dos colas) para "se sostiene"
MIN_GROUP = 8           # partidos mínimos por grupo para concluir algo
MIN_DRAW_MIN = 15       # minutos empatados mínimos para medir el plan de un partido
SERIES_STAGE = {"Play-in": "Play-in", "Cuartos": "Cuartos", "Semifinal": "Semifinal", "Final": "Final perdida"}


# ------------------------------------------------------------------ prueba común
def strat_perm(d: pd.DataFrame, y: str, g: str, strata=STRATA, n: int = 5000, seed: int = 0) -> dict:
    """Diferencia de medias de `y` entre `g` verdadero y falso, promediada DENTRO de cada estrato (peso = media
    armónica de los dos tamaños) y su p de permutación (se barajan las etiquetas dentro de cada estrato).
    También la diferencia en desviaciones estándar de `y` (tamaño del efecto, para comparar métricas)."""
    d = d.dropna(subset=[y, g]).copy()
    d[g] = d[g].astype(bool)
    keys = (d[list(strata)].astype("string").fillna("—").agg("|".join, axis=1).to_numpy() if strata
            else np.zeros(len(d)))
    yv, gv = d[y].to_numpy(float), d[g].to_numpy(bool)
    groups = [np.flatnonzero(keys == k) for k in pd.unique(keys)]
    groups = [ix for ix in groups if gv[ix].any() and (~gv[ix]).any()]
    if not groups:
        return {"dif": np.nan, "dif_sd": np.nan, "p": np.nan, "n_si": int(gv.sum()), "n_no": int((~gv).sum())}
    w = np.array([1 / (1 / gv[ix].sum() + 1 / (~gv[ix]).sum()) for ix in groups])

    def stat(lab):
        return np.average([yv[ix][lab[ix]].mean() - yv[ix][~lab[ix]].mean() for ix in groups], weights=w)

    obs = stat(gv)
    rng = np.random.default_rng(seed)
    perm = np.empty(n)
    lab = gv.copy()
    for i in range(n):
        for ix in groups:
            lab[ix] = rng.permutation(gv[ix])
        perm[i] = stat(lab)
    used = np.concatenate(groups)
    sd = yv[used].std(ddof=1)
    return {"dif": obs, "dif_sd": obs / sd if sd > 0 else np.nan, "p": (np.sum(np.abs(perm) >= abs(obs)) + 1) / (n + 1),
            "n_si": int(gv[used].sum()), "n_no": int((~gv[used]).sum())}


def compare(d: pd.DataFrame, cols: dict[str, str], g: str, strata=STRATA, **kw) -> pd.DataFrame:
    """`strat_perm` para varias métricas: una fila por métrica con las medias crudas de cada grupo."""
    rows = []
    for c, label in cols.items():
        r = strat_perm(d, c, g, strata, **kw)
        rows.append({"metrica": label, "si": d.loc[d[g].astype(bool), c].mean(), "no": d.loc[~d[g].astype(bool), c].mean(), **r})
    return pd.DataFrame(rows)


def veredicto(r: pd.Series | dict, alpha: float = ALPHA, min_group: int = MIN_GROUP, min_sd: float = 0.2) -> str:
    """Reglas fijas: "no alcanza" si un grupo tiene menos de `min_group` partidos; "se sostiene" si p < alpha y el
    efecto es de al menos `min_sd` desviaciones estándar; si no, "no cambia"."""
    if min(r["n_si"], r["n_no"]) < min_group or pd.isna(r["p"]):
        return "no alcanza"
    return "se sostiene" if r["p"] < alpha and abs(r["dif_sd"]) >= min_sd else "no cambia"


# ------------------------------------------------------------------ muestra y plan con el partido empatado
def ventana(p: pd.DataFrame) -> pd.DataFrame:
    """Partidos de la ventana oficial (Ap 2021 – Cl 2025) de Solari, Ortiz y Jardine."""
    return p[(p.muestra == "ventana") & p.coach.isin(COACHES)].copy()


def plan_empate(tramos: pd.DataFrame, cols=("possession_time_pct", "field_tilt", "ppda", "high_press_pct",
                                             "long_pass_pct", "def_action_x_mean")) -> pd.DataFrame:
    """Plan de juego de cada partido medido SOLO con el marcador empatado (media ponderada por minutos).
    Partidos con menos de MIN_DRAW_MIN minutos empatados quedan fuera (NaN)."""
    e = tramos[tramos.game_state == "Empate"]
    out = {}
    for c in cols:
        ok = e[e[c].notna()]
        out[f"{c}_empate"] = ok.groupby("match_id").apply(lambda d: np.average(d[c], weights=d.duration_min))
    out = pd.DataFrame(out)
    mins = e.groupby("match_id").duration_min.sum()
    out["min_empate"] = mins
    return out[out.min_empate >= MIN_DRAW_MIN]


# ------------------------------------------------------------------ E1 · ADN común de los técnicos
def adn_comun(p: pd.DataFrame, ref: pd.DataFrame, ejes) -> pd.DataFrame:
    """Cada rasgo del ADN de 0 a 100 frente a la liga, por técnico y por torneo (ventana). Es "del club" si los tres
    técnicos y todos los torneos quedan del mismo lado de 50."""
    w = ventana(p)
    by_coach = pd.DataFrame({c: K.adn_percentil(w[w.coach == c], ref, ejes) for c in COACHES})
    by_torneo = pd.DataFrame({t: K.adn_percentil(g, ref, ejes) for t, g in w.groupby("torneo")})
    out = by_coach.copy()
    out["torneo_min"], out["torneo_max"] = by_torneo.min(axis=1), by_torneo.max(axis=1)
    above, below = (by_torneo > 50).all(axis=1) & (by_coach > 50).all(axis=1), (by_torneo < 50).all(axis=1) & (by_coach < 50).all(axis=1)
    out["del_club"] = np.select([above, below], ["siempre arriba de la liga", "siempre abajo de la liga"], "depende del técnico")
    return out


# ------------------------------------------------------------------ E2 / E3 · liguilla serie por serie
def series_liguilla(p: pd.DataFrame, bp: pd.DataFrame) -> pd.DataFrame:
    """Una fila por serie de liguilla (todas las temporadas): rival, quién cerró en casa, marcador global, si avanzó,
    ocasiones (xG) a favor y en contra, posesión, presión (PPDA mediano) y balón parado. `merecia` = el América tuvo
    mejores ocasiones en la serie."""
    lg = p[(p.fase == "Liguilla") & (p.llego != "En curso")].sort_values("match_date").copy()
    lg["serie"] = lg.torneo + " · " + lg.ronda
    lg["pierna"] = lg.groupby("serie").cumcount().map({0: "ida", 1: "vuelta"})
    b = bp.groupby(["match_id", "lado"]).xg.sum().unstack(fill_value=0)
    lg = lg.join(b, on="match_id")
    rows = []
    for s, g in lg.groupby("serie", sort=False):
        r0 = g.iloc[0]
        stage = SERIES_STAGE.get(r0.ronda, r0.ronda)
        avanzo = K.STAGES.index(r0.llego) > K.STAGES.index(stage) if stage in K.STAGES else np.nan
        rows.append({"serie": s, "torneo": r0.torneo, "tecnico": r0.coach, "ronda": r0.ronda, "rival": r0.opponent,
                     "nivel_rival": r0.rival_nivel, "partidos": len(g), "vuelta_en_casa": g.localia.iloc[-1] == "Local",
                     "ida": f"{int(r0.goals_for)}-{int(r0.goals_against)}", "global": f"{int(g.goals_for.sum())}-{int(g.goals_against.sum())}",
                     "avanzo": avanzo, "xg_favor": g.xg_favor.sum(), "xg_contra": g.xg_contra.sum(),
                     "posesion": g.possession_time_pct.mean(), "ppda": g.ppda.median(), "field_tilt": g.field_tilt.mean(),
                     "bp_xg_favor": g.get("A favor", pd.Series(0)).sum(), "bp_xg_contra": g.get("En contra", pd.Series(0)).sum(),
                     "puntos_esperados": g.xpts.mean(), "llego": r0.llego})
    s = pd.DataFrame(rows)
    s["merecia"] = s.xg_favor > s.xg_contra
    return s


def ida_vuelta(p: pd.DataFrame) -> pd.DataFrame:
    """Partidos de series de ida y vuelta: puntos, goles y ocasiones por pierna y localía."""
    lg = p[(p.fase == "Liguilla")].sort_values("match_date").copy()
    lg["serie"] = lg.torneo + " · " + lg.ronda
    lg = lg[lg.groupby("serie").match_id.transform("size") == 2]
    lg["pierna"] = lg.groupby("serie").cumcount().map({0: "ida", 1: "vuelta"})
    return lg.groupby(["pierna", "localia"]).agg(partidos=("match_id", "size"), puntos=("puntos", "mean"),
                                                 goles_favor=("goals_for", "mean"), goles_contra=("goals_against", "mean"),
                                                 xg_favor=("xg_favor", "mean"), xg_contra=("xg_contra", "mean"),
                                                 posesion=("possession_time_pct", "mean")).reset_index()


# ------------------------------------------------------------------ E4 / E5 / E14 · localía y plan
STYLE = {"puntos": "Puntos por partido", "xg_favor": "Ocasiones a favor (xG)", "xg_contra": "Ocasiones en contra (xG)",
         "possession_time_pct": "Posesión (%)", "field_tilt": "Dominio territorial (%)", "ppda": "Pases que deja dar (PPDA)",
         "high_press_pct": "Acciones defensivas en campo rival (%)", "box_touches_per100poss": "Toques en el área rival (por 100 posesiones)"}


def localia(p: pd.DataFrame) -> pd.DataFrame:
    """Local frente a visita, dentro del mismo técnico y nivel de rival: ¿cambia el resultado?, ¿cambia el estilo?"""
    w = ventana(p).assign(local=lambda d: d.localia.eq("Local"))
    return compare(w, STYLE, "local").assign(veredicto=lambda d: d.apply(veredicto, axis=1))


def plan_y_puntos(p: pd.DataFrame, tramos: pd.DataFrame, plan: str, mas: str = "alto", only=None) -> pd.DataFrame:
    """¿Sacó más puntos cuando su plan (medido con el partido empatado) fue `mas` que la mediana de su técnico y nivel
    de rival? `only` filtra (p. ej. {"localia": "Visita", "fase": "Fase regular"})."""
    w = ventana(p).join(plan_empate(tramos), on="match_id")
    for k, v in (only or {}).items():
        w = w[w[k] == v]
    col = f"{plan}_empate"
    w = w.dropna(subset=[col])
    med = w.groupby(STRATA)[col].transform("median")
    w["grupo"] = w[col] > med if mas == "alto" else w[col] < med
    out = compare(w, {"puntos": "Puntos por partido", "xg_favor": "Ocasiones a favor (xG)", "xg_contra": "Ocasiones en contra (xG)",
                      col: f"{plan} con el partido empatado"}, "grupo")
    return out.assign(plan=plan, mas=mas, veredicto=lambda d: d.apply(veredicto, axis=1))


# ------------------------------------------------------------------ E6 / E7 · sistemas y medios
def lineas(sistema: str) -> tuple[int, int, int]:
    """'4-2-3-1' → (defensas 4, medios 5, delanteros 1). Medios = todo lo que hay entre defensa y delanteros."""
    n = [int(x) for x in str(sistema).split("-") if x.isdigit()]
    return (n[0], sum(n[1:-1]), n[-1]) if len(n) >= 3 else (np.nan, np.nan, np.nan)


SYSTEM_COLS = {"puntos": "Puntos por partido", "xg_favor": "Ocasiones a favor (xG)", "xg_contra": "Ocasiones en contra (xG)",
               "box_touches_per100poss": "Toques en el área rival (por 100 posesiones)",
               "opp_f3_entry_pct": "Jugadas rivales que llegan a su último tercio (%)",
               "possession_time_pct": "Posesión (%)", "ppda": "Pases que deja dar (PPDA)"}


def sistemas(p: pd.DataFrame, min_partidos: int = 9) -> pd.DataFrame:
    """Por sistema titular: medias crudas por partido, cuántos partidos y con qué técnicos y rivales."""
    w = ventana(p)
    keep = w.sistema.value_counts()[lambda s: s >= min_partidos].index
    w = w[w.sistema.isin(keep)]
    g = w.groupby("sistema")
    out = g[list(SYSTEM_COLS)].mean().rename(columns=SYSTEM_COLS)
    out.insert(0, "partidos", g.size())
    out["% contra rivales fuertes"] = g.rival_nivel.apply(lambda s: (s == "Fuerte").mean() * 100)
    out["técnicos"] = g.coach.agg(lambda s: ", ".join(f"{k} {v}" for k, v in s.value_counts().items()))
    return out.sort_values("partidos", ascending=False)


def sistema_vs(p: pd.DataFrame, a: str, b: str = "4-2-3-1") -> pd.DataFrame:
    """Sistema `a` frente a `b`, dentro del mismo técnico y nivel de rival."""
    w = ventana(p)
    w = w[w.sistema.isin([a, b])].assign(es_a=lambda d: d.sistema.eq(a))
    return compare(w, SYSTEM_COLS, "es_a").assign(sistema=a, frente_a=b, veredicto=lambda d: d.apply(veredicto, axis=1))


def medios(p: pd.DataFrame) -> pd.DataFrame:
    """E7: con menos medios (≤ 4) frente a más (≥ 5), dentro del mismo técnico y nivel de rival."""
    w = ventana(p)
    w[["defensas", "medios", "delanteros"]] = w.sistema.apply(lambda s: pd.Series(lineas(s)))
    w = w.dropna(subset=["medios"]).assign(menos_medios=lambda d: d.medios <= 4)
    return compare(w, SYSTEM_COLS, "menos_medios").assign(veredicto=lambda d: d.apply(veredicto, axis=1))


# ------------------------------------------------------------------ E8 · momento del partido
def peligro_por_minuto(seg: pd.DataFrame, ids, n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    """Ocasiones (xG) a favor y en contra por cada 90' en cada tramo de 15' (fct_segment), con intervalo del 90 %
    por remuestreo de partidos. 90+ va aparte: es corto y caótico."""
    s = seg[seg.match_id.isin(list(ids))].copy()
    s["xg_f"] = s.np_xg_per100poss.fillna(0) * s.n_poss_team / 100
    s["xg_c"] = s.opp_np_xg_per100poss.fillna(0) * s.n_poss_opp / 100
    m = s.groupby(["match_id", "minute_bin"])[["xg_f", "xg_c", "duration_min"]].sum().reset_index()
    rng = np.random.default_rng(seed)
    matches = m.match_id.unique()
    rows = []
    for b, g in m.groupby("minute_bin"):
        gi = g.set_index("match_id")
        bs = []
        for _ in range(n_boot):
            pick = gi.reindex(rng.choice(matches, len(matches))).dropna()
            bs.append(pick.xg_c.sum() / pick.duration_min.sum() * 90)
        rows.append({"tramo": b, "minutos": g.duration_min.sum(), "xg_favor_90": g.xg_f.sum() / g.duration_min.sum() * 90,
                     "xg_contra_90": g.xg_c.sum() / g.duration_min.sum() * 90,
                     "xg_contra_90_lo": np.percentile(bs, 5), "xg_contra_90_hi": np.percentile(bs, 95)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ E9 · cuando pierde
LOSS_COLS = {"xg_favor": "Ocasiones a favor (xG)", "xg_contra": "Ocasiones en contra (xG)",
             "np_xg_per_shot": "Calidad de cada tiro (xG por tiro)", "shots_per100poss": "Tiros (por 100 posesiones)",
             "box_touches_per100poss": "Toques en el área rival (por 100 posesiones)",
             "opp_shots_per100poss": "Tiros que concede (por 100 posesiones rivales)",
             "opp_transition_xg_per100poss": "Peligro que concede al contragolpe",
             "opp_sp_xg": "Peligro que concede a balón parado (xG)", "sp_xg": "Peligro a balón parado a favor (xG)",
             "possession_time_pct_empate": "Posesión con el partido empatado (%)",
             "field_tilt_empate": "Dominio territorial con el partido empatado (%)",
             "ppda_empate": "Pases que deja dar con el partido empatado (PPDA)",
             "long_pass_pct_empate": "Pases largos con el partido empatado (%)"}


def derrotas(p: pd.DataFrame, tramos: pd.DataFrame) -> pd.DataFrame:
    """E9: derrotas frente a victorias, dentro del mismo técnico y nivel de rival. Lo del marcador (posesión, presión)
    se mide con el partido empatado para no confundir causa y consecuencia."""
    w = ventana(p).join(plan_empate(tramos), on="match_id")
    w = w[w.result.isin(["W", "L"])].assign(perdio=lambda d: d.result.eq("L"))
    out = compare(w, LOSS_COLS, "perdio")
    return out.assign(veredicto=lambda d: d.apply(veredicto, axis=1)).sort_values("dif_sd", key=np.abs, ascending=False)


def peores_partidos(p: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Las derrotas con peor diferencia de ocasiones (xG) de la ventana."""
    w = ventana(p)
    w = w[w.result == "L"].assign(dif_xg=lambda d: d.xg_favor - d.xg_contra)
    return w.nsmallest(n, "dif_xg")[["match_date", "torneo", "coach", "localia", "opponent", "rival_nivel", "goals_for",
                                     "goals_against", "xg_favor", "xg_contra", "possession_time_pct", "sistema", "fase"]]


# ------------------------------------------------------------------ E10 · bandas
def bandas(p: pd.DataFrame) -> pd.DataFrame:
    """E10: por qué carril avanza (pases progresivos, el carril de destino) en victorias frente a derrotas.
    Por dónde le hacen daño NO se mide con el lugar del tiro (casi todos se tiran por el centro): haría falta el
    carril por el que entra el rival, que no está en el cubo."""
    w = ventana(p)
    w = w[w.result.isin(["W", "L"])].assign(perdio=lambda d: d.result.eq("L"))
    cols = {"prog_lane_left_pct": "Avanza por la izquierda (%)", "prog_lane_center_pct": "Avanza por el centro (%)",
            "prog_lane_right_pct": "Avanza por la derecha (%)"}
    return compare(w, cols, "perdio").assign(veredicto=lambda d: d.apply(veredicto, axis=1))


# ------------------------------------------------------------------ E12 · pierna hábil
FOOT_MIN_PASSES = 100     # pases con el pie mínimos para clasificar a un jugador
FOOT_SHARE = 0.70         # ≥ 70 % de sus pases con un pie → zurdo o diestro; si no, "ambidiestro"
WIDE = {"Left Wing": ("Extremo", "izq"), "Right Wing": ("Extremo", "der"), "Left Midfield": ("Extremo", "izq"),
        "Right Midfield": ("Extremo", "der"), "Left Back": ("Lateral", "izq"), "Right Back": ("Lateral", "der"),
        "Left Wing Back": ("Lateral", "izq"), "Right Wing Back": ("Lateral", "der")}


def pierna_habil(ev: pd.DataFrame) -> pd.DataFrame:
    """Pierna hábil de cada jugador del América: % de sus pases (con el pie) hechos con la izquierda."""
    d = ev[ev.am & (ev.type == "Pass") & ev.pass_body_part.isin(["Left Foot", "Right Foot"])]
    g = d.groupby(["player_id", "player"]).pass_body_part.agg(pases="size", izq=lambda s: (s == "Left Foot").mean())
    g = g[g.pases >= FOOT_MIN_PASSES].reset_index()
    g["pierna"] = np.select([g.izq >= FOOT_SHARE, g.izq <= 1 - FOOT_SHARE], ["Zurdo", "Diestro"], "Ambidiestro")
    return g


def perfil_bandas(lu: pd.DataFrame, foot: pd.DataFrame) -> pd.DataFrame:
    """Por partido: cuántos extremos y laterales titulares juegan a pierna cambiada ("invertido": un diestro por
    la izquierda o un zurdo por la derecha), a partir de la alineación titular y la pierna hábil."""
    f = foot.set_index("player_id").pierna
    w = lu[lu.position.isin(WIDE)].copy()
    w["puesto"], w["lado"] = zip(*w.position.map(WIDE))
    w["pierna"] = w.player_id.map(f)
    w = w[w.pierna.isin(["Zurdo", "Diestro"])]
    w["invertido"] = ((w.lado == "izq") & (w.pierna == "Diestro")) | ((w.lado == "der") & (w.pierna == "Zurdo"))
    out = w.groupby(["match_id", "puesto"]).invertido.agg(["sum", "size"]).unstack()
    out.columns = [f"{a}_{b}" for a, b in out.columns]
    return out.rename(columns={"sum_Extremo": "extremos_invertidos", "size_Extremo": "extremos",
                               "sum_Lateral": "laterales_invertidos", "size_Lateral": "laterales"})


def bandas_pierna(p: pd.DataFrame, perfil: pd.DataFrame) -> pd.DataFrame:
    """E12: partidos con los dos extremos a pierna cambiada frente al resto (con dos extremos titulares
    clasificados), dentro del mismo técnico y nivel de rival."""
    w = ventana(p).join(perfil, on="match_id")
    w = w[w.extremos == 2].assign(invertidos=lambda d: d.extremos_invertidos == 2)
    cols = {"puntos": "Puntos por partido", "xg_favor": "Ocasiones a favor (xG)", "np_xg_per_shot": "Calidad de cada tiro (xG por tiro)",
            "box_touches_per100poss": "Toques en el área rival (por 100 posesiones)", "cross_xg_share": "Peligro que nace de centros (%)",
            "prog_lane_center_pct": "Avanza por el centro (%)"}
    return compare(w, cols, "invertidos").assign(veredicto=lambda d: d.apply(veredicto, axis=1))


# ------------------------------------------------------------------ E11 · ¿mejor plantilla?
def plantilla(jug: pd.DataFrame, p: pd.DataFrame) -> pd.DataFrame:
    """E11: aporte (OBV) por 90' de cada línea en cada técnico × torneo, ponderado por minutos, y del once más usado
    (los 11 con más minutos), junto a hasta dónde llegó. Todas las temporadas con liguilla terminada."""
    j = jug[jug.minutos > 0].copy()
    j["linea2"] = j.linea.replace({"Banda": "Ataque", "Delantero": "Ataque", "Medio ofensivo": "Medio", "Medio defensivo": "Medio",
                                   "Carrilero": "Defensa"})
    llego = p.drop_duplicates(["coach", "torneo"]).set_index(["coach", "torneo"]).llego
    rows = []
    for (c, t), g in j.groupby(["coach", "torneo"]):
        r = {"tecnico": c, "torneo": t, "llego": llego.get((c, t))}
        for ln, gl in g.groupby("linea2"):
            r[f"aporte90_{ln}"] = gl.obv_pos.sum() / gl.minutos.sum() * 90
        top = g.nlargest(11, "minutos")
        r["aporte90_once"] = top.obv_pos.sum() / top.minutos.sum() * 90
        r["minutos_del_once_pct"] = top.minutos.sum() / g.minutos.sum() * 100
        rows.append(r)
    out = pd.DataFrame(rows)
    out = out[out.llego.isin(K.STAGES) & out.tecnico.isin(COACHES)]
    out["avance"] = out.llego.map(K.STAGES.index)
    return out


def spearman(df: pd.DataFrame, x: str, y: str = "avance") -> float:
    d = df[[x, y]].dropna()
    return d[x].rank().corr(d[y].rank()) if len(d) > 2 else np.nan


# ------------------------------------------------------------------ E13 · tiempo efectivo
def tiempo_efectivo(poss: pd.DataFrame) -> pd.Series:
    """Minutos con balón en juego por partido: suma de la duración de todas las posesiones (de los dos equipos),
    sin tiempos extra ni penales."""
    return poss[poss.period <= 4].groupby("match_id").duration_s.sum() / 60


# ------------------------------------------------------------------ E15 · cambios
def efecto_cambios(subs: pd.DataFrame, p: pd.DataFrame, min_dur: float = 5, n_boot: int = 2000, seed: int = 0) -> pd.DataFrame:
    """E15: cómo cambian las ocasiones (xG por 100 posesiones) a favor y en contra después de cada ventana de cambios,
    según quién sale (un atacante o un defensor) y el marcador. Descriptivo: no aísla el cambio de lo que ya venía
    pasando (los equipos cambian cuando algo va mal, y eso tiende a volver a la normalidad solo)."""
    w = ventana(p)
    s = subs[subs.match_id.isin(w.match_id) & (subs.dur_antes_min >= min_dur) & (subs.dur_despues_min >= min_dur)].copy()
    s["sale"] = np.select([s.n_off_att > s.n_off_def, s.n_off_def > s.n_off_att], ["Sale un atacante", "Sale un defensor"], "Mixto o mismo puesto")
    s["marcador"] = np.select([s.score_diff < 0, s.score_diff > 0], ["Perdiendo", "Ganando"], "Empatando")
    rng = np.random.default_rng(seed)
    rows = []
    for (m, sale), g in s.groupby(["marcador", "sale"]):
        r = {"marcador": m, "sale": sale, "ventanas": len(g)}
        for c, lab in [("d_np_xg_per100poss", "cambio_xg_favor"), ("d_opp_np_xg_per100poss", "cambio_xg_contra"),
                       ("d_field_tilt", "cambio_dominio")]:
            v = g[c].dropna().to_numpy()
            bs = [rng.choice(v, len(v)).mean() for _ in range(n_boot)] if len(v) else [np.nan]
            r[lab], r[f"{lab}_lo"], r[f"{lab}_hi"] = v.mean() if len(v) else np.nan, np.percentile(bs, 5), np.percentile(bs, 95)
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ E6 ampliada · TODAS las formaciones, por minutos
# La formación titular no basta: el técnico cambia de dibujo durante el partido (Tactical Shift). Aquí cada evento y
# cada posesión llevan la formación que había EN EL CAMPO en ese momento (la propia y la del rival), y los indicadores
# del marco se calculan con features.aggregate, igual que para un partido o un tramo de 15'.
COUNTS = {"xg_f": "Ocasiones a favor (xG por 90')", "xg_c": "Ocasiones en contra (xG por 90')",
          "tiros_f": "Tiros a favor por 90'", "tiros_c": "Tiros en contra por 90'",
          "claras_f": "Ocasiones claras a favor por 90'", "claras_c": "Ocasiones claras en contra por 90'"}
RATES = {"possession_time_pct": "Posesión (%)", "field_tilt": "Dominio territorial (%)", "ppda": "Pases que deja dar (PPDA)",
         "high_press_pct": "Acciones defensivas en campo rival (%)",
         "box_touches_per100poss": "Toques en el área rival (por 100 posesiones)",
         "opp_f3_entry_pct": "Jugadas rivales que llegan a su último tercio (%)"}


def formacion_str(f) -> str | None:
    """4231 → '4-2-3-1' (StatsBomb guarda la formación como número)."""
    return "-".join(str(int(f))) if pd.notna(f) else None


def formacion_timeline(ev: pd.DataFrame) -> pd.DataFrame:
    """(match_id, t, propio, formacion): la titular (Starting XI, t = -1) y cada cambio de dibujo (Tactical Shift)
    de cada equipo."""
    import json
    d = ev[ev.type.isin(["Starting XI", "Tactical Shift"])].copy()
    tac = d.tactics.map(lambda x: json.loads(x) if isinstance(x, str) else x)
    d["formacion"] = tac.map(lambda x: formacion_str(x.get("formation")) if isinstance(x, dict) else None)
    d.loc[d.type == "Starting XI", "t"] = -1
    return d.rename(columns={"am": "propio"})[["match_id", "t", "propio", "formacion"]].dropna().sort_values("t")


def _asof(df: pd.DataFrame, tl: pd.DataFrame, tcol: str, propio: bool) -> pd.Series:
    """Formación vigente (la última anterior o igual a `tcol`) de un equipo para cada fila de `df`."""
    t = tl[tl.propio == propio][["match_id", "t", "formacion"]].rename(columns={"t": "_t"})
    left = df[["match_id", tcol]].reset_index().rename(columns={tcol: "_t"})
    left["_t"], t["_t"] = left["_t"].astype(float), t["_t"].astype(float)
    m = pd.merge_asof(left.sort_values("_t"), t.sort_values("_t"), on="_t", by="match_id", direction="backward")
    return m.set_index("index")["formacion"].reindex(df.index)


def tramos_formacion(ev: pd.DataFrame, poss: pd.DataFrame, extra_keys=("game_state3",)) -> pd.DataFrame:
    """Una fila por partido × formación propia × formación rival × `extra_keys`: minutos de reloj, conteos
    (xG, tiros y ocasiones claras a favor y en contra) y los indicadores del marco (features.aggregate)."""
    from src import features as F
    from src import framework as fw
    tl = formacion_timeline(ev)
    ev = ev.copy()
    ev["formacion"], ev["formacion_rival"] = _asof(ev, tl, "t", True), _asof(ev, tl, "t", False)
    poss = poss.copy()
    poss["game_state3"] = np.sign(poss.score_diff).map({1: "Ganando", 0: "Empatando", -1: "Perdiendo"})
    poss["formacion"], poss["formacion_rival"] = _asof(poss, tl, "t_start", True), _asof(poss, tl, "t_start", False)
    keys = ["match_id", "formacion", "formacion_rival", *extra_keys]
    ev, poss = ev.dropna(subset=keys), poss.dropna(subset=keys)
    agg = F.aggregate(ev, poss, keys)
    # minutos de reloj: lo que pasa entre un evento y el siguiente, dentro del mismo periodo
    e = ev.sort_values(["match_id", "period", "t"])
    dt = e.groupby(["match_id", "period"]).t.shift(-1).sub(e.t).clip(lower=0, upper=120).fillna(0)
    out = pd.DataFrame({"minutos": (dt / 60).groupby([e[k] for k in keys]).sum()})
    big = fw.A["big_chance_xg"]
    for side, mask in [("f", ev.am), ("c", ~ev.am)]:
        s = ev[mask & ev.np_shot]
        out[f"xg_{side}"] = s.groupby(keys).np_xg.sum()
        out[f"tiros_{side}"] = s.groupby(keys).size()
        out[f"claras_{side}"] = s[s.np_xg >= big].groupby(keys).size()
    out[list(COUNTS)] = out[list(COUNTS)].fillna(0)
    out = out.join(agg[list(RATES)])
    return out[out.minutos > 0].reset_index()


def _tasas(d: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Conteos por 90' y tasas ponderadas por minutos, por grupo `by`."""
    g = d.groupby(by)
    out = pd.DataFrame({"minutos": g.minutos.sum()})
    for c in COUNTS:
        out[c] = g[c].sum() / out.minutos * 90
    for c in RATES:
        ok = d[d[c].notna()]
        out[c] = (ok[c] * ok.minutos).groupby([ok[b] for b in by]).sum() / ok.groupby(by).minutos.sum()
    return out


def formaciones(tr: pd.DataFrame, min_minutos: float = 300, col: str = "formacion") -> pd.DataFrame:
    """Todas las formaciones con al menos `min_minutos`: tasas, partidos, quién la usó, con qué marcador y contra
    qué rivales (la formación de remontar no se compara con la de cerrar un partido sin decirlo)."""
    t = _tasas(tr, [col])
    t = t[t.minutos >= min_minutos]
    d = tr[tr[col].isin(t.index)]
    g = d.groupby(col)
    t["partidos"] = g.match_id.nunique()
    t["técnicos"] = g.apply(lambda x: ", ".join(f"{k} {v:.0f}'" for k, v in
                                                x.groupby("coach").minutos.sum().sort_values(ascending=False).items()))
    st = d.pivot_table(index=col, columns="game_state3", values="minutos", aggfunc="sum", fill_value=0)
    for c in st:
        t[f"% minutos {c.lower()}"] = st[c] / st.sum(axis=1) * 100
    t["% minutos contra rivales fuertes"] = d[d.rival_nivel == "Fuerte"].groupby(col).minutos.sum() / t.minutos * 100
    return t.sort_values("minutos", ascending=False)


def comparar_formacion(tr: pd.DataFrame, a, b="4-2-3-1", strata=("coach", "rival_nivel", "game_state3"),
                       col: str = "formacion", min_min: float | None = None, n_boot: int = 500, seed: int = 0) -> pd.DataFrame:
    """`a` frente a `b` con el MISMO técnico, el mismo nivel de rival y el mismo marcador: en cada estrato donde las
    dos tienen al menos `min_min` minutos se resta la tasa de `b` a la de `a`, y se promedia con el peso de los
    minutos de `a`. Intervalo del 90 % remuestreando partidos. `a` y `b` pueden ser listas (familias de formaciones).
    Veredicto: "no alcanza" con menos de 450 minutos comparables (5 partidos); "se sostiene" si el intervalo no
    cruza el cero; si no, "no cambia"."""
    from src import framework as fw
    min_min = fw.A["formation_min_minutes"] if min_min is None else min_min
    a, b = ([a] if isinstance(a, str) else list(a)), ([b] if isinstance(b, str) else list(b))
    d = tr[tr[col].isin(a + b)].assign(grupo=lambda x: np.where(x[col].isin(a), "a", "b"))
    strata, metrics = list(strata), list(COUNTS) + list(RATES)

    def diff(dd: pd.DataFrame) -> pd.Series:
        t = _tasas(dd, strata + ["grupo"]).unstack("grupo")
        if "a" not in t["minutos"] or "b" not in t["minutos"]:
            return pd.Series(np.nan, index=metrics + ["minutos_a"])
        t = t[(t["minutos"]["a"] >= min_min) & (t["minutos"]["b"] >= min_min)]
        if t.empty:
            return pd.Series(np.nan, index=metrics + ["minutos_a"])
        w = t["minutos"]["a"]
        r = {}
        for m in metrics:
            dm = (t[m]["a"] - t[m]["b"])
            ok = dm.notna()
            r[m] = np.average(dm[ok], weights=w[ok]) if ok.any() else np.nan
        r["minutos_a"] = w.sum()
        return pd.Series(r)

    obs = diff(d)
    rng = np.random.default_rng(seed)
    by_match = dict(tuple(d.groupby("match_id")))
    ids = list(by_match)
    bs = pd.DataFrame([diff(pd.concat([by_match[m] for m in rng.choice(ids, len(ids))], ignore_index=True))
                       for _ in range(n_boot)])
    labels = {**COUNTS, **RATES}
    rows = []
    for m in metrics:
        lo, hi = (np.nanpercentile(bs[m], 5), np.nanpercentile(bs[m], 95)) if bs[m].notna().any() else (np.nan, np.nan)
        mins = obs.get("minutos_a", np.nan)
        ver = ("no alcanza" if not mins >= 450 or pd.isna(lo) else ("se sostiene" if (lo > 0 or hi < 0) else "no cambia"))
        rows.append({"formacion": "/".join(a), "frente_a": "/".join(b), "metrica": labels[m], "dif": obs[m], "lo": lo,
                     "hi": hi, "minutos_comparables": mins, "veredicto": ver})
    return pd.DataFrame(rows)


def familias(tr: pd.DataFrame, col: str = "formacion") -> pd.DataFrame:
    """Rasgos del dibujo de cada fila: línea de 3 o de 4 atrás, número de delanteros y de medios."""
    l = tr[col].map(lineas)
    return tr.assign(atras=l.map(lambda x: f"Línea de {x[0]}"), delanteros=l.map(lambda x: x[2]),
                     medios=l.map(lambda x: x[1]))

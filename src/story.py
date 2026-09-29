"""LA HISTORIA DE JARDINE (todo.md §3.2 con balón, §3.3 sin balón, §3.4 forma con 360) — cálculos reutilizables.

El notebook 05 y el reporte HTML final consumen estas funciones. Reglas:
- Todas las definiciones (zonas, carriles, pase progresivo, posesión, transición, recuperación, PPDA,
  contrapresión) vienen de src/framework.py y src/features.py; aquí solo se combinan.
- Toda cifra titular sale de la ventana oficial (Ap 2021 – Cl 2025, `split == "train"`); `match_scope`
  la aplica por defecto. Protagonista: Jardine; comparación: Solari y Ortiz (Cervantes, 2 partidos, fuera).
- A disco solo van AGREGADOS (`save_story` → data/gold/analysis/story_*.parquet); nunca eventos.
- Cancha StatsBomb 120 × 80, el América ataca hacia la derecha; y = 0 es su banda izquierda.
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from src import features as F
from src import framework as fw
from src.coach_profile import MIN_MATCHES, SPLIT_LABEL, short
from src.modeling import temporal_split
from src.pipeline.config import GOLD

A = fw.A
COACHES = ["Solari", "Ortiz", "Jardine"]  # orden cronológico: el "antes" y el protagonista
PROTAGONIST = "Jardine"
ANALYSIS = GOLD / "analysis"

ORIGINS = ["Juego posicional", "Transición", "Balón parado"]
ASSISTS = ["Centro", "Pase atrás al área", "Filtrado", "Otro pase", "Servicio a balón parado",
           "Tiro libre directo", "Jugada individual", "Rebote o balón suelto"]
INDIVIDUAL_CARRY_MIN = 5  # yd: conducción previa del propio tirador para contar como "jugada individual"
X_BINS = [0, 20, 40, 60, 80, 100, 120]   # rejilla de 6 franjas de 20 yd (alturas de la cancha)
Y_BINS = [0, 80 / 3, 160 / 3, 80]        # los tres carriles del marco (izquierdo, central, derecho)


# ------------------------------------------------------------------ muestra y carga
def match_scope(dim: pd.DataFrame, window_only: bool = True, coaches=COACHES) -> pd.DataFrame:
    """Partidos del análisis con técnico (apellido) y muestra. Por defecto: solo la ventana oficial."""
    d = dim.assign(split=dim.match_id.map(temporal_split(dim)), coach=dim.team_manager.map(short))
    d["muestra"] = d.split.map(SPLIT_LABEL)
    if window_only:
        d = d[d.split == "train"]
    return d[d.coach.isin(coaches)].reset_index(drop=True)


def n_matches(scope: pd.DataFrame) -> pd.Series:
    return scope.groupby("coach").size().reindex(COACHES).rename("partidos")


def load_story_events(scope: pd.DataFrame) -> pd.DataFrame:
    """Eventos de los partidos de `scope` con marcador, banderas del marco (features.event_flags) y técnico.
    Solo en memoria: nunca se guardan."""
    from src.pipeline.silver import load_events
    ev = load_events()
    ev = ev[ev.match_id.isin(scope.match_id)]
    ev = F.event_flags(fw.add_game_state(ev))
    ev = ev[ev.period < 5]
    return ev.assign(coach=ev.match_id.map(scope.set_index("match_id").coach))


def load_story_frames(scope: pd.DataFrame) -> pd.DataFrame:
    """360 (freeze frames) de los partidos de `scope`. Solo en memoria: nunca se guardan."""
    from src.pipeline.silver import load_frames
    return load_frames(scope.match_id)


def load_possessions(scope: pd.DataFrame) -> pd.DataFrame:
    """fct_possession (Gold, ya construida con framework.possessions) de los partidos de `scope`."""
    p = pd.read_parquet(GOLD / "fct_possession.parquet")
    p = p[p.match_id.isin(scope.match_id) & (p.period < 5)]
    return p.assign(coach=p.match_id.map(scope.set_index("match_id").coach))


def player_short_names() -> pd.Series:
    """player_id -> nombre corto (apodo de StatsBomb o nombre completo), el mismo que usan las fichas."""
    pm = pd.read_parquet(GOLD / "fct_player_match.parquet", columns=["player_id", "player_short"])
    return pm.drop_duplicates("player_id").set_index("player_id").player_short


def grid_per_match(grid: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Agrega a una rejilla (con columna coach) el conteo por partido del técnico."""
    return grid.assign(por_partido=grid.n / grid.coach.map(n_matches(scope)).values)


def per_match(counts: pd.DataFrame | pd.Series, scope: pd.DataFrame, by: str = "coach"):
    """Divide conteos indexados por técnico entre los partidos de cada técnico."""
    return counts.div(n_matches(scope).reindex(counts.index.get_level_values(by)).values, axis=0)


# ------------------------------------------------------------------ utilidades
def zone_grid(df: pd.DataFrame, x: str, y: str, by: list[str], values: tuple[str, ...] = (),
              x_bins=X_BINS, y_bins=Y_BINS) -> pd.DataFrame:
    """Agrega puntos en una rejilla de la cancha: una fila por grupo × celda con conteo (y suma de `values`).
    Es la forma de guardar mapas sin guardar eventos."""
    d = df.assign(_xb=pd.cut(df[x].clip(0, 119.99), x_bins, right=False),
                  _yb=pd.cut(df[y].clip(0, 79.99), y_bins, right=False))
    g = d.groupby(by + ["_xb", "_yb"], observed=False)
    out = g.size().rename("n").to_frame()
    for v in values:
        out[v] = g[v].sum()
    out = out.reset_index()
    out["x0"] = out._xb.map(lambda i: i.left).astype(float)
    out["x1"] = out._xb.map(lambda i: i.right).astype(float)
    out["y0"] = out._yb.map(lambda i: i.left).astype(float)
    out["y1"] = out._yb.map(lambda i: i.right).astype(float)
    out["share"] = out.n / out.groupby(by).n.transform("sum").replace(0, np.nan)
    return out.drop(columns=["_xb", "_yb"])


def player_positions(ev: pd.DataFrame) -> pd.Series:
    """(match_id, player_id) -> posición más frecuente del jugador en ese partido (según sus eventos)."""
    d = ev[ev.player_id.notna() & ev.position.notna()]
    return d.groupby(["match_id", "player_id"]).position.agg(lambda s: s.mode().iat[0])


def _share(df: pd.DataFrame, by: list[str], col: str) -> pd.DataFrame:
    t = df.groupby(by + [col], observed=True).size().rename("n").reset_index()
    t["share"] = t.n / t.groupby(by).n.transform("sum")
    return t


# ------------------------------------------------------------------ §3.2a salida desde atrás
def restarts(ev: pd.DataFrame) -> pd.DataFrame:
    """Saques de meta y pases del portero en juego (en memoria). Corto/largo con el umbral del marco;
    destino = zona donde cae el balón (tercio × carril) y línea del receptor si el pase se completa."""
    am = ev[ev.am & ev.is_pass]
    keeper_open = (am.position == "Goalkeeper") & am.pass_type.isna()
    r = am[am.goal_kick | keeper_open].copy()
    r["kind"] = np.where(r.goal_kick, "Saque de meta", "Portero en juego")
    r["length"] = np.where(r.pass_length >= A["long_pass_yd"], "Largo", "Corto")
    r["complete"] = r.pass_outcome.isna()
    r["end_third"] = fw.third(r.pass_end_location_x)
    r["end_lane"] = fw.lane(r.pass_end_location_y)
    pos = player_positions(ev)
    rec = pd.MultiIndex.from_arrays([r.match_id, r.pass_recipient_id])
    r["receiver_group"] = np.where(r.complete, pos.reindex(rec).map(fw.POSITION_GROUP).values, "Sin receptor")
    return r[["match_id", "possession", "coach", "kind", "length", "complete", "pass_length", "pass_end_location_x",
              "pass_end_location_y", "end_third", "end_lane", "receiver_group"]]


def restart_summary(r: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Por técnico y tipo de reinicio: volumen por partido, % en corto y precisión en corto y en largo."""
    g = r.groupby(["coach", "kind"])
    out = pd.DataFrame({"n": g.size(), "pct_corto": g.length.apply(lambda s: (s == "Corto").mean() * 100)})
    for L in ["Corto", "Largo"]:
        out[f"pct_completo_{L.lower()}"] = r[r.length == L].groupby(["coach", "kind"]).complete.mean() * 100
    out["por_partido"] = per_match(out.n, scope)
    return out.reset_index()


def restart_outcomes(r: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    """Qué pasa con la jugada según se salga en corto o en largo: % de posesiones que llegan a campo rival
    (x ≥ 60), % que terminan en tiro y xG por 100 salidas."""
    p = poss.set_index(["match_id", "possession"])[["max_x", "shot", "xg"]]
    d = r.join(p, on=["match_id", "possession"])
    g = d.groupby(["coach", "kind", "length"])
    out = pd.DataFrame({"n": g.size(), "pct_llega_campo_rival": g.max_x.apply(lambda s: (s >= 60).mean() * 100),
                        "pct_tiro": g.shot.mean() * 100, "xg_por_100": g.xg.sum() / g.size() * 100})
    return out.reset_index()


def restart_receivers(r: pd.DataFrame) -> pd.DataFrame:
    """Línea del primer receptor (pases completos) por técnico, tipo y longitud."""
    return _share(r[r.complete], ["coach", "kind", "length"], "receiver_group")


# ------------------------------------------------------------------ §3.2b progresión
def progressive_actions(ev: pd.DataFrame) -> pd.DataFrame:
    """Pases y conducciones progresivas (definición del marco) con el carril donde terminan."""
    am = ev[ev.am & (ev.prog_pass | ev.prog_carry)]
    is_pass = am.prog_pass
    return pd.DataFrame({"match_id": am.match_id, "coach": am.coach,
                         "action": np.where(is_pass, "Pase progresivo", "Conducción progresiva"),
                         "end_x": np.where(is_pass, am.pass_end_location_x, am.carry_end_location_x),
                         "end_y": np.where(is_pass, am.pass_end_location_y, am.carry_end_location_y),
                         "player_id": am.player_id, "position": am.position})


def progression_by_lane(pa: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Por técnico × acción × carril: acciones por partido y % del total de esa acción."""
    t = pa.assign(lane=fw.lane(pa.end_y)).groupby(["coach", "action", "lane"]).size().rename("n")
    out = t.to_frame()
    out["por_partido"] = per_match(t, scope)
    out["share"] = t / t.groupby(["coach", "action"]).transform("sum")
    return out.reset_index()


def entries(ev: pd.DataFrame) -> pd.DataFrame:
    """Entradas en juego (en memoria): pases completos de juego abierto y conducciones que cruzan al último tercio
    (x < 80 → x ≥ 80) o que entran al área desde fuera. Método: conducción, centro o pase."""
    am = ev[ev.am]
    p = am[am.open_pass & am.complete]
    c = am[am.type == "Carry"]
    d = pd.concat([
        pd.DataFrame({"match_id": p.match_id, "coach": p.coach, "sx": p.location_x, "sy": p.location_y,
                      "ex": p.pass_end_location_x, "ey": p.pass_end_location_y,
                      "method": np.where(p.pass_cross == True, "Centro", "Pase")}),  # noqa: E712
        pd.DataFrame({"match_id": c.match_id, "coach": c.coach, "sx": c.location_x, "sy": c.location_y,
                      "ex": c.carry_end_location_x, "ey": c.carry_end_location_y, "method": "Conducción"}),
    ], ignore_index=True).dropna(subset=["sx", "ex"])
    f3 = A["third_limits"][1]
    d["final_third"] = (d.sx < f3) & (d.ex >= f3)
    d["box"] = ~fw.in_box(d.sx, d.sy) & fw.in_box(d.ex, d.ey)
    d["lane"] = fw.lane(d.ey)
    return d[d.final_third | d.box].reset_index(drop=True)


def entry_summary(en: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Entradas por partido al último tercio y al área, por técnico × carril × método."""
    rows = []
    for kind, col in [("Último tercio", "final_third"), ("Área", "box")]:
        t = en[en[col]].groupby(["coach", "lane", "method"]).size().rename("n").to_frame()
        t["por_partido"] = per_match(t.n, scope)
        t["share"] = t.n / t.groupby("coach").n.transform("sum")
        rows.append(t.reset_index().assign(entrada=kind))
    return pd.concat(rows, ignore_index=True)


# ------------------------------------------------------------------ §3.2c ocasiones
def classify_assist(sh: pd.DataFrame, key: pd.DataFrame, prev: pd.DataFrame) -> pd.Series:
    """Tipo de jugada previa al tiro. `key` = pase clave de cada tiro (alineado a sh, NaN si no hay);
    `prev` = evento propio anterior al tiro (alineado a sh). Prioridad: tiro libre directo → servicio a balón
    parado → pase atrás al área → centro → filtrado → otro pase → jugada individual → rebote o balón suelto."""
    has_key = key.type.eq("Pass").values
    sp_pass = key.pass_type.isin(["Corner", "Free Kick", "Throw-in"]).values
    # pase atrás: bandera de StatsBomb o pase raso/medio desde la línea del área hacia atrás, a la zona de peligro
    geo_cut = ((key.location_x >= A["box"]["x_min"]) & (key.pass_end_location_x < key.location_x)
               & fw.in_danger_zone(key.pass_end_location_x, key.pass_end_location_y)
               & (key.pass_height != "High Pass")).values
    cut = (key.pass_cut_back == True).values | geo_cut  # noqa: E712
    cross = (key.pass_cross == True).values  # noqa: E712
    through = ((key.pass_through_ball == True) | (key.pass_technique == "Through Ball")).values  # noqa: E712
    carry_len = np.hypot(prev.carry_end_location_x - prev.location_x, prev.carry_end_location_y - prev.location_y)
    own_carry = ((prev.type == "Carry") & (prev.player_id.values == sh.player_id.values)
                 & (carry_len >= INDIVIDUAL_CARRY_MIN)).values
    individual = (sh.shot_follows_dribble == True).values | own_carry  # noqa: E712
    return pd.Series(np.select(
        [sh.shot_type.eq("Free Kick").values, has_key & sp_pass, has_key & cut, has_key & cross, has_key & through,
         has_key, individual],
        ["Tiro libre directo", "Servicio a balón parado", "Pase atrás al área", "Centro", "Filtrado", "Otro pase",
         "Jugada individual"],
        "Rebote o balón suelto"), index=sh.index)


def shots(ev: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    """Tiros del América sin penales (en memoria) con origen de la posesión (marco) y jugada previa."""
    ev = ev.sort_values(["match_id", "index"])
    am = ev[ev.am]
    sh = am[(am.type == "Shot") & (am.shot_type != "Penalty")]
    key = ev.set_index("id").reindex(sh.shot_key_pass_id).set_index(sh.index)
    # evento propio inmediatamente anterior en la misma posesión (sin contar recepciones)
    cols = ["type", "player_id", "location_x", "location_y", "carry_end_location_x", "carry_end_location_y"]
    own = am[am.type != "Ball Receipt*"]
    prev = own.groupby(["match_id", "possession"])[cols].shift(1).loc[sh.index]
    p = poss.set_index(["match_id", "possession"])[["is_set_piece", "transition"]]
    flags = p.reindex(pd.MultiIndex.from_arrays([sh.match_id, sh.possession]))
    origin = np.select([flags.is_set_piece.fillna(False).values | sh.shot_type.eq("Free Kick").values,
                        flags.transition.fillna(False).values], ["Balón parado", "Transición"], "Juego posicional")
    return pd.DataFrame({"match_id": sh.match_id, "coach": sh.coach, "x": sh.location_x, "y": sh.location_y,
                         "xg": sh.shot_statsbomb_xg, "goal": sh.shot_outcome.eq("Goal"),
                         "origin": origin, "assist": classify_assist(sh, key, prev),
                         "body_part": sh.shot_body_part, "in_box": fw.in_box(sh.location_x, sh.location_y)})


def chance_summary(s: pd.DataFrame, scope: pd.DataFrame, by: str) -> pd.DataFrame:
    """Por técnico × categoría (`origin` o `assist`): tiros y xG por partido, xG por tiro, goles y % del xG."""
    g = s.groupby(["coach", by])
    out = pd.DataFrame({"tiros": g.size(), "xg": g.xg.sum(), "goles": g.goal.sum()})
    out["tiros_por_partido"] = per_match(out.tiros, scope)
    out["xg_por_partido"] = per_match(out.xg, scope)
    out["xg_por_tiro"] = out.xg / out.tiros
    out["pct_xg"] = out.xg / out.groupby("coach").xg.transform("sum") * 100
    out["pct_tiros"] = out.tiros / out.groupby("coach").tiros.transform("sum") * 100
    return out.reset_index()


def shot_totals(s: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    g = s.groupby("coach")
    out = pd.DataFrame({"tiros": g.size(), "np_xg": g.xg.sum(), "goles": g.goal.sum(),
                        "pct_tiros_en_area": g.in_box.mean() * 100})
    out["tiros_por_partido"] = per_match(out.tiros, scope)
    out["np_xg_por_partido"] = per_match(out.np_xg, scope)
    out["xg_por_tiro"] = out.np_xg / out.tiros
    return out.reindex(COACHES).reset_index()


def shot_grid(s: pd.DataFrame, cell: float = 4.0) -> pd.DataFrame:
    """Mapa de tiros agregado (lo que se guarda y consume el HTML): celdas de `cell` yd en la mitad rival."""
    xb = np.arange(60, 120 + cell, cell)
    yb = np.arange(0, 80 + cell, cell)
    g = zone_grid(s.assign(goles=s.goal.astype(int)), "x", "y", ["coach", "origin"], ("xg", "goles"), xb, yb)
    return g[g.n > 0].reset_index(drop=True)


# ------------------------------------------------------------------ §3.2d red de pases
def starting_lineups(ev: pd.DataFrame) -> pd.DataFrame:
    """Alineación titular del América por partido (evento Starting XI): una fila por jugador con su posición."""
    xi = ev[ev.am & (ev.type == "Starting XI")]
    rows = []
    for mid, coach, tac in zip(xi.match_id, xi.coach, xi.tactics):
        t = json.loads(tac) if isinstance(tac, str) else tac
        for p in t["lineup"]:
            rows.append({"match_id": mid, "coach": coach, "formation": str(t["formation"]),
                         "player_id": float(p["player"]["id"]), "player": p["player"]["name"],
                         "position": p["position"]["name"]})
    return pd.DataFrame(rows)


def most_used_xi(lu: pd.DataFrame) -> pd.DataFrame:
    """El 11 más usado: sistema más frecuente y, en cada puesto de ese sistema, el jugador que más veces lo
    ocupó de titular (asignación codiciosa: primero los puestos con el titular más repetido; sin repetir jugador)."""
    formation = lu.drop_duplicates("match_id").formation.mode().iat[0]
    d = lu[lu.formation == formation]
    cnt = d.groupby(["position", "player_id", "player"]).size().rename("titularidades").reset_index()
    cnt = cnt.sort_values("titularidades", ascending=False)
    chosen, used_pos, used_pl = [], set(), set()
    for r in cnt.itertuples():
        if r.position not in used_pos and r.player_id not in used_pl:
            chosen.append(r)
            used_pos.add(r.position)
            used_pl.add(r.player_id)
    out = pd.DataFrame(chosen).drop(columns="Index")
    out["formation"] = formation
    out["partidos_sistema"] = d.match_id.nunique()
    return out.reset_index(drop=True)


def pass_network(ev: pd.DataFrame, lu: pd.DataFrame, xi: pd.DataFrame, min_passes: float = 0.0,
                 names: pd.Series | None = None):
    """Red de pases del 11 más usado. Solo partidos con ese sistema, cada jugador en los partidos en que fue
    titular en SU puesto, y hasta el primer cambio del América (para que la foto sea la del 11).
    Nodo = posición media de sus pases y recepciones; arista = pases completos entre ambos por partido juntos.
    names = player_id -> nombre corto (p. ej. player_short_names()); si falta, el nombre completo."""
    lu = lu[lu.formation == xi.formation.iat[0]]
    slot = lu.merge(xi[["position", "player_id"]], on=["position", "player_id"])[["match_id", "player_id"]]
    present = slot.groupby("match_id").player_id.apply(set)
    subs = ev[ev.am & (ev.type == "Substitution")].groupby("match_id").t.min()
    p = ev[ev.am & ev.open_pass & ev.complete & ev.match_id.isin(present.index)]
    p = p[p.t < p.match_id.map(subs).fillna(np.inf)]
    ok = [a in present[m] and b in present[m] for m, a, b in zip(p.match_id, p.player_id, p.pass_recipient_id)]
    p = p[ok]
    touches = pd.concat([
        p[["match_id", "player_id", "location_x", "location_y"]].set_axis(["match_id", "player_id", "x", "y"], axis=1),
        p[["match_id", "pass_recipient_id", "pass_end_location_x", "pass_end_location_y"]]
        .set_axis(["match_id", "player_id", "x", "y"], axis=1)])
    games = slot.groupby("player_id").match_id.nunique()
    nodes = touches.groupby("player_id").agg(x_media=("x", "mean"), y_media=("y", "mean"), toques=("x", "size"))
    nodes["partidos"] = games.reindex(nodes.index)
    nodes["pases_por_partido"] = p.groupby("player_id").size().reindex(nodes.index).fillna(0) / nodes.partidos
    nodes = nodes.join(xi.set_index("player_id")[["player", "position", "titularidades"]])
    nodes["nombre"] = (nodes.index.to_series().map(names) if names is not None else nodes.player).fillna(nodes.player)
    pair = pd.DataFrame({"match_id": p.match_id, "a": np.minimum(p.player_id, p.pass_recipient_id),
                         "b": np.maximum(p.player_id, p.pass_recipient_id)})
    edges = pair.groupby(["a", "b"]).size().rename("pases").reset_index()
    both = [len(present[(present.map(lambda s, a=a, b=b: a in s and b in s))]) for a, b in zip(edges.a, edges.b)]
    edges["partidos_juntos"] = both
    edges["pases_por_partido"] = edges.pases / edges.partidos_juntos
    return nodes.reset_index(), edges[edges.pases_por_partido >= min_passes].reset_index(drop=True)


# ------------------------------------------------------------------ §3.3 recuperaciones y presión
def recoveries(poss: pd.DataFrame) -> pd.DataFrame:
    """Recuperaciones = posesiones propias que nacen de un robo (marco: `regain`), con su ubicación."""
    r = poss[poss.is_team & poss.regain & poss.start_x.notna()]
    return r[["match_id", "coach", "start_x", "start_y", "transition", "shot", "xg"]].rename(
        columns={"start_x": "x", "start_y": "y"})


def recovery_summary(rec: pd.DataFrame, poss: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Por técnico: recuperaciones por partido y por 100 posesiones rivales, altura media, % en campo rival y en
    último tercio, y % que se convierten en transición o en tiro."""
    g = rec.groupby("coach")
    opp = poss[~poss.is_team].groupby("coach").size()
    out = pd.DataFrame({"recuperaciones": g.size(), "altura_media_x": g.x.mean(),
                        "pct_campo_rival": g.x.apply(lambda s: (s >= A["press_high_x"]).mean() * 100),
                        "pct_ultimo_tercio": g.x.apply(lambda s: (s >= A["third_limits"][1]).mean() * 100),
                        "pct_a_transicion": g.transition.mean() * 100, "pct_a_tiro": g.shot.mean() * 100})
    out["por_partido"] = per_match(out.recuperaciones, scope)
    out["por_100_pos_rivales"] = out.recuperaciones / opp * 100
    return out.reindex(COACHES).reset_index()


PRESS_METRICS = ["ppda", "high_press_pct", "def_action_x_mean", "high_regains_per100opp",
                 "counterpress_per_loss", "quick_regain_pct"]


def pressing_by_coach(mf: pd.DataFrame, scope: pd.DataFrame, cols=PRESS_METRICS) -> pd.DataFrame:
    """Métricas de presión del marco (match_features): mediana por partido de cada técnico (y P25–P75)."""
    d = mf[mf.match_id.isin(scope.match_id)].assign(coach=lambda x: x.match_id.map(scope.set_index("match_id").coach))
    q = d.groupby("coach")[list(cols)].quantile([.25, .5, .75]).unstack()
    out = pd.DataFrame({c: q[(c, .5)] for c in cols})
    for c in cols:
        out[f"{c}_p25"], out[f"{c}_p75"] = q[(c, .25)], q[(c, .75)]
    return out.reindex(COACHES).reset_index()


LEAGUE_METRICS = {  # métrica de team-match-stats (toda la liga) -> (etiqueta, "más = ...")
    "team_match_ppda": ("PPDA (pases rivales por acción defensiva)", "menos = presión más intensa"),
    "team_match_fhalf_pressures_ratio": ("% de presiones en campo rival", "más = presiona más arriba"),
    "team_match_counterpressures": ("Contrapresiones por partido", "más = reacciona más tras perder"),
    "team_match_counterpressure_regains": ("Recuperaciones por contrapresión por partido", "más = recupera al reaccionar"),
    "team_match_defensive_distance": ("Distancia media de las acciones defensivas a su portería (m)", "más = defiende más arriba"),
    "team_match_counter_attacking_shots": ("Tiros de contraataque por partido", "más = castiga en transición"),
    "team_match_counter_attacking_shots_conceded": ("Tiros de contraataque concedidos por partido", "menos = controla la transición defensiva"),
}


def league_benchmark(tml: pd.DataFrame, cols=tuple(LEAGUE_METRICS), min_matches: int = MIN_MATCHES,
                     relative: bool = True) -> pd.DataFrame:
    """Media por periodo de técnico (técnico × equipo) en la ventana oficial, para toda la Liga MX (≥ min_matches).
    Misma fuente (team-match-stats de StatsBomb) para el América y para la liga.
    relative=True: cada partido se expresa como diferencia con la media de la liga EN ESE TORNEO. Hace falta
    porque la liga entera se mueve (el PPDA medio pasa de ~8 en 2021 a ~12 en 2024 y las recuperaciones por
    contrapresión se duplican desde Ap 2024): sin esto, un técnico reciente parece presionar menos solo por la época."""
    d = tml[(tml.split == "train") & (tml.manager != "")].copy()
    if relative:
        cols = list(cols)
        d[cols] = d[cols] - tml[tml.split == "train"].groupby("torneo")[cols].transform("mean").loc[d.index]
    g = d.groupby("coach_team")
    out = g[list(cols)].mean()
    out["partidos"] = g.size()
    out["manager"], out["team"] = g.manager.first(), g.team_name.first()
    out = out[out.partidos >= min_matches]
    out["coach"] = np.where(out.team == fw.TEAM, out.manager.map(short), None)
    return out.reset_index()


def league_rank(bench: pd.DataFrame, col: str, coach: str = PROTAGONIST, higher_is_more: bool = True) -> dict:
    """Posición de un técnico del América entre los periodos de la liga: percentil (0–100) y lugar (1 = el que más)."""
    v = bench.loc[bench.coach == coach, col].iat[0]
    ref = bench[col].dropna()
    pct = (ref < v).mean() * 100 + (ref == v).mean() * 50
    place = int((ref > v).sum() + 1) if higher_is_more else int((ref < v).sum() + 1)
    return {"valor": v, "percentil": pct, "lugar": place, "de": len(ref), "mediana_liga": ref.median()}


# ------------------------------------------------------------------ §3.3 transiciones
def transition_summary(poss: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Transiciones ofensivas (a favor) y defensivas (del rival) con la definición del marco: cuántas por partido,
    qué tan rápido llegan al último tercio o al tiro (mediana, s), % que termina en tiro y xG por partido."""
    rows = []
    for side, mask in [("A favor", poss.is_team), ("En contra", ~poss.is_team)]:
        t = poss[mask & poss.transition].groupby("coach")
        base = poss[mask & poss.regain].groupby("coach").size()
        out = pd.DataFrame({"transiciones": t.size(), "segundos_mediana": t.t_reach_f3.median(),
                            "pct_tiro": t.shot.mean() * 100, "xg": t.xg.sum(), "xg_por_transicion": t.xg.mean(),
                            "pct_de_recuperaciones": t.size() / base * 100})
        out["por_partido"] = per_match(out.transiciones, scope)
        out["xg_por_partido"] = per_match(out.xg, scope)
        rows.append(out.reindex(COACHES).reset_index().assign(lado=side))
    return pd.concat(rows, ignore_index=True)


def counterpress_summary(poss: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Transición defensiva inmediata (marco: losses_and_regains): pérdidas en juego y % recuperado en ≤ 5 s."""
    lr = fw.losses_and_regains(poss).join(scope.set_index("match_id").coach)
    g = lr.groupby("coach")[["losses", "quick_regains"]].sum()
    g["pct_recuperado_5s"] = g.quick_regains / g.losses * 100
    g["perdidas_por_partido"] = per_match(g.losses, scope)
    return g.reindex(COACHES).reset_index()


def transition_starts(poss: pd.DataFrame) -> pd.DataFrame:
    """Dónde nacen las transiciones, SIEMPRE en coordenadas del América (ataca a la derecha):
    a favor = donde recupera; en contra = donde pierde el balón (se voltea la ubicación del rival)."""
    t = poss[poss.transition & poss.start_x.notna()]
    fav = t[t.is_team]
    con = t[~t.is_team]
    return pd.concat([
        pd.DataFrame({"coach": fav.coach, "lado": "A favor", "x": fav.start_x, "y": fav.start_y, "xg": fav.xg}),
        pd.DataFrame({"coach": con.coach, "lado": "En contra", "x": 120 - con.start_x, "y": 80 - con.start_y, "xg": con.xg}),
    ], ignore_index=True)


# ------------------------------------------------------------------ §3.4 forma defensiva (360)
SHAPE_METRICS = {"altura_linea": "Altura de la última línea (yd desde su portería)",
                 "distancia_lineas": "Distancia entre la última línea y la siguiente (yd)",
                 "largo_bloque": "Largo del bloque (yd)", "ancho_bloque": "Ancho del bloque (yd)",
                 "distancia_balon_linea": "Distancia del balón a la última línea (yd)"}
PHASES = ["Bloque alto", "Bloque medio", "Bloque bajo"]


def rival_open_play_passes(ev: pd.DataFrame, poss: pd.DataFrame) -> pd.DataFrame:
    """Pases rivales de juego abierto (en memoria), fuera de posesiones de balón parado, con el balón en coordenadas
    del América (ataca a la derecha). fase = altura del balón con los umbrales de presión del marco (≥ 60 bloque alto,
    40–60 medio, < 40 bajo). situacion = 'Tras pérdida' si la posesión rival nació de una del América hace ≤ 5 s
    (ventana de contrapresión del marco); si no, 'Posesión rival'."""
    p = poss.sort_values(["match_id", "possession"]).assign(prev_team=lambda d: d.groupby("match_id").team.shift())
    r = ev[(ev.team != fw.TEAM) & (ev.possession_team != fw.TEAM) & ev.is_pass & ev.pass_type.isna()]
    r = r.merge(p[["match_id", "possession", "t_start", "prev_team", "is_set_piece"]], on=["match_id", "possession"],
                how="left")
    r = r[~r.is_set_piece.fillna(False).astype(bool)]
    ball_x = 120 - r.location_x
    after_loss = (r.prev_team == fw.TEAM) & (r.t - r.t_start <= A["counterpress_window_s"])
    return pd.DataFrame({"id": r.id.values, "match_id": r.match_id.values, "coach": r.coach.values,
                         "ball_x": ball_x.values, "ball_y": (80 - r.location_y).values,
                         "fase": np.select([ball_x >= A["press_high_x"], ball_x >= A["press_mid_x"]], PHASES[:2],
                                           PHASES[2]),
                         "situacion": np.where(after_loss, "Tras pérdida", "Posesión rival")})


def defensive_shape(frames: pd.DataFrame, passes: pd.DataFrame) -> pd.DataFrame:
    """Forma defensiva del América en cada pase rival (en memoria). Usa solo a sus jugadores de campo VISIBLES en el 360
    (sin portero), volteados a coordenadas del América. Por frame: jugadores visibles; cuánto ve la toma detrás del más
    retrasado; altura de la última línea (media de los `shape_line_players` más retrasados); distancia a la siguiente
    línea (media de los siguientes hasta `shape_block_players`); largo (x del 8.º − x del 1.º) y ancho (rango de y de
    los 8) del bloque. util = cumple los mínimos del marco (jugadores visibles y vista detrás de la línea)."""
    fr = frames[frames.id.isin(passes.id)]
    team = fr.teammate.astype("boolean").fillna(False).astype(bool)
    gk = fr.keeper.astype("boolean").fillna(False).astype(bool)
    d = fr[~team & ~gk & fr.location_x.notna()]
    d = pd.DataFrame({"id": d.id, "x": 120 - d.location_x, "y": 80 - d.location_y}).sort_values(["id", "x"])
    d["rk"] = d.groupby("id").cumcount()
    nl, nb = A["shape_line_players"], A["shape_block_players"]
    line, nxt, blk = d[d.rk < nl], d[(d.rk >= nl) & (d.rk < nb)], d[d.rk < nb]
    out = pd.DataFrame({"visibles": d.groupby("id").size(), "x_primero": d[d.rk == 0].set_index("id").x,
                        "altura_linea": line.groupby("id").x.mean(), "siguiente_linea": nxt.groupby("id").x.mean(),
                        "x_octavo": d[d.rk == nb - 1].set_index("id").x,
                        "ancho_bloque": blk.groupby("id").y.agg(lambda s: s.max() - s.min())})
    # punto visible más cercano a la portería del América (visible_area viene en coordenadas del rival: x1, y1, x2, ...)
    va = fr.drop_duplicates("id").set_index("id").visible_area
    out["vista_min_x"] = va.reindex(out.index).map(lambda a: 120 - max(a[0::2]) if a is not None and len(a) else np.nan)
    out["vista_detras"] = out.x_primero - out.vista_min_x
    out["distancia_lineas"] = out.siguiente_linea - out.altura_linea
    out["largo_bloque"] = out.x_octavo - out.x_primero
    out["util"] = (out.visibles >= A["shape_min_visible"]) & (out.vista_detras >= A["shape_min_behind_yd"])
    out = passes.set_index("id").join(out, how="left")
    out["distancia_balon_linea"] = out.ball_x - out.altura_linea
    out["con_360"] = out.visibles.notna()
    out["util"] = out.util.astype("boolean").fillna(False).astype(bool)
    return out.reset_index()


def shape_summary(shape: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Por técnico × `by` (fase y/o situacion): pases rivales, % con 360, % de frames útiles y mediana (P25–P75) de
    cada métrica de forma en los frames útiles, más la mediana de la altura del balón."""
    g = shape.groupby(["coach"] + by)
    out = pd.DataFrame({"pases_rivales": g.size(), "pct_con_360": g.con_360.mean() * 100,
                        "frames_utiles": g.util.sum(), "pct_utiles": g.util.mean() * 100})
    u = shape[shape.util].groupby(["coach"] + by)
    for m in list(SHAPE_METRICS) + ["ball_x"]:
        q = u[m].quantile([.25, .5, .75]).unstack()
        out[m], out[f"{m}_p25"], out[f"{m}_p75"] = q[.5], q[.25], q[.75]
    return out.reset_index()


def match_level_diff(shape: pd.DataFrame, metric: str, a: str, b: str, n: int = 2000, seed: int = 0,
                     **filters) -> dict:
    """Diferencia a − b de la media de las medianas por partido de `metric` (frames útiles que cumplen `filters`), con
    IC 90 % por remuestreo de partidos: el partido es la unidad (los frames de un partido no son independientes)."""
    d = shape[shape.util]
    for k, v in filters.items():
        d = d[d[k] == v]
    pm = d.groupby(["coach", "match_id"])[metric].median()
    xa, xb = pm.loc[a].values, pm.loc[b].values
    rng = np.random.default_rng(seed)
    boot = [rng.choice(xa, len(xa)).mean() - rng.choice(xb, len(xb)).mean() for _ in range(n)]
    return {"diferencia": xa.mean() - xb.mean(), "lo": np.percentile(boot, 5), "hi": np.percentile(boot, 95),
            "partidos_a": len(xa), "partidos_b": len(xb)}


# ------------------------------------------------------------------ §3.8 balón parado
SP_KINDS = ["Córner", "Tiro libre", "Saque de banda"]
RESTART_PASS = {"Corner", "Free Kick", "Throw-in"}
SP_SHOT_ZONES = ["Área chica", "Zona de penal", "Área (costados)", "Fuera del área"]
SP_LEAGUE_METRICS = {  # team-match-stats (toda la liga) -> (etiqueta, lectura)
    "team_match_corners": ("Córners por partido", "más = más córners"),
    "team_match_xg_per_corner": ("xG por córner", "más = córners más peligrosos"),
    "team_match_corner_shot_ratio": ("% de córners que terminan en tiro", "más = remata más"),
    "team_match_sp_xg": ("xG a balón parado por partido", "más = más peligro"),
    "team_match_sp_xg_conceded": ("xG a balón parado concedido por partido", "menos = defiende mejor"),
    "team_match_xg_per_corner_conceded": ("xG concedido por córner", "menos = defiende mejor"),
    "team_match_corner_shot_ratio_conceded": ("% de córners rivales que terminan en tiro", "menos = defiende mejor"),
}


def load_set_pieces(scope: pd.DataFrame) -> pd.DataFrame:
    """fct_set_piece (Gold) de los partidos de `scope`, con técnico."""
    sp = pd.read_parquet(GOLD / "fct_set_piece.parquet")
    sp = sp[sp.match_id.isin(scope.match_id)]
    return sp.assign(coach=sp.match_id.map(scope.set_index("match_id").coach))


def set_piece_plays(sp: pd.DataFrame, ev: pd.DataFrame) -> pd.DataFrame:
    """Jugadas a balón parado DIRECTAS: la posesión la abre el saque del equipo que la tiene (su primer evento es el
    córner, el tiro libre o el saque de banda, o un tiro libre directo). Descarta posesiones que solo heredan el
    play_pattern (p. ej., el portero rival atrapa el córner). Córners, todos; tiros libres y saques de banda, solo desde
    el último tercio del que saca. restart_id = id del saque (para el 360 y para separar el remate directo)."""
    first = (ev[ev.team == ev.possession_team].groupby(["match_id", "possession"]).head(1)
             .set_index(["match_id", "possession"]).id.rename("restart_id"))
    restart = sp.start_pass_type.isin(RESTART_PASS) | ((sp.start_type == "Shot") & (sp.kind == "Tiro libre"))
    zone_ok = ((sp.kind == "Córner")
               | ((sp.kind == "Tiro libre") & (sp.start_x >= A["set_piece_free_kick_x_min"]))
               | ((sp.kind == "Saque de banda") & (sp.start_x >= A["set_piece_throw_in_x_min"])))
    d = sp[restart & zone_ok].join(first, on=["match_id", "possession"])
    return d.assign(lado=np.where(d.is_team, "A favor", "En contra"), tiro_directo=d.start_type.eq("Shot"))


def post_side(y, taken_y):
    """Primer o segundo palo respecto del lado del saque (mitades del ancho: sin umbral extra)."""
    return np.where((np.asarray(y) < 40) == (np.asarray(taken_y) < 40), "Primer palo", "Segundo palo")


def set_piece_shots(ev: pd.DataFrame, plays: pd.DataFrame) -> pd.DataFrame:
    """Tiros sin penales de las jugadas a balón parado (en memoria), en coordenadas de QUIEN ATACA (portería a la
    derecha). directo = remate asistido por el propio saque o tiro libre directo; si no, segunda jugada."""
    sh = ev[(ev.type == "Shot") & (ev.shot_type != "Penalty") & (ev.team == ev.possession_team)]
    keys = ["match_id", "possession", "coach", "lado", "kind", "location_y", "restart_id"]
    d = sh.drop(columns="coach").merge(plays[keys].rename(columns={"location_y": "taken_y"}),
                                       on=["match_id", "possession"])
    return pd.DataFrame({"match_id": d.match_id, "possession": d.possession, "coach": d.coach, "lado": d.lado,
                         "kind": d.kind, "x": d.location_x, "y": d.location_y, "xg": d.shot_statsbomb_xg,
                         "goal": d.shot_outcome.eq("Goal"),
                         "directo": d.shot_key_pass_id.eq(d.restart_id) | d.id.eq(d.restart_id),
                         "zona": fw.set_piece_target_zone(d.location_x, d.location_y, np.inf),
                         "palo": post_side(d.location_y, d.taken_y)}).reset_index(drop=True)


def set_piece_summary(plays: pd.DataFrame, shots: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    """Por técnico × lado × tipo (y 'Total'): jugadas por partido, % que termina en tiro, xG por jugada (toda la
    posesión y solo el remate directo), goles y xG por partido. Sin penales."""
    per_play = shots.groupby(["match_id", "possession"]).agg(xg=("xg", "sum"), goles=("goal", "sum"))
    per_play["xg_directo"] = shots[shots.directo].groupby(["match_id", "possession"]).xg.sum()
    p = plays.drop(columns="xg").join(per_play, on=["match_id", "possession"]).fillna({"xg": 0, "goles": 0, "xg_directo": 0})
    p["con_tiro"] = p.set_index(["match_id", "possession"]).index.isin(per_play.index)
    p = pd.concat([p, p.assign(kind="Total")])
    g = p.groupby(["coach", "lado", "kind"])
    out = pd.DataFrame({"jugadas": g.size(), "pct_tiro": g.con_tiro.mean() * 100, "xg": g.xg.sum(),
                        "xg_por_jugada": g.xg.mean(), "xg_directo_por_jugada": g.xg_directo.mean(),
                        "goles": g.goles.sum(), "pct_corto": g.delivery.apply(lambda s: (s == "Corto").mean() * 100)})
    out["pct_xg_directo"] = out.xg_directo_por_jugada / out.xg_por_jugada.replace(0, np.nan) * 100
    out["por_partido"] = per_match(out.jugadas, scope)
    out["xg_por_partido"] = per_match(out.xg, scope)
    return out.reset_index()


def delivery_summary(plays: pd.DataFrame) -> pd.DataFrame:
    """Dónde cae el envío (zona del marco: corto, área chica, zona de penal, costados, fuera) y tipo de envío
    (cerrado, abierto, corto), por técnico × lado × tipo (córner y tiro libre indirecto)."""
    d = plays[(plays.kind != "Saque de banda") & ~plays.tiro_directo]
    return pd.concat([_share(d, ["coach", "lado", "kind"], "target_zone").rename(columns={"target_zone": "valor"})
                      .assign(dimension="Zona de entrega"),
                      _share(d, ["coach", "lado", "kind"], "delivery").rename(columns={"delivery": "valor"})
                      .assign(dimension="Tipo de envío")], ignore_index=True)


def shot_zone_summary(shots: pd.DataFrame) -> pd.DataFrame:
    """Tiros y xG por zona de remate (y por palo en córners), por técnico × lado: % del xG a balón parado."""
    rows = []
    for dim, d in [("zona", shots), ("palo", shots[shots.kind == "Córner"])]:
        g = d.groupby(["coach", "lado", dim])
        t = pd.DataFrame({"tiros": g.size(), "xg": g.xg.sum(), "goles": g.goal.sum()}).reset_index()
        t["pct_xg"] = t.xg / t.groupby(["coach", "lado"]).xg.transform("sum") * 100
        t["xg_por_tiro"] = t.xg / t.tiros
        rows.append(t.rename(columns={dim: "valor"}).assign(dimension=dim))
    return pd.concat(rows, ignore_index=True)


def set_piece_xg_share(all_shots: pd.DataFrame, sp_shots: pd.DataFrame) -> pd.DataFrame:
    """% del xG sin penales del América que es balón parado, con dos definiciones:
    marco = toda la posesión que nace de córner o tiro libre (en cualquier zona) o de saque de banda en el último
    tercio (story.shots, origen 'Balón parado'); jugadas de §3.8 = córners, tiros libres y saques de banda del último
    tercio, toda la posesión; remate directo = solo el remate que asiste el saque o el tiro libre directo."""
    tot = all_shots.groupby("coach").xg.sum()
    fav = sp_shots[sp_shots.lado == "A favor"]
    return pd.DataFrame({"xg_total": tot,
                         "pct_marco": all_shots[all_shots.origin == "Balón parado"].groupby("coach").xg.sum() / tot * 100,
                         "pct_jugadas": fav.groupby("coach").xg.sum() / tot * 100,
                         "pct_directo": fav[fav.directo].groupby("coach").xg.sum() / tot * 100}
                        ).reindex(COACHES).reset_index()


_BOX_GRID = np.stack(np.meshgrid(np.arange(A["box"]["x_min"] + 0.5, 120, 1.0),
                                  np.arange(A["box"]["y_min"] + 0.5, A["box"]["y_max"], 1.0)), -1).reshape(-1, 2)
_IN_SIX = (_BOX_GRID[:, 0] >= 114) & (_BOX_GRID[:, 1] >= 30) & (_BOX_GRID[:, 1] <= 50)


def box_visibility(poly) -> tuple[float, float]:
    """Fracción visible del área y del área chica (rejilla de 1 yd) dentro del polígono visible_area del 360."""
    from matplotlib.path import Path
    if poly is None or len(poly) < 6:
        return np.nan, np.nan
    inside = Path(np.asarray(poly, dtype=float).reshape(-1, 2)).contains_points(_BOX_GRID)
    return inside.mean(), inside[_IN_SIX].mean()


def corner_defense(frames: pd.DataFrame, plays: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """360 en el momento del saque de cada córner RIVAL que no se saca en corto (en memoria). Coordenadas del rival
    (la portería del América a la derecha), con el saque siempre desde arriba (y volteada si se saca desde y > 40).
    Por córner: defensores del América en el área y en el área chica (sin portero), atacantes en el área y cuántos
    defensores del área están 'pegados' a un atacante (≤ set_piece_marking_yd). util = la toma ve al menos
    `set_piece_min_box_visible` del área y toda el área chica (fuera de cuadro no hay nadie: si no, faltarían jugadores).
    Devuelve (una fila por córner, posiciones de los defensores en los frames útiles); ambas solo en memoria."""
    c = plays[(plays.lado == "En contra") & (plays.kind == "Córner") & (plays.delivery != "Corto")]
    fr = frames[frames.id.isin(c.restart_id)].copy()
    flip = fr.id.map(c.set_index("restart_id").location_y) > 40
    fr["y"] = np.where(flip, 80 - fr.location_y, fr.location_y)
    fr["x"] = fr.location_x
    team = fr.teammate.astype("boolean").fillna(False).astype(bool)
    gk = fr.keeper.astype("boolean").fillna(False).astype(bool)
    actor = fr.actor.astype("boolean").fillna(False).astype(bool)
    fr["rol"] = np.select([~team & ~gk, team & ~gk & ~actor], ["Defensor", "Atacante"], "Otro")
    fr["en_area"] = fw.in_box(fr.x, fr.y)
    fr["en_chica"] = (fr.x >= 114) & (fr.y >= 30) & (fr.y <= 50)
    rows = []
    for fid, f in fr.groupby("id"):
        dfn = f[(f.rol == "Defensor") & f.en_area]
        atk = f[(f.rol == "Atacante") & f.en_area]
        if len(dfn) and len(atk):
            dist = np.hypot(dfn.x.values[:, None] - atk.x.values[None, :], dfn.y.values[:, None] - atk.y.values[None, :])
            pegados = int((dist.min(axis=1) <= A["set_piece_marking_yd"]).sum())
        else:
            pegados = 0
        area, six = box_visibility(f.visible_area.iat[0])
        rows.append({"restart_id": fid, "defensores_area": len(dfn), "defensores_chica": int(dfn.en_chica.sum()),
                     "atacantes_area": len(atk), "pegados": pegados, "area_visible": area,
                     "util": bool(area >= A["set_piece_min_box_visible"] and six == 1)})
    out = c[["match_id", "coach", "restart_id"]].merge(pd.DataFrame(rows), on="restart_id", how="left")
    out["con_360"] = out.util.notna()
    out["util"] = out.util.astype("boolean").fillna(False).astype(bool)
    out["pct_pegados"] = out.pegados / out.defensores_area.replace(0, np.nan) * 100
    keep = fr.id.isin(out.restart_id[out.util]) & fr.rol.isin(["Defensor", "Atacante"]) & fr.en_area
    return out, fr.loc[keep, ["id", "rol", "x", "y"]].assign(coach=fr.id.map(c.set_index("restart_id").coach))


def marking_vs_chance(players: pd.DataFrame, n: int = 200, seed: int = 0) -> pd.DataFrame:
    """¿Los defensores se pegan a un rival más de lo que daría el azar? Por técnico: % de defensores del área a
    ≤ set_piece_marking_yd de un atacante en el mismo córner (observado) frente al mismo cálculo con los atacantes de
    OTRO córner del mismo técnico, elegido al azar (n repeticiones). Si el observado supera claramente al azar, hay
    marcaje al hombre; lo que queda por debajo se explica con posiciones fijas (zona)."""
    rng = np.random.default_rng(seed)
    rows = []
    for coach, d in players.groupby("coach"):
        by = {i: (g[g.rol == "Defensor"][["x", "y"]].values, g[g.rol == "Atacante"][["x", "y"]].values)
              for i, g in d.groupby("id")}
        ids = list(by)

        def share(pairs):
            num = den = 0
            for dfn, atk in pairs:
                if len(dfn) and len(atk):
                    dist = np.hypot(dfn[:, None, 0] - atk[None, :, 0], dfn[:, None, 1] - atk[None, :, 1])
                    num += (dist.min(axis=1) <= A["set_piece_marking_yd"]).sum()
                den += len(dfn)
            return num / den * 100 if den else np.nan
        obs = share(by[i] for i in ids)
        perm = [share((by[i][0], by[j][1]) for i, j in zip(ids, rng.permutation(ids))) for _ in range(n)]
        rows.append({"coach": coach, "corners": len(ids), "pct_pegados": obs, "pct_pegados_azar": np.mean(perm),
                     "azar_p95": np.percentile(perm, 95)})
    return pd.DataFrame(rows).set_index("coach").reindex(COACHES).reset_index()


def corner_defense_summary(cd: pd.DataFrame) -> pd.DataFrame:
    """Por técnico: córners rivales (no cortos), % con 360 útil, mediana de defensores en el área y en el área chica,
    de atacantes en el área, y % medio de defensores del área pegados a un atacante."""
    g = cd.groupby("coach")
    u = cd[cd.util].groupby("coach")
    out = pd.DataFrame({"corners": g.size(), "pct_utiles": g.util.mean() * 100, "utiles": g.util.sum(),
                        "defensores_area": u.defensores_area.median(), "defensores_area_media": u.defensores_area.mean(),
                        "defensores_chica": u.defensores_chica.mean(), "atacantes_area": u.atacantes_area.mean(),
                        "pct_pegados": u.pct_pegados.mean()})
    return out.reindex(COACHES).reset_index()


# ------------------------------------------------------------------ guardar solo agregados
FORBIDDEN = {"id", "index", "possession", "timestamp", "related_events", "x", "y", "location_x", "location_y",
             "pass_end_location_x", "pass_end_location_y", "sx", "sy", "ex", "ey", "end_x", "end_y", "ball_y",
             "visible_area", "x_primero", "x_octavo", "vista_min_x"}


def save_story(df: pd.DataFrame, name: str, muestra: str = "ventana") -> str:
    """Guarda un AGREGADO en data/gold/analysis/story_<name>.parquet. Rechaza columnas de nivel evento
    (ids, coordenadas de eventos sueltos): los datos crudos no se pueden compartir. Las celdas de rejilla usan
    x0/x1/y0/y1 y los nodos de la red, posiciones medias (x_media/y_media)."""
    bad = FORBIDDEN & set(df.columns)
    if bad:
        raise ValueError(f"story_{name}: columnas de nivel evento no permitidas: {sorted(bad)}")
    ANALYSIS.mkdir(parents=True, exist_ok=True)
    path = ANALYSIS / f"story_{name}.parquet"
    df.assign(muestra=muestra).to_parquet(path, index=False)
    return str(path)

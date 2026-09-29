"""LA HISTORIA DE JARDINE (todo.md §3.2 con balón y §3.3 sin balón) — cálculos reutilizables.

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


# ------------------------------------------------------------------ guardar solo agregados
FORBIDDEN = {"id", "index", "possession", "timestamp", "related_events", "x", "y", "location_x", "location_y",
             "pass_end_location_x", "pass_end_location_y", "sx", "sy", "ex", "ey", "end_x", "end_y"}


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

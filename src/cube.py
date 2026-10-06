"""CUBO DE AGREGADOS POR PARTIDO — la base del explorador (app Streamlit y reporte HTML).

Idea: todo lo que el explorador muestra se calcula sumando o promediando partidos de este cubo, así que el
filtro de periodo y de contexto (técnico, torneo, fechas, un partido, localía, fuerza del rival) funciona sin
eventos. Reglas:
- Solo AGREGADOS: nada de eventos, coordenadas sueltas ni ids de evento (`_guard`). Las columnas `sb_*`
  (estadísticas de StatsBomb tal cual) no entran; los jugadores van por técnico × torneo, no por partido.
- Todas las definiciones vienen del marco (src/framework.py, src/features.py) a través de match_features,
  fct_possession, fct_set_piece, fct_segment y las funciones de src/story.py: el explorador y la historia
  (notebook 05) cuentan lo mismo con las mismas definiciones.
- Cada partido lleva su `muestra` (ventana, validación, prueba): las cifras titulares salen solo de la ventana.

Construcción: `python -m src.cube` → data/gold/cube/*.parquet (ignorado). `app/export_data.py` los copia a la app.
Las funciones de consulta (select, nivel_muestra, indicadores, adn_percentil, rejilla, ...) solo usan pandas y
numpy, para que la app sea ligera.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

CUBE = Path(__file__).resolve().parents[1] / "data" / "gold" / "cube"
CELL = 10                       # yd: rejilla de 12 × 8 celdas sobre la cancha 120 × 80
NX, NY = 120 // CELL, 80 // CELL
RIVAL_TIERS = ["Débil", "Medio", "Fuerte"]
LAYERS = {  # capa de la rejilla -> qué cuenta (todas en el marco del América: ataca hacia la derecha)
    "tiros": "Tiros del América sin penales (n, xG, goles), ubicación del remate",
    "tiros_rival": "Tiros del rival sin penales, ubicación en el marco del América (portería propia a la izquierda)",
    "recuperaciones": "Posesiones propias que nacen de un robo (marco: regain), donde empiezan",
    "acciones_defensivas": "Acciones defensivas del América (marco: DEF_ACTIONS), donde ocurren",
    "pases_progresivos": "Pases progresivos del América (marco), donde terminan",
}
FORBIDDEN = {"id", "index", "possession", "timestamp", "related_events", "x", "y", "location_x", "location_y",
             "pass_end_location_x", "pass_end_location_y", "start_x", "start_y", "shot_x", "shot_y", "player_id"}
MIN_FEW, MIN_TORNEO, MIN_ERA = 1, 5, 30   # regla de muestra (todo.md: definición del producto)


# ------------------------------------------------------------------ construcción (necesita Silver/Gold)
def _guard(df: pd.DataFrame, name: str) -> pd.DataFrame:
    bad = (FORBIDDEN & set(df.columns)) | {c for c in df.columns if str(c).startswith("sb_")}
    if bad:
        raise ValueError(f"cubo {name}: columnas no permitidas (nivel evento o StatsBomb crudo): {sorted(bad)}")
    return df


def _cells(x: pd.Series, y: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    cx = np.clip(np.floor(x.astype(float) / CELL), 0, NX - 1).astype(int)
    cy = np.clip(np.floor(y.astype(float) / CELL), 0, NY - 1).astype(int)
    return cx, cy


def _grid(d: pd.DataFrame, capa: str, x: str, y: str, xg: str | None = None, goal: str | None = None) -> pd.DataFrame:
    d = d.dropna(subset=[x, y])
    cx, cy = _cells(d[x], d[y])
    g = pd.DataFrame({"match_id": d.match_id.values, "cx": cx, "cy": cy,
                      "xg": d[xg].values if xg else 0.0, "goles": d[goal].astype(int).values if goal else 0})
    out = g.groupby(["match_id", "cx", "cy"]).agg(n=("xg", "size"), xg=("xg", "sum"), goles=("goles", "sum")).reset_index()
    return out.assign(capa=capa)


def build(verbose: bool = True) -> dict[str, pd.DataFrame]:
    """Construye el cubo para TODOS los partidos del América (ventana, validación y prueba)."""
    import joblib

    from src import coach_profile as C
    from src import story as S
    from src.features import FEATURES
    from src.modeling import ROLE_COLS
    from src.pipeline.config import GOLD, SILVER

    log = print if verbose else (lambda *a, **k: None)
    dim = pd.read_parquet(GOLD / "dim_match.parquet")
    coaches = dim.team_manager.map(C.short).unique().tolist()
    scope = S.match_scope(dim, window_only=False, coaches=coaches)
    mf = pd.read_parquet(GOLD / "match_features.parquet")
    tml = pd.read_parquet(GOLD / "fct_team_match_league.parquet")
    log(f"partidos: {len(scope)} · técnicos: {', '.join(coaches)}")

    # --- partidos: meta + indicadores del marco + ADN del partido
    cuts = S.rival_terciles(tml)
    ind = [c for c in FEATURES if c in mf.columns and not c.startswith("sb_")]
    p = scope[["match_id", "match_date", "torneo", "fase", "is_home", "opponent", "rival_ppg_prev", "goals_for",
               "goals_against", "result", "coach", "split", "muestra"]].copy()
    p["match_date"] = pd.to_datetime(p.match_date)
    p["localia"] = np.where(p.is_home, "Local", "Visita")
    p["rival_nivel"] = np.select([p.rival_ppg_prev < cuts[0], p.rival_ppg_prev < cuts[1]], RIVAL_TIERS[:2], RIVAL_TIERS[2])
    p.loc[p.rival_ppg_prev.isna(), "rival_nivel"] = None
    p["puntos"] = p.result.map({"W": 3, "D": 1, "L": 0})
    p = p.merge(mf[["match_id"] + ind], on="match_id", how="left")
    xg = mf.set_index("match_id")
    p["xg_favor"] = p.match_id.map(xg.sb_np_xg)          # resultado del partido (xG sin penales), no la tabla cruda
    p["xg_contra"] = p.match_id.map(xg.sb_np_xg_conceded)
    ma = C.build_match_axes(tml)
    am = ma[ma.team_name == C.TEAM].set_index("match_id")[[f"adj__{a}" for a in C.AXES]]
    p = p.join(am.set_axis([f"adn__{a}" for a in C.AXES], axis=1), on="match_id")

    ev = S.load_story_events(scope)                      # eventos: SOLO en memoria
    poss = S.load_possessions(scope)
    lu = S.starting_lineups(ev)
    p["sistema"] = p.match_id.map(lu.drop_duplicates("match_id").set_index("match_id").formation.map(
        lambda f: "-".join(str(f))))
    half = S.halftime_state(ev)
    p["marcador_descanso"] = p.match_id.map(half)
    log("partidos listos")

    # --- rejillas por partido
    sh = ev[ev.np_shot]
    am_sh, op_sh = sh[sh.am], sh[~sh.am]
    op_sh = op_sh.assign(fx=120 - op_sh.location_x, fy=80 - op_sh.location_y)
    rec = poss[poss.is_team & poss.regain.fillna(False)]
    da = ev[ev.am & ev.def_action]
    pp = ev[ev.am & ev.prog_pass]
    zonas = pd.concat([
        _grid(am_sh.assign(goal=am_sh.shot_outcome.eq("Goal")), "tiros", "location_x", "location_y", "shot_statsbomb_xg", "goal"),
        _grid(op_sh.assign(goal=op_sh.shot_outcome.eq("Goal")), "tiros_rival", "fx", "fy", "shot_statsbomb_xg", "goal"),
        _grid(rec, "recuperaciones", "start_x", "start_y"),
        _grid(da, "acciones_defensivas", "location_x", "location_y"),
        _grid(pp, "pases_progresivos", "pass_end_location_x", "pass_end_location_y"),
    ], ignore_index=True)
    log(f"rejillas: {len(zonas):,} celdas")

    # --- balón parado por partido (definición del marco: fct_set_piece, posesiones que abre el saque propio)
    sp = pd.read_parquet(GOLD / "fct_set_piece.parquet")
    sp = sp[sp.match_id.isin(scope.match_id)]
    bp = (sp.assign(lado=np.where(sp.is_team, "A favor", "En contra"))
          .groupby(["match_id", "lado", "kind", "delivery", "target_zone"], dropna=False)
          .agg(jugadas=("shot", "size"), con_tiro=("shot", "sum"), xg=("xg", "sum")).reset_index())

    # --- tramos de 15' × marcador (fct_segment, ya agregado) para el efecto del marcador
    seg = S.load_segments(scope)
    tramos = seg[["match_id", "minute_bin", "game_state", "duration_min"] + list(S.CONTEXT_METRICS)]

    # --- cambios por partido: conteos por marcador y perfil (sin nombres ni minutos sueltos)
    pm_all = S.load_player_matches(scope)
    usage = S.player_usage(pm_all)
    u3 = joblib.load(Path(__file__).resolve().parents[1] / "models" / "U3_player_roles.joblib")
    roles = S.assign_roles(pm_all, u3)
    prof = S.player_profile(usage, roles)
    subs = S.substitutions(ev, pd.read_parquet(SILVER / "lineup_positions.parquet"), prof)
    first = subs.sort_values("t").drop_duplicates("match_id").set_index("match_id")
    p["primer_cambio_min"] = p.match_id.map(first.minute)
    p["primer_cambio_descanso"] = p.match_id.map((first.period == 2) & (first.minute == 45))
    cambios = (subs.assign(tactico=subs.motivo != "Injury")
               .groupby(["match_id", "estado", "perfil", "tactico"]).size().rename("cambios").reset_index())
    # minutos por partido × marcador desde el segundo tiempo (para tasas de cambio por 90')
    d2 = ev[ev.period >= 2].sort_values(["match_id", "period", "index"])
    dt = d2.groupby(["match_id", "period"]).t.diff().shift(-1).clip(lower=0)
    dt = dt.where(d2.groupby(["match_id", "period"]).t.shift(-1).notna(), 0).fillna(0)
    min_estado = (dt.groupby([d2.match_id, d2.game_state3]).sum() / 60).rename("minutos").reset_index().rename(
        columns={"game_state3": "estado"})

    # --- jugadores por técnico × torneo (no por partido): uso, valor y rol habitual
    pm_all = pm_all.assign(o=pm_all.obv.clip(lower=0))
    rol = roles.groupby(["coach", "torneo", "player_short"]).rol.agg(lambda s: s.mode().iat[0])
    g = pm_all.groupby(["coach", "torneo", "player_short"])
    jug = pd.DataFrame({"partidos": g.size(), "titularidades": g.starter.sum(), "minutos": g.minutes.sum(),
                        "obv_pos": g.o.sum(), "obv": g.obv.sum(),
                        "linea": g.position_group.agg(lambda s: s.mode().iat[0] if s.notna().any() else None)}
                       ).join(rol).reset_index().rename(columns={"player_short": "jugador"})
    mins_torneo = pm_all.groupby("match_id").minutes.max().groupby(
        pm_all.drop_duplicates("match_id").set_index("match_id")[["coach", "torneo"]].apply(tuple, axis=1)).sum()
    jug["minutos_posibles"] = [mins_torneo.get((c, t), np.nan) for c, t in zip(jug.coach, jug.torneo)]
    n_ct = p.groupby(["coach", "torneo"]).size()
    jug["partidos_equipo"] = [int(n_ct.get((c, t), 0)) for c, t in zip(jug.coach, jug.torneo)]

    # --- ADN: referencia de la liga (percentiles) y perfiles de todos los técnicos de la liga (ventana)
    ref = C.coach_profiles(ma).reset_index()
    liga = C.coach_profiles(ma, period=None).reset_index()

    # --- catálogo de indicadores (etiqueta, bloque, definición, dirección)
    cat = pd.read_parquet(GOLD / "analysis" / "catalog.parquet").reindex(ind).reset_index()

    out = {"partidos": p, "zonas": zonas, "balon_parado": bp, "tramos": tramos, "cambios": cambios,
           "cambios_minutos": min_estado, "jugadores": jug, "adn_ref": ref, "adn_liga": liga, "catalogo": cat,
           "ejes": pd.DataFrame({"eje": C.AXES})}
    return {k: _guard(v, k) for k, v in out.items()}


def save(cube: dict[str, pd.DataFrame], path: Path = CUBE) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    for k, v in cube.items():
        v.to_parquet(path / f"{k}.parquet", index=False)
    return path


def load(path: Path = CUBE) -> dict[str, pd.DataFrame]:
    return {f.stem: pd.read_parquet(f) for f in sorted(Path(path).glob("*.parquet"))}


# ------------------------------------------------------------------ consultas (solo pandas: la app las usa)
def select(p: pd.DataFrame, coach=None, desde=None, hasta=None, torneos=None, match_ids=None, localia=None,
           rival=None, muestras=None) -> pd.DataFrame:
    """Partidos del periodo y contexto elegidos. Cada argumento None = sin filtro; listas o valores sueltos."""
    m = pd.Series(True, index=p.index)
    as_list = lambda v: [v] if isinstance(v, (str, int, np.integer)) else list(v)  # noqa: E731
    if coach is not None:
        m &= p.coach.isin(as_list(coach))
    if torneos is not None:
        m &= p.torneo.isin(as_list(torneos))
    if desde is not None:
        m &= p.match_date >= pd.Timestamp(desde)
    if hasta is not None:
        m &= p.match_date <= pd.Timestamp(hasta)
    if match_ids is not None:
        m &= p.match_id.isin(as_list(match_ids))
    if localia is not None:
        m &= p.localia.isin(as_list(localia))
    if rival is not None:
        m &= p.rival_nivel.isin(as_list(rival))
    if muestras is not None:
        m &= p.muestra.isin(as_list(muestras))
    return p[m].sort_values("match_date")


def nivel_muestra(n: int) -> dict:
    """Qué se puede afirmar con n partidos (regla del producto: el estilo por partido es identidad + ruido)."""
    if n == 0:
        return {"nivel": "vacio", "rankings": False, "aviso": "No hay partidos con esos filtros."}
    if n == 1:
        return {"nivel": "partido", "rankings": False,
                "aviso": "Un solo partido: se compara con el ADN del técnico; no define un estilo."}
    if n < MIN_TORNEO:
        return {"nivel": "pocos", "rankings": False,
                "aviso": f"Muestra chica ({n} partidos): tendencias, no identidad. Sin percentiles de liga."}
    if n < MIN_ERA:
        return {"nivel": "torneo", "rankings": True,
                "aviso": f"{n} partidos: identidad del periodo; percentiles aproximados."}
    return {"nivel": "era", "rankings": True, "aviso": f"{n} partidos: muestra suficiente para cifras titulares."}


def resumen(sel: pd.DataFrame) -> dict:
    """Ficha del periodo: partidos, récord, puntos por partido, goles y xG por partido, muestras presentes."""
    n = len(sel)
    if n == 0:
        return {"partidos": 0}
    r = sel.result.value_counts()
    return {"partidos": n, "ganados": int(r.get("W", 0)), "empatados": int(r.get("D", 0)),
            "perdidos": int(r.get("L", 0)), "puntos_por_partido": sel.puntos.mean(),
            "goles_favor": sel.goals_for.mean(), "goles_contra": sel.goals_against.mean(),
            "xg_favor": sel.xg_favor.mean(), "xg_contra": sel.xg_contra.mean(),
            "muestras": sorted(sel.muestra.dropna().unique()), "tecnicos": sorted(sel.coach.unique()),
            "desde": sel.match_date.min(), "hasta": sel.match_date.max()}


def indicadores(sel: pd.DataFrame, cols, base: pd.DataFrame | None = None) -> pd.DataFrame:
    """Media por partido de cada indicador en la selección y, si hay `base` (p. ej. el América típico de la
    ventana), su media, la diferencia y en qué percentil de los partidos de la base cae la media del periodo."""
    cols = [c for c in cols if c in sel.columns]
    out = pd.DataFrame({"valor": sel[cols].mean(), "n": sel[cols].notna().sum()})
    if base is not None and len(base):
        out["base"] = base[cols].mean()
        out["diferencia"] = out.valor - out.base
        out["pct_partidos_base"] = [(base[c].dropna() < v).mean() * 100 if pd.notna(v) else np.nan
                                    for c, v in zip(cols, out.valor)]
    return out


def adn_percentil(sel: pd.DataFrame, ref: pd.DataFrame, ejes) -> pd.Series:
    """ADN del periodo: media de cada eje (ajustado por rival y localía, contra la liga del torneo) en percentil
    frente a los técnicos de la liga en la ventana (≥ 15 partidos), igual que coach_profile.to_percentile."""
    out = {}
    for e in ejes:
        v = sel[f"adn__{e}"].mean()
        r = ref[e].dropna().values
        out[e] = (r < v).mean() * 100 + (r == v).mean() * 50 if pd.notna(v) else np.nan
    return pd.Series(out)


def rejilla(zonas: pd.DataFrame, ids, capa: str, valor: str = "n", por_partido: bool = True) -> np.ndarray:
    """Matriz NY × NX (fila = franja de y, columna = franja de x) de la capa en los partidos `ids`; por partido."""
    z = zonas[(zonas.capa == capa) & zonas.match_id.isin(list(ids))]
    m = np.zeros((NY, NX))
    if len(z):
        t = z.groupby(["cy", "cx"])[valor].sum()
        for (cy, cx), v in t.items():
            m[int(cy), int(cx)] = v
    n = len(set(ids))
    return m / n if por_partido and n else m


def balon_parado(bp: pd.DataFrame, ids, por: list[str]) -> pd.DataFrame:
    """Jugadas, % con tiro, xG y xG por jugada a balón parado de los partidos `ids`, agrupado por `por`
    (p. ej. ['lado', 'kind'] o ['lado', 'kind', 'target_zone']); por partido."""
    d = bp[bp.match_id.isin(list(ids))]
    n = max(len(set(ids)), 1)
    g = d.groupby(por).agg(jugadas=("jugadas", "sum"), con_tiro=("con_tiro", "sum"), xg=("xg", "sum"))
    g["por_partido"] = g.jugadas / n
    g["pct_tiro"] = g.con_tiro / g.jugadas * 100
    g["xg_por_jugada"] = g.xg / g.jugadas
    g["xg_por_partido"] = g.xg / n
    return g.reset_index()


def efecto_marcador(tramos: pd.DataFrame, ids, y: str, level: float = 0.90,
                    estados=("Pierde por 2+", "Pierde por 1", "Empate", "Gana por 1", "Gana por 2+")) -> pd.DataFrame:
    """Efecto del marcador en `y` en los partidos `ids`: el MISMO modelo que story.game_state_effect (regresión
    ponderada por minutos, y ~ estado [base: empate] + tramo de 15' + efecto fijo del partido; IC por errores
    agrupados por partido). Describe, no predice. Con menos de MIN_TORNEO partidos devuelve vacío."""
    import statsmodels.formula.api as smf
    d = tramos[tramos.match_id.isin(list(ids)) & tramos.game_state.isin(estados)].dropna(subset=[y])
    cols = ["estado", "efecto", "lo", "hi", "minutos"]
    if d.match_id.nunique() < MIN_TORNEO or d.game_state.nunique() < 2:
        return pd.DataFrame(columns=cols)
    f = f"{y} ~ C(game_state, Treatment('Empate')) + C(minute_bin) + C(match_id)"
    fit = smf.wls(f, data=d, weights=d.duration_min).fit(cov_type="cluster", cov_kwds={"groups": d.match_id})
    ci = fit.conf_int(1 - level)
    mins = d.groupby("game_state").duration_min.sum()
    rows = []
    for st in estados:
        t = f"C(game_state, Treatment('Empate'))[T.{st}]"
        rows.append({"estado": st, "efecto": fit.params.get(t, 0.0 if st == "Empate" else np.nan),
                     "lo": ci.loc[t, 0] if t in ci.index else np.nan, "hi": ci.loc[t, 1] if t in ci.index else np.nan,
                     "minutos": mins.get(st, 0.0)})
    return pd.DataFrame(rows, columns=cols)


def jugadores_periodo(jug: pd.DataFrame, sel: pd.DataFrame) -> pd.DataFrame:
    """Uso y valor de los jugadores en los torneos × técnicos que toca la selección (granularidad: torneo)."""
    keys = set(zip(sel.coach, sel.torneo))
    d = jug[[k in keys for k in zip(jug.coach, jug.torneo)]]
    g = d.groupby("jugador")
    out = pd.DataFrame({"partidos": g.partidos.sum(), "titularidades": g.titularidades.sum(), "minutos": g.minutos.sum(),
                        "minutos_posibles": d.drop_duplicates(["coach", "torneo"]).minutos_posibles.sum(),
                        "obv_pos": g.obv_pos.sum(),
                        "linea": g.linea.agg(lambda s: s.mode().iat[0] if s.notna().any() else None),
                        "rol": g.rol.agg(lambda s: s.mode().iat[0] if s.notna().any() else None)})
    out["pct_minutos"] = out.minutos / out.minutos_posibles * 100
    out["pct_obv_pos"] = out.obv_pos / out.obv_pos.sum() * 100
    out["obv_pos_p90"] = out.obv_pos / out.minutos * 90
    return out.sort_values("minutos", ascending=False).reset_index()


if __name__ == "__main__":
    c = build()
    print(save(c))
    for k, v in c.items():
        print(f"{k:>16}: {v.shape}")

"""MARCO ANALÍTICO (reto 5.6) — fuente única de definiciones.

Todo lo que se mide en el proyecto (tablas Gold, métricas, modelos, gráficas y fichas) se construye con
estas funciones y con los umbrales de ASSUMPTIONS. Ningún notebook redefine estos objetos.

Convenciones StatsBomb: cancha 120 x 80; cada equipo ataca de izquierda a derecha en SUS eventos
(x = 0 portería propia, x = 120 portería rival).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TEAM = "América"

# ---------------------------------------------------------------- supuestos explícitos
ASSUMPTIONS = {
    "pitch": (120, 80),
    "third_limits": (40, 80),              # tercio propio < 40 ≤ medio < 80 ≤ último
    "lane_limits": (80 / 3, 160 / 3),      # carril izquierdo / central / derecho (y)
    "box": {"x_min": 102, "y_min": 18, "y_max": 62},
    "danger_zone": {"x_min": 90, "y_min": 18, "y_max": 62},   # zona de peligro: frente al área o dentro
    "offensive_sequence_min_passes": 3,    # mediana de pases por posesión (EDA)
    "build_up_start_x_max": 40,            # construcción: posesión que inicia en tercio propio
    "progression_from_x_max": 60,          # progresión: cruza de x<60 a x>=80
    "transition_window_s": 15,             # transición ofensiva: recuperación → x>=80 o tiro en ≤ 15 s
    "counterpress_window_s": 5,            # transición defensiva: 5 s tras pérdida
    "press_high_x": 60, "press_mid_x": 40, # altura de presión: alta ≥ 60, media 40–60, baja < 40
    "ppda_def_zone_x": 48,                 # PPDA: acciones defensivas propias con x ≥ 48 (60% más alto)
    "ppda_opp_pass_x_max": 72,             # ... frente a pases rivales con x ≤ 72 (su 60% propio)
    "progressive_min_gain": 0.25,          # pase progresivo: reduce ≥ 25% la distancia a portería
    "progressive_end_x_min": 48,
    "set_piece_throw_in_x_min": 80,        # saque de banda "en zona de peligro"
    "minute_bins": [0, 15, 30, 45, 60, 75, 90, 200],
    "minute_labels": ["0-15", "15-30", "30-45+", "45-60", "60-75", "75-90", "90+"],
    "player_min_minutes": 30,              # umbral para métricas p90 de jugador
    "player_reference_window": 10,         # partidos previos para la referencia de un jugador
    "rival_strength_window": 17,           # partidos de liga previos para la fuerza del rival
    "sub_window_min": 15,                  # impacto de sustitución: 15' antes vs 15' después
}
A = ASSUMPTIONS

DEF_ACTIONS = {"Pressure", "Duel", "Interception", "Ball Recovery", "Foul Committed", "Block", "Clearance", "50/50"}
# PPDA: entradas (Duel sin "Aerial Lost"), intercepciones y faltas; vs. pases rivales de juego abierto.
# Validado contra el PPDA de StatsBomb: rho de Spearman = 0.96 con x>=48 (se probaron 4 conjuntos x 4 zonas).
PPDA_ACTIONS = {"Duel", "Interception", "Foul Committed"}
REGAIN_TYPES = {"Ball Recovery", "Interception", "Duel", "Block", "50/50"}
SET_PIECE_PATTERNS = {"From Corner": "Córner", "From Free Kick": "Tiro libre", "From Throw In": "Saque de banda"}

POSITION_GROUP = {
    "Goalkeeper": "Portero",
    "Right Back": "Defensa", "Right Center Back": "Defensa", "Center Back": "Defensa", "Left Center Back": "Defensa",
    "Left Back": "Defensa", "Right Wing Back": "Carrilero", "Left Wing Back": "Carrilero",
    "Right Defensive Midfield": "Medio defensivo", "Center Defensive Midfield": "Medio defensivo",
    "Left Defensive Midfield": "Medio defensivo",
    "Right Center Midfield": "Medio", "Center Midfield": "Medio", "Left Center Midfield": "Medio",
    "Right Midfield": "Banda", "Left Midfield": "Banda", "Right Wing": "Banda", "Left Wing": "Banda",
    "Right Attacking Midfield": "Medio ofensivo", "Center Attacking Midfield": "Medio ofensivo",
    "Left Attacking Midfield": "Medio ofensivo",
    "Right Center Forward": "Delantero", "Center Forward": "Delantero", "Left Center Forward": "Delantero",
    "Secondary Striker": "Delantero",
}


# ---------------------------------------------------------------- zonas
def third(x):
    lo, hi = A["third_limits"]
    return np.select([x < lo, x < hi], ["Propio", "Medio"], "Último")


def lane(y):
    lo, hi = A["lane_limits"]
    return np.select([y < lo, y < hi], ["Izquierdo", "Central"], "Derecho")


def in_box(x, y):
    b = A["box"]
    return (x >= b["x_min"]) & (y >= b["y_min"]) & (y <= b["y_max"])


def in_danger_zone(x, y):
    d = A["danger_zone"]
    return (x >= d["x_min"]) & (y >= d["y_min"]) & (y <= d["y_max"])


def press_height(x):
    return np.select([x >= A["press_high_x"], x >= A["press_mid_x"]], ["Alta", "Media"], "Baja")


def set_piece_target_zone(end_x, end_y, length):
    """Zona de destino de un envío a balón parado (córner, tiro libre, saque de banda)."""
    central = (end_y >= 30) & (end_y <= 50)
    return np.select(
        [length < 15, (end_x >= 114) & central, (end_x >= 102) & central, in_box(end_x, end_y)],
        ["Corto", "Área chica", "Zona de penal", "Área (costados)"], "Fuera del área")


def minute_bin(minute):
    return pd.cut(minute, A["minute_bins"], labels=A["minute_labels"], right=False)


# ---------------------------------------------------------------- tiempo y marcador
def add_clock(ev: pd.DataFrame) -> pd.DataFrame:
    """t = segundos de juego acumulados (minute*60 + second)."""
    ev = ev.sort_values(["match_id", "index"]).copy()
    ev["t"] = ev.minute * 60 + ev.second
    return ev


def add_game_state(ev: pd.DataFrame, team: str = TEAM) -> pd.DataFrame:
    """Diferencia de goles de `team` ANTES de cada evento, estado (5 niveles) y tramo de minuto.
    Goles = tiros convertidos + autogoles a favor; la tanda de penales (period 5) no cuenta."""
    ev = add_clock(ev)
    goal = (((ev.type == "Shot") & (ev.shot_outcome == "Goal")) | (ev.type == "Own Goal For")) & (ev.period < 5)
    gf = (goal & (ev.team == team)).groupby(ev.match_id).cumsum() - (goal & (ev.team == team))
    ga = (goal & (ev.team != team)).groupby(ev.match_id).cumsum() - (goal & (ev.team != team))
    ev["score_diff"] = (gf - ga).astype(int)
    ev["game_state"] = np.select([ev.score_diff >= 2, ev.score_diff == 1, ev.score_diff == 0, ev.score_diff == -1],
                                 ["Gana por 2+", "Gana por 1", "Empate", "Pierde por 1"], "Pierde por 2+")
    ev["game_state3"] = np.sign(ev.score_diff).map({1: "Ganando", 0: "Empatando", -1: "Perdiendo"})
    ev["minute_bin"] = minute_bin(ev.minute)
    return ev


# ---------------------------------------------------------------- pases
def progressive_pass(ev: pd.DataFrame) -> pd.Series:
    """Pase completo de juego abierto que reduce ≥ 25% la distancia a portería y termina en x ≥ 48."""
    is_pass = ev.type == "Pass"
    d0 = np.hypot(120 - ev.location_x, 40 - ev.location_y)
    d1 = np.hypot(120 - ev.pass_end_location_x, 40 - ev.pass_end_location_y)
    return (is_pass & ev.pass_outcome.isna() & ev.pass_type.isna()
            & (d1 <= (1 - A["progressive_min_gain"]) * d0) & (ev.pass_end_location_x >= A["progressive_end_x_min"]))


def progressive_carry(ev: pd.DataFrame) -> pd.Series:
    is_carry = ev.type == "Carry"
    d0 = np.hypot(120 - ev.location_x, 40 - ev.location_y)
    d1 = np.hypot(120 - ev.carry_end_location_x, 40 - ev.carry_end_location_y)
    return is_carry & (d1 <= (1 - A["progressive_min_gain"]) * d0) & (ev.carry_end_location_x >= A["progressive_end_x_min"])


# ---------------------------------------------------------------- posesiones
def possessions(ev: pd.DataFrame, team: str = TEAM) -> pd.DataFrame:
    """Tabla de posesiones (ambos equipos) con los objetos del marco:
    secuencia ofensiva, construcción, progresión, transición, balón parado, tiro, xG, OBV, estado del marcador."""
    ev = ev if "score_diff" in ev else add_game_state(ev, team)
    ev = ev[ev.period < 5]
    own = ev.team == ev.possession_team
    g = ev.assign(_own=own).groupby(["match_id", "possession"], sort=False)
    first = g.head(1).set_index(["match_id", "possession"])
    # primer evento del equipo en posesión con ubicación
    first_own = (ev[own & ev.location_x.notna()].groupby(["match_id", "possession"]).head(1)
                 .set_index(["match_id", "possession"]))
    t_end = g.t.max()
    ev_own = ev[own]
    go = ev_own.groupby(["match_id", "possession"])
    p = pd.DataFrame({
        "team": first.possession_team,
        "play_pattern": first.play_pattern,
        "period": first.period,
        "minute": first.minute,
        "t_start": g.t.min(),
        "t_end": t_end,
        "score_diff": first.score_diff,
        "game_state": first.game_state,
        "minute_bin": first.minute_bin,
        "start_type": first_own.type,
        "start_pass_type": first_own.get("pass_type"),
        "start_x": first_own.location_x,
        "start_y": first_own.location_y,
        "max_x": go.location_x.max(),
        "n_events": go.size(),
        "n_passes": (ev_own.type == "Pass").groupby([ev_own.match_id, ev_own.possession]).sum(),
        "shot": (ev_own.type == "Shot").groupby([ev_own.match_id, ev_own.possession]).any(),
        "xg": go.shot_statsbomb_xg.sum(),
        "obv": go.obv_total_net.sum(),
        "is_transition_sb": (ev_own.is_transition == True).groupby([ev_own.match_id, ev_own.possession]).mean(),  # noqa: E712
    })
    p["duration_s"] = p.t_end - p.t_start
    for col in ["n_passes", "n_events", "xg", "obv", "max_x"]:
        p[col] = p[col].fillna(0) if col != "max_x" else p[col]
    p["shot"] = p.shot.fillna(False).astype(bool)
    # tiempo a x>=80 o tiro, para transiciones
    reach = ev_own[(ev_own.location_x >= A["third_limits"][1]) | (ev_own.type == "Shot")]
    p["t_reach_f3"] = reach.groupby(["match_id", "possession"]).t.min() - p.t_start
    p["is_set_piece"] = p.play_pattern.isin(["From Corner", "From Free Kick"]) | (
        (p.play_pattern == "From Throw In") & (p.start_x >= A["set_piece_throw_in_x_min"]))
    p["regain"] = p.start_type.isin(REGAIN_TYPES) | p.start_pass_type.isin(["Recovery", "Interception"])
    p["offensive_sequence"] = (p.n_passes >= A["offensive_sequence_min_passes"]) | (p.max_x >= A["third_limits"][1])
    p["build_up"] = (p.start_x < A["build_up_start_x_max"]) & p.play_pattern.isin(["Regular Play", "From Goal Kick", "From Keeper"])
    p["build_up_reached_opp_half"] = p.build_up & (p.max_x >= 60)
    p["progression"] = (p.start_x < A["progression_from_x_max"]) & (p.max_x >= A["third_limits"][1])
    p["transition"] = p.regain & ~p.is_set_piece & (p.t_reach_f3 <= A["transition_window_s"])
    p["is_team"] = p.team == team
    return p.reset_index()


def ppda(ev: pd.DataFrame, team: str = TEAM, actions=PPDA_ACTIONS) -> pd.Series:
    """PPDA por partido: pases rivales en su 60% propio / acciones defensivas propias en nuestro 60% alto."""
    opp_pass = (ev.type == "Pass") & ev.pass_type.isna() & (ev.team != team) & (ev.location_x <= A["ppda_opp_pass_x_max"])
    def_act = (ev.type.isin(actions) & (ev.team == team) & (ev.location_x >= A["ppda_def_zone_x"])
               & ~((ev.type == "Duel") & (ev.duel_type == "Aerial Lost")))
    return opp_pass.groupby(ev.match_id).sum() / def_act.groupby(ev.match_id).sum().replace(0, np.nan)


def field_tilt(ev: pd.DataFrame, team: str = TEAM) -> pd.Series:
    f3 = (ev.type == "Pass") & (ev.location_x >= A["third_limits"][1])
    return (ev.team[f3] == team).groupby(ev.match_id[f3]).mean()


def losses_and_regains(p: pd.DataFrame, team: str = TEAM) -> pd.DataFrame:
    """Transición defensiva por partido: pérdidas en juego y recuperaciones ≤ 5 s tras pérdida."""
    p = p.sort_values(["match_id", "possession"])
    nxt = p.groupby("match_id").shift(-1)
    nxt2 = p.groupby("match_id").shift(-2)
    loss = p.is_team & (nxt.team != team) & (nxt.play_pattern == "Regular Play")
    quick = loss & (nxt2.team == team) & ((nxt2.t_start - p.t_end) <= A["counterpress_window_s"])
    return pd.DataFrame({"losses": loss.groupby(p.match_id).sum(), "quick_regains": quick.groupby(p.match_id).sum()})


def gini(x) -> float:
    """Índice de Gini (0 = reparto perfecto, 1 = todo en un jugador) sobre valores ≥ 0."""
    x = np.sort(np.clip(np.asarray(x, dtype=float), 0, None))
    if x.sum() == 0 or len(x) < 2:
        return np.nan
    n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))

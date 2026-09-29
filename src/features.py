"""VARIABLES POR CRITERIO DEL RETO — derivadas exclusivamente de los objetos de src/framework.py.

`aggregate(ev, poss, keys)` calcula las métricas para CUALQUIER agrupación (partido, segmento del
partido, ventana antes/después de un cambio). Así partido y segmento usan exactamente las mismas
definiciones (coherencia interna, reto 5.6). Todas son tasas o proporciones, no conteos.

FEATURES es el catálogo: nombre -> (criterio del reto, definición, dirección).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import framework as fw

TEAM = fw.TEAM

# ------------------------------------------------------------------ catálogo
FEATURES = {
    # 5.1 Construcción
    "gk_short_goal_kick_pct": ("Construcción", "% de saques de meta cortos (longitud < 32 yd)", "+ = salida corta"),
    "buildup_passes_per_seq": ("Construcción", "Pases medios por posesión de construcción (inicio x<40)", "+ = elaboración"),
    "buildup_success_pct": ("Construcción", "% de construcciones que llegan a campo rival (x≥60)", "+ = mejor salida"),
    "press_resistance_own_third": ("Construcción", "Precisión de pase bajo presión en tercio propio", "+ = resiste presión"),
    # 5.1 Progresión
    "prog_passes_per100": ("Progresión", "Pases progresivos por 100 pases", "+ = más vertical"),
    "prog_carries_per100": ("Progresión", "Conducciones progresivas por 100 pases", "+ = progresa conduciendo"),
    "prog_lane_left_pct": ("Progresión", "% de pases progresivos que terminan en carril izquierdo", "carril"),
    "prog_lane_center_pct": ("Progresión", "% de pases progresivos que terminan en carril central", "carril"),
    "prog_lane_right_pct": ("Progresión", "% de pases progresivos que terminan en carril derecho", "carril"),
    "progression_rate": ("Progresión", "% de posesiones que cruzan de x<60 a x≥80", "+ = progresa más"),
    "pass_x_mean": ("Progresión", "Altura media de los pases propios (x)", "+ = juega más arriba"),
    "long_pass_pct": ("Progresión", "% de pases largos (≥ 32 yd) en juego abierto", "+ = más directo"),
    # 5.1 Generación de ocasiones
    "np_xg_per100poss": ("Ocasiones", "np xG por 100 posesiones propias", "+ = más peligro"),
    "np_xg_per_shot": ("Ocasiones", "np xG por tiro", "+ = mejores ocasiones"),
    "shots_per100poss": ("Ocasiones", "Tiros por 100 posesiones propias", "+ = más volumen"),
    "box_touches_per100poss": ("Ocasiones", "Acciones en el área rival por 100 posesiones", "+ = pisa más el área"),
    "xg_share_open_play": ("Ocasiones", "% del xG propio en posesiones de juego abierto (no transición, no BP)", "origen"),
    "xg_share_transition": ("Ocasiones", "% del xG propio en transiciones", "origen"),
    "xg_share_set_piece": ("Ocasiones", "% del xG propio en balón parado", "origen"),
    "cross_xg_share": ("Ocasiones", "% del xG propio de tiros asistidos con centro", "+ = juego por centros"),
    # 5.1 Presión
    "ppda": ("Presión", "Pases rivales de juego abierto (x≤72) por entrada/intercepción/falta propia (x≥48)", "− = presión más intensa"),
    "def_action_x_mean": ("Presión", "Altura media de las acciones defensivas propias (x)", "+ = defiende más arriba"),
    "high_press_pct": ("Presión", "% de acciones defensivas en campo rival (x≥60)", "+ = presión alta"),
    "high_regains_per100opp": ("Presión", "Recuperaciones que inician posesión en x≥60 por 100 posesiones rivales", "+ = roba arriba"),
    "counterpress_per_loss": ("Presión", "Acciones de contrapresión por pérdida en juego", "+ = reacción tras pérdida"),
    # 5.1 Organización defensiva
    "opp_np_xg_per100poss": ("Organización defensiva", "np xG rival por 100 posesiones rivales", "− = defiende mejor"),
    "opp_shots_per100poss": ("Organización defensiva", "Tiros rivales por 100 posesiones rivales", "− = concede menos"),
    "opp_f3_entry_pct": ("Organización defensiva", "% de posesiones rivales que llegan a x≥80", "− = bloque más sólido"),
    "block_x_mean": ("Organización defensiva", "Altura media de duelos, intercepciones, bloqueos y despejes", "+ = bloque alto"),
    # 5.1 Transiciones
    "transition_poss_pct": ("Transiciones", "% de posesiones propias que son transición ofensiva", "+ = juego de transición"),
    "transition_xg_per100poss": ("Transiciones", "xG en transición por 100 posesiones propias", "+ = castiga al contragolpe"),
    "opp_transition_xg_per100poss": ("Transiciones", "xG rival en transición por 100 posesiones rivales", "− = controla transición defensiva"),
    "quick_regain_pct": ("Transiciones", "% de pérdidas recuperadas en ≤ 5 s", "+ = contrapresión efectiva"),
    # Dominio (síntesis, 5.5)
    "possession_time_pct": ("Dominio", "% del tiempo de posesión (duración de posesiones)", "+ = más balón"),
    "field_tilt": ("Dominio", "Pases propios en último tercio / pases de ambos en su último tercio", "+ = domina territorio"),
    "obv_net": ("Dominio", "OBV propio − OBV rival", "+ = domina en valor"),
    "np_xg_diff": ("Dominio", "np xG propio − np xG rival", "+ = domina en ocasiones"),
    # 5.4 Balón parado
    "sp_xg": ("Balón parado", "xG propio en balón parado", "+ = peligro a balón parado"),
    "opp_sp_xg": ("Balón parado", "xG rival en balón parado", "− = defiende bien el BP"),
    "corner_shot_pct": ("Balón parado", "% de córners propios que terminan en tiro", "+ = córners efectivos"),
    "opp_corner_shot_pct": ("Balón parado", "% de córners rivales que terminan en tiro", "− = defiende bien córners"),
}
PLAYER_FEATURES = {
    # 5.3 Uso de jugadores / distribución del juego (solo a nivel partido)
    "gini_obv": ("Uso de jugadores", "Gini del OBV (≥0) entre jugadores propios", "+ = juego concentrado"),
    "gini_touches": ("Uso de jugadores", "Gini de toques entre jugadores de campo", "+ = balón concentrado"),
    "gini_prog": ("Uso de jugadores", "Gini de acciones progresivas", "+ = progresión concentrada"),
    "top1_obv_share": ("Uso de jugadores", "% del OBV positivo del mejor jugador", "+ = depende de uno"),
    "top3_obv_share": ("Uso de jugadores", "% del OBV positivo de los 3 mejores", "+ = depende de pocos"),
    "obv_share_def": ("Uso de jugadores", "% del OBV positivo generado por defensas y carrileros", "línea"),
    "obv_share_mid": ("Uso de jugadores", "% del OBV positivo generado por medios", "línea"),
    "obv_share_wide": ("Uso de jugadores", "% del OBV positivo generado por bandas", "línea"),
    "obv_share_fwd": ("Uso de jugadores", "% del OBV positivo generado por delanteros", "línea"),
    "boost_pct": ("Uso de jugadores", "% de jugadores (≥30') por encima de su OBV p90 de referencia previa", "+ = el sistema los potencia"),
    "boost_mean": ("Uso de jugadores", "Media del OBV p90 − referencia previa, jugadores ≥30'", "+ = el sistema los potencia"),
    "xi_rotation": ("Uso de jugadores", "Titulares distintos respecto al partido anterior", "+ = rota más"),
    "tactical_shifts": ("Uso de jugadores", "Cambios de sistema en el partido (Tactical Shift)", "+ = ajusta en vivo"),
    "first_sub_minute": ("Uso de jugadores", "Minuto del primer cambio", "− = interviene antes"),
}
# etiquetas cortas para tablas, gráficas y crónica de la ficha (la definición completa sigue en FEATURES)
LABELS = {
    "gk_short_goal_kick_pct": "Saques de meta cortos (%)", "buildup_passes_per_seq": "Pases por construcción",
    "buildup_success_pct": "Construcciones que llegan a campo rival (%)",
    "press_resistance_own_third": "Precisión bajo presión en tercio propio (%)",
    "prog_passes_per100": "Pases progresivos /100 pases", "prog_carries_per100": "Conducciones progresivas /100 pases",
    "prog_lane_left_pct": "Progresión por izquierda (%)", "prog_lane_center_pct": "Progresión por el centro (%)",
    "prog_lane_right_pct": "Progresión por derecha (%)", "progression_rate": "Posesiones que progresan a último tercio (%)",
    "pass_x_mean": "Altura media de pase (x)", "long_pass_pct": "Pases largos (%)",
    "np_xg_per100poss": "np xG /100 posesiones", "np_xg_per_shot": "np xG por tiro",
    "shots_per100poss": "Tiros /100 posesiones", "box_touches_per100poss": "Acciones en área rival /100 posesiones",
    "xg_share_open_play": "xG de juego elaborado (%)", "xg_share_transition": "xG en transición (%)",
    "xg_share_set_piece": "xG a balón parado (%)", "cross_xg_share": "xG tras centro (%)",
    "ppda": "PPDA", "def_action_x_mean": "Altura de acciones defensivas (x)",
    "high_press_pct": "Acciones defensivas en campo rival (%)", "high_regains_per100opp": "Recuperaciones altas /100 pos. rivales",
    "counterpress_per_loss": "Contrapresión por pérdida", "opp_np_xg_per100poss": "np xG rival /100 pos. rivales",
    "opp_shots_per100poss": "Tiros rivales /100 pos. rivales", "opp_f3_entry_pct": "Posesiones rivales que llegan a último tercio (%)",
    "block_x_mean": "Altura del bloque (x)", "transition_poss_pct": "Posesiones en transición (%)",
    "transition_xg_per100poss": "xG en transición /100 posesiones", "opp_transition_xg_per100poss": "xG rival en transición /100 pos.",
    "quick_regain_pct": "Pérdidas recuperadas en ≤5 s (%)", "possession_time_pct": "Posesión (% del tiempo)",
    "field_tilt": "Field tilt (%)", "obv_net": "OBV neto", "np_xg_diff": "Diferencial de np xG",
    "sp_xg": "xG a balón parado", "opp_sp_xg": "xG rival a balón parado", "corner_shot_pct": "Córners con tiro (%)",
    "opp_corner_shot_pct": "Córners rivales con tiro (%)",
    "gini_obv": "Gini del OBV", "gini_touches": "Gini de toques", "gini_prog": "Gini de progresión",
    "top1_obv_share": "OBV del mejor jugador (%)", "top3_obv_share": "OBV de los 3 mejores (%)",
    "obv_share_def": "OBV de defensas y carrileros (%)", "obv_share_mid": "OBV de medios (%)",
    "obv_share_wide": "OBV de bandas (%)", "obv_share_fwd": "OBV de delanteros (%)",
    "boost_pct": "Jugadores sobre su referencia (%)", "boost_mean": "OBV p90 vs referencia (media)",
    "xi_rotation": "Cambios en el XI", "tactical_shifts": "Cambios de sistema", "first_sub_minute": "Minuto del primer cambio",
}


def label(var: str) -> str:
    return LABELS.get(var, var)


SEGMENT_FEATURES = ["possession_time_pct", "field_tilt", "pass_x_mean", "def_action_x_mean", "high_press_pct", "ppda",
                    "prog_passes_per100", "np_xg_per100poss", "opp_np_xg_per100poss", "obv_net", "np_xg_diff",
                    "long_pass_pct", "counterpress_per_loss"]


def _ratio(num, den, scale=1.0):
    return (num / den.replace(0, np.nan)) * scale


def event_flags(ev: pd.DataFrame, team: str = TEAM) -> pd.DataFrame:
    """Marca en cada evento los objetos del marco que usan las métricas (una sola pasada)."""
    e = ev.copy()
    e["am"] = e.team == team
    e["is_pass"] = e.type == "Pass"
    e["open_pass"] = e.is_pass & e.pass_type.isna()
    e["complete"] = e.is_pass & e.pass_outcome.isna()
    e["prog_pass"] = fw.progressive_pass(e)
    e["prog_carry"] = fw.progressive_carry(e)
    e["prog_lane"] = np.where(e.prog_pass, fw.lane(e.pass_end_location_y.fillna(40)), None)
    e["long_pass"] = e.open_pass & (e.pass_length >= 32)
    e["goal_kick"] = e.is_pass & (e.pass_type == "Goal Kick")
    e["gk_short"] = e.goal_kick & (e.pass_length < 32)
    e["pressed_own_third"] = e.is_pass & (e.under_pressure == True) & (e.location_x < fw.A["third_limits"][0])  # noqa: E712
    e["f3_pass"] = e.is_pass & (e.location_x >= fw.A["third_limits"][1])
    e["def_action"] = e.type.isin(fw.DEF_ACTIONS)
    e["block_action"] = e.type.isin({"Duel", "Interception", "Block", "Clearance"})
    e["ppda_action"] = (e.type.isin(fw.PPDA_ACTIONS) & (e.location_x >= fw.A["ppda_def_zone_x"])
                        & ~((e.type == "Duel") & (e.duel_type == "Aerial Lost")))
    e["ppda_opp_pass"] = e.open_pass & (e.location_x <= fw.A["ppda_opp_pass_x_max"])
    e["box_action"] = e.type.isin({"Pass", "Carry", "Ball Receipt*", "Shot", "Dribble"}) & fw.in_box(e.location_x, e.location_y)
    e["np_shot"] = (e.type == "Shot") & (e.shot_type != "Penalty")
    e["np_xg"] = np.where(e.np_shot, e.shot_statsbomb_xg, 0.0)
    e["cp_action"] = e.counterpress == True  # noqa: E712
    # tiros asistidos con centro
    cross_ids = set(e.loc[e.is_pass & (e.pass_cross == True), "id"])  # noqa: E712
    e["cross_xg"] = np.where(e.np_shot & e.shot_key_pass_id.isin(cross_ids), e.shot_statsbomb_xg, 0.0)
    return e


def aggregate(ev: pd.DataFrame, poss: pd.DataFrame, keys: list[str], team: str = TEAM) -> pd.DataFrame:
    """Métricas de FEATURES por grupo `keys` (p. ej. ['match_id'] o ['match_id','minute_bin','game_state3']).
    `ev` debe venir de event_flags(); `poss` de framework.possessions() con las mismas columnas de llave."""
    e = ev
    am, op = e[e.am], e[~e.am]
    ga, go_ = am.groupby(keys, observed=True), op.groupby(keys, observed=True)
    pa, po = poss[poss.is_team], poss[~poss.is_team]
    gpa, gpo = pa.groupby(keys, observed=True), po.groupby(keys, observed=True)
    n_pa, n_po = gpa.size(), gpo.size()
    passes_am = ga.is_pass.sum()
    out = pd.DataFrame(index=e.groupby(keys, observed=True).size().index)

    # construcción
    out["gk_short_goal_kick_pct"] = _ratio(ga.gk_short.sum(), ga.goal_kick.sum(), 100)
    bu = pa[pa.build_up].groupby(keys, observed=True)
    out["buildup_passes_per_seq"] = bu.n_passes.mean()
    out["buildup_success_pct"] = bu.build_up_reached_opp_half.mean() * 100
    pr = am[am.pressed_own_third].groupby(keys, observed=True)
    out["press_resistance_own_third"] = pr.complete.mean() * 100
    # progresión
    out["prog_passes_per100"] = _ratio(ga.prog_pass.sum(), passes_am, 100)
    out["prog_carries_per100"] = _ratio(ga.prog_carry.sum(), passes_am, 100)
    lanes = am[am.prog_pass].groupby(keys + ["prog_lane"], observed=True).size().unstack("prog_lane")
    lanes = lanes.div(lanes.sum(1), axis=0) * 100
    for k, name in [("Izquierdo", "left"), ("Central", "center"), ("Derecho", "right")]:
        out[f"prog_lane_{name}_pct"] = lanes.get(k)
    out["progression_rate"] = gpa.progression.mean() * 100
    out["pass_x_mean"] = am[am.is_pass].groupby(keys, observed=True).location_x.mean()
    out["long_pass_pct"] = _ratio(ga.long_pass.sum(), ga.open_pass.sum(), 100)
    # ocasiones
    out["np_xg_per100poss"] = _ratio(ga.np_xg.sum(), n_pa, 100)
    out["np_xg_per_shot"] = _ratio(ga.np_xg.sum(), ga.np_shot.sum())
    out["shots_per100poss"] = _ratio(ga.np_shot.sum(), n_pa, 100)
    out["box_touches_per100poss"] = _ratio(ga.box_action.sum(), n_pa, 100)
    xg_tot = gpa.xg.sum()
    out["xg_share_transition"] = _ratio(pa[pa.transition].groupby(keys, observed=True).xg.sum(), xg_tot, 100)
    out["xg_share_set_piece"] = _ratio(pa[pa.is_set_piece].groupby(keys, observed=True).xg.sum(), xg_tot, 100)
    has_xg = xg_tot.reindex(out.index) > 0
    for c in ["xg_share_transition", "xg_share_set_piece"]:
        out[c] = out[c].fillna(0).where(has_xg)
    out["xg_share_open_play"] = 100 - out.xg_share_transition - out.xg_share_set_piece
    out["cross_xg_share"] = _ratio(ga.cross_xg.sum(), ga.np_xg.sum(), 100)
    # presión
    out["ppda"] = _ratio(go_.ppda_opp_pass.sum(), ga.ppda_action.sum())
    da = am[am.def_action].groupby(keys, observed=True)
    out["def_action_x_mean"] = da.location_x.mean()
    out["high_press_pct"] = da.location_x.apply(lambda s: (s >= fw.A["press_high_x"]).mean() * 100)
    out["high_regains_per100opp"] = _ratio(pa[pa.regain & (pa.start_x >= fw.A["press_high_x"])].groupby(keys, observed=True).size(), n_po, 100)
    # organización defensiva
    out["opp_np_xg_per100poss"] = _ratio(go_.np_xg.sum(), n_po, 100)
    out["opp_shots_per100poss"] = _ratio(go_.np_shot.sum(), n_po, 100)
    out["opp_f3_entry_pct"] = gpo.max_x.apply(lambda s: (s >= fw.A["third_limits"][1]).mean() * 100)
    out["block_x_mean"] = am[am.block_action].groupby(keys, observed=True).location_x.mean()
    # transiciones
    out["transition_poss_pct"] = gpa.transition.mean() * 100
    out["transition_xg_per100poss"] = _ratio(pa[pa.transition].groupby(keys, observed=True).xg.sum(), n_pa, 100).fillna(0)
    out["opp_transition_xg_per100poss"] = _ratio(po[po.transition].groupby(keys, observed=True).xg.sum(), n_po, 100).fillna(0)
    # dominio
    dur_a, dur_o = gpa.duration_s.sum(), gpo.duration_s.sum()
    out["possession_time_pct"] = _ratio(dur_a, dur_a.add(dur_o, fill_value=0), 100)
    f3a, f3o = ga.f3_pass.sum(), go_.f3_pass.sum()
    out["field_tilt"] = _ratio(f3a, f3a.add(f3o, fill_value=0), 100)
    out["obv_net"] = ga.obv_total_net.sum().sub(go_.obv_total_net.sum(), fill_value=0)
    out["np_xg_diff"] = ga.np_xg.sum().sub(go_.np_xg.sum(), fill_value=0)
    # balón parado
    out["sp_xg"] = pa[pa.is_set_piece].groupby(keys, observed=True).xg.sum()
    out["opp_sp_xg"] = po[po.is_set_piece].groupby(keys, observed=True).xg.sum()
    out[["sp_xg", "opp_sp_xg"]] = out[["sp_xg", "opp_sp_xg"]].fillna(0)
    ca, co = pa[pa.play_pattern == "From Corner"], po[po.play_pattern == "From Corner"]
    out["corner_shot_pct"] = ca.groupby(keys, observed=True).shot.mean() * 100
    out["opp_corner_shot_pct"] = co.groupby(keys, observed=True).shot.mean() * 100
    # contrapresión / transición defensiva (pérdidas: posesión propia seguida de posesión rival)
    if keys == ["match_id"]:
        lr = fw.losses_and_regains(poss)
        out["counterpress_per_loss"] = _ratio(ga.cp_action.sum(), lr.losses)
        out["quick_regain_pct"] = _ratio(lr.quick_regains, lr.losses, 100)
    else:
        n_loss = pa.groupby(keys, observed=True).size()  # aprox.: cada posesión propia termina en pérdida
        out["counterpress_per_loss"] = _ratio(ga.cp_action.sum(), n_loss)
    # tamaño del grupo (para ponderar segmentos)
    out["n_poss_team"] = n_pa
    out["n_poss_opp"] = n_po
    out["duration_min"] = dur_a.add(dur_o, fill_value=0) / 60
    return out

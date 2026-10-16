"""Consultas del cubo (src/cube.py) con datos sintéticos: filtros, regla de muestra, ADN, rejillas, balón parado
y la guarda contra columnas crudas."""
import numpy as np
import pandas as pd
import pytest

from src import cube as K


def _partidos():
    return pd.DataFrame({
        "match_id": [1, 2, 3, 4, 5, 6],
        "match_date": pd.to_datetime(["2023-08-01", "2023-08-08", "2024-02-01", "2024-02-08", "2026-01-10", "2026-08-01"]),
        "torneo": ["Ap 2023", "Ap 2023", "Cl 2024", "Cl 2024", "Cl 2026", "Ap 2026"],
        "coach": ["Jardine"] * 5 + ["Almada"],
        "muestra": ["ventana"] * 4 + ["prueba"] * 2,
        "localia": ["Local", "Visita", "Local", "Visita", "Local", "Local"],
        "rival_nivel": ["Débil", "Fuerte", "Medio", "Fuerte", "Débil", "Fuerte"],
        "result": ["W", "L", "D", "W", "W", "L"], "puntos": [3, 0, 1, 3, 3, 0],
        "goals_for": [2, 0, 1, 1, 3, 0], "goals_against": [0, 1, 1, 0, 1, 2],
        "xg_favor": [1.5, 0.5, 1.0, 1.2, 2.0, 0.4], "xg_contra": [0.3, 1.1, 0.8, 0.5, 0.6, 1.4],
        "field_tilt": [70.0, 40.0, 60.0, 55.0, 65.0, 45.0], "adn__Control": [1.0, -1.0, 0.5, 0.5, 2.0, -2.0],
    })


def test_select_combina_filtros():
    p = _partidos()
    assert K.select(p, coach="Jardine", muestras="ventana").match_id.tolist() == [1, 2, 3, 4]
    assert K.select(p, coach="Jardine", rival="Fuerte").match_id.tolist() == [2, 4]
    assert K.select(p, desde="2024-01-01", hasta="2024-12-31").match_id.tolist() == [3, 4]
    assert K.select(p, localia="Local", torneos=["Ap 2023", "Cl 2024"]).match_id.tolist() == [1, 3]
    assert K.select(p, match_ids=6).coach.tolist() == ["Almada"]


def test_nivel_muestra_sigue_la_regla_del_producto():
    assert K.nivel_muestra(0)["nivel"] == "vacio"
    assert K.nivel_muestra(1)["nivel"] == "partido"
    assert K.nivel_muestra(4) == {**K.nivel_muestra(4), "nivel": "pocos", "rankings": False}
    assert K.nivel_muestra(20)["nivel"] == "torneo"
    assert K.nivel_muestra(91)["nivel"] == "era"


def test_resumen_e_indicadores():
    p = _partidos()
    sel = K.select(p, coach="Jardine", muestras="ventana")
    r = K.resumen(sel)
    assert (r["partidos"], r["ganados"], r["empatados"], r["perdidos"]) == (4, 2, 1, 1)
    assert r["puntos_por_partido"] == pytest.approx(7 / 4)
    ind = K.indicadores(sel, ["field_tilt"], base=p)
    assert ind.loc["field_tilt", "valor"] == pytest.approx(56.25)
    assert ind.loc["field_tilt", "diferencia"] == pytest.approx(56.25 - p.field_tilt.mean())


def test_adn_percentil_contra_la_referencia():
    p = _partidos()
    ref = pd.DataFrame({"Control": [-1.0, 0.0, 0.25, 1.0]})
    # media de Jardine en la ventana = 0.25 -> 2 de 4 por debajo + medio empate = 62.5
    assert K.adn_percentil(K.select(p, coach="Jardine", muestras="ventana"), ref, ["Control"])["Control"] == 62.5


def test_rejilla_por_partido():
    z = pd.DataFrame({"match_id": [1, 1, 2], "cx": [11, 11, 5], "cy": [3, 3, 0], "n": [2, 1, 4],
                      "xg": [0.3, 0.1, 0.0], "goles": [1, 0, 0], "capa": ["tiros", "tiros", "recuperaciones"]})
    m = K.rejilla(z, [1, 2], "tiros")
    assert m.shape == (K.NY, K.NX)
    assert m[3, 11] == pytest.approx(1.5)          # 3 tiros en 2 partidos
    assert K.rejilla(z, [1], "tiros", "xg", por_partido=False)[3, 11] == pytest.approx(0.4)


def test_balon_parado_por_partido():
    bp = pd.DataFrame({"match_id": [1, 1, 2], "lado": ["A favor"] * 3, "kind": ["Córner"] * 3,
                       "jugadas": [4, 2, 6], "con_tiro": [1, 1, 2], "xg": [0.1, 0.1, 0.2]})
    t = K.balon_parado(bp, [1, 2], ["lado", "kind"]).iloc[0]
    assert t.por_partido == 6 and t.pct_tiro == pytest.approx(100 / 3) and t.xg_por_jugada == pytest.approx(0.4 / 12)


def test_guarda_rechaza_datos_crudos():
    with pytest.raises(ValueError):
        K._guard(pd.DataFrame({"match_id": [1], "location_x": [50.0]}), "x")
    with pytest.raises(ValueError):
        K._guard(pd.DataFrame({"match_id": [1], "sb_np_xg": [1.0]}), "x")
    K._guard(pd.DataFrame({"match_id": [1], "cx": [3], "n": [2]}), "ok")


def test_celdas_recortan_a_la_cancha():
    cx, cy = K._cells(pd.Series([0.0, 119.9, 120.0, 130.0]), pd.Series([0.0, 79.9, 80.0, -1.0]))
    assert cx.tolist() == [0, 11, 11, 11] and cy.tolist() == [0, 7, 7, 0]
    assert np.all((cx >= 0) & (cx < K.NX))


def test_ronda_y_hasta_donde_llego():
    assert K.stage_of("Apertura - Quarter-finals") == "Cuartos"
    assert K.stage_of("Clausura - Semi-finals") == "Semifinal"
    assert K.stage_of("Play-offs - Semi-Finals") == "Play-in"
    assert K.stage_of("Finals") == "Final" and K.stage_of("Clausura") is None
    dim = pd.DataFrame({
        "torneo": ["A", "A", "A", "B", "B", "B", "C", "D"],
        "competition_stage": ["Apertura", "Finals", "Finals", "Clausura", "Clausura - Final", "Clausura - Final",
                              "Quarter-finals", "Apertura"],
        "goals_for": [1, 1, 3, 2, 0, 0, 1, 2], "goals_against": [0, 1, 0, 0, 0, 2, 2, 0],
        "match_date": pd.to_datetime(["2023-08-01", "2023-12-15", "2023-12-18", "2024-02-01", "2024-05-23",
                                      "2024-05-26", "2024-11-28", "2026-08-01"])})
    r = K.stage_reached(dim)
    assert r["A"] == "Campeón" and r["B"] == "Final perdida" and r["C"] == "Cuartos" and r["D"] == "En curso"


def test_distribucion_de_goles_exacta():
    d = K._goal_dist([0.5, 0.5])
    assert d == pytest.approx([0.25, 0.5, 0.25])
    assert K._goal_dist([]) == pytest.approx([1.0])


def test_rivales_y_valor_de_recuperar():
    p = _partidos().assign(opponent=["X", "Y", "X", "Y", "X", "Z"], xpts=[2.0, 1.0, 1.5, 1.5, 2.5, 0.5],
                           possession_time_pct=50.0, ppda=10.0)
    r = K.rivales(p).set_index("opponent")
    assert r.loc["X", "partidos"] == 3 and r.loc["X", "puntos"] == pytest.approx(7 / 3)
    assert r.loc["X", "diferencia"] == pytest.approx(7 / 3 - 2.0)
    rec = pd.DataFrame({"match_id": [1, 1, 2], "zona": ["Último tercio", "Tercio medio", "Último tercio"],
                        "robos": [2, 10, 2], "con_tiro": [1, 1, 1], "xg": [0.1, 0.1, 0.1]})
    v = K.recuperacion_valor(rec, [1, 2]).set_index("zona")
    assert v.loc["Último tercio", "pct_tiro"] == 50 and v.loc["Tercio medio", "por_partido"] == 5
    assert v.loc["Tercio propio", "robos"] == 0

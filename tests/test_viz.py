"""Piezas visuales compartidas por la app y el reporte (src/viz.py)."""
import numpy as np
import pandas as pd

from src import cube as K
from src import viz as V


def test_pitch_heat_draws_grid_and_pitch():
    m = np.zeros((80 // K.CELL, 120 // K.CELL))
    m[3, 10] = 2.0
    fig = V.pitch_heat(m, "prueba")
    assert fig.data[0].type == "heatmap"
    assert len(fig.layout.shapes) == 7                      # contorno, media cancha, 2 áreas, 2 áreas chicas, círculo
    labels = [v for row in fig.data[0].text for v in row if v]
    assert labels == ["2.0"]                                # solo se rotulan las celdas con valor relevante


def test_pitch_heat_empty_grid_has_no_labels():
    fig = V.pitch_heat(np.zeros((8, 12)), "vacío")
    assert not any(v for row in fig.data[0].text for v in row)


def test_radar_closes_polygon_and_uses_coach_color():
    s = pd.Series([50, 60, 70], index=["A", "B", "C"])
    fig = V.radar({"Jardine · selección": s, "América típico": s}, "t")
    assert len(fig.data) == 2
    assert list(fig.data[0].r) == [50, 60, 70, 50]
    assert fig.data[0].line.color == V.COACH_COLOR["Jardine"]
    assert fig.data[1].line.color == V.MUTED


def test_torneo_short():
    assert V.torneo_short("Apertura 2023") == "Ap 2023"
    assert V.torneo_short("Clausura 2025") == "Cl 2025"

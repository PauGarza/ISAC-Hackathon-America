"""ADN del Entrenador · Club América — las gráficas del reporte, para explorarlas.

Muestra las mismas gráficas que el reporte final (src/final_report.py), en el mismo orden y con el mismo
"Cómo leerla". Un solo control: el técnico. Cambia las gráficas de un solo técnico (canchas, marcador y torneo a
torneo); las demás comparan a los tres técnicos o son del América de Jardine, como en el reporte.
"Lo que muestra" solo aparece cuando la gráfica es la misma que la del reporte, para que el texto siempre sea cierto.
Datos: app/data (cubo por partido y tablas de las gráficas; ver app/export_data.py).

Correr: streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src import cube as K  # noqa: E402
from src import final_report as FR  # noqa: E402

DATA = ROOT / "app" / "data"
SECCIONES = [  # (título, pregunta, gráficas) en el orden del reporte
    ("El ADN del América", "¿Qué es del club y qué es del técnico?", ["g-radar"]),
    ("Cómo juega", "¿Cómo llegan sus goles, de dónde vienen sus ocasiones y dónde roba el balón?", ["g-tipos", "g-mapas"]),
    ("Cómo ajusta", "¿Qué cambia cuando va ganando o perdiendo?", ["g-marcador"]),
    ("El ADN ganador", "¿Qué hizo distinto el América campeón?", ["g-torneos", "g-series"]),
    ("Puntos críticos", "¿Dónde se le escapan los partidos?", ["g-minuto", "g-derrotas", "g-fuertes"]),
    ("Torneo a torneo", "¿Cuántas ocasiones generó en cada torneo?", ["g-epilogo"]),
    ("Índice de Encaje", "¿Qué técnicos de la liga se parecen más al ADN del América?", ["g-encaje"]),
]
CSS = """<style>
.pie { color: #4b5563; font-size: 0.95rem; margin: -0.5rem 0 0.6rem; }
.muestra { font-size: 0.97rem; border-left: 3px solid #1d4e89; background: #f4f6f9; padding: 8px 12px;
           border-radius: 0 6px 6px 0; margin-bottom: 2rem; }
abbr[title] { text-decoration: underline dotted; text-underline-offset: 3px; cursor: help; }
.exp { color: #6f7782; font-size: 0.92em; }
</style>"""

st.set_page_config(page_title="ADN del Entrenador · Club América", page_icon="⚽", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data
def datos() -> tuple[dict, dict]:
    N = FR.base(DATA / "reporte", K.load(DATA))
    return N, FR.lecturas(N)


N, LEC = datos()

st.title("ADN del Entrenador · Club América")
st.caption("Las gráficas de nuestro reporte, para explorarlas. Partidos del América del Apertura 2021 al Clausura 2025 "
           "(y las temporadas recientes en «Torneo a torneo») · Datos: StatsBomb")
coach = st.radio("¿Qué técnico quieres ver?", FR.COACHES[::-1], horizontal=True,
                 help="Cambia las canchas, el marcador y el torneo a torneo. Las demás gráficas comparan a los tres "
                      "técnicos o son del América de Jardine.")
st.caption("Pasa el cursor sobre una gráfica para ver cada cifra, y sobre las siglas subrayadas para ver qué quieren decir.")

for titulo, pregunta, gids in SECCIONES:
    st.header(titulo, divider="gray")
    st.markdown(f"**{pregunta}**")
    for gid in gids:
        fn = FR.FIGURAS[gid]
        fig = fn(N, coach) if gid in FR.POR_TECNICO else fn(N)
        st.plotly_chart(fig, theme=None, config={"displayModeBar": False}, width="stretch")
        s = set()
        st.markdown(f'<p class="pie"><b>Cómo leerla.</b> {FR.e(FR.pie(gid, N, coach), s)}</p>', unsafe_allow_html=True)
        if gid not in FR.POR_TECNICO or coach == "Jardine":
            st.markdown(f'<p class="muestra"><b>Lo que muestra.</b> {FR.e(LEC[gid], s)}</p>', unsafe_allow_html=True)
        else:
            st.markdown("<div style='margin-bottom:2rem'></div>", unsafe_allow_html=True)

# El ADN de André Jardine · Club América

> **Hackathon ISAC 2026 · ITAM Sports Analytics Conference** · reto presentado por Club América:
> *"La historia de un entrenador a través de los datos"*.
>
> Emilio Villalobos García Padilla · Othoniel Reyes Camacho · Paulina Garza Allende

Entre 2023 y 2024 el América de André Jardine ganó tres torneos seguidos, en una liga donde 7 de cada 10 técnicos no completan dos torneos en su equipo. Con los eventos y el 360 de StatsBomb de 175 partidos del América (Apertura 2021 – Clausura 2025) y las estadísticas de toda la Liga MX, contamos cómo juega su equipo, qué conserva del club, cómo ajusta según el partido y qué lo hizo campeón, para que lo entienda alguien que no vio los partidos.

| Entregable | Dónde |
|---|---|
| **Reporte** (HTML interactivo, funciona sin conexión) | [`reports/final/reporte_america.html`](reports/final/reporte_america.html): descárgalo y ábrelo en el navegador |
| **Reporte en PDF** (misma versión, para leer o imprimir) | [`reports/final/reporte_america.pdf`](reports/final/reporte_america.pdf) |
| **App interactiva** (explorador por técnico, torneo o partido) | https://isac-hackathon-america-2rkgqdhmmyqxvkxnogcpci.streamlit.app/ |
| **Video** (menos de 5 min) | Se envió con la entrega |

> La app puede tardar unos segundos en despertar la primera vez que se abre.

---

## En un minuto

1. **El América tiene un ADN que no depende del técnico.** Con Solari, Ortiz y Jardine tuvo más balón, generó más peligro y concedió menos que la liga. Lo que cambia con cada técnico es cómo presiona.
2. **Jardine lo pulió: sale jugando, espera y remata mejor.** Saca en corto el 45 % de sus saques de meta (Ortiz 31 %), presiona menos que la liga y tira mejor: 0.12 xG (goles esperados) por tiro (Ortiz 0.10).
3. **Lee el partido.** Perdiendo por un gol empuja (+8 puntos de dominio territorial); ganando por uno guarda el balón lejos del área (−17).
4. **En liguilla, el campeón juega de copa.** En las 15 series que pasó dejó dar 19 pases al rival antes de presionar; en las 5 que perdió, 10.
5. **Dónde se le escapa.** Del minuto 30 al descanso le generan 1.41 xG por 90 minutos, su tramo más vulnerable. Con tres centrales se repliega sin protegerse más.

Cada hallazgo termina en una **recomendación con un indicador para seguirla** (sección 6 del reporte). También publicamos **las ideas que probamos y no se sostienen** (sección 7).

---

## Cómo revisar este proyecto

| Si tienes… | Mira |
|---|---|
| 10 minutos | El **reporte**: "En un minuto", luego las secciones 1 a 6. |
| 5 minutos más | La **app**: elige técnico y periodo; cada gráfica explica cómo leerla. |
| Interés en el método | Anexo A del reporte (metodología, marco analítico y límites) y [`reports/framework/framework_report.pdf`](reports/framework/framework_report.pdf). |
| Interés en el código | [`src/framework.py`](src/framework.py) (todas las definiciones), [`src/coach_profile.py`](src/coach_profile.py) (ADN del Entrenador e Índice de Encaje) y los notebooks [04](notebooks/04_adn_entrenador.ipynb) a [07](notebooks/07_complementos.ipynb). |

---

## Qué hicimos

**Un solo marco analítico.** Cada objeto del reto (posesión, secuencia ofensiva, construcción, transición, presión, balón parado, bloque defensivo con 360, fuerza del rival…) se define **una sola vez** en [`src/framework.py`](src/framework.py), con sus umbrales en `ASSUMPTIONS`. Todas las cifras, gráficas y comparaciones del reporte y de la app salen de esas mismas definiciones.

**Comparaciones justas.** Un estilo solo se ve comparando, y una comparación injusta engaña. Por eso:
- comparamos con el mismo técnico y el mismo nivel de rival;
- medimos el plan de juego (posesión, presión) con el **partido empatado**, porque con el marcador movido el plan es consecuencia del resultado;
- medimos el efecto del marcador dentro del mismo partido;
- comparamos el ADN con la liga **del mismo torneo**, porque la liga y la forma de registrar los datos cambiaron con los años.

Una diferencia "se sostiene" solo si el azar la explica menos de 1 de cada 10 veces (prueba de permutación), si es de un tamaño relevante y si hay al menos 8 partidos por grupo.

**Dos métricas propias.**
- **ADN del Entrenador**: 8 rasgos de juego (control del balón, verticalidad, llegada al área, presión alta, reacción tras pérdida, peligro generado, solidez defensiva y balón parado). Cada uno se compara con la liga del mismo torneo, se ajusta por rival y localía y se expresa de 0 a 100 frente a los 70 técnicos de la Liga MX con 15 partidos o más. Sirve para cualquier técnico de la liga.
- **Índice de Encaje**: qué tan cerca está un técnico del ADN del club. Sirve para elegir técnico con datos y para revisar, torneo a torneo, si el técnico en turno se aleja de la identidad del club.

Las calculamos solo con la ventana del reto. Después las probamos con partidos de 2025–26 que no se usaron para construirlas: en el 31 % de esos partidos el técnico correcto queda entre los 5 más parecidos de la liga (por azar sería 16 %), y el estilo de Almada aparece en el América sin haberlo visto ahí.

**Ideas de otras disciplinas.**
- **Béisbol (OPS+, ERA+)**: ajustar por estadio y época → ajustamos por torneo, rival y localía.
- **Ensayos clínicos**: comparar contra casos parecidos → mismo técnico, mismo rival, partido empatado.
- **Genética**: comparar perfiles marcador por marcador → el Índice de Encaje.
- **Monte Carlo**: repetimos cada partido con sus ocasiones para saber qué tanto mereció el América sus puntos. Sirve para explicar, no para predecir.

---

## Datos y reglas de uso

- **Fuente:** Hudl StatsBomb, eventos y 360 de la Liga MX, Apertura 2021 – Clausura 2025, proporcionados para el hackathon. Toda cifra del reporte sale de esa ventana; lo de 2025–26 aparece solo en el epílogo.
- **Los datos no se publican.** La carpeta `data/` (descargas y tablas intermedias) y las credenciales están en [`.gitignore`](.gitignore).
- [`app/data/`](app/data/) contiene solo los **resúmenes por partido** que la app necesita para funcionar (indicadores por partido y por tramo, conteos por zona, ADN por técnico). No incluye eventos ni posiciones 360.

---

## Estructura del repo

```
├── reports/
│   ├── final/reporte_america.html     # ★ el reporte entregable
│   ├── final/textos.md                # textos del reporte y guion del video
│   ├── figures/                       # figuras de cada etapa (eda, framework, coach, story)
│   ├── framework/framework_report.pdf # marco analítico: definiciones, supuestos, validaciones
│   ├── eda/eda_report.pdf             # exploración de los datos
│   └── match_reports/                 # ejemplos de ficha automática por partido
├── app/
│   ├── streamlit_app.py               # ★ la app (explorador por técnico y periodo)
│   ├── export_data.py                 # exporta los resúmenes que usa la app
│   └── data/                          # resúmenes por partido (sin eventos ni 360)
├── notebooks/
│   ├── 01_descarga_datos.ipynb        # descarga de StatsBomb
│   ├── 02_exploracion_datos.ipynb     # exploración de los datos
│   ├── 03_formulacion_variables_modelos.ipynb  # marco, variables por criterio del reto y su evaluación
│   ├── 04_adn_entrenador.ipynb        # ADN del Entrenador frente a la liga, Índice de Encaje, prueba con 2025–26
│   ├── 05_historia_jardine.ipynb      # con balón, sin balón, 360, contexto, jugadores, balón parado
│   ├── 06_hipotesis_equipo.ipynb      # cada hipótesis se prueba antes de entrar al reporte
│   └── 07_complementos.ipynb          # tipos de gol, recuperación tras pérdida, defensa del área
├── src/
│   ├── framework.py                   # ★ marco analítico: fuente única de definiciones y supuestos
│   ├── coach_profile.py · coach_viz.py  # ADN del Entrenador e Índice de Encaje
│   ├── story.py · story_viz.py        # la historia de Jardine (cálculos y canchas)
│   ├── hipotesis.py                   # pruebas de las hipótesis (permutación, efectos por grupo)
│   ├── cube.py                        # cubo de agregados por partido (base de la app y del reporte)
│   ├── viz.py                         # gráficas compartidas por la app y el reporte
│   ├── final_report.py + templates/   # construye el reporte HTML
│   ├── features.py · evaluation.py · modeling.py  # variables, validación del marco y modelos
│   └── pipeline/                      # descarga → limpieza con controles de calidad → tablas de análisis
├── tests/                             # pruebas del marco, del ADN, de la historia y de las gráficas (pytest)
└── models/                            # fichas de cada modelo (.json)
```

---

## Cómo reproducirlo

Requiere credenciales de la API de StatsBomb (las del hackathon) y Python 3.12.

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate                     # Windows (en bash: source .venv/Scripts/activate)
pip install -r requirements.txt
copy .env.example .env                     # y llenar SB_USERNAME / SB_PASSWORD

# 1. Datos: descarga, limpieza con controles de calidad y tablas de análisis (re-correrlo no duplica nada)
python -m src.pipeline run --stages bronze,silver,gold

# 2. Análisis: notebooks 03 a 07, en orden
jupyter nbconvert --to notebook --execute --inplace notebooks/0[3-7]_*.ipynb

# 3. Reporte y app
python -m src.cube                         # cubo de agregados por partido
python -m src.final_report                 # → reports/final/reporte_america.html
python -m app.export_data                  # → app/data/
streamlit run app/streamlit_app.py

pytest -q                                  # pruebas
```

La app desplegada solo instala [`app/requirements.txt`](app/requirements.txt).

---

## Uso de inteligencia artificial y trabajo de terceros

- **IA generativa:** usamos Claude, el asistente de inteligencia artificial de Anthropic, a través de Claude Code, para escribir y revisar el código del análisis, del reporte y de la app; para redactar y editar textos, y para preparar el guion y las diapositivas del video. Todas las cifras salen del código que corre sobre los datos de StatsBomb, y revisamos los resultados y los textos antes de incluirlos.
- **Librerías públicas:** `statsbombpy`, pandas, NumPy, scikit-learn, statsmodels, matplotlib, mplsoccer, Plotly y Streamlit (ver [`requirements.txt`](requirements.txt)).
- **Referencias:**
  - Hudl StatsBomb. Datos de eventos y 360 de la Liga MX, Apertura 2021 – Clausura 2025.
  - StatsBomb (2021). [Introducing On-Ball Value (OBV)](https://blogarchive.statsbomb.com/news/introducing-on-ball-value-obv/).
  - StatsBomb. [Set-pieces remain an under-utilised game-changer](https://blogarchive.statsbomb.com/articles/soccer/set-pieces-remain-an-underutilised-gamechanger/).
  - Clijmans, J., Van Roy, M. y Davis, J. (2022). *Looking Beyond the Past: Analyzing the Intrinsic Playing Style of Soccer Teams*. ECML PKDD.
  - Baseball-Reference. [Glosario de estadísticas ajustadas (OPS+, ERA+)](https://www.baseball-reference.com/about/bat_glossary.shtml).

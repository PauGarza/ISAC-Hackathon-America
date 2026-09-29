# ISAC Hackathon 2026 · Club América

> **"La historia de un entrenador a través de los datos"** — ITAM Sports Analytics Conference.
> Reto oficial: https://mr2293.github.io/hackathon_isac/ · Bases: https://www.isac-app.com/competitions/hackathon-america
>
> **Fechas clave**:
> - cierre de convocatoria: 7 oct 2026;
> - **entrega: 9 oct 2026** (reporte HTML + video de máximo 5 min);
> - finalistas: 27 oct;
> - **final: 9 nov 2026** (máximo 10 diapositivas).
>
> Pendientes: [todo.md](todo.md).

## 1. El reto

Con datos de eventos **StatsBomb + StatsBomb 360** de muchos partidos de un mismo equipo bajo un mismo entrenador, construir una **narrativa analítica basada en evidencia** que explique cómo juega el equipo y cuáles son las ideas del entrenador.

**Pregunta central**

> ¿Cuáles son los principios que definen a su equipo en fase ofensiva y defensiva, cómo se manifiestan estos patrones a lo largo del tiempo, y de qué manera el entrenador ajusta su comportamiento en función del contexto del partido?

**Principio fundamental:** alguien que **no vio los partidos** debe poder entender con claridad *cómo juega el equipo* y *cuáles son las ideas del entrenador*.

### Qué hay que cubrir

| Bloque | Qué pide el reto |
|---|---|
| Estilo ofensivo | Construcción, progresión entre fases, generación de ocasiones |
| Estilo defensivo | Presión, organización defensiva, transiciones |
| Consistencia y variabilidad | Identidad clara; cambios según rival, marcador, localía, momento del partido |
| Uso de jugadores | Roles posicionales, cambios de alineación, impacto de sustituciones |
| Balón parado ofensivo | Córners, tiros libres, saques de banda en zona de peligro; movimientos y zonas de remate |
| Balón parado defensivo | Organización/marcaje, zonas vulnerables |
| Evidencia cuantitativa | xG, OBV, pases progresivos, métricas de presión, field tilt… y métricas propias |
| **Marco analítico (obligatorio)** | Definir objetos (posesión, secuencia ofensiva, transición, fase de presión), supuestos explícitos (umbrales, zonas), coherencia interna, alcance y límites |

**Entregable:** narrativa analítica (reporte o crónica) + visualizaciones; opcional modelos/simulaciones, siempre **para explicar**, no para predecir ni apostar. Herramientas libres (Python, R, Tableau, Streamlit, Shiny…).

**Reglas de datos:** uso exclusivo para la competencia. El análisis y los resultados son nuestros; **los datos no se comparten** (por eso `data/` y las credenciales están en `.gitignore`).

## 2. Cómo funciona StatsBomb

StatsBomb (Hudl) etiqueta manualmente **cada acción con balón** de un partido (~3,500 eventos por partido).

```
competición → temporada → partidos → { eventos, alineaciones, 360, stats agregadas }
```

- **Evento**: una acción (`Pass`, `Carry`, `Ball Receipt*`, `Pressure`, `Shot`, `Duel`, `Ball Recovery`, `Interception`, `Clearance`, `Foul Committed`, `Substitution`, `Tactical Shift`…) con `minute/second`, `team`, `player`, `position`, `location` y atributos específicos del tipo (`pass_end_location`, `pass_height`, `shot_statsbomb_xg`, `shot_outcome`…).
- **Cancha**: 120 × 80 (x hacia la portería rival, y de 0 a 80). **Cada equipo siempre ataca de izquierda a derecha** en sus propios eventos: `x > 80` es el último tercio, el área rival es `x ≥ 102, 18 ≤ y ≤ 62`.
- **Posesión**: `possession` (número secuencial) y `possession_team`. Una posesión cambia cuando el otro equipo toma control del balón. `play_pattern` dice cómo empezó: `Regular Play`, `From Corner`, `From Free Kick`, `From Throw In`, `From Goal Kick`, `From Counter`, `From Keeper`, `From Kick Off`.
- **Contexto de presión**: `under_pressure` (el ejecutor estaba presionado) y `counterpress` (presión dentro de los 5 s tras perder el balón).
- **Métricas de valor**:
  - `shot_statsbomb_xg`: probabilidad de gol del tiro.
  - `obv_for_net / obv_against_net / obv_total_net` (**On-Ball Value**): cuánto cambia la probabilidad de marcar/recibir gol por una acción.
  - `is_transition`, `is_controlled_possession`: flags de StatsBomb útiles para separar juego posicional de transiciones.
- **360** (`frames360`): para cada evento, las posiciones de los jugadores **visibles en cámara** (`teammate`, `actor`, `keeper`, `location`) y el polígono `visible_area`. Permite medir líneas rotas, jugadores superados, compactación, altura de la línea defensiva, etc. Ojo: no es tracking completo, solo lo que se ve en la toma.
- **Stats agregadas**: `team_match_stats` (~200 métricas por equipo/partido: PPDA, xG, posesión, pases, presiones…) y `player_match_stats` (~175 por jugador/partido).
- **Alineaciones**: jugadores, posiciones jugadas con minutos de entrada/salida, formaciones.

Acceso: API privada (`https://data.statsbomb.com`, docs en `/api-overview` con las credenciales) vía la librería [`statsbombpy`](https://github.com/statsbomb/statsbombpy) con `creds={"user", "passwd"}`.

## 3. Datos disponibles

Nuestras credenciales dan acceso a **Liga MX** (comp 73, con 360) y **Liga MX Femenil** (comp 1438, sin 360).

| Temporada (season_id) | Entrenador(es) del América | Partidos |
|---|---|---|
| 2021/22 (108) | Santiago Solari · Fernando Ortiz | 27 · 13 |
| 2022/23 (235) | Fernando Ortiz | 42 |
| 2023/24 (281) | **André Jardine** | 46 |
| 2024/25 (317) | **André Jardine** · Diego Cervantes (interino) | 45 · 2 |
| 2025/26 (318) | **André Jardine** | 38 |
| 2026/27 (351) | Jorge Almada (en curso) | 9 jugados + 8 programados |

- **222 partidos jugados**, todos con eventos + 360. Incluye fase regular y liguilla.
- Una "temporada" StatsBomb = **Apertura + Clausura**; para cortar por torneo usar `match_date` (Apertura ≈ jul–dic, Clausura ≈ ene–may).
- Jardine concentra la muestra más grande (~129 partidos, 3 temporadas) → candidato natural para la narrativa; los demás entrenadores sirven como **punto de comparación** ("qué cambió cuando llegó Jardine") y Almada como epílogo/contraste.

## 4. Ruta de solución propuesta

### 4.1 Marco analítico (definirlo primero, todo lo demás lo usa)

Borrador inicial (fase 1). **La versión final y validada vive en [`src/framework.py`](src/framework.py)** (umbrales en `ASSUMPTIONS`) y está documentada en [`reports/framework/framework_report.pdf`](reports/framework/framework_report.pdf):

| Objeto | Definición inicial |
|---|---|
| Posesión | `possession` de StatsBomb con `possession_team == América` |
| Secuencia ofensiva | Posesión del América con ≥ N pases (p. ej. 3) o que alcanza el último tercio |
| Fase de construcción | Posesión que inicia en tercio propio (`x < 40`) desde saque de meta/portero/regular play |
| Transición ofensiva | Posesión que inicia con recuperación/intercepción y llega a tiro o al último tercio en ≤ 10–15 s (o `is_transition`) |
| Transición defensiva / contrapresión | Eventos del América con `counterpress == True` o acciones defensivas ≤ 5 s tras pérdida |
| Fase de presión alta | Acciones defensivas del América (Pressure, Duel, Interception, Ball Recovery, Foul) con `x ≥ 60` (campo rival); PPDA en zona alta |
| Balón parado | Posesiones con `play_pattern` ∈ {From Corner, From Free Kick, From Throw In} (saques de banda solo en último tercio) |
| Contexto | Marcador en el momento (ganando/empatando/perdiendo), localía, minuto (tramos de 15'), rival (nivel por tabla o xG diferencial) |

Supuestos, umbrales y limitaciones se documentan en `reports/` y se mantienen **iguales en todo el análisis** (coherencia interna).

### 4.2 Métricas por bloque

| Bloque | Métricas / análisis |
|---|---|
| Construcción y progresión | % salida corta vs larga desde meta, pases progresivos, conducciones progresivas, **líneas rotas (360)**, mapas de progresión por carril, cadenas de pase típicas |
| Generación de ocasiones | xG a favor/partido, xG por tipo de posesión (posicional, transición, balón parado), zonas de remate, asistencias (centros vs pases filtrados vs cut-backs) |
| Presión | PPDA, altura media de recuperación, % recuperaciones en campo rival, contrapresión exitosa (recuperación ≤ 5 s), presiones por zona |
| Organización defensiva | xG en contra, zonas de tiro rival, altura de la línea defensiva (360), field tilt en contra |
| Dominio | Field tilt (% de toques en último tercio), posesión, OBV neto por fase |
| Consistencia/contexto | Mismas métricas cortadas por marcador, localía, rival, minuto, torneo; variabilidad partido a partido |
| Uso de jugadores | Minutos por jugador, 11 más usado, formaciones, mapa de posiciones medias, impacto de cambios (xG/OBV antes vs después del cambio) |
| Balón parado | Mapas de entrega y remate en córners/TL, xG por jugada, zonas vulnerables en contra |

### 4.3 Narrativa y entregable

1. **Identidad**: 3–4 principios del entrenador, cada uno con 1–2 visualizaciones clave.
2. **Evolución en el tiempo**: cómo cambian esos principios por torneo (y vs. Ortiz/Solari antes, Almada después).
3. **Adaptación al contexto**: qué cambia cuando va ganando/perdiendo, de local/visita, vs. rivales fuertes.
4. **Jugadores**: quién hace funcionar el sistema.
5. **Balón parado** a favor y en contra.
6. (Opcional) Simulación para medir dominio relativo (p. ej. simular partidos desde xG por tiro).

Formato de entrega (bases oficiales): **reporte HTML** con selector de partido, más un **video de máximo 5 min**. Para la final: máximo 10 diapositivas y, opcionalmente, una app en Streamlit.

## 5. Estado del proyecto

| Fase | Qué se hizo | Entregables |
|---|---|---|
| **1 · Entender los datos** | Descarga completa y EDA por columna, calidad, relaciones y contexto; 10 hipótesis | `notebooks/01`, `notebooks/02`, [`reports/eda/eda_report.pdf`](reports/eda/eda_report.pdf) |
| **2 · Del dato al criterio** | Pipeline medallion local, marco analítico validado, 55 variables por partido (incluido el uso de jugadores) evaluadas como criterios → 29 núcleo, 11 tareas ML (T1–T7, U1–U3) con partición temporal y baselines, model cards, ficha HTML automática por partido y monitoreo de drift | `src/pipeline/`, `notebooks/03`, [`reports/framework/framework_report.pdf`](reports/framework/framework_report.pdf), `reports/match_reports/*.html` |
| **2b · ADN del Entrenador** | Benchmark de toda la Liga MX (1,789 partidos, 106 técnicos), perfil de 8 rasgos ajustado por rival y localía, consistencia, contexto, evolución, mapa de técnicos, Índice de Encaje, validación con el cambio a Almada, rotación de técnicos y ROI por escenarios. Hipótesis del EDA reescritas hacia el resultado del hackathon | `src/coach_profile.py`, `src/coach_viz.py`, `src/business.py`, `notebooks/04`, `reports/figures/coach/` |
| 3 · Narrativa y entrega | Reporte HTML interactivo (con selector de partido) en lenguaje de juego, comparación de entrenadores, ROI/activación/escalabilidad, video de 5 min | pendiente, ver [todo.md](todo.md) |

**Partición oficial.** Entrenamiento = ventana oficial del hackathon (Apertura 2021 – Clausura 2025); validación = Apertura 2025; prueba = 2026 (incluye la llegada de Almada). Constantes `OFFICIAL_END` y `VAL_END` en `src/pipeline/config.py`.

**Hallazgos de la fase 2 (versiones base)**
- **ADN del entrenador**: Solari = solidez; Ortiz = presión alta y llegada; Jardine = control del balón y peligro con presión media; Almada (2026) = llegada, balón parado y reacción tras pérdida. El modelo reconoce a Almada en el América sin haberlo visto ahí (posición mediana 2 de 31 técnicos): **el estilo sigue al técnico, no a la plantilla**.
- El estilo *por partido* se comporta como una **identidad estable más ruido**: predecir un partido de 2026 desde el contexto apenas mejora a la media histórica, pero los efectos del contexto son claros (frente a rivales fuertes el equipo cede posesión y territorio; de local sube el field tilt y la presión).
- **El marcador cambia el plan**: perdiendo por un gol, el field tilt sube ~9 puntos; ganando por uno, baja ~13.
- Los principios de proceso que acompañan al diferencial de xG son pisar el área rival, repartir los toques, resistir la presión en la salida y progresar por pase.
- **El juego está repartido y se construye desde atrás**: los 3 mejores generan ~62 % del OBV positivo, y defensas y carrileros ~35 %.
- Balón parado y xG concedido son **demasiado ruidosos por partido** para usarse como criterio. El efecto de las sustituciones no es predecible con esta información.

## 6. Arquitectura de datos (medallion, local)

```
API StatsBomb ─extract─▶ BRONZE ─transform+validar─▶ SILVER ─construir─▶ GOLD ─▶ modelos · scores · fichas HTML
                         JSON crudo inmutable       Parquet tipado,       tablas por caso de uso
                         + manifest (sha256)        validado, por season  (contrato con modelos y ficha)
```

| Capa | Ruta | Contenido | Reglas |
|---|---|---|---|
| Bronze | `data/bronze/statsbomb/` | Respuesta exacta de la API (`.json.gz`) + `_manifest.parquet` | Inmutable, incremental, reintentos ante cortes de red |
| Silver | `data/silver/` | `matches`, `league_matches`, `league_team_match_stats` (toda la liga), `events/season=*/`, `frames360/season=*/`, `lineups`, `lineup_positions`, `player_match_stats`, `team_match_stats` | Compuertas de calidad (`QualityError`): cobertura, ids, coordenadas, xG, marcador reconstruido = oficial |
| Gold | `data/gold/` | `dim_match`, `fct_team_match_league` + `dim_coach` (benchmark de liga), `match_features`, `fct_possession`, `fct_segment`, `fct_set_piece`, `fct_substitution`, `fct_player_match`, `scores/`, `analysis/` | Se reconstruye completo desde Silver con `framework.py` + `features.py`; contexto sin leakage |

Modelos: `models/<nombre>.joblib` (ignorado) + `models/<nombre>.json` (**model card**: tarea, variables, hiperparámetros, fechas, métrica frente al mejor baseline, hash de datos). No hay model registry: para un equipo pequeño en local basta con las model cards más git.

## 7. Estructura del repo

```
├── notebooks/
│   ├── 01_descarga_datos.ipynb            # descarga (fase 1; hoy la reemplaza la etapa bronze del pipeline)
│   ├── 02_exploracion_datos.ipynb         # EDA
│   ├── 03_formulacion_variables_modelos.ipynb  # ciclo de vida ML: problema, marco, variables, leakage, T1–T7, U1–U3, drift, fichas
│   └── 04_adn_entrenador.ipynb            # ADN del entrenador vs la liga, validación del cambio de técnico, valor para el club
├── src/
│   ├── pipeline/                          # python -m src.pipeline run --stages ...
│   │   ├── config.py                      # rutas, temporadas, endpoints, logger (logs/pipeline.log)
│   │   ├── bronze.py · silver.py · gold.py
│   │   ├── quality.py                     # compuertas de calidad
│   │   └── monitoring.py                  # PSI con umbrales calibrados por remuestreo
│   ├── framework.py                       # MARCO ANALÍTICO: fuente única de definiciones y ASSUMPTIONS
│   ├── features.py                        # variables por criterio (FEATURES, PLAYER_FEATURES, aggregate)
│   ├── evaluation.py                      # validación del marco, evaluación de variables, núcleo, sensibilidad, supuestos
│   ├── modeling.py                        # TASKS, partición temporal oficial, baselines, T1–T7, U1–U3, model cards, scoring
│   ├── coach_profile.py                   # ADN del entrenador: rasgos, ajuste por contexto, percentiles, encaje, validación
│   ├── coach_viz.py                       # figuras del ADN (radar, mapa de la liga, contexto, cambio de técnico)
│   ├── business.py                        # rotación de técnicos (dato) y ROI por escenarios (supuestos explícitos)
│   ├── match_report.py + templates/       # ficha HTML automática por partido
│   ├── latex.py                           # exportar tablas y cifras a LaTeX
│   ├── sb_client.py · eda.py · eda_dictionary.py
├── tests/test_framework.py                # definiciones del marco + reglas anti-leakage (pytest)
├── models/                                # model cards (.json versionadas; .joblib ignorados)
├── reports/
│   ├── eda/                               # reporte fase 1 (make_tables.py → eda_report.pdf)
│   ├── framework/                         # reporte fase 2 (make_tables.py → framework_report.pdf)
│   ├── figures/{eda,framework}/
│   └── match_reports/                     # fichas HTML por partido
├── data/                                  # (ignorado) bronze/ silver/ gold/ (+ raw/ processed/ de la fase 1)
├── requirements.txt · .env.example
└── secrets.md / .env                      # (ignorados) credenciales reales
```

## 8. Cómo correrlo

```bash
py -3.12 -m venv .venv
.venv\Scripts\activate                     # Windows (en bash: source .venv/Scripts/activate)
pip install -r requirements.txt
copy .env.example .env                     # y llenar SB_USERNAME / SB_PASSWORD
python -m ipykernel install --user --name isac-america --display-name "Python (isac-america)"

# pipeline completo (idempotente: re-correr no descarga ni duplica nada)
python -m src.pipeline run --stages bronze,silver,gold,train,score,report

# ficha de partidos concretos
python -m src.pipeline run --stages score,report --match-id 3971433 --match-id 3939923
# (bronze también descarga team-match-stats de TODA la liga para el benchmark del ADN)

pytest -q                                  # marco + reglas anti-leakage

# notebook 03 y reporte de la fase 2
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=isac-america notebooks/03_formulacion_variables_modelos.ipynb notebooks/04_adn_entrenador.ipynb
python reports/framework/make_tables.py
cd reports/framework && latexmk -pdf framework_report.tex
```

| Etapa | Lee | Escribe |
|---|---|---|
| `bronze` | API StatsBomb | `data/bronze/statsbomb/` + manifest |
| `silver` | Bronze | `data/silver/` (valida con compuertas) |
| `gold` | Silver | `data/gold/*.parquet` |
| `train` | Gold | `models/*.joblib` + model cards `.json` |
| `score` | Gold + modelos | `data/gold/scores/match_scores.parquet` |
| `report` | Gold + scores + cards | `reports/match_reports/<fecha>_<rival>.html` (sin `--match-id`: el último partido) |

> Los datos de la fase 1 (`data/raw`, `data/processed`) se conservan porque los notebooks 01–02 los leen. Silver ya reproduce exactamente esos datos (mismos 736,829 eventos, xG y OBV), así que se pueden retirar cuando los notebooks 01–02 pasen a leer de las capas.

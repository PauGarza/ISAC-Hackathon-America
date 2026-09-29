# TODO · ISAC Hackathon 2026 · Club América

> Actualizado: 29 sep 2026 (ADN del Entrenador, partición oficial, benchmark de toda la liga).
> Fuentes: bases oficiales en [isac-app.com](https://www.isac-app.com/competitions/hackathon-america) y [página del reto](https://mr2293.github.io/hackathon_isac/).
>
> Prioridad:
> - 🔴 antes del **9 oct** (entrega);
> - 🟡 del 10 oct al 9 nov (final, si pasamos);
> - ⚪ opcional.

---

## 0. Bases oficiales

| Hito | Fecha |
|---|---|
| Cierre de convocatoria (registro de equipo) | **7 oct 2026** |
| **Entrega de proyectos** | **9 oct 2026** |
| Anuncio de finalistas | 27 oct 2026 |
| Presentaciones finales (CDMX) | **9 nov 2026** |

**Entregables obligatorios** (en español):
1. **Reporte en formato HTML** con metodología, visualizaciones y resultados. El PDF en LaTeX no es el formato de entrega; queda como anexo.
2. **Video de máximo 5 minutos** con una demostración.
3. Solo finalistas: **presentación de máximo 10 diapositivas**.

**Reto:** "contar la historia de un entrenador a través de los datos" y "construir una **metodología que permita al club entender los estilos de juego de entrenadores** y las características que los definen".

**Equipo:** 2 a 4 integrantes, todos inscritos en licenciatura o maestría (a los ganadores se les pide evidencia).

**Datos:**
- Oficiales: "8 temporadas, Apertura 2021 – Clausura 2025".
- Nosotros tenemos hasta 2026 (222 partidos). Hay que decidir si el análisis principal usa la ventana oficial o si se declaran los partidos extra.
- Se pueden presentar **resultados, pero no datos crudos**, y ISAC puede publicar los proyectos.

**Criterios de evaluación:**

| Criterio | Peso | ¿Lo cubrimos hoy? |
|---|---|---|
| Análisis estratégico | 25 % | parcial (falta la narrativa del entrenador) |
| Justificación con datos | 20 % | sí (marco validado, modelos con baseline) |
| ROI estimado realista (escenarios y sensibilidad) | 20 % | **no** |
| Creatividad en activación (coherente con la marca) | 15 % | **no** |
| Escalabilidad (replicable a otros mercados) | 10 % | parcial (pipeline parametrizable) |
| Calidad de presentación | 10 % | parcial |

> ⚠️ ROI, activación y escalabilidad (45 %) parecen venir de una plantilla de reto de negocio. Hay que confirmarlo con los organizadores, pero conviene cubrirlos de todos modos (ver §4).

---

## 0.b Lecciones de los 13 proyectos ganadores anteriores

Retos anteriores, con los mismos datos de Liga MX 2021–2025:
- 2024: balón parado ("¿qué aumenta la probabilidad de gol?");
- 2025: *scouting* ("¿qué jugador encaja mejor?").

| # | Proyecto | Formato | Qué hace |
|---|---|---|---|
| 1 | Optimización de Tiros de Esquina | PDF | Casos de estudio + densidad en el área chica (360) → recomendación con jugadores del América |
| 2 | Set-Piece Optimization | Diapositivas | "¿Qué hace peligroso un córner?": 360 en 2 momentos, CatBoost + SHAP → "del modelo al entrenamiento" |
| 3 | AEGIS | Paper | Simulador de eventos con XGBoost para proyectar un fichaje |
| 4 | LAP | Paper | **Métrica propia con nombre** (a partir del USG del básquet) |
| 5 | Club América – Player Scouting System | Streamlit | (no accesible) |
| 6 | Ojos Diamantes | Streamlit | (no accesible) |
| 7 | Scouting del Club América | Diapositivas | Caso de negocio (Brentford, Brighton) → plataforma con "xG Impact", radares y simulador |
| 8 | Player Style Explorer | Streamlit | Embeddings de estilo de jugador |
| 9 | El Fútbol como Sistema Predictivamente Inteligible | Web React + paper | "OBV Predictor": ensamble, simulador, importancia de variables |
| 10 | Análisis y Metodología de Scouting | Reporte | PCA + K-means de roles, split temporal, sensibilidad |
| 11 | Offside.exe | Reporte + web | "Amazon para jugadores": PCA, clústeres, Word2Vec |
| 12 | Águila Analytics | Video | (solo título) |
| 13 | Análisis Corners Liga MX | R Shiny + GitHub | Dashboard; "3 atacantes en área chica = 14.4 % de gol por remate" |

**Lo que tienen en común:**
1. Un **producto con nombre**, no "un análisis".
2. Una **herramienta interactiva** (6 de 13): se elige un jugador o escenario y el resultado se genera solo.
3. Un **caso de negocio al inicio** (Moneyball, Brentford, Liverpool, Brighton), con valor en millones de dólares.
4. **Recomendaciones con nombres del plantel** y en lenguaje de cancha.
5. **Una pregunta de fútbol como título** y **un hallazgo con número**.
6. **Modelos explicados** (SHAP, importancia de variables, roles con PCA + K-means), con visuales de cancha, radares y mapas de calor.
7. **360** como diferenciador.
8. **Debilidades frecuentes que podemos superar**:
   - partición aleatoria (se cuela información del futuro);
   - poca comparación con un modelo de referencia;
   - ningún marco analítico explícito.

   Nuestro rigor es la diferencia, **pero hay que contarlo en simple**.

Tareas:
- [x] 🔴 **Nombre del producto** → **"ADN del Entrenador"** (`src/coach_profile.py`, notebook 04). Antes: (p. ej., "Radar del Entrenador" o "ADN Azulcrema") y una línea de valor: "entiende el estilo de cualquier entrenador partido por partido".
- [ ] 🔴 **Una pregunta de fútbol como título de cada sección** y **un hallazgo titular con número** (p. ej., "Perdiendo por 1, el América inclina la cancha 9 puntos más").
- [ ] 🔴 (parcial: rotación de técnicos + ROI en el notebook 04) **Caso de negocio breve al inicio**, conectado con el ROI (§4).
- [ ] 🔴 **Recomendaciones con nombres del plantel** (p. ej., "Juárez y Calderón generan más valor que los medios: la salida pasa por atrás").
- [ ] 🔴 El rigor en una frase y sin jerga: "probamos con los partidos más recientes, que el modelo nunca vio".
- [x] 🟡 **Métrica propia con nombre** → **Índice de Encaje** con la identidad del América (notebook 04). Antes: que resuma el estilo, p. ej., un "Índice de Identidad": qué tan parecido es el partido al "América típico" en el mapa de estilo.
- [ ] 🟡 **SHAP o importancia de variables** explicada en lenguaje simple.
- [ ] 🟡 Una idea visible con **360** (altura de la línea defensiva o compactación).

---

## 1. 🔴 Administrativo (antes del 7 oct)
- [ ] Confirmar el registro del equipo (2–4 integrantes) y juntar la constancia de inscripción de cada uno.
- [ ] Preguntar a los organizadores:
  - si los criterios de ROI, activación y escalabilidad aplican a este reto;
  - dónde se suben los entregables;
  - si se pueden usar partidos posteriores al Clausura 2025.
- [x] Ventana de datos: **entrenamiento = ventana oficial (Ap 2021–Cl 2025); validación = Ap 2025; prueba = 2026** (`OFFICIAL_END`, `VAL_END`).

---

## 2. 🔴 Reporte HTML entregable

**Decisión:** un solo **HTML autocontenido e interactivo**, `reports/final/reporte_america.html`, generado con `python -m src.pipeline run --stages final`.
- Cumple el formato oficial y permite **elegir un partido** sin servidor.
- La app en Streamlit queda para la final (🟡) y se construye sobre las mismas funciones.

Estructura:
1. **Resumen para el club** (1 pantalla): la historia del entrenador en 5 ideas, con una visual cada una.
2. **Identidad**: con balón, sin balón, transiciones y balón parado.
3. **Evolución**: por torneo y por entrenador.
4. **Adaptación al contexto**: rival, marcador, localía y minuto.
5. **Jugadores**: cómo se reparte el juego, roles y quién hace funcionar el sistema.
6. **Explorador de partidos**: un **desplegable con los 222 partidos** que actualiza la ficha, los mapas y la crónica.
7. **Metodología** (plegable): pipeline, marco, variables, modelos, validación y limitaciones (resumen del PDF actual).
8. **Valor para el club**: ROI, activación y escalabilidad.
9. **Glosario**.

Tareas:
- [ ] Plantilla Jinja2 (se reutiliza `src/templates/`) con gráficas **Plotly** interactivas (tooltips con explicación).
- [ ] Reutilizar `percentiles` y `chronicle` de `src/match_report.py`, más Gold, `scores` y `analysis`.
- [ ] Embeber **solo agregados** (métricas por partido, percentiles, agregados por jugador, tiros y pases resumidos), **nunca eventos crudos**. Presupuesto: menos de 15 MB.
- [ ] Validar la paleta (daltonismo) y probarla en el celular.
- [ ] Prueba de lectura con alguien que no sepa de datos.

---

## 3. 🔴 Lenguaje de juego (para quien no sabe de ML)

Regla: **primero el fútbol, después el número y al final (plegado) el método.**

| Hoy | En el reporte |
|---|---|
| percentil 94 | "más que 9 de cada 10 partidos del América" |
| z = −2.1 | "muy por debajo de lo esperado para este rival y contexto" |
| Gini | "¿el balón pasa por todos o por pocos?" |
| OBV | "cuánto mejora cada acción las opciones de gol" |
| xG | "calidad de las ocasiones" |
| PSI / drift | "¿el equipo juega distinto últimamente?" |
| MAE, R², model cards | solo en "Metodología" |

- [ ] Nuevo campo `explicacion` en el catálogo de `src/features.py`, con una frase de fútbol por métrica. Ejemplo — PPDA: "pases que el rival da antes de que intentemos recuperar; menos = presionamos más". Se usa en el reporte, los tooltips y el glosario.
- [ ] Reemplazar la gráfica de 55 barras por **8–10 indicadores clave** frente al "América típico" (pizza o barras). El detalle completo va plegado.
- [ ] **Mapas de cancha**:
  - tiros con tamaño = xG;
  - pases progresivos y entradas al área;
  - zonas de recuperación y presión;
  - red de pases con posiciones medias.
- [ ] El color dice **"bueno o malo para el América"**, no "alto o bajo" (p. ej., un PPDA alto es "presionó poco").
- [ ] Crónica de máximo 6 frases naturales, comparada con el América típico y con lo típico contra rivales de este nivel.

---

## 4. 🔴 Valor para el club: ROI, activación y escalabilidad (45 % de la nota)
- [x] (base en `src/business.py`; validar los supuestos con el club) **ROI prudente con 3 escenarios** (conservador, base y optimista) y tabla de sensibilidad:
  - **Costos**:
    - stack local y gratuito (Python, sin nube ni licencias);
    - horas de mantenimiento;
    - datos (el club ya paga a StatsBomb).
  - **Beneficios**:
    - horas de analista ahorradas (la ficha se genera en menos de 1 minuto frente a varias horas manuales);
    - más partidos y rivales analizados;
    - apoyo para evaluar entrenadores candidatos con la misma metodología.
  - Supuestos explícitos.
- [ ] **Activación** coherente con la marca:
  - uso interno: fichas antes y después de cada partido para el cuerpo técnico, y *scouting* de entrenadores y rivales;
  - afición: "la historia del partido en datos", una gráfica por partido en redes, solo con resultados agregados.
- [ ] **Escalabilidad**:
  - el pipeline está parametrizado (`TEAM` y `COMPETITION_ID` en `src/pipeline/config.py`);
  - otro club, la Liga MX Femenil (comp 1438) u otra liga con datos StatsBomb es cambiar la configuración;
  - **demostrarlo con un segundo equipo**.

---

## 5. 🔴 Video de 5 minutos
- [ ] Guion (unas 750 palabras):
  1. el problema, 30 s;
  2. la historia del entrenador en 3 ideas, 90 s;
  3. demo del explorador de partidos, 90 s;
  4. metodología en 1 diagrama, 45 s;
  5. valor para el club, 45 s.
- [ ] Grabación de pantalla con narración y subtítulos en español; revisar que no aparezcan datos crudos.

---

## 6. 🟡 Metodología ML: hiperparámetros, validación y robustez

**Cómo se eligieron hoy:**
- `GridSearchCV` con mallas pequeñas definidas a mano (`REG_CANDIDATES` y `CLF_CANDIDATES` en `src/modeling.py`):
  - Ridge: α ∈ {0.1, 1, 10, 30, 100};
  - LASSO: α ∈ {0.01…1};
  - árbol: profundidad ∈ {2, 3, 4} y hoja mínima ∈ {10, 20};
  - KNN: k ∈ {5, 10, 20}.
- Cada combinación se evalúa con **validación cruzada temporal de ventana creciente** (`TimeSeriesSplit(4)`) sobre entrenamiento + validación: siempre se entrena con el pasado y se valida con los partidos siguientes.
- La prueba (los 34 partidos más recientes) se usa una sola vez.

**¿Vale la pena random search + CV?**
- **Validación cruzada**: ya se hace, en su versión temporal, que es la correcta para estos datos. Lo que falta es hacerla más honesta (ver tareas).
- **Random search**: no aporta para Ridge, LASSO y KNN (1–2 hiperparámetros). Conviene más una malla amplia o `RidgeCV`/`LassoCV`.
- Solo conviene si se agregan modelos con muchos hiperparámetros (gradient boosting, random forest): `RandomizedSearchCV` con distribuciones `loguniform`, unas 50–100 iteraciones y la misma CV temporal.

Tareas:
- [ ] **Óptimos en el borde de la malla** (Ridge α = 100, LASSO α = 1.0) → ampliar con `np.logspace` y agregar una prueba que avise.
- [ ] `TimeSeriesSplit(n_splits=5, gap=2)`; comparar ventana creciente con ventana deslizante (el estilo cambia con cada entrenador).
- [ ] **Validación anidada** para estimar sin optimismo el procedimiento de selección.
- [ ] **Incertidumbre en la prueba** (solo 34 partidos): intervalos bootstrap del MAE y prueba pareada frente al baseline. "Supera al baseline" solo si la mejora es significativa; agregarlo a las model cards.
- [ ] Documentar o separar el rol del conjunto de validación (hoy se funde con la CV).
- [ ] Calibrar T4 y T5 (`CalibratedClassifierCV`) y mostrar la curva de calibración.
- [ ] Efectos aleatorios del rival (`MixedLM`) en T1: los rivales se repiten.
- [ ] Coeficientes con intervalos (bootstrap); SHAP o dependencia parcial si se agregan árboles o boosting.
- [ ] Estabilidad de clústeres U2 y U3 (bootstrap + ARI; comparar con GMM y jerárquico) y nombres de roles validados con jugadores conocidos.
- [ ] Sensibilidad de la selección del núcleo a sus umbrales (fiabilidad 0.30, |ρ| 0.85, VIF 10).
- [ ] Registrar commit, versiones de librerías y semilla en cada model card.

---

## 7. Análisis para la historia del entrenador
- [x] 🔴 (ADN ajustado por rival y localía frente a toda la liga, notebook 04) **Comparar entrenadores y periodos** con las 29 variables núcleo, controlando por rival y localía (regresión con efecto de periodo, no medias crudas).
- [ ] 🔴 (hipótesis reescritas hacia el resultado del hackathon; veredicto de H1, H2, H3, H9 y H10 en el notebook 04; faltan H4–H8) **Contrastar las 10 hipótesis del EDA**: tabla hipótesis → evidencia → veredicto.
- [ ] 🟡 **Encaje rol–uso** (estaba en el plan de la fase 2 y no se implementó): el perfil histórico del jugador frente a su perfil en el partido.
- [ ] 🟡 **360**: pases que rompen líneas, compactación y altura de la línea defensiva.
- [ ] 🟡 Estilo del rival con las mismas variables (no solo sus puntos).
- [ ] 🟡 Balón parado agregado por torneo (por partido es ruido).
- [ ] 🟡 Sustituciones: describir patrones (quién sale, quién entra, con qué marcador) en lugar de predecir su efecto.

---

## 8. 🟡 Profesionalismo del repo
- [ ] Migrar los notebooks 01–02 a leer de Silver/Gold y retirar `data/raw` y `data/processed`.
- [ ] Hacer que `reports/eda/make_tables.py` use `src/latex.py` (hoy duplica `write_table`).
- [ ] Contratos de datos con `pandera` en Silver y Gold.
- [ ] Más tests con datos sintéticos: `aggregate`, `possessions`, `psi`, compuertas y generación del HTML.
- [ ] GitHub Actions (solo tests unitarios, sin datos ni credenciales) + `ruff` + `pre-commit`.
- [ ] `pyproject.toml` con versiones fijadas y un `Makefile` (`make pipeline`, `make final`, `make app`).
- [ ] `docs/arquitectura.md` y `docs/glosario.md`.
- [ ] Registro de corridas en `logs/runs.parquet`.
- [ ] Commits por fase. Verificar que nada versionado contenga datos crudos.

---

## 9. 🟡 Final (9 nov, si somos finalistas)
- [ ] Máximo 10 diapositivas:
  1. problema;
  2–4. la historia del entrenador;
  5. adaptación al contexto;
  6. jugadores;
  7. demo;
  8. metodología;
  9. valor para el club;
  10. cierre.
- [ ] Demo en vivo (HTML o app en Streamlit).
- [ ] Ensayo con cronómetro y preguntas probables del jurado (ROI, metodología, datos).

---

## 10. Calendario

| Fecha | Foco |
|---|---|
| 29 sep – 1 oct | §1 administrativo · §0.b nombre del producto, preguntas-título y hallazgos · §3 catálogo con `explicacion` · ventana de datos |
| 2 – 5 oct | §2 reporte HTML (resumen, identidad, contexto, jugadores, explorador) · §7 comparación de entrenadores |
| 6 – 7 oct | §4 ROI, activación y escalabilidad · §7 hipótesis · **7 oct: cierre de convocatoria** |
| 8 oct | §5 video · revisión final del HTML (tamaño, sin datos crudos, lectura no técnica) |
| **9 oct** | **Entrega: HTML + video** |
| 10 – 27 oct | §6 metodología · §8 profesionalismo · §7 360 y roles |
| 28 oct – 8 nov | §9 diapositivas, demo y ensayo |
| **9 nov** | **Presentación final** |

# TODO · ISAC Hackathon 2026 · Club América

> Actualizado: 29 sep 2026. Reorientado al reto y a los pesos de la evaluación.
>
> Fuentes:
> - [página del reto](https://mr2293.github.io/hackathon_isac/): **qué** analizar;
> - [bases oficiales](https://www.isac-app.com/competitions/hackathon-america): **cómo nos califican**.
>
> Prioridad:
> - 🔴 antes del **9 oct** (entrega);
> - 🟡 del 10 oct al 9 nov (final, si pasamos);
> - ⚪ opcional.
>
> Regla de trabajo: **si una tarea no mueve un criterio con peso o un bloque del reto, no va antes del 9 oct.**

---

## 0. Qué nos evalúan y cómo lo respondemos

| Hito | Fecha |
|---|---|
| Cierre de convocatoria (registro de equipo) | **7 oct 2026** |
| **Entrega: reporte HTML + video (máximo 5 min)** | **9 oct 2026** |
| Anuncio de finalistas | 27 oct 2026 |
| Final en CDMX (máximo 10 diapositivas) | **9 nov 2026** |

**Reglas de datos:**
- se pueden mostrar resultados, **nunca datos crudos**;
- ISAC puede publicar el proyecto.

### 0.a Tabla maestra: criterio → nuestra respuesta

| Criterio | Peso | Qué pide el jurado | Nuestra respuesta | Dónde | Estado |
|---|---|---|---|---|---|
| Análisis estratégico | **25 %** | Comprensión profunda del valor estratégico, criterios de selección claros | **La historia táctica de Jardine** en 5 principios + criterios explícitos para entender y elegir técnicos (ADN) | §3 | parcial: falta la historia |
| Justificación con datos | **20 %** | Uso riguroso de datos, comparación sólida | Marco analítico validado; ADN ajustado por rival y localía frente a 106 técnicos; comparación con Solari, Ortiz y Almada; validación fuera de muestra | §3.9, §3.10 | ✅ base · falta contarlo |
| ROI estimado | **20 %** | Proyección prudente y defendible, varios escenarios | Piso: horas de analista ahorradas. Beneficio adicional: mejores decisiones de técnico. 3 escenarios + sensibilidad | §4.1 | parcial (`src/business.py`) |
| Creatividad en activación | **15 %** | Coherente con la marca, plataforma escalable | Interno: cuerpo técnico y dirección deportiva. Afición: "El ADN del partido" | §4.2 | **no** |
| Escalabilidad | **10 %** | De México a otros mercados | El ADN ya corre para toda la Liga MX; Femenil y otras ligas StatsBomb con solo cambiar la configuración | §4.3 | parcial |
| Calidad de presentación | **10 %** | Claridad lógica, comunicación ejecutiva | HTML con resumen de 1 pantalla, lenguaje de juego, video de 5 min | §5, §6, §7 | **no** |

### 0.b Checklist de bloques del reto (control final antes de entregar)

Pregunta central: *¿qué principios definen al equipo con y sin balón, cómo se manifiestan a lo largo del tiempo y cómo ajusta el entrenador según el contexto?*

| Bloque del reto | Sección | ✔ |
|---|---|---|
| Ofensivo: construcción, progresión, generación de ocasiones | §3.2 | [x] notebook 05 |
| Defensivo: presión, organización, transiciones | §3.3, §3.4 | [x] presión y transiciones (§3.3) · altura y compactación con 360 (§3.4) |
| Consistencia e identidad | §3.5, §3.9 | [ ] |
| Cambios según el contexto (rival, marcador, localía, momento) | §3.5 | [ ] |
| Evolución en el tiempo | §3.6 | [ ] |
| Uso de jugadores: roles, alineaciones, sustituciones | §3.7 | [ ] |
| Balón parado ofensivo: córners, tiros libres, saques de banda; movimientos y zonas de remate | §3.8 | [x] notebook 05 |
| Balón parado defensivo: organización, marcaje, zonas vulnerables | §3.8 | [x] notebook 05 (360 en el saque) |
| Evidencia cuantitativa: xG, OBV, pases progresivos, presión + métrica propia | §3 (todo) | [ ] |
| **Marco analítico**: definiciones, supuestos, coherencia, alcance y límites | §5 (metodología) | [x] `src/framework.py` |
| Modelos o simulaciones **para explicar, no para predecir** | §1 | [ ] |

---

## 1. Decisiones tomadas

- **Ventana de datos.** Constantes `OFFICIAL_END = "2025-06-30"` y `VAL_END = "2025-12-31"` en `src/pipeline/config.py`.

  | Muestra | Periodo | Partidos |
  |---|---|---|
  | **Núcleo** (ventana oficial) | Ap 2021 – Cl 2025 | 175: Jardine 91 · Ortiz 55 · Solari 27 · Cervantes 2 |
  | **Validación** | Ap 2025 | 19, todos de Jardine |
  | **Prueba** | 2026 | 28: Cl 2026 de Jardine 19 · Almada 9 |

  - **Toda cifra titular sale solo de la ventana oficial.**
  - Validación y prueba aparecen solo en "¿Se sostiene el ADN?" (§3.9) y en el explorador de partidos, siempre con su etiqueta.
- **Protagonista: André Jardine.**
  - Tiene 91 partidos en la ventana y el tricampeonato como gancho.
  - Solari y Ortiz son el "antes"; Almada, el "después" (prueba).
- **Producto: "ADN del Entrenador"** (`src/coach_profile.py`, notebook 04), con el **Índice de Encaje** como métrica propia.
  - Encuadre: *la historia de Jardine contada con una metodología que sirve para cualquier técnico*.
  - La historia responde al reto táctico; la metodología responde a ROI, activación y escalabilidad.
- **Modelos para explicar, no para predecir.**
  - T1–T7 y U1–U3 se presentan como "evidencia de que el patrón es real" (p. ej., "el marcador cambia el plan").
  - Nunca como pronóstico.
  - El ajuste fino de ML pasa a 🟡 (§8).

---

## 2. 🔴 Administrativo y auditoría (29–30 sep)

- [ ] Confirmar el registro del equipo (2–4 integrantes) y juntar la constancia de inscripción de cada uno.
- [ ] Preguntar a los organizadores:
  - dónde se suben los entregables;
  - si se pueden usar partidos posteriores al Clausura 2025 como validación y prueba declaradas.
- [x] **Auditoría de la ventana** (29 sep). Qué estaba bien y qué se corrigió:

  | Pieza | Estado |
  |---|---|
  | Partición de modelos (`split_by_date`) | ✅ Correcta: T1–T7 y U1–U3 se ajustan con la ventana; val = 19, prueba = 28. El "34" era un error del todo viejo. Las model cards no cambiaron. |
  | ADN (percentiles, identidad η², consistencia, contexto, encaje, clasificador) | ✅ Ya usaba la ventana; Almada = prueba, etiquetado. |
  | Evolución por torneo (`evolution`, `evolucion.png`) | 🔧 Mezclaba muestras sin etiqueta → columna `muestra` y fondo gris en validación y prueba. |
  | Mapa de estilo de la liga (`liga_mapa_estilo.png`) | 🔧 Usaba todos los partidos (2025–26 incluidos) → ajuste solo con la ventana; Almada-América se proyecta como "2026, prueba". |
  | Selección de variables núcleo (notebook 03) | 🔧 Usaba los 222 partidos (validación y prueba influían) → solo ventana: **27 variables núcleo** (antes 29). |
  | Cifras de jugadores (README, reporte) | 🔧 222 partidos → ventana: top-3 = **61 %** (antes 62), defensas y carrileros = **33 %** (antes 35). |
  | Evolución por partido (`framework/evolution.png`) | 🔧 Fondo gris en validación y prueba. |
  | `america_profile` (sin uso, mezclaba 2026) | 🔧 Eliminada. |
  | Pie de tabla T1 "OLS en train + val" | 🔧 Corregido: el código usa solo la ventana. |
  | Efecto del marcador (+9.5 / −13.7 field tilt) | ✅ Ya era solo de la ventana (Ridge de T2). |
  | Reporte EDA (fase 1) | Se queda con los 222 partidos: es una descripción de los datos, no un hallazgo titular. **No citar sus cifras en el HTML** sin recalcularlas. |

- [ ] Hallazgo honesto para §3.9: el clasificador del ADN en **validación** (Ap 2025) acierta top-5 en 23 % frente a 16 % por azar, más débil que en prueba (31 %). Contarlo así, sin inflarlo. (Cifras con el ADN por torneo; con z de ventana eran 22 % y 35 %.)
- [ ] Etiquetar con su muestra las figuras nuevas (§3) y el explorador de partidos (§5). Las de §3.2–§3.3 (`reports/figures/story/`) ya llevan la muestra al pie.
- [x] **ADN por deriva de la liga** (29 sep; notebook 04 §1b, `liga_deriva.png`, `coach_norm_*.parquet`).
  - **Diagnóstico**: la tasa de recuperación tras contrapresión es estable en ~12 por cada 100 contrapresiones hasta el Cl 2024 y salta a 22 en el Ap 2024 (89 % de los equipos a la vez) y a 30 en el Ap 2025: **escalón simultáneo = cambio de etiquetado de StatsBomb**. El PPDA sube **gradual** (~1 pase por torneo de Ap 2022 a Ap 2023, 72–78 % de los equipos por paso) y se estabiliza desde el Cl 2024: parece cambio real de la liga.
  - **Cambio**: `coach_profile.axis_scores(norm=...)` con `"torneo"` (z contra la liga del mismo torneo; en validación y prueba, la liga de ese torneo, declarado) o `"ventana"`. **Oficial: `AXIS_NORM = "torneo"`.**
  - **Evidencia**: con z de ventana el torneo explicaba el 12 % de la variación de *Reacción tras pérdida* (resto ≤ 3 %); con z por torneo, 0 %. Clasificador igual (top-5 val 22 → 23 %, prueba 35 → 31 %; Almada sigue en posición mediana 2 de 31). Encaje: Jardine 97 → 99 (ahora el n.º 1), Ortiz 99 → 96.
  - **Qué cambió en el relato**: Almada ya no es "reacción tras pérdida" (percentil 79 → 30) sino **presión alta** (67 → 86); Jardine sigue siendo "control y peligro con presión media" (presión alta 37; reacción tras pérdida 69 → 46). README, reporte del marco y notebook 05 revisados: coherentes.
  - **En una frase de fútbol**: a cada técnico se le compara con la liga que le tocó; desde mediados de 2024 StatsBomb cuenta más balones recuperados tras perder en todos los equipos, y eso inflaba a los técnicos recientes.
- [ ] **Decidir la definición de balón parado del marco** (visto en §3.8). El 40 % de xG a balón parado incluye ~3 puntos de posesiones del América que solo **heredan** el `play_pattern` (p. ej., un contragolpe tras atrapar un córner rival). Hay dos opciones:
  - ajustarlo en `framework.possessions`, que cambia `xg_share_set_piece` y las cifras que dependen de ella;
  - dejarlo y declararlo como límite.

  Recomendación: ajustarlo, porque es un error de definición y no un matiz.
- [ ] **Regenerar las fichas HTML** de `reports/match_reports/`: se hicieron antes del ADN por torneo (`python -m src.pipeline run --stages score,report --match-id …`).
- [ ] Buscar "35 %" en textos y diapositivas nuevas: la cifra de prueba del clasificador ya es **31 %**.

---

## 3. 🔴 La historia del entrenador (25 % + 20 %)

Formato de cada sección:
- **una pregunta de fútbol como título**;
- **un hallazgo con número**;
- 1–2 visuales;
- comparación con la liga, con otros técnicos o con el "América típico".

Todo se calcula sobre los 91 partidos de Jardine en la ventana, salvo que se indique otra cosa. Los análisis nuevos con eventos van en un notebook `05_historia_jardine.ipynb` y en funciones reutilizables de `src/story.py`, para que el HTML las consuma.

### 3.1 Identidad en 5 ideas (resumen para el club)
- [ ] 5 principios de Jardine sacados del ADN (p. ej., control del balón, peligro con presión media, juego repartido, construcción desde atrás), cada uno con un número y una visual.
- [ ] Una frase por principio que entienda alguien que no vio los partidos.

### 3.2 Con balón: ¿cómo sale, por dónde progresa y cómo genera ocasiones? ✅ (29 sep)
Hecho en `notebooks/05_historia_jardine.ipynb` con `src/story.py` (cálculos) y `src/story_viz.py` (canchas). Figuras en `reports/figures/story/`, agregados en `data/gold/analysis/story_*.parquet` (hallazgos: `story_hallazgos.parquet`). Ventana oficial: Jardine 91 · Ortiz 55 · Solari 27.
- [x] **Salida** (`salida_saque_meta.png`): Jardine saca en corto el **45 %** de los saques de meta (Ortiz 31 %, Solari 33 %) y el corto lo recibe un **mediocentro que baja en el 44 %** (Ortiz 20 %, Solari 4 %: antes iba casi siempre al central). Es control, no atajo: 66 % de las salidas cortas llega a campo rival (Ortiz 77 %; en largo, 74 %) y dan el mismo xG que en largo (0.7 por 100).
- [x] **Progresión** (`progresion_carriles.png`, `entradas_area.png`): progresa por dentro y entra por fuera. 42 % de los pases progresivos termina en el carril central, pero al último tercio entra 21.1 veces por partido por la izquierda y 17.9 por la derecha frente a 9.3 por el centro. Pisa el área 14.7 veces por partido (Ortiz 15.0, Solari 9.9: +48 %), 41 % conduciendo.
- [x] **Ocasiones** (`tiros_origen.png`, `pase_previo.png`): no tira más, tira mejor: 13.2 tiros y 1.52 xG sin penales por partido, **0.12 xG por tiro** (Ortiz 0.10, Solari 0.08), 65 % de los tiros en el área. Origen del xG: 25 % juego posicional, 36 % transición, 40 % balón parado (definición del marco: toda la posesión que nace de córner o tiro libre). Jugada distintiva: **pase atrás al área, 15 % del xG** (Ortiz 10 %, Solari 8 %); centro 17 % (Solari 28 %).
- [x] **Red de pases** (`red_pases.png`): 4-2-3-1 más usado (41 de 91 partidos), hasta el primer cambio. El balón pasa por el doble pivote Fidalgo (28 pases por partido) y Jonathan dos Santos (27); su conexión es la más usada (21 por partido); el juego se carga a la izquierda (56 % de los pases del 11).

### 3.3 Sin balón: ¿dónde y cómo recupera? ✅ (29 sep, salvo 360 → §3.4)
- [x] **Recuperación** (`recuperaciones.png`): Jardine no roba más arriba que sus antecesores: 52 recuperaciones por partido, altura media 42 yd (Solari 43, Ortiz 42), 24 % en campo rival (igual que ellos). Su zona de robo es el centro de su campo, delante del área (6.4 por partido).
- [x] **Presión frente a la liga** (`presion_liga.png`, comparación contra la media de la liga **en el mismo torneo**, 70 técnicos-club con ≥ 15 partidos): Jardine no asfixia (PPDA 1.9 pases por encima de la liga, 11.º más alto de 70; Ortiz −0.6), pero cuando presiona lo hace arriba (+1.7 puntos de presiones en campo rival, percentil 71) y recupera algo más tras perder (+0.2 por partido, percentil 74) aunque contrapresiona menos (−2.3 por partido).
- [x] **Transiciones** (`transiciones.png`): gana el intercambio: 19.5 a favor por partido (0.54 xG) frente a 17.2 del rival (0.30 xG): 1.8 veces más peligro a favor (Ortiz 1.7, Solari 1.0). Llegan en ~6 s. Concede 0.89 tiros de contraataque por partido, 14.º que menos de 70 técnicos. El % de pérdidas recuperadas en ≤ 5 s (marco) no distingue a los tres técnicos (13–15 %).

### 3.4 360: ¿qué tan alto y qué tan junto defiende? ✅ (29 sep)
Notebook 05 §3.4 con `story.rival_open_play_passes`, `defensive_shape`, `shape_summary`, `match_level_diff`; figura `forma_bloque.png`; agregados `story_forma_*.parquet`. Supuestos nuevos en `ASSUMPTIONS`: `shape_line_players` (4), `shape_block_players` (8), `shape_min_visible` (8), `shape_min_behind_yd` (5). Solo hay 360 del América: la comparación es entre técnicos.
- [x] **Altura y compactación por fase** (pases rivales de juego abierto; fase por la altura del balón con los umbrales de presión del marco). En bloque medio, la última línea de Jardine está a **32 yd** de su portería (Ortiz 34, Solari 33; −1.7 yd por partido frente a Ortiz, IC 90 % −2.6 a −0.8) y su bloque mide **20 yd** (Ortiz 23; −2.1 yd, IC 90 % −2.7 a −1.5). En bloque bajo junta a sus 8 en 15 yd (Ortiz 18, Solari 14). El ancho no distingue a los técnicos (~41 yd).
- [x] **Posesión rival frente a tras pérdida**: tras perder, la línea de Jardine queda en 39 yd (Ortiz 45), pero porque pierde el balón más atrás (54 frente a 59 yd): la distancia balón–línea es casi la misma (12 frente a 11 yd). Lectura: **no adelanta la defensa para asfixiar, la junta** (coherente con la presión media de §3.3).
- [x] **Límite declarado**: 89 % de los pases rivales tiene 360, pero solo 32 % da un frame útil (≥ 8 jugadores de campo visibles y la toma ve ≥ 5 yd detrás del último); en bloque alto, 17 % (la cámara sigue al balón). Líneas por orden de profundidad (4 + 4), no por posición nominal.
- [ ] ⚪ Pases que rompen líneas (no entró; queda en §8).

### 3.5 Contexto: ¿cómo ajusta según el rival, el marcador, la localía y el minuto?
- [x] Base hecha: T1/T2 y notebook 04 (ADN por contexto).
- [ ] Redactar los titulares:
  - "perdiendo por 1, el América inclina la cancha ~9 puntos más; ganando por 1, baja ~13";
  - "frente a rivales fuertes cede balón y territorio";
  - "de local sube la presión".
- [ ] Recalcular esos números solo con la ventana (§2).

### 3.6 Evolución: ¿qué cambió cuando llegó Jardine?
- [x] Base hecha: ADN por periodo y figura `evolucion.png`.
- [ ] Solari → Ortiz → Jardine por torneo (ventana), con un titular por cambio.
- [ ] Almada como epílogo (prueba): "el estilo sigue al técnico, no a la plantilla".

### 3.7 Jugadores: ¿quién hace funcionar el sistema?
- [ ] 11 más usado, formaciones por torneo y rotación (minutos, estabilidad de la alineación).
- [ ] Reparto del juego: los 3 mejores generan ~61 % del OBV positivo; defensas y carrileros, ~33 % (ventana oficial). **Con nombres del plantel.**
- [ ] Roles U3 nombrados con jugadores conocidos.
- [ ] **Sustituciones (describir, no predecir)**: minuto, marcador al momento del cambio y perfil que sale y que entra. Usar `fct_substitution`.

### 3.8 Balón parado: ¿cómo ataca y cómo defiende las jugadas a balón parado? ✅ (29 sep)
Agregado de toda la era en la ventana (notebook 05 §3.8). Funciones: `story.set_piece_plays` (solo jugadas que abre el saque de quien la tiene: descarta posesiones que heredan el `play_pattern`), `set_piece_shots`, `set_piece_summary`, `delivery_summary`, `shot_zone_summary`, `set_piece_xg_share`, `corner_defense`, `marking_vs_chance`; figuras `balon_parado.png` y `balon_parado_defensa.png`; agregados `story_bp_*.parquet`. Supuestos nuevos: `set_piece_free_kick_x_min` (80), `set_piece_marking_yd` (2), `set_piece_min_box_visible` (0.9).
- [x] **A favor**: Jardine juega en corto el **25 %** de sus córners (Ortiz 13 %, Solari 9 %) y, cuando centra, apunta al punto de penal (38 %) más que al área chica (16 %; Ortiz 27 %). 5.0 córners por partido, 36 % termina en tiro, **0.039 xG por córner** (Ortiz 0.034; +0.006 frente a la liga de su torneo, 16.º de 70). Tiros libres del último tercio: 2.5 por partido, 40 % con tiro; saques de banda del último tercio: 7.1 por partido, 11 % con tiro. Total: 0.40 xG y 35 goles a balón parado en 91 partidos; 35 % de ese xG se remata en el área chica.
- [x] **Las dos cifras de xG a balón parado**: marco (toda la posesión que nace de córner o tiro libre en cualquier zona) = **40 %** del xG sin penales; jugadas de §3.8 (córners + último tercio, toda la jugada) = 26 %; **solo el remate directo del envío = 7 %** (Ortiz 10 %, Solari 14 %). La mayor parte del peligro es la segunda jugada.
- [x] **En contra**: 0.30 xG por partido a balón parado (Ortiz 0.25, Solari 0.23), 16 goles. El córner es lo que más le cuesta: 4.8 por partido (Ortiz 3.9); frente a la liga concede 0.03 xG menos a balón parado por partido (23.º de 70) pero 0.003 más por córner (49.º). Zona vulnerable: la zona de penal (52 % del xG en contra); área chica 29 % (Ortiz 41 %); primer palo 53 % en córners.
- [x] **360 en el saque** (córners rivales no jugados en corto; 198 de 406 con ≥ 90 % del área y toda el área chica a la vista): **9 defensores en el área, 3.6 en el área chica**; 41 % pegados a un rival (≤ 2 yd) frente a 24 % por azar → **esquema mixto** (base zonal en el área chica + marcas individuales). Ortiz, más al hombre (50 % frente a 26 %); Solari 32 % frente a 24 %. "Pegado" no es "marcando": la prueba contra el azar dice si hay más cercanía de la que darían posiciones fijas.
- [x] **Liga**: eje "Balón parado" del ADN, percentil 74 (Ortiz 79, Solari 62); métricas de StatsBomb contra la media del mismo torneo en `story_bp_liga_rank.parquet`.

### 3.9 ¿Se sostiene el ADN? (justificación con datos)
- [x] Base hecha: validación del cambio a Almada en el notebook 04 (posición mediana 2 de 31 técnicos).
- [ ] Validación, Ap 2025: ¿el Jardine de 2025 sigue siendo el de la ventana?
- [ ] Prueba, 2026: Cl 2026 de Jardine y llegada de Almada.
- [ ] El rigor en una frase y sin jerga: "probamos con partidos que el modelo nunca vio".

### 3.10 Hipótesis del EDA
- [ ] Tabla hipótesis → evidencia → veredicto.
  - H1, H2, H3, H9 y H10 ya tienen veredicto (notebook 04).
  - **Faltan H4–H8.**

### 3.11 Recomendaciones
- [ ] 3–5 recomendaciones con nombres del plantel y en lenguaje de cancha:
  - para el cuerpo técnico;
  - para la dirección deportiva: qué perfil de técnico encaja, según el Índice de Encaje.

---

## 4. 🔴 Valor para el club (45 % de la nota)

### 4.1 ROI (20 %)
Base en `src/business.py`: `scenario_table`, `sensitivity`, `coach_stints`, `turnover_summary`.
- [ ] **Caso de negocio al inicio**: rotación de técnicos en la Liga MX (dato real de `turnover_summary`) → el costo de elegir mal.
- [ ] **Piso defendible**: horas de analista ahorradas (la ficha se genera en menos de 1 minuto frente a varias horas manuales) × partidos por año.
- [ ] **Beneficio adicional**: reducción del error al elegir técnico, con la tabla de sensibilidad. Decir explícitamente que es un supuesto.
- [ ] 3 escenarios (conservador, base y optimista) con los supuestos visibles.
- [ ] Costos:
  - stack local y gratuito;
  - horas de mantenimiento;
  - los datos ya se pagan a StatsBomb.

### 4.2 Activación (15 %)
- [ ] **Uso interno**:
  - ficha antes y después de cada partido para el cuerpo técnico;
  - *scouting* de rivales y de técnicos;
  - evaluación de candidatos a técnico con el ADN y el Índice de Encaje.
- [ ] **Afición**: "El ADN del partido", una tarjeta por partido para redes con el radar del partido frente al ADN del técnico. Ya existe en la ficha: `feat(ficha): radar del partido frente al ADN`. Solo agregados.
- [ ] 1–2 **maquetas visuales**: tarjeta para redes y vista para el cuerpo técnico.
- [ ] Cómo escala la plataforma: calendario (por jornada), formatos y métricas de éxito (interacción, uso interno).

### 4.3 Escalabilidad (10 %)
- [ ] Demostrarla con lo que ya existe:
  - ADN para los 106 técnicos de la Liga MX;
  - ficha automática para un **segundo equipo**.
- [ ] Liga MX Femenil (comp 1438, sin 360): qué funciona y qué no.
- [ ] Otras ligas StatsBomb cambiando `TEAM` y `COMPETITION_ID` (`src/pipeline/config.py`).
- [ ] Una visual "México → otros mercados".

---

## 5. 🔴 Reporte HTML entregable

**Decisión:** un solo HTML autocontenido e interactivo, `reports/final/reporte_america.html`, generado con `python -m src.pipeline run --stages final`.
- Jinja2 + Plotly.
- Reutiliza `src/match_report.py` (`percentiles`, `chronicle`), `src/coach_viz.py` y `src/templates/`.

Estructura (orden según el peso de cada criterio):
1. **Resumen para el club** (1 pantalla): la historia de Jardine en 5 ideas + el caso de negocio en una línea.
2. **La historia**: §3.2–§3.8.
3. **¿Se sostiene?**: §3.9.
4. **Valor para el club**: ROI, activación y escalabilidad (§4).
5. **Explorador de partidos**: desplegable que actualiza la ficha, los mapas y la crónica. Cada partido lleva la etiqueta de su muestra.
6. **Metodología** (plegable): marco analítico (definiciones, supuestos, coherencia, alcance y límites), pipeline, variables, validación.
7. **Glosario**.

Tareas:
- [ ] Esqueleto de la plantilla y la etapa `final` del pipeline.
- [ ] Embeber **solo agregados**, nunca eventos crudos. Presupuesto: menos de 15 MB.
- [ ] Paleta apta para daltonismo; el color dice "bueno o malo para el América"; probar en el celular.
- [ ] Prueba de lectura con alguien que no sepa de datos.

---

## 6. 🔴 Lenguaje de juego (para quien no sabe de ML)

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

- [ ] Nuevo campo `explicacion` en el catálogo de `src/features.py`, con una frase de fútbol por métrica. Se usa en el reporte, los tooltips y el glosario.
- [ ] Reemplazar la gráfica de 55 barras por **8–10 indicadores clave** frente al "América típico".
- [ ] Crónica de máximo 6 frases naturales por partido.

---

## 7. 🔴 Video de 5 minutos

- [ ] Guion (unas 750 palabras), con tiempos según el peso de cada criterio:
  1. problema y caso de negocio, 30 s;
  2. la historia de Jardine en 3–5 ideas, 2 min;
  3. demo del explorador y del ADN de otro técnico, 1 min;
  4. valor para el club (ROI, activación y escalabilidad), 1 min;
  5. metodología en 1 diagrama, 30 s.
- [ ] Grabación de pantalla con narración y subtítulos en español.
- [ ] Revisar que no aparezcan datos crudos.

---

## 8. 🟡 Después del 9 oct

**Metodología ML** (se presenta como rigor, no es prioridad para la entrega):
- [ ] Óptimos en el borde de la malla (Ridge α = 100, LASSO α = 1.0) → ampliar con `np.logspace`.
- [ ] `TimeSeriesSplit(n_splits=5, gap=2)`; comparar ventana creciente con ventana deslizante.
- [ ] Validación anidada.
- [ ] Intervalos bootstrap en la prueba y prueba pareada frente al baseline.
- [ ] Calibrar T4 y T5.
- [ ] Efectos aleatorios del rival (`MixedLM`).
- [ ] Coeficientes con intervalos y SHAP o dependencia parcial explicados en simple.
- [ ] Estabilidad de clústeres U2 y U3 (bootstrap + ARI).
- [ ] Sensibilidad de la selección del núcleo a sus umbrales.
- [ ] Commit, versiones y semilla en cada model card.

**Análisis extra:**
- [ ] Encaje rol–uso por jugador.
- [ ] Estilo del rival con las mismas variables.
- [ ] Pases que rompen líneas con 360, si no entró en §3.4.

**Profesionalismo del repo:**
- [ ] Notebooks 01–02 que lean de Silver/Gold; retirar `data/raw` y `data/processed`.
- [ ] `reports/eda/make_tables.py` → `src/latex.py`.
- [ ] Contratos de datos con `pandera`.
- [ ] Más tests con datos sintéticos.
- [ ] GitHub Actions + `ruff` + `pre-commit`.
- [ ] `pyproject.toml` con versiones fijadas y un `Makefile`.
- [ ] `docs/arquitectura.md` y `docs/glosario.md`.
- [ ] Registro de corridas en `logs/runs.parquet`.

---

## 9. 🟡 Final (9 nov, si somos finalistas)

- [ ] Máximo 10 diapositivas, en proporción al peso de cada criterio:
  1. caso de negocio;
  2–4. la historia de Jardine (identidad, contexto, jugadores y balón parado);
  5. ¿se sostiene? (validación y Almada);
  6. demo;
  7. ROI;
  8. activación y escalabilidad;
  9. metodología;
  10. cierre y recomendaciones.
- [ ] Demo en vivo (HTML o app en Streamlit sobre las mismas funciones).
- [ ] Ensayo con cronómetro y preguntas probables del jurado (ROI, metodología, datos, por qué Jardine).

---

## 10. Lecciones de los 13 proyectos ganadores anteriores (lo que falta aplicar)

Lo que tienen en común:
- un producto con nombre ✅ (ADN del Entrenador);
- una métrica propia ✅ (Índice de Encaje);
- una herramienta interactiva (§5);
- un caso de negocio al inicio (§4.1);
- recomendaciones con nombres del plantel (§3.11);
- una pregunta de fútbol como título y un hallazgo con número (§3);
- 360 como diferenciador (§3.4);
- visuales de cancha (§3.2, §3.3).

Sus debilidades frecuentes, que en nosotros son fortalezas **que hay que contar en simple**:
- partición aleatoria;
- poca comparación con un modelo de referencia;
- ningún marco analítico explícito.

---

## 11. Calendario

| Fecha | Foco |
|---|---|
| 29–30 sep | §2 administrativo y auditoría de la ventana · §3.1 identidad en 5 ideas |
| 1–3 oct | §3.2 con balón · §3.3 sin balón · §3.4 360 · §3.7 jugadores · §3.8 balón parado |
| 4–5 oct | §5 HTML (esqueleto, historia, explorador) · §6 lenguaje · §3.5–3.6 titulares |
| 6–7 oct | §4 ROI, activación y escalabilidad · §3.9–3.11 · **7 oct: cierre de convocatoria** |
| 8 oct | §7 video · revisión con el checklist de §0.b (sin datos crudos, lectura no técnica, tamaño del HTML) |
| **9 oct** | **Entrega: HTML + video** |
| 10–27 oct | §8 metodología y repo |
| 28 oct – 8 nov | §9 diapositivas, demo y ensayo |
| **9 nov** | **Final** |

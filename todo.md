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

## ★ Plan vie 16 → jue 22 oct (entrega real: **22 oct**; el "9 oct" de abajo era un error)

### Decisión del 16 oct: historia y app separadas
- **Reporte HTML** = la historia fija; combina las ideas de los tres:
  - Pau: historia de Jardine, ADN del Entrenador, Índice de Encaje;
  - Otho: ADN del club, ADN ganador, liguillas, rivales;
  - Emi: lenguaje de cancha, puntos críticos, recomendaciones con solución, hipótesis nuevas.
- **App** = explorador **sin conclusiones escritas a mano**. Todo texto se calcula con la selección.
- Las dos usan el mismo cubo y las mismas piezas visuales (`src/viz.py`).

### Hecho (16 oct)
- [x] App sin historia:
  - fuera el modo "La historia de Jardine", textos, hallazgos y figuras fijas;
  - Torneo a torneo con una tabla calculada;
  - siglas explicadas y glosario de siglas en "Cómo lo medimos";
  - `app/data/` sin `textos.md` ni `hallazgos.parquet`.
- [x] `src/viz.py`: cancha, mapa de calor, radar y paleta compartidos (tests en `tests/test_viz.py`).
- [x] **Hipótesis de los tres probadas**:
  - `src/hipotesis.py`, notebook `06_hipotesis_equipo.ipynb` y registro en `data/gold/analysis/hipotesis_equipo.parquet` (31 hipótesis con origen, evidencia, veredicto y sección del reporte);
  - **todas las formaciones, por minutos en el campo** (titular + cambios tácticos; la propia y la del rival), comparadas con el 4-2-3-1 con el mismo técnico, rival y marcador (`tramos_formacion`, `comparar_formacion`). Umbrales nuevos en `ASSUMPTIONS`: `big_chance_xg` 0.30 (ocasión clara) y `formation_min_minutes` 20;
  - comparaciones dentro del mismo técnico y nivel de rival (permutación estratificada);
  - el plan de juego se mide con el partido empatado.
- Lo más importante del registro:
  - el ADN del club es **control, peligro y solidez** (corrige H2: el balón parado depende del técnico);
  - la **localía sí distingue**, en resultado y en estilo;
  - en liguilla, **el que avanza cede el balón y presiona menos** (Otho, se sostiene serie por serie);
  - que el campeón produzca más en la fase regular es solo una pista;
  - **Ortiz perdió sus semifinales presionando como nunca**;
  - el **cierre del primer tiempo** es su momento más vulnerable;
  - al perder: tira peor, le hacen daño al contragolpe y domina menos con el partido empatado;
  - formaciones:
    - el 4-4-2 rinde igual que el 4-2-3-1 (solo presiona menos), pero contra rivales fuertes llega más al área sin conceder más;
    - con **tres centrales el equipo se repliega sin protegerse más**, incluso contra rivales con línea de 3 (el espejo no ayuda);
    - el 4-3-3 genera menos;
  - **no había mejores jugadores** cuando ganó (por aporte, OBV);
  - extremos a pierna cambiada desde Ortiz.

### Decidido (17 oct)
- **El reporte HTML es el producto principal**; la app es un complemento para explorar.
- **Ventana:** cifras de Ap 2021 – Cl 2025; 2025–26 solo como epílogo. La liguilla del notebook 06 ya se recalculó con la ventana:
  - C2 (presión de espera en liguilla) se sostiene con pocas series;
  - C4 (balón parado en liguilla) ahora se sostiene en ocasiones a favor;
  - H6/D8 pasa al epílogo.
- **Recuperación tras pérdida:** por evento, ≤ 5 s tras perder.
  - [ ] Llevarla a `src/framework.py` y al cubo.
- Los documentos del equipo van en "nosotros", sin atribuir ideas a nadie.

### Decidido (20 oct)
- **Marco:** Python como base. Del marco en R solo entra la recuperación tras pérdida por evento, que ya está en el marco, la capa gold, el cubo y la app.
- **Historia en 5 ideas:**
  1. el ADN del club;
  2. lo que puso Jardine;
  3. lee el partido;
  4. el ADN ganador;
  5. los puntos críticos.
- **Recomendaciones:**
  - plan de liguilla;
  - 4-4-2 contra rivales fuertes;
  - cierre del primer tiempo y cambios;
  - primer palo y relevo de Fidalgo.
- **Del análisis en R** entran finales, rivales, tipos de gol y defensa bajo ataque, recalculados en Python (notebook 07).
- [x] Reporte final: `python -m src.final_report` → `reports/final/reporte_america.html`.
- [ ] Antes de entregar:
  - enlace a la app publicada (`APP_URL` en `src/final_report.py`);
  - nombres del equipo;
  - video;
  - correo de entrega.

### Pendiente
- [ ] Discutir el prerreporte (`reports/prereporte/prereporte_equipo.html`, `python -m src.prereporte`):
  - elegir una definición para cada diferencia entre el marco en Python y el de R;
  - las 5–6 ideas del reporte;
  - las recomendaciones;
  - el material del análisis en R que entra.
- [x] Otho pasó su parte (`Otho/Hackathon América/`: R, salidas agregadas, narrativa y framework). **`Otho/` completa está en `.gitignore`**: trae datos crudos de StatsBomb (`reto/`, 337 MB) y una tabla con un renglón por gol.
- [ ] Para el reporte: copiar a `reports/final/` solo las tablas o figuras agregadas de Otho que entren (recetas y tipos de gol, defensa bajo ataque, finales, índice de rival). Nunca `goles_secuencias.csv`.
- [ ] Reescribir `reports/final/textos.md` con la estructura acordada:
  - 0 · en un minuto;
  - 1 · ADN del América;
  - 2 · lo que agregó Jardine;
  - 3 · cómo ajusta;
  - 4 · por qué ganó y por qué no ganaron;
  - 5 · puntos críticos;
  - 6 · lo que probamos y no cambia;
  - 7 · recomendaciones;
  - 8 · nuestro aporte;
  - anexos: marco analítico y glosario.
- [ ] `src/final_report.py` + `src/templates/final_report.html.j2` → `reports/final/reporte_america.html` (< 15 MB, solo agregados).
- [ ] Video (≤ 5 min) y prueba de lectura con alguien de fuera de datos (21 oct).
- [ ] Entrega por correo a itamsportsanalytics@gmail.com con los correos de los tres (22 oct).

---

## ★ Plan lun 5 → vie 9 oct (una persona, ~6 h/día)

### Definición del producto (decidida el 5 oct)
**Es un producto de visualización, no de ML, y lo usa la marca, no un equipo de datos.**
- La validación y la prueba (Ap 2025, 2026) solo sirvieron para comprobar nuestras hipótesis: no aparecen en la app.
- En la app no se habla de "ventana", "muestra", "percentil", "modelo", "validación" ni "prueba". Se dice:
  - "Ap 2021 – Cl 2025" o "2023–2025";
  - "temporadas recientes";
  - "de 0 a 100 frente a la liga";
  - "aporte" en lugar de OBV;
  - "dominio territorial" en lugar de field tilt;
  - "pases que deja dar al rival antes de presionar" en lugar de PPDA.

  Las figuras de la historia ya llevan pies de figura en ese lenguaje (5 oct).

**"ADN del Entrenador · Club América"**: una página donde **primero se elige el periodo** y luego se despliega todo el análisis.
- **Protagonista Jardine, los demás como contraste.** El estilo solo se ve comparando: Solari y Ortiz son el "antes" y Almada el "después" (prueba). Se puede elegir cualquier técnico del América, y el ADN existe para los 106 de la liga.
- **Selector**:
  - técnico;
  - periodo: torneo, rango de fechas o un partido;
  - contexto: local o visita, rival fuerte, medio o débil.

  Siempre se muestra **cuántos partidos** hay y de qué muestra son (ventana, validación o prueba).
- **Regla de muestra** (el estilo por partido es identidad más ruido):

  | Selección | Qué se muestra |
  |---|---|
  | 1 partido | La ficha: el partido frente al ADN, crónica y mapas |
  | Menos de 5 partidos | Tendencias con aviso de muestra chica, sin rankings |
  | Torneo | Todo, con percentil aproximado |
  | Era completa | Las cifras titulares |
- **Rivales siempre visibles**: un calendario del periodo con rival, fuerza, resultado y xG. El rival pesa más que la localía (Jardine: 61 % de posesión contra débiles, 49 % contra fuertes); un tramo con rivales grandes no es un cambio de estilo.
- **La historia es el explorador con la selección predeterminada** (Jardine, ventana oficial) y los textos de `reports/final/textos.md` encima.
- **Bloques**:
  1. Identidad (ADN del periodo frente a la era y la liga, Índice de Encaje, 5 ideas).
  2. Con balón.
  3. Sin balón (incluye 360).
  4. Balón parado.
  5. Contexto.
  6. Jugadores.
  7. Comparar con otro técnico o periodo.
- **Datos**: la app pública no lleva eventos ni frames 360. Usa un **cubo de agregados por partido** (indicadores y conteos por zona), y filtrar es sumar o promediar partidos. Lo que necesita eventos y solo existe por era (360, red de pases, roles) se muestra fijo, con su etiqueta.
- **Entregables**:
  - **HTML oficial** = la historia fija (textos y figuras) con el enlace a la app;
  - **app Streamlit** = el producto (también es la demo del video);
  - **video** de 5 min o menos.
- **Rúbrica frente al reto**: la rúbrica habla de "IP", ROI, activación y escalabilidad; el reto es táctico. **Prioridad: el producto táctico.** El bloque de negocio queda contemplado (base en `src/business.py`), pero en pausa hasta la **junta con los organizadores (mar 6, 7 pm)**.

### Hecho hasta hoy
- [x] Registro del equipo.
- [x] Marco analítico (`src/framework.py`), pipeline medallion, model cards, fichas por partido.
- [x] ADN del Entrenador (106 técnicos, z por torneo) + Índice de Encaje + validación con Almada.
- [x] Historia: §3.2 con balón · §3.3 sin balón · §3.4 forma con 360 · §3.8 balón parado (notebook 05).
- [x] Base de ROI en `src/business.py` (escenarios, sensibilidad, rotación).
- [x] Historia: §3.5 contexto · §3.6 evolución · §3.7 jugadores (notebook 05, 5 oct).

### Lun 5 · Cerrar la historia
- [x] Actualizar este todo.
- [ ] **Junta con los organizadores, mar 6 a las 7 pm**. Preguntar:
  - ¿aplica la rúbrica de IP, ROI y activación de marca a este reto?, ¿con qué peso?;
  - ¿dónde se suben el HTML y el video?, ¿vale un enlace de YouTube o Drive?;
  - ¿se pueden usar partidos posteriores al Cl 2025 como validación y prueba?;
  - ¿se puede entregar una app de Streamlit además del HTML?
- [x] §3.7 jugadores, §3.5 contexto y §3.6 evolución: notebook 05, 7 figuras nuevas, hallazgos en `story_hallazgos.parquet`, commit.
- [x] Textos de la historia en `reports/final/textos.md`: resumen de 1 pantalla, §3.1 5 ideas, §3.2–§3.8, §3.9, §3.10 corta, §3.11 recomendaciones con nombres.
- [x] Fichas regeneradas con el ADN por torneo (Santos 20 oct 2024 y Monterrey 16 dic 2024). Pesan ~650 KB cada una → el explorador del HTML va con JSON de agregados, no con fichas embebidas.

### Mar 6 · Cubo de agregados + núcleo de la app (adelantado el lun 5 por la noche)
- [x] `src/cube.py`: 222 partidos (ventana, validación y prueba), 11 tablas, 0.4 MB:
  - partidos: meta, rival por terciles, 41 indicadores del marco, ADN del partido, sistema, primer cambio;
  - rejillas 12×8 por partido: tiros, tiros rivales, recuperaciones, acciones defensivas, pases progresivos;
  - balón parado, tramos × marcador, cambios, jugadores por técnico × torneo, referencia del ADN.

  Guarda contra columnas crudas: sin eventos, sin coordenadas sueltas, sin `sb_*`. Los jugadores van por torneo, no por partido.
- [x] **Validado contra el notebook**:
  - ADN de Jardine y Almada idéntico;
  - 13.2 tiros y 1.52 xG por partido;
  - 0.039 xG por córner;
  - efecto del marcador +8.3 / −16.9 (misma regresión);
  - % de minutos y de OBV de los jugadores.

  Ojo: los indicadores del cubo son **media por partido**. La historia a veces junta todos los eventos (saques de meta cortos: 47 % frente a 45 %); etiquetarlo así.
- [x] Consultas: `select`, `nivel_muestra`, `resumen`, `indicadores`, `adn_percentil`, `rejilla`, `balon_parado`, `efecto_marcador`, `jugadores_periodo`. 8 tests sintéticos (`tests/test_cube.py`, 42 en verde en total).
- [x] `app/export_data.py` → `app/data/`. El patrón `data/` del `.gitignore` lo ignora: decidir el jueves, al desplegar (repo privado o excepción solo para `app/data/`).
- [x] `app/streamlit_app.py`:
  - modo "La historia de Jardine" o "Explorar";
  - periodo (era, torneo, fechas, un partido) y contexto (localía, fuerza del rival);
  - aviso de muestra y calendario de rivales;
  - comparación con otro técnico o el América típico;
  - pestañas: Identidad (radar del ADN), Con balón, Sin balón, Balón parado, Contexto, Jugadores, Método.

  Probada sin errores en todos los modos (AppTest). Correr con `streamlit run app/streamlit_app.py`.
- [ ] **Revisión visual con la usuaria** y ajustes de diseño y textos.
- [ ] Pendientes de la app:
  - vista de 1 partido más rica (crónica y radar del partido frente al ADN, reusando `match_report`);
  - "Comparar" lado a lado;
  - explicaciones de cada indicador en lenguaje de cancha (tooltips).

### Mié 7 · Resto de la app + HTML oficial + valor para el club
- [ ] App: Balón parado, Contexto, Jugadores, Comparar, vista de 1 partido (ficha), y la historia como selección predeterminada.
- [ ] HTML oficial: etapa `final` del pipeline + `src/templates/final_report.html.j2` (textos + figuras PNG en base64 + enlace a la app), menos de 15 MB, sin datos crudos.
- [ ] ⏸ Según lo que se diga en la junta: §4.1 ROI (escenarios + sensibilidad) · §4.2 activación · §4.3 escalabilidad. Si no aplica, queda una sección corta de "usos y escalabilidad" (ADN de los 106 técnicos).

### Jue 8 · Despliegue + video
- [ ] **Hosting: GitHub Pages con stlite** (Streamlit corriendo en el navegador). Pages solo sirve archivos estáticos, así que la app normal no corre ahí.
  - Una sola página `index.html` que carga `app/streamlit_app.py`, `src/cube.py` y `app/data/*.parquet`.
  - Probar que carguen pandas, plotly y statsmodels en el navegador. Si `statsmodels` falla, cambiar el efecto del marcador por una versión con numpy (mínimos cuadrados con efecto fijo del partido) o precalcularlo por técnico × torneo.
  - Costos:
    - la primera carga tarda unos 20–40 s;
    - los datos agregados quedan **públicos** (Pages es público): confirmarlo con los organizadores en la junta.
  - Plan B: Streamlit Community Cloud, que es un servidor real y admite un repositorio privado.
  - `app/data/` hoy está ignorado (patrón `data/` del `.gitignore`): abrir una excepción solo para esa carpeta al publicar.
- [ ] Guion (~750 palabras), grabación de pantalla con narración y subtítulos (demo de la app).
- [ ] Revisión final:
  - checklist §0.b;
  - sin datos crudos;
  - sin jerga en la app;
  - prueba de lectura con alguien de fuera de datos.

### Vie 9 · Colchón y entrega
- [ ] Ajustes de la prueba de lectura, regenerar el HTML y el cubo desde cero, subir el HTML, el video y el enlace a la app, README.

### 16 oct · Ideas del reporte de Otho (`Otho/reporte_adn_america.html`, no se versiona)
- [x] **Torneo a torneo / "ADN ganador"**:
  - filtro Fase regular / Liguilla y hasta dónde llegó en cada torneo (`cube.stage_reached`);
  - en las 3 liguillas ganadas el América cedió el balón y esperó (48 % de posesión, 21 pases antes de presionar; en las 7 no ganadas, 56 % y 11);
  - **controlado por marcador**: con el partido empatado se repite (47 % frente a 54 %) y el tiempo que pasó ganando es parecido (25 % frente a 21 %);
  - en fase regular la posesión casi no cambia; el campeón genera más (1.61 frente a 1.43 xG por partido).
- [x] **Puntos esperados** (simulación del reto, sección 6): cálculo exacto de goles por posesión, 1 − ∏(1 − xG). Coincide con Otho: Jardine 1.86 reales frente a 1.78 esperados. Aparece en el encabezado, en un partido suelto ("ganaba X % de las veces"), en Rivales y en Torneo a torneo.
- [x] **Rivales**: puntos frente a lo que merecía, por rival (Pachuca 1.31 con 31 % de victorias; Tigres 2.17).
- [x] **Valor de recuperar por zona**: en el último tercio, 24 % de los robos termina en tiro; en el medio, 13 %; en campo propio, 8 %.
- [ ] Revisar "balones recuperados en 5 s o menos": se mide por posesiones y puede subestimarse (Otho: 2.5 % por posesión frente a 24 % por evento; nosotros, 13–15 %).
- [ ] Pendientes de Otho que no entraron:
  - tipos de ataque (balón parado, contragolpe, directo, elaborado, corto);
  - "lo que el América siempre es" frente a la liga;
  - recetas de gol.

### Recortes (pasan a 🟡)
- §3.10 H4–H8 → tabla corta solo con H1, H2, H3, H9, H10.
- §6 campo `explicacion` → glosario fijo en el HTML.
- §4.3 Femenil → un párrafo, sin correrla.
- Maqueta de redes → el radar de la ficha como "tarjeta".

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
| Consistencia e identidad | §3.5, §3.6, §3.9 | [x] ADN por torneo (§3.6) · falta §3.9 |
| Cambios según el contexto (rival, marcador, localía, momento) | §3.5 | [x] notebook 05 |
| Evolución en el tiempo | §3.6 | [x] notebook 05 |
| Uso de jugadores: roles, alineaciones, sustituciones | §3.7 | [x] notebook 05 |
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

- [x] Confirmar el registro del equipo (2–4 integrantes) y juntar la constancia de inscripción de cada uno.
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
  | Selección de variables núcleo (notebook 03) | 🔧 Usaba los 222 partidos (validación y prueba influían) → solo ventana: 27 variables núcleo (antes 29); **28** tras ajustar la definición de balón parado (ver abajo). |
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
- [x] **Definición de balón parado del marco** (29 sep). `framework.possessions` solo marca `is_set_piece` si la posesión la abre el saque del **propio** equipo (`framework.opens_with_restart`, la misma regla que `story.set_piece_plays`; test `test_set_piece_only_when_own_restart_opens_possession`). Las posesiones que heredaban la etiqueta (p. ej., un contragolpe tras atrapar un córner rival) pasan a transición o a juego posicional. Gold, notebooks 03, 04 y 05 y reporte del marco regenerados. Qué cambió:

  | Cifra (Jardine, ventana) | Antes | Ahora |
  |---|---|---|
  | xG a balón parado, definición del marco (§3.2, §3.8) | 40 % | **37 %** |
  | xG de transición / juego posicional (§3.2) | 36 % / 25 % | **38 % / 26 %** |
  | Transiciones a favor por partido (§3.3) | 19.5 (0.54 xG) | **20.6 (0.57 xG)**; rival 17.2 → 18.1 |
  | Recuperaciones que acaban en transición (§3.3) | 38 % | 40 % |
  | `fct_set_piece` (todas las jugadas, ambos equipos) | 12,509 | 10,874 |
  | Variables núcleo (notebook 03) | 27 | **28** (entra *Posesiones en transición*, fiabilidad 0.28 → 0.31) |
  | T5 (¿el balón parado termina en tiro?), ROC-AUC en prueba | 0.68 a favor · 0.71 en contra | 0.70 · 0.75 |
  | `corner_shot_pct` (ahora solo córners que saca el propio equipo) | 29 % | 36 % |

  Sin cambios: el ADN (usa métricas de StatsBomb de toda la liga), el efecto del marcador de T2, las cifras de jugadores y el resto de §3.8 (ya usaba jugadas directas).
- [x] **Regenerar las fichas HTML** de `reports/match_reports/`: se hicieron antes del ADN por torneo (`python -m src.pipeline run --stages score,report --match-id …`).
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
- [x] **Ocasiones** (`tiros_origen.png`, `pase_previo.png`): no tira más, tira mejor: 13.2 tiros y 1.52 xG sin penales por partido, **0.12 xG por tiro** (Ortiz 0.10, Solari 0.08), 65 % de los tiros en el área. Origen del xG: 26 % juego posicional, 38 % transición, 37 % balón parado (definición del marco: toda la posesión que abre el saque propio de un córner o un tiro libre). Jugada distintiva: **pase atrás al área, 15 % del xG** (Ortiz 10 %, Solari 8 %); centro 17 % (Solari 28 %).
- [x] **Red de pases** (`red_pases.png`): 4-2-3-1 más usado (41 de 91 partidos), hasta el primer cambio. El balón pasa por el doble pivote Fidalgo (28 pases por partido) y Jonathan dos Santos (27); su conexión es la más usada (21 por partido); el juego se carga a la izquierda (56 % de los pases del 11).

### 3.3 Sin balón: ¿dónde y cómo recupera? ✅ (29 sep, salvo 360 → §3.4)
- [x] **Recuperación** (`recuperaciones.png`): Jardine no roba más arriba que sus antecesores: 52 recuperaciones por partido, altura media 42 yd (Solari 43, Ortiz 42), 24 % en campo rival (igual que ellos). Su zona de robo es el centro de su campo, delante del área (6.4 por partido).
- [x] **Presión frente a la liga** (`presion_liga.png`, comparación contra la media de la liga **en el mismo torneo**, 70 técnicos-club con ≥ 15 partidos): Jardine no asfixia (PPDA 1.9 pases por encima de la liga, 11.º más alto de 70; Ortiz −0.6), pero cuando presiona lo hace arriba (+1.7 puntos de presiones en campo rival, percentil 71) y recupera algo más tras perder (+0.2 por partido, percentil 74) aunque contrapresiona menos (−2.3 por partido).
- [x] **Transiciones** (`transiciones.png`): gana el intercambio: 20.6 a favor por partido (0.57 xG) frente a 18.1 del rival (0.31 xG): 1.8 veces más peligro a favor (Ortiz 1.7, Solari 0.9). Llegan en ~6 s. Concede 0.89 tiros de contraataque por partido, 14.º que menos de 70 técnicos. El % de pérdidas recuperadas en ≤ 5 s (marco) no distingue a los tres técnicos (13–15 %).

### 3.4 360: ¿qué tan alto y qué tan junto defiende? ✅ (29 sep)
Notebook 05 §3.4 con `story.rival_open_play_passes`, `defensive_shape`, `shape_summary`, `match_level_diff`; figura `forma_bloque.png`; agregados `story_forma_*.parquet`. Supuestos nuevos en `ASSUMPTIONS`: `shape_line_players` (4), `shape_block_players` (8), `shape_min_visible` (8), `shape_min_behind_yd` (5). Solo hay 360 del América: la comparación es entre técnicos.
- [x] **Altura y compactación por fase** (pases rivales de juego abierto; fase por la altura del balón con los umbrales de presión del marco). En bloque medio, la última línea de Jardine está a **32 yd** de su portería (Ortiz 34, Solari 33; −1.7 yd por partido frente a Ortiz, IC 90 % −2.6 a −0.8) y su bloque mide **20 yd** (Ortiz 23; −2.1 yd, IC 90 % −2.7 a −1.5). En bloque bajo junta a sus 8 en 15 yd (Ortiz 18, Solari 15). El ancho no distingue a los técnicos (~41 yd).
- [x] **Posesión rival frente a tras pérdida**: tras perder, la línea de Jardine queda en 40 yd (Ortiz 45), pero porque pierde el balón más atrás (54 frente a 59 yd): la distancia balón–línea es casi la misma (12 frente a 11 yd). Lectura: **no adelanta la defensa para asfixiar, la junta** (coherente con la presión media de §3.3).
- [x] **Límite declarado**: 89 % de los pases rivales tiene 360, pero solo 32 % da un frame útil (≥ 8 jugadores de campo visibles y la toma ve ≥ 5 yd detrás del último); en bloque alto, 16 % (la cámara sigue al balón). Líneas por orden de profundidad (4 + 4), no por posición nominal.
- [ ] ⚪ Pases que rompen líneas (no entró; queda en §8).

### 3.5 Contexto: ¿cómo ajusta según el rival, el marcador, la localía y el minuto? ✅ (5 oct)
Notebook 05 §3.5: `story.game_state_effect` (tramos de 15', efecto fijo del partido, IC 90 % por partido), `context_metrics`, `minute_profile`; figuras `contexto_marcador.png`, `contexto_rival.png`; agregados `story_contexto_*.parquet`.
- [x] **Marcador** (Jardine, mismo partido frente al empate): perdiendo por 1, field tilt **+8** y posesión **+11**, PPDA −6.7 (presiona más); ganando por 1, la posesión casi no cambia (−3) pero el field tilt baja **−17** (Ortiz −18): guarda el balón lejos del área rival. *Sustituye al "+9 / −13" de T2, que mezclaba técnicos sin efecto fijo.*
- [x] **Rival**: débil → 61 % de posesión, PPDA 12, 2.06 xG por 100 posesiones; fuerte → 49 %, 19, 1.15: cede balón y presiona menos.
- [x] **Localía**: field tilt 62 % frente a 57 %; 44 % frente a 38 % de acciones defensivas en campo rival; 2.27 frente a 1.61 puntos por partido.
- Ojo: el PPDA crudo sube con la liga → solo comparar dentro de cada técnico.

### 3.6 Evolución: ¿qué cambió cuando llegó Jardine? ✅ (5 oct)
Notebook 05 §3.6: `story.adn_by_coach_torneo` (ADN por torneo, z por torneo, percentil de liga), `coach_changes`; figura `evolucion_adn.png` (validación y prueba punteadas).
- [x] Ortiz → Jardine: control del balón se mantiene (93 → 90); **presión alta −49** y reacción tras pérdida −25 puntos de percentil: menos persecución, más orden.
- [x] Identidad estable en sus 4 torneos: control ≥ 77, peligro ≥ 86, llegada ≥ 86. La presión sí evoluciona: percentil 17 (Ap 2023) → 81 (Cl 2025).
- [x] Epílogo Almada (prueba): presión alta +49, solidez −31, balón parado +25 → el estilo sigue al técnico.

### 3.7 Jugadores: ¿quién hace funcionar el sistema? ✅ (5 oct)
Notebook 05 §3.7; figuras `jugadores_uso.png`, `jugadores_obv.png`, `jugadores_roles.png`, `cambios.png`; agregados `story_jugadores_*`, `story_cambios_*`.
- [x] **Uso**: 3.6 titulares cambian de un partido al siguiente (Ortiz 2.4); 79 onces distintos en 91 partidos, 47 jugadores; núcleo de 8 con ≥ 50 % de los minutos (Malagón, Fidalgo, Zendejas, Israel Reyes, Henry Martín, Jonathan dos Santos, Ramón Juárez, Kevin Álvarez). 4-2-3-1 en 45 %.
- [x] **Valor**: top 3 = 62 % del OBV positivo (mediana por partido), defensas y carrileros 32 %. Fidalgo 11.1 %, Malagón 9.1 %, Zendejas 7.4 % de la era.
- [x] **Roles U3**: Defensor de corte 37 % (Israel Reyes) · Delantero de área 27 % (Henry Martín) · Mediocentro organizador 17 % (Fidalgo) · Extremo que encara 13 % (Brian Rodríguez) · Creador del último pase 7 % (Valdés).
- [x] **Sustituciones**: primer cambio en el descanso en 26 % de los partidos (Ortiz 13 %, Solari 11 %); perdiendo 9.1 cambios por 90' frente a 7.6 ganando; perdiendo, 38 % más ofensivos; ganando, 34 % más defensivos.

### 3.8 Balón parado: ¿cómo ataca y cómo defiende las jugadas a balón parado? ✅ (29 sep)
Agregado de toda la era en la ventana (notebook 05 §3.8). Funciones: `story.set_piece_plays` (solo jugadas que abre el saque de quien la tiene: descarta posesiones que heredan el `play_pattern`), `set_piece_shots`, `set_piece_summary`, `delivery_summary`, `shot_zone_summary`, `set_piece_xg_share`, `corner_defense`, `marking_vs_chance`; figuras `balon_parado.png` y `balon_parado_defensa.png`; agregados `story_bp_*.parquet`. Supuestos nuevos: `set_piece_free_kick_x_min` (80), `set_piece_marking_yd` (2), `set_piece_min_box_visible` (0.9).
- [x] **A favor**: Jardine juega en corto el **25 %** de sus córners (Ortiz 13 %, Solari 9 %) y, cuando centra, apunta al punto de penal (38 %) más que al área chica (16 %; Ortiz 27 %). 5.0 córners por partido, 36 % termina en tiro, **0.039 xG por córner** (Ortiz 0.034; +0.006 frente a la liga de su torneo, 16.º de 70). Tiros libres del último tercio: 2.5 por partido, 40 % con tiro; saques de banda del último tercio: 7.1 por partido, 11 % con tiro. Total: 0.40 xG y 35 goles a balón parado en 91 partidos; 35 % de ese xG se remata en el área chica.
- [x] **Las dos cifras de xG a balón parado**: marco (toda la posesión que abre el saque propio de un córner o un tiro libre, en cualquier zona) = **37 %** del xG sin penales (40 % antes de ajustar la definición, §2); jugadas de §3.8 (córners + último tercio, toda la jugada) = 26 %; **solo el remate directo del envío = 7 %** (Ortiz 10 %, Solari 14 %). La mayor parte del peligro es la segunda jugada.
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

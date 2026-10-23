# Textos del reporte final · La historia de Jardine

> Fuente única de texto del reporte HTML (§5) y del guion del video (§7).
> Regla: **primero el fútbol, después el número; el método va plegado.**
> Toda cifra sale de la **ventana oficial** (Ap 2021 – Cl 2025: Jardine 91 · Ortiz 55 · Solari 27 partidos), salvo donde dice *validación* o *prueba*.
> Hallazgos con sus cifras exactas en `data/gold/analysis/story_hallazgos.parquet` (notebook 05) y `coach_*.parquet` (notebook 04).
>
> Formato por sección: `pregunta` · `hallazgo` · `lectura` · `figuras`.

---

## resumen · El América de Jardine en una pantalla

**El América de Jardine quiere el balón, lo saca jugando, ataca por fuera y defiende junto, no arriba. Y cambia el plan según el marcador.**

En 91 partidos (tricampeón Ap 2023 – Ap 2024) su ADN fue el que mejor encajó con la identidad del club: **Índice de Encaje 99 de 100**, el n.º 1 de 70 técnicos de la Liga MX.

Lo medimos con un método que sirve para **cualquier técnico de la liga**:
- el **ADN del Entrenador**: 8 rasgos comparados con la liga del mismo torneo y ajustados por rival y localía;
- el **Índice de Encaje**: qué tan cerca está un técnico de la identidad del club.

Ese mismo ADN reconoce el estilo de Almada en sus primeros 9 partidos: el estilo sigue al técnico, no a la plantilla.

**Por qué importa:** en la Liga MX hubo 104 cambios de técnico entre 2021 y 2025, y 7 de cada 10 técnicos no duran ni dos torneos. Elegir mal un técnico es caro; esta herramienta ayuda a elegir con datos (§4).

---

## 3.1 · Jardine en 5 ideas

1. **Quiere el balón y lo saca jugando.**
   - Saca en corto el **45 %** de sus saques de meta (Ortiz 31 %, Solari 33 %).
   - Un mediocentro baja a recibir el **44 %** de las veces (Ortiz 20 %).
   - Control del balón: **90 de 100** frente a los técnicos de la liga.
   - *Figuras:* `salida_saque_meta.png`.
2. **Progresa por dentro, entra por fuera y tira mejor, no más.**
   - El 42 % de sus pases progresivos van por el centro, pero llega al último tercio sobre todo por las bandas: izquierda 21.1 y derecha 17.9 por partido, frente a 9.3 por el centro.
   - Tira **0.12 xG por tiro** (Ortiz 0.10, Solari 0.08).
   - Su jugada distintiva es **el pase atrás al área: 15 % de su xG**.
   - *Figuras:* `progresion_carriles.png`, `pase_previo.png`.
3. **No asfixia, se junta.**
   - Deja 1.9 pases más que la liga antes de intentar robar (PPDA, el 11.º más alto de 70).
   - Su bloque mide **20 yd** (Ortiz 23).
   - Gana el intercambio de transiciones: **1.8 veces más peligro a favor que en contra**.
   - *Figuras:* `presion_liga.png`, `forma_bloque.png`, `transiciones.png`.
4. **El balón parado es un arma, sobre todo la segunda jugada.**
   - Juega en corto el **25 %** de sus córners (Ortiz 13 %).
   - El balón parado genera el 37 % de su xG, pero solo el 7 % es el remate directo del envío: el peligro está en lo que viene después.
   - *Figuras:* `balon_parado.png`.
5. **Lee el partido.**
   - Perdiendo por 1, inclina la cancha **+8** puntos y tiene **+11** de posesión.
   - Ganando por 1, **guarda el balón lejos del área** (field tilt −17).
   - Hace su primer cambio en el descanso en el **26 %** de los partidos, el doble que sus antecesores.
   - *Figuras:* `contexto_marcador.png`, `cambios.png`.

---

## 3.2a · Con balón: ¿cómo sale desde atrás?
- **Pregunta:** ¿Cómo sale el América desde atrás?
- **Hallazgo:** Jardine saca en corto el **45 %** de sus saques de meta (Ortiz 31 %, Solari 33 %). El pase corto lo recibe un **mediocentro que baja en el 44 %** de los casos (Ortiz 20 %, Solari 4 %, que se la daban casi siempre a un central).
- **Lectura:** es una idea de control, no un atajo al gol. 66 % de esas salidas llega a campo rival y producen el mismo peligro que el saque largo (0.7 xG por cada 100 salidas).
- **Figuras:** `salida_saque_meta.png`

## 3.2b · Con balón: ¿por dónde progresa?
- **Pregunta:** ¿Por dónde avanza el América?
- **Hallazgo:**
  - **Progresa por dentro y entra por fuera.** El 42 % de los pases progresivos termina en el carril central, pero al último tercio entra 21.1 veces por partido por la izquierda y 17.9 por la derecha, frente a 9.3 por el centro.
  - Pisa el área **14.7 veces por partido**, como Ortiz (15.0) y 48 % más que Solari (9.9).
- **Lectura:** atrae al rival al centro y lo ataca por las bandas. El 41 % de las veces entra al área conduciendo.
- **Figuras:** `progresion_carriles.png`, `entradas_area.png`

## 3.2c · Con balón: ¿cómo genera ocasiones?
- **Pregunta:** ¿Cómo crea peligro el América?
- **Hallazgo:**
  - **No tira más, tira mejor**: 13.2 tiros y 1.52 xG por partido sin penales, **0.12 xG por tiro** (Ortiz 0.10, Solari 0.08), con 65 % de los tiros dentro del área.
  - Origen del xG: 26 % juego posicional, 38 % transición, 37 % balón parado.
- **Lectura:** su jugada distintiva es **el pase atrás al área: 15 % del xG** (Ortiz 10 %, Solari 8 %). El centro pesa menos que con Solari (17 % frente a 28 %).
- **Figuras:** `tiros_origen.png`, `pase_previo.png`

## 3.2d · Con balón: ¿quién conecta con quién?
- **Pregunta:** ¿Por dónde pasa el balón en el 11 de Jardine?
- **Hallazgo:**
  - En su 4-2-3-1 más usado (41 de 91 partidos), el balón pasa por el **doble pivote**: Fidalgo da 28 pases por partido y Jonathan dos Santos 27.
  - Su conexión es la más usada (21 pases por partido).
  - El juego se carga a la izquierda: 56 % de los pases del 11.
- **Lectura:** Fidalgo es el reloj del equipo (§3.7: el que más valor genera).
- **Figuras:** `red_pases.png`

## 3.3a · Sin balón: ¿dónde recupera?
- **Pregunta:** ¿Dónde recupera el balón el América?
- **Hallazgo:**
  - Jardine **no roba más arriba** que sus antecesores: 52 recuperaciones por partido a 42 yd de su portería (Solari 43, Ortiz 42) y 24 % en campo rival.
  - Su zona de robo es **el centro de su campo, delante del área**.
- **Lectura:** espera y roba en su mitad. El 40 % de lo que recupera se convierte en transición.
- **Figuras:** `recuperaciones.png`

## 3.3b · Sin balón: ¿presiona más o menos que la liga?
- **Pregunta:** ¿Presiona más o menos que la liga?
- **Hallazgo:**
  - **No asfixia**: deja dar 1.9 pases más que la media de su torneo antes de intentar robar (PPDA; el 11.º más alto de 70 técnicos). Ortiz presionaba más que la liga.
  - Cuando presiona, lo hace arriba: tiene más presiones en campo rival que 71 de cada 100 técnicos.
- **Lectura:** presión media y selectiva: elige cuándo saltar.
- **Figuras:** `presion_liga.png`

## 3.3c · Sin balón: ¿cómo le va en las transiciones?
- **Pregunta:** ¿Quién gana las transiciones?
- **Hallazgo:**
  - Gana el intercambio: **20.6 transiciones a favor por partido (0.57 xG) frente a 18.1 del rival (0.31 xG)**, 1.8 veces más peligro a favor (Ortiz 1.7, Solari 0.9).
  - Concede 0.89 tiros de contragolpe por partido, el 14.º que menos de 70 técnicos.
- **Lectura:** al defender junto, el rival casi no le hace daño a la contra, y él sí.
- **Figuras:** `transiciones.png`

## 3.4 · 360: ¿qué tan alto y qué tan junto defiende?
- **Pregunta:** ¿Qué tan alto y qué tan junto defiende el América?
- **Hallazgo:**
  - En bloque medio, su última línea está a **32 yd** de su portería (Ortiz 34) y su bloque mide **20 yd** (Ortiz 23; −2.1 yd por partido, IC 90 % −2.7 a −1.5).
  - En bloque bajo junta a sus 8 jugadores en 15 yd.
- **Lectura:** **no adelanta la defensa para asfixiar, la junta**. Es coherente con su presión media.
- **Límite:** las cifras solo cuentan lo que capta la cámara, y solo 32 % de los pases rivales dan una imagen útil.
- **Figuras:** `forma_bloque.png`

## 3.5a · Contexto: ¿cómo cambia el plan con el marcador?
- **Pregunta:** ¿Qué hace cuando pierde y qué hace cuando gana?
- **Hallazgo:**
  - Comparado con el **mismo partido empatado**: perdiendo por un gol, el América de Jardine inclina la cancha **+8 puntos** (field tilt) y tiene **+11 de posesión**, y presiona más.
  - Ganando por uno, la posesión casi no cambia (−3), pero el field tilt baja **−17**.
- **Lectura:** cuando gana no se encierra sin balón: **lo guarda lejos del área rival** y controla el partido en vez de buscar el segundo.
- **Método (plegado):** tramos de 15'; efecto fijo del partido; IC 90 % con errores agrupados por partido. Describe, no predice.
- **Figuras:** `contexto_marcador.png`

## 3.5b · Contexto: ¿juega igual contra fuertes y débiles, de local y de visita?
- **Pregunta:** ¿Cambia según el rival y la cancha?
- **Hallazgo:**
  - **El rival manda más que la localía.** Contra débiles tiene 61 % de posesión; contra fuertes, 49 %, presiona menos y su peligro cae de 2.06 a 1.15 xG por cada 100 posesiones.
  - De local inclina más la cancha (62 % frente a 57 %) y presiona más arriba: 44 % de sus acciones defensivas en campo rival, frente a 38 % de visita.
- **Lectura:** contra los grandes cede el balón. Suma 2.27 puntos por partido en casa y 1.61 fuera.
- **Figuras:** `contexto_rival.png`

## 3.6 · Evolución: ¿qué cambió cuando llegó Jardine?
- **Pregunta:** ¿Qué cambió con cada técnico?
- **Hallazgo:**
  - Jardine heredó un equipo que ya tenía el balón (control: Ortiz percentil 93, Jardine 90) y cambió **cómo defiende**: la presión alta baja **49 puntos de percentil** y la reacción tras pérdida, 25.
  - Su identidad es estable en sus 4 torneos: control del balón ≥ percentil 77, peligro ≥ 86, llegada ≥ 86.
  - Lo que evoluciona es la presión: del percentil 17 en su primer torneo al **81** en el Cl 2025.
- **Lectura:** menos persecución y más orden, con un equipo que aprende a presionar con el tiempo.
- **Epílogo (2026, prueba):** con la misma plantilla, Almada sube la presión alta **+49** y la solidez defensiva cae **−31**. **El estilo sigue al técnico, no a la plantilla.**
- **Figuras:** `evolucion_adn.png`

## 3.7a · Jugadores: ¿con quién juega y cuánto rota?
- **Pregunta:** ¿Con quién juega Jardine?
- **Hallazgo:**
  - Rota más que Ortiz: cambia 3.6 titulares de un partido al siguiente (Ortiz 2.4) y usó 79 onces distintos en 91 partidos.
  - Tiene un **núcleo de confianza de 8**, jugadores con más de la mitad de los minutos: Malagón, Fidalgo, Zendejas, Israel Reyes, Henry Martín, Jonathan dos Santos, Ramón Juárez y Kevin Álvarez.
- **Lectura:** rota alrededor de una columna fija.
- **Figuras:** `jugadores_uso.png`

## 3.7b · Jugadores: ¿quién genera el valor?
- **Pregunta:** ¿Quién hace funcionar el sistema?
- **Hallazgo:**
  - En el partido mediano, los 3 mejores generan **62 %** del valor con balón (Solari 66 %), y defensas y carrileros el **32 %**.
  - Los que más valor suman en la era son Fidalgo (11.1 %), Malagón (9.1 %) y Zendejas (7.4 %).
- **Lectura:** el juego está repartido y se construye desde atrás, hasta con el portero.
- **Figuras:** `jugadores_obv.png`

## 3.7c · Jugadores: ¿qué roles tiene el sistema?
- **Pregunta:** ¿Qué papel cumple cada uno?
- **Hallazgo:** cinco roles, sacados de lo que hace cada jugador por 90':
  - **Defensor de corte**: 37 % de los partidos (Israel Reyes, Ramón Juárez).
  - **Delantero de área**: 27 % (Henry Martín).
  - **Mediocentro organizador**: 17 % (Fidalgo, Jonathan dos Santos).
  - **Extremo que encara**: 13 % (Brian Rodríguez).
  - **Creador del último pase**: 7 % (Diego Valdés).
- **Lectura:** un solo organizador real sostiene el sistema. Por eso su relevo es la pieza más sensible del plantel.
- **Figuras:** `jugadores_roles.png`

## 3.7d · Jugadores: ¿cómo mueve el banco?
- **Pregunta:** ¿Cuándo y para qué cambia?
- **Hallazgo:**
  - Interviene antes: hace el primer cambio en el descanso en el **26 %** de los partidos (Ortiz 13 %, Solari 11 %).
  - Perdiendo cambia más (9.1 cambios por cada 90' frente a 7.6 ganando) y el **38 %** de esos cambios mete un perfil más ofensivo.
  - Ganando, el **34 %** de los cambios mete a alguien más defensivo.
- **Lectura:** usa el banco para corregir pronto, no solo para refrescar. Es descriptivo: no mide si el cambio funcionó.
- **Figuras:** `cambios.png`

## 3.8a · Balón parado a favor
- **Pregunta:** ¿Cómo ataca el balón parado?
- **Hallazgo:**
  - Juega en corto el **25 %** de sus córners (Ortiz 13 %, Solari 9 %), y cuando centra apunta al punto de penal.
  - Cada córner vale **0.039 xG**, el 16.º mejor de 70 técnicos.
  - El balón parado da el 37 % de su xG, pero **solo el 7 % es el remate directo** del envío.
- **Lectura:** el peligro está en **la segunda jugada**.
- **Figuras:** `balon_parado.png`

## 3.8b · Balón parado en contra
- **Pregunta:** ¿Cómo defiende el balón parado?
- **Hallazgo:**
  - Concede 0.30 xG por partido a balón parado, y lo que más le cuesta es el córner: concede 0.003 xG más por córner que la liga (49.º de 70).
  - Zona vulnerable: **la zona de penal** (52 % del xG en contra); en córners, **el primer palo** (53 %).
  - Con 360 en el saque: 9 defensores en el área y 41 % pegados a un rival, frente a 24 % por azar. Es un **esquema mixto**: base zonal más marcas individuales.
- **Lectura:** el primer palo es la puerta de entrada.
- **Figuras:** `balon_parado.png`, `balon_parado_defensa.png`

---

## 3.9 · ¿Se sostiene el ADN? (probado con partidos que el modelo nunca vio)

- **Cómo lo probamos.** El ADN se calculó **solo** con la ventana oficial (Ap 2021 – Cl 2025). Después le dimos partidos que nunca vio:
  - **validación**: Apertura 2025, 19 partidos de Jardine;
  - **prueba**: 2026, el Clausura de Jardine y los primeros 9 partidos de Almada.

  A cada partido le preguntamos al modelo *"¿qué técnico de la liga juega así?"*.
- **Resultados:**
  - **Almada**: el modelo lo reconoce en el América sin haberlo visto ahí. Queda en la **posición mediana 2 de 31** técnicos posibles.
  - **Prueba**: el técnico correcto está entre los 5 primeros en el **31 %** de los partidos, frente a 16 % por azar.
  - **Validación**: 23 % frente a 16 %. Es una señal más débil, y la contamos así, sin inflarla.
  - **Jardine después de la ventana**: en el Ap 2025 mantiene su identidad (control 84, llegada 93, solidez 99). En el Cl 2026 su peligro generado cae al percentil 19.
- **Lectura:** el ADN no es una foto de un torneo. **Distingue técnicos en partidos nuevos** y sigue al técnico cuando cambia de plantilla.
- **Figuras:** `coach/cambio_tecnico.png`, `story/evolucion_adn.png`

## 3.10 · Hipótesis → veredicto (versión corta)

| | Hipótesis | Evidencia | Veredicto |
|---|---|---|---|
| H1 | Cada técnico tiene un ADN distinguible | Top-5 en prueba 31 % frente a 16 % por azar | ✅ se sostiene |
| H2 | Hay rasgos del club y rasgos del técnico | Del club: solidez defensiva y balón parado; el resto cambia con el técnico | ✅ se sostiene |
| H3 | Jardine se adapta al rival más que Solari y Ortiz | Ajuste fuerte − débil: Jardine 2.93, Solari 2.78, Ortiz 1.56 | ✅ leve |
| H9 | El ADN reconoce a un técnico que nunca vio en el club | Almada: posición mediana 2 de 31 | ✅ se sostiene |
| H10 | El Índice de Encaje ordena a los técnicos | Top 3: Jardine (América), Paiva (Toluca), Ortiz (América) | ✅ se sostiene |

---

## 3.11 · Recomendaciones

**Para el cuerpo técnico**
1. **Asegurar el relevo del organizador.** Fidalgo genera el 11 % del valor del equipo y es el eje de la red de pases. Solo Richard Sánchez y Jonathan dos Santos han cumplido ese rol (62 % y 58 % de sus partidos). Planificar su minutaje y un plan B para la salida corta.
2. **Cerrar el primer palo en córners.** De ahí sale el 53 % del xG que concede en córners, y por córner concede más que la liga (49.º de 70). Ajustar la base zonal del área chica hacia el primer palo.
3. **Seguir cargando la izquierda y el pase atrás.** La izquierda mueve el 56 % de los pases del 11, y el pase atrás al área da el 15 % del xG. Son señas de identidad; conviene entrenar la llegada al punto de penal.
4. **Un plan para los partidos grandes.** Contra rivales fuertes el peligro cae casi a la mitad (2.06 → 1.15 xG por cada 100 posesiones). Su ventaja está en las transiciones (1.8 veces más peligro a favor): ceder el balón con un plan de contragolpe, no solo por resistir.

**Para la dirección deportiva**
5. **Elegir técnico con el Índice de Encaje.** Los rasgos que se quedan en el club, gane quien gane, son la solidez defensiva y el balón parado.
   - Con Almada, el balón parado se mantiene (percentil 99), pero **la solidez cae al percentil 67** (Jardine 98). Es la primera alerta que el ADN da en la prueba de 2026.
   - Los perfiles más cercanos a la identidad del club en la liga son Renato Paiva (97), Antonio Mohamed (94) y Víctor Vucetich (93).
   - El ADN también sirve para revisar cada jornada si el técnico en turno se aleja de la identidad que se quiere.

---

## 7 · Guion del video (máximo 5 min)

> **Cómo se arma.** Voz A y Voz B mandan **una nota de voz por bloque** con el texto exacto de abajo. Pau narra sus bloques (los que van pegados a la pantalla: la demo) y graba la pantalla siguiendo cada audio.
> Cada bloque de A y B se apoya en **una sola gráfica**, así que la toma de pantalla se alarga o se recorta al largo del audio sin que se note.
> Meta: **4:45 en total**. Si nos pasamos de 4:50, quitamos lo marcado como *[recortable]* (unos 15 s).
> Cifras: las del reporte (ventana Ap 2021 – Cl 2025), salvo el bloque 9 y la demo, que usan 2025–26.

### Reparto

| Bloque | Qué | Voz | Duración |
|---|---|---|---|
| 1 | El problema | Pau | 20 s |
| 2 | Cómo lo hicimos | Pau | 38 s |
| 3 | Idea 1 · El ADN del club | A | 22 s |
| 4 | Idea 2 · Lo que puso Jardine | A | 30 s |
| 5 | Idea 3 · Lee el partido | A | 15 s |
| 6 | Idea 4 · El ADN ganador | B | 37 s |
| 7 | Idea 5 · Puntos críticos | B | 20 s |
| 8 | Recomendaciones | B | 43 s |
| 9 | ¿Se sostiene? | A | 25 s |
| 10 | Demo de la app | Pau | 32 s |
| 11 | Cierre | Pau | 16 s |

Cada voz suma más o menos lo mismo: A unos 1:30, B unos 1:40 y Pau unos 1:45. Si alguien no alcanza a mandar su audio, Pau lo graba: el texto funciona con cualquier voz.

### Cómo grabar tu nota de voz (A y B)

- **Una nota por bloque**, en orden (3, 4, 5, 9 o 6, 7, 8). No digas el número del bloque en el audio.
- Cuarto cerrado y sin eco (un clóset con ropa es ideal). Celular a un palmo de la boca, sin altavoz y sin audífonos con micrófono de cable suelto.
- Un segundo de silencio antes y después de hablar.
- Lee **con calma**, como si se lo contaras a alguien que no vio los partidos. Si te equivocas, repite la nota completa.
- Mándalas **como documento** (WhatsApp → adjuntar → documento), no como nota de voz, para que no pierdan calidad. Si solo puedes como nota de voz, también sirve.
- Las cifras se dicen así: "0.12" = "cero punto doce"; "4-4-2" = "cuatro, cuatro, dos"; "1.41" = "uno punto cuarenta y uno".

### Bloques

**Bloque 1 · El problema · Pau · 20 s**
- *Pantalla:* portada del reporte (título y autores) → bajar a "¿Por qué importa?".
- *Pistas:* al decir "104 cambios", el recuadro de cifras ya debe estar a la vista.

> Entre 2021 y 2025 hubo 104 cambios de técnico en la Liga MX, y siete de cada diez técnicos no completan dos torneos en su equipo. André Jardine ganó tres seguidos con el América. Nos preguntamos: ¿cómo juega su América, qué es del club, qué es suyo y qué lo hizo campeón?

**Bloque 2 · Cómo lo hicimos · Pau · 38 s**
- *Pantalla:* sección 8, "De dónde tomamos las ideas" (las 4 tarjetas) → "Cómo lo hicimos" (los 5 pasos).
- *Pistas:* "béisbol" → cursor en la tarjeta de béisbol; "ensayo clínico" → tarjeta de medicina; "el partido empatado" → paso 4 del flujo.

> Usamos los eventos y el 360 de StatsBomb (dónde estaba cada jugador en cada acción) de 175 partidos del América, y las estadísticas de toda la liga. Tomamos ideas de otras disciplinas. El béisbol ajusta sus estadísticas por estadio y por época; nosotros comparamos cada rasgo con la liga del mismo torneo y descontamos rival y localía. Como en un ensayo clínico, comparamos contra casos parecidos: el mismo técnico, el mismo nivel de rival y, para el plan de juego, el partido empatado. Así no confundimos el estilo con el marcador.

**Bloque 3 · Idea 1: el ADN del club · Voz A · 22 s**
- *Pantalla:* sección 1, el radar con su "Lo que muestra" visible.
- *Pistas:* "más balón y más peligro" → cursor recorre control, peligro y solidez; "la presión" → cursor en presión alta, sobre Ortiz y luego sobre Jardine.

> Primero: el América tiene un ADN que no depende del técnico. Con Solari, Ortiz y Jardine tuvo más balón y más peligro, y concedió menos que la liga. Eso es del club. Lo que cambia con cada técnico es la presión: Ortiz presionaba arriba como pocos, 86 de 100; Jardine, 37, por debajo del técnico típico.

**Bloque 4 · Idea 2: lo que puso Jardine · Voz A · 30 s**
- *Pantalla:* sección 2, gráfica de tipos de gol → mapas de ocasiones y robos.
- *Pistas:* "sale jugando" → tipos de gol; "sin balón no asfixia" → mapa de robos (la zona oscura en su mitad).

> Segundo: sobre esa base, Jardine sale jugando: saca en corto el 45 % de sus saques de meta, contra 31 % de Ortiz. No tira más, tira mejor. Sin balón no asfixia: espera y se junta. Con el 360 medimos su bloque: 20 yardas de largo, tres menos que Ortiz. Y gana las transiciones: genera casi el doble de peligro al contragolpe del que concede.

**Bloque 5 · Idea 3: lee el partido · Voz A · 15 s**
- *Pantalla:* sección 3, gráfica del marcador.
- *Pistas:* "perdiendo por un gol" → fila "pierde por 1"; "ganando por uno" → fila "gana por 1".

> Tercero: lee el partido. Perdiendo por un gol, empuja: más balón y más campo rival. Ganando por uno, guarda el balón lejos del área en vez de buscar el segundo.

**Bloque 6 · Idea 4: el ADN ganador · Voz B · 37 s** ⭐
- *Pantalla:* sección 4, gráfica por torneo → gráfica de series.
- *Pistas:* "15 series" → cursor sobre las estrellas; "Ortiz" → cambiar a la gráfica de series y pasar el cursor por los puntos vacíos de abajo; "finales" → regresar al texto de las finales.

> Cuarto, lo que más nos sorprendió: en liguilla, el campeón juega de copa. En las 15 series que el América pasó, dejó dar al rival 19 pases antes de presionar; en las 5 que perdió, 10. Ninguna serie perdida pasa de 13. Ortiz perdió sus tres semifinales presionando como nunca *[recortable: y en dos tuvo ocasiones iguales o mejores que el rival]*. Y Jardine ganó las finales de 2024 con menos de la mitad del balón; la que perdió, contra Toluca, la jugó dominando.

**Bloque 7 · Idea 5: puntos críticos · Voz B · 20 s**
- *Pantalla:* sección 5, gráfica por minuto (tramo sombreado) → gráfica de dibujos contra rivales fuertes.
- *Pistas:* "del minuto 30 al descanso" → cursor en el pico naranja del tramo sombreado; "tres centrales" → segunda gráfica.

> Quinto: dónde se le escapan los partidos. Del minuto 30 al descanso le generan 1.41 goles esperados por cada 90 minutos; al volver del descanso, 0.89. Y la línea de tres centrales que usó contra los grandes no lo protege: cede el balón y concede más tiros.

**Bloque 8 · Recomendaciones · Voz B · 43 s**
- *Pantalla:* sección 6, las 4 tarjetas; bajar una por una con zoom en "Cómo medirlo".
- *Pistas:* "Uno", "Dos", "Tres", "Cuatro" → una tarjeta cada vez.

> Cada hallazgo se vuelve una decisión con un indicador para seguirla. Uno: en liguilla, esperar en vez de asfixiar. La meta es dejar dar 15 pases o más antes de presionar, no tener el balón. Dos: contra los grandes, 4-4-2 en lugar de tres centrales; se mide con las llegadas al área y las ocasiones en contra. Tres: un ajuste desde el minuto 30, no solo en el descanso; se mide con lo que concede entre el 30 y el 45. Cuatro: cerrar el primer palo en los córners, de donde nace la mitad del peligro que concede, y preparar un relevo para Fidalgo, el organizador.

**Bloque 9 · ¿Se sostiene? · Voz A · 25 s**
- *Pantalla:* sección 7, tabla "Lo que probamos y no cambia el resultado" → sección 8, primer párrafo de "Nuestro aporte".
- *Pistas:* "mejores jugadores" → fila "Cuando ganó tenía mejores jugadores".

> No todo lo que probamos se sostuvo, y también lo publicamos: son diez ideas que no cambian el resultado. Por ejemplo, Jardine no ganó por tener mejores jugadores: el once de Ortiz en sus semifinales aportaba lo mismo o más. Y el ADN funciona en partidos nuevos: en 2025–26 pone al técnico correcto entre los cinco más parecidos el doble de veces que el azar.

**Bloque 10 · Demo de la app · Pau · 38 s (máximo 42)**
- *Pantalla (app):* https://isac-hackathon-america-2rkgqdhmmyqxvkxnogcpci.streamlit.app/
  1. Jardine, toda su etapa, pestaña "El ADN": cursor por Técnico, Periodo y "Más filtros" (abrirlo: liguilla, localía, fuerza del rival); señalar "Cómo leerla".
  2. Pestaña "Sin balón" → gráfica "¿Cuánto vale robar en cada zona?".
  3. Pestaña "Puntos críticos" → gráfica de rivales; señalar Necaxa, abajo de la línea.
  4. Periodo "Un partido" → escribir "Dec 2024" → 13 Dec 2024 · vs Monterrey (2-1) → "¿Merecía el resultado?" (80 %).
  5. Periodo "Toda su etapa" (primero) → Técnico Almada (compara solo con Jardine) → pestaña "El ADN": presión alta y solidez defensiva.
- *Ojo:* abrir la app unos minutos antes para despertarla. No desplegar "Partidos del periodo" ni "Todos los indicadores".

> Todo esto vive en una app abierta. Elegimos técnico y periodo (toda su etapa, un torneo o un partido) y filtramos por liguilla, localía o fuerza del rival; cada gráfica se recalcula y explica cómo leerla. En «Sin balón» vemos cuánto vale robar en cada zona. En «Puntos críticos», contra quién sacó menos puntos de los que merecía, como Necaxa. Un solo partido: la ida de la final del Apertura 2024. Con sus ocasiones, el América la ganaba 8 de cada 10 veces. Y con Almada, casi la misma plantilla, la presión sube y la solidez baja: el estilo sigue al técnico.

**Bloque 11 · Cierre · Pau · 16 s**
- *Pantalla:* sección 8, Índice de Encaje → portada con los tres nombres y el enlace de la app.

> *[recortable: Para la dirección deportiva, el Índice de Encaje dice qué técnicos de la liga se parecen al ADN del club: hoy, Renato Paiva y Antonio Mohamed.]* Convertimos 175 partidos en una historia que cualquiera puede leer y en decisiones que se pueden medir. Gracias.

### Montaje (Pau)

1. **Juntar los audios** en una carpeta con nombres `03_A.m4a`, `04_A.m4a`… Si Clipchamp no abre algún audio de WhatsApp (.opus), convertirlo: `ffmpeg -i nota.opus nota.m4a`.
2. **Grabar los bloques de Pau** (1, 2, 10 y 11) con las mismas reglas de la nota de voz.
3. **Poner todos los audios en orden** en la línea de tiempo de Clipchamp. Ese es el esqueleto: la imagen se acomoda al audio, no al revés.
4. **Grabar la pantalla bloque por bloque** escuchando el audio en audífonos y siguiendo las *pistas*. La demo (bloque 10) se graba en vivo mientras se narra.
5. **Igualar el volumen** de las tres voces, porque cada celular graba distinto. Música muy baja o sin música.
6. **Subtítulos automáticos** en español y revisar las cifras a mano (los decimales y "4-4-2" suelen salir mal).
7. **Revisar antes de exportar:** dura menos de 5:00; no aparece código, notebooks ni tablas de datos; se leen las cifras en 1080p.

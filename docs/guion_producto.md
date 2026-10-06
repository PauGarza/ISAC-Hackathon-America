# Guion del producto · ADN del Entrenador · Club América

> **Para qué es este documento:** que cualquier persona del equipo entienda qué hace la app, de dónde sale cada número, qué decidimos, por qué, qué problemas encontramos y por qué el producto quedó como quedó.
> **Estado:** 5 oct 2026. Código en `src/`, app en `app/`, pendientes en `todo.md`.

---

## 1. En una frase

**Una página donde eliges un periodo del América (una etapa, un torneo, unas fechas o un partido) y ves cómo jugó el equipo y qué ideas tenía su técnico, comparado con otros técnicos y con la liga.**

Por defecto abre en la historia de André Jardine (2023–2025).

---

## 2. Cómo leímos el reto

El reto pregunta: **"¿cómo juega este entrenador?"**. Concretamente:
- qué principios definen al equipo con y sin balón;
- cómo se repiten o cambian con el tiempo;
- cómo ajusta el técnico según el rival, el marcador, la localía y el minuto.

La condición más importante: *alguien que no vio los partidos debe entenderlo*.

Lo tradujimos en tres ideas que guían todo el producto:

1. **Un estilo solo se ve comparando.** "Saca en corto el 45 %" no dice nada. "45 % frente a 31 % de Ortiz con casi la misma plantilla" sí. Por eso todo el producto compara: técnico contra técnico, contra la liga, y el mismo partido con distinto marcador.
2. **El estilo se ve en muchos partidos, no en uno.** Un partido suelto es mucho ruido. Por eso el producto parte de elegir un **periodo**, y siempre dice cuántos partidos hay detrás.
3. **Explicar, no predecir.** Es un producto de **visualización** para la marca y el club, no un modelo de pronóstico. Los modelos que hicimos solo sirvieron para comprobar, en privado, que lo que contamos es real.

> **Aparte, la rúbrica.** Los criterios de calificación hablan de IP, ROI, activación de marca y escalabilidad, y no encajan del todo con un reto táctico. Lo confirmamos en la junta con los organizadores (mar 6, 7 pm). Mientras tanto, la prioridad es el producto táctico.

---

## 3. Los datos

| Qué | Cuánto | Para qué |
|---|---|---|
| Eventos StatsBomb del América | 222 partidos (2021–2026), unas 3,500 acciones por partido | Todo lo táctico: salida, progresión, tiros, presión, balón parado |
| StatsBomb 360 | Los mismos 222 partidos | Posiciones de los jugadores en la toma: altura y compactación del bloque, marcaje en córners |
| Estadísticas por equipo y partido de **toda la Liga MX** | 1,789 partidos, 106 técnicos | El ADN: comparar al América con todos los técnicos de la liga |
| Alineaciones | Los 222 partidos | Sistemas, titulares, minutos, cambios |

**Periodo principal: Apertura 2021 – Clausura 2025**, 175 partidos (el periodo que fija el reto):

| Técnico | Partidos |
|---|---|
| Jardine | 91 |
| Ortiz | 55 |
| Solari | 27 |
| Cervantes (interino) | 2 |

Los partidos de 2025–2026 (Ap 2025 de Jardine, Cl 2026 de Jardine y los de Almada) se guardaron aparte para comprobar nuestras hipótesis (sección 8). En la app aparecen como "temporadas recientes".

**¿Por qué Jardine es el protagonista?** Tiene la muestra más grande (91 partidos), ganó el tricampeonato y tiene un "antes" claro (Solari y Ortiz) y un "después" (Almada, con casi la misma plantilla).

**Regla de datos:** se pueden mostrar resultados, **nunca datos crudos**. Esto marcó la arquitectura de la app (sección 10).

---

## 4. El marco analítico: definimos cada cosa una sola vez

El reto exige un marco: qué es cada objeto, qué supuestos usamos, coherencia interna y qué queda fuera. Lo resolvimos con **un solo archivo que define todo**: `src/framework.py`, con los umbrales en `ASSUMPTIONS`.

Ninguna figura, métrica ni pantalla de la app redefine nada. Si cambia una definición, cambia en todos lados.

### 4.1 La cancha

- **Medidas**: cancha StatsBomb de 120 × 80 yardas. El América siempre ataca hacia la derecha: x = 0 es su portería y x = 120 la rival.
- **Tercios**: propio (x < 40), medio (40–80) y último (x ≥ 80).
- **Carriles**: izquierdo, central y derecho, cada uno de un tercio del ancho.
- **Área rival**: x ≥ 102 y 18 ≤ y ≤ 62.
- **Zona de peligro**: x ≥ 90, frente al área.

### 4.2 Los objetos del juego

| Objeto | Definición | Por qué así |
|---|---|---|
| **Posesión** | La posesión de StatsBomb: termina cuando el otro equipo toma el control del balón | Es el estándar del proveedor; no inventamos una propia |
| **Secuencia ofensiva** | Posesión con **3 pases o más**, o que llega al último tercio | 3 es la mediana de pases por posesión (lo vimos en la exploración de datos) |
| **Construcción (salida)** | Posesión que **empieza en el tercio propio** (x < 40) en juego, desde saque de meta o del portero | Separa "sacar el balón desde atrás" del resto |
| **Progresión** | Posesión que empieza antes de la mitad (x < 60) y llega al último tercio (x ≥ 80) | Mide si el equipo logra cruzar el campo |
| **Pase (o conducción) progresivo** | Completo, de juego abierto, que **acorta 25 % o más** la distancia a la portería y termina en x ≥ 48 | Definición habitual en la industria; el umbral de x evita contar pases que solo "avanzan" en campo propio |
| **Pase largo** | 32 yardas o más (también en los saques de meta: corto, menos de 32) | Umbral que separa bien los dos tipos en los datos |
| **Recuperación** | Posesión propia que nace de un robo: recuperación, intercepción, duelo ganado, bloqueo o 50/50 | Es "dónde roba el balón" |
| **Transición ofensiva** | Recuperación que **llega al último tercio o a tiro en 15 segundos o menos** | Contragolpe es velocidad tras robar; 15 s deja fuera los ataques elaborados |
| **Transición defensiva / contrapresión** | Lo que pasa en los **5 segundos** después de perder el balón: presión inmediata y balones recuperados en ese tiempo | Los 5 s son la convención de la contrapresión ("reacción tras pérdida") |
| **Presión** | Altura de cada acción defensiva: **alta** si x ≥ 60 (campo rival), media de 40 a 60, baja si x < 40 | La mitad del campo es una frontera fácil de explicar |
| **PPDA** | Pases rivales en su 60 % del campo ÷ acciones defensivas propias (entradas, intercepciones, faltas) en nuestro 60 % alto. **Menos = presiona más** | Validado contra el PPDA de StatsBomb (correlación 0.96); probamos 4 conjuntos de acciones en 4 zonas |
| **Field tilt (dominio territorial)** | De todos los pases en el último tercio, el % que da el América | Dice quién vive en campo rival |
| **Balón parado** | Posesión que **abre el saque del propio equipo**: córner, tiro libre o saque de banda en el último tercio | Ver el reto 4 de la sección 9: corregimos el etiquetado de StatsBomb |
| **Marcador** | Diferencia de goles **antes** de cada acción, en 5 estados: pierde por 2+, pierde por 1, empate, gana por 1, gana por 2+ | "Antes" evita que el gol cuente en su propia jugada |
| **Fuerza del rival** | Puntos por partido del rival en sus **17 partidos previos** de liga, en tres niveles (débil, medio, fuerte) según la liga | Solo usa partidos anteriores: no se "sabe el futuro". 17 es un torneo |
| **Minuto** | Tramos de 15': 0–15, 15–30, 30–45+, 45–60, 60–75, 75–90, 90+ | — |

### 4.3 Supuestos específicos del 360

El 360 no es un seguimiento completo: solo ve a los jugadores que entran en la toma. Para estas cuentas:
- **Última línea**: los 4 jugadores de campo más retrasados.
- **Bloque**: los 8 más retrasados.
- **Imagen útil**: la que ve a 8 jugadores de campo o más y 5 yardas o más detrás del último. Si no, podría haber un defensor oculto.
- **Marcaje en córners**:
  - el córner solo cuenta si se ve el 90 % del área o más y toda el área chica;
  - un defensor está "pegado" a un rival si está a 2 yardas o menos.

---

## 5. De los datos a las métricas: las tres capas

```
Eventos StatsBomb  ──►  Objetos del marco  ──►  Indicadores por partido  ──►  Lo que ves en la app
(pases, tiros,          (posesión,              (55 variables:                 (promedio de los
 presiones…)             transición…)            salida, presión…)              partidos elegidos)
```

**Capa 1: eventos.** Cada acción con balón: tipo, jugador, ubicación, xG del tiro y OBV de la acción.

**Capa 2: objetos del marco.** Con las definiciones de la sección 4 armamos tablas de posesiones y de jugadas a balón parado, y marcamos cada acción como progresiva, de presión alta, de contrapresión, etc.

**Capa 3: indicadores por partido.** Son 55 variables, cada una asignada a un bloque del reto. Ejemplos:

| Bloque del reto | Indicadores (ejemplos) | De qué variables salen |
|---|---|---|
| Construcción | % de saques de meta en corto; salidas que llegan a campo rival; precisión de pase presionado en campo propio | Pases de saque de meta con su longitud; posesiones de construcción y hasta dónde llegan; pases bajo presión con x < 40 |
| Progresión | Pases y conducciones progresivas por cada 100 pases; carril por el que avanza; % de posesiones que llegan al último tercio | Ubicación inicial y final de pases y conducciones; carril del destino |
| Ocasiones | Goles esperados por cada 100 posesiones; xG por tiro; toques en el área; de dónde nace el xG (juego elaborado, contragolpe, balón parado) | Tiros sin penales con su xG + el tipo de posesión del marco |
| Presión | PPDA; altura de las acciones defensivas; % en campo rival; robos arriba; contrapresión por pérdida | Acciones defensivas con su ubicación; pases rivales |
| Organización defensiva | xG y tiros que concede; % de posesiones rivales que llegan a su último tercio; altura del bloque | Tiros rivales; posesiones rivales; duelos, intercepciones y despejes |
| Transiciones | % de posesiones que son contragolpe; xG al contragolpe a favor y en contra; balones recuperados en 5 s o menos | Posesiones de transición (15 s); pérdidas y recuperaciones (5 s) |
| Dominio | Posesión (% del tiempo); field tilt; OBV neto; xG a favor menos en contra | Duración de posesiones; pases en el último tercio; OBV |
| Balón parado | xG a favor y en contra; % de córners que terminan en tiro | Jugadas a balón parado del marco |
| Jugadores | Reparto del valor (¿pocos o muchos?); valor por línea; cambios en el once; minuto del primer cambio | OBV por jugador; alineaciones; sustituciones |

**Las métricas de StatsBomb que usamos y cómo se las explicamos a la marca:**

| Métrica | Qué es | En la app |
|---|---|---|
| **xG** (goles esperados) | Probabilidad de gol de cada tiro, según cómo y desde dónde se tiró | "Goles esperados" o "peligro" |
| **OBV** (On-Ball Value) | Cuánto cambia cada acción con balón la probabilidad de marcar o de recibir gol | "Aporte" |

**Nuestras métricas propias:**
- el **ADN del Entrenador** (8 rasgos);
- el **Índice de Encaje**;
- el **efecto del marcador**, medido dentro del mismo partido;
- la forma del bloque con 360.

---

## 6. El ADN del Entrenador: qué es y cómo lo construimos

### 6.1 Por qué lo necesitábamos

Los indicadores de la sección 5 describen al América, pero no responden "¿esto es mucho o poco?". Para eso hace falta compararlo con **todos los técnicos de la liga**. El problema es que los eventos solo los tenemos del América. Para la liga entera solo hay estadísticas por equipo y partido, que son agregados de StatsBomb.

El ADN resuelve eso: un perfil de estilo que se puede calcular **para cualquier técnico de la Liga MX**, y donde el América es uno más.

### 6.2 Los 8 rasgos

Cada rasgo es el promedio de 2 a 4 métricas, todas orientadas a que "más" signifique "más de ese rasgo":

| Rasgo | Métricas (estadísticas por equipo y partido de StatsBomb) | Qué significa |
|---|---|---|
| **Control del balón** | posesión, % de pases completos, tiempo en control | Cuánto tiene el balón y qué tan seguro lo circula |
| **Verticalidad** | directness, velocidad hacia la portería, verticalidad media de las posesiones | Qué tan rápido y directo va al arco rival en lugar de elaborar |
| **Llegada al área** | progresiones profundas, pases completados cerca del área, pases dentro del área | Cuántas veces pisa el último tercio y el área |
| **Presión alta** | PPDA (invertido), % de presiones en campo rival, distancia defensiva, agresividad | Qué tan arriba y qué tan intenso intenta recuperar |
| **Reacción tras pérdida** | contrapresiones, balones recuperados con contrapresión | Cuánto presiona justo después de perder el balón |
| **Peligro generado** | xG sin penales, xG por tiro, OBV | Calidad y cantidad de las ocasiones |
| **Solidez defensiva** | xG concedido, progresiones concedidas, OBV concedido (todo invertido) | Qué tan poco peligro concede |
| **Balón parado** | xG a balón parado, xG por jugada, xG concedido a balón parado (invertido) | Peligro a balón parado, menos el que concede |

### 6.3 Los tres pasos del cálculo (y por qué cada uno)

1. **Comparar con la liga del mismo torneo.** Cada métrica se estandariza (z-score) con la media y la desviación de la liga **en ese torneo**, no de todos los años juntos.
   - *Por qué:* la liga cambia con el tiempo. Ver el reto 1 de la sección 9: sin esto, los técnicos recientes parecían más presionantes de lo que eran.
2. **Descontar al rival y la localía.** A cada rasgo se le quita el efecto de contra quién se jugó (un efecto por rival) y de si fue en casa o fuera. Ese efecto se estima con una regresión lineal usando solo los partidos de 2021 a 2025.
   - *Por qué:* contra un rival grande cualquier equipo tiene menos el balón. Queremos el estilo del técnico, no su calendario. Lo vimos en los datos: con Jardine, el rival pesa más que la localía (posesión de 61 % contra rivales débiles y de 49 % contra fuertes).
3. **Expresarlo de 0 a 100.** El promedio del técnico en cada rasgo se ubica entre los **70 técnico-club de la liga** con 15 partidos o más entre 2021 y 2025.
   - 50 es el técnico típico; 100, el que más lo hace.
   - *Por qué:* es una escala que entiende cualquiera, sin hablar de desviaciones estándar.

**Unidad de análisis: técnico × club.** Por ejemplo, Almada-Pachuca y Almada-América son dos perfiles distintos. Así podemos ver si el estilo viaja con el técnico.

### 6.4 El Índice de Encaje

Es la distancia de cada técnico de la liga a la **identidad del América**, convertida a una escala de 0 a 100 (100 = el más parecido).
- La identidad del América es el promedio de sus 8 rasgos entre 2021 y 2025, con todos sus técnicos.
- Los rasgos que se mantienen gane quien gane son la **solidez defensiva** y el **balón parado**. Son "del club"; el resto cambia con el técnico.

> ⚠ **Ojo al contarlo:** la identidad del club se calcula con los partidos de 2021 a 2025, y más de la mitad son de Jardine (91 de 175). Que Jardine salga con el encaje más alto (99) es en parte **por construcción**: no lo presentemos como un descubrimiento. Lo que sí es informativo es el resto de la tabla: los técnicos de otros clubes más cercanos son Renato Paiva (97), Antonio Mohamed (94) y Víctor Vucetich (93).

---

## 7. Qué comparamos con qué, y por qué

| Comparación | Para responder | Por qué esa y no otra |
|---|---|---|
| **Jardine frente a Solari y Ortiz** (mismo club, 2021–2025) | ¿Qué cambió cuando llegó Jardine? | Misma institución y plantillas parecidas: lo que cambia es sobre todo el técnico |
| **Jardine frente a Almada** (2026, misma plantilla) | ¿El estilo es del técnico o de los jugadores? | Es casi un experimento natural: mismo plantel, otro técnico. Almada sube la presión alta (+49) y baja la solidez (−31) |
| **El América frente a la liga del mismo torneo** | ¿Esto es mucho o poco? | Es la única comparación justa entre épocas (sección 9, reto 1) |
| **El mismo partido ganando, empatando o perdiendo** | ¿Cómo cambia el plan con el marcador? | Comparar partidos distintos mezcla rivales y días. Dentro del mismo partido, lo único que cambia es el marcador. Se hace con una regresión ponderada por minutos, con efecto fijo del partido y del tramo de 15' |
| **Rival débil, medio y fuerte; local y visita** | ¿Ajusta según el rival y la cancha? | Niveles según la fuerza del rival en sus 17 partidos previos |
| **Torneo a torneo** | ¿Su idea se mantiene o evoluciona? | El ADN por torneo. Ejemplo: la presión de Jardine pasa de 17 a 81 de 100 entre su primer y su último torneo |
| **"América típico"** (todos los partidos de 2021 a 2025) | Referencia neutra en la app | Para quien no quiere comparar con un técnico en particular |

---

## 8. Cómo comprobamos que el ADN es real (trabajo interno, **no aparece en la app**)

Antes de construir el producto sobre el ADN, quisimos saber si de verdad distingue estilos o solo es ruido. Separamos los partidos en tres grupos:

| Grupo | Periodo | Uso |
|---|---|---|
| **Aprendizaje** | 2021–2025 | Con estos partidos se calculó todo |
| **Validación** | Apertura 2025 | Partidos nuevos |
| **Prueba** | 2026: Cl 2026 de Jardine y Almada | Partidos nuevos |

Después le pedimos a un clasificador que, viendo solo los 8 rasgos de un partido, adivinara qué técnico de la liga jugaba así.

**Resultados:**
- **Prueba**: el técnico correcto queda entre los 5 primeros en el **31 %** de los partidos, frente a 16 % por azar.
- **Validación**: 23 % frente a 16 %. Es una señal más débil, y no la inflamos.
- **Almada**: el clasificador nunca lo vio dirigir al América, y aun así lo reconoce en la **posición 2 de 31** técnicos posibles. Es la evidencia de que el estilo sigue al técnico.

**Conclusión:** el ADN no es una foto de un torneo; distingue técnicos en partidos que no usó para aprender. Con eso nos sentimos seguros de construir el producto encima. **En la app no hablamos de esto:** la marca no necesita saber de validación ni de modelos, solo que lo que ve es sólido.

---

## 9. Los retos que encontramos (y cómo los resolvimos)

1. **La liga cambió y StatsBomb cambió su forma de etiquetar.**
   - Al comparar técnicos de distintas épocas, los recientes salían como "muy presionantes". Investigamos y encontramos dos cosas:
     - el PPDA de toda la liga sube poco a poco (de ~8 a ~12 entre 2021 y 2024): es un cambio real de la liga;
     - las recuperaciones por contrapresión saltan de 12 a 22 por cada 100 en el Ap 2024, en el 89 % de los equipos a la vez: un escalón así solo se explica por un **cambio de etiquetado de StatsBomb**.
   - **Solución:** comparar a cada técnico con la liga **de su mismo torneo**.
   - **Efecto:** Almada dejó de parecer un técnico de "reacción tras pérdida" (79 → 30 de 100) y quedó como de **presión alta** (86).
   - **Por eso en la app** decimos que la presión no se compara entre épocas sin ese ajuste.
2. **Un partido es casi puro ruido.**
   - Cuando intentamos predecir el estilo de un partido desde su contexto, apenas mejoramos sobre el promedio histórico. El estilo por partido se comporta como **identidad + ruido**.
   - **Solución:** la regla de muestra de la app:

     | Partidos | Qué se puede afirmar |
     |---|---|
     | 1 | Solo se compara con el ADN |
     | Menos de 5 | Tendencias |
     | Un torneo | Identidad aproximada |
     | Una etapa | Cifras titulares |

   - Balón parado y xG concedido son tan ruidosos partido a partido que no se usan como criterio individual.
3. **El 360 solo ve lo que ve la cámara.**
   - Solo el 32 % de los pases rivales da una imagen útil para medir el bloque, y en presión alta, el 16 % (la cámara sigue al balón, lejos de la defensa).
   - **Solución:** reglas mínimas de visibilidad (sección 4.3), que el límite quede escrito y comparar solo entre técnicos del América (solo hay 360 de sus partidos).
4. **El balón parado venía "heredado".**
   - StatsBomb marca toda la posesión según cómo empezó la jugada. Si el portero atrapa un córner rival y sale al contragolpe, esa posesión queda marcada "desde córner".
   - **Solución:** solo cuenta como balón parado si la posesión la abre **el saque del propio equipo**.
   - **Efecto:** el xG a balón parado de Jardine pasó de 40 % a **37 %** del total, y el de transición subió.
5. **Las cifras de balón parado dependen de la definición.** Las tres son correctas y miden cosas distintas:

   | Definición | Peso en el xG de Jardine |
   |---|---|
   | Toda la posesión que abre el saque propio | 37 % |
   | Córners y jugadas del último tercio | 26 % |
   | Solo el remate directo del envío | 7 % |

   **Lectura:** la mayor parte del peligro es **la segunda jugada**.
6. **No se pueden compartir datos crudos.** La app no puede llevar eventos. **Solución:** el cubo de agregados por partido (sección 10).
7. **Promedio por partido frente a total de la era.** La app promedia partido a partido (los saques de meta cortos de Jardine dan 47 %) y la historia a veces suma todas las jugadas (45 %). Las dos son correctas, pero hay que decir cuál es cuál.

---

## 10. Cómo funciona la app (recorrido)

### 10.1 Arquitectura

```
Eventos y 360 (solo en nuestras máquinas)
      │  src/framework.py + src/features.py + src/story.py
      ▼
Cubo de agregados por partido (src/cube.py)      ← solo resúmenes: sin eventos, sin coordenadas sueltas,
      │  app/export_data.py                         sin tablas crudas de StatsBomb
      ▼
app/data/ (0.4 MB)  ──►  app/streamlit_app.py
```

**El cubo** tiene una fila por partido (222) con:
- **datos del partido**: fecha, torneo, técnico, rival y su fuerza, localía, resultado, goles, xG a favor y en contra;
- **los 41 indicadores** del marco;
- **los 8 rasgos del ADN** de ese partido;
- **sistema titular y primer cambio**.

Aparte, guarda tablas complementarias:
- **conteos por zona de la cancha** (cuadros de 10 × 10 yardas) para los mapas: tiros, tiros rivales, robos, acciones defensivas y pases progresivos;
- **balón parado** por tipo y zona de envío;
- **tramos de 15'** con su marcador;
- **jugadores por técnico y torneo** (no por partido, para no exponer datos individuales de StatsBomb).

**Por qué un cubo:** así **cualquier filtro funciona sumando o promediando partidos**, sin eventos. El ADN, los tiros por partido, el balón parado y el efecto del marcador que salen del cubo coinciden exactamente con los del análisis completo (lo verificamos).

### 10.2 Lo que ve el usuario

1. **Eliges qué ver** (barra lateral):
   - **"La historia de Jardine"**: la selección por defecto, con los textos y figuras de la historia;
   - **"Explorar"**:
     - técnico;
     - periodo: toda la etapa, torneo, rango de fechas o un partido;
     - localía y fuerza del rival;
     - con quién comparar: otro técnico o el América típico.
2. **Arriba, el resumen del periodo**: partidos, récord, puntos, goles y goles esperados, y un aviso de cuánto se puede concluir con ese número de partidos.
3. **El calendario: contra quién jugó.** Cada partido con su rival, la fuerza del rival, el resultado y quién tuvo mejores ocasiones.
   - *Por qué siempre visible:* un tramo con rivales grandes no es un cambio de estilo.
4. **Pestañas**:

   | Pestaña | Qué muestra | De dónde sale |
   |---|---|---|
   | **Identidad** | Radar del ADN de la selección frente a la comparación (y frente a toda la etapa del técnico si eliges menos); las 5 ideas; sistemas usados | Rasgos del ADN por partido, promediados y ubicados de 0 a 100 frente a los 70 técnicos |
   | **Con balón** | Mapa de dónde vienen las ocasiones (xG) y hasta dónde progresa; indicadores de construcción, progresión, ocasiones y dominio | Rejillas por partido + indicadores del marco |
   | **Sin balón** | Mapas de robos, acciones defensivas y peligro concedido; indicadores de presión, organización defensiva y transiciones | Ídem |
   | **Balón parado** | Por tipo (córner, tiro libre, saque de banda), a favor y en contra: jugadas, % con tiro y peligro; a qué zona van los córners | Jugadas a balón parado del marco |
   | **Contexto** | Cómo cambian el dominio, la posesión y la presión con el marcador (mismo partido, con su margen de error); tabla por localía y fuerza del rival | Tramos de 15' × marcador, la misma regresión que el análisis |
   | **Jugadores** | Minutos, quién genera el valor, roles, primer cambio | Jugadores por técnico × torneo |
   | **Cómo lo medimos** | El método en lenguaje simple y el diccionario de indicadores | — |

   Los indicadores se muestran **de 0 a 100 frente a la comparación**: "supera a X de cada 100 partidos de la comparación". Así se leen todos igual, aunque estén en unidades distintas.
5. **Lenguaje para la marca.** La app no habla de "validación", "muestra", "percentil" ni "modelo". Dice "temporadas recientes", "de 0 a 100 frente a la liga", "aporte" (OBV), "dominio territorial" (field tilt) y "pases que deja dar al rival antes de presionar" (PPDA).

---

## 11. La historia de Jardine en 5 ideas (lo que la app cuenta por defecto)

1. **Quiere el balón y lo saca jugando.**
   - Saca en corto el 45 % de sus saques de meta (Ortiz 31 %).
   - Un mediocentro baja a recibir el 44 % de las veces (Ortiz 20 %).
2. **Progresa por dentro, entra por fuera y tira mejor, no más.**
   - 0.12 xG por tiro (Ortiz 0.10).
   - El pase atrás al área es el 15 % de su xG.
3. **No asfixia, se junta.**
   - Presión media (PPDA 1.9 pases por encima de la liga) y un bloque de 20 yardas (Ortiz 23).
   - Gana las transiciones: 1.8 veces más peligro a favor que en contra.
4. **El balón parado es un arma, sobre todo la segunda jugada.**
   - 25 % de los córners en corto.
   - Solo el 7 % del xG es el remate directo.
5. **Lee el partido.**
   - Perdiendo por 1: +8 de dominio territorial y +11 de posesión frente al mismo partido empatado.
   - Ganando por 1: guarda el balón lejos del área (−17).
   - Primer cambio en el descanso en el 26 % de los partidos (el doble que Ortiz y Solari).

Detalle y recomendaciones: `reports/final/textos.md`.

---

## 12. Lo que el producto NO hace (límites)

- **No predice resultados ni recomienda alineaciones.** Describe y compara.
- **No juzga si un cambio funcionó.** Las sustituciones se describen (cuándo, con qué marcador y qué perfil entra), pero su efecto no se puede medir con estos datos.
- **El 360 es parcial.** Solo cuenta lo que capta la cámara.
- **Solo hay eventos del América.** El resto de la liga entra solo por sus estadísticas por equipo y partido (el ADN). Por eso los mapas y los indicadores detallados son solo del América.
- **Con pocos partidos, todo es tendencia.** La app lo avisa.
- **Los jugadores van por torneo, no por partido**, por la regla de datos.

---

## 13. Decisiones clave, en una tabla

| Decisión | Alternativa que descartamos | Por qué |
|---|---|---|
| Un protagonista (Jardine) y los demás como contraste | Analizar a cada técnico por separado | El estilo solo se ve comparando; Jardine tiene la mejor muestra y la mejor historia |
| Todo parte de elegir un periodo | Un reporte fijo | Que el usuario explore por torneo, fechas o partido |
| La historia es el explorador con una selección predeterminada | Historia y explorador separados | Un solo producto, coherente: lo que lees es lo que exploras |
| Comparar con la liga del mismo torneo | Comparar con el promedio de todos los años | La liga y el etiquetado cambiaron (sección 9, reto 1) |
| Descontar rival y localía en el ADN | Promedio crudo | Que el perfil sea del técnico y no de su calendario |
| Balón parado = posesión que abre el saque propio | Usar la etiqueta de StatsBomb tal cual | Evita contar contragolpes como balón parado |
| Efecto del marcador dentro del mismo partido | Comparar partidos ganados frente a perdidos | Aísla el marcador de quién era el rival ese día |
| Regla de muestra visible | Mostrar todo igual siempre | Un partido no es un estilo |
| Cubo de agregados por partido | Llevar eventos a la app | Regla de datos + rapidez |
| Producto de visualización, lenguaje para la marca | Mostrar los modelos | El usuario es la marca; los modelos solo nos dieron confianza |
| Explicar, no predecir | Pronósticos | Lo pide el reto y es lo que se puede defender |

---

## 14. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Definiciones y supuestos (el marco) | `src/framework.py` (`ASSUMPTIONS`) |
| Indicadores por partido (catálogo) | `src/features.py` (`FEATURES`) |
| ADN del Entrenador, Índice de Encaje, validación | `src/coach_profile.py`, notebook `04_adn_entrenador.ipynb` |
| La historia de Jardine (análisis y figuras) | `src/story.py`, `src/story_viz.py`, notebook `05_historia_jardine.ipynb`, `reports/figures/story/` |
| Textos de la historia | `reports/final/textos.md` |
| Cubo de agregados | `src/cube.py` (`python -m src.cube`) |
| App | `app/streamlit_app.py` (`streamlit run app/streamlit_app.py`); datos: `python -m app.export_data` |
| Pendientes y decisiones con fecha | `todo.md` |
| Pruebas | `tests/` (`pytest -q`) |

---

## 15. Glosario rápido

| Término | Explicación |
|---|---|
| **xG (goles esperados)** | Probabilidad de que un tiro sea gol, según cómo y desde dónde se tiró. Sumado: "cuántos goles merecía" un equipo |
| **OBV (aporte)** | Cuánto mejora o empeora cada acción con balón las opciones de marcar o de recibir gol |
| **PPDA** | Pases que deja dar al rival antes de intentar robar. Menos = presiona más |
| **Field tilt (dominio territorial)** | Qué % de los pases del último tercio son propios |
| **Contrapresión** | Presionar en los 5 segundos después de perder el balón |
| **Transición** | Robo que llega al último tercio o a tiro en 15 segundos o menos |
| **360** | Posiciones de los jugadores visibles en la toma, en el momento de cada acción |
| **Técnico-club** | Un técnico en un club (Almada-Pachuca ≠ Almada-América) |
| **De 0 a 100** | Lugar frente a los técnicos de la liga: 50 = típico, 100 = el que más |

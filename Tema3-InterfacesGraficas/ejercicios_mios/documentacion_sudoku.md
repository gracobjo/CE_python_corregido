# Guía del código: `sudoku.py`

Documento pensado para un estudiante de Python que **aún no domina Tkinter** ni el detalle de cada función del fichero. El objetivo es entender **qué hace el programa**, **cómo está organizado** y **qué papel tiene cada bloque**, sin necesidad de memorizar la API de ventanas.

---

## 1. ¿Qué es este programa?

Es un **Sudoku jugable** con ventana gráfica. Al ejecutarlo:

1. Se abre una ventana con un tablero 9×9.
2. Puedes elegir dificultad (Fácil / Medio / Difícil).
3. Rellenas casillas vacías (teclado 1–9; opcionalmente, clic en candidatos).
4. Los **candidatos** (números pequeños) están **ocultos por defecto**; se activan con el botón **«Mostrar candidatos»**.
5. Puedes pedir pistas, guardar la partida, ver récords, etc.

El fichero mezcla dos mundos:

| Mundo | Qué es | En el código |
|--------|--------|--------------|
| **Lógica** (backend) | Reglas del Sudoku, generar tableros, candidatos… | Funciones sueltas al principio |
| **Interfaz** (frontend) | Botones, colores, clics, mensajes | Clases `CeldaSudoku` y `SudokuApp` |

Idea clave: **primero se resuelve el problema con listas y funciones; después se “pinta” en pantalla**.

---

## 2. Cómo se representa el tablero

Un tablero es una **lista de 9 listas**, cada una con 9 enteros:

```text
tablero[fila][columna]
```

- `0` = casilla vacía  
- `1` … `9` = número colocado  

Ejemplo (solo conceptual):

```python
tablero = [
    [5, 3, 0, 0, 7, 0, 0, 0, 0],  # fila 0
    [6, 0, 0, 1, 9, 5, 0, 0, 0],  # fila 1
    # ...
]
```

En la partida hay **tres tableros** relacionados:

| Nombre | Significado |
|--------|-------------|
| `tablero_resuelto` | Solución completa (la conoce el programa) |
| `tablero_fijo` | Pistas iniciales (no se pueden borrar) |
| `tablero_actual` | Lo que se ve ahora (pistas + lo que escribió el jugador) |

---

## 3. Cómo arranca el programa (final del fichero)

Al final aparece:

```python
if __name__ == "__main__":
    root = tk.Tk()          # crea la ventana principal
    app = SudokuApp(root)   # construye la aplicación dentro de esa ventana
    root.mainloop()         # bucle: espera clics, teclas, etc. hasta cerrar
```

- `tk` es el módulo **Tkinter** (biblioteca estándar de Python para ventanas).
- No hace falta saber todos los widgets: basta pensar que **Tkinter dibuja controles** (botones, etiquetas) y **llama a tus funciones** cuando el usuario interactúa (“eventos”).
- `mainloop()` es el “motor” que mantiene la ventana abierta.

---

## 4. Mapa del fichero (de arriba abajo)

```text
1) Imports          → herramientas (aleatorio, JSON, tiempo, Tkinter…)
2) Guardado/récords → leer y escribir ficheros .json
3) Lógica Sudoku    → reglas, generar puzzle, candidatos, bloqueos
4) class CeldaSudoku→ UNA casilla de la cuadrícula
5) class SudokuApp  → TODA la aplicación (botones, pistas, timer…)
6) if __name__…     → punto de entrada
```

---

## 5. Imports: ¿para qué cada uno?

| Import | Uso sencillo |
|--------|----------------|
| `tkinter` | Crear ventana, botones, etiquetas |
| `messagebox` | Ventanas emergentes (“¿Guardar?”, “¡Ganaste!”) |
| `scrolledtext` | Texto largo con scroll (tutorial) |
| `random` | Mezclar números al generar tableros |
| `copy` | Copiar tableros sin modificar el original (`deepcopy`) |
| `json` | Guardar/cargar partidas como texto estructurado |
| `os` | Rutas de carpetas y ficheros |
| `time` / `datetime` | Cronómetro y fechas de récords |
| `combinations` | Combinaciones de filas/columnas (rectángulo mortal) |

---

## 6. Guardado de partidas y récords

Carpeta usada: `sudoku_partidas/` junto al `.py`.

### Funciones importantes

- **`ruta_guardado(dificultad)`**  
  Devuelve la ruta del fichero, p. ej. `partida_facil.json`.

- **`guardar_partida(...)`**  
  Escribe un diccionario con los tres tableros y el tiempo en un `.json`.

- **`cargar_partida(dificultad)`**  
  Lee ese fichero. Si no existe, devuelve `None`.

- **`eliminar_guardado(dificultad)`**  
  Borra el guardado (p. ej. al empezar un juego nuevo).

- **`formatear_tiempo(segundos)`**  
  Convierte `125` → `"02:05"` (texto legible).

- **`registrar_partida_terminada(...)`**  
  Cuando ganas, guarda el tiempo en `records.json` y comprueba si es récord.

**Concepto JSON:** es un formato de texto para guardar diccionarios y listas. Python lo escribe y lo vuelve a leer con `json.dump` / `json.load`.

---

## 7. Lógica del Sudoku (el “cerebro”)

Estas funciones **no dibujan nada**. Solo trabajan con listas.

### 7.1. ¿Se puede poner este número?

**`es_valido(tablero, fila, col, num)`**

Comprueba las tres reglas:

1. `num` no está ya en la **misma fila**
2. ni en la **misma columna**
3. ni en la **caja 3×3**

Devuelve `True` o `False`.

La caja se calcula con división entera:

```text
fila 5 → caja que empieza en fila 3
porque 5 // 3 = 1  →  1 * 3 = 3
```

### 7.2. Candidatos (números posibles)

- **`candidatos_celda`**: lista de números 1–9 que caben en una casilla vacía.  
- **`mapa_candidatos`**: hace eso para **todas** las casillas → matriz 9×9 de listas.

Ejemplo: si una casilla solo admite `[3, 7]`, esos son sus candidatos.

### 7.3. Unicidad en zona (“hidden single”)

**`unicos_en_zona(cands)`**

A veces un número **sí cabe en varias celdas de la fila**, pero en la práctica **solo una** de esas celdas lo tiene como candidato. Entonces ese número está “forzado” en esa celda (aunque la celda tenga otros candidatos).

Devuelve un conjunto de triples `(fila, col, número)`.

En la interfaz:

- **Verde** ≈ solo queda un candidato en la casilla (*naked single*).  
- **Morado** ≈ único sitio de la fila/columna/caja para ese número (*hidden single*).  
- Solo se colorean si coinciden con la **solución real** (para no engañar si el jugador puso números mal).

### 7.4. Generar un Sudoku

1. **`resolver_sudoku(tablero)`**  
   Rellena huecos por **prueba y error** (backtracking):
   - Busca una casilla vacía.
   - Prueba un número válido.
   - Llama **otra vez a sí misma** (recursión).
   - Si no hay salida, borra el número (`0`) y prueba otro.

2. **`generar_tablero_resuelto()`**  
   Empieza con todo a `0` y llama al resolver → tablero lleno.

3. **`contar_soluciones(tablero, limite=2)`**  
   Cuenta cuántas soluciones hay (como mucho 2). Sirve para saber si el puzzle es **único**.

4. **`crear_puzzle(tablero_resuelto, dificultad)`**  
   Copia la solución y **borra** casillas (más borradas = más difícil), pero **solo si tras borrar sigue habiendo exactamente 1 solución**.  
   Así se evitan partidas con dos finales posibles.

5. **`reparar_unicidad(...)`**  
   Para partidas **antiguas** guardadas que tenían 2 soluciones: vuelve a poner pistas mínimas hasta que quede 1.

### 7.5. Rectángulo mortal (ambigüedad)

**`buscar_rectangulo_mortal(cands)`**

Busca 4 casillas vacías en forma de rectángulo (2 filas × 2 columnas) con el **mismo par** de candidatos, p. ej. todas con `{5, 7}`.

Eso permite **dos diagonales** válidas:

```text
  5 ... 7          7 ... 5
  .     .    o     .     .
  7 ... 5          5 ... 7
```

La lógica “pura” no elige. La app marca en **azul** el dígito de **esta** partida (según `tablero_resuelto`) y puede ofrecer rellenar las cuatro.

### 7.6. Conflictos y bloqueos

- **`celdas_en_conflicto`**: casillas donde un número está **repetido** en fila/columna/caja (fondo rojo).
- **`celdas_que_bloquean`**: qué casillas impiden poner un número concreto en otra.
- **`analizar_bloqueo`**: detecta callejones sin salida (casilla vacía sin candidatos útiles) y propone **UNDO** (quitar números de usuario incorrectos).

---

## 8. Tkinter en 5 ideas (antes de las clases)

1. **Widget** = control visual (`Button`, `Label`, `Frame`…).  
2. **`Frame`** = caja contenedora (agrupa widgets).  
3. **`pack` / `grid` / `place`** = formas de colocar widgets en la ventana.  
4. **`command=funcion`** o **`bind("evento", funcion)`** = “cuando ocurra X, ejecuta Y”.  
5. **`messagebox`** = diálogo modal (el programa espera tu respuesta).

No hace falta memorizar más para seguir el código.

---

## 9. Clase `CeldaSudoku`: una casilla

Hereda de `tk.Frame`: **es un cuadradito** del tablero.

### Dos capas

```text
┌─────────────────┐
│  Número grande  │  ← Label encima (si hay valor)
│  (place)        │
├─────────────────┤
│ 1 2 3           │  ← Candidatos pequeños 3×3
│ 4 5 6           │     (siempre debajo)
│ 7 8 9           │
└─────────────────┘
```

- Si la casilla está **vacía**, ves los candidatos.  
- Si tiene **valor**, se muestra el número grande encima (sin destruir la capa de candidatos).

### Atributos útiles

| Atributo | Idea |
|----------|------|
| `fila`, `col` | Posición en el tablero |
| `_valor` | Número actual (`0` = vacío) |
| `_fijo` | `True` si es pista inicial (no editable) |
| `app` | Referencia a `SudokuApp` (para avisar: “me han clicado”) |

### Métodos que conviene conocer

- **`set_valor(valor, fijo=...)`** — pone o quita el número grande.  
- **`actualizar_candidatos(...)`** — decide qué candidatos se ven y de qué color.  
- **`set_bg` / `restaurar_bg`** — cambia el color de fondo (selección, pista, conflicto…).  
- **`_pulsar_candidato`** — al soltar el clic sobre un candidato pequeño, pide a la app colocar ese número.

Los métodos que empiezan por `_` son “internos” (uso habitual dentro de la clase).

---

## 10. Clase `SudokuApp`: el director de orquesta

Esta clase **monta la ventana completa** y coordina lógica + interfaz.

### Al crear la app (`__init__`)

1. Guarda la ventana (`self.root`).  
2. Prepara variables de estado (tablero, foco, timer…).  
3. Llama a **`crear_interfaz()`** (botones, tablero, leyenda, barra de estado).  
4. Programa **`_inicio_con_guardado`**: pregunta si hay partida guardada.

### Piezas de la interfaz (idea general)

- Menú de dificultad + botones: Nuevo, Pista, **Mostrar/Ocultar candidatos**, Comprobar, Guardar, Retomar, Tutorial, Récords, Deshacer bloqueo, Salir.  
- Cuadrícula 9×9 de objetos `CeldaSudoku`.  
- Cronómetro.  
- Etiqueta de estado (mensajes de ayuda / error).  
- Leyenda de colores de candidatos (solo visible si están activados).  

Flag `mostrar_candidatos` (por defecto `False`): `alternar_mostrar_candidatos` cambia el modo; `_refrescar_candidatos` pinta o limpia los números pequeños. Pista / ambigüedad pueden activarlos solos con `_asegurar_candidatos_visibles`.

### Flujo de un juego nuevo (`nuevo_juego`)

```text
generar_tablero_resuelto()
        ↓
crear_puzzle(...)          → tablero_fijo
        ↓
pintar casillas (actualizar_tablero_gui)
        ↓
refrescar candidatos
        ↓
iniciar cronómetro
```

### Colocar un número (`colocar_numero`)

1. Comprueba que la casilla no sea fija.  
2. Actualiza el valor en la celda.  
3. Refresca candidatos de **todo** el tablero.  
4. Marca conflictos si los hay.  
5. Comprueba si ya está resuelto (`verificar_victoria`).

### Selección y teclado

- Clic en una casilla → `seleccionar_celda` (fondo amarillo).  
- Teclas `1`–`9` → `_introducir_digito` en la casilla seleccionada.  
- Suprimir / Backspace → borrar número de usuario.

### Pista (`dar_pista`)

Mira la casilla enfocada y explica, en este orden aproximado:

1. ¿Naked single? (solo un candidato)  
2. ¿Hidden single?  
3. ¿Rectángulo mortal?  
4. Si no, lista candidatos y qué números están bloqueados (y por qué casillas).

Resalta en color el **contexto** (fila/columna/caja) y las celdas **bloqueantes**.

### Guardar / cargar

- Guardar: serializa tableros + tiempo a JSON y **pausa** el timer.  
- Cargar: restaura tableros; si el puzzle antiguo no era único, **`reparar_unicidad`** añade pistas y avisa.

### Deshacer bloqueo

Usa `analizar_bloqueo` y propone quitar números incorrectos del jugador para salir del callejón.

### Victoria

Si el tablero actual coincide con `tablero_resuelto`:

- Para el timer.  
- Registra récord.  
- Bloquea todas las casillas.  
- Muestra mensaje de enhorabuena.

---

## 11. Colores de candidatos (resumen para el jugador/estudiante)

| Color | Significado |
|-------|-------------|
| Gris | Posible, **no forzado** (puede equivocarte) |
| Verde | Forzado en esa casilla (un solo candidato correcto) |
| Morado | Forzado por fila/columna/caja (hidden single correcto) |
| Azul | Ante ambigüedad (rectángulo): elige este (solución de la partida) |
| Gris muy claro | Ante ambigüedad: candidato a descartar |

Regla didáctica del programa: **prioriza verde/morado; el gris es solo “posible”**.

---

## 12. Diagrama mental de datos

```text
                    ┌──────────────────┐
                    │ tablero_resuelto │  (solución secreta)
                    └────────┬─────────┘
                             │ se usa para
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        pistas fijas    comprobar      colorear
        (tablero_fijo)  victoria       candidatos
              │
              ▼
        tablero_actual  ←→  matriz de CeldaSudoku (pantalla)
```

---

## 13. Orden recomendado para leer el código

1. Final: `if __name__ == "__main__"`  
2. `es_valido`, `candidatos_celda`, `resolver_sudoku`, `crear_puzzle`  
3. `CeldaSudoku.set_valor` y `actualizar_candidatos`  
4. `SudokuApp.nuevo_juego`, `colocar_numero`, `_refrescar_candidatos`  
5. `dar_pista`, `deshacer_bloqueo`, guardado/timer  

Así pasas de **reglas → casilla → aplicación completa**.

---

## 14. Glosario rápido

| Término | Significado aquí |
|---------|------------------|
| Backtracking | Probar, y si falla deshacer y probar otra opción |
| Candidato | Número que aún cabe en una casilla vacía |
| Pista fija | Número del puzzle inicial; no editable |
| Widget | Elemento visual de Tkinter |
| Evento | Clic, tecla, etc. que dispara una función |
| Recursión | Función que se llama a sí misma (`resolver_sudoku`) |
| `deepcopy` | Copia profunda: clonar listas anidadas sin compartir memoria |
| JSON | Formato de fichero para guardar diccionarios/listas |

---

## 15. Cómo ejecutarlo

Desde la carpeta del fichero:

```bash
python sudoku.py
```

Se abrirá la ventana. No hace falta instalar Tkinter aparte en la mayoría de instalaciones normales de Python en Windows.

---

## 16. Ideas para practicar (opcionales)

1. Cambia los colores de candidatos en `CeldaSudoku`.  
2. Añade un botón que muestre cuántas casillas vacías quedan.  
3. Imprime en consola el resultado de `candidatos_celda` al colocar un número.  
4. Lee un `partida_*.json` y explica qué representan las tres matrices.

Con eso se refuerza la separación **lógica / interfaz**, que es la lección principal de este fichero.

import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import copy
import json
import os

# ==========================================
# RUTAS DE GUARDADO
# ==========================================

DIRECTORIO_GUARDADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_partidas")

def ruta_guardado(dificultad):
    nombre = f"partida_{dificultad.lower().replace('á','a').replace('é','e')}.json"
    return os.path.join(DIRECTORIO_GUARDADO, nombre)

def guardar_partida(dificultad, tablero_resuelto, tablero_fijo, tablero_actual):
    os.makedirs(DIRECTORIO_GUARDADO, exist_ok=True)
    datos = {
        "dificultad":       dificultad,
        "tablero_resuelto": tablero_resuelto,
        "tablero_fijo":     tablero_fijo,
        "tablero_actual":   tablero_actual,
    }
    with open(ruta_guardado(dificultad), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

def cargar_partida(dificultad):
    ruta = ruta_guardado(dificultad)
    if not os.path.exists(ruta):
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)

def eliminar_guardado(dificultad):
    ruta = ruta_guardado(dificultad)
    if os.path.exists(ruta):
        os.remove(ruta)

# ==========================================
# LÓGICA DEL SUDOKU (Backend)
# ==========================================

def es_valido(tablero, fila, col, num):
    if num in tablero[fila]:
        return False
    if num in [tablero[i][col] for i in range(9)]:
        return False
    caja_fila, caja_col = 3 * (fila // 3), 3 * (col // 3)
    for i in range(3):
        for j in range(3):
            if tablero[caja_fila + i][caja_col + j] == num:
                return False
    return True

def resolver_sudoku(tablero):
    for i in range(9):
        for j in range(9):
            if tablero[i][j] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if es_valido(tablero, i, j, num):
                        tablero[i][j] = num
                        if resolver_sudoku(tablero):
                            return True
                        tablero[i][j] = 0
                return False
    return True

def generar_tablero_resuelto():
    tablero = [[0] * 9 for _ in range(9)]
    resolver_sudoku(tablero)
    return tablero

def crear_puzzle(tablero_resuelto, dificultad):
    puzzle = copy.deepcopy(tablero_resuelto)
    celdas = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(celdas)
    borrar = {"Fácil": 35, "Medio": 45, "Difícil": 55}
    for i in range(borrar.get(dificultad, 45)):
        fila, col = celdas[i]
        puzzle[fila][col] = 0
    return puzzle

def celdas_en_conflicto(tablero):
    """Devuelve el conjunto de (i,j) con valor repetido en su fila, columna o caja."""
    conflictos = set()
    for i in range(9):
        for j in range(9):
            val = tablero[i][j]
            if val == 0:
                continue
            for jj in range(9):
                if jj != j and tablero[i][jj] == val:
                    conflictos.add((i, j)); conflictos.add((i, jj))
            for ii in range(9):
                if ii != i and tablero[ii][j] == val:
                    conflictos.add((i, j)); conflictos.add((ii, j))
            ci, cj = 3 * (i // 3), 3 * (j // 3)
            for di in range(3):
                for dj in range(3):
                    ni, nj = ci + di, cj + dj
                    if (ni, nj) != (i, j) and tablero[ni][nj] == val:
                        conflictos.add((i, j)); conflictos.add((ni, nj))
    return conflictos

# ==========================================
# INTERFAZ GRÁFICA
# ==========================================

class SudokuApp:

    # ── Paleta de colores ─────────────────────────────────────────────
    COLOR_FIJO          = "black"
    COLOR_USUARIO       = "#1565C0"     # azul – número de usuario sin conflicto
    COLOR_CONFLICTO     = "#E65100"     # naranja – número repetido
    COLOR_ESTADO_OK     = "green"
    COLOR_ESTADO_ERR    = "red"
    COLOR_ESTADO_INF    = "#1565C0"

    COLOR_BG_SELECCION  = "#FFF59D"     # amarillo – celda activa
    COLOR_BG_PAR        = "#FFFFFF"     # blanco – bloques pares
    COLOR_BG_IMPAR      = "#E0E0E0"     # gris – bloques impares
    COLOR_BG_CONTEXTO   = "#DDEEFF"     # azul claro – misma fila/col/caja
    COLOR_BG_BLOQUEANTE = "#FFE0B2"     # naranja claro – celda que bloquea un número

    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku en Python")
        self.root.resizable(False, False)

        self.dificultad       = tk.StringVar(value="Medio")
        self.tablero_resuelto = []
        self.tablero_fijo     = []
        self.entries          = [[None] * 9 for _ in range(9)]
        self.widget_map       = {}
        self._celdas_resaltadas        = set()   # celdas con bg de pista activa
        self._ultimo_aviso_conflicto   = 0

        self.crear_interfaz()
        self.root.after(100, self._inicio_con_guardado)

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ------------------------------------------------------------------

    def crear_interfaz(self):
        # ── Fila 1 de botones ─────────────────────────────────────────
        frame1 = tk.Frame(self.root, pady=6)
        frame1.pack()

        tk.Label(frame1, text="Dificultad:").pack(side=tk.LEFT, padx=5)
        tk.OptionMenu(frame1, self.dificultad,
                      "Fácil", "Medio", "Difícil",
                      command=self._cambiar_dificultad).pack(side=tk.LEFT, padx=5)

        tk.Button(frame1, text="Nuevo Juego",  command=self.nuevo_juego,
                  bg="#4CAF50", fg="white", width=10).pack(side=tk.LEFT, padx=4)
        tk.Button(frame1, text="Pista (Ayuda)", command=self.dar_pista,
                  bg="#2196F3", fg="white", width=11).pack(side=tk.LEFT, padx=4)
        tk.Button(frame1, text="Comprobar",    command=self.comprobar_tablero,
                  bg="#FF9800", fg="white", width=10).pack(side=tk.LEFT, padx=4)
        tk.Button(frame1, text="Tutorial",     command=self.mostrar_tutorial,
                  bg="#9C27B0", fg="white", width=9).pack(side=tk.LEFT, padx=4)

        # ── Fila 2 de botones ─────────────────────────────────────────
        frame2 = tk.Frame(self.root, pady=2)
        frame2.pack()

        tk.Button(frame2, text="💾  Guardar partida", command=self.guardar_partida_manual,
                  bg="#795548", fg="white", width=16).pack(side=tk.LEFT, padx=4)
        tk.Button(frame2, text="📂  Retomar partida", command=self.retomar_partida_manual,
                  bg="#607D8B", fg="white", width=16).pack(side=tk.LEFT, padx=4)
        tk.Button(frame2, text="🚪  Salir",           command=self.salir,
                  bg="#F44336", fg="white", width=10).pack(side=tk.LEFT, padx=4)

        # ── Tablero 9×9 ───────────────────────────────────────────────
        self.frame_tablero = tk.Frame(self.root, bd=2, relief=tk.SOLID)
        self.frame_tablero.pack(padx=10, pady=10)

        for i in range(9):
            for j in range(9):
                bg = self._bg_normal(i, j)
                entry = tk.Entry(self.frame_tablero, width=2, font=("Arial", 24),
                                 justify="center", bg=bg, relief=tk.FLAT, bd=1)
                entry.grid(row=i, column=j, padx=1, pady=1, ipadx=8, ipady=8)

                vcmd = (self.root.register(self.validar_input), "%P", "%W")
                entry.config(validate="key", validatecommand=vcmd)

                entry.bind("<KeyRelease>", self._on_key_release)
                entry.bind("<FocusIn>",    self.marcar_seleccion)
                entry.bind("<FocusOut>",   self.desmarcar_seleccion)

                self.entries[i][j] = entry
                self.widget_map[str(entry)] = (i, j)

        # ── Barra de estado ───────────────────────────────────────────
        self.estado = tk.Label(self.root,
                               text="Selecciona una casilla vacía y pulsa 'Pista (Ayuda)'",
                               font=("Arial", 11), fg=self.COLOR_ESTADO_INF,
                               wraplength=680, justify=tk.LEFT, pady=6)
        self.estado.pack(padx=10)

        self.root.protocol("WM_DELETE_WINDOW", self.salir)

    # ------------------------------------------------------------------
    # HELPERS DE COLOR
    # ------------------------------------------------------------------

    def _bg_normal(self, i, j):
        return self.COLOR_BG_PAR if (i // 3 + j // 3) % 2 == 0 else self.COLOR_BG_IMPAR

    # ------------------------------------------------------------------
    # DETECCIÓN DE CONFLICTOS EN TIEMPO REAL
    # ------------------------------------------------------------------

    def _on_key_release(self, event):
        self._limpiar_resaltado_pista()
        self.root.after(0, self._actualizar_colores_conflicto)
        self.root.after(0, lambda: self.verificar_victoria(event))

    def _actualizar_colores_conflicto(self):
        if not self.tablero_fijo:
            return
        tablero_actual = self.obtener_tablero_actual()
        en_conflicto   = celdas_en_conflicto(tablero_actual)

        for i in range(9):
            for j in range(9):
                entry = self.entries[i][j]
                if self.tablero_fijo[i][j] != 0:
                    entry.config(fg=self.COLOR_FIJO)
                elif entry.get() != "":
                    color = self.COLOR_CONFLICTO if (i, j) in en_conflicto else self.COLOR_USUARIO
                    entry.config(fg=color)

        num_conf = len(en_conflicto)
        if num_conf != self._ultimo_aviso_conflicto:
            self._ultimo_aviso_conflicto = num_conf
            if num_conf > 0:
                self.estado.config(
                    text=f"⚠️  {num_conf} celda(s) en conflicto (naranja): número repetido en fila, columna o caja.",
                    fg=self.COLOR_CONFLICTO
                )
            elif self.estado.cget("fg") == self.COLOR_CONFLICTO:
                self.estado.config(text="Sin conflictos. ¡Buen trabajo!", fg=self.COLOR_ESTADO_OK)

    # ------------------------------------------------------------------
    # RESALTADO DE PISTA
    # ------------------------------------------------------------------

    def _limpiar_resaltado_pista(self):
        """Restaura el fondo normal de todas las celdas resaltadas por la pista."""
        for i, j in self._celdas_resaltadas:
            self.entries[i][j].config(bg=self._bg_normal(i, j))
        self._celdas_resaltadas.clear()

    def _celdas_contexto(self, i, j):
        """Devuelve todas las celdas de la misma fila, columna y caja (sin (i,j))."""
        celdas = set()
        for jj in range(9): celdas.add((i, jj))
        for ii in range(9): celdas.add((ii, j))
        ci, cj = 3 * (i // 3), 3 * (j // 3)
        for di in range(3):
            for dj in range(3):
                celdas.add((ci + di, cj + dj))
        celdas.discard((i, j))
        return celdas

    def _celda_bloqueante(self, tablero, i, j, num):
        """Devuelve la celda (ri, ci) que impide colocar 'num' en (i, j), o None."""
        for jj in range(9):
            if jj != j and tablero[i][jj] == num:
                return (i, jj)
        for ii in range(9):
            if ii != i and tablero[ii][j] == num:
                return (ii, j)
        ci, cj = 3 * (i // 3), 3 * (j // 3)
        for di in range(3):
            for dj in range(3):
                ni, nj = ci + di, cj + dj
                if (ni, nj) != (i, j) and tablero[ni][nj] == num:
                    return (ni, nj)
        return None

    def _detectar_hidden_single(self, tablero, i, j, posibles):
        """
        Comprueba si (i,j) es un 'hidden single' para algún número posible.
        Devuelve (num, descripcion_zona, celdas_justificacion) o None.
        """
        for num in posibles:
            # ¿Es (i,j) la única celda vacía de la fila donde cabe num?
            otros_fila = [
                (i, jj) for jj in range(9)
                if jj != j and tablero[i][jj] == 0 and es_valido(tablero, i, jj, num)
            ]
            if not otros_fila:
                justif = [(i, jj) for jj in range(9) if jj != j and tablero[i][jj] == 0]
                return num, f"fila {i+1}", justif

            # ¿Es (i,j) la única celda vacía de la columna donde cabe num?
            otros_col = [
                (ii, j) for ii in range(9)
                if ii != i and tablero[ii][j] == 0 and es_valido(tablero, ii, j, num)
            ]
            if not otros_col:
                justif = [(ii, j) for ii in range(9) if ii != i and tablero[ii][j] == 0]
                return num, f"columna {j+1}", justif

            # ¿Es (i,j) la única celda vacía de la caja donde cabe num?
            ci, cj = 3 * (i // 3), 3 * (j // 3)
            otros_caja = [
                (ci + di, cj + dj) for di in range(3) for dj in range(3)
                if (ci + di, cj + dj) != (i, j)
                and tablero[ci + di][cj + dj] == 0
                and es_valido(tablero, ci + di, cj + dj, num)
            ]
            if not otros_caja:
                justif = [
                    (ci + di, cj + dj) for di in range(3) for dj in range(3)
                    if (ci + di, cj + dj) != (i, j) and tablero[ci + di][cj + dj] == 0
                ]
                return num, "caja 3×3", justif
        return None

    # ------------------------------------------------------------------
    # PISTA EXPLICADA
    # ------------------------------------------------------------------

    def dar_pista(self):
        focus_widget = self.root.focus_get()
        if not focus_widget or str(focus_widget) not in self.widget_map:
            self.estado.config(text="Primero haz clic dentro de una casilla vacía.", fg=self.COLOR_ESTADO_ERR)
            return

        i, j = self.widget_map[str(focus_widget)]

        if self.tablero_fijo[i][j] != 0:
            self.estado.config(text="Esta casilla ya tiene un número fijo.", fg=self.COLOR_ESTADO_ERR)
            return
        if self.entries[i][j].get() != "":
            self.estado.config(text="Borra el número de la casilla antes de pedir una pista.", fg=self.COLOR_ESTADO_ERR)
            return

        # ── Limpiar resaltados previos ────────────────────────────────
        self._limpiar_resaltado_pista()

        tablero_actual = self.obtener_tablero_actual()
        posibles = [n for n in range(1, 10) if es_valido(tablero_actual, i, j, n)]

        if not posibles:
            self.estado.config(
                text="No hay números válidos para esa casilla. Revisa los números introducidos.",
                fg=self.COLOR_ESTADO_ERR
            )
            return

        # ── 1. Resaltar contexto (misma fila / col / caja) ───────────
        for ci, cj in self._celdas_contexto(i, j):
            self.entries[ci][cj].config(bg=self.COLOR_BG_CONTEXTO)
            self._celdas_resaltadas.add((ci, cj))

        # ── 2. Encontrar celdas bloqueantes para cada número excluido ─
        bloqueantes = {}
        for num in range(1, 10):
            if num not in posibles:
                cb = self._celda_bloqueante(tablero_actual, i, j, num)
                if cb:
                    bloqueantes[num] = cb

        # Resaltar celdas bloqueantes en naranja claro
        for num, (bi, bj) in bloqueantes.items():
            self.entries[bi][bj].config(bg=self.COLOR_BG_BLOQUEANTE)
            self._celdas_resaltadas.add((bi, bj))

        # ── Construir texto de exclusiones ───────────────────────────
        def zona(bi, bj):
            if bi == i:   return f"fila {i+1} (col {bj+1})"
            if bj == j:   return f"col {j+1} (fila {bi+1})"
            return f"caja ({bi+1},{bj+1})"

        excl_partes = [f"{n}→{zona(*cb)}" for n, cb in list(bloqueantes.items())[:5]]
        excl_txt = " | ".join(excl_partes)
        if len(bloqueantes) > 5:
            excl_txt += "…"

        # ── 3a. Número único (Naked Single) ──────────────────────────
        if len(posibles) == 1:
            num = posibles[0]
            self.estado.config(
                text=(f"Fila {i+1}, col {j+1}: ¡Sólo puede ser {num}! "
                      f"(Naked Single)\n"
                      f"Los demás están bloqueados: {excl_txt}\n"
                      f"🔵 Azul = contexto  |  🟠 Naranja = celda bloqueante"),
                fg=self.COLOR_ESTADO_OK
            )
            return

        # ── 3b. Número oculto (Hidden Single) ────────────────────────
        hs = self._detectar_hidden_single(tablero_actual, i, j, posibles)
        if hs:
            num, zona_hs, justif_celdas = hs
            # Resaltar las celdas de la zona que NO pueden tener este número (en naranja)
            for ci, cj in justif_celdas:
                self.entries[ci][cj].config(bg=self.COLOR_BG_BLOQUEANTE)
                self._celdas_resaltadas.add((ci, cj))
            self.estado.config(
                text=(f"Fila {i+1}, col {j+1}: Debe ser {num} (Hidden Single)\n"
                      f"Es el único lugar de la {zona_hs} donde cabe el {num}.\n"
                      f"🟠 Naranja = otras celdas vacías de la zona que no admiten {num}"),
                fg=self.COLOR_ESTADO_OK
            )
            return

        # ── 3c. Varios candidatos ────────────────────────────────────
        self.estado.config(
            text=(f"Fila {i+1}, col {j+1}: posibles → {', '.join(map(str, posibles))}\n"
                  f"Bloqueados: {excl_txt}\n"
                  f"🔵 Azul = contexto  |  🟠 Naranja = celdas que bloquean números"),
            fg=self.COLOR_ESTADO_INF
        )

    # ------------------------------------------------------------------
    # TUTORIAL
    # ------------------------------------------------------------------

    def mostrar_tutorial(self):
        win = tk.Toplevel(self.root)
        win.title("Tutorial: Cómo resolver un Sudoku")
        win.resizable(False, False)
        win.grab_set()

        txt = scrolledtext.ScrolledText(
            win, width=64, height=38, font=("Courier New", 10),
            wrap=tk.WORD, state=tk.NORMAL, padx=12, pady=10,
            relief=tk.FLAT
        )
        txt.pack(fill=tk.BOTH, expand=True)

        # Definir estilos
        txt.tag_config("titulo",  font=("Arial", 14, "bold"), foreground="#1A237E", spacing3=6)
        txt.tag_config("h2",      font=("Arial", 12, "bold"), foreground="#0D47A1", spacing1=8, spacing3=4)
        txt.tag_config("h3",      font=("Arial", 11, "bold"), foreground="#1565C0", spacing1=4)
        txt.tag_config("body",    font=("Arial", 11))
        txt.tag_config("code",    font=("Courier New", 10), foreground="#263238", background="#ECEFF1",
                       lmargin1=20, lmargin2=20, spacing1=2, spacing3=2)
        txt.tag_config("tip",     font=("Arial", 11, "italic"), foreground="#2E7D32")
        txt.tag_config("warn",    font=("Arial", 11, "bold"),   foreground="#E65100")
        txt.tag_config("legend",  font=("Arial", 10), foreground="#555555")
        txt.tag_config("hr",      foreground="#BDBDBD")

        def ln(text="", tag="body"):
            txt.insert(tk.END, text + "\n", tag)

        # ── Título ────────────────────────────────────────────────────
        ln("🎯  CÓMO RESOLVER UN SUDOKU", "titulo")
        ln("─" * 62, "hr")

        # ── Reglas ───────────────────────────────────────────────────
        ln()
        ln("📋  REGLAS BÁSICAS", "h2")
        ln("El tablero es una cuadrícula de 9×9 casillas dividida en", "body")
        ln("9 bloques de 3×3. Rellena cada casilla con un dígito 1-9:", "body")
        ln()
        ln("  ✔  Cada FILA      → los 9 dígitos, sin repetir", "body")
        ln("  ✔  Cada COLUMNA   → los 9 dígitos, sin repetir", "body")
        ln("  ✔  Cada BLOQUE    → los 9 dígitos, sin repetir", "body")
        ln()
        ln("Ejemplo de tablero (· = casilla vacía):", "body")
        ln()
        ln("  ┌───────┬───────┬───────┐", "code")
        ln("  │ 5 3 · │ · 7 · │ · · · │", "code")
        ln("  │ 6 · · │ 1 9 5 │ · · · │", "code")
        ln("  │ · 9 8 │ · · · │ · 6 · │", "code")
        ln("  ├───────┼───────┼───────┤", "code")
        ln("  │ 8 · · │ · 6 · │ · · 3 │", "code")
        ln("  │ 4 · · │ 8 · 3 │ · · 1 │", "code")
        ln("  │ 7 · · │ · 2 · │ · · 6 │", "code")
        ln("  ├───────┼───────┼───────┤", "code")
        ln("  │ · 6 · │ · · · │ 2 8 · │", "code")
        ln("  │ · · · │ 4 1 9 │ · · 5 │", "code")
        ln("  │ · · · │ · 8 · │ · 7 9 │", "code")
        ln("  └───────┴───────┴───────┘", "code")
        ln()
        ln("─" * 62, "hr")

        # ── Estrategia 1: Naked Single ────────────────────────────────
        ln()
        ln("🔧  ESTRATEGIA 1 — NAKED SINGLE (número único)", "h2")
        ln("Si en una casilla solo cabe UN número (los otros 8 ya están", "body")
        ln("en su fila, columna o bloque), ese número es la respuesta.", "body")
        ln()
        ln("Ejemplo — Fila 1, Columna 3:", "h3")
        ln()
        ln("  Fila:   5  3  ·  ·  7  ·  ·  ·  ·", "code")
        ln("               ↑", "code")
        ln("  Ya hay: 5, 3, 7 en la fila", "code")
        ln("  Col 3 : 8, ·, ·, ·, 9, ·, ·, ·  → excluye: 8, 9", "code")
        ln("  Bloque : 5, 3, ·, 6, ·, ·, ·, 9, 8 → excluye: 6, 8, 9", "code")
        ln("  ─────────────────────────────────────────────────────────", "code")
        ln("  Números posibles: solo el  4  ← ¡esa es la respuesta!", "code")
        ln()
        ln("  💡 'Pista' detecta esto y te indica el número exacto.", "tip")
        ln()
        ln("─" * 62, "hr")

        # ── Estrategia 2: Hidden Single ───────────────────────────────
        ln()
        ln("🔧  ESTRATEGIA 2 — HIDDEN SINGLE (número oculto)", "h2")
        ln("Un número puede ir en varias casillas de una fila, pero si", "body")
        ln("todas las demás celdas vacías de esa fila/columna/bloque", "body")
        ln("lo descartan, esa casilla es la única opción.", "body")
        ln()
        ln("Ejemplo — ¿Dónde va el 7 en la fila 1?", "h3")
        ln()
        ln("  Fila 1:  5  3  4  ·  ·  ·  ·  ·  ·", "code")
        ln("                    a  b  c  d  e  f   ← vacías", "code")
        ln("  El 7 está en col 5 (bloquea b) y col 8 (bloquea e)", "code")
        ln("  El 7 está en bloque superior-derecho (bloquea d,e,f)", "code")
        ln("  ─────────────────────────────────────────────────────────", "code")
        ln("  Solo la casilla  a  (col 4) puede alojar el 7", "code")
        ln()
        ln("  💡 'Pista' marca en naranja las casillas que descartan", "tip")
        ln("  el número, dejando claro cuál es la elegida.", "tip")
        ln()
        ln("─" * 62, "hr")

        # ── Estrategia 3: Escaneo ─────────────────────────────────────
        ln()
        ln("🔧  ESTRATEGIA 3 — ESCANEO CRUZADO DE FILAS/COLUMNAS", "h2")
        ln("Para colocar un número en un bloque 3×3:", "body")
        ln("1. Mira en qué filas del bloque ya aparece ese número", "body")
        ln("   (en otras columnas) → esas filas quedan descartadas.", "body")
        ln("2. Haz lo mismo con las columnas.", "body")
        ln("3. Si solo queda una celda libre en la intersección, ahí va.", "body")
        ln()
        ln("Ejemplo — Colocar el 2 en el bloque central:", "h3")
        ln()
        ln("  El 2 aparece en fila 4 (otro bloque) → fila 4 descartada", "code")
        ln("  El 2 aparece en col 6 (otro bloque)  → col 6 descartada", "code")
        ln("  Solo queda fila 5, col 4 → ¡ese es el lugar del 2!", "code")
        ln()
        ln("─" * 62, "hr")

        # ── Leyenda de colores ────────────────────────────────────────
        ln()
        ln("🎨  LEYENDA DE COLORES DE ESTA APLICACIÓN", "h2")
        ln()
        ln("  Negro       → número dado por el puzzle (fijo)", "body")
        ln("  Azul        → número introducido por ti, sin conflicto", "body")
        ln("  Naranja     → ¡CONFLICTO! ese número ya existe en", "body")
        ln("                su fila, columna o caja", "warn")
        ln()
        ln("  Al pulsar 'Pista (Ayuda)':", "body")
        ln("  Fondo azul claro  → celdas de la misma fila/col/caja", "body")
        ln("  Fondo naranja     → celda que bloquea un número candidato", "body")
        ln()
        ln("─" * 62, "hr")

        # ── Consejos ──────────────────────────────────────────────────
        ln()
        ln("💡  CONSEJOS GENERALES", "h2")
        ln("  • Empieza por las casillas con más restricciones", "body")
        ln("    (filas/columnas/cajas casi completas).", "body")
        ln("  • Anota lápiz los candidatos posibles en cada celda.", "body")
        ln("  • Cuando coloques un número, revisa si resuelve más celdas", "body")
        ln("    en la misma fila, columna o bloque.", "body")
        ln("  • Usa 'Comprobar' para saber si vas bien.", "body")
        ln("  • ¡Usa 'Pista' sin miedo: te explica el razonamiento!", "tip")
        ln()

        txt.config(state=tk.DISABLED)
        tk.Button(win, text="  Cerrar  ", command=win.destroy,
                  bg="#F44336", fg="white", font=("Arial", 11), pady=4).pack(pady=8)

    # ------------------------------------------------------------------
    # INICIO / GUARDADO DE PARTIDA
    # ------------------------------------------------------------------

    def _inicio_con_guardado(self):
        dif = self.dificultad.get()
        guardado = cargar_partida(dif)
        if guardado:
            resp = messagebox.askyesno(
                "Partida guardada",
                f"Hay una partida de nivel «{dif}» guardada.\n¿Deseas retomarla?"
            )
            if resp:
                self._cargar_estado(guardado)
                return
        self.nuevo_juego()

    def _cambiar_dificultad(self, nueva_dif):
        if self.tablero_resuelto:
            actual = self.obtener_tablero_actual()
            if any(actual[i][j] == 0 for i in range(9) for j in range(9)):
                if messagebox.askyesno("Cambio de nivel",
                        f"¿Guardar la partida de «{self._dif_actual()}» antes de cambiar?"):
                    self._guardar_estado_actual()
        guardado = cargar_partida(nueva_dif)
        if guardado:
            if messagebox.askyesno("Partida guardada",
                    f"Hay una partida de nivel «{nueva_dif}» guardada.\n¿Deseas retomarla?"):
                self._cargar_estado(guardado)
                return
        self.nuevo_juego()

    def _dif_actual(self):
        return self.dificultad.get()

    def _guardar_estado_actual(self):
        guardar_partida(self._dif_actual(), self.tablero_resuelto,
                        self.tablero_fijo, self.obtener_tablero_actual())

    def _cargar_estado(self, datos):
        self.tablero_resuelto = datos["tablero_resuelto"]
        self.tablero_fijo     = datos["tablero_fijo"]
        tablero_actual        = datos["tablero_actual"]
        self._limpiar_resaltado_pista()
        self._ultimo_aviso_conflicto = -1

        for i in range(9):
            for j in range(9):
                self.entries[i][j].config(state=tk.NORMAL)

        for i in range(9):
            for j in range(9):
                entry = self.entries[i][j]
                entry.delete(0, tk.END)
                val = tablero_actual[i][j]
                if val != 0:
                    entry.insert(0, str(val))
                    entry.config(fg=self.COLOR_FIJO if self.tablero_fijo[i][j] != 0 else self.COLOR_USUARIO)

        self._actualizar_colores_conflicto()
        self.estado.config(
            text=f"Partida «{datos['dificultad']}» retomada. ¡A seguir!",
            fg=self.COLOR_ESTADO_OK
        )

    # ------------------------------------------------------------------
    # BOTONES DE GUARDADO MANUAL Y SALIDA
    # ------------------------------------------------------------------

    def guardar_partida_manual(self):
        if not self.tablero_resuelto:
            messagebox.showwarning("Sin partida", "No hay ninguna partida en curso.")
            return
        actual = self.obtener_tablero_actual()
        if not any(actual[i][j] == 0 for i in range(9) for j in range(9)):
            messagebox.showinfo("Ya completada", "El tablero ya está completo, no hace falta guardar.")
            return
        self._guardar_estado_actual()
        dif = self._dif_actual()
        self.estado.config(text=f"Partida «{dif}» guardada correctamente.", fg=self.COLOR_ESTADO_OK)
        messagebox.showinfo("Guardado",
            f"La partida de nivel «{dif}» se ha guardado.\nPuedes retomarla más adelante.")

    def retomar_partida_manual(self):
        dif = self._dif_actual()
        guardado = cargar_partida(dif)
        if not guardado:
            messagebox.showinfo("Sin guardado",
                f"No hay ninguna partida guardada para el nivel «{dif}».")
            return
        if messagebox.askyesno("Retomar partida",
                f"¿Retomar la partida guardada de nivel «{dif}»?\nSe perderá el progreso actual."):
            self._cargar_estado(guardado)

    def salir(self):
        if self.tablero_resuelto:
            actual = self.obtener_tablero_actual()
            if any(actual[i][j] == 0 for i in range(9) for j in range(9)):
                resp = messagebox.askyesnocancel("Salir",
                    "Hay una partida en curso.\n¿Deseas guardarla antes de salir?")
                if resp is None:
                    return
                if resp:
                    self._guardar_estado_actual()
        self.root.destroy()

    # ------------------------------------------------------------------
    # LÓGICA DE JUEGO
    # ------------------------------------------------------------------

    def validar_input(self, P, widget_nombre):
        if P == "":
            self.root.after(0, self._actualizar_colores_conflicto)
            return True
        # len(P)==1 evita que "89" (subcadena de "123456789") pase el filtro
        if len(P) == 1 and P in "123456789":
            i, j = self.widget_map[widget_nombre]
            if self.tablero_fijo[i][j] != 0:
                self.entries[i][j].delete(0, tk.END)
                self.entries[i][j].insert(0, str(self.tablero_fijo[i][j]))
                self.estado.config(text="No puedes cambiar los números iniciales.", fg=self.COLOR_ESTADO_ERR)
                return False
            self.root.after(0, self._actualizar_colores_conflicto)
            return True
        return False

    def nuevo_juego(self):
        dif = self.dificultad.get()
        self.estado.config(text=f"Generando tablero {dif}...", fg="black")
        self.root.update()

        self.tablero_resuelto = generar_tablero_resuelto()
        puzzle = crear_puzzle(self.tablero_resuelto, dif)
        self.tablero_fijo = copy.deepcopy(puzzle)
        self._limpiar_resaltado_pista()
        self._ultimo_aviso_conflicto = 0

        eliminar_guardado(dif)

        for i in range(9):
            for j in range(9):
                self.entries[i][j].config(state=tk.NORMAL)

        self.actualizar_tablero_gui(puzzle)
        self.estado.config(text="¡Buena suerte! Haz clic en una casilla vacía y pulsa 'Pista (Ayuda)'.",
                           fg="black")

    def actualizar_tablero_gui(self, tablero):
        for i in range(9):
            for j in range(9):
                entry = self.entries[i][j]
                entry.delete(0, tk.END)
                if tablero[i][j] != 0:
                    entry.insert(0, str(tablero[i][j]))
                    entry.config(fg=self.COLOR_FIJO)
                else:
                    entry.config(fg=self.COLOR_USUARIO)

    def obtener_tablero_actual(self):
        """Devuelve el estado actual del tablero como matriz 9×9 (0 = vacío)."""
        return [
            [int(self.entries[i][j].get()) if self.entries[i][j].get() != "" else 0
             for j in range(9)]
            for i in range(9)
        ]

    def comprobar_tablero(self):
        tablero_actual = self.obtener_tablero_actual()

        en_conflicto = celdas_en_conflicto(tablero_actual)
        if en_conflicto:
            messagebox.showwarning("Conflictos detectados",
                f"Hay {len(en_conflicto)} celda(s) con números repetidos "
                f"(marcadas en naranja).\nCorrige los conflictos antes de comprobar.")
            return

        vacias = [(i, j) for i in range(9) for j in range(9) if tablero_actual[i][j] == 0]
        if vacias:
            self.estado.config(
                text=f"Tablero incompleto: quedan {len(vacias)} casillas vacías.",
                fg="darkorange"
            )
            messagebox.showwarning("Tablero incompleto",
                f"Todavía quedan {len(vacias)} casillas sin rellenar.\n¡Sigue intentándolo!")
            return

        errores = [
            (i + 1, j + 1)
            for i in range(9) for j in range(9)
            if tablero_actual[i][j] != self.tablero_resuelto[i][j]
        ]
        if errores:
            for i in range(9):
                for j in range(9):
                    if self.tablero_fijo[i][j] == 0:
                        color = self.COLOR_ESTADO_ERR if tablero_actual[i][j] != self.tablero_resuelto[i][j] else self.COLOR_USUARIO
                        self.entries[i][j].config(fg=color)
            self.estado.config(
                text=f"Hay {len(errores)} error(es). Las celdas incorrectas aparecen en rojo.",
                fg=self.COLOR_ESTADO_ERR
            )
            messagebox.showerror("Solución incorrecta",
                f"Hay {len(errores)} celda(s) con errores (marcadas en rojo).\n¡Inténtalo de nuevo!")
        else:
            self._marcar_victoria()

    def marcar_seleccion(self, event):
        self._limpiar_resaltado_pista()
        event.widget.config(bg=self.COLOR_BG_SELECCION)

    def desmarcar_seleccion(self, event):
        i, j = self.widget_map[str(event.widget)]
        event.widget.config(bg=self._bg_normal(i, j))

    def verificar_victoria(self, event):
        for i in range(9):
            for j in range(9):
                val = self.entries[i][j].get()
                if val == "" or int(val) != self.tablero_resuelto[i][j]:
                    return
        self._marcar_victoria()

    def _marcar_victoria(self):
        eliminar_guardado(self._dif_actual())
        self._limpiar_resaltado_pista()
        self.estado.config(text="¡FELICIDADES! Has resuelto el Sudoku correctamente.", fg=self.COLOR_ESTADO_OK)
        messagebox.showinfo("¡Victoria!", "¡Enhorabuena! Has completado el Sudoku correctamente. 🎉")
        for i in range(9):
            for j in range(9):
                self.entries[i][j].config(state=tk.DISABLED)


# ==========================================
# PUNTO DE ENTRADA
# ==========================================

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()

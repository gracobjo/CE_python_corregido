import tkinter as tk
from tkinter import messagebox, scrolledtext
import random
import copy
import json
import os
import time
from datetime import datetime
from itertools import combinations

# ==========================================
# RUTAS DE GUARDADO
# ==========================================

DIRECTORIO_GUARDADO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sudoku_partidas")
RUTA_RECORDS = os.path.join(DIRECTORIO_GUARDADO, "records.json")

def ruta_guardado(dificultad):
    nombre = f"partida_{dificultad.lower().replace('á','a').replace('é','e')}.json"
    return os.path.join(DIRECTORIO_GUARDADO, nombre)

def formatear_tiempo(segundos):
    """Convierte segundos a texto hh:mm:ss o mm:ss."""
    segundos = max(0, int(segundos))
    h, resto = divmod(segundos, 3600)
    m, s = divmod(resto, 60)
    if h:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def guardar_partida(dificultad, tablero_resuelto, tablero_fijo, tablero_actual, segundos_juego=0):
    os.makedirs(DIRECTORIO_GUARDADO, exist_ok=True)
    datos = {
        "dificultad":       dificultad,
        "tablero_resuelto": tablero_resuelto,
        "tablero_fijo":     tablero_fijo,
        "tablero_actual":   tablero_actual,
        "segundos_juego":   int(segundos_juego),
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

def cargar_records():
    if not os.path.exists(RUTA_RECORDS):
        return {}
    with open(RUTA_RECORDS, "r", encoding="utf-8") as f:
        return json.load(f)

def registrar_partida_terminada(dificultad, segundos):
    """
    Guarda el tiempo de la partida y actualiza el récord.
    Devuelve (es_record, mejor_segundos, historial_reciente).
    """
    os.makedirs(DIRECTORIO_GUARDADO, exist_ok=True)
    records = cargar_records()
    clave = dificultad
    entrada = records.get(clave, {"mejor": None, "partidas": []})
    mejor_antes = entrada.get("mejor")
    es_record = mejor_antes is None or segundos < mejor_antes
    if es_record:
        entrada["mejor"] = int(segundos)
    partida = {
        "segundos": int(segundos),
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tiempo": formatear_tiempo(segundos),
    }
    entrada.setdefault("partidas", []).append(partida)
    # Conservar las 10 más recientes
    entrada["partidas"] = entrada["partidas"][-10:]
    records[clave] = entrada
    with open(RUTA_RECORDS, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    return es_record, entrada["mejor"], entrada["partidas"]

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

def candidatos_celda(tablero, fila, col):
    """Números 1-9 que caben en (fila, col) si está vacía."""
    if tablero[fila][col] != 0:
        return []
    return [n for n in range(1, 10) if es_valido(tablero, fila, col, n)]

def mapa_candidatos(tablero):
    """Matriz 9×9 con la lista de candidatos de cada celda vacía."""
    return [[candidatos_celda(tablero, i, j) for j in range(9)] for i in range(9)]

def unicos_en_zona(cands):
    """
    Devuelve un set de (i, j, num) donde 'num' solo cabe en esa celda
    dentro de su fila, su columna o su caja (hidden single).
    """
    unicos = set()
    for i in range(9):
        for num in range(1, 10):
            celdas = [(i, j) for j in range(9) if num in cands[i][j]]
            if len(celdas) == 1:
                unicos.add((celdas[0][0], celdas[0][1], num))
    for j in range(9):
        for num in range(1, 10):
            celdas = [(i, j) for i in range(9) if num in cands[i][j]]
            if len(celdas) == 1:
                unicos.add((celdas[0][0], celdas[0][1], num))
    for bi in range(3):
        for bj in range(3):
            for num in range(1, 10):
                celdas = [
                    (bi * 3 + di, bj * 3 + dj)
                    for di in range(3) for dj in range(3)
                    if num in cands[bi * 3 + di][bj * 3 + dj]
                ]
                if len(celdas) == 1:
                    unicos.add((celdas[0][0], celdas[0][1], num))
    return unicos

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

def contar_soluciones(tablero, limite=2):
    """Cuenta soluciones (hasta 'limite'). Usado para garantizar unicidad del puzzle."""
    t = copy.deepcopy(tablero)
    contador = [0]

    def buscar():
        if contador[0] >= limite:
            return
        for i in range(9):
            for j in range(9):
                if t[i][j] == 0:
                    for num in range(1, 10):
                        if es_valido(t, i, j, num):
                            t[i][j] = num
                            buscar()
                            t[i][j] = 0
                            if contador[0] >= limite:
                                return
                    return
        contador[0] += 1

    buscar()
    return contador[0]

def crear_puzzle(tablero_resuelto, dificultad):
    """
    Genera un puzzle con solución ÚNICA.
    Solo elimina una celda si el tablero sigue teniendo exactamente 1 solución.
    """
    puzzle = copy.deepcopy(tablero_resuelto)
    celdas = [(i, j) for i in range(9) for j in range(9)]
    random.shuffle(celdas)
    objetivo = {"Fácil": 35, "Medio": 45, "Difícil": 55}.get(dificultad, 45)
    eliminadas = 0
    for fila, col in celdas:
        if eliminadas >= objetivo:
            break
        backup = puzzle[fila][col]
        puzzle[fila][col] = 0
        if contar_soluciones(puzzle, limite=2) != 1:
            puzzle[fila][col] = backup  # restaurar: rompería la unicidad
        else:
            eliminadas += 1
    return puzzle

def reparar_unicidad(tablero_fijo, tablero_resuelto):
    """
    Si el puzzle fijo admite más de una solución (partidas antiguas),
    rellena pistas mínimas desde la solución hasta dejar exactamente 1.
    Devuelve (nuevo_fijo, num_pistas_añadidas).
    """
    fijo = copy.deepcopy(tablero_fijo)
    if contar_soluciones(fijo, limite=2) == 1:
        return fijo, 0
    vacias = [(i, j) for i in range(9) for j in range(9) if fijo[i][j] == 0]
    random.shuffle(vacias)
    anadidas = 0
    for i, j in vacias:
        if contar_soluciones(fijo, limite=2) == 1:
            break
        fijo[i][j] = tablero_resuelto[i][j]
        anadidas += 1
    return fijo, anadidas

def buscar_rectangulo_mortal(cands):
    """
    Busca 4 casillas vacías en rectángulo (2 filas × 2 cols) con el MISMO par
    de candidatos {a,b}. Eso permite dos rellenos (diagonales) → ambigüedad.
    Devuelve (par_tuple, lista_4_celdas) o None.
    """
    por_par = {}
    for i in range(9):
        for j in range(9):
            if len(cands[i][j]) == 2:
                clave = tuple(sorted(cands[i][j]))
                por_par.setdefault(clave, []).append((i, j))

    for par, celdas in por_par.items():
        if len(celdas) < 4:
            continue
        filas = sorted({i for i, _ in celdas})
        cols = sorted({j for _, j in celdas})
        set_celdas = set(celdas)
        for r1, r2 in combinations(filas, 2):
            for c1, c2 in combinations(cols, 2):
                rect = [(r1, c1), (r1, c2), (r2, c1), (r2, c2)]
                if all(pos in set_celdas for pos in rect):
                    if all(tuple(sorted(cands[i][j])) == par for i, j in rect):
                        return par, rect
    return None

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

def celdas_que_bloquean(tablero, fila, col, num):
    """Celdas de la misma fila/columna/caja que ya contienen 'num'."""
    bloquean = []
    for jj in range(9):
        if jj != col and tablero[fila][jj] == num:
            bloquean.append((fila, jj))
    for ii in range(9):
        if ii != fila and tablero[ii][col] == num:
            bloquean.append((ii, col))
    ci, cj = 3 * (fila // 3), 3 * (col // 3)
    for di in range(3):
        for dj in range(3):
            ni, nj = ci + di, cj + dj
            if (ni, nj) != (fila, col) and tablero[ni][nj] == num:
                if (ni, nj) not in bloquean:
                    bloquean.append((ni, nj))
    return bloquean

def analizar_bloqueo(tablero_fijo, tablero_actual, tablero_resuelto):
    """
    Detecta callejón sin salida y calcula undos.
    Devuelve dict con vacias_bloqueadas, undos_minimos, undos_todos_errores.
    Cada undo: (i, j, valor_actual, valor_correcto, motivo)
    """
    vacias = [
        (i, j) for i in range(9) for j in range(9)
        if tablero_actual[i][j] == 0
    ]
    vacias_bloqueadas = []
    undos_minimos = {}  # (i,j) -> undo info

    for i, j in vacias:
        cands = candidatos_celda(tablero_actual, i, j)
        sol = tablero_resuelto[i][j]
        # Bloqueada si no hay candidatos o la solución ya no es legal
        if not cands or sol not in cands:
            vacias_bloqueadas.append((i, j, sol, cands))
            for bi, bj in celdas_que_bloquean(tablero_actual, i, j, sol):
                if tablero_fijo[bi][bj] != 0:
                    continue  # no se puede deshacer un fijo
                clave = (bi, bj)
                if clave not in undos_minimos:
                    undos_minimos[clave] = (
                        bi, bj,
                        tablero_actual[bi][bj],
                        tablero_resuelto[bi][bj],
                        f"bloquea el {sol} en fila {i+1}, col {j+1}",
                    )

    undos_todos = []
    for i in range(9):
        for j in range(9):
            if tablero_fijo[i][j] != 0:
                continue
            val = tablero_actual[i][j]
            if val != 0 and val != tablero_resuelto[i][j]:
                undos_todos.append(
                    (i, j, val, tablero_resuelto[i][j], "no coincide con la solución")
                )

    return {
        "vacias": vacias,
        "vacias_bloqueadas": vacias_bloqueadas,
        "undos_minimos": list(undos_minimos.values()),
        "undos_todos": undos_todos,
    }

# ==========================================
# CELDA CON CANDIDATOS
# ==========================================

class CeldaSudoku(tk.Frame):
    """
    Casilla del tablero.
    - Vacía: candidatos 1-9 en pequeño (3×3), clicables.
    - Con valor: número grande encima (place), sin destruir/ocultar candidatos.
    """

    TAM = 58
    FONT_VALOR = ("Arial", 20, "bold")
    FONT_CAND = ("Arial", 7)
    FONT_CAND_UNIC = ("Arial", 7, "bold")

    COLOR_CAND_NORMAL = "#616161"
    COLOR_CAND_NAKED = "#2E7D32"
    COLOR_CAND_HIDDEN = "#6A1B9A"
    COLOR_CAND_AMB = "#0277BD"   # azul: dígito correcto ante ambigüedad (2 soluciones)
    COLOR_CAND_VACIO = "#BDBDBD"

    def __init__(self, parent, app, fila, col, bg_normal):
        super().__init__(
            parent, width=self.TAM, height=self.TAM,
            bg=bg_normal, highlightthickness=1,
            highlightbackground="#9E9E9E", bd=0,
        )
        self.grid_propagate(False)
        self.pack_propagate(False)

        self.app = app
        self.fila = fila
        self.col = col
        self.bg_normal = bg_normal
        self._valor = 0
        self._fijo = False
        self._bloqueada = False
        self._bg_actual = bg_normal
        self._posibles = set()

        # Capa inferior: candidatos (siempre montada)
        self.frame_cands = tk.Frame(self, bg=bg_normal, bd=0, highlightthickness=0)
        self.frame_cands.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.cand_btns = {}

        for n in range(1, 10):
            r, c = (n - 1) // 3, (n - 1) % 3
            btn = tk.Label(
                self.frame_cands, text="", width=2,
                font=self.FONT_CAND, fg=self.COLOR_CAND_NORMAL,
                bg=bg_normal, cursor="hand2",
            )
            btn.grid(row=r, column=c, sticky="nsew")
            # Button-1: siempre selecciona la casilla (también en huecos vacíos)
            btn.bind("<Button-1>", lambda e, num=n: self._pulsar_candidato(num, colocar=False))
            btn.bind("<ButtonRelease-1>", lambda e, num=n: self._pulsar_candidato(num, colocar=True))
            self.cand_btns[n] = btn

        for r in range(3):
            self.frame_cands.rowconfigure(r, weight=1)
        for c in range(3):
            self.frame_cands.columnconfigure(c, weight=1)

        # Capa superior: valor (place encima; no se destruye)
        self.lbl_valor = tk.Label(
            self, text="", font=self.FONT_VALOR,
            bg=bg_normal, fg=app.COLOR_FIJO,
        )
        # Empieza oculta (fuera / tamaño 0) — se muestra con place al tener valor
        self.lbl_valor.place_forget()

        self.bind("<Button-1>", self._seleccionar)
        self.frame_cands.bind("<Button-1>", self._seleccionar)
        self.lbl_valor.bind("<Button-1>", self._seleccionar)
        self.lbl_valor.bind("<ButtonRelease-1>", self._seleccionar)
        # Borrar número de usuario: doble clic o clic derecho
        self.lbl_valor.bind("<Double-Button-1>", self._borrar_si_usuario)
        self.lbl_valor.bind("<Button-3>", self._borrar_si_usuario)
        self.bind("<Double-Button-1>", self._borrar_si_usuario)
        self.bind("<Button-3>", self._borrar_si_usuario)

    # ── API pública ───────────────────────────────────────────────────

    def valor(self):
        return self._valor

    def es_fijo(self):
        return self._fijo

    def set_valor(self, valor, fijo=False, color=None):
        self._valor = int(valor) if valor else 0
        self._fijo = bool(fijo) and self._valor != 0
        if self._valor == 0:
            self.lbl_valor.place_forget()
            self.lbl_valor.config(text="")
            self.frame_cands.lift()
        else:
            fg = color if color else (
                self.app.COLOR_FIJO if self._fijo else self.app.COLOR_USUARIO
            )
            self.lbl_valor.config(text=str(self._valor), fg=fg, bg=self._bg_actual)
            self.lbl_valor.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.lbl_valor.lift()

    def set_fg(self, color):
        if self._valor != 0:
            self.lbl_valor.config(fg=color)

    def set_bg(self, color):
        self._bg_actual = color
        self.config(bg=color)
        self.frame_cands.config(bg=color)
        self.lbl_valor.config(bg=color)
        for btn in self.cand_btns.values():
            btn.config(bg=color)

    def restaurar_bg(self):
        self.set_bg(self.bg_normal)

    def set_bloqueada(self, bloqueada):
        self._bloqueada = bloqueada

    def actualizar_candidatos(self, posibles, unicos_hidden, bg_extra=None,
                              valor_solucion=None, forzar_solucion=False):
        """
        posibles: candidatos legales con el tablero actual.
        unicos_hidden: números únicos en fila/col/caja (pueden ser falsos si hay errores).
        valor_solucion: dígito correcto de la casilla; solo se colorea verde/morado
                        si el candidato único coincide con él (propuesta inequívoca real).
        forzar_solucion: True en rectángulo mortal / ambigüedad → marcar en azul
                         el dígito de la solución guardada de la partida.
        """
        if self._valor != 0:
            return
        self._posibles = set(posibles)
        naked = len(posibles) == 1
        for n, btn in self.cand_btns.items():
            if n in self._posibles:
                es_inequivoco = (
                    valor_solucion is not None
                    and n == valor_solucion
                    and (naked or n in unicos_hidden)
                )
                es_ambiguedad = (
                    forzar_solucion
                    and valor_solucion is not None
                    and n == valor_solucion
                    and not es_inequivoco
                )
                if es_inequivoco and naked:
                    btn.config(
                        text=str(n), fg=self.COLOR_CAND_NAKED,
                        font=self.FONT_CAND_UNIC, cursor="hand2",
                    )
                elif es_inequivoco:
                    btn.config(
                        text=str(n), fg=self.COLOR_CAND_HIDDEN,
                        font=self.FONT_CAND_UNIC, cursor="hand2",
                    )
                elif es_ambiguedad:
                    btn.config(
                        text=str(n), fg=self.COLOR_CAND_AMB,
                        font=self.FONT_CAND_UNIC, cursor="hand2",
                    )
                elif (
                    forzar_solucion
                    and valor_solucion is not None
                    and n != valor_solucion
                ):
                    # Candidato descartado por la solución de la partida
                    btn.config(
                        text=str(n), fg="#CFD8DC",
                        font=self.FONT_CAND, cursor="hand2",
                    )
                else:
                    # Varios candidatos o "único" engañoso por números mal puestos
                    btn.config(
                        text=str(n), fg=self.COLOR_CAND_NORMAL,
                        font=self.FONT_CAND, cursor="hand2",
                    )
            else:
                btn.config(
                    text="", fg=self.COLOR_CAND_VACIO,
                    font=self.FONT_CAND, cursor="arrow",
                )
        # Fondo verdoso solo si el naked single es el de la solución
        if (
            bg_extra == "#E8F5E9"
            and not (
                naked
                and valor_solucion is not None
                and posibles
                and posibles[0] == valor_solucion
            )
        ):
            bg_extra = None
        if bg_extra is not None:
            self.set_bg(bg_extra)

    # ── Eventos ───────────────────────────────────────────────────────

    def _seleccionar(self, event=None):
        if self._bloqueada:
            return "break"
        self.app.seleccionar_celda(self.fila, self.col)
        return "break"

    def _borrar_si_usuario(self, event=None):
        if self._bloqueada or self._fijo or self._valor == 0:
            return "break"
        self.app.seleccionar_celda(self.fila, self.col)
        self.app.colocar_numero(self.fila, self.col, 0)
        return "break"

    def _pulsar_candidato(self, num, colocar=True):
        """Cualquier clic en la rejilla selecciona la casilla; al soltar puede colocar."""
        if self._bloqueada:
            return "break"
        self.app.seleccionar_celda(self.fila, self.col)
        if not colocar or self._fijo or self._valor != 0:
            return "break"
        if num in self._posibles:
            self.app.colocar_numero(self.fila, self.col, num)
        return "break"


# ==========================================
# INTERFAZ GRÁFICA
# ==========================================

class SudokuApp:

    # ── Paleta de colores ─────────────────────────────────────────────
    COLOR_FIJO          = "black"
    COLOR_USUARIO       = "#1565C0"
    COLOR_CONFLICTO     = "#E65100"
    COLOR_ESTADO_OK     = "green"
    COLOR_ESTADO_ERR    = "red"
    COLOR_ESTADO_INF    = "#1565C0"

    COLOR_BG_SELECCION  = "#FFF59D"
    COLOR_BG_PAR        = "#FFFFFF"
    COLOR_BG_IMPAR      = "#E0E0E0"
    COLOR_BG_CONTEXTO   = "#DDEEFF"
    COLOR_BG_BLOQUEANTE = "#FFE0B2"
    COLOR_BG_CONFLICTO  = "#FFCDD2"   # rojo claro – celdas en conflicto / que bloquean

    def __init__(self, root):
        self.root = root
        self.root.title("Sudoku en Python")
        self.root.resizable(False, False)

        self.dificultad       = tk.StringVar(value="Medio")
        self.tablero_resuelto = []
        self.tablero_fijo     = []
        self.celdas           = [[None] * 9 for _ in range(9)]
        self._celda_focus     = None
        self._celdas_resaltadas        = set()   # pista / bloqueos temporales
        self._celdas_conflicto_bg      = set()   # fondo rojo de conflictos activos
        self._ultimo_aviso_conflicto   = 0
        self._actualizando_cands       = False
        self._ambiguedad_ofrecida      = None  # firma del rectángulo ya ofrecido

        # Temporizador de partida
        self._segundos_acumulados = 0      # tiempo ya jugado (p. ej. al retomar)
        self._inicio_tramo = None          # time.time() del tramo actual
        self._timer_activo = False
        self._timer_en_pausa = False       # True tras «Guardar partida»
        self._timer_after_id = None
        self._partida_terminada = False

        self.crear_interfaz()
        self.root.after(100, self._inicio_con_guardado)

    # ------------------------------------------------------------------
    # CONSTRUCCIÓN DE LA INTERFAZ
    # ------------------------------------------------------------------

    def crear_interfaz(self):
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
        tk.Button(frame1, text="Deshacer bloqueo", command=self.deshacer_bloqueo,
                  bg="#D32F2F", fg="white", width=14).pack(side=tk.LEFT, padx=4)

        frame2 = tk.Frame(self.root, pady=2)
        frame2.pack()

        tk.Button(frame2, text="💾  Guardar partida", command=self.guardar_partida_manual,
                  bg="#795548", fg="white", width=16).pack(side=tk.LEFT, padx=4)
        tk.Button(frame2, text="📂  Retomar partida", command=self.retomar_partida_manual,
                  bg="#607D8B", fg="white", width=16).pack(side=tk.LEFT, padx=4)
        tk.Button(frame2, text="🚪  Salir",           command=self.salir,
                  bg="#F44336", fg="white", width=10).pack(side=tk.LEFT, padx=4)
        tk.Button(frame2, text="⏱  Récords",         command=self.mostrar_records,
                  bg="#455A64", fg="white", width=10).pack(side=tk.LEFT, padx=4)

        # Temporizador visible
        frame_timer = tk.Frame(self.root, pady=2)
        frame_timer.pack()
        tk.Label(frame_timer, text="Tiempo:", font=("Arial", 11)).pack(side=tk.LEFT, padx=(4, 2))
        self.lbl_tiempo = tk.Label(
            frame_timer, text="00:00", font=("Consolas", 14, "bold"),
            fg="#0D47A1", width=10, anchor="w"
        )
        self.lbl_tiempo.pack(side=tk.LEFT)

        # Leyenda de candidatos
        leyenda = tk.Frame(self.root, pady=2)
        leyenda.pack()
        tk.Label(leyenda, text="Candidatos:", font=("Arial", 9)).pack(side=tk.LEFT, padx=(8, 2))
        tk.Label(leyenda, text="● normal", fg=CeldaSudoku.COLOR_CAND_NORMAL,
                 font=("Arial", 9)).pack(side=tk.LEFT, padx=6)
        tk.Label(leyenda, text="● forzado (casilla)", fg=CeldaSudoku.COLOR_CAND_NAKED,
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=6)
        tk.Label(leyenda, text="● forzado (fila/col/caja)", fg=CeldaSudoku.COLOR_CAND_HIDDEN,
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=6)
        tk.Label(leyenda, text="● ambigüedad→solución", fg=CeldaSudoku.COLOR_CAND_AMB,
                 font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=6)
        tk.Label(leyenda, text="(gris = posible · verde/morado = inequívoco · Supr/doble clic = borrar)",
                 font=("Arial", 8), fg="#757575").pack(side=tk.LEFT, padx=8)

        self.frame_tablero = tk.Frame(self.root, bd=2, relief=tk.SOLID)
        self.frame_tablero.pack(padx=10, pady=8)

        for i in range(9):
            for j in range(9):
                bg = self._bg_normal(i, j)
                celda = CeldaSudoku(self.frame_tablero, self, i, j, bg)
                pad_x = (3, 1) if j % 3 == 0 else (1, 3) if j % 3 == 2 else (1, 1)
                pad_y = (3, 1) if i % 3 == 0 else (1, 3) if i % 3 == 2 else (1, 1)
                celda.grid(row=i, column=j, padx=pad_x, pady=pad_y)
                self.celdas[i][j] = celda

        self.estado = tk.Label(
            self.root,
            text="Clic en un candidato pequeño para colocarlo. Los verdes/morados marcan unicidades.",
            font=("Arial", 11), fg=self.COLOR_ESTADO_INF,
            wraplength=680, justify=tk.LEFT, pady=6
        )
        self.estado.pack(padx=10)

        # Teclado global (bind_all: funciona tras messagebox / clic en botones)
        self.root.bind_all("<KeyPress>", self._tecla_global)
        self.root.bind_all("<Delete>", self._tecla_borrar)
        self.root.bind_all("<KP_Delete>", self._tecla_borrar)
        self.root.bind_all("<BackSpace>", self._tecla_borrar)
        self.root.protocol("WM_DELETE_WINDOW", self.salir)

    # ------------------------------------------------------------------
    # HELPERS DE COLOR / ESTADO DE CELDAS
    # ------------------------------------------------------------------

    def _bg_normal(self, i, j):
        return self.COLOR_BG_PAR if (i // 3 + j // 3) % 2 == 0 else self.COLOR_BG_IMPAR

    def seleccionar_celda(self, i, j):
        """Marca la casilla activa (sin usar FocusIn/Out de Tk)."""
        self._reanudar_timer_si_pausado()
        prev = self._celda_focus
        self._limpiar_resaltado_pista()
        if prev and prev != (i, j):
            self.celdas[prev[0]][prev[1]].restaurar_bg()
        self._celda_focus = (i, j)
        self.celdas[i][j].set_bg(self.COLOR_BG_SELECCION)
        self._refrescar_candidatos()
        self._actualizar_colores_conflicto()

    def colocar_numero(self, i, j, num):
        """Coloca o borra (num=0) un número de usuario y refresca candidatos."""
        if not self.tablero_fijo:
            return
        if self.tablero_fijo[i][j] != 0:
            self.estado.config(text="No puedes cambiar los números iniciales.", fg=self.COLOR_ESTADO_ERR)
            return
        celda = self.celdas[i][j]
        if celda._bloqueada:
            return
        self._reanudar_timer_si_pausado()
        self._limpiar_resaltado_pista()
        self._celda_focus = (i, j)
        celda.set_valor(num, fijo=False, color=self.COLOR_USUARIO)
        if num != 0:
            celda.set_bg(self.COLOR_BG_SELECCION)
        else:
            celda.restaurar_bg()
            celda.set_bg(self.COLOR_BG_SELECCION)
        self._refrescar_candidatos()
        self._actualizar_colores_conflicto()
        self.verificar_victoria()

    def _refrescar_candidatos(self):
        if not self.tablero_fijo or self._actualizando_cands:
            return
        self._actualizando_cands = True
        try:
            tablero = self.obtener_tablero_actual()
            cands = mapa_candidatos(tablero)
            hidden = unicos_en_zona(cands)
            rect = buscar_rectangulo_mortal(cands)
            celdas_rect = set(rect[1]) if rect else set()
            for i in range(9):
                for j in range(9):
                    if tablero[i][j] != 0:
                        continue
                    unicos_aqui = {n for (ii, jj, n) in hidden if ii == i and jj == j}
                    en_pista = (i, j) in self._celdas_resaltadas
                    en_focus = self._celda_focus == (i, j)
                    bg_extra = None
                    sol = (
                        self.tablero_resuelto[i][j]
                        if self.tablero_resuelto else None
                    )
                    naked_real = (
                        len(cands[i][j]) == 1
                        and sol is not None
                        and cands[i][j][0] == sol
                    )
                    if not en_pista and not en_focus:
                        self.celdas[i][j].restaurar_bg()
                        if naked_real:
                            bg_extra = "#E8F5E9"
                        elif (i, j) in celdas_rect:
                            bg_extra = "#E3F2FD"  # azul claro: rectángulo ambiguo
                    elif en_focus and not en_pista:
                        bg_extra = self.COLOR_BG_SELECCION
                    self.celdas[i][j].actualizar_candidatos(
                        cands[i][j], unicos_aqui,
                        bg_extra=bg_extra, valor_solucion=sol,
                        forzar_solucion=(i, j) in celdas_rect,
                    )
            # Aviso + oferta de relleno si hay rectángulo mortal
            if rect and not self._celdas_resaltadas:
                a, b = rect[0]
                self.estado.config(
                    text=(
                        f"Ambigüedad {a}/{b}: 4 casillas con el mismo par. "
                        f"Azul = elige este; gris claro = no. "
                        f"Pulsa «Pista» o acepta rellenarlas."
                    ),
                    fg=self.COLOR_ESTADO_INF,
                )
                firma = (rect[0], tuple(rect[1]))
                if self._ambiguedad_ofrecida != firma:
                    self._ambiguedad_ofrecida = firma
                    self.root.after(
                        50, lambda r=rect: self._ofrecer_resolver_ambiguedad(r)
                    )
        finally:
            self._actualizando_cands = False

    def _ofrecer_resolver_ambiguedad(self, rect):
        """Pregunta una sola vez si rellenar las 4 casillas del rectángulo mortal."""
        if self._partida_terminada or not self.tablero_resuelto:
            return
        par, celdas = rect
        actual = self.obtener_tablero_actual()
        if any(actual[i][j] != 0 for i, j in celdas):
            return
        a, b = par
        detalles = "\n".join(
            f"  · fila {i+1}, col {j+1} → {self.tablero_resuelto[i][j]}"
            for i, j in celdas
        )
        if messagebox.askyesno(
            "Ambigüedad (2 soluciones posibles)",
            f"Hay 4 casillas con el par {{{a},{b}}} en rectángulo.\n"
            f"La lógica admite dos diagonales; esta partida elige:\n\n"
            f"{detalles}\n\n"
            f"¿Colocar esos 4 números ahora?",
        ):
            for i, j in celdas:
                self.colocar_numero(i, j, self.tablero_resuelto[i][j])
            self.estado.config(
                text="Ambigüedad resuelta con la solución de esta partida.",
                fg=self.COLOR_ESTADO_OK,
            )

    # ------------------------------------------------------------------
    # DETECCIÓN DE CONFLICTOS EN TIEMPO REAL
    # ------------------------------------------------------------------

    def _limpiar_fondos_conflicto(self):
        """Quita el fondo rojo de conflictos previos (respeta selección y pista)."""
        for i, j in list(self._celdas_conflicto_bg):
            if (i, j) in self._celdas_resaltadas:
                continue
            if self._celda_focus == (i, j):
                self.celdas[i][j].set_bg(self.COLOR_BG_SELECCION)
            else:
                self.celdas[i][j].restaurar_bg()
        self._celdas_conflicto_bg.clear()

    def _marcar_celdas_conflicto(self, celdas, mantener_seleccion=True):
        """Pone fondo rojo claro en las celdas indicadas."""
        self._limpiar_fondos_conflicto()
        for i, j in celdas:
            if mantener_seleccion and self._celda_focus == (i, j):
                # Selección amarilla + borde visual: prioriza rojo suave distinto
                self.celdas[i][j].set_bg("#FFECB3")
            else:
                self.celdas[i][j].set_bg(self.COLOR_BG_CONFLICTO)
            self._celdas_conflicto_bg.add((i, j))

    def _actualizar_colores_conflicto(self):
        if not self.tablero_fijo:
            return
        tablero_actual = self.obtener_tablero_actual()
        en_conflicto   = celdas_en_conflicto(tablero_actual)

        for i in range(9):
            for j in range(9):
                celda = self.celdas[i][j]
                if self.tablero_fijo[i][j] != 0:
                    celda.set_fg(self.COLOR_FIJO)
                elif celda.valor() != 0:
                    color = self.COLOR_CONFLICTO if (i, j) in en_conflicto else self.COLOR_USUARIO
                    celda.set_fg(color)

        # Fondo rojo en todas las celdas en conflicto (también las fijas si chocan)
        if en_conflicto:
            self._marcar_celdas_conflicto(en_conflicto)
        else:
            self._limpiar_fondos_conflicto()

        num_conf = len(en_conflicto)
        if num_conf != self._ultimo_aviso_conflicto:
            self._ultimo_aviso_conflicto = num_conf
            if num_conf > 0:
                self.estado.config(
                    text=(f"⚠️  {num_conf} celda(s) en conflicto (fondo rojo / número naranja): "
                          f"repetido en fila, columna o caja."),
                    fg=self.COLOR_CONFLICTO
                )
            elif self.estado.cget("fg") == self.COLOR_CONFLICTO:
                self.estado.config(text="Sin conflictos. ¡Buen trabajo!", fg=self.COLOR_ESTADO_OK)

    # ------------------------------------------------------------------
    # RESALTADO DE PISTA
    # ------------------------------------------------------------------

    def _limpiar_resaltado_pista(self):
        for i, j in self._celdas_resaltadas:
            if self._celda_focus == (i, j):
                self.celdas[i][j].set_bg(self.COLOR_BG_SELECCION)
            elif (i, j) in self._celdas_conflicto_bg:
                self.celdas[i][j].set_bg(self.COLOR_BG_CONFLICTO)
            else:
                self.celdas[i][j].restaurar_bg()
        self._celdas_resaltadas.clear()

    def _celdas_contexto(self, i, j):
        celdas = set()
        for jj in range(9):
            celdas.add((i, jj))
        for ii in range(9):
            celdas.add((ii, j))
        ci, cj = 3 * (i // 3), 3 * (j // 3)
        for di in range(3):
            for dj in range(3):
                celdas.add((ci + di, cj + dj))
        celdas.discard((i, j))
        return celdas

    def _celda_bloqueante(self, tablero, i, j, num):
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
        for num in posibles:
            otros_fila = [
                (i, jj) for jj in range(9)
                if jj != j and tablero[i][jj] == 0 and es_valido(tablero, i, jj, num)
            ]
            if not otros_fila:
                justif = [(i, jj) for jj in range(9) if jj != j and tablero[i][jj] == 0]
                return num, f"fila {i+1}", justif

            otros_col = [
                (ii, j) for ii in range(9)
                if ii != i and tablero[ii][j] == 0 and es_valido(tablero, ii, j, num)
            ]
            if not otros_col:
                justif = [(ii, j) for ii in range(9) if ii != i and tablero[ii][j] == 0]
                return num, f"columna {j+1}", justif

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
        if self._celda_focus is None:
            self.estado.config(text="Primero haz clic dentro de una casilla vacía.", fg=self.COLOR_ESTADO_ERR)
            return

        i, j = self._celda_focus

        if self.tablero_fijo[i][j] != 0:
            self.estado.config(text="Esta casilla ya tiene un número fijo.", fg=self.COLOR_ESTADO_ERR)
            return
        if self.celdas[i][j].valor() != 0:
            self.estado.config(text="Borra el número de la casilla antes de pedir una pista.", fg=self.COLOR_ESTADO_ERR)
            return

        self._limpiar_resaltado_pista()

        tablero_actual = self.obtener_tablero_actual()
        posibles = candidatos_celda(tablero_actual, i, j)

        if not posibles:
            self.estado.config(
                text="No hay números válidos para esa casilla. Revisa los números introducidos.",
                fg=self.COLOR_ESTADO_ERR
            )
            return

        for ci, cj in self._celdas_contexto(i, j):
            self.celdas[ci][cj].set_bg(self.COLOR_BG_CONTEXTO)
            self._celdas_resaltadas.add((ci, cj))

        bloqueantes = {}
        for num in range(1, 10):
            if num not in posibles:
                cb = self._celda_bloqueante(tablero_actual, i, j, num)
                if cb:
                    bloqueantes[num] = cb

        for num, (bi, bj) in bloqueantes.items():
            self.celdas[bi][bj].set_bg(self.COLOR_BG_BLOQUEANTE)
            self._celdas_resaltadas.add((bi, bj))

        def zona(bi, bj):
            if bi == i:
                return f"fila {i+1} (col {bj+1})"
            if bj == j:
                return f"col {j+1} (fila {bi+1})"
            return f"caja ({bi+1},{bj+1})"

        excl_partes = [f"{n}→{zona(*cb)}" for n, cb in list(bloqueantes.items())[:5]]
        excl_txt = " | ".join(excl_partes)
        if len(bloqueantes) > 5:
            excl_txt += "…"

        if len(posibles) == 1:
            num = posibles[0]
            self.estado.config(
                text=(f"Fila {i+1}, col {j+1}: ¡Sólo puede ser {num}! "
                      f"(Naked Single)\n"
                      f"Los demás están bloqueados: {excl_txt}\n"
                      f"🔵 Azul = contexto  |  🟠 Naranja = celda bloqueante  |  🟢 candidato único"),
                fg=self.COLOR_ESTADO_OK
            )
            return

        hs = self._detectar_hidden_single(tablero_actual, i, j, posibles)
        if hs:
            num, zona_hs, justif_celdas = hs
            for ci, cj in justif_celdas:
                self.celdas[ci][cj].set_bg(self.COLOR_BG_BLOQUEANTE)
                self._celdas_resaltadas.add((ci, cj))
            self.estado.config(
                text=(f"Fila {i+1}, col {j+1}: Debe ser {num} (Hidden Single)\n"
                      f"Es el único lugar de la {zona_hs} donde cabe el {num}.\n"
                      f"🟣 candidato morado = único en fila/col/caja"),
                fg=self.COLOR_ESTADO_OK
            )
            return

        # Rectángulo mortal: 4 casillas con el mismo par → 2 diagonales posibles
        if self._explicar_rectangulo_si_aplica(tablero_actual, i, j):
            return

        self.estado.config(
            text=(f"Fila {i+1}, col {j+1}: posibles → {', '.join(map(str, posibles))}\n"
                  f"Bloqueados: {excl_txt}\n"
                  f"Clic en un candidato pequeño para colocarlo."),
            fg=self.COLOR_ESTADO_INF
        )

    def _explicar_rectangulo_si_aplica(self, tablero_actual, i, j):
        """
        Si (i,j) forma parte de un rectángulo con el mismo par de candidatos,
        resalta las 4 casillas, marca en azul la diagonal de la solución
        y explica por qué la lógica pura no elige.
        """
        if not self.tablero_resuelto:
            return False
        cands = mapa_candidatos(tablero_actual)
        hallado = buscar_rectangulo_mortal(cands)
        if not hallado:
            return False
        par, rect = hallado
        if (i, j) not in rect:
            # Si hay rectángulo en el tablero pero el foco no está en él, aún así
            # informar si no hay otra pista fuerte (caller ya agotó singles).
            # Solo actuar cuando el foco pertenece al rectángulo.
            return False

        a, b = par
        for ci, cj in rect:
            self.celdas[ci][cj].set_bg("#BBDEFB")
            self._celdas_resaltadas.add((ci, cj))
            sol = self.tablero_resuelto[ci][cj]
            self.celdas[ci][cj].actualizar_candidatos(
                cands[ci][cj], set(),
                bg_extra="#BBDEFB", valor_solucion=sol, forzar_solucion=True,
            )

        detalles = ", ".join(
            f"f{ci+1}c{cj+1}→{self.tablero_resuelto[ci][cj]}"
            for ci, cj in rect
        )
        self.estado.config(
            text=(
                f"Rectángulo mortal {{{a},{b}}}: 4 casillas con el mismo par.\n"
                f"La lógica solo ve 2 rellenos válidos (las dos diagonales); "
                f"ningún candidato es forzado.\n"
                f"En ESTA partida elige el azul: {detalles}. "
                f"(Partidas nuevas ya se generan con solución única.)"
            ),
            fg=self.COLOR_ESTADO_INF,
        )
        return True

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

        txt.tag_config("titulo",  font=("Arial", 14, "bold"), foreground="#1A237E", spacing3=6)
        txt.tag_config("h2",      font=("Arial", 12, "bold"), foreground="#0D47A1", spacing1=8, spacing3=4)
        txt.tag_config("h3",      font=("Arial", 11, "bold"), foreground="#1565C0", spacing1=4)
        txt.tag_config("body",    font=("Arial", 11))
        txt.tag_config("code",    font=("Courier New", 10), foreground="#263238", background="#ECEFF1",
                       lmargin1=20, lmargin2=20, spacing1=2, spacing3=2)
        txt.tag_config("tip",     font=("Arial", 11, "italic"), foreground="#2E7D32")
        txt.tag_config("warn",    font=("Arial", 11, "bold"),   foreground="#E65100")
        txt.tag_config("hr",      foreground="#BDBDBD")

        def ln(text="", tag="body"):
            txt.insert(tk.END, text + "\n", tag)

        ln("🎯  CÓMO RESOLVER UN SUDOKU", "titulo")
        ln("─" * 62, "hr")
        ln()
        ln("📋  REGLAS BÁSICAS", "h2")
        ln("El tablero es una cuadrícula de 9×9 casillas dividida en", "body")
        ln("9 bloques de 3×3. Rellena cada casilla con un dígito 1-9:", "body")
        ln()
        ln("  ✔  Cada FILA      → los 9 dígitos, sin repetir", "body")
        ln("  ✔  Cada COLUMNA   → los 9 dígitos, sin repetir", "body")
        ln("  ✔  Cada BLOQUE    → los 9 dígitos, sin repetir", "body")
        ln()
        ln("─" * 62, "hr")
        ln()
        ln("✏️  CANDIDATOS EN CADA CASILLA", "h2")
        ln("En las casillas vacías verás en pequeño los números posibles.", "body")
        ln("Haz clic en uno para colocarlo. Supr / Backspace lo borra.", "body")
        ln()
        ln("  Gris/negro  → candidato normal", "body")
        ln("  Verde       → único candidato de esa casilla (Naked Single)", "tip")
        ln("  Morado      → único lugar de la fila/columna/caja (Hidden Single)", "tip")
        ln()
        ln("Así ves de un vistazo dónde solo cabe un número.", "body")
        ln()
        ln("─" * 62, "hr")
        ln()
        ln("🔧  NAKED SINGLE (número único)", "h2")
        ln("Si en una casilla solo cabe UN número, ese es la respuesta.", "body")
        ln("Aparece en verde y con fondo verdoso.", "tip")
        ln()
        ln("🔧  HIDDEN SINGLE (número oculto)", "h2")
        ln("Si un número solo puede ir en una casilla de su fila,", "body")
        ln("columna o caja, aparece en morado aunque haya más candidatos.", "body")
        ln()
        ln("─" * 62, "hr")
        ln()
        ln("🎨  LEYENDA DE COLORES", "h2")
        ln("  Negro       → número dado por el puzzle (fijo)", "body")
        ln("  Azul        → número introducido por ti, sin conflicto", "body")
        ln("  Naranja     → ¡CONFLICTO! número repetido", "warn")
        ln()
        ln("  Al pulsar 'Pista (Ayuda)':", "body")
        ln("  Fondo azul claro  → misma fila/col/caja", "body")
        ln("  Fondo naranja     → celda que bloquea un candidato", "body")
        ln()
        ln("💡  Usa 'Pista' para ver el razonamiento paso a paso.", "tip")

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

    # ------------------------------------------------------------------
    # TEMPORIZADOR
    # ------------------------------------------------------------------

    def _segundos_actuales(self):
        total = self._segundos_acumulados
        if self._timer_activo and self._inicio_tramo is not None:
            total += time.time() - self._inicio_tramo
        return total

    def _actualizar_lbl_tiempo(self):
        self.lbl_tiempo.config(text=formatear_tiempo(self._segundos_actuales()))

    def _tick_timer(self):
        if not self._timer_activo:
            return
        self._actualizar_lbl_tiempo()
        self._timer_after_id = self.root.after(250, self._tick_timer)

    def _iniciar_timer(self, segundos_previos=0):
        self._detener_timer(guardar_acumulado=False)
        self._segundos_acumulados = int(segundos_previos)
        self._inicio_tramo = time.time()
        self._timer_activo = True
        self._timer_en_pausa = False
        self._partida_terminada = False
        self.lbl_tiempo.config(fg="#0D47A1")
        self._actualizar_lbl_tiempo()
        self._tick_timer()

    def _detener_timer(self, guardar_acumulado=True):
        if self._timer_after_id is not None:
            try:
                self.root.after_cancel(self._timer_after_id)
            except tk.TclError:
                pass
            self._timer_after_id = None
        if guardar_acumulado and self._timer_activo and self._inicio_tramo is not None:
            self._segundos_acumulados += time.time() - self._inicio_tramo
        self._inicio_tramo = None
        self._timer_activo = False
        self._actualizar_lbl_tiempo()

    def _pausar_timer(self):
        """Para el cronómetro (p. ej. al guardar) sin perder el tiempo acumulado."""
        self._detener_timer(guardar_acumulado=True)
        self._timer_en_pausa = True
        self.lbl_tiempo.config(
            text=formatear_tiempo(self._segundos_acumulados) + " ⏸",
            fg="#EF6C00",
        )

    def _reanudar_timer_si_pausado(self):
        """Reanuda tras guardar, al volver a interactuar con el tablero."""
        if self._partida_terminada or not self._timer_en_pausa:
            return
        if self._timer_activo:
            return
        self._inicio_tramo = time.time()
        self._timer_activo = True
        self._timer_en_pausa = False
        self.lbl_tiempo.config(fg="#0D47A1")
        self._actualizar_lbl_tiempo()
        self._tick_timer()

    def _guardar_estado_actual(self):
        # Congela el tramo actual en acumulado antes de guardar
        if self._timer_activo and self._inicio_tramo is not None:
            self._segundos_acumulados += time.time() - self._inicio_tramo
            self._inicio_tramo = time.time()
        guardar_partida(
            self._dif_actual(), self.tablero_resuelto,
            self.tablero_fijo, self.obtener_tablero_actual(),
            segundos_juego=int(self._segundos_acumulados),
        )

    def _cargar_estado(self, datos):
        self.tablero_resuelto = datos["tablero_resuelto"]
        self.tablero_fijo     = datos["tablero_fijo"]
        tablero_actual        = copy.deepcopy(datos["tablero_actual"])
        self._limpiar_resaltado_pista()
        self._ultimo_aviso_conflicto = -1
        self._ambiguedad_ofrecida = None

        # Partidas antiguas podían tener 2 soluciones → añadir pistas mínimas
        self.tablero_fijo, n_extra = reparar_unicidad(
            self.tablero_fijo, self.tablero_resuelto
        )
        if n_extra:
            for i in range(9):
                for j in range(9):
                    if self.tablero_fijo[i][j] != 0:
                        # La pista nueva prevalece (corrige ambigüedad)
                        tablero_actual[i][j] = self.tablero_fijo[i][j]

        for i in range(9):
            for j in range(9):
                self.celdas[i][j].set_bloqueada(False)

        for i in range(9):
            for j in range(9):
                val = tablero_actual[i][j]
                fijo = self.tablero_fijo[i][j] != 0
                if val != 0:
                    self.celdas[i][j].set_valor(
                        val, fijo=fijo,
                        color=self.COLOR_FIJO if fijo else self.COLOR_USUARIO
                    )
                else:
                    self.celdas[i][j].set_valor(0)

        self._actualizar_colores_conflicto()
        self._refrescar_candidatos()
        previos = int(datos.get("segundos_juego", 0))
        self._iniciar_timer(previos)
        extra = (
            f" Se añadieron {n_extra} pista(s) para dejar solución única."
            if n_extra else ""
        )
        self.estado.config(
            text=(f"Partida «{datos['dificultad']}» retomada "
                  f"(tiempo previo {formatear_tiempo(previos)}).{extra}"),
            fg=self.COLOR_ESTADO_OK
        )
        if n_extra:
            messagebox.showinfo(
                "Partida corregida",
                "Esta partida guardada tenía más de una solución "
                "(generada con una versión anterior).\n\n"
                f"Se han añadido {n_extra} pista(s) fijas para que "
                "quede una única solución y no reaparezca el "
                "rectángulo con el mismo par de candidatos.",
            )
            self._guardar_estado_actual()

    def mostrar_records(self):
        records = cargar_records()
        lineas = ["Récords y últimas partidas\n" + "─" * 40]
        for dif in ("Fácil", "Medio", "Difícil"):
            datos = records.get(dif)
            lineas.append(f"\n▶ {dif}")
            if not datos or not datos.get("partidas"):
                lineas.append("  (aún no hay partidas terminadas)")
                continue
            mejor = datos.get("mejor")
            lineas.append(f"  Mejor marca: {formatear_tiempo(mejor)}")
            lineas.append("  Últimas:")
            for p in reversed(datos["partidas"][-5:]):
                lineas.append(f"    · {p['fecha']}  →  {p['tiempo']}")
        messagebox.showinfo("Récords", "\n".join(lineas))

    def deshacer_bloqueo(self):
        """
        Analiza callejones sin salida (casillas vacías sin candidatos o
        sin la solución entre ellos) y propone/aplica UNDO de casillas
        de usuario incorrectas.
        """
        if not self.tablero_resuelto or not self.tablero_fijo:
            messagebox.showinfo("Sin partida", "No hay partida en curso.")
            return
        if self._partida_terminada:
            return

        actual = self.obtener_tablero_actual()
        analisis = analizar_bloqueo(self.tablero_fijo, actual, self.tablero_resuelto)
        vacias_bloq = analisis["vacias_bloqueadas"]
        undos_min = analisis["undos_minimos"]
        undos_todos = analisis["undos_todos"]

        if not vacias_bloq and not undos_todos:
            cands = mapa_candidatos(actual)
            rect = buscar_rectangulo_mortal(cands)
            if rect and self.tablero_resuelto:
                par, celdas = rect
                a, b = par
                lineas = [
                    f"No hay números incorrectos, pero hay ambigüedad {{{a},{b}}}:",
                    "4 casillas forman un rectángulo con el mismo par de candidatos.",
                    "Eso admite dos rellenos (diagonales); la lógica sola no elige.",
                    "",
                    "En esta partida usa el candidato AZUL (solución guardada):",
                ]
                for ci, cj in celdas:
                    lineas.append(
                        f"  · fila {ci+1}, col {cj+1} → "
                        f"{self.tablero_resuelto[ci][cj]}"
                    )
                lineas.append("")
                lineas.append(
                    "(Las partidas nuevas se generan con solución única; "
                    "esta pudo cargarse de antes.)"
                )
                self._limpiar_resaltado_pista()
                for ci, cj in celdas:
                    self.celdas[ci][cj].set_bg("#BBDEFB")
                    self._celdas_resaltadas.add((ci, cj))
                    self.celdas[ci][cj].actualizar_candidatos(
                        cands[ci][cj], set(),
                        bg_extra="#BBDEFB",
                        valor_solucion=self.tablero_resuelto[ci][cj],
                        forzar_solucion=True,
                    )
                messagebox.showinfo("Ambigüedad (rectángulo)", "\n".join(lineas))
                return
            messagebox.showinfo(
                "Sin bloqueo",
                "No hay callejón sin salida ni números de usuario incorrectos.\n"
                "Puedes seguir con los candidatos (verde/morado = inequívoco)."
            )
            return

        lineas = [
            "Se llegó a un bloqueo porque se colocaron números",
            "que NO eran inequívocos (solo gris = posible, no forzado).",
            "",
            "Regla: prioriza siempre verde/morado; el gris puede equivocarte.",
            "",
        ]

        if vacias_bloq:
            lineas.append("Casillas vacías bloqueadas (0 candidatos útiles):")
            for i, j, sol, cands in vacias_bloq:
                lineas.append(
                    f"  · fila {i+1}, col {j+1}: candidatos={cands or '∅'} "
                    f"(necesita {sol})"
                )
            lineas.append("")

        if undos_min:
            lineas.append("UNDO MÍNIMO para desbloquear esas casillas:")
            for n, (i, j, actual_v, correcto, motivo) in enumerate(undos_min, 1):
                lineas.append(
                    f"  {n}. Supr en fila {i+1}, col {j+1}: "
                    f"quitar {actual_v} → luego irá {correcto}"
                )
                lineas.append(f"      ({motivo})")
            lineas.append("")

        if undos_todos:
            lineas.append("UNDO COMPLETO (todas las de usuario incorrectas):")
            for n, (i, j, actual_v, correcto, _) in enumerate(undos_todos, 1):
                lineas.append(
                    f"  {n}. Supr fila {i+1}, col {j+1}: quitar {actual_v} "
                    f"(correcto {correcto})"
                )

        # Marcar en tablero los undos mínimos (o todos si no hay mínimos)
        marcar = undos_min if undos_min else undos_todos
        self._limpiar_resaltado_pista()
        self._marcar_celdas_conflicto([(i, j) for i, j, *_ in marcar])
        for i, j, *_ in marcar:
            self._celdas_resaltadas.add((i, j))

        texto = "\n".join(lineas)
        aplicar = messagebox.askyesno(
            "Deshacer bloqueo",
            texto + "\n\n¿Aplicar ahora el UNDO mínimo "
            "(borrar solo las casillas en rojo que bloquean)?"
            if undos_min else
            texto + "\n\n¿Borrar ahora TODAS las casillas incorrectas (en rojo)?"
        )
        if not aplicar:
            self.estado.config(
                text="UNDO mostrado (rojo). Bórralas con Supr o vuelve a pulsar Deshacer bloqueo.",
                fg=self.COLOR_ESTADO_ERR,
            )
            return

        lista = undos_min if undos_min else undos_todos
        for i, j, *_ in lista:
            self.colocar_numero(i, j, 0)
        self._limpiar_resaltado_pista()
        self._limpiar_fondos_conflicto()
        self._refrescar_candidatos()
        self._actualizar_colores_conflicto()
        self.estado.config(
            text=f"Aplicados {len(lista)} UNDO. Revisa candidatos verdes/morados y continúa.",
            fg=self.COLOR_ESTADO_OK,
        )
        messagebox.showinfo(
            "UNDO aplicado",
            f"Se han borrado {len(lista)} casilla(s).\n"
            f"Ahora coloca solo candidatos verdes/morados (inequívocos)."
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
        self._pausar_timer()
        dif = self._dif_actual()
        t = formatear_tiempo(self._segundos_acumulados)
        self.estado.config(
            text=f"Partida «{dif}» guardada. Cronómetro en pausa ({t}). Clic en una casilla para continuar.",
            fg=self.COLOR_ESTADO_OK,
        )
        messagebox.showinfo(
            "Guardado",
            f"La partida de nivel «{dif}» se ha guardado.\n"
            f"Tiempo acumulado: {t}\n"
            f"El cronómetro está en pausa.\n\n"
            f"Al retomar o al hacer clic en el tablero, seguirá contando."
        )

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

    def nuevo_juego(self):
        dif = self.dificultad.get()
        self.estado.config(text=f"Generando tablero {dif}...", fg="black")
        self.root.update()

        self.tablero_resuelto = generar_tablero_resuelto()
        puzzle = crear_puzzle(self.tablero_resuelto, dif)
        self.tablero_fijo = copy.deepcopy(puzzle)
        self._limpiar_resaltado_pista()
        self._ultimo_aviso_conflicto = 0
        self._celda_focus = None
        self._ambiguedad_ofrecida = None

        eliminar_guardado(dif)

        for i in range(9):
            for j in range(9):
                self.celdas[i][j].set_bloqueada(False)
                self.celdas[i][j].restaurar_bg()

        self.actualizar_tablero_gui(puzzle)
        self._refrescar_candidatos()
        self._iniciar_timer(0)
        self.estado.config(
            text="Clic en un candidato (verde/morado = unicidad). Teclado 1-9 también sirve.",
            fg="black"
        )

    def actualizar_tablero_gui(self, tablero):
        for i in range(9):
            for j in range(9):
                val = tablero[i][j]
                if val != 0:
                    self.celdas[i][j].set_valor(val, fijo=True, color=self.COLOR_FIJO)
                else:
                    self.celdas[i][j].set_valor(0)

    def obtener_tablero_actual(self):
        return [[self.celdas[i][j].valor() for j in range(9)] for i in range(9)]

    def comprobar_tablero(self):
        tablero_actual = self.obtener_tablero_actual()

        en_conflicto = celdas_en_conflicto(tablero_actual)
        if en_conflicto:
            self._actualizar_colores_conflicto()
            ci, cj = next(iter(en_conflicto))
            self.seleccionar_celda(ci, cj)
            self._actualizar_colores_conflicto()
            messagebox.showwarning(
                "Conflictos detectados",
                f"Hay {len(en_conflicto)} celda(s) con números repetidos "
                f"(fondo rojo / número naranja).\n\n"
                f"Haz clic en una casilla en conflicto y pulsa Supr "
                f"(o doble clic / clic derecho) para borrarla."
            )
            self.root.focus_force()
            return

        vacias = [(i, j) for i in range(9) for j in range(9) if tablero_actual[i][j] == 0]
        if vacias:
            vi, vj = vacias[0]
            self.seleccionar_celda(vi, vj)
            self.estado.config(
                text=(f"Tablero incompleto: quedan {len(vacias)} casillas vacías. "
                      f"Seleccionada fila {vi+1}, col {vj+1} — escribe un dígito o haz clic en un candidato."),
                fg="darkorange"
            )
            messagebox.showwarning(
                "Tablero incompleto",
                f"Todavía quedan {len(vacias)} casillas sin rellenar.\n\n"
                f"Se ha seleccionado la primera vacía (fila {vi+1}, col {vj+1}).\n"
                f"Escribe un número 1-9 o haz clic en un candidato pequeño."
            )
            self.root.focus_force()
            return

        errores = [
            (i, j)
            for i in range(9) for j in range(9)
            if tablero_actual[i][j] != self.tablero_resuelto[i][j]
        ]
        if errores:
            for i in range(9):
                for j in range(9):
                    if self.tablero_fijo[i][j] == 0:
                        color = (
                            self.COLOR_ESTADO_ERR
                            if tablero_actual[i][j] != self.tablero_resuelto[i][j]
                            else self.COLOR_USUARIO
                        )
                        self.celdas[i][j].set_fg(color)
            # Selecciona el primer error para poder borrar enseguida con Supr
            ei, ej = errores[0]
            self.seleccionar_celda(ei, ej)
            self.estado.config(
                text=(f"Hay {len(errores)} error(es) en rojo. "
                      f"Casilla seleccionada: fila {ei+1}, col {ej+1}. "
                      f"Supr / doble clic / clic derecho para borrar."),
                fg=self.COLOR_ESTADO_ERR
            )
            messagebox.showerror(
                "Solución incorrecta",
                f"Hay {len(errores)} celda(s) incorrectas (en rojo).\n\n"
                f"Para corregir:\n"
                f"1. Haz clic en una casilla roja\n"
                f"2. Pulsa Supr o Backspace (o doble clic / clic derecho)\n"
                f"3. Elige de nuevo entre los candidatos"
            )
            self.root.focus_force()
        else:
            self._marcar_victoria()

    def _tecla_borrar(self, event=None):
        if self._celda_focus is None or not self.tablero_fijo:
            return
        if self._partida_terminada:
            return
        i, j = self._celda_focus
        celda = self.celdas[i][j]
        if celda._bloqueada or celda.es_fijo():
            return
        if celda.valor() != 0:
            self.colocar_numero(i, j, 0)

    def _tecla_global(self, event):
        if self._partida_terminada or not self.tablero_fijo:
            return
        if event.keysym in ("BackSpace", "Delete", "KP_Delete"):
            return
        ch = event.char if event.char in "123456789" else ""
        # Teclado numérico en Windows suele venir como KP_1..KP_9
        if not ch and event.keysym.startswith("KP_") and event.keysym[-1] in "123456789":
            ch = event.keysym[-1]
        if ch in "123456789":
            self._introducir_digito(int(ch))

    def _introducir_digito(self, num):
        if self._celda_focus is None:
            # Si no hay selección, ir a la primera casilla vacía
            tablero = self.obtener_tablero_actual()
            vacias = [(i, j) for i in range(9) for j in range(9) if tablero[i][j] == 0]
            if not vacias:
                return
            self.seleccionar_celda(*vacias[0])
        i, j = self._celda_focus
        celda = self.celdas[i][j]
        if celda._bloqueada:
            return
        if celda.es_fijo():
            self.estado.config(
                text="Esa casilla es fija. Haz clic en una casilla vacía (candidatos pequeños) y escribe el número.",
                fg=self.COLOR_ESTADO_ERR,
            )
            return
        # Si la seleccionada ya tiene número de usuario, el dígito lo sustituye;
        # si está vacía, coloca el candidato (avisando si no es legal).
        if celda.valor() == 0 and num not in celda._posibles:
            tablero = self.obtener_tablero_actual()
            bloquean = celdas_que_bloquean(tablero, i, j, num)
            self._limpiar_resaltado_pista()
            # Resalta la casilla actual + las que ya tienen ese número
            marcar = set(bloquean)
            marcar.add((i, j))
            self._marcar_celdas_conflicto(marcar)
            # También deja pista naranja en las bloqueantes
            for bi, bj in bloquean:
                self.celdas[bi][bj].set_bg(self.COLOR_BG_CONFLICTO)
                self._celdas_resaltadas.add((bi, bj))
                self._celdas_conflicto_bg.add((bi, bj))
            self.celdas[i][j].set_bg(self.COLOR_BG_SELECCION)
            zonas = []
            for bi, bj in bloquean:
                if bi == i:
                    zonas.append(f"fila {i+1} col {bj+1}")
                elif bj == j:
                    zonas.append(f"col {j+1} fila {bi+1}")
                else:
                    zonas.append(f"caja ({bi+1},{bj+1})")
            detalle = ", ".join(zonas) if zonas else "sin localizar"
            self.estado.config(
                text=(f"El {num} no cabe en fila {i+1}, col {j+1}. "
                      f"Ya está en: {detalle}. Celdas en rojo = conflicto."),
                fg=self.COLOR_ESTADO_ERR,
            )
            return
        self.colocar_numero(i, j, num)
        self.estado.config(
            text=f"Colocado {num} en fila {i+1}, col {j+1}.",
            fg=self.COLOR_ESTADO_INF,
        )

    def verificar_victoria(self, event=None):
        if not self.tablero_resuelto:
            return
        for i in range(9):
            for j in range(9):
                if self.celdas[i][j].valor() != self.tablero_resuelto[i][j]:
                    return
        self._marcar_victoria()

    def _marcar_victoria(self):
        if self._partida_terminada:
            return
        self._partida_terminada = True
        self._detener_timer(guardar_acumulado=True)
        segundos = int(self._segundos_acumulados)
        texto_tiempo = formatear_tiempo(segundos)
        dif = self._dif_actual()
        eliminar_guardado(dif)
        self._limpiar_resaltado_pista()

        es_record, mejor, historial = registrar_partida_terminada(dif, segundos)
        lineas_hist = "\n".join(
            f"  · {p['fecha']}  →  {p['tiempo']}" for p in reversed(historial[-5:])
        )
        record_txt = "¡Nuevo récord en este nivel!" if es_record else f"Mejor marca: {formatear_tiempo(mejor)}"

        self.lbl_tiempo.config(text=texto_tiempo, fg="#2E7D32")
        self.estado.config(
            text=f"¡Completado en {texto_tiempo}! ({dif})  {record_txt}",
            fg=self.COLOR_ESTADO_OK
        )
        messagebox.showinfo(
            "¡Victoria!",
            f"¡Enhorabuena! Has completado el Sudoku.\n\n"
            f"Nivel: {dif}\n"
            f"Tiempo: {texto_tiempo}\n"
            f"{record_txt}\n\n"
            f"Últimas partidas ({dif}):\n{lineas_hist}"
        )
        for i in range(9):
            for j in range(9):
                self.celdas[i][j].set_bloqueada(True)


# ==========================================
# PUNTO DE ENTRADA
# ==========================================

if __name__ == "__main__":
    root = tk.Tk()
    app = SudokuApp(root)
    root.mainloop()

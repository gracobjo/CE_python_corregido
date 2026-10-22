import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import ast
import subprocess
import sys
import time
import tempfile
import os
import threading
import re


# ============================================
# 1. VENTANA PRINCIPAL
# ============================================
ventana = tk.Tk()
ventana.title("🧪 Laboratorio de Pruebas de Código")
ventana.geometry("1100x750")

colores = {
    "fondo": "#1e1e1e",
    "texto": "#d4d4d4",
    "accent": "#007acc",
    "ok": "#4ec9b0",
    "error": "#f48771",
    "warning": "#dcdcaa",
    "keyword": "#569cd6",
    "string": "#ce9178",
    "comment": "#6a9955",
}


# ============================================
# 2. UTILIDAD: COLOREAR SINTAXIS PYTHON
# ============================================
PATRONES_PYTHON = {
    "keyword": r"\b(def|class|if|elif|else|for|while|return|import|from|as|"
               r"try|except|finally|with|raise|pass|break|continue|and|or|"
               r"not|in|is|lambda|yield|global|nonlocal|True|False|None)\b",
    "string": r"'[^']*'|\"[^\"]*\"",
    "comment": r"#.*$",
    "number": r"\b\d+\.?\d*\b",
    "decorator": r"@\w+",
}


def aplicar_resaltado(text_widget):
    """Aplica colores de sintaxis al contenido del Text."""
    # Quitar tags anteriores
    for tag in PATRONES_PYTHON.keys():
        text_widget.tag_remove(tag, "1.0", tk.END)
    
    contenido = text_widget.get("1.0", tk.END)
    
    for tag, patron in PATRONES_PYTHON.items():
        for coincidencia in re.finditer(patron, contenido, re.MULTILINE):
            inicio, fin = coincidencia.span()
            inicio_idx = f"1.0+{inicio}c"
            fin_idx = f"1.0+{fin}c"
            text_widget.tag_add(tag, inicio_idx, fin_idx)
    
    # Configurar colores de cada tag
    text_widget.tag_config("keyword", foreground=colores["keyword"])
    text_widget.tag_config("string", foreground=colores["string"])
    text_widget.tag_config("comment", foreground=colores["comment"], font=("Consolas", 10, "italic"))
    text_widget.tag_config("number", foreground="#b5cea8")
    text_widget.tag_config("decorator", foreground=colores["warning"])


# ============================================
# 3. PESTAÑA 1: EDITOR + EJECUTOR
# ============================================
def ejecutar_codigo():
    """Ejecuta el código en un proceso separado y captura output."""
    codigo = editor.get("1.0", tk.END)
    if not codigo.strip():
        return
    
    # Desactivar botón mientras ejecuta
    btn_ejecutar.config(state=tk.DISABLED, text="⏳ Ejecutando...")
    salida.delete(1.0, tk.END)
    salida.insert(tk.END, "▶ Ejecutando...\n\n")
    salida.update()
    
    def tarea():
        try:
            # Crear archivo temporal
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(codigo)
                ruta_tmp = tmp.name
            
            inicio = time.time()
            
            # Ejecutar en proceso separado
            resultado = subprocess.run(
                [sys.executable, ruta_tmp],
                capture_output=True,
                text=True,
                timeout=10,  # Timeout de 10 segundos
                cwd=tempfile.gettempdir(),
            )
            
            duracion = time.time() - inicio
            
            # Construir salida
            output = ""
            if resultado.stdout:
                output += resultado.stdout
            if resultado.stderr:
                output += f"\n⚠️ STDERR:\n{resultado.stderr}"
            
            if resultado.returncode == 0:
                output += f"\n✅ Finalizado en {duracion:.3f}s"
            else:
                output += f"\n❌ Error (código {resultado.returncode}) en {duracion:.3f}s"
            
            # Mostrar en el hilo principal
            ventana.after(0, lambda: mostrar_salida(output, resultado.returncode == 0))
            
        except subprocess.TimeoutExpired:
            ventana.after(0, lambda: mostrar_salida("⏱️ TIMEOUT: El código tardó más de 10s", False))
        except Exception as e:
            ventana.after(0, lambda: mostrar_salida(f"❌ Error: {e}", False))
        finally:
            try:
                os.unlink(ruta_tmp)
            except:
                pass
            ventana.after(0, lambda: btn_ejecutar.config(state=tk.NORMAL, text="▶ Ejecutar"))
    
    threading.Thread(target=tarea, daemon=True).start()


def mostrar_salida(texto, exitoso):
    salida.delete(1.0, tk.END)
    salida.insert(tk.END, texto)
    salida.tag_config("ok", foreground=colores["ok"])
    salida.tag_config("error", foreground=colores["error"])
    
    # Colorear líneas según éxito/error
    for linea_num in range(1, int(salida.index("end-1c").split(".")[0]) + 1):
        linea = salida.get(f"{linea_num}.0", f"{linea_num}.end")
        if "✅" in linea:
            salida.tag_add("ok", f"{linea_num}.0", f"{linea_num}.end")
        elif "❌" in linea or "⚠️" in linea:
            salida.tag_add("error", f"{linea_num}.0", f"{linea_num}.end")


# ============================================
# 4. PESTAÑA 2: ANÁLISIS ESTÁTICO
# ============================================
def analizar_codigo():
    """Analiza el código sin ejecutarlo: AST, PEP8 básico, complejidad."""
    codigo = editor.get("1.0", tk.END)
    if not codigo.strip():
        return
    
    resultado_texto.delete(1.0, tk.END)
    resultado_texto.insert(tk.END, "🔍 ANÁLISIS ESTÁTICO\n")
    resultado_texto.insert(tk.END, "=" * 60 + "\n\n")
    
    problemas = []
    metricas = {}
    
    # --- 1. Parseo AST ---
    try:
        arbol = ast.parse(codigo)
        resultado_texto.insert(tk.END, "✅ Sintaxis válida (AST parseado correctamente)\n\n")
        
        # Contar elementos
        metricas["funciones"] = len([n for n in ast.walk(arbol) if isinstance(n, ast.FunctionDef)])
        metricas["clases"] = len([n for n in ast.walk(arbol) if isinstance(n, ast.ClassDef)])
        metricas["imports"] = len([n for n in ast.walk(arbol) 
                                   if isinstance(n, (ast.Import, ast.ImportFrom))])
        metricas["lineas"] = len(codigo.splitlines())
        metricas["lineas_codigo"] = len([l for l in codigo.splitlines() 
                                         if l.strip() and not l.strip().startswith("#")])
        
        resultado_texto.insert(tk.END, "📊 MÉTRICAS:\n")
        for k, v in metricas.items():
            resultado_texto.insert(tk.END, f"  • {k:<20}: {v}\n")
        resultado_texto.insert(tk.END, "\n")
        
        # --- 2. Detectar funciones sin docstring ---
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.FunctionDef):
                docstring = ast.get_docstring(nodo)
                if not docstring:
                    problemas.append(
                        ("warning", f"Línea {nodo.lineno}: función '{nodo.name}' sin docstring")
                    )
                
                # --- 3. Complejidad ciclomática básica ---
                complejidad = 1  # base
                for subnodo in ast.walk(nodo):
                    if isinstance(subnodo, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                        complejidad += 1
                    elif isinstance(subnodo, ast.BoolOp):
                        complejidad += len(subnodo.values) - 1
                
                if complejidad > 10:
                    problemas.append(
                        ("error", f"Línea {nodo.lineno}: '{nodo.name}' tiene complejidad {complejidad} (>10)")
                    )
                elif complejidad > 5:
                    problemas.append(
                        ("warning", f"Línea {nodo.lineno}: '{nodo.name}' complejidad {complejidad} (moderada)")
                    )
        
        # --- 4. Detectar líneas muy largas ---
        for i, linea in enumerate(codigo.splitlines(), 1):
            if len(linea) > 100:
                problemas.append(
                    ("warning", f"Línea {i}: supera 100 caracteres ({len(linea)} chars)")
                )
        
        # --- 5. Detectar 'print' en funciones (posible debug) ---
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.FunctionDef):
                for sub in ast.walk(nodo):
                    if isinstance(sub, ast.Call):
                        if isinstance(sub.func, ast.Name) and sub.func.id == "print":
                            problemas.append(
                                ("warning", 
                                 f"Línea {sub.lineno}: 'print' dentro de función '{nodo.name}' (¿debug?)")
                            )
                            break
        
        # --- 6. Detectar except sin especificar excepción ---
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.ExceptHandler) and nodo.type is None:
                problemas.append(
                    ("error", f"Línea {nodo.lineno}: 'except:' genérico (mala práctica)")
                )
    
    except SyntaxError as e:
        resultado_texto.insert(tk.END, f"❌ ERROR DE SINTAXIS:\n")
        resultado_texto.insert(tk.END, f"   Línea {e.lineno}: {e.msg}\n")
        resultado_texto.insert(tk.END, f"   {e.text}\n\n")
    
    # --- Mostrar problemas ---
    resultado_texto.insert(tk.END, "=" * 60 + "\n")
    resultado_texto.insert(tk.END, f"📋 PROBLEMAS DETECTADOS: {len(problemas)}\n")
    resultado_texto.insert(tk.END, "=" * 60 + "\n\n")
    
    if not problemas:
        resultado_texto.insert(tk.END, "🎉 ¡Sin problemas! Código limpio.\n")
    else:
        resultado_texto.tag_config("error_tag", foreground=colores["error"])
        resultado_texto.tag_config("warning_tag", foreground=colores["warning"])
        
        for tipo, msg in problemas:
            tag = "error_tag" if tipo == "error" else "warning_tag"
            icono = "❌" if tipo == "error" else "⚠️"
            resultado_texto.insert(tk.END, f"{icono} {msg}\n", tag)


# ============================================
# 5. PESTAÑA 3: TEST RUNNER
# ============================================
def ejecutar_tests():
    """Ejecuta tests unitarios escritos en el editor de tests."""
    codigo_test = editor_tests.get("1.0", tk.END)
    codigo_fuente = editor.get("1.0", tk.END)
    
    if not codigo_test.strip():
        messagebox.showinfo("Info", "Escribe tests en el editor de la derecha")
        return
    
    btn_tests.config(state=tk.DISABLED, text="⏳ Ejecutando tests...")
    salida_tests.delete(1.0, tk.END)
    salida_tests.insert(tk.END, "▶ Ejecutando tests...\n\n")
    
    def tarea():
        try:
            # Crear archivo temporal con el código fuente + tests
            codigo_completo = codigo_fuente + "\n\n" + codigo_test
            
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False, encoding="utf-8"
            ) as tmp:
                tmp.write(codigo_completo)
                ruta_tmp = tmp.name
            
            resultado = subprocess.run(
                [sys.executable, "-m", "unittest", ruta_tmp, "-v"],
                capture_output=True,
                text=True,
                timeout=15,
                cwd=tempfile.gettempdir(),
            )
            
            output = resultado.stdout + resultado.stderr
            
            ventana.after(0, lambda: mostrar_tests(output, resultado.returncode))
        
        except subprocess.TimeoutExpired:
            ventana.after(0, lambda: mostrar_tests("⏱️ TIMEOUT en tests", 1))
        except Exception as e:
            ventana.after(0, lambda: mostrar_tests(f"❌ Error: {e}", 1))
        finally:
            try:
                os.unlink(ruta_tmp)
            except:
                pass
            ventana.after(0, lambda: btn_tests.config(state=tk.NORMAL, text="▶ Ejecutar tests"))
    
    threading.Thread(target=tarea, daemon=True).start()


def mostrar_tests(output, returncode):
    salida_tests.delete(1.0, tk.END)
    salida_tests.insert(tk.END, output)
    
    salida_tests.tag_config("ok", foreground=colores["ok"])
    salida_tests.tag_config("fail", foreground=colores["error"])
    salida_tests.tag_config("header", foreground=colores["keyword"], font=("Consolas", 10, "bold"))
    
    # Colorear líneas
    for linea_num in range(1, int(salida_tests.index("end-1c").split(".")[0]) + 1):
        linea = salida_tests.get(f"{linea_num}.0", f"{linea_num}.end")
        if "ok" in linea.lower() and "fail" not in linea.lower():
            salida_tests.tag_add("ok", f"{linea_num}.0", f"{linea_num}.end")
        elif "fail" in linea.lower() or "error" in linea.lower() or "FAIL" in linea:
            salida_tests.tag_add("fail", f"{linea_num}.0", f"{linea_num}.end")
        elif linea.startswith("test_") or "Ran " in linea:
            salida_tests.tag_add("header", f"{linea_num}.0", f"{linea_num}.end")


# ============================================
# 6. CONSTRUIR LA INTERFAZ
# ============================================
# --- Notebook (pestañas) ---
notebook = ttk.Notebook(ventana)
notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

# ======================================================
# PESTAÑA 1: EDITOR + EJECUTOR
# ======================================================
tab1 = tk.Frame(notebook, bg=colores["fondo"])
notebook.add(tab1, text=" 📝 Editor y Ejecutor ")

# Panel izquierdo: editor
panel_izq = tk.Frame(tab1, bg=colores["fondo"])
panel_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

tk.Label(
    panel_izq, text="💻 CÓDIGO PYTHON",
    bg=colores["fondo"], fg=colores["texto"],
    font=("Arial", 10, "bold")
).pack(anchor="w", pady=(0, 5))

editor = tk.Text(
    panel_izq, bg=colores["fondo"], fg=colores["texto"],
    insertbackground="white", font=("Consolas", 10),
    wrap=tk.NONE, padx=8, pady=8,
)
editor.pack(fill=tk.BOTH, expand=True)

# Scrollbars del editor
scroll_y_ed = tk.Scrollbar(editor, orient=tk.VERTICAL, command=editor.yview)
scroll_x_ed = tk.Scrollbar(editor, orient=tk.HORIZONTAL, command=editor.xview)
editor.configure(yscrollcommand=scroll_y_ed.set, xscrollcommand=scroll_x_ed.set)
scroll_y_ed.place(relx=1.0, rely=0, relheight=1.0, anchor="ne", bordermode="outside")
scroll_x_ed.place(relx=0, rely=1.0, relwidth=1.0, anchor="sw", bordermode="outside")

# Código de ejemplo
codigo_ejemplo = '''# Escribe tu código Python aquí
def saludar(nombre):
    """Saluda a una persona."""
    return f"Hola, {nombre}!"

def sumar(a, b):
    return a + b

if __name__ == "__main__":
    print(saludar("Mundo"))
    print(f"2 + 3 = {sumar(2, 3)}")
    
    # Prueba un bucle
    for i in range(3):
        print(f"Iteración {i}")
'''
editor.insert(tk.END, codigo_ejemplo)
aplicar_resaltado(editor)

# Resaltado al soltar tecla
editor.bind("<KeyRelease>", lambda e: aplicar_resaltado(editor))

# Botones
marco_botones = tk.Frame(panel_izq, bg=colores["fondo"])
marco_botones.pack(fill=tk.X, pady=5)

btn_ejecutar = tk.Button(
    marco_botones, text="▶ Ejecutar", command=ejecutar_codigo,
    bg=colores["ok"], fg="black", font=("Arial", 10, "bold"),
    padx=15, pady=5,
)
btn_ejecutar.pack(side=tk.LEFT, padx=5)

tk.Button(
    marco_botones, text="🗑️ Limpiar",
    command=lambda: editor.delete(1.0, tk.END),
    bg="#555", fg="white", font=("Arial", 10), padx=10, pady=5,
).pack(side=tk.LEFT, padx=5)

tk.Button(
    marco_botones, text="📋 Ejemplo",
    command=lambda: (editor.delete(1.0, tk.END), 
                     editor.insert(tk.END, codigo_ejemplo),
                     aplicar_resaltado(editor)),
    bg="#555", fg="white", font=("Arial", 10), padx=10, pady=5,
).pack(side=tk.LEFT, padx=5)

# Panel derecho: output
panel_der = tk.Frame(tab1, bg=colores["fondo"], width=400)
panel_der.pack(side=tk.RIGHT, fill=tk.BOTH, padx=5, pady=5)

tk.Label(
    panel_der, text="📤 SALIDA",
    bg=colores["fondo"], fg=colores["texto"],
    font=("Arial", 10, "bold")
).pack(anchor="w", pady=(0, 5))

salida = tk.Text(
    panel_der, bg="#252526", fg=colores["texto"],
    font=("Consolas", 10), wrap=tk.NONE, padx=8, pady=8,
)
salida.pack(fill=tk.BOTH, expand=True)

# ======================================================
# PESTAÑA 2: ANÁLISIS ESTÁTICO
# ======================================================
tab2 = tk.Frame(notebook, bg=colores["fondo"])
notebook.add(tab2, text=" 🔬 Análisis Estático ")

marco_analisis_top = tk.Frame(tab2, bg=colores["fondo"])
marco_analisis_top.pack(fill=tk.X, padx=10, pady=10)

tk.Button(
    marco_analisis_top, text="🔍 Analizar código del editor",
    command=analizar_codigo, bg=colores["accent"], fg="white",
    font=("Arial", 10, "bold"), padx=15, pady=7,
).pack(side=tk.LEFT)

tk.Label(
    marco_analisis_top,
    text="Detecta: sintaxis, complejidad, PEP8 básico, docstrings, prints en funciones",
    bg=colores["fondo"], fg=colores["texto"], font=("Arial", 9, "italic")
).pack(side=tk.LEFT, padx=15)

resultado_texto = tk.Text(
    tab2, bg="#252526", fg=colores["texto"],
    font=("Consolas", 10), wrap=tk.NONE, padx=10, pady=10,
)
resultado_texto.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

scroll_res = tk.Scrollbar(resultado_texto, orient=tk.VERTICAL, command=resultado_texto.yview)
resultado_texto.configure(yscrollcommand=scroll_res.set)
scroll_res.place(relx=1.0, rely=0, relheight=1.0, anchor="ne", bordermode="outside")

# ======================================================
# PESTAÑA 3: TEST RUNNER
# ======================================================
tab3 = tk.Frame(notebook, bg=colores["fondo"])
notebook.add(tab3, text=" 🧪 Test Runner ")

tk.Label(
    tab3,
    text="💡 Escribe tests usando unittest. El código del editor se incluye automáticamente.",
    bg=colores["fondo"], fg=colores["warning"],
    font=("Arial", 10, "italic"), padx=10, pady=5
).pack(anchor="w")

panel_tests = tk.Frame(tab3, bg=colores["fondo"])
panel_tests.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# Editor de tests
panel_tests_izq = tk.Frame(panel_tests, bg=colores["fondo"])
panel_tests_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

tk.Label(
    panel_tests_izq, text="📝 TESTS (unittest)",
    bg=colores["fondo"], fg=colores["texto"], font=("Arial", 10, "bold")
).pack(anchor="w", pady=(0, 5))

editor_tests = tk.Text(
    panel_tests_izq, bg=colores["fondo"], fg=colores["texto"],
    insertbackground="white", font=("Consolas", 10),
    wrap=tk.NONE, padx=8, pady=8,
)
editor_tests.pack(fill=tk.BOTH, expand=True)

tests_ejemplo = '''import unittest

class TestFunciones(unittest.TestCase):
    
    def test_saludar(self):
        self.assertEqual(saludar("Ana"), "Hola, Ana!")
    
    def test_saludar_vacio(self):
        self.assertEqual(saludar(""), "Hola, !")
    
    def test_sumar(self):
        self.assertEqual(sumar(2, 3), 5)
        self.assertEqual(sumar(-1, 1), 0)
        self.assertEqual(sumar(0, 0), 0)
    
    def test_sumar_decimales(self):
        self.assertAlmostEqual(sumar(0.1, 0.2), 0.3, places=5)

if __name__ == "__main__":
    unittest.main()
'''
editor_tests.insert(tk.END, tests_ejemplo)

# Output de tests
panel_tests_der = tk.Frame(panel_tests, bg=colores["fondo"])
panel_tests_der.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

tk.Label(
    panel_tests_der, text="📤 RESULTADO DE TESTS",
    bg=colores["fondo"], fg=colores["texto"], font=("Arial", 10, "bold")
).pack(anchor="w", pady=(0, 5))

salida_tests = tk.Text(
    panel_tests_der, bg="#252526", fg=colores["texto"],
    font=("Consolas", 10), wrap=tk.NONE, padx=8, pady=8,
)
salida_tests.pack(fill=tk.BOTH, expand=True)

btn_tests = tk.Button(
    tab3, text="▶ Ejecutar tests", command=ejecutar_tests,
    bg=colores["ok"], fg="black", font=("Arial", 10, "bold"),
    padx=15, pady=7,
)
btn_tests.pack(pady=5)

ventana.mainloop()
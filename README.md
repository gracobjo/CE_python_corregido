# Curso de Python

Material de apoyo para aprender Python mediante notebooks de Jupyter. El contenido avanza desde los conceptos básicos del lenguaje hasta funciones, estructuras de datos, iteradores, generadores y fechas.

## Contenido

Los notebooks están organizados de forma progresiva:

| Notebook | Tema |
| --- | --- |
| `00_IndicePython.ipynb` | Índice del curso |
| `01_Generalidades_REV.ipynb` | Conceptos generales de Python |
| `02_EstructuraIF_REV.ipynb` | Condicionales `if`, `elif` y `else` |
| `03_EstructuraMATCH_REV.ipynb` | Estructura `match` |
| `04_BucleWHILE_REV.ipynb` | Bucles `while` |
| `05_BucleFOR_REV.ipynb` | Bucles `for` |
| `06_Funciones_REV.ipynb` | Definición y uso de funciones |
| `07_FuncionesLambda_REV.ipynb` | Funciones anónimas con `lambda` |
| `08_FuncionesDecoradores_REV.ipynb` | Decoradores |
| `09_FilterSortedMap_REV.ipynb` | `filter`, `sorted` y `map` |
| `10_Listas_REV.ipynb` | Listas y operaciones habituales |
| `11_Diccionarios_REV.ipynb` | Diccionarios |
| `12_Iteradores_REV.ipynb` | Iterables e iteradores |
| `13_Tuplas_REV.ipynb` | Tuplas |
| `14_Conjuntos_REV.ipynb` | Conjuntos |
| `15_Generadores_REV.ipynb` | Generadores y `yield` |
| `16_FechasHoras_REV.ipynb` | Fechas y horas |
| `17_FuncionesDefLambda_REV.ipynb` | Refactorización de funciones `def` a `lambda` |

La carpeta `Ejercicios/` contiene ejercicios prácticos complementarios.

## Requisitos

- Python 3.13 o superior
- Jupyter Notebook o JupyterLab
- Visual Studio Code con la extensión Jupyter, opcionalmente

El proyecto no requiere dependencias externas para ejecutar los ejemplos actuales.

## Configuración

### Opción 1: entorno virtual de Python

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install jupyter
```

En macOS o Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install jupyter
```

### Opción 2: uv

Si utilizas [uv](https://docs.astral.sh/uv/):

```bash
uv sync
uv run python --version
```

Para abrir Jupyter con el entorno del proyecto:

```bash
uv run jupyter notebook
```

## Cómo usar los notebooks

1. Clona el repositorio:

   ```bash
   git clone https://github.com/gracobjo/CE_python_corregido.git
   cd CE_python_corregido
   ```

2. Configura el entorno siguiendo una de las opciones anteriores.
3. Abre `00_IndicePython.ipynb` para consultar el recorrido recomendado.
4. Ejecuta las celdas en orden y modifica los ejemplos para practicar.
5. Continúa con los ejercicios de la carpeta `Ejercicios/`.

En Visual Studio Code también puedes abrir directamente cualquier archivo `.ipynb`, seleccionar el intérprete de Python y ejecutar sus celdas desde el editor.

## Ejemplo destacado: `map` y `lambda`

El notebook 17 resume cómo transformar una función sencilla definida con `def` en una expresión `lambda`:

```python
def doble(x):
    return x * 2

lista = [1, 2, 3, 4, 5]
print(list(map(doble, lista)))
print(list(map(lambda x: x * 2, lista)))
```

Ambas versiones producen:

```text
[2, 4, 6, 8, 10]
```

La misma idea se practica con `filter` para seleccionar elementos y con `sorted` para ordenar usando una función como criterio.

## Estructura del repositorio

```text
.
├── 00_IndicePython.ipynb
├── 01_Generalidades_REV.ipynb
├── ...
├── 17_FuncionesDefLambda_REV.ipynb
├── Ejercicios/
├── Imagenes/
├── main.py
├── pyproject.toml
└── uv.lock
```

## Licencia

Este repositorio contiene material educativo personal para el aprendizaje y la práctica de Python.

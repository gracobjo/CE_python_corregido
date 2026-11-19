"""Muestra la estructura del JSON de un país y permite recorrer sus ramas."""

import argparse
import json

from api_client import buscar_pais, crear_sesion, nombre_comun


CAMPOS = "names,codes,capitals,flag,region,subregion,continents,borders"


def imprimir_arbol(valor, nivel=0, ruta="$"):
    """Imprime rutas JSON y tipos, mostrando un ejemplo de cada lista."""
    sangria = "  " * nivel

    if isinstance(valor, dict):
        print(f"{sangria}{ruta}: object ({len(valor)} claves)")
        for clave, elemento in valor.items():
            imprimir_arbol(elemento, nivel + 1, f"{ruta}.{clave}")
    elif isinstance(valor, list):
        print(f"{sangria}{ruta}: array ({len(valor)} elementos)")
        if valor:
            imprimir_arbol(valor[0], nivel + 1, f"{ruta}[0]")
    else:
        tipo = type(valor).__name__
        print(f"{sangria}{ruta}: {tipo} = {valor!r}")


def main():
    parser = argparse.ArgumentParser(
        description="Explora el árbol JSON que devuelve REST Countries."
    )
    parser.add_argument(
        "--pais",
        default="España",
        help="Nombre, traducción o código ISO del país (por defecto: España).",
    )
    argumentos = parser.parse_args()

    sesion = crear_sesion()
    pais = buscar_pais(sesion, argumentos.pais, CAMPOS)
    print(f"Estructura de {nombre_comun(pais)}:")
    imprimir_arbol(pais)
    print("\nObjeto JSON completo:")
    print(json.dumps(pais, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    from api_client import ejecutar

    ejecutar(main)

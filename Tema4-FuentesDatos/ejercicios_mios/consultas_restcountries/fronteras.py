"""Lista países con fronteras terrestres y las ordena por nombre o cantidad."""

import argparse

from api_client import crear_sesion, ejecutar, nombre_comun, normalizar, obtener_paises


CAMPOS = "names.common,codes.alpha_3,borders"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--orden",
        choices=("nombre", "fronteras"),
        default="nombre",
        help="Criterio de orden (por defecto: nombre).",
    )
    parser.add_argument(
        "--desc",
        action="store_true",
        help="Orden descendente (especialmente útil con --orden fronteras).",
    )
    argumentos = parser.parse_args()

    paises = obtener_paises(crear_sesion(), CAMPOS)
    con_fronteras = [
        (pais, pais.get("borders") or [])
        for pais in paises
        if pais.get("borders")
    ]

    if argumentos.orden == "fronteras":
        con_fronteras.sort(key=lambda fila: normalizar(nombre_comun(fila[0])))
        con_fronteras.sort(
            key=lambda fila: len(fila[1]),
            reverse=argumentos.desc,
        )
    else:
        con_fronteras.sort(
            key=lambda fila: normalizar(nombre_comun(fila[0])),
            reverse=argumentos.desc,
        )
    print(f"{'País':<32} {'Código':<8} Número de fronteras")
    print("-" * 60)
    for pais, fronteras in con_fronteras:
        codigo = pais.get("codes", {}).get("alpha_3", "")
        print(f"{nombre_comun(pais):<32} {codigo:<8} {len(fronteras)}")


if __name__ == "__main__":
    ejecutar(main)

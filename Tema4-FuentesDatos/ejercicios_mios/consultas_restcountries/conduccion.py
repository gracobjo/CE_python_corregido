"""Agrupa alfabéticamente países según el lado de circulación."""

from api_client import crear_sesion, ejecutar, nombre_comun, normalizar, obtener_paises


CAMPOS = "names.common,cars.driving_side"


def main():
    paises = obtener_paises(crear_sesion(), CAMPOS)
    for lado in ("left", "right"):
        grupo = [
            pais
            for pais in paises
            if pais.get("cars", {}).get("driving_side") == lado
        ]
        grupo.sort(key=lambda pais: normalizar(nombre_comun(pais)))
        etiqueta = "izquierda" if lado == "left" else "derecha"
        print(f"\nConducción por la {etiqueta} ({len(grupo)} países):")
        for pais in grupo:
            print(f"  - {nombre_comun(pais)}")


if __name__ == "__main__":
    ejecutar(main)

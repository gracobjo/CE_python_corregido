"""Busca países indicados por el usuario y descarga sus banderas PNG."""

from pathlib import Path

import requests

from api_client import (
    TIMEOUT,
    buscar_pais,
    crear_sesion,
    ejecutar,
    nombre_comun,
)


CAMPOS = "names,codes.alpha_3,flag.url_png"
DESTINO = Path(__file__).resolve().parents[2] / "recursos" / "banderas"


def main():
    entrada = input(
        "Países cuyas banderas quieres descargar, separados por comas: "
    )
    consultas = [pais.strip() for pais in entrada.split(",") if pais.strip()]
    if not consultas:
        raise ValueError("Introduce al menos un país.")

    sesion = crear_sesion()
    DESTINO.mkdir(parents=True, exist_ok=True)

    for consulta in consultas:
        pais = buscar_pais(sesion, consulta, CAMPOS)
        url = pais.get("flag", {}).get("url_png")
        if not url:
            print(f"No hay una URL PNG disponible para {nombre_comun(pais)}.")
            continue

        # La URL de la bandera es otro dominio: no se le envía la clave API.
        respuesta = requests.get(url, timeout=TIMEOUT)
        respuesta.raise_for_status()

        codigo = pais.get("codes", {}).get("alpha_3", "pais").lower()
        ruta = DESTINO / f"bandera_{codigo}.png"
        ruta.write_bytes(respuesta.content)
        print(f"{nombre_comun(pais)}: {ruta}")


if __name__ == "__main__":
    ejecutar(main)

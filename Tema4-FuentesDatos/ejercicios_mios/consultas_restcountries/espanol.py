"""Lista países cuya información de idiomas incluye el español."""

from api_client import crear_sesion, ejecutar, nombre_comun, normalizar, obtener_paises


CAMPOS = "names.common,languages"


def tiene_espanol(pais):
    """Comprueba si la lista languages contiene español por código o nombre."""
    idiomas = pais.get("languages") or []
    if isinstance(idiomas, dict):
        idiomas = list(idiomas.values())
    if not isinstance(idiomas, list):
        return False

    for idioma in idiomas:
        if isinstance(idioma, str):
            valores = [idioma]
        elif isinstance(idioma, dict):
            valores = [
                idioma.get(clave)
                for clave in (
                    "bcp47",
                    "iso_639_1",
                    "iso639_1",
                    "code",
                    "name",
                    "native_name",
                )
            ]
        else:
            continue

        for valor in valores:
            if not isinstance(valor, str):
                continue
            texto = normalizar(valor).strip()
            if texto == "es" or texto.startswith("es-") or texto in {
                "spanish",
                "espanol",
            }:
                return True
    return False


def main():
    paises = obtener_paises(crear_sesion(), CAMPOS)
    hispanohablantes = sorted(
        (pais for pais in paises if tiene_espanol(pais)),
        key=lambda pais: normalizar(nombre_comun(pais)),
    )
    print(f"Países con español en el campo languages ({len(hispanohablantes)}):")
    for pais in hispanohablantes:
        print(f"  - {nombre_comun(pais)}")
    print(
        "\nNota: la API informa de los idiomas del país, pero no ofrece en este "
        "campo una marca que distinga explícitamente idioma oficial de idioma "
        "de uso."
    )


if __name__ == "__main__":
    ejecutar(main)

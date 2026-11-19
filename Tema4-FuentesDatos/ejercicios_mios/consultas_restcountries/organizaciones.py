"""Agrupa países por organizaciones y cuenta las afiliaciones de cada país."""

from api_client import crear_sesion, ejecutar, nombre_comun, normalizar, obtener_paises


CAMPOS = "names.common,memberships"


def organizaciones_de(pais):
    """Devuelve las organizaciones cuya pertenencia está marcada como true."""
    membresias = pais.get("memberships") or {}
    if not isinstance(membresias, dict):
        return []
    return sorted(
        (
            organizacion
            for organizacion, pertenece in membresias.items()
            if pertenece is True
        ),
        key=normalizar,
    )


def main():
    paises = obtener_paises(crear_sesion(), CAMPOS)
    paises.sort(key=lambda pais: normalizar(nombre_comun(pais)))
    grupos = {}

    for pais in paises:
        for organizacion in organizaciones_de(pais):
            grupos.setdefault(organizacion, []).append(nombre_comun(pais))

    print("Países agrupados por organización internacional:")
    for organizacion in sorted(grupos, key=normalizar):
        miembros = grupos[organizacion]
        print(
            f"\n{organizacion.replace('_', ' ').upper()} "
            f"({len(miembros)} países):"
        )
        for miembro in miembros:
            print(f"  - {miembro}")

    print("\nNúmero de organizaciones por país:")
    for pais in paises:
        organizaciones = organizaciones_de(pais)
        if organizaciones:
            nombres = ", ".join(organizaciones)
            print(f"{nombre_comun(pais)}: {len(organizaciones)} — {nombres}")


if __name__ == "__main__":
    ejecutar(main)

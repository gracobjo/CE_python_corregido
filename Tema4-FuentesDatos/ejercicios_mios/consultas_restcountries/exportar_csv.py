"""Exporta datos de países preparados para análisis KPI en un CSV con ';'."""

import csv
from pathlib import Path

from api_client import (
    crear_sesion,
    ejecutar,
    nombre_comun,
    obtener_paises,
    valor_anidado,
)


CAMPOS = (
    "names.common,codes.alpha_3,continents,region,subregion,population,"
    "flag.url_png,capitals,memberships,currencies,languages,borders,"
    "cars.driving_side,area.kilometers,landlocked,timezones"
)
COLUMNAS: tuple[str, ...] = (
    "codigo_alpha3",
    "pais",
    "continentes",
    "region",
    "subregion",
    "poblacion",
    "bandera_png",
    "capitales",
    "organizaciones",
    "numero_organizaciones",
    "monedas",
    "idiomas",
    "numero_idiomas",
    "fronteras",
    "numero_fronteras",
    "lado_conduccion",
    "superficie_km2",
    "densidad_poblacion_hab_km2",
    "sin_litoral",
    "numero_husos_horarios",
)
DESTINO = Path(__file__).resolve().parents[2] / "recursos" / "paises_kpi.csv"


def como_lista(valor):
    if valor is None:
        return []
    if isinstance(valor, list):
        return valor
    if isinstance(valor, dict):
        return list(valor.values())
    return [valor]


def unir_valores(valores):
    """Une valores múltiples por coma, ignorando los campos vacíos."""
    textos = []
    for valor in valores:
        if isinstance(valor, str) and valor.strip():
            textos.append(valor.strip())
        elif isinstance(valor, (int, float)):
            textos.append(str(valor))
    return ", ".join(textos)


def capitales_de(pais):
    capitales = como_lista(pais.get("capitals"))
    nombres = []
    for capital in capitales:
        if isinstance(capital, str):
            nombres.append(capital)
        elif isinstance(capital, dict) and capital.get("name"):
            nombres.append(capital["name"])
    return unir_valores(nombres)


def monedas_de(pais):
    monedas = pais.get("currencies") or {}
    if isinstance(monedas, dict):
        resultado = []
        for codigo, datos in monedas.items():
            if isinstance(datos, dict):
                nombre = datos.get("name")
                simbolo = datos.get("symbol")
                detalle = " ".join(
                    parte for parte in (nombre, f"({simbolo})" if simbolo else None)
                    if parte
                )
                resultado.append(f"{codigo}: {detalle}".rstrip(": "))
            else:
                resultado.append(codigo)
        return unir_valores(resultado)

    resultado = []
    for moneda in como_lista(monedas):
        if isinstance(moneda, dict):
            codigo = moneda.get("code", "")
            nombre = moneda.get("name", "")
            simbolo = moneda.get("symbol")
            detalle = " ".join(
                parte for parte in (nombre, f"({simbolo})" if simbolo else None)
                if parte
            )
            resultado.append(f"{codigo}: {detalle}".strip(": "))
    return unir_valores(resultado)


def idiomas_de(pais):
    idiomas = pais.get("languages") or []
    if isinstance(idiomas, dict):
        resultado = []
        for codigo, datos in idiomas.items():
            if isinstance(datos, dict):
                resultado.append(datos.get("name") or codigo)
            elif isinstance(datos, str):
                resultado.append(datos)
        return resultado

    resultado = []
    for idioma in como_lista(idiomas):
        if isinstance(idioma, str):
            resultado.append(idioma)
        elif isinstance(idioma, dict):
            nombre = idioma.get("name") or idioma.get("native_name")
            if nombre:
                resultado.append(nombre)
    return resultado


def organizaciones_de(pais):
    membresias = pais.get("memberships") or {}
    if not isinstance(membresias, dict):
        return []
    return sorted(
        (
            organizacion
            for organizacion, pertenece in membresias.items()
            if pertenece is True
        )
    )


def fila_csv(pais):
    fronteras = pais.get("borders") or []
    organizaciones = organizaciones_de(pais)
    idiomas = idiomas_de(pais)
    superficie = valor_anidado(pais, "area.kilometers")
    poblacion = pais.get("population")
    densidad = (
        round(poblacion / superficie, 2)
        if isinstance(poblacion, (int, float))
        and isinstance(superficie, (int, float))
        and superficie > 0
        else ""
    )
    continentes = unir_valores(como_lista(pais.get("continents")))

    return {
        "codigo_alpha3": valor_anidado(pais, "codes.alpha_3", ""),
        "pais": nombre_comun(pais),
        "continentes": continentes,
        "region": pais.get("region", ""),
        "subregion": pais.get("subregion", ""),
        "poblacion": poblacion if poblacion is not None else "",
        "bandera_png": valor_anidado(pais, "flag.url_png", ""),
        "capitales": capitales_de(pais),
        "organizaciones": unir_valores(organizaciones),
        "numero_organizaciones": len(organizaciones),
        "monedas": monedas_de(pais),
        "idiomas": unir_valores(idiomas),
        "numero_idiomas": len(idiomas),
        "fronteras": unir_valores(fronteras),
        "numero_fronteras": len(fronteras),
        "lado_conduccion": valor_anidado(pais, "cars.driving_side", ""),
        "superficie_km2": superficie if superficie is not None else "",
        "densidad_poblacion_hab_km2": densidad,
        "sin_litoral": pais.get("landlocked", ""),
        "numero_husos_horarios": len(como_lista(pais.get("timezones"))),
    }


def main():
    paises = obtener_paises(crear_sesion(), CAMPOS)
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(
            archivo,
            fieldnames=COLUMNAS,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
        )
        escritor.writeheader()
        escritor.writerows(fila_csv(pais) for pais in paises)
    print(f"CSV creado con {len(paises)} países: {DESTINO}")


if __name__ == "__main__":
    ejecutar(main)

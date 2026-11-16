import os
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.restcountries.com"
URL_PAIS = f"{BASE_URL}/countries/v5"
URL_CONVERSION = f"{BASE_URL}/currencies/v1/convert"
TIMEOUT = 20
RESPONSE_FIELDS = (
    "names.common,names.official,names.alternates,names.native,"
    "names.translations,currencies,codes.alpha_3"
)


def normalizar(texto):
    """Compara nombres ignorando mayúsculas y tildes."""
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(caracter for caracter in texto if not unicodedata.combining(caracter)).casefold()


def recorrer_textos(valor):
    """Devuelve los textos encontrados dentro de nombres anidados."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for elemento in valor.values():
            yield from recorrer_textos(elemento)
    elif isinstance(valor, list):
        for elemento in valor:
            yield from recorrer_textos(elemento)


def pedir_datos(session, url, params=None):
    respuesta = session.get(url, params=params, timeout=TIMEOUT)
    respuesta.raise_for_status()
    contenido = respuesta.json()

    if contenido.get("errors"):
        mensajes = "; ".join(
            error.get("message", "Error de la API")
            for error in contenido["errors"]
        )
        raise RuntimeError(mensajes)

    datos = contenido.get("data")
    if not isinstance(datos, dict):
        raise RuntimeError("La respuesta de la API no tiene el formato esperado.")
    if "_demo" in datos:
        raise RuntimeError(
            "La API devolvió datos de demostración, no resultados reales. "
            "Configura una clave API propia en RESTCOUNTRIES_API_KEY."
        )

    return datos


def buscar_pais(session, nombre_pais):
    """Busca un país por su nombre común, nativo o traducido."""
    parametros = {
        "q": nombre_pais,
        "limit": 100,
        "response_fields": RESPONSE_FIELDS,
    }

    for endpoint in ("name", "names.translations"):
        datos = pedir_datos(
            session,
            f"{URL_PAIS}/{endpoint}",
            params=parametros,
        )
        paises = datos.get("objects", [])
        nombre_buscado = normalizar(nombre_pais)
        coincidencias = []

        for pais in paises:
            nombres = pais.get("names", {})
            nombres_disponibles = {
                normalizar(texto) for texto in recorrer_textos(nombres)
            }
            if nombre_buscado in nombres_disponibles:
                coincidencias.append(pais)

        paises_unicos = {}
        for pais in coincidencias:
            codigo = pais.get("codes", {}).get("alpha_3")
            if codigo:
                paises_unicos[codigo] = pais

        if len(paises_unicos) == 1:
            return next(iter(paises_unicos.values()))
        if len(paises_unicos) > 1:
            raise ValueError(
                f"El nombre «{nombre_pais}» coincide con varios países. "
                "Prueba con el nombre oficial o en inglés."
            )

    raise ValueError(
        f"No se ha encontrado el país «{nombre_pais}». "
        "Prueba con su nombre común, nativo o traducido."
    )


def seleccionar_moneda(pais):
    """Obtiene el código de moneda del país; pregunta si hay varios."""
    monedas = pais.get("currencies", [])

    if isinstance(monedas, dict):
        monedas = [
            {"code": codigo, **datos}
            for codigo, datos in monedas.items()
            if isinstance(datos, dict)
        ]

    monedas = [
        moneda for moneda in monedas
        if isinstance(moneda, dict) and moneda.get("code")
    ]
    if not monedas:
        raise ValueError(
            f"No se encontró una moneda para {pais['names']['common']}."
        )
    if len(monedas) == 1:
        return monedas[0]

    print(f"{pais['names']['common']} tiene varias monedas:")
    for moneda in monedas:
        print(f"  {moneda['code']}: {moneda.get('name', 'Sin nombre')}")

    codigos = {moneda["code"].upper(): moneda for moneda in monedas}
    while True:
        codigo = input("Escribe el código de la moneda que quieres usar: ")
        moneda = codigos.get(codigo.strip().upper())
        if moneda:
            return moneda
        print("Código no válido; elige uno de la lista.")


def pedir_cantidad():
    while True:
        texto = input("Cantidad a convertir (por ejemplo, 100): ").strip()
        try:
            cantidad = Decimal(texto.replace(",", "."))
        except InvalidOperation:
            print("Escribe una cantidad numérica válida.")
            continue

        if cantidad.is_finite() and cantidad > 0:
            return cantidad
        print("La cantidad debe ser un número mayor que cero.")


def convertir(session, moneda_origen, moneda_destino, cantidad):
    parametros = {
        "from": moneda_origen["code"],
        "to": moneda_destino["code"],
        "amount": str(cantidad),
    }
    datos = pedir_datos(session, URL_CONVERSION, params=parametros)
    resultados = datos.get("objects", [])
    if not resultados:
        raise RuntimeError("La API no devolvió el resultado de la conversión.")

    resultado = resultados[0]
    cantidad_convertida = Decimal(str(resultado["result"]))
    tasa = Decimal(str(resultado["rate"]))
    return cantidad_convertida, tasa


def main():
    load_dotenv(dotenv_path=Path(__file__).with_name(".env"))
    api_key = os.getenv("RESTCOUNTRIES_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta la clave API. Añádela como RESTCOUNTRIES_API_KEY "
            "en el archivo .env."
        )

    pais_origen = input("País de origen: ").strip()
    pais_destino = input("País de destino: ").strip()
    cantidad = pedir_cantidad()

    session = requests.Session()
    session.headers.update({
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })

    datos_origen = buscar_pais(session, pais_origen)
    datos_destino = buscar_pais(session, pais_destino)
    moneda_origen = seleccionar_moneda(datos_origen)
    moneda_destino = seleccionar_moneda(datos_destino)

    cantidad_convertida, tasa = convertir(
        session,
        moneda_origen,
        moneda_destino,
        cantidad,
    )

    print(
        f"{cantidad} {moneda_origen['code']} "
        f"({moneda_origen.get('name', '')}) = "
        f"{cantidad_convertida:.2f} {moneda_destino['code']} "
        f"({moneda_destino.get('name', '')})"
    )
    print(f"Tasa aplicada: 1 {moneda_origen['code']} = {tasa} {moneda_destino['code']}")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, RuntimeError, ValueError) as error:
        print(f"No se pudo completar la conversión: {error}")

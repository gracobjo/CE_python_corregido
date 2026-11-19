"""Utilidades compartidas para consultar REST Countries API v5."""

import os
import unicodedata
from pathlib import Path

import requests
from dotenv import load_dotenv


BASE_URL = "https://api.restcountries.com/countries/v5"
TIMEOUT = 20
PAGE_SIZE = 100


def crear_sesion():
    """Crea una sesión autenticada leyendo RESTCOUNTRIES_API_KEY del entorno."""
    ruta_env = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(dotenv_path=ruta_env)

    api_key = os.getenv("RESTCOUNTRIES_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Falta RESTCOUNTRIES_API_KEY. Añade tu clave al archivo "
            f".env de {ruta_env.parent}."
        )

    sesion = requests.Session()
    sesion.headers.update({
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    })
    return sesion


def _pedir_json(sesion, ruta, parametros):
    respuesta = sesion.get(
        f"{BASE_URL}{ruta}",
        params=parametros,
        timeout=TIMEOUT,
    )
    respuesta.raise_for_status()
    contenido = respuesta.json()

    if not isinstance(contenido, dict):
        raise RuntimeError("La API no devolvió un objeto JSON.")

    errores = contenido.get("errors")
    if errores:
        mensajes = "; ".join(
            error.get("message", "Error de la API")
            for error in errores
            if isinstance(error, dict)
        )
        raise RuntimeError(mensajes or "La API devolvió un error.")

    datos = contenido.get("data")
    if not isinstance(datos, dict):
        raise RuntimeError("La respuesta no contiene el objeto esperado data.")
    if "_demo" in datos:
        raise RuntimeError(
            "La API devolvió datos de demostración. Configura una clave "
            "RESTCOUNTRIES_API_KEY propia para consultar los datos reales."
        )
    return datos


def obtener_paises(sesion, campos, filtros=None):
    """Recorre todas las páginas y devuelve los países como una lista."""
    parametros_base = dict(filtros or {})
    parametros_base["response_fields"] = campos
    parametros_base["limit"] = PAGE_SIZE
    paises = []
    offset = 0

    while True:
        parametros = {**parametros_base, "offset": offset}
        datos = _pedir_json(sesion, "", parametros)
        objetos = datos.get("objects")
        if not isinstance(objetos, list):
            raise RuntimeError("La respuesta data.objects no es una lista.")
        if any(not isinstance(pais, dict) for pais in objetos):
            raise RuntimeError("La lista data.objects contiene datos inválidos.")

        paises.extend(objetos)
        metadatos = datos.get("meta", {})
        if not isinstance(metadatos, dict):
            raise RuntimeError("La respuesta data.meta tiene un formato inválido.")

        if "more" in metadatos:
            hay_mas = metadatos["more"]
        else:
            hay_mas = len(objetos) == PAGE_SIZE

        if not hay_mas or not objetos:
            return paises
        offset += len(objetos)


def textos_en(valor):
    """Recorre un objeto y devuelve todos los textos que contiene."""
    if isinstance(valor, str):
        yield valor
    elif isinstance(valor, dict):
        for elemento in valor.values():
            yield from textos_en(elemento)
    elif isinstance(valor, list):
        for elemento in valor:
            yield from textos_en(elemento)


def normalizar(texto):
    """Normaliza para comparar nombres sin distinguir tildes ni mayúsculas."""
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    ).casefold()


def buscar_pais(sesion, consulta, campos):
    """Busca un país por nombre común, traducción o código ISO."""
    consulta = consulta.strip()
    if not consulta:
        raise ValueError("La búsqueda no puede estar vacía.")

    paises = obtener_paises(sesion, campos, filtros={"q": consulta})
    consulta_normalizada = normalizar(consulta)
    coincidencias = {}

    for pais in paises:
        nombres = pais.get("names", {})
        codigos = pais.get("codes", {})
        nombres_normalizados = {
            normalizar(texto) for texto in textos_en(nombres)
        }
        codigos_normalizados = {
            normalizar(texto)
            for texto in codigos.values()
            if isinstance(texto, str)
        }

        if (
            consulta_normalizada in nombres_normalizados
            or consulta_normalizada in codigos_normalizados
        ):
            codigo = codigos.get("alpha_3")
            identificador = codigo or pais.get("uuid") or consulta_normalizada
            coincidencias[identificador] = pais

    if len(coincidencias) == 1:
        return next(iter(coincidencias.values()))
    if len(coincidencias) > 1:
        nombres = sorted(
            (nombre_comun(pais) for pais in coincidencias.values()),
            key=normalizar,
        )
        raise ValueError(
            f"«{consulta}» coincide con varios países: {', '.join(nombres)}."
        )
    raise ValueError(f"No se encontró un país que coincida exactamente con «{consulta}».")


def nombre_comun(pais):
    """Devuelve el nombre común o una etiqueta alternativa."""
    return pais.get("names", {}).get("common") or pais.get("codes", {}).get(
        "alpha_3", "País sin nombre"
    )


def valor_anidado(objeto, ruta, predeterminado=None):
    """Obtiene un valor usando una ruta separada por puntos."""
    actual = objeto
    for clave in ruta.split("."):
        if not isinstance(actual, dict) or clave not in actual:
            return predeterminado
        actual = actual[clave]
    return actual


def ejecutar(main):
    """Muestra errores esperables sin ocultar fallos inesperados."""
    try:
        main()
    except (requests.RequestException, RuntimeError, ValueError) as error:
        raise SystemExit(f"No se pudo completar la consulta: {error}") from error

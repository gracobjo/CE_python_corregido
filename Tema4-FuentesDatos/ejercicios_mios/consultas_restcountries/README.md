# Consultas con REST Countries API v5

Estos ejercicios usan la misma API v5 que `banderasUE.py` y
`conversorMoneda.py` en la carpeta `ejercicios_mios`.

## Preparación

Instala las dependencias de `Tema4-FuentesDatos/ejercicios_mios/requirements.txt`
y configura tu clave en el archivo `.env` de `ejercicios_mios`:

```text
RESTCOUNTRIES_API_KEY=tu_clave
```

No publiques ese archivo ni incluyas la clave en el código. Los scripts se
ejecutan desde esta carpeta; por ejemplo:

```powershell
python explorar_json.py --pais España
python banderas.py
python fronteras.py --orden nombre
python fronteras.py --orden fronteras --desc
python conduccion.py
python organizaciones.py
python espanol.py
python exportar_csv.py
```

`banderas.py` solicita uno o varios nombres separados por comas y descarga
los PNG en `Tema4-FuentesDatos/recursos/banderas`. El CSV se guarda en
`Tema4-FuentesDatos/recursos/paises_kpi.csv`.

## Cómo leer el JSON

La versión usada es la v5. El JSON de una lista de países tiene este esquema:

```text
respuesta                         dict
└── data                          dict
    ├── objects                   list[dict]  <- registros de países
    │   └── [0]                   dict        <- un país
    │       ├── names             dict        <- common, official, ...
    │       ├── codes             dict        <- alpha_2, alpha_3, ...
    │       ├── flag              dict        <- url_png, url_svg, emoji, ...
    │       ├── capitals          list[dict]
    │       ├── borders           list[str]   <- códigos alpha-3
    │       ├── cars              dict        <- driving_side
    │       ├── languages         list[dict]
    │       ├── currencies        dict/list
    │       └── memberships       dict[str, bool]
    └── meta                      dict        <- total, count, limit, offset, more
```

JSON objects se convierten en diccionarios de Python; arrays, en listas;
`true`/`false`, en `True`/`False`; y `null`, en `None`. Por eso, para obtener
el PNG de un país se navega por claves anidadas:

```python
url = pais["flag"]["url_png"]
```

Para recorrer resultados se itera `respuesta["data"]["objects"]`. Un campo
opcional se debe leer con `.get()` para evitar un `KeyError`:

```python
fronteras = pais.get("borders", [])
numero_fronteras = len(fronteras)
lado = pais.get("cars", {}).get("driving_side")
```

`explorar_json.py` imprime rutas como `$.flag.url_png` y `$.borders[0]`
junto con el tipo de dato y después muestra un registro JSON completo.
Esto permite localizar el camino de un dato antes de utilizarlo en una
consulta.

## Consultas incluidas

| Fichero | Resultado |
|---|---|
| `explorar_json.py` | Árbol y objeto JSON de un país |
| `banderas.py` | Busca los países solicitados y descarga sus PNG |
| `fronteras.py` | Países con fronteras y cantidad; orden por nombre o cantidad |
| `conduccion.py` | Grupos de circulación por izquierda y por derecha |
| `organizaciones.py` | Países por organización y número de organizaciones por país |
| `espanol.py` | Países con español en el campo `languages` |
| `exportar_csv.py` | CSV separado por `;`, con listas internas unidas por comas |

El cliente compartido `api_client.py` añade autenticación, errores explícitos,
normalización de nombres y paginación (`limit=100`, leyendo `data.meta.more`).
Los campos se seleccionan con `response_fields` para no pedir ramas que cada
consulta no necesita.

### Nota sobre idiomas oficiales

La API entrega una lista `languages`, pero no incluye una marca específica
que identifique cuáles son oficiales y cuáles son de uso. Por ello
`espanol.py` devuelve los países cuyo campo de idiomas contiene español y
expone esta limitación en su salida; ese resultado no debe interpretarse como
una clasificación legal de oficialidad.

## CSV para KPI

El CSV incluye código alpha-3, país, continente, región, población, URL PNG,
capitales, organizaciones y su cantidad, monedas, idiomas y su cantidad,
fronteras y su cantidad, lado de conducción, superficie, densidad de población
calculada (habitantes/km²), condición sin litoral y número de husos horarios.
Los campos múltiples se unen con comas; el delimitador de columnas es punto y
coma. La biblioteca `csv` aplica comillas cuando un valor necesita escaparse.

## Referencia

- [REST Countries — documentación de Countries API](https://restcountries.com/docs/countries)
- [REST Countries](https://restcountries.com/)

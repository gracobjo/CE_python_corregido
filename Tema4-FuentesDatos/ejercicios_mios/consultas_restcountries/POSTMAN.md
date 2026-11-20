# Probar REST Countries con Postman

Esta guía configura una petición equivalente a la consulta de
`conduccion.py`: obtiene el nombre común de cada país y su lado de circulación,
sin descargar las demás ramas de datos.

## 1. Crear un entorno

En Postman, crea o selecciona un Environment y define estas variables:

| Variable | Valor inicial | Uso |
|---|---|---|
| `baseUrl` | `https://api.restcountries.com/countries/v5` | URL base de Countries API v5 |
| `RESTCOUNTRIES_API_KEY` | Tu clave personal | Token Bearer; márcala como secreta |
| `offset` | `0` | Desplazamiento para la paginación |

El archivo `.env` del proyecto Python no se carga automáticamente en Postman.
Introduce la clave en el Environment de Postman como valor secreto. No la
escribas en un script, no la compartas ni la incluyas en una exportación.

## 2. Configurar la petición

1. Crea una petición **GET** con esta URL:

   ```text
   {{baseUrl}}
   ```

2. En **Authorization**, selecciona **Bearer Token** y usa:

   ```text
   {{RESTCOUNTRIES_API_KEY}}
   ```

3. En **Params**, añade:

   | Key | Value |
   |---|---|
   | `response_fields` | `names.common,cars.driving_side` |
   | `limit` | `100` |
   | `offset` | `{{offset}}` |

Postman codifica los parámetros al enviar la petición. La URL equivalente para
la primera página es:

```text
https://api.restcountries.com/countries/v5?response_fields=names.common%2Ccars.driving_side&limit=100&offset=0
```

El encabezado de autenticación sigue siendo necesario. Si solo interesa el
valor del lado de circulación y no el nombre del país, se puede cambiar
`response_fields` a `cars.driving_side`; para identificar cada resultado se
recomienda conservar también `names.common`.

`response_fields` limita las propiedades de cada país, no elimina el envoltorio
de la respuesta. Los registros están en `data.objects` y la información de
paginación en `data.meta`.

### Mostrar los países sin `meta` en Postman

La API devuelve `data.meta` como parte de su respuesta y `response_fields` no
puede quitarlo. Si solo quieres ver los países en Postman, añade este código
en **Scripts → Post-response**:

```javascript
const body = pm.response.json();
pm.visualizer.set(
  "<pre>{{json}}</pre>",
  { json: JSON.stringify(body.data.objects, null, 2) }
);
```

Después de enviar la petición, abre la pestaña **Visualize** para ver solo
`data.objects`, sin `data.meta`. La pestaña **Body** seguirá mostrando la
respuesta HTTP original. Si ya tienes otro script Post-response, añade este
bloque al final del mismo.

## Consultas disponibles en esta carpeta

Cada script de Python selecciona solo los campos que necesita. Para repetir
una consulta en Postman, conserva la configuración de autenticación anterior y
usa estos valores en **Params**:

| Script | `response_fields` | Parámetros adicionales | Qué hace |
|---|---|---|---|
| `explorar_json.py` | `names,codes,capitals,flag,region,subregion,continents,borders` | `q` = nombre, traducción o código del país | Busca un país y permite inspeccionar el objeto JSON y sus ramas. |
| `banderas.py` | `names,codes.alpha_3,flag.url_png` | `q` = país; una búsqueda por petición | Busca el PNG y lo descarga desde la URL devuelta. |
| `fronteras.py` | `names.common,codes.alpha_3,borders` | Ninguno | Conserva países con fronteras y permite ordenarlos por nombre o por cantidad. |
| `conduccion.py` | `names.common,cars.driving_side` | Ninguno | Agrupa los países con conducción por la izquierda (`left`) o derecha (`right`). |
| `organizaciones.py` | `names.common,memberships` | Ninguno | Agrupa países por organizaciones cuya pertenencia es `true` y cuenta las afiliaciones. |
| `espanol.py` | `names.common,languages` | Ninguno | Busca español en los datos de idiomas. No determina si es idioma oficial. |
| `exportar_csv.py` | `names.common,codes.alpha_3,continents,region,subregion,population,flag.url_png,capitals,memberships,currencies,languages,borders,cars.driving_side,area.kilometers,landlocked,timezones` | Ninguno | Obtiene los datos usados para construir el CSV KPI. |

Para las consultas sin `q`, configura `limit=100` y `offset=0` como en la
petición principal. Para `explorar_json.py` y `banderas.py`, añade también
`q` con el país a buscar (por ejemplo, `España` o `ESP`). `q` puede devolver
coincidencias; revisa `data.objects` y elige el país correcto.

### URLs completas de ejemplo

Estas URL se pueden pegar directamente en el campo de la petición **GET**.
Para `explorar_json.py` y `banderas.py`, cambia `España` por el país que quieras
consultar; `%C3%B1` representa la `ñ` codificada en la URL. La clave API no se
incluye en la URL: configúrala en **Authorization → Bearer Token**.

**`explorar_json.py` — inspeccionar España:**

```text
https://api.restcountries.com/countries/v5?response_fields=names,codes,capitals,flag,region,subregion,continents,borders&q=Espa%C3%B1a&limit=100&offset=0
```

**`banderas.py` — obtener la URL PNG de España:**

```text
https://api.restcountries.com/countries/v5?response_fields=names,codes.alpha_3,flag.url_png&q=Espa%C3%B1a&limit=100&offset=0
```

La descarga de la imagen es una segunda petición **GET** a la URL
`flag.url_png` devuelta por la consulta anterior.

**`fronteras.py` — países y códigos con sus fronteras:**

```text
https://api.restcountries.com/countries/v5?response_fields=names.common,codes.alpha_3,borders&limit=100&offset=0
```

**`conduccion.py` — países y lado de circulación:**

```text
https://api.restcountries.com/countries/v5?response_fields=names.common,cars.driving_side&limit=100&offset=0
```

**`organizaciones.py` — membresías de cada país:**

```text
https://api.restcountries.com/countries/v5?response_fields=names.common,memberships&limit=100&offset=0
```

**`espanol.py` — países y sus idiomas:**

```text
https://api.restcountries.com/countries/v5?response_fields=names.common,languages&limit=100&offset=0
```

**`exportar_csv.py` — campos utilizados para el CSV KPI:**

```text
https://api.restcountries.com/countries/v5?response_fields=names.common,codes.alpha_3,continents,region,subregion,population,flag.url_png,capitals,memberships,currencies,languages,borders,cars.driving_side,area.kilometers,landlocked,timezones&limit=100&offset=0
```

Para pedir la siguiente página, cambia `offset=0` por `offset=100` (o por la
cantidad de registros de la página anterior). El token Bearer se mantiene en
Authorization para todas las consultas a la API.

### Inspeccionar un país: `explorar_json.py`

Con los campos de la tabla y `q=España`, **Post-response** puede mostrar el
objeto devuelto en la consola:

```javascript
const body = pm.response.json();
console.log(JSON.stringify(body.data.objects, null, 2));
```

Si quieres explorar más ramas, añade sus rutas a `response_fields`. Para ver
todos los campos disponibles, omite ese parámetro, teniendo en cuenta que la
respuesta será mucho mayor.

### Descargar una bandera: `banderas.py`

Primero solicita los datos del país con los campos de la tabla. Copia
`flag.url_png` de `data.objects` y úsala como URL de una segunda petición **GET**
para descargar la imagen. Esa segunda petición va al dominio de las banderas:
no le envíes el encabezado Bearer de la API. En Postman puedes guardar la
respuesta de imagen desde **Save Response**.

### Filtrar y ordenar países con fronteras: `fronteras.py`

La petición trae `borders`; el siguiente script conserva los países con al
menos una frontera y los muestra ordenados alfabéticamente:

```javascript
const paises = pm.response.json().data.objects
  .filter(function (pais) {
    return Array.isArray(pais.borders) && pais.borders.length > 0;
  })
  .sort(function (a, b) {
    return a.names.common.localeCompare(b.names.common);
  });

console.table(paises.map(function (pais) {
  return {
    pais: pais.names.common,
    codigo: pais.codes.alpha_3,
    numero_fronteras: pais.borders.length
  };
}));
```

Para ordenarlos por cantidad de fronteras, sustituye el comparador de
`sort` por:

```javascript
paises.sort(function (a, b) {
  return b.borders.length - a.borders.length;
});
```

Para orden descendente por nombre, invierte el orden de los argumentos de
`localeCompare`.

### Agrupar por conducción: `conduccion.py`

La petición ya está configurada en la sección anterior. Este ejemplo agrupa y
ordena los nombres en Postman:

```javascript
const paises = pm.response.json().data.objects;
const grupos = { left: [], right: [] };

paises.forEach(function (pais) {
  const lado = pais.cars && pais.cars.driving_side;
  if (grupos[lado]) {
    grupos[lado].push(pais.names.common);
  }
});

grupos.left.sort();
grupos.right.sort();
console.log("Conducción por la izquierda:", grupos.left);
console.log("Conducción por la derecha:", grupos.right);
```

### Agrupar por organizaciones: `organizaciones.py`

`memberships` es un objeto cuyas claves son organizaciones. Solo se cuentan
las que tienen valor `true`:

```javascript
const paises = pm.response.json().data.objects;
const grupos = {};

paises.forEach(function (pais) {
  const memberships = pais.memberships || {};
  Object.keys(memberships).forEach(function (organizacion) {
    if (memberships[organizacion] === true) {
      if (!grupos[organizacion]) {
        grupos[organizacion] = [];
      }
      grupos[organizacion].push(pais.names.common);
    }
  });
});

console.log("Países por organización:", grupos);
console.log("Número de organizaciones por país:",
  paises.map(function (pais) {
    const memberships = pais.memberships || {};
    const cantidad = Object.keys(memberships).filter(function (organizacion) {
      return memberships[organizacion] === true;
    }).length;
    return { pais: pais.names.common, numero_organizaciones: cantidad };
  })
);
```

### Buscar países con español: `espanol.py`

`languages` puede ser una lista o un objeto. Este ejemplo revisa los nombres y
códigos de idioma que utiliza el script Python:

```javascript
function normalizar(texto) {
  return texto.normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function tieneEspanol(pais) {
  const idiomas = Array.isArray(pais.languages)
    ? pais.languages
    : Object.values(pais.languages || {});
  const claves = [
    "bcp47", "iso_639_1", "iso639_1", "code", "name", "native_name"
  ];

  return idiomas.some(function (idioma) {
    const valores = typeof idioma === "string"
      ? [idioma]
      : claves.map(function (clave) {
          return idioma && typeof idioma === "object" ? idioma[clave] : null;
        });

    return valores.some(function (valor) {
      if (typeof valor !== "string") {
        return false;
      }
      const texto = normalizar(valor);
      return texto === "es" || texto.startsWith("es-") ||
        texto === "spanish" || texto === "espanol";
    });
  });
}

const hispanohablantes = pm.response.json().data.objects
  .filter(tieneEspanol)
  .map(function (pais) {
    return pais.names.common;
  })
  .sort();

console.log("Países con español en languages:", hispanohablantes);
```

Como en el script Python, esto solo indica que el campo `languages` incluye
español; no clasifica su oficialidad.

### Datos KPI: `exportar_csv.py`

Usa todos los campos de la última fila de la tabla y recorre las páginas. En
Postman puedes inspeccionar o guardar la respuesta JSON. El CSV del script
Python, además, transforma los datos: une listas, cuenta idiomas, fronteras y
organizaciones, calcula densidad de población y establece el orden y
delimitador de columnas. Esas transformaciones no las aplica automáticamente
la consulta HTTP; para obtener exactamente el CSV del ejercicio, ejecuta
`exportar_csv.py`.

## 3. Validar y resumir la respuesta

En **Scripts → Post-response**, se puede comprobar el estado y los campos, y
contar los países de la página por lado de circulación:

```javascript
const body = pm.response.json();
const paises = body.data.objects;

pm.test("La API responde con estado 200", function () {
  pm.response.to.have.status(200);
});

pm.test("La respuesta contiene una lista de países", function () {
  pm.expect(paises).to.be.an("array");
});

pm.test("Cada país incluye nombre y lado de circulación", function () {
  paises.forEach(function (pais) {
    pm.expect(pais.names).to.have.property("common");
    pm.expect(pais.cars).to.have.property("driving_side");
  });
});

const conteo = { left: 0, right: 0, "sin dato": 0 };

paises.forEach(function (pais) {
  const lado = pais.cars && pais.cars.driving_side;
  if (lado === "left" || lado === "right") {
    conteo[lado]++;
  } else {
    conteo["sin dato"]++;
  }
});

console.log("Países de esta página por lado:", conteo);
```

Abre **View → Show Postman Console** para ver el conteo. Este script resume la
página recibida; no cambia ni filtra la petición al servidor.

## 4. Recorrer todas las páginas (opcional)

La API devuelve páginas de resultados. La respuesta indica si hay más datos en
`data.meta.more`. Para recorrerlas automáticamente:

1. Ejecuta la petición desde **Collection Runner**; **Send** solo ejecuta una
   petición.
2. Antes de empezar, comprueba que `offset` tenga el valor `0`.
3. Añade al script **Post-response**, después de las validaciones anteriores:

   ```javascript
   const meta = body.data.meta || {};

   if (meta.more) {
     const offsetActual = Number(pm.environment.get("offset") || "0");
     pm.environment.set(
       "offset",
       String(offsetActual + paises.length)
     );
     pm.execution.setNextRequest(pm.info.requestName);
   } else {
     pm.environment.set("offset", "0");
     pm.execution.setNextRequest(null);
   }
   ```

El Runner repetirá la misma petición mientras `meta.more` indique que quedan
resultados. En cada repetición, el script avanza `offset` según la cantidad de
registros recibidos. Al terminar, lo restablece a `0`.

## Referencias

- [REST Countries — documentación de Countries API](https://restcountries.com/docs/countries)
- [README de estos ejercicios](./README.md)

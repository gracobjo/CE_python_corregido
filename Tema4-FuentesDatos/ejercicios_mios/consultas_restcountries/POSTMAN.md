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

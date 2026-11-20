# Migracion animal con Movebank

Aplicacion local de un usuario para explorar estudios accesibles, descargar posiciones GPS y analizar sus trayectorias. La unica fuente de datos de seguimiento es la API real de Movebank. La descarga y el uso de los datos estan sujetos a los [terminos de Movebank](https://www.movebank.org/cms/movebank-content/general-movebank-terms-of-use), su [politica de datos](https://www.movebank.org/cms/movebank-content/data-policy) y la licencia de cada estudio; revise tambien sus [recomendaciones de cita](https://www.movebank.org/cms/movebank-content/citation-guidelines).

## Arquitectura

```text
movebank_migracion/
  src/movebank/
    domain/
      models.py              modelos Pydantic
      analytics.py           mediciones de movilidad
      spatial.py             envolvente convexa y limites GeoJSON
    infrastructure/
      movebank/              cliente HTTP y servicios de entidades
      persistence/store.py   almacenamiento SQLite con SQLAlchemy
    application/
      ports.py               contratos de sincronizacion
      sync.py                casos de uso de sincronizacion
      cli.py                 script de carga
    presentation/
      streamlit/app.py       interfaz y mapas
  tests/                     pruebas unitarias con respuestas controladas
  Dockerfile
  docker-compose.yml
  pyproject.toml
```

El dominio no depende de la interfaz, el cliente ni la base de datos. Los casos de uso coordinan servicios y persistencia mediante contratos; la configuracion de infraestructura conecta las implementaciones concretas. Se elige **SQLite** frente a DuckDB: es suficiente para sincronizar registros por individuo, permite transacciones y claves primarias, no requiere servidor y SQLAlchemy lo soporta directamente. DuckDB seria una evolucion adecuada para consultas analiticas masivas sobre Parquet, pero aqui no compensa mantener dos almacenes. La API REST propia, colas, procesamiento distribuido y permisos multiusuario quedan fuera de esta primera version: no exponer Streamlit a redes no confiables.

Las claves internas de Movebank pueden cambiar y los identificadores locales solo son unicos dentro de un estudio. La caché usa IDs internos para consultar y guardar snapshots, conserva identificadores locales y debe actualizarse si se recrean entidades. Cada descarga sustituye atomicamente los eventos del individuo; incluso una descarga vacia queda marcada como completa. La caché no detecta cambios remotos: use actualizacion explicita. Los archivos SQLite contienen potencialmente datos privados sin cifrar; proteja su acceso y no los comparta.

## Instalacion y uso local

Requiere Python 3.12 o posterior.

Edite el archivo `.env` situado en esta carpeta y escriba sus credenciales:

```dotenv
MOVEBANK_USERNAME='su_usuario'
MOVEBANK_PASSWORD='su_contrasena'
```

Use comillas simples para valores con caracteres especiales; una comilla simple dentro del valor se escribe como `\'`. El archivo contiene la contrasena **sin cifrar**: proteja el acceso local y no lo comparta. Esta excluido de Git y de la imagen Docker. El archivo `.env.example` es una plantilla sin credenciales.

```powershell
cd movebank_migracion
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\movebank-load.exe studies
.\.venv\Scripts\movebank-load.exe individuals --study 2911040
.\.venv\Scripts\movebank-load.exe events --study 2911040 --individual ID_INDIVIDUO
.\.venv\Scripts\streamlit.exe run src\movebank\presentation\streamlit\app.py
```

La CLI y el dashboard leen `.env` del directorio desde el que se ejecutan; inicie ambos desde esta carpeta. Las variables de entorno existentes tienen prioridad sobre `.env`. Despues de cambiar las credenciales, reinicie el dashboard y cierre las sesiones anteriores del navegador. Si ambas estan vacias, se intenta el acceso anonimo documentado; algunas instalaciones o respuestas pueden exigir autenticacion. Utilice su propia cuenta y permisos. Nunca incluya contrasenas en el codigo ni en el repositorio. La ruta SQLite predeterminada depende de un hash del nombre de usuario; `--database` permite seleccionar otra ruta para la CLI. El dashboard usa el directorio desde el que se inicia y su ruta predeterminada correspondiente. Para refrescar eventos mediante CLI use `--refresh`. Desde el dashboard, «Descargar o actualizar GPS» siempre refresca.

## Notebook de consulta

Abra [consulta_movebank.ipynb](consulta_movebank.ipynb) en VS Code y seleccione el kernel de `.venv`. Si no tiene soporte de notebooks en ese entorno, instale `.\.venv\Scripts\python.exe -m pip install -e ".[notebook]"`. Ejecute las celdas en orden: el notebook consulta la API real y muestra los estudios con mas de tres individuos. Sus resultados se mantienen en el notebook, no se cargan automaticamente en la cache del dashboard. Antes de compartirlo, borre sus salidas si contienen datos cuyo acceso o redistribucion este restringido.

Cuando Movebank devuelve una licencia, se muestra el contenido completo. Solo tras la confirmacion explicita se calcula y envia el MD5 del contenido exacto, conservando las cookies de sesion. Si los terminos cambian se solicita una nueva aceptacion. El MD5 es un requisito del protocolo, no una garantia criptografica. No se almacenan aceptaciones para uso futuro.

La API limita a **una solicitud concurrente por IP** y 20 globalmente. Este cliente serializa las llamadas dentro de su proceso y espera un segundo entre ellas, con reintentos para 429 y errores transitorios. No coordina varios procesos o maquinas que compartan IP: ejecute una sola instancia y evite otros clientes simultaneos. El limite de frecuencia exacto no es una garantia de Movebank.

## Docker

Con el archivo `.env` configurado, ejecute `docker compose up --build` desde esta carpeta. Docker Compose lee las credenciales del archivo y las pasa como variables al contenedor. Visite `http://localhost:8501`. Los datos se guardan en `data/`; para los limites GeoJSON, coloque el archivo alli y use su ruta en el contenedor, por ejemplo `/data/limites.geojson`. El puerto solo se publica en localhost; el dashboard no implementa autenticacion propia. No utilice este despliegue para multiples usuarios.

## Datos y criterios analiticos

- Se descargan GPS (`sensor_type_id=653`) por estudio e individuo, con `event_id`, identificadores, taxon y `visible`. Se omiten registros sin coordenadas; valores invalidos provocan error. Los eventos marcados `visible=false` se excluyen del analisis, no del almacenamiento. Los de visibilidad desconocida se conservan.
- Distancia: suma de geodesicas WGS84 entre posiciones consecutivas del mismo individuo. Velocidad media: distancia total dividida por tiempo entre posiciones admitidas; maxima: maxima velocidad de segmento. Distancia media: media por segmento. Dos posiciones con igual fecha no forman segmento. Intervalos superiores al maximo configurable se excluyen; distancia diaria se atribuye al dia UTC de la posicion final. Se trata de estimaciones, no de distancia real continua.
- Detenido/en movimiento: suma de intervalos cuya velocidad de segmento es inferior/superior o igual al umbral configurable. No equivale a comportamiento observado. La duracion es el intervalo UTC entre primera y ultima posicion valida del conjunto, no la suma de tiempos de seguimiento.
- Area: envolvente convexa de todas las posiciones seleccionadas, proyectada a Lambert azimutal equivalente local; no es una estimacion de area de campeo por KDE. La densidad es posiciones por km² de dicha envolvente. No se calcula para trayectorias que cruzan el antimeridiano. Menos de tres posiciones no producen area.
- Actividad significa numero de posiciones, condicionada por la frecuencia de muestreo. Las estaciones son meteorologicas del hemisferio norte. Las comparaciones no corrigen diferencias de esfuerzo.
- Paises y regiones requieren un GeoJSON FeatureCollection en WGS84, aportado por el usuario, con los dos campos configurados en todas sus entidades. Se cuentan unicamente poligonos que cubren posiciones observadas; no se infieren cruces entre ellas. Los puntos en el mar pueden no pertenecer a ningun poligono. Seleccione datos de limites y licencias apropiados; no se descarga ningun dataset externo. La capa de mapa base de Folium puede solicitar teselas a su proveedor, que recibe la IP del cliente.

Los estudios se filtran por taxon, sensor y ano comprendido entre las fechas de seguimiento conocidas. La lista se obtiene con `i_have_download_access=true`: si hay autenticacion puede incluir estudios privados accesibles, no solamente publicos. Sin autenticacion el acceso se limita a lo publico segun la documentacion. Las fechas y taxones incompletos pueden excluir estudios relevantes.

## Pruebas y calidad

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m black --check src tests
.\.venv\Scripts\python.exe -m ruff check src tests
.\.venv\Scripts\python.exe -m mypy src
```

Las pruebas controladas no sustituyen una integracion real autenticada. Para verificarla, use una cuenta propia y un estudio cuyo uso este autorizado; contraste el CSV, los permisos, los terminos y las cifras con Movebank. No se incluyen credenciales ni datos de terceros.

## Roadmap

1. **Robustez y produccion:** prueba de integracion autenticada, aislamiento multiusuario y control de acceso, sincronizacion incremental incluyendo eliminaciones, streaming y limites de volumen, observabilidad, control de concurrencia distribuido por IP y migraciones de esquema. Solo despues desplegar en un servidor compartido.
2. **GIS:** capas versionadas y licenciadas, indice espacial, tratamiento del antimeridiano, modelos KDE y evaluacion de incertidumbre de GPS y huecos.
3. **Clustering espacial:** modulo DBSCAN con distancia haversine, coordenadas en radianes y `eps` en metros convertido al radio terrestre; agrupar por individuo y validar duracion y muestreo antes de etiquetar zonas de descanso.
4. **Eventos migratorios:** detector configurable por especie basado en distancia, direccion y persistencia; distinguir paradas prolongadas de huecos de muestreo y validar con datos etiquetados. No presentar umbrales arbitrarios como observaciones biologicas.
5. **Prediccion:** evaluar XGBoost frente a un baseline de ultima posicion usando particiones temporales y por individuo; medir error geodesico por horizonte y evitar fuga temporal. Prophet modela series temporales, no ubicaciones geograficas directamente, por lo que requiere modelar coordenadas por separado y evaluar el cruce del antimeridiano. Ninguno se ofrece hasta disponer de validacion.
6. **API propia:** definir contratos, autenticacion, autorizacion por estudio, paginacion y limites; reutilizar los casos de uso sin publicar datos sujetos a licencias.

Fuente tecnica: [documentacion oficial de la API de Movebank](https://github.com/movebank/movebank-api-doc/blob/master/movebank-api.md), incluidos los apartados de licencias, atributos, entidades, sensores y limites.

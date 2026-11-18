import os
import requests
from pathlib import Path
from dotenv import load_dotenv

# 1. Cargar variables de entorno desde el archivo .env
load_dotenv()
API_KEY = os.getenv("RESTCOUNTRIES_API_KEY")

if not API_KEY:
    raise ValueError("⚠️ No se encontró la variable RESTCOUNTRIES_API_KEY en el archivo .env")

# 2. Configurar la carpeta de destino: un nivel superior al directorio de este script
# __file__ es la ruta de este archivo .py. .parent es su carpeta. .parent otra vez sube un nivel.
script_dir = Path(__file__).parent.resolve()
target_dir = script_dir.parent / "./recursos"

# Crear la carpeta .recursos si no existe (parents=True crea también los directorios intermedios si faltan)
target_dir.mkdir(parents=True, exist_ok=True)
print(f"📁 Las banderas se guardarán en: {target_dir}\n")

# 3. Pedir al usuario los países
user_input = input("🌍 Introduce los países que deseas (separados por comas, ej: España, Francia, Alemania): ")
countries_to_search = [c.strip() for c in user_input.split(",") if c.strip()]

if not countries_to_search:
    print("⚠️ No se introdujeron países. Saliendo del programa.")
    exit()

# 4. Cabeceras con la API Key
headers = {"Authorization": f"Bearer {API_KEY}"}

# 5. Procesar cada país solicitado
for country_query in countries_to_search:
    print(f"🔍 Buscando: '{country_query}'...")

    # Endpoint de búsqueda de la API v5
    url = f"https://api.restcountries.com/countries/v5?q={country_query}"
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        data = response.json()

        # La API v5 devuelve los resultados en data["data"]["objects"]
        countries_list = data.get("data", {}).get("objects", [])

        if countries_list:
            # Tomamos la primera coincidencia (la más relevante según la API)
            country = countries_list[0]
            name = country.get("names", {}).get("common", "Desconocido")
            flag_info = country.get("flag", {})
            png_url = flag_info.get("url_png")

            if png_url:
                print(f"   ✅ Encontrado: {name}")
                print(f"   ⬇️ Descargando bandera...")

                # Descargar la imagen
                img_response = requests.get(png_url)
                if img_response.status_code == 200:
                    # Sanitizar el nombre para crear un nombre de archivo seguro
                    safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
                    safe_name = safe_name.replace(" ", "_").lower()
                    filename = f"bandera_{safe_name}.png"
                    filepath = target_dir / filename

                    # Guardar el archivo
                    with open(filepath, "wb") as file:
                        file.write(img_response.content)
                    print(f"   💾 Guardado en: {filepath}\n")
                else:
                    print(f"   ❌ Error al descargar la imagen de {name}.\n")
            else:
                print(f"   ⚠️ No se encontró URL de bandera para {name}.\n")
        else:
            print(f"   ❌ No se encontraron resultados para '{country_query}'. Verifica la ortografía.\n")
    else:
        print(f"   ❌ Error en la API para '{country_query}'. Código: {response.status_code}")
        print(f"   Detalle: {response.text}\n")

print("🎉 ¡Proceso completado!")
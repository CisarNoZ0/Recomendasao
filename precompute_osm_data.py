import pandas as pd
import requests
import time
from tqdm import tqdm
from collections import Counter

# URL del API de Overpass
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

# Plantilla de la consulta Overpass QL para obtener hoteles en un país
# Usamos un timeout generoso porque estas consultas pueden ser lentas
OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:600];
area["name:en"="{country_name}"]->.searchArea;
(
  node["tourism"="hotel"](area.searchArea);
  way["tourism"="hotel"](area.searchArea);
  relation["tourism"="hotel"](area.searchArea);
);
out tags;
"""

def get_hotel_count_for_country(country_name):
    """
    Consulta la API de Overpass para obtener el número de hoteles por ciudad para un país específico.
    """
    print(f"Procesando: {country_name}... ", end="", flush=True)
    query = OVERPASS_QUERY_TEMPLATE.format(country_name=country_name)
    try:
        response = requests.get(OVERPASS_URL, params={'data': query})
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error de red o HTTP para {country_name}: {e}")
        return []
    except ValueError:
        print(f"No se pudo decodificar la respuesta JSON para {country_name}. Contenido: {response.text[:100]}...")
        return []

    city_counter = Counter()
    for element in data.get('elements', []):
        tags = element.get('tags', {})
        city = tags.get('addr:city')
        if city:
            city_counter[city] += 1

    if not city_counter:
        print("No se encontraron ciudades con hoteles.")
        return []

    print(f"Se encontraron {len(city_counter)} ciudades.")
    
    # Convertir el contador a una lista de diccionarios
    cities_data = [{"country": country_name, "city": city, "hotel_count": count} for city, count in city_counter.items()]
    return cities_data

def main():
    """
    Función principal para leer la lista de países, procesarlos y guardar los resultados.
    """
    print("Iniciando el proceso de pre-cómputo de datos de hoteles de OSM.")
    
    # Cargar el dataframe principal para obtener la lista de países
    try:
        df_main = pd.read_csv('world_tourism_economy_data.csv')
        # Nos aseguramos de que los países sean únicos
        countries = df_main['country'].unique()
        print(f"Se procesarán {len(countries)} países.")
    except FileNotFoundError:
        print("Error: No se encontró el archivo 'world_tourism_economy_data.csv'. Asegúrate de que esté en el mismo directorio.")
        return

    all_cities_data = []
    
    # Usamos tqdm para mostrar una barra de progreso
    for country in tqdm(countries, desc="Procesando países"):
        hotel_data = get_hotel_count_for_country(country)
        if hotel_data:
            all_cities_data.extend(hotel_data)
        
        # Pausa de cortesía para no sobrecargar la API de Overpass
        time.sleep(2)

    if not all_cities_data:
        print("No se pudo recopilar ningún dato de hoteles. El proceso ha finalizado sin resultados.")
        return

    # Crear un DataFrame final y guardarlo en CSV
    print("\nProceso de recopilación finalizado. Guardando datos en el archivo CSV...")
    df_final = pd.DataFrame(all_cities_data)
    
    # Ordenar por país y luego por cantidad de hoteles para que el archivo sea más legible
    df_final = df_final.sort_values(by=['country', 'hotel_count'], ascending=[True, False])
    
    output_filename = 'osm_cities_with_hotels.csv'
    df_final.to_csv(output_filename, index=False)
    
    print(f"¡Éxito! Los datos se han guardado en '{output_filename}'.")
    print(f"El archivo contiene {len(df_final)} filas (ciudades).")

if __name__ == '__main__':
    main()
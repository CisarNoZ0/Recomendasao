import pandas as pd
import requests
import time
import os
from tqdm import tqdm

# URL del API de Overpass (OpenStreetMap)
OVERPASS_URL = "http://overpass-api.de/api/interpreter"

def get_country_list(df_main: pd.DataFrame) -> pd.DataFrame:
    """
    Extrae una lista única de países y sus códigos del DataFrame principal.
    
    Args:
        df_main: DataFrame cargado de 'world_tourism_economy_data.csv'.
    
    Returns:
        DataFrame con columnas 'country' y 'country_code'.
    """
    # Lista de agregaciones a excluir
    aggregations_exact = [
        'Africa Eastern and Southern', 'Africa Western and Central', 'Arab World',
        'Caribbean small states', 'Central Europe and the Baltics', 'Early-demographic dividend',
        'East Asia & Pacific', 'East Asia & Pacific (excluding high income)',
        'East Asia & Pacific (IDA & IBRD countries)', 'Euro area', 'Europe & Central Asia',
        'Europe & Central Asia (excluding high income)', 'Europe & Central Asia (IDA & IBRD countries)',
        'European Union', 'Fragile and conflict affected situations', 'Heavily indebted poor countries (HIPC)',
        'High income', 'IBRD only', 'IDA & IBRD total', 'IDA blend', 'IDA only', 'IDA total',
        'Late-demographic dividend', 'Latin America & Caribbean',
        'Latin America & Caribbean (excluding high income)', 'Latin America & the Caribbean (IDA & IBRD countries)',
        'Least developed countries: UN classification', 'Low & middle income', 'Low income',
        'Lower middle income', 'Middle East & North Africa',
        'Middle East & North Africa (excluding high income)', 'Middle East & North Africa (IDA & IBRD countries)',
        'Middle income', 'North America', 'Not classified', 'OECD members', 'Other small states',
        'Pacific island small states', 'Post-demographic dividend', 'Pre-demographic dividend',
        'South Asia', 'South Asia (IDA & IBRD)', 'Sub-Saharan Africa',
        'Sub-Saharan Africa (excluding high income)', 'Sub-Saharan Africa (IDA & IBRD countries)',
        'Upper middle income', 'World'
    ]
    
    # Filtrar agregaciones y obtener países únicos
    df_countries = df_main[~df_main['country'].isin(aggregations_exact)].copy()
    unique_countries = df_countries[['country', 'country_code']].drop_duplicates().reset_index(drop=True)
    
    print(f"🌍 Encontrados {len(unique_countries)} países únicos para procesar.")
    return unique_countries

def get_cities_with_hotels_for_country(country_name: str, country_code: str) -> list:
    """
    Consulta la API de Overpass UNA VEZ por país para obtener todas las ciudades con hoteles.
    
    Args:
        country_name: Nombre del país (para los resultados).
        country_code: Código ISO 3166-1 alpha-2 del país.
    
    Returns:
        Una lista de diccionarios, cada uno con {'country', 'city', 'hotel_count'}.
    """
    # Consulta Overpass QL optimizada:
    # 1. Define el área del país.
    # 2. Encuentra todos los hoteles (nodos, vías, relaciones) dentro de esa área.
    # 3. Para cada hotel, encuentra la ciudad que lo contiene.
    # 4. Agrupa por ciudad y cuenta los hoteles.
    query = f"""
    [out:json][timeout:300];
    area["ISO3166-1"="{country_code}"][admin_level=2]->.country;
    (
      node["tourism"="hotel"](area.country);
      way["tourism"="hotel"](area.country);
      relation["tourism"="hotel"](area.country);
    )->.hotels;
    foreach .hotels -> .hotel (
      .hotel is_in;
      area._[admin_level=8]["name"];
      out;
    )
    """
    try:
        response = requests.post(OVERPASS_URL, data={'data': query})
        response.raise_for_status()  # Lanza un error para códigos 4xx/5xx
        data = response.json()
        
        # Procesar la respuesta para contar hoteles por ciudad
        city_counts = {}
        for element in data.get('elements', []):
            if element.get('type') == 'area' and 'name' in element.get('tags', {}):
                city_name = element['tags']['name']
                city_counts[city_name] = city_counts.get(city_name, 0) + 1
        
        # Formatear la salida
        return [{'country': country_name, 'city': city, 'hotel_count': count} for city, count in city_counts.items()]

    except requests.exceptions.RequestException as e:
        print(f"   - ❌ Error de red para {country_name}: {e}")
        return []
    except Exception as e:
        print(f"   - ❌ Error inesperado procesando {country_name}: {e}")
        return []

def main():
    """
    Función principal para ejecutar el pre-cómputo de datos de hoteles.
    """
    print("🚀 Iniciando el script para pre-calcular datos de hoteles desde OpenStreetMap.")
    
    # Cargar datos principales para obtener la lista de países
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_csv_path = os.path.join(script_dir, "world_tourism_economy_data.csv")
    df_main = pd.read_csv(main_csv_path)
    
    countries_to_process = get_country_list(df_main)
    
    all_results = []
    
    # Usar tqdm para una barra de progreso
    for index, row in tqdm(countries_to_process.iterrows(), total=len(countries_to_process), desc="Procesando Países"):
        country_name = row['country']
        # El código de país debe ser el alpha-2 (2 letras) para la API de Overpass
        country_code_alpha2 = df_main[df_main['country_code'] == row['country_code']]['country_code'].iloc[0]
        
        # Realizar una única consulta por país
        country_cities_data = get_cities_with_hotels_for_country(country_name, country_code_alpha2)
        
        if country_cities_data:
            all_results.extend(country_cities_data)
            print(f"  - ✔️ {country_name}: Encontradas {len(country_cities_data)} ciudades con hoteles.")
        
        time.sleep(10) # Pausa de 10 segundos entre cada país para ser respetuosos con la API

    # Guardar los resultados en un nuevo CSV
    df_results = pd.DataFrame(all_results)
    output_path = os.path.join(script_dir, "osm_cities_with_hotels.csv")
    df_results.to_csv(output_path, index=False)
    
    print(f"\n✅ Proceso completado. Datos guardados en: {output_path}")

if __name__ == "__main__":
    main()
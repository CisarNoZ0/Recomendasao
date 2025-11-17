import pandas as pd
import numpy as np
import os
import requests
import time
import geonamescache

# Estas funciones son una copia de las encontradas en frontv1.py
# para mantener este script independiente.

def _contar_pois_en_ciudad(ciudad, tags_query):
    """Función auxiliar para ejecutar una consulta a la API Overpass."""
    OVERPASS_URL = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:60];
    area[name="{ciudad}"]->.searchArea;
    (
      {tags_query}
    );
    out count;
    """
    try:
        response = requests.get(OVERPASS_URL, params={'data': query})
        response.raise_for_status()
        data = response.json()
        # A veces la API devuelve una estructura diferente si no hay resultados
        if 'elements' in data and len(data['elements']) > 0 and 'tags' in data['elements'][0]:
            return int(data['elements'][0]['tags']['total'])
        return 0
    except (requests.RequestException, KeyError, IndexError, ValueError) as e:
        print(f"    -> Error consultando '{ciudad}': {e}")
        return 0

def enriquecer_con_datos_osm_mejorado(df, columna_pais='Country/Region', max_ciudades_por_pais=3):
    """
    Enriquece el DataFrame buscando dinámicamente las ciudades principales
    y contando puntos de interés, incluyendo hoteles.
    """
    print("Iniciando enriquecimiento con OSM (puede tardar varios minutos)...")
    
    gc = geonamescache.GeonamesCache()
    paises_gc = gc.get_countries()
    ciudades_gc = gc.get_cities()
    country_name_to_iso2 = {data['name']: code for code, data in paises_gc.items()}

    intereses = {
        'Cultura': 'node["tourism"]=["museum"](area.searchArea); way["tourism"]=["museum"](area.searchArea);',
        'Historia': 'node["historic"](area.searchArea); way["historic"](area.searchArea);',
        'Naturaleza': 'node["leisure"]=["park"](area.searchArea); way["leisure"]=["nature_reserve"](area.searchArea);',
        'Hoteles': 'node["tourism"]=["hotel"](area.searchArea); way["tourism"]=["hotel"](area.searchArea);'
    }

    resultados_ciudades = []
    paises_en_df = df[columna_pais].unique()
    
    total_paises = len(paises_en_df)
    for i, nombre_pais in enumerate(paises_en_df):
        print(f"\n[{i+1}/{total_paises}] Procesando País: {nombre_pais}")
        codigo_iso2 = country_name_to_iso2.get(nombre_pais)
        if not codigo_iso2:
            print(f"  -> Advertencia: No se encontró código ISO para {nombre_pais}. Saltando.")
            continue

        ciudades_del_pais = [ciudades_gc[key] for key in ciudades_gc if ciudades_gc[key]['countrycode'] == codigo_iso2]
        ciudades_del_pais.sort(key=lambda x: x['population'], reverse=True)
        ciudades_a_procesar = ciudades_del_pais[:max_ciudades_por_pais]

        if not ciudades_a_procesar:
            print(f"  -> Advertencia: No se encontraron ciudades en la base de datos local para {nombre_pais}.")
            continue

        for ciudad_data in ciudades_a_procesar:
            nombre_ciudad = ciudad_data['name']
            print(f"  -> Ciudad: {nombre_ciudad}...")
            
            fila = {'ciudad': nombre_ciudad, 'pais': nombre_pais}
            for nombre_interes, tags_query in intereses.items():
                print(f"    -> Contando '{nombre_interes}'...")
                conteo = _contar_pois_en_ciudad(nombre_ciudad, tags_query)
                fila[f"osm_{nombre_interes.lower()}"] = conteo
                time.sleep(1)  # Pausa para no sobrecargar la API
            
            resultados_ciudades.append(fila)

    if not resultados_ciudades:
        print("Advertencia: No se obtuvieron datos de ciudades desde OSM.")
        return df

    df_ciudades = pd.DataFrame(resultados_ciudades)
    
    columnas_intereses = ['osm_cultura', 'osm_historia', 'osm_naturaleza']
    df_agregado = df_ciudades.groupby('pais')[columnas_intereses].sum().reset_index()
    
    df_enriquecido = df.merge(df_agregado, left_on=columna_pais, right_on='pais', how='left')
    df_enriquecido[columnas_intereses] = df_enriquecido[columnas_intereses].fillna(0).astype(int)

    df_final = df_enriquecido.merge(df_ciudades[['pais', 'ciudad', 'osm_hoteles']], left_on=columna_pais, right_on='pais', how='left')
    
    print("¡Enriquecimiento con OSM completado!")
    return df_final.drop(columns=['pais_x', 'pais_y']).rename(columns={'ciudad': 'City'})

def clasificar_ambiente_por_hoteles(df, columna_pais='Country/Region'):
    """
    Clasifica el "ambiente" de una ciudad basado en la densidad de hoteles.
    """
    print("Clasificando ambiente de ciudades por densidad de hoteles...")
    if 'osm_hoteles' not in df.columns:
        print("Advertencia: La columna 'osm_hoteles' no existe. No se puede clasificar.")
        df['clasificacion_ambiente'] = 'Indefinido'
        return df

    q_low = df.groupby(columna_pais)['osm_hoteles'].transform(lambda x: x.quantile(0.33))
    q_high = df.groupby(columna_pais)['osm_hoteles'].transform(lambda x: x.quantile(0.66))

    conditions = [
        (df['osm_hoteles'] <= q_low) & (df['osm_hoteles'] < q_high),
        (df['osm_hoteles'] >= q_high) & (df['osm_hoteles'] > q_low)
    ]
    choices = ['Refugio Tranquilo', 'Centro Vibrante']
    
    df['clasificacion_ambiente'] = pd.Series(pd.NA, index=df.index)		.mask(conditions[0], choices[0])		.mask(conditions[1], choices[1])		.fillna('Equilibrado')

    print("Clasificación de ambiente completada.")
    return df

def load_base_data():
    """Carga y limpia los datos base del CSV original."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "world_tourism_economy_data.csv")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"Error al leer el CSV: {e}")
        return pd.DataFrame()
    
    aggregations_exact = [
        'World', 'Euro area', 'European Union', 'High income', 'Low income', 'Middle income',
        'Lower middle income', 'Upper middle income', 'Low & middle income', 'OECD members',
        'East Asia & Pacific', 'East Asia & Pacific (excluding high income)', 'East Asia & Pacific (IDA & IBRD countries)',
        'Europe & Central Asia', 'Europe & Central Asia (excluding high income)', 'Europe & Central Asia (IDA & IBRD countries)',
        'Latin America & Caribbean', 'Latin America & Caribbean (excluding high income)', 'Latin America & the Caribbean (IDA & IBRD countries)',
        'Middle East & North Africa', 'Middle East & North Africa (excluding high income)', 'Middle East & North Africa (IDA & IBRD countries)',
        'South Asia', 'South Asia (IDA & IBRD)', 'Sub-Saharan Africa', 'Sub-Saharan Africa (excluding high income)',
        'Sub-Saharan Africa (IDA & IBRD countries)', 'Small states', 'Caribbean small states', 'Pacific island small states',
        'Other small states', 'Fragile and conflict affected situations', 'Heavily indebted poor countries (HIPC)',
        'IDA & IBRD total', 'IDA blend', 'IDA only', 'IBRD only', 'IDA total',
        'Least developed countries: UN classification', 'Arab World', 'Central Europe and the Baltics',
        'Africa Eastern and Southern', 'Africa Western and Central', 'Early-demographic dividend',
        'Late-demographic dividend', 'Pre-demographic dividend', 'Post-demographic dividend', 'North America',
    ]
    
    mask = ~df['country'].isin(aggregations_exact)
    df = df[mask].copy()
    
    df_latest = df.copy()
    df_latest = df_latest[
        (df_latest['tourism_receipts'].notna()) | (df_latest['tourism_arrivals'].notna())
    ].sort_values(['country', 'year']).groupby('country').tail(1).copy()
    
    if df_latest.empty:
        df_latest = df.sort_values('year').groupby('country').tail(1).copy()
    
    df_latest['costo_por_turista'] = np.where(
        (df_latest['tourism_receipts'].notna()) & (df_latest['tourism_arrivals'].notna()),
        df_latest['tourism_receipts'] / df_latest['tourism_arrivals'],
        np.nan
    )
    
    df_trend = df.sort_values('year').groupby('country').agg({
        'tourism_arrivals': 'last', 'year': 'last'
    }).reset_index()
    
    df_trend_prev = df[df['year'] < df['year'].max()].sort_values('year').groupby('country').agg({
        'tourism_arrivals': 'last'
    }).reset_index()
    df_trend_prev.columns = ['country', 'tourism_arrivals_prev']
    
    df_trend = df_trend.merge(df_trend_prev, on='country', how='left')
    df_trend['crecimiento_anual'] = ((df_trend['tourism_arrivals'] - df_trend['tourism_arrivals_prev']) 
                                      / df_trend['tourism_arrivals_prev'] * 100).fillna(0)
    
    df_latest = df_latest.merge(df_trend[['country', 'crecimiento_anual']], on='country', how='left')
    df_latest = df_latest[(df_latest['tourism_receipts'].notna()) | (df_latest['tourism_arrivals'].notna())].copy()
    
    df_latest['costo_por_turista'] = df_latest['costo_por_turista'].fillna(df_latest['costo_por_turista'].median())
    df_latest['tourism_arrivals'] = df_latest['tourism_arrivals'].fillna(0)
    df_latest['tourism_receipts'] = df_latest['tourism_receipts'].fillna(0)
    
    return df_latest

if __name__ == "__main__":
    print("Cargando datos base...")
    df_base = load_base_data()
    
    if not df_base.empty:
        print("Iniciando proceso de enriquecimiento de datos. Esto puede tardar mucho tiempo.")
        df_enriquecido = enriquecer_con_datos_osm_mejorado(df_base, columna_pais='country', max_ciudades_por_pais=3)
        
        print("Iniciando clasificación de ambiente...")
        df_clasificado = clasificar_ambiente_por_hoteles(df_enriquecido, columna_pais='country')
        
        # Guardar el archivo final
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos_enriquecidos.csv")
        df_clasificado.to_csv(output_path, index=False)
        
        print(f"\n¡Proceso completado! Los datos enriquecidos se han guardado en:\n{output_path}")
    else:
        print("No se pudieron cargar los datos base. El proceso ha sido cancelado.")

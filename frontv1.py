import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import requests
import time
import geonamescache
# FUNCIONES AUXILIARES
def _contar_pois_en_ciudad(ciudad, tags_query):
    """Función auxiliar para ejecutar una consulta a la API Overpass."""
    OVERPASS_URL = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json][timeout:25];
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
        return int(data['elements'][0]['tags']['total'])
    except (requests.RequestException, KeyError, IndexError, ValueError):
        return 0

@st.cache_data
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
        'Cultura': 'node["tourism"="museum"](area.searchArea); way["tourism"="museum"](area.searchArea);',
        'Historia': 'node["historic"](area.searchArea); way["historic"](area.searchArea);',
        'Naturaleza': 'node["leisure"="park"](area.searchArea); way["leisure"="nature_reserve"](area.searchArea);',
        # TAREA 1.1 
        'Hoteles': 'node["tourism"="hotel"](area.searchArea); way["tourism"="hotel"](area.searchArea);'
    }

    resultados_ciudades = []
    paises_en_df = df[columna_pais].unique()
    
    for nombre_pais in paises_en_df:
        codigo_iso2 = country_name_to_iso2.get(nombre_pais)
        if not codigo_iso2: continue

        ciudades_del_pais = [ciudades_gc[key] for key in ciudades_gc if ciudades_gc[key]['countrycode'] == codigo_iso2]
        ciudades_del_pais.sort(key=lambda x: x['population'], reverse=True)
        ciudades_a_procesar = ciudades_del_pais[:max_ciudades_por_pais]

        if not ciudades_a_procesar: continue
        print(f"\nProcesando País: {nombre_pais}")

        for ciudad_data in ciudades_a_procesar:
            nombre_ciudad = ciudad_data['name']
            print(f"  -> Ciudad: {nombre_ciudad}...")
            
            fila = {'ciudad': nombre_ciudad, 'pais': nombre_pais}
            for nombre_interes, tags_query in intereses.items():
                conteo = _contar_pois_en_ciudad(nombre_ciudad, tags_query)
                # El nombre de la columna será, por ejemplo, 'osm_hoteles'
                fila[f"osm_{nombre_interes.lower()}"] = conteo
                time.sleep(1)
            
            resultados_ciudades.append(fila)

    if not resultados_ciudades:
        print("Advertencia: No se obtuvieron datos de ciudades desde OSM.")
        return df

    df_ciudades = pd.DataFrame(resultados_ciudades)
    
    # Agregamos los datos de intereses a nivel de país (sumando los de sus ciudades)
    columnas_intereses = ['osm_cultura', 'osm_historia', 'osm_naturaleza']
    df_agregado = df_ciudades.groupby('pais')[columnas_intereses].sum().reset_index()
    
    df_enriquecido = df.merge(df_agregado, left_on=columna_pais, right_on='pais', how='left')
    df_enriquecido[columnas_intereses] = df_enriquecido[columnas_intereses].fillna(0).astype(int)

    # Unimos los datos de hoteles a nivel de ciudad
    df_final = df_enriquecido.merge(df_ciudades[['pais', 'ciudad', 'osm_hoteles']], left_on=columna_pais, right_on='pais', how='left')
    
    print("¡Enriquecimiento con OSM completado!")
    return df_final.drop(columns=['pais_x', 'pais_y']).rename(columns={'ciudad': 'City'})

def clasificar_ambiente_por_hoteles(df, columna_pais='Country/Region'):
    """
    Clasifica el "ambiente" de una ciudad basado en la densidad de hoteles
    en comparación con otras ciudades del mismo país.
    """
    print("Clasificando ambiente de ciudades por densidad de hoteles...")

    # Usamos transform para calcular los cuantiles para cada grupo de país
    q_low = df.groupby(columna_pais)['osm_hoteles'].transform(lambda x: x.quantile(0.33))
    q_high = df.groupby(columna_pais)['osm_hoteles'].transform(lambda x: x.quantile(0.66))

    # Creamos la nueva columna 'clasificacion_ambiente'
    conditions = [
        (df['osm_hoteles'] <= q_low) & (df['osm_hoteles'] < q_high), # Menos hoteles (y no es el único valor)
        (df['osm_hoteles'] >= q_high) & (df['osm_hoteles'] > q_low)  # Más hoteles (y no es el único valor)
    ]
    choices = ['Refugio Tranquilo', 'Centro Vibrante']
    
    df['clasificacion_ambiente'] = pd.Series(
        pd.NA, index=df.index
    ).mask(conditions[0], choices[0]).mask(conditions[1], choices[1]).fillna('Equilibrado')

    print("Clasificación de ambiente completada.")
    return df


@st.cache_data
def obtener_ciudades_con_hoteles_osm(pais):
    """
    Obtiene una lista de ciudades y su cantidad de hoteles para un país específico
    utilizando la API Overpass de OpenStreetMap.
    """
    st.info(f"Buscando ciudades con hoteles en {pais} vía OSM... Esto puede tardar un momento.")
    
    gc = geonamescache.GeonamesCache()
    paises_gc = gc.get_countries()
    ciudades_gc = gc.get_cities()
    country_name_to_iso2 = {data['name']: code for code, data in paises_gc.items()}

    codigo_iso2 = country_name_to_iso2.get(pais)
    if not codigo_iso2:
        st.warning(f"No se encontró el código ISO para '{pais}'. No se pueden buscar ciudades.")
        return pd.DataFrame({'ciudad': [], 'hoteles': []})

    ciudades_del_pais = [ciudades_gc[key] for key in ciudades_gc if ciudades_gc[key]['countrycode'] == codigo_iso2]
    ciudades_del_pais.sort(key=lambda x: x['population'], reverse=True)
    
    # Limitar a las 20 ciudades más pobladas para no sobrecargar la API
    ciudades_a_procesar = ciudades_del_pais[:20]

    if not ciudades_a_procesar:
        st.warning(f"No se encontraron ciudades para '{pais}' en la base de datos local.")
        return pd.DataFrame({'ciudad': [], 'hoteles': []})

    resultados = []
    progress_bar = st.progress(0, text="Consultando ciudades en OSM...")

    for i, ciudad_data in enumerate(ciudades_a_procesar):
        nombre_ciudad = ciudad_data['name']
        query_hoteles = f'node["tourism"="hotel"](area.searchArea); way["tourism"="hotel"](area.searchArea);'
        
        # Reutilizamos la función auxiliar existente
        num_hoteles = _contar_pois_en_ciudad(nombre_ciudad, query_hoteles)
        
        if num_hoteles > 0:
            resultados.append({'ciudad': nombre_ciudad, 'hoteles': num_hoteles})
        
        # Actualizar barra de progreso
        progress_text = f"Consultando ciudades en OSM... ({i+1}/{len(ciudades_a_procesar)})"
        progress_bar.progress((i + 1) / len(ciudades_a_procesar), text=progress_text)
        time.sleep(1) # Pausa para no sobrecargar la API

    progress_bar.empty()

    if not resultados:
        st.warning(f"No se encontraron hoteles en las principales ciudades de {pais} a través de OSM.")
        return pd.DataFrame({'ciudad': [], 'hoteles': []})

    return pd.DataFrame(resultados)


# --- Configuración de la Página ---
st.set_page_config(
    page_title="Recomendador Turístico",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state para almacenar datos históricos
if 'df_trend_historico' not in st.session_state:
    st.session_state.df_trend_historico = None

# Inicializar session state para perfil de usuario
if 'paises_ideales' not in st.session_state:
    st.session_state.paises_ideales = []
if 'paises_no_ideales' not in st.session_state:
    st.session_state.paises_no_ideales = []
if 'perfil_generado' not in st.session_state:
    st.session_state.perfil_generado = False
if 'perfil_datos' not in st.session_state:
    st.session_state.perfil_datos = None

# --- Capa de Datos (Datos Reales) ---
@st.cache_data
def load_data():
    """Carga datos históricos reales del CSV world_tourism_economy_data.csv"""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "world_tourism_economy_data.csv")
    
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        st.error(f"Error al leer el CSV: {e}")
        return pd.DataFrame()
    
    # Filtrar solo datos de países individuales (excluir agregaciones)
    # Lista exacta de agregaciones del Banco Mundial (entidades no-país)
    aggregations_exact = [
        'World',
        'Euro area',
        'European Union',
        'High income',
        'Low income',
        'Middle income',
        'Lower middle income',
        'Upper middle income',
        'Low & middle income',
        'OECD members',
        'East Asia & Pacific',
        'East Asia & Pacific (excluding high income)',
        'East Asia & Pacific (IDA & IBRD countries)',
        'Europe & Central Asia',
        'Europe & Central Asia (excluding high income)',
        'Europe & Central Asia (IDA & IBRD countries)',
        'Latin America & Caribbean',
        'Latin America & Caribbean (excluding high income)',
        'Latin America & the Caribbean (IDA & IBRD countries)',
        'Middle East & North Africa',
        'Middle East & North Africa (excluding high income)',
        'Middle East & North Africa (IDA & IBRD countries)',
        'South Asia',
        'South Asia (IDA & IBRD)',
        'Sub-Saharan Africa',
        'Sub-Saharan Africa (excluding high income)',
        'Sub-Saharan Africa (IDA & IBRD countries)',
        'Small states',
        'Caribbean small states',
        'Pacific island small states',
        'Other small states',
        'Fragile and conflict affected situations',
        'Heavily indebted poor countries (HIPC)',
        'IDA & IBRD total',
        'IDA blend',
        'IDA only',
        'IBRD only',
        'IDA total',
        'Least developed countries: UN classification',
        'Arab World',
        'Central Europe and the Baltics',
        'Africa Eastern and Southern',
        'Africa Western and Central',
        'Early-demographic dividend',
        'Late-demographic dividend',
        'Pre-demographic dividend',
        'Post-demographic dividend',
        'North America',
    ]
    
    # Crear máscara: excluir filas donde country coincida exactamente con agregaciones
    mask = ~df['country'].isin(aggregations_exact)
    df = df[mask].copy()
    
    # Usar datos más recientes por país (buscar último año con datos de turismo)
    df_latest = df.copy()
    
    # Para cada país, encontrar el último registro que tenga tourism_receipts O tourism_arrivals
    df_latest = df_latest[
        (df_latest['tourism_receipts'].notna()) | (df_latest['tourism_arrivals'].notna())
    ].sort_values(['country', 'year']).groupby('country').tail(1).copy()
    
    if df_latest.empty:
        # Si no hay datos de turismo, usar el más reciente de todas formas
        df_latest = df.sort_values('year').groupby('country').tail(1).copy()
    
    # Calcular costo promedio por turista (solo si ambos están disponibles)
    df_latest['costo_por_turista'] = np.where(
        (df_latest['tourism_receipts'].notna()) & (df_latest['tourism_arrivals'].notna()),
        df_latest['tourism_receipts'] / df_latest['tourism_arrivals'],
        np.nan
    )
    
    # Calcular tendencia
    df_trend = df.sort_values('year').groupby('country').agg({
        'tourism_arrivals': 'last',
        'year': 'last'
    }).reset_index()
    
    df_trend_prev = df[df['year'] < df['year'].max()].sort_values('year').groupby('country').agg({
        'tourism_arrivals': 'last'
    }).reset_index()
    df_trend_prev.columns = ['country', 'tourism_arrivals_prev']
    
    df_trend = df_trend.merge(df_trend_prev, on='country', how='left')
    df_trend['crecimiento_anual'] = ((df_trend['tourism_arrivals'] - df_trend['tourism_arrivals_prev']) 
                                      / df_trend['tourism_arrivals_prev'] * 100).fillna(0)
    
    df_latest = df_latest.merge(df_trend[['country', 'crecimiento_anual']], on='country', how='left')
    
    # Mantener registros que tengan al menos tourism_arrivals o tourism_receipts
    df_latest = df_latest[(df_latest['tourism_receipts'].notna()) | (df_latest['tourism_arrivals'].notna())].copy()
    
    # Llenar valores faltantes con promedios razonables
    df_latest['costo_por_turista'] = df_latest['costo_por_turista'].fillna(df_latest['costo_por_turista'].median())
    df_latest['tourism_arrivals'] = df_latest['tourism_arrivals'].fillna(0)
    df_latest['tourism_receipts'] = df_latest['tourism_receipts'].fillna(0)
    
    # Guardar datos históricos completos para visualización de tendencias (últimos 10 años)
    df_trend_completo = df[df['year'] >= df['year'].max() - 10].sort_values(['country', 'year'])
    st.session_state.df_trend_historico = df_trend_completo
    
    return df_latest

@st.cache_data
def get_processed_data():
    """
    Función única para cargar, enriquecer y procesar todos los datos.
    El resultado se cachea para evitar recálculos en cada interacción.
    La primera ejecución puede tardar varios minutos.
    """
    with st.spinner("Cargando y procesando datos por primera vez. Esto puede tardar varios minutos..."):
        df_destinos = load_data()
        #INICIO: ENRIQUECIMIENTO CON DATOS OSM Y CLASIFICACIÓN
        df_enriquecido = enriquecer_con_datos_osm_mejorado(df_destinos, columna_pais='country', max_ciudades_por_pais=3)
        df_clasificado = clasificar_ambiente_por_hoteles(df_enriquecido, columna_pais='country')
        #FIN: ENRIQUECIMIENTO
    return df_clasificado

df_clasificado = get_processed_data()
# Manejar el caso donde no hay datos válidos
if df_clasificado.empty:
    st.error("❌ No hay datos válidos disponibles. Verifica que el archivo CSV esté correcto.")
    st.stop()

# --- Barra Lateral (Inputs del Usuario) ---
st.sidebar.header("✈️ Tu Perfil de Viajero")
st.sidebar.write("Define tus preferencias.")

# Calcular rangos dinámicos basados en datos reales
min_budget = float(df_clasificado['costo_por_turista'].quantile(0.05))
max_budget = float(df_clasificado['costo_por_turista'].quantile(0.95))
median_budget = float(df_clasificado['costo_por_turista'].median())

# 1. Input de Presupuesto por persona
presupuesto = st.sidebar.slider(
    '¿Cuál es tu presupuesto máximo por persona (USD)?',
    min_value=int(min_budget) if not pd.isna(min_budget) else 100,
    max_value=int(max_budget) if not pd.isna(max_budget) else 10000,
    value=int(median_budget) if not pd.isna(median_budget) else 2000,
    step=100,
    help="Basado en el costo promedio por turista en cada destino"
)

# 2. Input de Interés Turístico (basado en llegadas de turistas)
interes_turistico = st.sidebar.select_slider(
    '¿Qué tan popular prefieres que sea el destino?',
    options=['Joyas ocultas (pocas llegadas)', 'Emergentes (crecimiento)', 'Populares (muchas llegadas)'],
    value='Populares (muchas llegadas)',
    help="Basado en datos históricos de llegadas de turistas"
)

# 3. Input de Situación Económica
salud_economica = st.sidebar.selectbox(
    '¿Qué estabilidad económica buscas?',
    options=['Flexible (cualquiera)', 'Estable (baja inflación/desempleo)', 'En crecimiento (alta demanda)'],
    help="Basado en inflación, desempleo y demanda turística"
)

# 4. Filtro por región (opcional)
regiones_disponibles = ['Todas'] + sorted(df_clasificado['country'].unique().tolist())[:50]  # Top 50
region = st.sidebar.selectbox(
    'Filtrar por región/país (opcional):',
    options=regiones_disponibles
)

# ============================================
# SECCIÓN: PERFIL DE USUARIO PERSONALIZADO
# ============================================
st.sidebar.divider()
st.sidebar.markdown("### 👤 Tu Perfil Personalizado")
st.sidebar.write("Ayúdanos a entender tus preferencias turísticas reales")

# Selector de destinos ideales (favoritos)
st.sidebar.subheader("✅ Destinos Ideales")
st.sidebar.caption("Países que visitaste y te *encantaron*")
paises_ideales_input = st.sidebar.multiselect(
    "Selecciona destinos que visitaste y amaste:",
    sorted(df_clasificado['country'].unique().tolist()),
    default=st.session_state.paises_ideales,
    key='paises_ideales_selector',
    help="Estos países sirven como referencia para encontrar similares"
)
st.session_state.paises_ideales = paises_ideales_input

# Selector de destinos no-ideales (no te gustaron)
st.sidebar.subheader("❌ Destinos No-Ideales")
st.sidebar.caption("Países que visitaste pero no recomendarías")
paises_no_ideales_input = st.sidebar.multiselect(
    "Selecciona destinos que NO te gustaron:",
    sorted(df_clasificado['country'].unique().tolist()),
    default=st.session_state.paises_no_ideales,
    key='paises_no_ideales_selector',
    help="Ayuda al sistema a evitar destinos similares a estos"
)
st.session_state.paises_no_ideales = paises_no_ideales_input

# Botón para generar perfil
if st.sidebar.button('🎯 Generar Perfil Personalizado', use_container_width=True):
    try:
        from perfil_usuario import extraer_perfil_usuario
        
        st.session_state.perfil_datos = extraer_perfil_usuario(
            df_clasificado,
            st.session_state.paises_ideales,
            st.session_state.paises_no_ideales
        )
        st.session_state.perfil_generado = True
        st.sidebar.success("✅ Perfil generado exitosamente")
    except ImportError as e:
        st.sidebar.error(f"⚠️ Error al cargar módulo de perfil: {e}")
    except Exception as e:
        st.sidebar.error(f"❌ Error al generar perfil: {e}")

# Mostrar estado del perfil
if st.session_state.perfil_generado:
    st.sidebar.info(f"👤 Perfil activo con {len(st.session_state.paises_ideales)} favoritos y {len(st.session_state.paises_no_ideales)} rechazados")
else:
    st.sidebar.caption("💡 Tip: Selecciona destinos para activar el sistema de similitud")

# --- Capa Lógica (Motor de Recomendación Mejorado) ---

def generar_recomendaciones(df, presupuesto, interes_turistico, salud_economica, region, perfil_generado, perfil_datos):
    """
    Motor de recomendación unificado.
    Combina filtros de viajero, métricas económicas y perfil de similitud personal.
    """
    df_filtrado = df.copy()

    # --- PASO 1: Filtros directos ---
    df_filtrado = df_filtrado[df_filtrado['costo_por_turista'] <= presupuesto]
    if region != 'Todas':
        df_filtrado = df_filtrado[df_filtrado['country'] == region]

    if df_filtrado.empty:
        return df_filtrado

    # --- PASO 2: Score General (basado en sliders del "perfil de viajero") ---
    # Score de Interés Turístico
    if interes_turistico == 'Joyas ocultas (pocas llegadas)':
        # Normaliza las llegadas y combina con el crecimiento
        norm_arrivals = 1 - (df_filtrado['tourism_arrivals'] / df_filtrado['tourism_arrivals'].max())
        norm_growth = df_filtrado['crecimiento_anual'] / 100
        df_filtrado['score_turismo'] = (norm_arrivals + norm_growth) / 2
    elif interes_turistico == 'Emergentes (crecimiento)':
        # Prioriza crecimiento positivo
        df_filtrado['score_turismo'] = np.maximum(df_filtrado['crecimiento_anual'], 0) / 100
    else:  # Populares
        # Prioriza destinos con más llegadas
        df_filtrado['score_turismo'] = df_filtrado['tourism_arrivals'] / df_filtrado['tourism_arrivals'].max()

    # Score de Estabilidad Económica
    if salud_economica == 'Estable (baja inflación/desempleo)':
        # Normaliza inflación y desempleo (menor es mejor)
        inflation_norm = 1 - (df_filtrado['inflation'].fillna(df_filtrado['inflation'].median()) / df_filtrado['inflation'].max())
        unemployment_norm = 1 - (df_filtrado['unemployment'].fillna(df_filtrado['unemployment'].median()) / df_filtrado['unemployment'].max())
        df_filtrado['score_economia'] = (inflation_norm + unemployment_norm) / 2
    elif salud_economica == 'En crecimiento (alta demanda)':
        # Asocia crecimiento económico con crecimiento turístico
        df_filtrado['score_economia'] = df_filtrado['crecimiento_anual'] / 100
    else:  # Flexible
        df_filtrado['score_economia'] = 0.5  # Puntaje neutral
    
    # Combinar scores de sliders en un "Score General"
    df_filtrado['score_general'] = (df_filtrado['score_turismo'] * 0.6 + df_filtrado['score_economia'] * 0.4)

    # --- PASO 3: Score de Similitud Personal (si el perfil personalizado está activo) ---
    df_filtrado['similitud_score'] = 0.0
    if perfil_generado and perfil_datos is not None:
        try:
            from perfil_usuario import calcular_similitud_para_todos
            
            df_filtrado['similitud_score'] = calcular_similitud_para_todos(
                df_filtrado,
                perfil_datos
            )
            
            # Unificar los scores: 70% perfil personal, 30% perfil de viajero (sliders)
            ponderacion_similitud = 0.7
            ponderacion_general = 0.3
            df_filtrado['score_final'] = (df_filtrado['similitud_score'] * ponderacion_similitud) + (df_filtrado['score_general'] * ponderacion_general)
            
            # Usar st.info para notificar al usuario que su perfil está siendo usado
            st.info("🎯 Perfil Personalizado Activo. Las recomendaciones combinan tus gustos con los filtros generales.")

        except Exception as e:
            st.warning(f"⚠️ No se pudo calcular la similitud personalizada: {e}. Usando ranking general.")
            df_filtrado['score_final'] = df_filtrado['score_general']
    else:
        # Si no hay perfil, el score final es simplemente el score general de los sliders
        df_filtrado['score_final'] = df_filtrado['score_general']
        
    # --- PASO 4: Ordenar y devolver el TOP 10 ---
    # Si hay perfil, se ordena por similitud y luego por score general. Si no, solo por score final.
    if perfil_generado and perfil_datos is not None:
        df_recomendado = df_filtrado.sort_values(by=['similitud_score', 'score_final'], ascending=False)
    else:
        df_recomendado = df_filtrado.sort_values('score_final', ascending=False)
        
    return df_recomendado.head(10)


# --- Capa de Presentación (UI Principal) ---

st.title("🌍 Sistema de Recomendación Turística")
st.subheader("Basado en Datos Históricos Objetivos (1999-2023)")
st.write("""
Este sistema utiliza datos históricos reales de turismo y economía para recomendarte
destinos que se ajusten a tu perfil y presupuesto, evitando sesgos subjetivos.
""")

# Mostrar resumen de filtros seleccionados
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Presupuesto", f"${presupuesto:,}")
with col2:
    st.metric("Tipo de Destino", interes_turistico.split('(')[0].strip())
with col3:
    st.metric("Salud Económica", salud_economica.split('(')[0].strip())
with col4:
    st.metric("Destinos Disponibles", len(df_clasificado))

st.divider()

# Botón para generar la recomendación
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 3])
with col_btn1:
    generar_btn = st.button('🔍 Generar Recomendaciones', type='primary', use_container_width=True)
with col_btn2:
    limpiar_btn = st.button('🔄 Limpiar', use_container_width=True)

if generar_btn or ('mostrar_recomendaciones' in st.session_state and st.session_state.mostrar_recomendaciones):
    st.session_state.mostrar_recomendaciones = True
    
    with st.spinner('Analizando datos y aplicando tu perfil... 📊'):
        # Llamar a la función lógica unificada, pasando todos los parámetros necesarios
        recomendaciones = generar_recomendaciones(
            df=df_clasificado,
            presupuesto=presupuesto,
            interes_turistico=interes_turistico,
            salud_economica=salud_economica,
            region=region,
            perfil_generado=st.session_state.perfil_generado,
            perfil_datos=st.session_state.perfil_datos
        )


        if recomendaciones.empty:
            st.warning('⚠️ No se encontraron destinos que coincidan con todos tus criterios. Intenta ampliar tu búsqueda.')
        else:
            st.success("✅ ¡Hemos encontrado estos destinos para ti!")
            
            # Tabs para diferentes vistas
            tab1, tab2, tab3, tab4, tab5 = st.tabs(["📍 Recomendaciones", "📊 Comparativa", "👤 Mi Perfil", "📈 Tendencias", "🏛️ Ciudades del Destino"])
            
            with tab1:
                # Mostrar resultados
                for idx, (index, row) in enumerate(recomendaciones.iterrows(), 1):
                    with st.container(border=True):
                        col_rank, col_info = st.columns([0.5, 2])
                        
                        with col_rank:
                            st.metric("Ranking", f"#{idx}")
                        
                        with col_info:
                            st.markdown(f"### 🌏 {row['country']}")
                        
                        # Métricas principales
                        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                        with m_col1:
                            st.metric(
                                "Costo/Turista",
                                f"${row['costo_por_turista']:,.0f}",
                                help="Ingresos de turismo ÷ llegadas de turistas"
                            )
                        with m_col2:
                            st.metric(
                                "Llegadas Anuales",
                                f"{row['tourism_arrivals']/1e6:.2f}M",
                                help="Número de llegadas en últimos datos"
                            )
                        with m_col3:
                            crecimiento = row['crecimiento_anual']
                            color = "green" if crecimiento > 0 else "red"
                            st.metric(
                                "Crecimiento",
                                f"{crecimiento:+.1f}%",
                                delta=f"{crecimiento:.1f}%",
                                help="Cambio anual en llegadas de turistas"
                            )
                        with m_col4:
                            st.metric(
                                "Score Final",
                                f"{row['score_final']:.2f}",
                                help="Combinación de popularidad y economía"
                            )
                        
                        # Barra de similitud personalizada (si el perfil está activo)
                        if st.session_state.perfil_generado and row['similitud_score'] > 0:
                            similitud_pct = row['similitud_score'] * 100
                            st.progress(
                                row['similitud_score'],
                                text=f"🎯 Similitud con tu Perfil: {similitud_pct:.1f}%"
                            )
                        
                        # Información económica adicional
                        econ_col1, econ_col2, econ_col3 = st.columns(3)
                        with econ_col1:
                            st.metric(
                                "Inflación",
                                f"{row['inflation']:.1f}%",
                                help="Tasa de inflación (% anual)" if pd.notna(row['inflation']) else "No disponible"
                            )
                        with econ_col2:
                            st.metric(
                                "Desempleo",
                                f"{row['unemployment']:.1f}%" if pd.notna(row['unemployment']) else "N/A",
                                help="Tasa de desempleo" if pd.notna(row['unemployment']) else "No disponible"
                            )
                        with econ_col3:
                            gdp_billions = row['gdp'] / 1e9
                            st.metric(
                                "GDP",
                                f"${gdp_billions:,.0f}B",
                                help="Producto Interno Bruto"
                            )
                        
                        st.markdown(f"""
                        **Recibos de Turismo:** ${row['tourism_receipts']/1e9:.2f}B | 
                        **Año Datos:** {int(row['year'])} | 
                        **Código País:** {row['country_code']}
                        """)
            
            with tab2:
                # Tabla comparativa
                df_compare = recomendaciones[[
                    'country', 'costo_por_turista', 'tourism_arrivals', 'crecimiento_anual',
                    'inflation', 'unemployment', 'score_final'
                ]].copy()
                
                df_compare.columns = ['País', 'Costo/Turista ($)', 'Llegadas (M)', 'Crecimiento (%)', 
                                     'Inflación (%)', 'Desempleo (%)', 'Score']
                
                df_compare['Llegadas (M)'] = df_compare['Llegadas (M)'] / 1e6
                
                st.dataframe(
                    df_compare.style.format({
                        'Costo/Turista ($)': '{:,.0f}',
                        'Llegadas (M)': '{:.2f}',
                        'Crecimiento (%)': '{:+.1f}',
                        'Inflación (%)': '{:.1f}',
                        'Desempleo (%)': '{:.1f}',
                        'Score': '{:.3f}'
                    }),
                    use_container_width=True,
                    hide_index=True
                )
            
            with tab3:
                st.subheader("👤 Tu Perfil Personalizado")
                
                if st.session_state.perfil_generado and st.session_state.perfil_datos is not None:
                    perfil = st.session_state.perfil_datos
                    
                    # SECCIÓN 1: Destinos Seleccionados
                    st.markdown("### ✅ Destinos Ideales (que te ENCANTARON)")
                    if st.session_state.paises_ideales:
                        col1, col2 = st.columns(2)
                        for idx, pais in enumerate(st.session_state.paises_ideales):
                            if idx % 2 == 0:
                                with col1:
                                    st.info(f"🌍 {pais}")
                            else:
                                with col2:
                                    st.info(f"🌍 {pais}")
                    else:
                        st.caption("No hay destinos ideales seleccionados")
                    
                    st.markdown("### ❌ Destinos No-Ideales (a EVITAR)")
                    if st.session_state.paises_no_ideales:
                        col1, col2 = st.columns(2)
                        for idx, pais in enumerate(st.session_state.paises_no_ideales):
                            if idx % 2 == 0:
                                with col1:
                                    st.warning(f"⛔ {pais}")
                            else:
                                with col2:
                                    st.warning(f"⛔ {pais}")
                    else:
                        st.caption("No hay destinos a evitar seleccionados")
                    
                    st.divider()
                    
                    # SECCIÓN 2: Características Extraídas
                    st.markdown("### 📊 Características de Tu Perfil")
                    
                    metric_col1, metric_col2, metric_col3 = st.columns(3)
                    
                    with metric_col1:
                        st.metric(
                            "🎯 Densidad Ideal",
                            f"{perfil['densidad_ideal_media']/1e6:.2f}M",
                            help="Promedio de llegadas de turistas en destinos que te encantaron"
                        )
                    
                    with metric_col2:
                        st.metric(
                            "💰 Presupuesto Ideal",
                            f"${perfil['presupuesto_ideal_media']:,.0f}",
                            help="Costo promedio por turista en destinos favoritos"
                        )
                    
                    with metric_col3:
                        st.metric(
                            "🏆 Tipo de Turismo",
                            perfil['tipo_turismo_ideal'],
                            help="Clasificación preferida de destino"
                        )
                    
                    st.divider()
                    
                    # SECCIÓN 3: Gráfico Comparativo
                    st.markdown("### 📈 Comparativa: Ideales vs. A Evitar")
                    
                    if perfil['densidad_evitar_media'] and perfil['presupuesto_evitar_media']:
                        try:
                            import matplotlib.pyplot as plt
                            
                            # Gráfico 1: Densidad (primera fila)
                            fig1, ax1 = plt.subplots(1, 1, figsize=(10, 4))
                            
                            categorias_densidad = ['Ideales', 'A Evitar']
                            valores_densidad = [
                                perfil['densidad_ideal_media'] / 1e6,
                                perfil['densidad_evitar_media'] / 1e6
                            ]
                            colores1 = ['#2ecc71', '#e74c3c']
                            
                            ax1.bar(categorias_densidad, valores_densidad, color=colores1, alpha=0.7, edgecolor='black')
                            ax1.set_ylabel('Millones de Viajeros')
                            ax1.set_title('Densidad Turística Comparada (Solo Países)')
                            ax1.grid(axis='y', alpha=0.3)
                            
                            for i, v in enumerate(valores_densidad):
                                ax1.text(i, v + max(valores_densidad)*0.05, f'{v:.1f}M', ha='center', fontweight='bold')
                            
                            plt.tight_layout()
                            st.pyplot(fig1)
                            
                            # Gráfico 2: Presupuesto (segunda fila)
                            fig2, ax2 = plt.subplots(1, 1, figsize=(10, 4))
                            
                            categorias_presupuesto = ['Ideales', 'A Evitar']
                            valores_presupuesto = [
                                perfil['presupuesto_ideal_media'],
                                perfil['presupuesto_evitar_media']
                            ]
                            
                            ax2.bar(categorias_presupuesto, valores_presupuesto, color=colores1, alpha=0.7, edgecolor='black')
                            ax2.set_ylabel('USD por Turista')
                            ax2.set_title('Presupuesto Promedio Comparado (Solo Países)')
                            ax2.grid(axis='y', alpha=0.3)
                            
                            for i, v in enumerate(valores_presupuesto):
                                ax2.text(i, v + max(valores_presupuesto)*0.05, f'${v:,.0f}', ha='center', fontweight='bold')
                            
                            plt.tight_layout()
                            st.pyplot(fig2)
                            
                        except Exception as e:
                            st.error(f"Error al mostrar gráfico: {e}")
                    else:
                        st.info("📊 Selecciona destinos no-ideales para ver la comparativa completa")
                    
                    st.divider()
                    
                    # SECCIÓN 4: Explicación del Sistema
                    st.markdown("### 🔍 Cómo Funciona Tu Perfil")
                    
                    with st.expander("📚 Ver Explicación Detallada"):
                        st.markdown("""
                        **Tu perfil personalizado utiliza un sistema híbrido de similitud que combina:**
                        
                        1. **🔵 Similitud Coseno (50%)**
                           - Compara densidad turística, presupuesto e ingresos
                           - Encuentra destinos con patrones similares a tus favoritos
                        
                        2. **🟠 Similitud Euclidiana (30%)**
                           - Prioriza compatibilidad en presupuesto
                           - Penaliza diferencias muy grandes en costo/turista
                        
                        3. **🟡 Similitud Jaccard (20%)**
                           - Compara atributos categóricos (región, tipo)
                           - Evita destinos en regiones que rechazaste
                        
                        **Resultado:** Destinos ordenados por cuán similar son a tus preferencias (0-100%)
                        """)
                
                else:
                    st.info("👈 Primero, selecciona destinos ideales en la barra lateral y haz clic en '🎯 Generar Perfil Personalizado'")
            
            # TAB 4 DESHABILITADA POR AHORA - PRÓXIMA ITERACIÓN
            # with tab4:
            #     st.subheader("📈 Tendencias de Densidad Turística")
            #     st.write("Analiza la tendencia de llegadas y salidas de turistas en los últimos 10 años")

            #     if st.session_state.df_trend_historico is not None:
            #         df_pais_trend = st.session_state.df_trend_historico[
            #             st.session_state.df_trend_historico['country'] == pais_seleccionado
            #         ].sort_values('year').copy()
            #         
            #         if not df_pais_trend.empty:
            #             # Gráfico de líneas: Llegadas y Salidas
            #             st.subheader(f"Flujo Turístico - {pais_seleccionado}")
            #             
            #             # Preparar datos para el gráfico
            #             df_grafico = df_pais_trend[['year', 'tourism_arrivals', 'tourism_departures']].copy()
            #             df_grafico.columns = ['Año', 'Llegadas', 'Salidas']
            #             df_grafico.set_index('Año', inplace=True)
            #             
            #             st.line_chart(df_grafico)
            #             
            #             # Métricas de tendencia
            #             st.divider()
            #             st.subheader("📊 Métricas de Tendencia")
            #             
            #             llegadas_inicio = df_pais_trend['tourism_arrivals'].iloc[0]
            #             llegadas_final = df_pais_trend['tourism_arrivals'].iloc[-1]
            #             porcentaje_llegadas = ((llegadas_final - llegadas_inicio) / llegadas_inicio * 100) if llegadas_inicio > 0 else 0
            #             
            #             salidas_inicio = df_pais_trend['tourism_departures'].iloc[0]
            #             salidas_final = df_pais_trend['tourism_departures'].iloc[-1]
            #             porcentaje_salidas = ((salidas_final - salidas_inicio) / salidas_inicio * 100) if salidas_inicio > 0 else 0
            #             
            #             # Mostrar métricas en columnas
            #             met_col1, met_col2, met_col3 = st.columns(3)
            #             
            #             with met_col1:
            #                 st.metric(
            #                     "Cambio en Llegadas",
            #                     f"{porcentaje_llegadas:+.1f}%",
            #                     delta=f"{(llegadas_final - llegadas_inicio)/1e6:+.2f}M",
            #                     help=f"De {llegadas_inicio/1e6:.2f}M a {llegadas_final/1e6:.2f}M"
            #                 )
            #             
            #             with met_col2:
            #                 st.metric(
            #                     "Cambio en Salidas",
            #                     f"{porcentaje_salidas:+.1f}%",
            #                     delta=f"{(salidas_final - salidas_inicio)/1e6:+.2f}M",
            #                     help=f"De {salidas_inicio/1e6:.2f}M a {salidas_final/1e6:.2f}M"
            #                 )
            #             
            #             with met_col3:
            #                 # Densidad turística (interpretación)
            #                 densidad_valor = llegadas_final / 1e6
            #                 if densidad_valor > 100:
            #                     densidad_icon = "🔴"
            #                     densidad_nivel = "Muy Alta"
            #                 elif densidad_valor > 50:
            #                     densidad_icon = "🟠"
            #                     densidad_nivel = "Alta"
            #                 elif densidad_valor > 10:
            #                     densidad_icon = "🟡"
            #                     densidad_nivel = "Media"
            #                 else:
            #                     densidad_icon = "🟢"
            #                     densidad_nivel = "Baja"
            #                 
            #                 st.metric(
            #                     f"{densidad_icon} Densidad Turística",
            #                     densidad_nivel,
            #                     help=f"{densidad_valor:.2f}M de llegadas"
            #                 )
            #             
            #             # Tabla histórica detallada
            #             st.divider()
            #             st.subheader("📋 Datos Históricos Detallados")
            #             
            #             df_tabla = df_pais_trend[[
            #                 'year', 'tourism_arrivals', 'tourism_departures', 'tourism_receipts', 'gdp'
            #             ]].copy()
            #             
            #             df_tabla.columns = ['Año', 'Llegadas', 'Salidas', 'Recibos ($)', 'GDP ($)']
            #             
            #             st.dataframe(
            #                 df_tabla.style.format({
            #                     'Llegadas': '{:,.0f}',
            #                     'Salidas': '{:,.0f}',
            #                     'Recibos ($)': '{:,.0f}',
            #                     'GDP ($)': '{:,.0f}'
            #                 }),
            #                 use_container_width=True,
            #                 hide_index=True
            #             )
            #         else:
            #             st.warning(f"⚠️ No hay datos históricos disponibles para {pais_seleccionado}")
            #     else:
            #         st.error("❌ Los datos históricos no se cargaron correctamente")

if limpiar_btn:
    st.session_state.mostrar_recomendaciones = False
    st.rerun()

# Información adicional en la barra lateral
with st.sidebar:
    st.divider()
    st.markdown("### 📚 Sobre estos datos")
    st.info("""
    **Fuente:** World Bank Tourism & Economy Dataset (1999-2023)
    
    **Métricas utilizadas:**
    - Tourism Receipts: Ingresos por turismo internacional
    - Tourism Arrivals: Llegadas de turistas internacionales
    - GDP: Producto Interno Bruto
    - Inflation & Unemployment: Indicadores económicos
    
    **Objetivo:** Proporcionar recomendaciones basadas en datos históricos objetivos
    en lugar de opiniones subjetivas.
    """)

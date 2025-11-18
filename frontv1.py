import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
import requests
import time
import geonamescache

# --- Configuración de la Página ---
st.set_page_config(
    page_title="Recomendador Turístico",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inicializar session state para perfil de usuario
if 'paises_ideales' not in st.session_state:
    st.session_state.paises_ideales = []
if 'paises_no_ideales' not in st.session_state:
    st.session_state.paises_no_ideales = []
if 'perfil_generado' not in st.session_state:
    st.session_state.perfil_generado = False
if 'perfil_datos' not in st.session_state:
    st.session_state.perfil_datos = None

# --- Funciones de Carga de Datos ---

@st.cache_data
def load_precomputed_osm_data():
    """Carga los datos de OSM precalculados desde el archivo CSV."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "osm_cities_with_hotels.csv")
    try:
        df = pd.read_csv(csv_path)
        # Asegurarse de que los nombres de columna no tengan espacios extra
        df.columns = df.columns.str.strip()

        # --- TAREA 1: FILTRAR AGREGACIONES GLOBALES ---
        # Lista de agregaciones a excluir para que solo queden países.
        aggregations_to_exclude = [
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
        
        # Aplicar el filtro para excluir las agregaciones
        original_rows = len(df)
        df = df[~df['country'].isin(aggregations_to_exclude)]
        st.sidebar.caption(f"Limpiando datos: {original_rows - len(df)} agregaciones eliminadas.")
        
        return df
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo 'osm_cities_with_hotels.csv'.")
        st.warning("Por favor, ejecute el script 'precompute_osm_data.py' para generar este archivo.")
        return None
    except Exception as e:
        st.error(f"Error al leer el CSV de OSM: {e}")
        return None

@st.cache_data
def load_country_data():
    """Carga y preprocesa los datos económicos y turísticos a nivel de país."""
    try:
        # Carga de datos base
        df = pd.read_csv("world_tourism_economy_data.csv")
        df.columns = df.columns.str.strip()

        # Limpieza y manejo de nulos
        df.replace('..', np.nan, inplace=True)
        numeric_cols = [
            'tourism_receipts', 'tourism_arrivals', 'tourism_departures',
            'gdp', 'inflation', 'unemployment'
        ]
        for col in numeric_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        # Llenar nulos de forma básica (se puede mejorar)
        df['inflation'].fillna(df['inflation'].median(), inplace=True)
        df['unemployment'].fillna(df['unemployment'].median(), inplace=True)

        # --- LUGAR CORRECTO PARA FILTRAR AGREGACIONES GLOBALES ---
        aggregations_to_exclude = [
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
        
        # Aplicar el filtro para excluir las agregaciones
        original_rows = len(df)
        df = df[~df['country'].isin(aggregations_to_exclude)]
        
        # Usamos st.session_state para mostrar el mensaje solo una vez
        if 'agregaciones_eliminadas' not in st.session_state:
            st.session_state.agregaciones_eliminadas = original_rows - len(df)
            st.sidebar.caption(f"Limpiando datos: {st.session_state.agregaciones_eliminadas} agregaciones eliminadas.")

        # Feature Engineering: Crear métricas clave
        df_processed = df.sort_values(by=['country', 'year']).copy()
        df_processed['prev_year_arrivals'] = df_processed.groupby('country')['tourism_arrivals'].shift(1)
        df_processed['crecimiento_anual'] = (
            (df_processed['tourism_arrivals'] - df_processed['prev_year_arrivals']) /
            df_processed['prev_year_arrivals'] * 100
        ).fillna(0)

        df_processed['costo_por_turista'] = (
            df_processed['tourism_receipts'] / df_processed['tourism_arrivals']
        ).replace([np.inf, -np.inf], 0).fillna(0)

        # --- LÓGICA CORREGIDA ---
        # Seleccionar el último año POR PAÍS que tenga datos de turismo válidos.
        # Esto evita que se seleccionen años recientes sin datos, lo que vaciaba el dataframe.
        df_final = df_processed[
            (df_processed['tourism_arrivals'].notna()) | (df_processed['tourism_receipts'].notna())
        ].sort_values('year').groupby('country').tail(1).copy()
        
        # Eliminar países sin datos cruciales
        
        return df_final

    except FileNotFoundError:
        st.error("Error: No se encontró el archivo 'world_tourism_economy_data.csv'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al procesar los datos de países: {e}")
        return pd.DataFrame()

@st.cache_data
def get_processed_data():
    """
    Función principal para cargar los datos de países.
    """
    with st.spinner("Cargando datos de países..."):
        df_destinos = load_country_data()
    return df_destinos

@st.cache_data
def enriquecer_con_datos_osm(df_paises, df_ciudades):
    """
    Enriquece el DataFrame de países con métricas agregadas desde el DataFrame de ciudades.
    """
    if df_ciudades is None or df_ciudades.empty:
        st.warning("No se pudieron cargar los datos de ciudades de OSM. La recomendación se basará solo en datos económicos.")
        df_paises['total_hoteles_pais'] = 0
        df_paises['diversidad_ciudades_pais'] = 0
        return df_paises

    # 1. Calcular el total de hoteles por país
    total_hoteles = df_ciudades.groupby('country')['hotel_count'].sum().reset_index()
    total_hoteles.rename(columns={'hotel_count': 'total_hoteles_pais'}, inplace=True)

    # 2. Calcular la diversidad de ciudades (número de ciudades con hoteles)
    diversidad_ciudades = df_ciudades.groupby('country')['city'].nunique().reset_index()
    diversidad_ciudades.rename(columns={'city': 'diversidad_ciudades_pais'}, inplace=True)

    # Unir las nuevas métricas al DataFrame de países
    df_enriquecido = pd.merge(df_paises, total_hoteles, on='country', how='left')
    df_enriquecido = pd.merge(df_enriquecido, diversidad_ciudades, on='country', how='left')

    # Llenar con 0 los países que no tengan datos de hoteles
    df_enriquecido[['total_hoteles_pais', 'diversidad_ciudades_pais']] = df_enriquecido[['total_hoteles_pais', 'diversidad_ciudades_pais']].fillna(0)
    return df_enriquecido

# Carga los dos dataframes por separado
df_clasificado = get_processed_data()
df_osm_ciudades = load_precomputed_osm_data()

# Manejar el caso donde no hay datos válidos
if df_clasificado.empty or df_osm_ciudades is None:
    st.error("❌ No se pudieron cargar los datos necesarios. Verifica los archivos CSV.")
    st.stop()

# Enriquecer el dataframe principal con los datos de OSM
df_clasificado = enriquecer_con_datos_osm(df_clasificado, df_osm_ciudades)

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
regiones_disponibles = ['Todas'] + sorted(df_clasificado['country'].unique().tolist())
region = st.sidebar.selectbox(
    'Filtrar por región/país (opcional):',
    options=regiones_disponibles
)

# --- TAREA 1: AÑADIR EL TERMÓMETRO DE AMBIENTE TURÍSTICO ---
st.sidebar.divider()
st.sidebar.markdown("### 🌡️ Termómetro de Ambiente")
ambiente_turistico = st.sidebar.select_slider(
    '¿Qué tipo de ambiente prefieres en una ciudad?',
    options=['Refugio Tranquilo', 'Equilibrado', 'Centro Vibrante'],
    value='Equilibrado',
    help="Define si prefieres ciudades con más o menos infraestructura hotelera (un indicador de concurrencia)."
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
            
            # Pestañas para diferentes vistas de los resultados
            tab1, tab2, tab3 = st.tabs(["📍 Recomendaciones y Ciudades", "📊 Comparativa Detallada", " Mi Perfil"])
            
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
                        
                        # --- TAREA 3: INTEGRAR CIUDADES EN LA MISMA PESTAÑA ---
                        # --- TAREA 2: UNIFICAR LÓGICA CON LA RECOMENDACIÓN ---
                        with st.expander(f"🏨 Ver Ciudades con ambiente '{ambiente_turistico}' en este País"):
                            if df_osm_ciudades is not None:
                                ciudades_del_pais = df_osm_ciudades[df_osm_ciudades['country'] == row['country']].copy()
                                
                                if not ciudades_del_pais.empty:
                                    # Calcular cuantiles para definir los umbrales de densidad
                                    q1 = ciudades_del_pais['hotel_count'].quantile(0.33)
                                    q2 = ciudades_del_pais['hotel_count'].quantile(0.66)

                                    ciudades_filtradas = pd.DataFrame()
                                    titulo_seccion = ""

                                    if ambiente_turistico == 'Refugio Tranquilo':
                                        # Ciudades con menos hoteles que el primer tercio (o 1 si el cuantil es bajo)
                                        umbral = max(q1, 1)
                                        ciudades_filtradas = ciudades_del_pais[ciudades_del_pais['hotel_count'] <= umbral]
                                        titulo_seccion = f"Ciudades con ambiente de 'Refugio Tranquilo' en **{row['country']}**:"
                                        ciudades_filtradas = ciudades_filtradas.sort_values(by='hotel_count', ascending=True)

                                    elif ambiente_turistico == 'Equilibrado':
                                        # Ciudades en el rango intermedio
                                        ciudades_filtradas = ciudades_del_pais[
                                            (ciudades_del_pais['hotel_count'] > q1) & 
                                            (ciudades_del_pais['hotel_count'] <= q2)
                                        ]
                                        titulo_seccion = f"Ciudades con ambiente 'Equilibrado' en **{row['country']}**:"
                                        ciudades_filtradas = ciudades_filtradas.sort_values(by='hotel_count', ascending=False)

                                    elif ambiente_turistico == 'Centro Vibrante':
                                        # Ciudades en el tercio superior
                                        ciudades_filtradas = ciudades_del_pais[ciudades_del_pais['hotel_count'] > q2]
                                        titulo_seccion = f"Ciudades con ambiente de 'Centro Vibrante' en **{row['country']}**:"
                                        ciudades_filtradas = ciudades_filtradas.sort_values(by='hotel_count', ascending=False)

                                    st.write(titulo_seccion)
                                    st.dataframe(
                                        ciudades_filtradas[['city', 'hotel_count']].rename(columns={'city': 'Ciudad', 'hotel_count': 'Número de Hoteles'}),
                                        use_container_width=True,
                                        hide_index=True
                                    )
                                    if ciudades_filtradas.empty:
                                        st.caption(f"No se encontraron ciudades que coincidan con el criterio '{ambiente_turistico}' para este país.")
                                else:
                                    st.info(f"No se encontraron datos de ciudades para '{row['country']}' en el archivo precalculado.")

                        
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

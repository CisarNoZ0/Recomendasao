import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime
<<<<<<< Updated upstream

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
=======
import requests
import time
import geonamescache
# --- Funciones de Carga de Datos ---

@st.cache_data
def load_precomputed_osm_data():
    """Carga los datos de OSM precalculados desde el archivo CSV."""
>>>>>>> Stashed changes
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(script_dir, "osm_cities_with_hotels.csv")
    try:
        df = pd.read_csv(csv_path)
        # Asegurarse de que los nombres de columna no tengan espacios extra
        df.columns = df.columns.str.strip()
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

        # Seleccionar los datos más recientes por país
        df_final = df_processed.loc[df_processed.groupby('country')['year'].idxmax()]
        
        # Eliminar países sin datos cruciales
        df_final.dropna(subset=['tourism_arrivals', 'costo_por_turista'], inplace=True)
        
        return df_final

    except FileNotFoundError:
        st.error("Error: No se encontró el archivo 'world_tourism_economy_data.csv'.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Error al procesar los datos de países: {e}")
        return pd.DataFrame()

<<<<<<< Updated upstream

df_destinos = load_data()

# Manejar el caso donde no hay datos válidos
if df_destinos.empty:
    st.error("❌ No hay datos válidos disponibles. Verifica que el archivo CSV esté correcto.")
=======
@st.cache_data
def get_processed_data():
    """
    Función principal para cargar los datos de países.
    """
    with st.spinner("Cargando datos de países..."):
        df_destinos = load_country_data()
    return df_destinos

# Carga los dos dataframes por separado
df_clasificado = get_processed_data()
df_osm_ciudades = load_precomputed_osm_data()

# Manejar el caso donde no hay datos válidos
if df_clasificado.empty or df_osm_ciudades is None:
    st.error("❌ No se pudieron cargar los datos necesarios. Verifica los archivos CSV.")
>>>>>>> Stashed changes
    st.stop()

# --- Barra Lateral (Inputs del Usuario) ---
st.sidebar.header("✈️ Tu Perfil de Viajero")
st.sidebar.write("Define tus preferencias.")

# Calcular rangos dinámicos basados en datos reales
min_budget = float(df_destinos['costo_por_turista'].quantile(0.05))
max_budget = float(df_destinos['costo_por_turista'].quantile(0.95))
median_budget = float(df_destinos['costo_por_turista'].median())

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
regiones_disponibles = ['Todas'] + sorted(df_destinos['country'].unique().tolist())[:50]  # Top 50
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
    sorted(df_destinos['country'].unique().tolist()),
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
    sorted(df_destinos['country'].unique().tolist()),
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
            df_destinos,
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
    st.metric("Destinos Disponibles", len(df_destinos))

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
            df=df_destinos,
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
            tab1, tab2, tab3 = st.tabs(["📍 Recomendaciones", "📊 Comparativa", "👤 Mi Perfil"])
            
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
            
            with tab5:
                st.subheader("🏛️ Ciudades Populares en tus Destinos Recomendados")
                st.write("Explora las ciudades con más hoteles (según OpenStreetMap) dentro de los países que te recomendamos.")

                # Extraer la lista única de países recomendados
                paises_recomendados = recomendaciones['country'].unique()

                if len(paises_recomendados) > 0:
                    # Selector para que el usuario elija un país de la lista de recomendados
                    pais_seleccionado_ciudades = st.selectbox(
                        "Selecciona un país para explorar sus ciudades:",
                        options=paises_recomendados,
                        key="selector_ciudades_pais"
                    )

                    if pais_seleccionado_ciudades and df_osm_ciudades is not None:
                        # CORRECTO: Filtrar el dataframe de OSM (df_osm_ciudades)
                        ciudades_del_pais = df_osm_ciudades[df_osm_ciudades['Pais'] == pais_seleccionado_ciudades].copy()

                        if not ciudades_del_pais.empty:
                            # Opciones de ordenamiento
                            orden_ciudades = st.radio(
                                "Ordenar ciudades por:",
                                ["Mayor número de hoteles", "Menor número de hoteles"],
                                key="orden_hoteles",
                                horizontal=True
                            )

                            # Ordenar el dataframe de ciudades
                            ascending_order = (orden_ciudades == "Menor número de hoteles")
                            ciudades_ordenadas = ciudades_del_pais.sort_values(by='Hoteles', ascending=ascending_order)

                            st.write(f"Mostrando ciudades en **{pais_seleccionado_ciudades}**:")

                            # Mostrar las ciudades en un formato de tabla mejorado
                            st.dataframe(
                                ciudades_ordenadas[['Ciudad', 'Hoteles']].rename(columns={'Hoteles': 'Número de Hoteles'}),
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.info(f"No se encontraron datos de ciudades para '{pais_seleccionado_ciudades}' en el archivo precalculado.")
                else:
                    st.warning("Primero genera una recomendación para poder explorar las ciudades.")
            
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

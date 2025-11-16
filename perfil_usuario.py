# Funciones para Perfil de Usuario y Similitud de Destinos
# Este archivo contiene las funciones auxiliares para implementar el sistema de perfiles
# Se importará en frontv1.py una vez esté listo

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from scipy.spatial.distance import cosine, euclidean
from typing import Dict, List, Tuple

# ============================================================================
# SECCIÓN 1: EXTRACCIÓN DE PERFIL DE USUARIO
# ============================================================================

def extraer_perfil_usuario(df: pd.DataFrame, paises_ideales: List[str], paises_no_ideales: List[str]) -> Dict:
    """
    Extrae características del perfil basado en destinos visitados ideales vs no-ideales.
    
    Args:
        df: DataFrame con todos los países
        paises_ideales: Lista de países visitados favorablemente
        paises_no_ideales: Lista de países visitados desfavorablemente
    
    Returns:
        Dict con características del perfil:
        - densidad_ideal_media: promedio de turistas llegadas en ideales
        - presupuesto_ideal_media: promedio costo/turista en ideales
        - tipo_turismo_ideal: clasificación más frecuente
        - regiones_ideales: lista de regiones preferidas
        - vector_caracteristicas: array normalizado para similitud
    """
    
    # Filtrar agregaciones para evitar distorsiones en gráficos
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
    df_paises = df[mask].copy()
    
    perfil = {}
    
    # Filtrar datos de ideales
    if paises_ideales:
        df_ideales = df_paises[df_paises['country'].isin(paises_ideales)]
        perfil['densidad_ideal_media'] = df_ideales['tourism_arrivals'].mean()
        perfil['presupuesto_ideal_media'] = df_ideales['costo_por_turista'].mean()
        perfil['tipo_turismo_ideal'] = df_ideales['clasificacion_turismo'].mode()[0] if 'clasificacion_turismo' in df_ideales else "desconocido"
        perfil['regiones_ideales'] = df_ideales['region'].unique().tolist() if 'region' in df_ideales else []
        perfil['ingresos_ideales_media'] = df_ideales['tourism_receipts'].mean()
    else:
        perfil['densidad_ideal_media'] = df_paises['tourism_arrivals'].median()
        perfil['presupuesto_ideal_media'] = df_paises['costo_por_turista'].median()
        perfil['tipo_turismo_ideal'] = "equilibrado"
        perfil['regiones_ideales'] = []
        perfil['ingresos_ideales_media'] = df_paises['tourism_receipts'].median()
    
    # Filtrar datos de no-ideales (para saber qué EVITAR)
    if paises_no_ideales:
        df_no_ideales = df_paises[df_paises['country'].isin(paises_no_ideales)]
        perfil['densidad_evitar_media'] = df_no_ideales['tourism_arrivals'].mean()
        perfil['presupuesto_evitar_media'] = df_no_ideales['costo_por_turista'].mean()
        perfil['tipo_turismo_evitar'] = df_no_ideales['clasificacion_turismo'].mode()[0] if 'clasificacion_turismo' in df_no_ideales else "ninguno"
        perfil['regiones_evitar'] = df_no_ideales['region'].unique().tolist() if 'region' in df_no_ideales else []
    else:
        perfil['densidad_evitar_media'] = None
        perfil['presupuesto_evitar_media'] = None
        perfil['tipo_turismo_evitar'] = None
        perfil['regiones_evitar'] = []
    
    # Crear vector de características normalizado (para cálculos de similitud)
    perfil['vector_caracteristicas'] = {
        'densidad': perfil['densidad_ideal_media'],
        'presupuesto': perfil['presupuesto_ideal_media'],
        'ingresos': perfil['ingresos_ideales_media']
    }
    
    return perfil


# ============================================================================
# SECCIÓN 2: CÁLCULO DE SIMILITUD
# ============================================================================

def normalizar_caracteristicas(df: pd.DataFrame, caracteristicas: List[str]) -> pd.DataFrame:
    """
    Normaliza características usando Z-score (media=0, std=1).
    """
    df_norm = df.copy()
    scaler = StandardScaler()
    df_norm[caracteristicas] = scaler.fit_transform(df[caracteristicas])
    return df_norm


def similitud_coseno(perfil: Dict, destino: Dict) -> float:
    """
    Calcula similitud coseno entre perfil de usuario y destino.
    
    Args:
        perfil: Dict con vector_caracteristicas del usuario
        destino: Dict/Series con características del destino
    
    Returns:
        float [0,1]: similitud coseno normalizada
    """
    # Extraer vectores
    vector_perfil = np.array([
        perfil['vector_caracteristicas']['densidad'],
        perfil['vector_caracteristicas']['presupuesto'],
        perfil['vector_caracteristicas']['ingresos']
    ])
    
    vector_destino = np.array([
        destino.get('tourism_arrivals', 0),
        destino.get('costo_por_turista', 0),
        destino.get('tourism_receipts', 0)
    ])
    
    # Evitar división por cero
    if np.linalg.norm(vector_perfil) == 0 or np.linalg.norm(vector_destino) == 0:
        return 0.0
    
    # Coseno retorna [0,1]
    return 1 - cosine(vector_perfil, vector_destino)


def similitud_euclidiana_normalizada(perfil: Dict, destino: Dict) -> float:
    """
    Calcula similitud Euclidiana normalizada (0=muy diferente, 1=igual).
    """
    vector_perfil = np.array([
        perfil['vector_caracteristicas']['presupuesto'],
    ])
    
    vector_destino = np.array([
        destino.get('costo_por_turista', 0),
    ])
    
    # Calcular distancia euclidiana
    dist = euclidean(vector_perfil, vector_destino)
    
    # Normalizar a [0,1]: exp(-dist) converge a 0 conforme dist crece
    similitud = np.exp(-dist / 1000)  # Escala: 1000 es la "unidad de diferencia"
    return similitud


def similitud_jaccard_categorica(perfil: Dict, destino: Dict) -> float:
    """
    Similitud Jaccard para atributos categóricos (región, tipo turismo).
    """
    score = 0.0
    total_criterios = 0
    
    # Criterio 1: Región (si coincide +0.5, si es cercana +0.25)
    if perfil['regiones_ideales']:
        total_criterios += 0.5
        region_destino = destino.get('region', '')
        if region_destino in perfil['regiones_ideales']:
            score += 0.5
        elif region_destino not in perfil['regiones_evitar']:
            score += 0.25
    
    # Criterio 2: Evitar regiones no-ideales
    if perfil['regiones_evitar']:
        total_criterios += 0.5
        region_destino = destino.get('region', '')
        if region_destino not in perfil['regiones_evitar']:
            score += 0.5
    
    # Evitar división por cero
    if total_criterios == 0:
        return 0.5  # Neutral si no hay criterios categóricos
    
    return score / total_criterios


def similitud_hibrida(perfil: Dict, destino: Dict, 
                      pesos: Dict = None) -> float:
    """
    Combina múltiples métricas de similitud con pesos ponderados.
    
    Args:
        perfil: Dict con información del perfil de usuario
        destino: Dict/Series con características del destino
        pesos: Dict con 'coseno', 'euclidiana', 'jaccard' (por defecto 0.5, 0.3, 0.2)
    
    Returns:
        float [0,1]: similitud final ponderada
    """
    if pesos is None:
        pesos = {'coseno': 0.5, 'euclidiana': 0.3, 'jaccard': 0.2}
    
    # Calcular cada componente
    sim_cos = similitud_coseno(perfil, destino)
    sim_euc = similitud_euclidiana_normalizada(perfil, destino)
    sim_jac = similitud_jaccard_categorica(perfil, destino)
    
    # Ponderar
    similitud_final = (
        pesos['coseno'] * sim_cos +
        pesos['euclidiana'] * sim_euc +
        pesos['jaccard'] * sim_jac
    )
    
    return min(1.0, max(0.0, similitud_final))  # Clamp [0,1]


def calcular_similitud_para_todos(df: pd.DataFrame, perfil: Dict) -> pd.Series:
    """
    Calcula similitud para cada país en el DataFrame.
    
    Returns:
        Series con similitud [0,1] para cada país
    """
    similitudes = df.apply(
        lambda row: similitud_hibrida(perfil, row),
        axis=1
    )
    return similitudes


# ============================================================================
# SECCIÓN 3: SEGMENTACIÓN POR PRESUPUESTO
# ============================================================================

def segmentar_por_presupuesto(df: pd.DataFrame, 
                             bandas: List[Tuple] = None) -> Dict[str, pd.DataFrame]:
    """
    Segmenta recomendaciones por bandas de presupuesto.
    
    Args:
        df: DataFrame con recomendaciones
        bandas: List de tuplas (min, max, etiqueta). Por defecto:
                [(0, 1000, 'Presupuesto Bajo'),
                 (1000, 3000, 'Presupuesto Medio'),
                 (3000, 5000, 'Presupuesto Alto'),
                 (5000, float('inf'), 'Lujo')]
    
    Returns:
        Dict {'etiqueta': DataFrame_filtrado, ...}
    """
    if bandas is None:
        bandas = [
            (0, 1000, 'Presupuesto Bajo'),
            (1000, 3000, 'Presupuesto Medio'),
            (3000, 5000, 'Presupuesto Alto'),
            (5000, float('inf'), 'Presupuesto Lujo')
        ]
    
    segmentacion = {}
    for min_val, max_val, etiqueta in bandas:
        df_banda = df[(df['costo_por_turista'] >= min_val) & 
                      (df['costo_por_turista'] < max_val)].copy()
        if not df_banda.empty:
            segmentacion[etiqueta] = df_banda.sort_values('similitud_score', ascending=False)
    
    return segmentacion


# ============================================================================
# SECCIÓN 4: UTILIDADES PARA VISUALIZACIÓN
# ============================================================================

def generar_resumen_perfil(perfil: Dict) -> str:
    """
    Genera un resumen textual del perfil para mostrar en la UI.
    """
    resumen = f"""
    📊 **Perfil Extraído:**
    
    **Destinos Ideales:**
    - Densidad promedio: {perfil['densidad_ideal_media']/1e6:.2f}M viajeros
    - Costo promedio: ${perfil['presupuesto_ideal_media']:,.0f}/turista
    - Tipo preferido: {perfil['tipo_turismo_ideal']}
    - Regiones: {', '.join(perfil['regiones_ideales']) if perfil['regiones_ideales'] else 'Todas'}
    
    **Destinos a Evitar:**
    - Tipo a evitar: {perfil['tipo_turismo_evitar']}
    - Regiones: {', '.join(perfil['regiones_evitar']) if perfil['regiones_evitar'] else 'Ninguna'}
    """
    return resumen


def categorizar_densidad(llegadas: float) -> Tuple[str, str]:
    """
    Categoriza densidad turística con emoji y etiqueta.
    
    Returns:
        Tupla (emoji, etiqueta)
    """
    if llegadas > 100e6:
        return ("🔴", "Muy Alta")
    elif llegadas > 50e6:
        return ("🟠", "Alta")
    elif llegadas > 10e6:
        return ("🟡", "Media")
    else:
        return ("🟢", "Baja")

import pandas as pd
import numpy as np
import os

script_dir = os.getcwd()
csv_path = os.path.join(script_dir, "world_tourism_economy_data.csv")

df = pd.read_csv(csv_path)
print(f"CSV cargado: {len(df)} filas, {len(df.columns)} columnas")

# Filtrar agregaciones
aggregations = ['World', 'High income', 'Low income', 'Middle income', 'OECD', 
               'Europe', 'Asia', 'Africa', 'Latin America', 'Caribbean',
               'Post-demographic', 'Fragile', 'Africa Eastern', 'Africa Western',
               'Arab World', 'Pacific island', 'Heavily indebted',
               'Early-demographic', 'Late-demographic', 'dividend']

mask = ~df['country'].str.contains('|'.join(aggregations), case=False, na=False)
df = df[mask].copy()
print(f"Despues de filtrar agregaciones: {len(df)} filas")

# Tomar último año por país
df_latest = df.sort_values('year').groupby('country').tail(1).copy()
print(f"Datos mas recientes por pais: {len(df_latest)} filas")

# Calcular costo por turista
df_latest['costo_por_turista'] = np.where(
    (df_latest['tourism_receipts'].notna()) & (df_latest['tourism_arrivals'].notna()),
    df_latest['tourism_receipts'] / df_latest['tourism_arrivals'],
    np.nan
)

# Tendencia
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

# Filtrar países con al menos un dato de turismo
df_latest = df_latest[(df_latest['tourism_receipts'].notna()) | (df_latest['tourism_arrivals'].notna())].copy()

# Llenar valores faltantes
df_latest['costo_por_turista'] = df_latest['costo_por_turista'].fillna(df_latest['costo_por_turista'].median())
df_latest['tourism_arrivals'] = df_latest['tourism_arrivals'].fillna(0)
df_latest['tourism_receipts'] = df_latest['tourism_receipts'].fillna(0)

print(f"\nDatos finales: {len(df_latest)} paises")
print(f"¿Vacío? {df_latest.empty}")
print(f"\nTop 10 por costo/turista:")
print(df_latest.nlargest(10, 'costo_por_turista')[['country', 'costo_por_turista', 'tourism_arrivals', 'crecimiento_anual']])

print(f"\nEstadísticas:")
print(f"  Costo/Turista - Min: ${df_latest['costo_por_turista'].min():,.0f}, Max: ${df_latest['costo_por_turista'].max():,.0f}, Median: ${df_latest['costo_por_turista'].median():,.0f}")
print(f"  Llegadas - Min: {df_latest['tourism_arrivals'].min():,.0f}, Max: {df_latest['tourism_arrivals'].max():,.0f}")
print(f"  Crecimiento - Min: {df_latest['crecimiento_anual'].min():.1f}%, Max: {df_latest['crecimiento_anual'].max():.1f}%")

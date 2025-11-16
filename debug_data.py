import pandas as pd
import os

script_dir = os.getcwd()
csv_path = os.path.join(script_dir, 'world_tourism_economy_data.csv')

print(f'CSV Path: {csv_path}')
print(f'Archivo existe: {os.path.exists(csv_path)}')

df = pd.read_csv(csv_path)
print(f'\nDatos cargados: {len(df)} filas')

aggregations = ['World', 'High income', 'Low income', 'Middle income', 'OECD', 'Europe', 'Asia', 'Africa', 'Latin America', 'Caribbean', 'Post-demographic', 'Fragile', 'Africa Eastern', 'Africa Western', 'Arab World', 'Pacific island', 'Heavily indebted', 'Early-demographic', 'Late-demographic', 'dividend']

mask = ~df['country'].str.contains('|'.join(aggregations), case=False, na=False)
df_filtered = df[mask].copy()
print(f'Despues de filtrar agregaciones: {len(df_filtered)} filas')

df_latest = df_filtered.sort_values('year').groupby('country').tail(1).copy()
print(f'Despues de agrupar por pais: {len(df_latest)} filas')

df_latest['costo_por_turista'] = df_latest['tourism_receipts'] / df_latest['tourism_arrivals']

print(f'\nAntes de dropar NaN:')
print(f'  tourism_receipts no-null: {df_latest["tourism_receipts"].notna().sum()}')
print(f'  tourism_arrivals no-null: {df_latest["tourism_arrivals"].notna().sum()}')
print(f'  costo_por_turista no-null: {df_latest["costo_por_turista"].notna().sum()}')

print(f"\nPrimeras filas con datos:")
valid_rows = df_latest[(df_latest['tourism_receipts'].notna()) & (df_latest['tourism_arrivals'].notna())]
print(valid_rows[['country', 'tourism_receipts', 'tourism_arrivals', 'costo_por_turista']].head(10))

df_final = df_latest.dropna(subset=['tourism_receipts', 'tourism_arrivals', 'costo_por_turista'])
print(f'\nDespues de dropar NaN: {len(df_final)} filas')
print(f'¿DataFrame vacio? {df_final.empty}')

if not df_final.empty:
    print(f'\nEstadisticas de costo_por_turista:')
    print(df_final['costo_por_turista'].describe())

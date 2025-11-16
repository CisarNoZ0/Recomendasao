import pandas as pd
import numpy as np
import os

csv_path = os.path.join(os.getcwd(), "world_tourism_economy_data.csv")
df = pd.read_csv(csv_path)

print(f"CSV cargado: {len(df)} filas")
print(f"\nNulos por columna:")
print(df.isnull().sum())

print(f"\n\nÚltimo año disponible: {df['year'].max()}")
print(f"Años únicos: {sorted(df['year'].unique())[-10:]}")

aggregations = ['World', 'High income', 'Low income', 'Middle income', 'OECD', 
               'Europe', 'Asia', 'Africa', 'Latin America', 'Caribbean',
               'Post-demographic', 'Fragile', 'Africa Eastern', 'Africa Western',
               'Arab World', 'Pacific island', 'Heavily indebted',
               'Early-demographic', 'Late-demographic', 'dividend']

mask = ~df['country'].str.contains('|'.join(aggregations), case=False, na=False)
df = df[mask].copy()

df_latest = df.sort_values('year').groupby('country').tail(1).copy()
print(f"\n\nÚltimos registros por país: {len(df_latest)}")
print(f"Nulls en df_latest:")
print(df_latest[['tourism_receipts', 'tourism_arrivals']].isnull().sum())

print(f"\nRegistros con tourism_receipts no-null: {df_latest['tourism_receipts'].notna().sum()}")
print(f"Registros con tourism_arrivals no-null: {df_latest['tourism_arrivals'].notna().sum()}")

print(f"\nPrimeros 10 paises:")
print(df_latest[['country', 'year', 'tourism_receipts', 'tourism_arrivals']].head(10))

print(f"\nÚltimos 10 países:")
print(df_latest[['country', 'year', 'tourism_receipts', 'tourism_arrivals']].tail(10))

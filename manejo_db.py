import pandas as pd
import io
import os

# --- Ruta de tu archivo CSV ---
script_dir = os.path.dirname(os.path.abspath(__file__))
csv_data = os.path.join(script_dir, "world_tourism_economy_data.csv")
# --------------------------------------

try:
    # Usamos io.StringIO para leer el string de texto como si fuera un archivo
    # (Esto es solo para la simulación. Para un archivo real, usa: pd.read_csv("tu_archivo.csv"))
    df = pd.read_csv(csv_data)

    print("--- Análisis Básico del Archivo CSV ---")
    print("\n")

    # 1. Mostrar las primeras filas del DataFrame
    print("1. Primeras 5 filas de datos (.head()):")
    print(df.head())
    print("-" * 40)

    # 2. Obtener información general (tipos de datos, nulos)
    print("\n2. Información general y tipos de datos (.info()):")
    # Redirigimos la salida de .info() para poder imprimirla
    buffer = io.StringIO()
    df.info(buf=buffer)
    print(buffer.getvalue())
    print("-" * 40)

    # 3. Obtener estadísticas descriptivas para columnas numéricas
    print("\n3. Estadísticas descriptivas (.describe()):")
    # .describe() funciona automáticamente en todas las columnas numéricas
    print(df.describe())
    print("-" * 40)

    # 4. Análisis Específico (Ejemplos basados en tus columnas)
    print("\n4. Análisis Específico (basado en tus columnas):")
    
    # Calcular recibos de turismo promedio
    # Usamos :.2f para formatear a 2 decimales y , para separador de miles
    recibos_promedio = df['tourism_receipts'].mean()
    print(f"  - Recibos de turismo promedio (todos los países/años): {recibos_promedio:,.2f}")

    # Calcular recibos promedio por país (agrupando por si hay varios años)
    recibos_por_pais = df.groupby('country')['tourism_receipts'].mean().sort_values(ascending=False)
    print("\n  - Recibos de turismo promedio por país:")
    print(recibos_por_pais)

    # Encontrar el país con el GDP más alto en el dataset
    # (Nota: 'gdp' en el ejemplo parece estar en distintas escalas, ej 1.4 vs 25.0, ¡ten cuidado!)
    print("\n  - Países ordenados por GDP (solo como ejemplo):")
    print(df.sort_values('gdp', ascending=False)[['country', 'year', 'gdp']])
    
    # Calcular tasa de desempleo promedio
    desempleo_promedio = df['unemployment'].mean()
    print(f"\n  - Tasa de desempleo promedio: {desempleo_promedio:.2f}%")

except FileNotFoundError:
    print("Error: No se encontró el archivo CSV. Asegúrate de que esté en la misma carpeta.")
except KeyError as e:
    # Este error es útil si el nombre de una columna cambia
    print(f"Error de columna: No se encontró la columna {e}. Revisa los encabezados del CSV.")
except Exception as e:
    print(f"Ocurrió un error al procesar el archivo: {e}")
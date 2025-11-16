import pandas as pd
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(script_dir, "world_tourism_economy_data.csv")

df = pd.read_csv(csv_path)
print("=" * 80)
print(f"Total rows in CSV: {len(df)}")
print(f"Total unique countries: {df['country'].nunique()}")
print("=" * 80)

# Current aggregations list from frontv1.py (UPDATED - EXACT MATCH)
current_aggregations = [
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

print("\n✓ CURRENT AGGREGATIONS TO FILTER (EXACT MATCH):")
print("-" * 80)
for agg in current_aggregations:
    if agg in df['country'].values:
        print(f"  ✓ '{agg}'")
    else:
        print(f"  ✗ '{agg}' NOT FOUND")

# Apply current filter
mask = ~df['country'].isin(current_aggregations)
df_filtered = df[mask].copy()
print(f"\n✓ AFTER FILTERING: {len(df_filtered)} rows left from {len(df)}")
print(f"✓ Unique countries after filtering: {df_filtered['country'].nunique()}")

# Get latest data per country and check for remaining aggregations
df_latest = df_filtered[
    (df_filtered['tourism_receipts'].notna()) | (df_filtered['tourism_arrivals'].notna())
].sort_values(['country', 'year']).groupby('country').tail(1).copy()

print(f"\n✓ LATEST DATA PER COUNTRY: {len(df_latest)} records")
print("\nAll countries in latest data:")
print(sorted(df_latest['country'].unique().tolist()))

# Look for suspicious entries that look like aggregations
print("\n⚠️  CHECKING FOR POTENTIAL REMAINING AGGREGATIONS:")
print("-" * 80)
suspicious_keywords = ['world', 'total', 'income', 'demographic', 'oecd', 'island', 'region', 
                       'europe', 'asia', 'africa', 'america', 'caribbean', 'arab', 'fragile',
                       'heavily', 'dividend', 'ida', 'post', 'early', 'late']

for country in sorted(df_latest['country'].unique()):
    country_lower = country.lower()
    for keyword in suspicious_keywords:
        if keyword in country_lower:
            print(f"  ⚠️  '{country}' contains '{keyword}'")
            break

# 🌍 Sistema de Recomendación Turística - Mejoras Implementadas

## 📋 Resumen de Cambios

Se ha transformado `frontv1.py` de una aplicación con datos mockup a un **sistema de recomendación de viajes basado en datos históricos objetivos** (1999-2023) utilizando el dataset `world_tourism_economy_data.csv` del Banco Mundial.

---

## 🎯 Objetivos Logrados

✅ **Datos Históricos Reales**: Carga y procesa automáticamente datos del CSV  
✅ **Filtros Objetivos**: Basados en métricas económicas y turísticas, no en opiniones  
✅ **Motor de Recomendación Mejorado**: Combina múltiples criterios de forma inteligente  
✅ **UI Moderna**: Interfaz Streamlit mejorada con visualizaciones de datos  
✅ **Transparencia**: Explica el "por qué" de cada recomendación  

---

## 🔧 Cambios Técnicos

### 1. **Carga de Datos**
```python
# Antes: Datos mockup hardcodeados
data = {
    'Destino': ['París', 'Kioto', ...],
    'Tipo': ['Cultural', 'Cultural', ...],
    ...
}

# Después: Carga dinámica del CSV real
df = pd.read_csv("world_tourism_economy_data.csv")
# + Limpieza de agregaciones (World, High income, etc.)
# + Cálculo de métricas derivadas (costo/turista, crecimiento anual)
```

### 2. **Filtros Rediseñados**

**Antes:**
- Presupuesto (fijo: 500-5000 USD)
- Temporada (Primavera/Verano/Otoño/Invierno)
- Tipo de viaje (Cultural/Natural/etc.)

**Después:**
- **Presupuesto** (dinámico: basado en datos reales, 5º-95º percentil)
- **Preferencia Turística** (3 opciones):
  - 🔍 Joyas ocultas (pocas llegadas, alto crecimiento)
  - 📈 Emergentes (destinos en crecimiento)
  - 🌟 Populares (muchas llegadas)
- **Salud Económica** (3 opciones):
  - 💪 Estable (baja inflación/desempleo)
  - 🚀 En crecimiento (alta demanda turística)
  - 🔄 Flexible (cualquiera)
- **Región** (filtro opcional por país)

### 3. **Motor de Recomendación**

**Algoritmo de Scoring:**

```
Score Final = (Score Turismo × 0.6) + (Score Económica × 0.4)

Score Turismo:
  - Joyas ocultas: (1 - normalizado_llegadas) + crecimiento_anual
  - Emergentes: crecimiento_anual
  - Populares: llegadas_normalizadas

Score Económica:
  - Estable: promedio(1 - inflación_norm, 1 - desempleo_norm)
  - En crecimiento: crecimiento_anual
  - Flexible: 0.5 (neutral)
```

### 4. **Métricas Disponibles**

| Métrica | Fuente | Cálculo | Uso |
|---------|--------|---------|-----|
| Costo/Turista | tourism_receipts ÷ tourism_arrivals | Manual | Filtro presupuesto |
| Crecimiento Anual | Cambio año a año | (Actual - Anterior) / Anterior | Score turismo |
| Llegadas | tourism_arrivals | Directo | Popularidad |
| Ingresos | tourism_receipts | Directo | Salud turística |
| GDP | gdp | Directo | Economía |
| Inflación | inflation | Directo | Estabilidad |
| Desempleo | unemployment | Directo | Estabilidad |

---

## 📊 UI/UX Mejorada

### Dashboard Principal
- Visualización de filtros seleccionados
- Contador de destinos disponibles
- Botones de acción (Generar/Limpiar)

### Resultados en Dos Vistas

**📍 Vista de Recomendaciones:**
- Ranking (#1, #2, etc.)
- 4 métricas principales por destino
- 3 métricas económicas adicionales
- Información contextual (ingresos, año datos, código país)

**📊 Vista Comparativa:**
- Tabla interactiva con todos los destinos
- Formato numérico consistente
- Sorteable y exportable

### Información Contextual
- Pestaña de información sobre fuentes de datos
- Ayuda integrada en cada filtro
- Explicación transparente de cálculos

---

## 🚀 Cómo Usar

### Instalación

```bash
# 1. Instalar dependencias
pip install streamlit pandas numpy

# 2. Navegar al directorio del proyecto
cd c:\Users\cesar\OneDrive\Documentos\GitHub\Recomendasao

# 3. Ejecutar la app
streamlit run frontv1.py
```

### Uso de la App

1. **Ajusta los filtros en la barra lateral:**
   - Define tu presupuesto máximo
   - Selecciona el tipo de destino que buscas
   - Elige el criterio de salud económica
   - (Opcional) Filtra por región específica

2. **Haz clic en "🔍 Generar Recomendaciones"**
   - El sistema analiza todos los datos históricos
   - Calcula scores basados en tus preferencias
   - Devuelve los 10 mejores destinos

3. **Explora los resultados:**
   - Revisa las recomendaciones en tarjetas detalladas
   - Compara países en la tabla interactiva
   - Copia datos si necesitas exportar

---

## 📈 Ejemplos de Caso de Uso

### Caso 1: Viajero con presupuesto limitado que busca joyas ocultas
```
Presupuesto: $1,000
Preferencia: Joyas ocultas (pocas llegadas)
Economía: Flexible
Resultado: Destinos emergentes, accesibles y con potencial de crecimiento
```

### Caso 2: Turista aventurero que busca destinos en expansión
```
Presupuesto: $3,000
Preferencia: Emergentes (crecimiento)
Economía: En crecimiento
Resultado: Países con crecimiento turístico acelerado
```

### Caso 3: Viajero que busca destinos económicamente estables
```
Presupuesto: $5,000
Preferencia: Populares (muchas llegadas)
Economía: Estable (baja inflación/desempleo)
Resultado: Destinos consolidados y económicamente seguros
```

---

## 🔍 Limitaciones y Futuros Mejores

### Limitaciones Actuales
- Datos agregados anualmente (sin granularidad mensual)
- Algunos países tienen datos incompletos
- Las métricas económicas pueden no estar disponibles para todos los años
- No incluye costos de vuelos (solo costos locales por turista)

### Mejoras Futuras
- [ ] Integración de datos de vuelos y hospedaje
- [ ] Predicción de tendencias futuras (ML)
- [ ] Segmentación por tipo de viajero (mochilero, lujo, familia)
- [ ] Filtro por estación/mes específico
- [ ] Visualización de series temporales por destino
- [ ] Integración de reviews y experiencias de viajeros
- [ ] API para recomendaciones vía endpoints
- [ ] Sistema de favoritos y seguimiento de precios

---

## 📊 Estadísticas del Dataset

- **Período:** 1999-2023 (25 años)
- **Países:** 266 (incluye algunas agregaciones)
- **Países únicos válidos:** ~180 (después de limpieza)
- **Total registros:** 6,650
- **Cobertura de datos:**
  - Tourism Receipts: 64.5%
  - Tourism Arrivals: 74.5%
  - GDP: 96.6%
  - Inflation: 85.3%
  - Unemployment: 55.0%

---

## 🔧 Estructura de Código

```
frontv1.py
├── load_data()              # Carga y limpia datos CSV
├── generar_recomendaciones() # Motor de scoring
├── Sidebar (Inputs)         # Filtros de usuario
├── Main UI                  # Dashboard
│   ├── Métricas resumen
│   ├── Tab 1: Recomendaciones
│   └── Tab 2: Comparativa
└── Información contextual
```

---

## 📝 Notas de Desarrollo

- La app usa `@st.cache_data` para optimizar la carga de datos
- Los scores se normalizan a escala 0-1 para comparabilidad
- Los valores NaN se manejan automáticamente
- Las recomendaciones se ordenan por score descendente
- Se devuelven máximo 10 destinos para evitar sobrecarga

---

## 👤 Autor

Desarrollado como parte del Proyecto de Recomendación Turística basado en datos objetivos (Proyecto Finis Terrae)

---

## 📚 Fuentes de Datos

- **World Bank Tourism & Economy Dataset**
- Variables: Tourism Receipts, Tourism Arrivals, GDP, Inflation, Unemployment
- Acceso: Dataset público del Banco Mundial
- Archivo: `world_tourism_economy_data.csv`

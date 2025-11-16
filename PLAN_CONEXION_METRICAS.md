# 📋 PLAN DE CONEXIÓN COMPLETA DEL SISTEMA DE MÉTRICAS

## 🎯 Estado Actual vs. Meta

### ✅ YA INTEGRADO:
1. **Extracción de Perfil** → Funciona correctamente
   - Usuario selecciona destinos ideales/no-ideales
   - Se calcula vector de características
   - Se guarda en `st.session_state.perfil_datos`

2. **Cálculo de Similitud** → Funciona correctamente
   - Se aplica métrica híbrida (50% Coseno + 30% Euclidiana + 20% Jaccard)
   - Se reordenan recomendaciones por similitud
   - Se muestra barra visual de similitud en Tab 1

### ❌ PENDIENTE DE INTEGRACIÓN:

#### **CAMBIO 1: Crear Nueva Tab "👤 Mi Perfil"**
**Ubicación:** frontv1.py, línea ~331 (Tab 2 Comparativa)

**Contenido de la Tab:**
```
┌─────────────────────────────────────────────┐
│ 👤 Tu Perfil Personalizado                 │
├─────────────────────────────────────────────┤
│                                             │
│ ✅ DESTINOS IDEALES (2 columnas)           │
│ ├─ Tailandia                               │
│ ├─ Vietnam                                 │
│                                             │
│ ❌ DESTINOS NO-IDEALES (2 columnas)        │
│ ├─ Dubai                                   │
│                                             │
│ ─────────────────────────────────────────   │
│                                             │
│ 📊 CARACTERÍSTICAS EXTRAÍDAS (3 métricas)  │
│ ├─ Densidad Ideal: 15.5M viajeros         │
│ ├─ Presupuesto Ideal: $850/turista        │
│ ├─ Tipo Preferido: Emergentes             │
│                                             │
│ ─────────────────────────────────────────   │
│                                             │
│ 📈 GRÁFICO: Comparativa Ideales vs. Evitar│
│    (Bar chart: Densidad, Presupuesto)     │
│                                             │
└─────────────────────────────────────────────┘
```

**Código necesario:**
- Mostrar listas de destinos seleccionados (ideales/no-ideales)
- Mostrar 3 métricas principales en tarjetas (Densidad, Presupuesto, Tipo)
- Gráfico bar chart comparativo (matplotlib/plotly)
- Mensajes condicionales si no hay perfil

---

#### **CAMBIO 2: Crear Nueva Tab "💰 Por Presupuesto"**
**Ubicación:** frontv1.py, línea ~331 (Tab 3 nueva)

**Contenido de la Tab:**
```
┌──────────────────────────────────────┐
│ 💰 Recomendaciones por Presupuesto  │
├──────────────────────────────────────┤
│                                      │
│ 🟢 PRESUPUESTO BAJO ($0 - $1,000)  │
│ ├─ 5 países disponibles            │
│ ├─ Costo Promedio: $650/turista    │
│ ├─ Score Promedio: 0.65            │
│ └─ [Tabla expandible ↓]            │
│    ├─ País 1 | $500 | ...         │
│    ├─ País 2 | $750 | ...         │
│                                      │
│ 🟡 PRESUPUESTO MEDIO ($1k - $3k)   │
│ ├─ 12 países disponibles           │
│ ├─ Costo Promedio: $1,850/turista  │
│ ├─ Score Promedio: 0.72            │
│ └─ [Tabla expandible ↓]            │
│                                      │
│ 🟠 PRESUPUESTO ALTO ($3k - $5k)    │
│ ├─ 8 países disponibles            │
│ ├─ Costo Promedio: $4,200/turista  │
│ ├─ Score Promedio: 0.78            │
│ └─ [Tabla expandible ↓]            │
│                                      │
│ 🔴 PRESUPUESTO LUJO (>$5k)         │
│ ├─ 4 países disponibles            │
│ ├─ Costo Promedio: $7,500/turista  │
│ ├─ Score Promedio: 0.81            │
│ └─ [Tabla expandible ↓]            │
│                                      │
└──────────────────────────────────────┘
```

**Código necesario:**
- Llamar `segmentar_por_presupuesto(recomendaciones)`
- Crear acordeones (st.expander) por cada banda
- En cada acordeón: métricas + tabla de destinos
- Si perfil activo: mostrar similitud en tabla
- Ordenar por similitud dentro de cada banda

---

#### **CAMBIO 3: Mejorar Lógica de Reordenación en Tab 1**
**Ubicación:** frontv1.py, líneas ~310-320

**Cambios necesarios:**
1. Si perfil está activo: ordenar PRIMERO por similitud
2. Si perfil NO está activo: ordenar por score_final (comportamiento actual)
3. Guardar `recomendaciones` en `st.session_state` para reutilizar en otras tabs

**Código actual (FUNCIONA):**
```python
recomendaciones = recomendaciones.sort_values(
    by=['similitud_score', 'score_final'],
    ascending=[False, False]
)
```

**Mejora sugerida:**
```python
# Guardar en session_state para otras tabs
st.session_state.recomendaciones_final = recomendaciones.copy()

# Mostrar estado
if st.session_state.perfil_generado:
    st.info("Ordenadas por: 1️⃣ Similitud Personal | 2️⃣ Score Económico")
else:
    st.info("Ordenadas por: Score Económico")
```

---

#### **CAMBIO 4: Agregar Información de Métricas en Sidebar**
**Ubicación:** frontv1.py, línea ~191 (después de mostrar estado del perfil)

**Contenido:**
```
Si perfil está generado:
┌────────────────────────────────┐
│ 📊 Resumen de Tu Perfil       │
├────────────────────────────────┤
│                                │
│ Destinos Favoritos: 2         │
│ Densidad Promedio: 15.5M      │
│ Presupuesto Promedio: $850    │
│                                │
│ 🔄 Tipo de Similitud:         │
│    🔵 Coseno (50%)            │
│    🟠 Euclidiana (30%)        │
│    🟡 Jaccard (20%)           │
│                                │
└────────────────────────────────┘
```

**Código necesario:**
```python
if st.session_state.perfil_generado and st.session_state.perfil_datos:
    perfil = st.session_state.perfil_datos
    
    with st.sidebar.expander("📊 Detalles del Perfil"):
        st.metric("Destinos Ideales", len(st.session_state.paises_ideales))
        st.metric("Destinos a Evitar", len(st.session_state.paises_no_ideales))
        st.metric("Densidad Media", f"{perfil['densidad_ideal_media']/1e6:.2f}M")
        st.metric("Presupuesto Medio", f"${perfil['presupuesto_ideal_media']:,.0f}")
        st.divider()
        st.caption("**Método de Similitud Híbrida:**")
        st.caption("🔵 Coseno 50% + 🟠 Euclidiana 30% + 🟡 Jaccard 20%")
```

---

## 📊 RESUMEN DE CAMBIOS

| Cambio | Archivo | Línea | Prioridad | Complejidad |
|--------|---------|-------|-----------|-------------|
| Tab "Mi Perfil" | frontv1.py | ~331 | 🔴 ALTA | 🟠 Media |
| Tab "Por Presupuesto" | frontv1.py | ~370 | 🔴 ALTA | 🟠 Media |
| Mejorar Reordenación | frontv1.py | ~310-320 | 🟠 Media | 🟢 Baja |
| Info Métricas Sidebar | frontv1.py | ~191 | 🟡 Baja | 🟢 Baja |

---

## 🔄 ORDEN DE IMPLEMENTACIÓN RECOMENDADO

### **Fase 1: Cambios Básicos**
1. ✅ Mejorar Reordenación (guardar en session_state)
2. ✅ Info Métricas en Sidebar

### **Fase 2: Nuevas Tabs**
3. ⏳ Crear Tab "Mi Perfil" (con gráfico)
4. ⏳ Crear Tab "Por Presupuesto" (con acordeones y tablas)

---

## 🎨 DEPENDENCIAS NUEVAS

Para los gráficos en Tab "Mi Perfil":
- ✅ matplotlib (ya está instalado)
- ⚠️ Verificar plotly (más atractivo, pero menos estable)

**Recomendación:** Usar matplotlib para gráficos simples, es más estable con Streamlit.

---

## ⚙️ FLUJO COMPLETO TRAS INTEGRACIÓN

```
USUARIO
  ↓
├─ Selecciona destinos ideales/no-ideales
  ↓
├─ Clic "Generar Perfil Personalizado"
  ├─ Se calcula vector de características
  ├─ Se muestra en SIDEBAR (Info Métricas) ← CAMBIO 4
  ↓
├─ Llena filtros (presupuesto, tipo, economía, región)
  ↓
├─ Clic "Generar Recomendaciones"
  ├─ Se calculan similitudes
  ├─ Se reordenan destinos
  ├─ Se guardan en session_state ← CAMBIO 3
  ↓
├─ VE TRES TABS:
  │
  ├─ Tab 1 "📍 Recomendaciones" (ACTUAL - mejora menor)
  │  ├─ Destinos ordenados por similitud ✅
  │  ├─ Barra de similitud por destino ✅
  │  └─ Mensaje de estado mejorado ← CAMBIO 3
  │
  ├─ Tab 2 "👤 Mi Perfil" (NUEVA) ← CAMBIO 1
  │  ├─ Destinos seleccionados
  │  ├─ Características extraídas
  │  └─ Gráfico comparativo
  │
  └─ Tab 3 "💰 Por Presupuesto" (NUEVA) ← CAMBIO 2
     ├─ Bandas presupuestarias en acordeones
     ├─ Métricas por banda
     └─ Tabla de destinos segmentados
```

---

## 💡 PREGUNTAS PARA TI

1. ¿Quieres agregar **todos estos cambios** o **solo algunos**?
2. ¿Prefieres **gráficos simples** (matplotlib) o **más interactivos** (plotly)?
3. ¿La **segmentación por presupuesto** debería incluir filtros dinámicos?
4. ¿Quieres que los **pesos de la similitud** sean ajustables por usuario?

---

## ✨ BENEFICIO FINAL

Después de estos cambios:
- ✅ Usuario COMPRENDE su perfil (Tab "Mi Perfil")
- ✅ Usuario VE recomendaciones personalizadas (Tab 1 mejorada)
- ✅ Usuario EXPLORA destinos por presupuesto (Tab "Por Presupuesto")
- ✅ Sistema EXPLICA cómo funciona (Métricas en sidebar)

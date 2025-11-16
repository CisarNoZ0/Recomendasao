# 📍 UBICACIÓN DE MÉTRICAS DE SIMILITUD EN EL CÓDIGO

## 🔴 ESTADO ACTUAL: Métricas Implementadas pero NO Integradas

Las métricas están **implementadas** en `perfil_usuario.py` pero **aún no conectadas** en `frontv1.py`

---

## 📁 ARCHIVO: `perfil_usuario.py` (291 líneas)

### 🟢 SECCIÓN 1: Extracción de Perfil (líneas 13-68)
**Función:** `extraer_perfil_usuario(df, paises_ideales, paises_no_ideales)`

- Calcula vector de características del usuario basado en destinos ideales
- Extrae: densidad media, presupuesto, tipo turismo, regiones
- Almacena vector normalizado para comparaciones
- **Ubicación:** Líneas 13-68

```python
perfil['vector_caracteristicas'] = {
    'densidad': perfil['densidad_ideal_media'],
    'presupuesto': perfil['presupuesto_ideal_media'],
    'ingresos': perfil['ingresos_ideales_media']
}
```

---

### 🟠 SECCIÓN 2: Métricas de Similitud (líneas 75-193)

#### **2.1 Similitud Coseno** (líneas 79-107)
**Función:** `similitud_coseno(perfil, destino) → float [0,1]`
- Compara vector de densidad, presupuesto, ingresos
- Captura relaciones multidimensionales
- **Ventaja:** Independiente de magnitud absoluta
- **Fórmula:** `1 - cosine_distance`

```python
def similitud_coseno(perfil: Dict, destino: Dict) -> float:
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
    return 1 - cosine(vector_perfil, vector_destino)
```

---

#### **2.2 Similitud Euclidiana Normalizada** (líneas 110-129)
**Función:** `similitud_euclidiana_normalizada(perfil, destino) → float [0,1]`
- Compara presupuesto (costo/turista) específicamente
- Normaliza con exponencial decreciente
- **Ventaja:** Penaliza diferencias grandes en presupuesto
- **Fórmula:** `exp(-distancia / 1000)`

```python
def similitud_euclidiana_normalizada(perfil: Dict, destino: Dict) -> float:
    dist = euclidean(
        [perfil['vector_caracteristicas']['presupuesto']],
        [destino.get('costo_por_turista', 0)]
    )
    similitud = np.exp(-dist / 1000)
    return similitud
```

---

#### **2.3 Similitud Jaccard Categórica** (líneas 132-165)
**Función:** `similitud_jaccard_categorica(perfil, destino) → float [0,1]`
- Compara atributos categóricos: región, tipo turismo
- Región exacta: +0.5 puntos
- Región no evitada: +0.25 puntos
- **Ventaja:** Excluye destinos de regiones rechazadas

```python
def similitud_jaccard_categorica(perfil: Dict, destino: Dict) -> float:
    # Si región del destino está en ideales: +0.5
    # Si NO está en regiones a evitar: +0.25
    # Siempre evita regiones rechazadas por el usuario
```

---

#### **2.4 ⭐ SIMILITUD HÍBRIDA** (líneas 168-193) [FUNCIÓN PRINCIPAL]
**Función:** `similitud_hibrida(perfil, destino, pesos=None) → float [0,1]`

**Combinación Ponderada (por defecto):**
```python
Similitud_Final = 0.5 * Coseno +      # 50% - relaciones multidimensionales
                  0.3 * Euclidiana +  # 30% - compatibilidad presupuestaria
                  0.2 * Jaccard       # 20% - atributos categóricos
```

**Código:**
```python
def similitud_hibrida(perfil: Dict, destino: Dict, pesos: Dict = None) -> float:
    if pesos is None:
        pesos = {'coseno': 0.5, 'euclidiana': 0.3, 'jaccard': 0.2}
    
    sim_cos = similitud_coseno(perfil, destino)
    sim_euc = similitud_euclidiana_normalizada(perfil, destino)
    sim_jac = similitud_jaccard_categorica(perfil, destino)
    
    similitud_final = (
        pesos['coseno'] * sim_cos +
        pesos['euclidiana'] * sim_euc +
        pesos['jaccard'] * sim_jac
    )
    return min(1.0, max(0.0, similitud_final))  # Clamp [0,1]
```

---

#### **2.5 Aplicar a Todo el DataFrame** (líneas 196-206)
**Función:** `calcular_similitud_para_todos(df, perfil) → pd.Series`
- Itera sobre cada fila del DataFrame
- Llama `similitud_hibrida()` para cada destino
- **Output:** Serie con similitud [0,1] para cada país

```python
def calcular_similitud_para_todos(df: pd.DataFrame, perfil: Dict) -> pd.Series:
    similitudes = df.apply(
        lambda row: similitud_hibrida(perfil, row),
        axis=1
    )
    return similitudes
```

---

### 🟡 SECCIÓN 3: Segmentación por Presupuesto (líneas 211-243)
**Función:** `segmentar_por_presupuesto(df, bandas=None) → Dict`

**Bandas Presupuestarias (por defecto):**
- Presupuesto Bajo: $0 - $1,000
- Presupuesto Medio: $1,000 - $3,000
- Presupuesto Alto: $3,000 - $5,000
- Presupuesto Lujo: >$5,000

```python
def segmentar_por_presupuesto(df: pd.DataFrame, bandas: List[Tuple] = None):
    # Crea Dict con Keys = bandas, Values = DataFrames filtrados
    # Cada DataFrame ordenado por similitud_score descendente
    segmentacion[etiqueta] = df_banda.sort_values('similitud_score', ascending=False)
```

---

### 🟣 SECCIÓN 4: Funciones de Utilidad (líneas 246-291)
- `generar_resumen_perfil()`: Resume características del perfil
- `categorizar_densidad()`: Devuelve emoji + etiqueta según llegadas

```python
def generar_resumen_perfil(perfil: Dict) -> str:
    """Genera resumen textual del perfil"""

def categorizar_densidad(llegadas: float) -> Tuple[str, str]:
    """Retorna (emoji, etiqueta) según densidad"""
    # 🔴 Muy Alta (>100M)
    # 🟠 Alta (>50M)
    # 🟡 Media (>10M)
    # 🟢 Baja (<10M)
```

---

## 📁 ARCHIVO: `frontv1.py` (529 líneas)

### ❌ ESTADO: Aún NO Integradas las Métricas

**Dónde se DEBERÍA integrar:**

#### **1. Línea ~195-210: Botón "Generar Perfil"**
- Actualmente: Solo genera `perfil_datos`
- **Falta:** Calcular similitud para recomendaciones

```python
# ACTUAL (línea 182):
st.session_state.perfil_datos = extraer_perfil_usuario(...)

# DEBERÍA SER (línea 182 + NUEVO):
st.session_state.perfil_datos = extraer_perfil_usuario(...)

# + AGREGADO (falta):
if st.session_state.perfil_generado:
    # Calcular similitud cuando se genere recomendación
    recomendaciones['similitud_score'] = calcular_similitud_para_todos(
        recomendaciones,
        st.session_state.perfil_datos
    )
```

#### **2. Línea ~290: En Tab 1 "Recomendaciones"**
- **Falta:** Reordenar por similitud + mostrar barra de progreso
- **Código necesario:** 
  ```python
  if st.session_state.perfil_generado:
      recomendaciones = recomendaciones.sort_values('similitud_score', ascending=False)
      st.progress(row['similitud_score'], text=f"Similitud: {row['similitud_score']*100:.1f}%")
  ```

#### **3. Línea ~350+: Nueva Tab "👤 Mi Perfil"**
- **Falta:** Mostrar características del perfil, gráficos de distribución
- **Llamadas necesarias:** `generar_resumen_perfil()`, `categorizar_densidad()`

#### **4. Línea ~400+: Nueva Tab "💰 Por Presupuesto"**
- **Falta:** Crear acordeones con bandas presupuestarias
- **Llamada necesaria:** `segmentar_por_presupuesto(recomendaciones)`

---

## 📊 RESUMEN DE INTEGRACIÓN PENDIENTE

| Métrica | Ubicación | Estado | Prioridad |
|---------|-----------|--------|-----------|
| Coseno | `perfil_usuario.py:79-107` | ✅ Implementada | 🔴 ALTA |
| Euclidiana | `perfil_usuario.py:110-129` | ✅ Implementada | 🔴 ALTA |
| Jaccard | `perfil_usuario.py:132-165` | ✅ Implementada | 🔴 ALTA |
| **Híbrida** ⭐ | `perfil_usuario.py:168-193` | ✅ Implementada | 🔴 **MÁS ALTA** |
| Segmentación | `perfil_usuario.py:211-243` | ✅ Implementada | 🟠 MEDIA |
| **Integración en frontv1.py** | Líneas 182-290 | ❌ **NO HECHO** | 🔴 **CRÍTICO** |

---

## 🚀 PRÓXIMOS PASOS

1. **PASO 6 (Siguiente):** Integrar similitud en Tab 1 (Recomendaciones)
   - Calcular `similitud_score` cuando usuario hace click en "Generar Recomendaciones"
   - Reordenar destinos por similitud
   - Mostrar barra de progreso visual en cada tarjeta

2. **PASO 7:** Crear Tab "Mi Perfil" con visualización
3. **PASO 8:** Crear Tab "Por Presupuesto" con segmentación

¿Quieres que continúe con la **integración en frontv1.py** (PASO 6)?

# ESTRUCTURA DE UI PARA PERFIL DE USUARIO
# Plan de implementación del sidebar y nuevas tabs

## PASO 1: MODIFICAR SIDEBAR (frontv1.py líneas ~50-120)
```python
# En la sección de sidebar, DESPUÉS de los filtros actuales, agregar:

st.sidebar.divider()
st.sidebar.markdown("### 👤 Crear Tu Perfil")
st.sidebar.write("Ayúdanos a entender tus preferencias turísticas")

# Inicializar session_state para perfil
if 'paises_ideales' not in st.session_state:
    st.session_state.paises_ideales = []
if 'paises_no_ideales' not in st.session_state:
    st.session_state.paises_no_ideales = []
if 'perfil_generado' not in st.session_state:
    st.session_state.perfil_generado = False
if 'perfil_datos' not in st.session_state:
    st.session_state.perfil_datos = None

# Selector de destinos ideales (favoritos)
st.sidebar.subheader("✅ Destinos Ideales")
st.sidebar.write("Países que te *ENCANTARON*")
paises_ideales_input = st.sidebar.multiselect(
    "Selecciona destinos que visitaste y te encantaron:",
    df_destinos['country'].sort_values().unique(),
    default=st.session_state.paises_ideales,
    key='paises_ideales_selector'
)
st.session_state.paises_ideales = paises_ideales_input

# Selector de destinos no-ideales (no te gustaron)
st.sidebar.subheader("❌ Destinos No-Ideales")
st.sidebar.write("Países que visitaste pero no recomendarías")
paises_no_ideales_input = st.sidebar.multiselect(
    "Selecciona destinos que NO te gustaron:",
    df_destinos['country'].sort_values().unique(),
    default=st.session_state.paises_no_ideales,
    key='paises_no_ideales_selector'
)
st.session_state.paises_no_ideales = paises_no_ideales_input

# Botón para generar perfil
if st.sidebar.button('🎯 Generar Perfil Personalizado', use_container_width=True):
    from perfil_usuario import extraer_perfil_usuario
    
    st.session_state.perfil_datos = extraer_perfil_usuario(
        df_destinos,
        st.session_state.paises_ideales,
        st.session_state.paises_no_ideales
    )
    st.session_state.perfil_generado = True
    st.sidebar.success("✅ Perfil generado exitosamente")
```

## PASO 2: MODIFICAR TABS (frontv1.py líneas ~232)
```python
# Cambiar de:
# tab1, tab2 = st.tabs(["📍 Recomendaciones", "📊 Comparativa"])

# A:
tab1, tab2, tab_perfil, tab_presupuesto = st.tabs([
    "📍 Recomendaciones",
    "📊 Comparativa",
    "👤 Mi Perfil",
    "💰 Por Presupuesto"
])
```

## PASO 3: AGREGAR TAB "MI PERFIL" (Nueva)
```python
with tab_perfil:
    st.subheader("👤 Tu Perfil Personalizado")
    
    if st.session_state.perfil_generado and st.session_state.perfil_datos:
        perfil = st.session_state.perfil_datos
        
        # Mostrar destinos seleccionados
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ Destinos Ideales")
            for pais in st.session_state.paises_ideales:
                st.markdown(f"• {pais}")
        
        with col2:
            st.subheader("❌ Destinos Evitar")
            for pais in st.session_state.paises_no_ideales:
                st.markdown(f"• {pais}")
        
        st.divider()
        
        # Características extraídas
        st.subheader("📊 Características Preferidas")
        
        perf_col1, perf_col2, perf_col3 = st.columns(3)
        
        with perf_col1:
            st.metric(
                "Densidad Ideal",
                f"{perfil['densidad_ideal_media']/1e6:.2f}M",
                help="Promedio de llegadas en destinos que te encantaron"
            )
        
        with perf_col2:
            st.metric(
                "Presupuesto Ideal",
                f"${perfil['presupuesto_ideal_media']:,.0f}",
                help="Costo promedio por turista"
            )
        
        with perf_col3:
            st.metric(
                "Tipo Turismo",
                perfil['tipo_turismo_ideal'],
                help="Clasificación preferida"
            )
        
        st.divider()
        
        # Gráfico: Comparativa de preferencias
        if perfil['densidad_evitar_media']:
            import matplotlib.pyplot as plt
            
            fig, ax = plt.subplots(figsize=(10, 4))
            
            categorias = ['Densidad\nTurística', 'Presupuesto\nPromedio']
            ideales = [
                perfil['densidad_ideal_media']/1e6,
                perfil['presupuesto_ideal_media']/1000
            ]
            evitar = [
                perfil['densidad_evitar_media']/1e6,
                perfil['presupuesto_evitar_media']/1000
            ]
            
            x = np.arange(len(categorias))
            width = 0.35
            
            ax.bar(x - width/2, ideales, width, label='✅ Ideales', color='#2ecc71')
            ax.bar(x + width/2, evitar, width, label='❌ Evitar', color='#e74c3c')
            
            ax.set_ylabel('Valor')
            ax.set_title('Comparativa: Destinos Ideales vs. A Evitar')
            ax.set_xticks(x)
            ax.set_xticklabels(categorias)
            ax.legend()
            
            st.pyplot(fig)
    else:
        st.info("👈 Selecciona destinos ideales y no-ideales en la barra lateral y haz clic en 'Generar Perfil'")
```

## PASO 4: AGREGAR TAB "POR PRESUPUESTO" (Nueva)
```python
with tab_presupuesto:
    st.subheader("💰 Recomendaciones por Nivel Presupuestario")
    st.write("Destinos agrupados según costo promedio por turista")
    
    from perfil_usuario import segmentar_por_presupuesto
    
    # Segmentar recomendaciones
    segmentacion = segmentar_por_presupuesto(recomendaciones)
    
    for banda_nombre, df_banda in segmentacion.items():
        with st.expander(f"{banda_nombre} (${df_banda['costo_por_turista'].min():,.0f} - ${df_banda['costo_por_turista'].max():,.0f})"):
            
            # Resumen de la banda
            suma_col1, suma_col2, suma_col3 = st.columns(3)
            
            with suma_col1:
                st.metric("Países", len(df_banda))
            with suma_col2:
                st.metric("Costo Promedio", f"${df_banda['costo_por_turista'].mean():,.0f}")
            with suma_col3:
                st.metric("Score Promedio", f"{df_banda['score_final'].mean():.2f}")
            
            st.divider()
            
            # Tabla con destinos de esta banda
            df_mostrar = df_banda[[
                'country', 'costo_por_turista', 'tourism_arrivals', 
                'inflation', 'score_final'
            ]].head(5).copy()
            
            df_mostrar.columns = ['País', 'Costo/Turista ($)', 'Llegadas (M)', 
                                  'Inflación (%)', 'Score']
            df_mostrar['Llegadas (M)'] = df_mostrar['Llegadas (M)'] / 1e6
            
            st.dataframe(
                df_mostrar.style.format({
                    'Costo/Turista ($)': '{:,.0f}',
                    'Llegadas (M)': '{:.2f}',
                    'Inflación (%)': '{:.1f}',
                    'Score': '{:.3f}'
                }),
                use_container_width=True,
                hide_index=True
            )
```

## PASO 5: INTEGRAR SIMILITUD EN TAB 1 (Recomendaciones)
```python
# EN TAB 1, ANTES de mostrar recomendaciones, agregar:

if st.session_state.perfil_generado and st.session_state.perfil_datos:
    from perfil_usuario import calcular_similitud_para_todos
    
    # Calcular similitud para todas las recomendaciones
    recomendaciones['similitud_score'] = calcular_similitud_para_todos(
        recomendaciones,
        st.session_state.perfil_datos
    )
    
    # Reordenar por similitud (descendente)
    recomendaciones = recomendaciones.sort_values('similitud_score', ascending=False)
    
    st.info(f"🎯 Basado en tu perfil, estos destinos tienen {recomendaciones['similitud_score'].iloc[0]*100:.0f}% de similitud con tus preferencias")

# EN CADA TARJETA DE DESTINO, agregar barra de similitud:
if 'similitud_score' in recomendaciones.columns:
    similitud = row['similitud_score']
    st.progress(similitud, text=f"Similitud: {similitud*100:.1f}%")
```

## NOTAS DE IMPLEMENTACIÓN

### Orden de Implementación Recomendado:
1. ✅ Crear `perfil_usuario.py` (funciones auxiliares) - DONE
2. ⏳ Modificar sidebar para inputs de perfil (PASO 1)
3. ⏳ Agregar tabs nuevas en frontv1.py (PASO 2)
4. ⏳ Agregar Tab "Mi Perfil" con visualización (PASO 3)
5. ⏳ Agregar Tab "Por Presupuesto" (PASO 4)
6. ⏳ Integrar similitud en Tab 1 (PASO 5)

### Dependencias Necesarias:
- scipy
- scikit-learn
- matplotlib (ya debería estar)

### Testing Mínimo:
- [ ] Seleccionar destinos ideales/no-ideales
- [ ] Generar perfil exitosamente
- [ ] Ver Tab "Mi Perfil" con datos correctos
- [ ] Ver Tab "Por Presupuesto" segmentado
- [ ] Verificar similitud aparezca en Tab 1 y reordene correctamente

# 🧪 PLAN DE TESTING - Tab "Mi Perfil"

## Objetivo
Verificar que la Tab "👤 Mi Perfil" funciona correctamente mostrando:
1. Destinos ideales seleccionados
2. Destinos no-ideales seleccionados
3. Características extraídas (Densidad, Presupuesto, Tipo)
4. Gráfico comparativo
5. Explicación del sistema

---

## 📋 PASOS DE TEST

### TEST 1: Interface Básica
```
1. Abre http://localhost:8501
2. Ve a la barra lateral
3. Verifica que ves:
   - ✅ "✅ Destinos Ideales" (multiselect)
   - ✅ "❌ Destinos No-Ideales" (multiselect)
   - ✅ Botón "🎯 Generar Perfil Personalizado"
```

### TEST 2: Seleccionar Destinos Ideales
```
1. En sidebar, abre "✅ Destinos Ideales"
2. Selecciona 2-3 destinos (ej: Tailandia, Vietnam, Indonesia)
3. Verifica que se muestran en el multiselect
4. ✅ ESPERADO: Los países aparecen en la lista
```

### TEST 3: Seleccionar Destinos No-Ideales
```
1. En sidebar, abre "❌ Destinos No-Ideales"
2. Selecciona 1-2 destinos (ej: Dubai, Singapur)
3. Verifica que se muestran en el multiselect
4. ✅ ESPERADO: Los países aparecen en la lista
```

### TEST 4: Generar Perfil
```
1. Haz clic en "🎯 Generar Perfil Personalizado"
2. Espera a que se procese (3-5 segundos)
3. ✅ ESPERADO: 
   - Mensaje de éxito ✅ (verde)
   - Indicador en sidebar: "👤 Perfil activo con X favoritos..."
```

### TEST 5: Verificar Tab "Mi Perfil" - Destinos Ideales
```
1. Llena los filtros (presupuesto, tipo, economía)
2. Haz clic en "🔍 Generar Recomendaciones"
3. En las tabs, haz clic en "👤 Mi Perfil"
4. En la sección "✅ Destinos Ideales":
   ✅ ESPERADO: Ves los destinos que seleccionaste
   ✅ FORMATO: Cada uno en una caja azul (st.info)
```

### TEST 6: Verificar Tab "Mi Perfil" - Destinos No-Ideales
```
1. En la Tab "👤 Mi Perfil", ve la sección "❌ Destinos No-Ideales"
2. ✅ ESPERADO: Ves los destinos que seleccionaste como "a evitar"
3. ✅ FORMATO: Cada uno en una caja naranja (st.warning)
```

### TEST 7: Verificar Características Extraídas
```
1. En la Tab "👤 Mi Perfil", ve la sección "📊 Características de Tu Perfil"
2. Verifica que aparecen 3 tarjetas (métricas):
   ✅ "🎯 Densidad Ideal" (ej: 15.5M)
   ✅ "💰 Presupuesto Ideal" (ej: $850)
   ✅ "🏆 Tipo de Turismo" (ej: Emergentes)
3. ✅ ESPERADO: Los valores tiene sentido (promedio de tus destinos favoritos)
```

### TEST 8: Verificar Gráfico Comparativo
```
1. En la Tab "👤 Mi Perfil", ve la sección "📈 Comparativa: Ideales vs. A Evitar"
2. ✅ ESPERADO: Ves dos gráficos de barras:
   - Izquierda: Densidad Turística Comparada
     └─ Barras verdes (Ideales) vs rojas (A Evitar)
   - Derecha: Presupuesto Promedio Comparado
     └─ Barras verdes (Ideales) vs rojas (A Evitar)
3. ✅ Valores mostrados arriba de cada barra
```

### TEST 9: Verificar Explicación
```
1. En la Tab "👤 Mi Perfil", ve el expander "📚 Ver Explicación Detallada"
2. Haz clic para expandir
3. ✅ ESPERADO: Ves explicación de:
   - 🔵 Similitud Coseno (50%)
   - 🟠 Similitud Euclidiana (30%)
   - 🟡 Similitud Jaccard (20%)
```

### TEST 10: Verificar Sin Perfil
```
1. Abre la app en nueva ventana sin generar perfil
2. Llena filtros y genera recomendaciones
3. Haz clic en Tab "👤 Mi Perfil"
4. ✅ ESPERADO: Ves mensaje azul: 
   "👈 Primero, selecciona destinos ideales..."
```

### TEST 11: Verificar Tab 1 Aún Funciona
```
1. Genera un perfil
2. En Tab "📍 Recomendaciones":
   ✅ ESPERADO: Ves destinos con barra de similitud
   ✅ Destinos ordenados por similitud (descendente)
```

### TEST 12: Verificar Tab 2 Aún Funciona
```
1. Genera un perfil
2. En Tab "📊 Comparativa":
   ✅ ESPERADO: Tabla con todos los destinos y métricas
```

---

## ✅ CHECKLIST DE VALIDACIÓN

- [ ] Tab "Mi Perfil" aparece en las opciones (tercera tab)
- [ ] Se muestran destinos ideales correctamente (cajas azules)
- [ ] Se muestran destinos no-ideales correctamente (cajas naranja)
- [ ] Aparecen 3 métricas en tarjetas
- [ ] Gráfico comparativo se renderiza sin errores
- [ ] Gráfico muestra barras verdes (ideales) y rojas (evitar)
- [ ] Explicación es clara y accesible
- [ ] Sin perfil, muestra mensaje informativo
- [ ] Con perfil, muestra datos completos
- [ ] Tab 1 aún funciona (similitud visible)
- [ ] Tab 2 aún funciona (tabla visible)
- [ ] No hay errores en la consola

---

## 🐛 POSIBLES ERRORES

| Error | Causa | Solución |
|-------|-------|----------|
| Tab 3 no aparece | `tab3` no definida en st.tabs | Verificar línea de tabs |
| Gráfico no se muestra | matplotlib no instalada | `pip install matplotlib` |
| Datos None | Perfil no generado | Generar perfil primero |
| Valores vacíos en destinos | Multiselect vacío | Seleccionar al menos 1 país |
| Columnas mal alineadas | CSS de Streamlit | Recarga la página |

---

## 📊 RESULTADO ESPERADO FINAL

### Tab 1: Recomendaciones ✅
```
✅ Similaridad con tu Perfil activa
✅ Destinos ordenados por similitud (100%, 95%, 90%, ...)
✅ Barra de progreso en cada destino
```

### Tab 2: Comparativa ✅
```
✅ Tabla con todos los destinos
✅ Todas las métricas visibles
```

### Tab 3: Mi Perfil ✅ (NUEVA)
```
✅ 2 destinos ideales (Tailandia, Vietnam)
✅ 1 destino a evitar (Dubai)
✅ 3 métricas (Densidad: 15M, Presupuesto: $850, Tipo: Emergentes)
✅ Gráfico con barras verdes y rojas
✅ Explicación clara del sistema
```

---

## 🚀 PRÓXIMO PASO TRAS VALIDACIÓN

Si TODO funciona:
→ Confirma "✅ Todo funciona perfectamente"
→ Procederemos a crear Tab 4 "💰 Por Presupuesto"

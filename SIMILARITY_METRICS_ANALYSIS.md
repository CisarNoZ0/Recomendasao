# Análisis de Métricas de Similitud para Recomendación de Destinos Turísticos

## Contexto del Problema
Necesitamos encontrar destinos similares a los visitados favorablemente por el usuario, considerando:
- **Densidad turística** (millones de llegadas)
- **Presupuesto promedio** (costo/turista)
- **Tipo de turismo** (joyas ocultas, emergentes, populares)
- **Salud económica** (estabilidad, crecimiento)
- **Región geográfica**

---

## Comparativa de Métricas

### 1. **Correlación de Pearson** 🔵
**Fórmula:** Mide relación lineal entre dos variables (-1 a 1)
```
ρ(X,Y) = Cov(X,Y) / (σ_X * σ_Y)
```

**Ventajas:**
- ✅ Detecta relaciones lineales fuertes
- ✅ Valor intuitivo: 1=perfecta similitud, 0=ninguna, -1=inversa
- ✅ Maneja bien variabilidad de escala
- ✅ Computacionalmente eficiente

**Desventajas:**
- ❌ Solo captura relaciones **lineales** (si hay relaciones no-lineales, falla)
- ❌ Requiere mínimo 2-3 puntos de datos por país
- ❌ Sensible a outliers (países con densidad extrema distorsionan)
- ❌ No considera diferencias de magnitud absolutas (ej: $100 vs $1000)

**Caso de uso:** ✔️ Bueno para correlacionar TENDENCIAS (ej: crecimiento % similar)

---

### 2. **Similitud de Coseno** 🟢
**Fórmula:** Ángulo entre vectores de características (0 a 1)
```
cos(θ) = (A·B) / (||A|| * ||B||) = Σ(a_i * b_i) / √(Σa_i²) * √(Σb_i²)
```

**Ventajas:**
- ✅ **Mejor para espacios multidimensionales** (nuestro caso)
- ✅ Independiente de magnitud (normaliza automáticamente)
- ✅ Rápido de calcular, O(n)
- ✅ Insensible a outliers de escala
- ✅ Excelente cuando características son independientes

**Desventajas:**
- ❌ Ignora diferencias de magnitud (país de 100M vs 1M turistas = igual similitud)
- ❌ No captura "distancia real" en el espacio
- ❌ Valores en [0,1] pero requiere normalización previa

**Caso de uso:** ✔️ **RECOMENDADO** para este proyecto (densidad, presupuesto, región)

---

### 3. **Distancia Euclidiana** 🟡
**Fórmula:** Distancia geométrica en espacio n-dimensional
```
d(X,Y) = √(Σ(x_i - y_i)²)
```

**Ventajas:**
- ✅ Captura diferencia absoluta en todas las dimensiones
- ✅ Intuitiva: "qué tan lejos estamos"
- ✅ Funciona bien con características normalizadas

**Desventajas:**
- ❌ Sensible a diferencias de escala (país con GDP $1T vs $10B domina)
- ❌ Requiere normalización explícita Z-score o Min-Max
- ❌ Computacionalmente más cara que coseno
- ❌ En muchas dimensiones: la mayoría de puntos quedan equidistantes (curse of dimensionality)

**Caso de uso:** ⚠️ Viable si normalizas bien las características

---

### 4. **Similitud de Jaccard** 🟣
**Fórmula:** Intersección/Unión de conjuntos
```
J(A,B) = |A ∩ B| / |A ∪ B|
```

**Ventajas:**
- ✅ Excelente para datos **categóricos** (región, tipo turismo)
- ✅ No requiere normalización
- ✅ Intuitivo: porcentaje de atributos en común

**Desventajas:**
- ❌ No funciona bien con datos continuos (densidad, presupuesto)
- ❌ Pierde información sobre "cuán diferentes" son
- ❌ Requiere discretizar variables continuas (poca precisión)

**Caso de uso:** ⚠️ Solo para filtrado categórico, no como métrica principal

---

### 5. **Distancia de Manhattan (L1)** 🟠
**Fórmula:** Suma de diferencias absolutas
```
d(X,Y) = Σ|x_i - y_i|
```

**Ventajas:**
- ✅ Menos sensible a outliers que Euclidiana
- ✅ Más rápida que Euclidiana
- ✅ Mejor para datos dispersos

**Desventajas:**
- ❌ Aún requiere normalización
- ❌ Menos intuitiva en espacios altos-dimensionales

**Caso de uso:** ⚠️ Segunda opción si Coseno no da buenos resultados

---

### 6. **Dynamic Time Warping (DTW)** 🟤
**Fórmula:** Distancia óptima entre series temporales permitiendo "warping"
```
DTW(A,B) = min(Σ d(a_i, b_i)) con restricción de orden temporal
```

**Ventajas:**
- ✅ **Excelente para TENDENCIAS históricas** (Tab 3 deshabilitada)
- ✅ Detecta patrones temporales similares incluso con desfase
- ✅ Captura "forma" de la curva, no solo valores

**Desventajas:**
- ❌ Computacionalmente costoso O(n²)
- ❌ Complejo de implementar
- ❌ Overkill si solo usamos estado actual

**Caso de uso:** ⚠️ Futuro: cuando Tab 3 (Tendencias) esté activa

---

### 7. **Similitud Híbrida (Recomendada para este proyecto)** ✨
**Combinación ponderada:**
```
Similitud_Final = w1 * Coseno(perfil_turístico) + 
                  w2 * Euclidiana_normalizada(presupuesto) + 
                  w3 * Jaccard(región, tipo_turismo)

Típicamente: w1=0.5, w2=0.3, w3=0.2
```

**Ventajas:**
- ✅ Captura múltiples dimensiones de similitud
- ✅ Flexible: ajusta pesos según importancia
- ✅ Combinan fortalezas de cada métrica
- ✅ Personalizable por usuario

**Desventajas:**
- ⚠️ Requiere calibración de pesos
- ⚠️ Más compleja de interpretar

**Caso de uso:** ✔️ **MÁS RECOMENDADO** para este proyecto

---

## Recomendación Final para el Proyecto

### **Implementar Similitud Híbrida (3-métrica):**

1. **Coseno (50%):** Perfil turístico (densidad, tipo, ingresos por turista)
   - Normalizado por Z-score antes
   
2. **Euclidiana (30%):** Presupuesto promedio
   - Escalado Min-Max [0,1]
   - Penalizar diferencias extremas
   
3. **Jaccard (20%):** Atributos categóricos (región, clasificación económica)
   - Región exacta: +0.5
   - Región vecina: +0.25
   - Clasificación económica igual: +0.25

### **Flujo de Cálculo:**

```
1. Usuario selecciona: [Tailandia (visitado ✅), Dubai (visitado ❌)]
2. Sistema extrae perfil:
   - Densidad media positivos: 25M viajeros
   - Presupuesto positivos: $850/turista
   - Regiones positivas: Asia
   - Densidad media negativos: 50M viajeros
   - Tipo rechazo: "masivo, densidad muy alta"
   
3. Para CADA país candidato:
   - Coseno({densidad, tipo, ingresos} destino vs perfil)
   - Euclidiana(presupuesto destino vs preferencia)
   - Jaccard(región, categoría)
   - Similitud_Final = 0.5*Coseno + 0.3*Euclidiana + 0.2*Jaccard
   
4. Ordenar por Similitud_Final
5. Mostrar top-10 con barra visual de similitud %
```

### **Alternativa Simplificada (si es muy complejo):**
Solo usar **Coseno** (95% del valor con 5% de complejidad)

---

## Próximos Pasos
- [ ] Implementar extractor de perfil de destinos seleccionados
- [ ] Normalizar DataFrame de características
- [ ] Calcular matriz de similitud híbrida
- [ ] Integrar en Tab 1 (Recomendaciones)
- [ ] Agregar visualización de "similitud %" por destino

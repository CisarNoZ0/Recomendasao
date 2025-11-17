# Informe de Funcionalidades: Proyecto de Recomendación Turística

Este documento explica el funcionamiento del sistema de recomendación turística en términos sencillos, diseñado para una presentación oral y para responder preguntas de una audiencia general.

## 1. ¿Cuál es el objetivo del proyecto?

El proyecto es una aplicación web que recomienda destinos turísticos (países) a los usuarios. Su principal característica es que se basa en **datos objetivos** (economía, número de turistas) y en un **perfil de gustos personalizado**, en lugar de opiniones subjetivas.

El objetivo es ayudar a un usuario a descubrir su próximo destino ideal basándose en sus preferencias y en las características reales de los países.

## 2. Estructura del Código

El proyecto se divide en varios archivos clave, cada uno con una responsabilidad clara:

| Archivo | Responsabilidad | Explicación Sencilla |
| :--- | :--- | :--- |
| `frontv1.py` | **Interfaz de Usuario y Orquestador** | Es el corazón de la aplicación. Dibuja la página web que el usuario ve (usando Streamlit), captura sus selecciones (presupuesto, gustos) y llama a otras partes del código para obtener los resultados. |
| `perfil_usuario.py` | **El Cerebro de la Personalización** | Contiene la "magia" detrás de las recomendaciones personalizadas. Analiza los países que al usuario le gustaron y disgustaron para crear un "perfil matemático" de sus gustos. |
| `world_tourism_economy_data.csv` | **La Base de Datos Principal** | Es un archivo Excel (CSV) que contiene todos los datos históricos sobre turismo, economía, inflación, etc., para cada país. Es la fuente de toda la información objetiva. |
| `manejo_db.py` | **Script de Análisis de Datos** | Es un archivo auxiliar usado durante el desarrollo para explorar y entender los datos del CSV. No forma parte de la aplicación en vivo. |

---

## 3. ¿Cómo Funciona? (Paso a Paso)

El proceso desde que el usuario abre la página hasta que recibe una recomendación es el siguiente:

### Paso 1: Carga y Preparación de Datos

1.  **Lectura de Datos:** La aplicación lee el archivo `world_tourism_economy_data.csv`.
2.  **Limpieza:** Filtra datos irrelevantes (como "Unión Europea", que no es un país de destino) y se queda con la información más reciente y completa de cada país.
3.  **Enriquecimiento (Conexión a Internet):** La aplicación se conecta a **OpenStreetMap** (una especie de Wikipedia de mapas) para obtener datos adicionales que no están en el CSV, como la cantidad de hoteles, museos o parques en las ciudades principales de cada país.
    -   *Nota:* Para evitar que esta conexión sea lenta cada vez, el sistema **guarda en caché** los resultados. La primera vez que busca datos de un país es lento, pero las siguientes veces es instantáneo.

### Paso 2: El Usuario Define sus Preferencias

El usuario tiene dos maneras de decirle al sistema lo que busca:

1.  **Filtros Generales (Sliders):** En la barra lateral, el usuario ajusta:
    -   **Presupuesto:** ¿Cuánto está dispuesto a gastar?
    -   **Popularidad:** ¿Prefiere un lugar muy concurrido, uno emergente o una "joya oculta"?
    -   **Economía:** ¿Busca un país económicamente estable?

2.  **Perfil Personalizado (Selección de Países):**
    -   El usuario selecciona países que **le encantaron** en el pasado.
    -   También puede seleccionar países que **no le gustaron**.

### Paso 3: El Motor de Recomendación Trabaja

Aquí es donde ocurre la lógica principal:

-   **Si el usuario solo usa los filtros generales:** El sistema simplemente busca los países que cumplen con el presupuesto y los ordena según qué tan bien encajan con la popularidad y economía deseadas.

-   **Si el usuario crea un Perfil Personalizado (la parte más avanzada):**
    1.  **Extracción del Perfil:** La función `extraer_perfil_usuario` analiza las características de los países que al usuario le gustaron (ej: "A este usuario le gustan los países con ~20 millones de turistas y un costo promedio de $1,500"). Esto crea un **vector de gustos**.
    2.  **Cálculo de Similitud:** La función `similitud_hibrida` compara ese "vector de gustos" con CADA uno de los otros países del mundo. Usa fórmulas matemáticas (similitud coseno, euclidiana) para calcular un **porcentaje de similitud** (de 0% a 100%).
    3.  **Ponderación:** El resultado final es una combinación: un 70% del peso viene de la similitud con su perfil personal y un 30% de los filtros generales (sliders).

### Paso 4: Se Muestran los Resultados

La aplicación presenta los **10 países con la puntuación más alta** en una lista clara y ordenada. Para cada país, muestra:
-   Métricas clave (costo, llegadas de turistas, crecimiento).
-   El **porcentaje de similitud** con su perfil.
-   Datos económicos (inflación, desempleo).
-   Una pestaña adicional para explorar las **ciudades principales** y su cantidad de hoteles (los datos obtenidos de OpenStreetMap).

---

## 4. Funciones Clave Explicadas

-   `load_data()`: **"El Lector"**. Carga y limpia los datos del archivo CSV.
-   `enriquecer_con_datos_osm_mejorado()`: **"El Explorador"**. Se conecta a internet para buscar información adicional de ciudades (hoteles, museos) y la añade a los datos de los países.
-   `generar_recomendaciones()`: **"El Director de Orquesta"**. Recibe todas las preferencias del usuario y utiliza los datos para generar la lista final de recomendaciones.
-   `extraer_perfil_usuario()`: **"El Psicólogo"**. Entiende los gustos del usuario analizando sus viajes pasados para crear un perfil numérico.
-   `similitud_hibrida()`: **"El Juez de Compatibilidad"**. Es la fórmula matemática que decide qué tan compatible es un país con los gustos del usuario.
-   `obtener_ciudades_con_hoteles_osm()`: **"El Agente de Viajes Local"**. Busca específicamente ciudades y hoteles para un país recomendado, y usa un sistema de caché (`@st.cache_data`) para ser muy rápido después de la primera búsqueda.


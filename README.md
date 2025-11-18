# Recomendasao
App para recomendasao

Aplicación web de recomendación turística que utiliza datos históricos objetivos para sugerir destinos basados en las preferencias del usuario.

## Estructura del Repositorio

Para que la aplicación funcione correctamente, es crucial entender el propósito de cada archivo. No es necesario modificar ninguna ruta en el código siempre y cuando se mantenga la estructura de carpetas original.

### Archivos Esenciales (Necesarios para Ejecutar)

Estos archivos son **indispensables** para que la aplicación funcione:

*   `frontv1.py`: El script principal de la aplicación Streamlit. Contiene la interfaz de usuario y la lógica de presentación.
*   `perfil_usuario.py`: Módulo que contiene las funciones para generar perfiles de usuario personalizados y calcular la similitud entre destinos.
*   `world_tourism_economy_data.csv`: La fuente de datos principal con información económica y turística a nivel de país.
*   `osm_cities_with_hotels.csv`: Archivo precalculado con el conteo de hoteles por ciudad para cada país. Es crucial para la funcionalidad del "Termómetro de Ambiente Turístico".
*   `requirements.txt`: Archivo que lista todas las dependencias de Python necesarias para el proyecto.

### Archivos Auxiliares (Para Desarrollo)

Estos archivos son para mantenimiento y no son necesarios para la ejecución normal de la aplicación.

*   `precompute_osm_data.py`: Script utilizado para generar el archivo `osm_cities_with_hotels.csv`. Su ejecución es muy lenta (puede tardar horas) ya que consulta una API externa para cada país. **No necesitas ejecutarlo** a menos que quieras actualizar los datos de hoteles.

## Configuración del Entorno

1.  **Requisito Previo**: Asegúrate de tener Python 3.9+ instalado.

2.  **Instalar Dependencias**: Crea un archivo llamado `requirements.txt` en la raíz del proyecto con el siguiente contenido:
    ```
    streamlit
    pandas
    numpy
    requests
    geonamescache
    scikit-learn
    matplotlib
    ```
    Luego, instala todas las librerías necesarias con un solo comando:
    ```bash
    pip install -r requirements.txt
    ```

## Ejecución

### Iniciar la aplicación
Para ejecutar la aplicación web, utiliza el siguiente comando en tu terminal:
```bash
python -m streamlit run frontv1.py
```

### Detener la aplicación
Para detener todos los procesos de Python (incluyendo el servidor de Streamlit), puedes usar este comando de PowerShell:
```powershell
Stop-Process -Name python -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2
```

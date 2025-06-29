# Scraper y Analizador de Datos de ZonaProp

**Autor:** Facundo Javier Martinez

## Descripción

Este proyecto contiene una serie de scripts de Python diseñados para extraer (scrapear), procesar y analizar datos de publicaciones inmobiliarias (Casas y PH) del sitio web ZonaProp para la Capital Federal.

El objetivo final es generar un dataset limpio y estructurado para su posterior análisis exploratorio y el entrenamiento de modelos predictivos.

## Estructura del Proyecto

-   **/data/**: Carpeta donde se almacena la salida de los scripts.
    -   **/raw_html/**: Contiene los archivos HTML crudos de cada publicación descargada.
    -   **/processed/**: Contiene el dataset final en formato CSV.
    -   `urls.txt`: Archivo de persistencia para las URLs recolectadas, permite reanudar el scraping.
-   **/src/**: Carpeta con el código fuente del proyecto.
    -   `scraper.py`: Script principal para la recolección de URLs y descarga de los archivos HTML.
    -   `parser.py`: Script para procesar los HTML, extraer la información relevante y generar el CSV final.
    -   `utils.py`: Funciones de utilidad (ej. configuración de logs).
    -   `config.py`: Variables de configuración del proyecto (URLs, rutas, etc.).
-   `requirements.txt`: Listado de las dependencias de Python necesarias para ejecutar el proyecto.

## Instalación y Uso

1.  **Clonar el repositorio**
    ```bash
    git clone <url-del-repositorio>
    cd scrap_zonaprop
    ```

2.  **Crear y activar un entorno virtual**
    ```bash
    python -m venv venv
    # En Windows
    .\venv\Scripts\activate
    # En macOS/Linux
    source venv/bin/activate
    ```

3.  **Instalar dependencias**
    ```bash
    pip install -r requirements.txt
    ```

## Flujo de Ejecución

El proceso está dividido en dos etapas principales:

1.  **Etapa 1: Recolección de Datos**
    Para descargar los archivos HTML de las publicaciones, ejecuta el scraper. Este script es reanudable; si se interrumpe, puedes volver a ejecutarlo para continuar la descarga donde se quedó.
    ```bash
    python -m src.scraper
    ```

2.  **Etapa 2: Procesamiento de Datos**
    Una vez que tienes los archivos HTML en la carpeta `data/raw_html`, ejecuta el parser. Este script leerá todos los archivos, extraerá los datos y generará `propiedades_procesado_FINAL.csv`.
    ```bash
    python -m src.parser
    ```

3.  **Etapa 3: Análisis de Datos**
    Utilizar un Jupyter Notebook para cargar y analizar el archivo `propiedades_procesado_FINAL.csv` ubicado en la carpeta `data/processed`.

## Tecnologías Utilizadas

-   Python 3.9+
-   Selenium con Undetected Chromedriver
-   BeautifulSoup4
-   Demjson3
-   Pandas
-   Folium, Plotly, Matplotlib, Seaborn (para visualización)
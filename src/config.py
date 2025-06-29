import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# --- Configuración General ---
BASE_URL_ZONAPROP = "https://www.zonaprop.com.ar/casas-ph-venta-capital-federal-con-apto-credito.html" # de mi interés personal
PROYECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Rutas de datos
DATA_DIR = os.path.join(PROYECT_ROOT, 'data')
RAW_HTML_DIR = os.path.join(DATA_DIR, 'raw_html')
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, 'processed')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')

# Asegurar que los directorios existan
os.makedirs(RAW_HTML_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

# --- Configuración del Scraper ---
# Retrasos aleatorios para simular comportamiento humano (en segundos)
MIN_DELAY = 3
MAX_DELAY = 8

# Número de reintentos para cargar una página
MAX_RETRIES = 3

# Modo Headless de Selenium
HEADLESS_MODE = False

# Opcional: Proxies
PROXIES = os.getenv("PROXIES", "").split(';')
if not PROXIES or PROXIES == ['']:
    PROXIES = [] # No usar proxies por defecto

# Número de páginas a scrapear
MAX_PAGES_TO_SCRAPE = 154
import logging
import os
import random
from src.config import LOGS_DIR 

def setup_logging():
    """Configura el logger del proyecto."""
    log_file = os.path.join(LOGS_DIR, 'scraper.log')
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def random_delay():
    """Genera un retraso aleatorio para simular comportamiento humano."""
    from src.config import MIN_DELAY, MAX_DELAY # Importar aquí para evitar circular dependency al inicio
    delay = random.uniform(MIN_DELAY, MAX_DELAY)
    logging.info(f"Esperando {delay:.2f} segundos...")
    return delay

def safe_click(driver, by, value):
    """
    Intenta hacer clic en un elemento, esperando que sea clickeable.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException

    logger = logging.getLogger(__name__)
    try:
        element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((by, value))
        )
        element.click()
        return True
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"No se pudo hacer clic en el elemento ({by}, {value}): {e}")
        return False
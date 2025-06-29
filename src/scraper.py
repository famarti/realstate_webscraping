# src/scraper.py
import os
import time
import random
import hashlib

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException

from bs4 import BeautifulSoup

from src.config import (
    BASE_URL_ZONAPROP, RAW_HTML_DIR,
    MIN_DELAY, MAX_DELAY, MAX_PAGES_TO_SCRAPE, DATA_DIR
)
from src.utils import setup_logging, random_delay

logger = setup_logging()
os.makedirs(RAW_HTML_DIR, exist_ok=True)
URLS_FILE = os.path.join(DATA_DIR, 'urls.txt')

class ZonaPropScraper:
    def __init__(self):
        self.driver = self._init_driver()
        self.all_ad_urls = self._load_urls_from_file() 
        if self.all_ad_urls:
            logger.info(f"Se cargaron {len(self.all_ad_urls)} URLs desde el archivo {URLS_FILE}.")

    def _init_driver(self):
        logger.info("Inicializando undetected_chromedriver...")
        options = uc.ChromeOptions()
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
        try:
            driver = uc.Chrome(options=options, version_main=137)
            logger.info("WebDriver inicializado correctamente.")
            return driver
        except WebDriverException as e:
            logger.error(f"Error al inicializar WebDriver: {e}")
            return None

    def _save_html(self, html_content, filename):
        filepath = os.path.join(RAW_HTML_DIR, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"HTML guardado: {filename}")
        except IOError as e:
            logger.error(f"Error al guardar el archivo HTML {filename}: {e}")

    def _load_urls_from_file(self):
        if os.path.exists(URLS_FILE):
            with open(URLS_FILE, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def _save_urls_to_file(self):
        logger.info(f"Guardando {len(self.all_ad_urls)} URLs en {URLS_FILE}...")
        with open(URLS_FILE, 'w') as f:
            for url in sorted(list(self.all_ad_urls)):
                f.write(f"{url}\n")
    
    def collect_all_urls(self):
        if not self.driver: return False
        
        logger.info("--- INICIANDO FASE 1: Recolección de URLs ---")
        self.driver.get(BASE_URL_ZONAPROP)
        
        input("El script está en pausa. Resuelve el CAPTCHA si aparece y presiona [ENTER] para continuar...")
        logger.info("Pausa finalizada. Comenzando recolección.")
        
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-qa="cookies-policy-banner"]')))
            self.driver.execute_script("arguments[0].click();", cookie_button)
            logger.info("Banner de cookies aceptado.")
        except TimeoutException:
            logger.info("No se encontró el banner de cookies.")
        
        current_page = 1
        while current_page <= MAX_PAGES_TO_SCRAPE:
            logger.info(f"Recolectando de página de listado {current_page}...")
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/propiedades/clasificado/"]')))
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            ad_links = soup.select('a[href*="/propiedades/clasificado/"]')
            
            if not ad_links:
                logger.warning(f"No se encontraron más enlaces en la página {current_page}.")
                break
            
            page_urls = set()
            for link in ad_links:
                url = link.get('href')
                if url:
                    full_url = f"https://www.zonaprop.com.ar{url}" if not url.startswith('http') else url
                    page_urls.add(full_url)
            
            new_urls_found = len(page_urls - self.all_ad_urls)
            logger.info(f"Encontrados {len(page_urls)} URLs en esta página. {new_urls_found} son nuevas.")
            self.all_ad_urls.update(page_urls)

            try:
                next_page_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'a[data-qa="PAGING_NEXT"]')))
                next_page_url = next_page_button.get_attribute('href')
                if not next_page_url: break
                
                logger.info(f"Navegando directamente a la página siguiente: {next_page_url}")
                self.driver.get(next_page_url)
                current_page += 1
                random_delay()
            except Exception as e:
                logger.error(f"No se pudo navegar a la siguiente página: {e.__class__.__name__}. Fin de la recolección.")
                break
        
        self._save_urls_to_file()
        logger.info(f"--- FASE 1 COMPLETADA: Total de URLs únicas recolectadas: {len(self.all_ad_urls)} ---")
        return True
    
    def download_all_htmls(self):
        # ... (sin cambios)
        if not self.all_ad_urls: return
        logger.info(f"--- INICIANDO FASE 2: Descarga de HTML de {len(self.all_ad_urls)} Anuncios ---")
        downloaded_count = 0
        
        for i, url in enumerate(list(self.all_ad_urls)):
            logger.info(f"Procesando URL {i+1}/{len(self.all_ad_urls)}: {url}")
            try:
                url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
                filename = f"propiedad_{url_hash}.html"

                if os.path.exists(os.path.join(RAW_HTML_DIR, filename)):
                    logger.info(f"HTML para {url_hash[:8]}... ya existe. Saltando.")
                    continue

                self.driver.get(url)
                WebDriverWait(self.driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
                
                self._save_html(self.driver.page_source, filename)
                downloaded_count += 1
                random_delay()

            except Exception as e:
                logger.error(f"Error fatal al descargar la URL {url}: {e.__class__.__name__}")
        
        logger.info(f"--- FASE 2 COMPLETADA: Total de HTMLs descargados en esta sesión: {downloaded_count} ---")

    def run(self):
        if not self.driver:
            logger.error("WebDriver no se pudo inicializar. Abortando.")
            return
        
        try:
            # Siempre ejecuto la recolección. esto por si se cae la conexión.
            if self.collect_all_urls():
                # Si la recolección fue exitosa, procedemos a la descarga.
                self.download_all_htmls()
        except Exception as e:
            logger.critical(f"Ocurrió un error inesperado y fatal durante la ejecución: {e}", exc_info=True)
        finally:
            if self.driver:
                self.driver.quit()
                logger.info("WebDriver cerrado.")

if __name__ == "__main__":
    scraper = ZonaPropScraper()
    scraper.run()
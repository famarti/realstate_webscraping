import os
import json
import re
import base64
from bs4 import BeautifulSoup
import pandas as pd
import demjson3
from src.config import RAW_HTML_DIR, PROCESSED_DATA_DIR
from src.utils import setup_logging

logger = setup_logging()

def find_aviso_info_json(soup, filename):
    scripts = soup.find_all('script')
    for script in scripts:
        content = script.string
        if content and 'const avisoInfo = ' in content:
            url_map_of, map_lat_of, map_lng_of = None, None, None
            match_url = re.search(r'const\s+urlMapOf\s*=\s*"(.*?)"', content)
            if match_url: url_map_of = match_url.group(1)
            match_lat = re.search(r'const\s+mapLatOf\s*=\s*"(.*?)"', content)
            if match_lat: map_lat_of = match_lat.group(1)
            match_lng = re.search(r'const\s+mapLngOf\s*=\s*"(.*?)"', content)
            if match_lng: map_lng_of = match_lng.group(1)

            start_index = content.find('{', content.find('const avisoInfo = '))
            if start_index == -1: continue
            
            open_braces = 0
            for i, char in enumerate(content[start_index:]):
                if char == '{': open_braces += 1
                elif char == '}': open_braces -= 1
                if open_braces == 0:
                    end_index = start_index + i + 1
                    js_object_str = content[start_index:end_index]
                    if url_map_of: js_object_str = js_object_str.replace("'urlMap': urlMapOf", f"'urlMap': '{url_map_of}'")
                    if map_lat_of: js_object_str = js_object_str.replace("'mapLat': mapLatOf", f"'mapLat': '{map_lat_of}'")
                    if map_lng_of: js_object_str = js_object_str.replace("'mapLng': mapLngOf", f"'mapLng': '{map_lng_of}'")
                    try:
                        return demjson3.decode(js_object_str)
                    except demjson3.JSONDecodeError as e:
                        logger.error(f"Error al decodificar el objeto JS en {filename}: {e}")
                        return None
    return None

def find_antiquity(soup):
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            match = re.search(r"const\s+antiquity\s*=\s*'(.*?)'", script.string)
            if match:
                antiquity_text = match.group(1)
                days_match = re.search(r'\d+', antiquity_text)
                if days_match: return int(days_match.group(0))
    return None

def find_coordinates(soup):
    lat, lon = None, None
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            lat_match = re.search(r'const\s+mapLatOf\s*=\s*"(.*?)"', script.string)
            if lat_match:
                try: lat = base64.b64decode(lat_match.group(1)).decode('utf-8')
                except: pass
            lon_match = re.search(r'const\s+mapLngOf\s*=\s*"(.*?)"', script.string)
            if lon_match:
                try: lon = base64.b64decode(lon_match.group(1)).decode('utf-8')
                except: pass
        if lat and lon: return lat, lon
    return lat, lon

def parse_property_html(html_content, filename):
    if not html_content: return None
    soup = BeautifulSoup(html_content, 'html.parser')
    aviso_json = find_aviso_info_json(soup, filename)

    if not aviso_json:
        return None # Si no hay JSON, no podemos hacer nada, retornamos None

    data = {}
    data['origen_archivo'] = filename
    try: data['url_publicacion'] = soup.find('link', rel='canonical')['href']
    except: data['url_publicacion'] = 'URL no encontrada'
    
    data['tipo_propiedad'] = aviso_json.get('realEstateType', {}).get('name', 'Indeterminado')
    
    main_features = aviso_json.get('mainFeatures', {})
    data['sup_total'] = float(main_features.get('CFT100', {}).get('value', 0))
    data['sup_cubierta'] = float(main_features.get('CFT101', {}).get('value', 0))
    data['ambientes'] = int(main_features.get('CFT1', {}).get('value', 0))
    data['banos'] = int(main_features.get('CFT3', {}).get('value', 0))
    data['toilettes'] = int(main_features.get('CFT4', {}).get('value', 0))
    data['cocheras'] = int(main_features.get('CFT7', {}).get('value', 0))
    data['dormitorios'] = int(main_features.get('CFT2', {}).get('value', 0))
    
    try:
        antiquity_value = main_features.get('CFT5', {}).get('value', '0')
        data['antiguedad_anos'] = int(antiquity_value)
    except (ValueError, TypeError):
        # Si no se puede convertir a int (ej. es 'A estrenar'), asignamos 0.
        data['antiguedad_anos'] = 0

    data['dias_publicado'] = find_antiquity(soup)
    
    general_features = aviso_json.get('generalFeatures', {})
    caracteristicas = general_features.get('Características generales', {})
    ambientes_features = general_features.get('Ambientes', {})
    
    data['apto_credito'] = 1 if any(feat.get('label') == 'Apto crédito' for feat in caracteristicas.values()) else 0
    data['permite_mascotas'] = 1 if any(feat.get('label') == 'Permite mascotas' for feat in caracteristicas.values()) else 0
    data['apto_profesional'] = 1 if any(feat.get('label') == 'Apto profesional' for feat in caracteristicas.values()) else 0
    data['parrilla'] = 1 if any(feat.get('label') == 'Parrilla' for feat in caracteristicas.values()) else 0
    data['dormitorio_en_suite'] = 1 if any(feat.get('label') == 'Dormitorio en suite' for feat in ambientes_features.values()) else 0
    data['patio'] = 1 if any(feat.get('label') == 'Patio' for feat in ambientes_features.values()) else 0
    
    data['barrio'] = aviso_json.get('location', {}).get('name', 'N/A')
    data['direccion'] = aviso_json.get('address', {}).get('name', 'N/A')
    
    prices_data = aviso_json.get('pricesData', [{}])[0]
    price_info = prices_data.get('prices', [{}])[0]
    data['moneda'] = price_info.get('currency', 'N/A')
    data['precio'] = float(price_info.get('amount', 0))
    data['expensas'] = float(str(aviso_json.get('expenses', '0')).replace('.', '').replace(',', '.'))
    
    data['latitud'], data['longitud'] = find_coordinates(soup)
    
    description = aviso_json.get('description', '').lower()
    if data['parrilla'] == 0: data['parrilla'] = 1 if 'parrilla' in description else 0
    if data['patio'] == 0: data['patio'] = 1 if 'patio' in description else 0
    data['flag_terraza'] = 1 if 'terraza' in description else 0
    data['flag_quincho'] = 1 if 'quincho' in description else 0
    data['flag_luminoso'] = 1 if 'luminoso' in description else 0
    data['flag_sotano'] = 1 if 'sótano' in description or 'sotano' in description else 0
    data['flag_pileta'] = 1 if 'pileta' in description or 'piscina' in description else 0
    data['flag_lavadero'] = 1 if 'lavadero' in description else 0
    data['flag_subte'] = 1 if 'subte' in description else 0
    data['flag_a_reciclar'] = 1 if 'a reciclar' in description or 'reciclado' in description else 0
    
    return data

def main():
    logger.info("--- INICIANDO PROCESO DE PARSEO ---")
    html_files = [f for f in os.listdir(RAW_HTML_DIR) if f.endswith('.html')]
    if not html_files:
        logger.warning(f"No se encontraron archivos .html en: {RAW_HTML_DIR}")
        return

    # Pon 'False' para correr con todo.
    is_test_run = False 
    if is_test_run:
        logger.info("MODO PRUEBA: Se procesarán un máximo de 5 archivos.")
        html_files = html_files[:5]

    all_properties_data = []
    for i, filename in enumerate(html_files):
        logger.info(f"Procesando archivo {i+1}/{len(html_files)}: {filename}")
        filepath = os.path.join(RAW_HTML_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
            property_data = parse_property_html(html_content, filename)
            if property_data:
                all_properties_data.append(property_data)
        except Exception as e:
            logger.error(f"Error irrecuperable procesando {filename}: {e}", exc_info=True)
            continue

    if not all_properties_data:
        logger.error("No se pudo extraer información de ningún archivo.")
        return

    df = pd.DataFrame(all_properties_data)
    
    if is_test_run:
        logger.info("--- RESULTADO DE LA PRUEBA (DataFrame de Pandas) ---")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        print(df.head())
    
    output_filename = 'propiedades_procesado_PRUEBA.csv' if is_test_run else 'propiedades_procesado_FINAL.csv'
    output_path = os.path.join(PROCESSED_DATA_DIR, output_filename)
    df.to_csv(output_path, index=False, sep=';', encoding='utf-8-sig')
    logger.info(f"--- PROCESO COMPLETADO ---")
    logger.info(f"Datos guardados en: {output_path}")

if __name__ == "__main__":
    main()
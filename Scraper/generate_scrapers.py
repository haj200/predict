import json
import os
import shutil

def create_scraper_script(nature_id, nature_name):
    script = f'''import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- Configuration ---
MAX_WORKERS = 8
RETRIES = 3
TIMEOUT = 50
PAGE_SIZE = 50

BASE_URL = "https://www.marchespublics.gov.ma"
SEARCH_URL = BASE_URL + "/bdc/entreprise/consultation/resultat"

FIXED_URL_PART_1 = (
    "search_consultation_resultats%5Bkeyword%5D="
    "&search_consultation_resultats%5Breference%5D="
    "&search_consultation_resultats%5Bobjet%5D="
    "&search_consultation_resultats%5BdateLimitePublicationStart%5D="
    "&search_consultation_resultats%5BdateLimitePublicationEnd%5D="
    "&search_consultation_resultats%5BdateMiseEnLigneStart%5D="
    "&search_consultation_resultats%5BdateMiseEnLigneEnd%5D="
    "&search_consultation_resultats%5Bcategorie%5D="
)
FIXED_URL_PART_2 = (
    "&search_consultation_resultats%5Bacheteur%5D="
    "&search_consultation_resultats%5Bservice%5D="
    "&search_consultation_resultats%5BlieuExecution%5D="
    f"&search_consultation_resultats%5BpageSize%5D={{PAGE_SIZE}}"
)

headers = {{"User-Agent": "Mozilla/5.0"}}
session = requests.Session()
session.headers.update(headers)

# Création du dossier data s'il n'existe pas
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

NATURE_ID = "{nature_id}"  # ID spécifique à cette nature
NATURE_NAME = "{nature_name}"  # Nom de la nature

def get_max_page_for_nature():
    query = (
        f"{{FIXED_URL_PART_1}}"
        f"&search_consultation_resultats%5BnaturePrestation%5D={{NATURE_ID}}"
        f"{{FIXED_URL_PART_2}}"
    )
    url = f"{{SEARCH_URL}}?{{query}}"

    try:
        res = session.get(url, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')

        div_result = soup.find('div', class_='content__resultat')
        if div_result:
            text = div_result.get_text(strip=True)
            match = re.search(r'Nombre de résultats\\s*:\\s*(\\d+)', text)
            if match:
                total_results = int(match.group(1))
                max_pages = (total_results + PAGE_SIZE - 1) // PAGE_SIZE
                return max_pages, total_results
    except Exception as e:
        print(f"[get_max_page_for_nature] Erreur: {{e}}")

    return 1, 0

def extract_card_data(card):
    try:
        ref_element = card.select_one('.font-bold.table__links')
        reference = ref_element.text.strip().replace('Référence :', '').strip() if ref_element else None

        object_element = card.select_one('[data-bs-toggle="tooltip"]')
        obj = object_element.text.strip().replace('Objet :', '').strip() if object_element else None

        buyer_span = card.find('span', string=lambda s: s and "Acheteur" in s)
        buyer = buyer_span.parent.text.replace('Acheteur :', '').strip() if buyer_span else None

        date_span = card.find('span', string=lambda s: s and "Date de publication" in s)
        publication_date = date_span.parent.text.replace('Date de publication du résultat :', '').strip() if date_span else None

        number_of_quotes = None
        awarded = False
        awarded_company = None
        amount_ttc = None

        right_card = card.select_one('.entreprise__rightSubCard--top')
        if right_card:
            quotes_match = right_card.find(string=lambda s: s and "Nombre de devis reçus" in s)
            if quotes_match:
                quotes_span = right_card.select_one("span span.font-bold")
                if quotes_span:
                    number_of_quotes = quotes_span.text.strip()

            spans = right_card.find_all('span', recursive=False)

            def get_bold_text(span):
                b = span.find('span', class_='font-bold')
                return b.text.strip() if b else None

            if len(spans) >= 3:
                awarded_company = get_bold_text(spans[1])
                amount_ttc = get_bold_text(spans[2])
                awarded = awarded_company is not None

        return {{
            "reference": reference,
            "objet": obj,
            "acheteur": buyer,
            "date_publication": publication_date,
            "nombre_devis": number_of_quotes,
            "attribue": awarded,
            "entreprise_attributaire": awarded_company if awarded else None,
            "montant": amount_ttc if awarded else None
        }}
    except Exception as e:
        print(f"[extract_card_data] Erreur extraction carte: {{e}}")
        return None

def fetch_page(page):
    query = (
        f"{{FIXED_URL_PART_1}}"
        f"&search_consultation_resultats%5BnaturePrestation%5D={{NATURE_ID}}"
        f"{{FIXED_URL_PART_2}}"
        f"&search_consultation_resultats%5Bpage%5D={{page}}"
    )
    url = f"{{SEARCH_URL}}?{{query}}"

    for attempt in range(RETRIES):
        try:
            time.sleep(random.uniform(0.25, 0.35))
            res = session.get(url, timeout=TIMEOUT)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, 'lxml')
            cards = soup.select('.entreprise__card')
            return [extract_card_data(card) for card in cards if card]
        except requests.RequestException as e:
            print(f"[fetch_page] Tentative {{attempt+1}}/{{RETRIES}} Page {{page}} erreur: {{e}}")
            time.sleep(0.3)
    return []

def save_results(data):
    # Séparer les consultations attribuées et infructueuses
    attributed = [d for d in data if d and d['attribue']]
    infructuous = [d for d in data if d and not d['attribue']]

    # Sauvegarder les consultations attribuées
    if attributed:
        filepath = os.path.join(DATA_DIR, "attributed.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(attributed, f, ensure_ascii=False, indent=2)
        print(f"✅ {{len(attributed)}} consultations attribuées sauvegardées")

    # Sauvegarder les consultations infructueuses
    if infructuous:
        filepath = os.path.join(DATA_DIR, "infructuous.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(infructuous, f, ensure_ascii=False, indent=2)
        print(f"✅ {{len(infructuous)}} consultations infructueuses sauvegardées")

def main():
    query = (
        f"{{FIXED_URL_PART_1}}"
        f"&search_consultation_resultats%5BnaturePrestation%5D={{NATURE_ID}}"
        f"{{FIXED_URL_PART_2}}"
    )
    url = f"{{SEARCH_URL}}?{{query}}"
    
    print(f"Début extraction des consultations pour {{NATURE_NAME}}...")
    print(f"URL d'extraction: {{url}}")
    
    max_pages, total_results = get_max_page_for_nature()
    print(f"Nombre total de résultats: {{total_results}} ({{max_pages}} pages)")

    all_data = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {{
            executor.submit(fetch_page, page): page
            for page in range(1, max_pages + 1)
        }}
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Pages"):
            result = future.result()
            if result:
                all_data.extend(result)

    save_results(all_data)
    print("\\n✅ Extraction terminée, voir dossier 'data'")

if __name__ == "__main__":
    main()
'''
    return script

def create_readme(nature_id, nature_name):
    return f'''# Scraper pour {nature_name}

Ce script permet de scraper les consultations de la nature de prestation "{nature_name}" depuis le site des marchés publics du Maroc.

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

## Utilisation

1. Exécuter le script :
```bash
python scraper.py
```

Les données seront sauvegardées dans le dossier `data` :
- `attributed.json` : consultations attribuées
- `infructuous.json` : consultations infructueuses
'''

def create_requirements():
    return '''requests==2.31.0
beautifulsoup4==4.12.2
tqdm==4.66.1
lxml==4.9.3'''

def main():
    # Charger les natures depuis le fichier JSON
    try:
        with open('natures.json', 'r', encoding='utf-8') as f:
            natures = json.load(f)
    except FileNotFoundError:
        print("❌ Fichier natures.json non trouvé. Exécutez d'abord get_natures.py")
        return

    print(f"Génération des scrapers pour {len(natures)} natures...")

    # Pour chaque nature, créer un dossier et les fichiers nécessaires
    for nature_id, nature_name in natures.items():
        # Créer le dossier principal de la nature
        nature_dir = f"nature_{nature_id}"
        os.makedirs(nature_dir, exist_ok=True)

        # Créer le dossier scraper
        scraper_dir = os.path.join(nature_dir, 'scraper')
        os.makedirs(scraper_dir, exist_ok=True)

        # Créer le dossier data
        data_dir = os.path.join(scraper_dir, 'data')
        os.makedirs(data_dir, exist_ok=True)

        # Créer les fichiers
        # scraper.py
        with open(os.path.join(scraper_dir, 'scraper.py'), 'w', encoding='utf-8') as f:
            f.write(create_scraper_script(str(nature_id), nature_name))

        # README.md
        with open(os.path.join(scraper_dir, 'README.md'), 'w', encoding='utf-8') as f:
            f.write(create_readme(nature_dir, nature_name))

        # requirements.txt
        with open(os.path.join(scraper_dir, 'requirements.txt'), 'w', encoding='utf-8') as f:
            f.write(create_requirements())

        print(f"✅ Scraper généré pour nature_{nature_id} : {nature_name}")

    print("\n✅ Génération des scrapers terminée")

if __name__ == "__main__":
    main() 
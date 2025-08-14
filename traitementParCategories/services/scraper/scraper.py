import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# --- Configuration ---
MAX_WORKERS = 4  # Réduction du nombre de threads
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
    "&search_consultation_resultats%5Bcategorie%5D=3"
)
FIXED_URL_PART_2 = (
    "&search_consultation_resultats%5Bacheteur%5D="
    "&search_consultation_resultats%5Bservice%5D="
    "&search_consultation_resultats%5BlieuExecution%5D="
    f"&search_consultation_resultats%5BpageSize%5D={PAGE_SIZE}"
)

headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(headers)

# Création du dossier data s'il n'existe pas
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_max_page():
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BnaturePrestation%5D="
        f"{FIXED_URL_PART_2}"
    )
    url = f"{SEARCH_URL}?{query}"

    try:
        res = session.get(url, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')

        div_result = soup.find('div', class_='content__resultat')
        if div_result:
            text = div_result.get_text(strip=True)
            match = re.search(r'Nombre de résultats\s*:\s*(\d+)', text)
            if match:
                total_results = int(match.group(1))
                max_pages = (total_results + PAGE_SIZE - 1) // PAGE_SIZE
                return max_pages, total_results
    except Exception as e:
        print(f"[get_max_page] Erreur: {e}")

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

        return {
            "reference": reference,
            "objet": obj,
            "acheteur": buyer,
            "date_publication": publication_date,
            "nombre_devis": number_of_quotes,
            "attribue": awarded,
            "entreprise_attributaire": awarded_company if awarded else None,
            "montant": amount_ttc if awarded else None
        }
    except Exception as e:
        print(f"[extract_card_data] Erreur extraction carte: {e}")
        return None

def fetch_page(page):
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BnaturePrestation%5D="
        f"{FIXED_URL_PART_2}"
        f"&page={page}"
    )
    url = f"{SEARCH_URL}?{query}"

    for attempt in range(RETRIES):
        try:
            time.sleep(random.uniform(0.7, 1.2))  # Pause plus longue avant la requête
            res = session.get(url, timeout=TIMEOUT)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, 'lxml')
            cards = soup.select('.entreprise__card')
            return [extract_card_data(card) for card in cards if card]
        except requests.RequestException as e:
            print(f"[fetch_page] Tentative {attempt+1}/{RETRIES} Page {page} erreur: {e}")
            time.sleep(0.5)
    return []

def save_results(data):
    attributed = [d for d in data if d and d['attribue']]
    infructuous = [d for d in data if d and not d['attribue']]

    if attributed:
        filepath = os.path.join(DATA_DIR, "attributed.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(attributed, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(attributed)} consultations attribuées sauvegardées")

    if infructuous:
        filepath = os.path.join(DATA_DIR, "infructuous.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(infructuous, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(infructuous)} consultations infructueuses sauvegardées")

def main():
    print(f"📥 Début extraction des consultations pour les services ...")
    print(f"URL d'extraction: {SEARCH_URL}?{FIXED_URL_PART_1}&search_consultation_resultats%5BnaturePrestation%5D={FIXED_URL_PART_2}")

    max_pages, total_results = get_max_page()
    print(f"Nombre total de résultats: {total_results} ({max_pages} pages)")

    all_data = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_page, page): page
            for page in range(1, max_pages + 1)
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Pages"):
            result = future.result()
            if result:
                all_data.extend(result)
            time.sleep(random.uniform(0.5, 1.0))  # Pause entre chaque page traitée

    save_results(all_data)
    print("\n✅ Extraction terminée, voir dossier 'data'")

if __name__ == "__main__":
    main()

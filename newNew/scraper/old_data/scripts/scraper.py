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
MAX_WORKERS = 4
RETRIES = 20
TIMEOUT = 60
PAGE_SIZE = 10

BASE_URL = "https://www.marchespublics.gov.ma"
SEARCH_URL = BASE_URL + "/bdc/entreprise/consultation/resultat"

headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(headers)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

ATTRIB_FILE = os.path.join(DATA_DIR, "attributed.jsonl")
INFRUC_FILE = os.path.join(DATA_DIR, "infructuous.jsonl")


def get_max_page():
    url = f"{SEARCH_URL}"
    print(f"[INFO] URL d'extraction: {url}")
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
    url = f"{SEARCH_URL}?page={page}"

    for attempt in range(RETRIES):
        try:
            time.sleep(random.uniform(1.2, 2.2))
            res = session.get(url, timeout=TIMEOUT)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, 'lxml')
            cards = soup.select('.entreprise__card')
            data = [extract_card_data(card) for card in cards if card]
            return data
        except requests.RequestException as e:
            wait = min(2 ** attempt, 60)
            print(f"[fetch_page] Tentative {attempt+1}/{RETRIES} Page {page} erreur: {e} — nouvelle tentative dans {wait:.1f}s")
            time.sleep(wait)
    return []


def append_to_file(filepath, items):
    with open(filepath, 'a', encoding='utf-8') as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def process_and_save_page(page):
    data = fetch_page(page)
    attributed = [d for d in data if d and d['attribue']]
    infructuous = [d for d in data if d and not d['attribue']]

    if attributed:
        append_to_file(ATTRIB_FILE, attributed)
        print(f"📄 Page {page:03d} : {len(attributed)} attribuées ajoutées")

    if infructuous:
        append_to_file(INFRUC_FILE, infructuous)
        print(f"📄 Page {page:03d} : {len(infructuous)} infructueuses ajoutées")


def main():
    print(f"📥 Début extraction des bons de commande ...")

    # Nettoyage des anciens fichiers si existants
    if os.path.exists(ATTRIB_FILE):
        os.remove(ATTRIB_FILE)
    if os.path.exists(INFRUC_FILE):
        os.remove(INFRUC_FILE)

    max_pages, total_results = get_max_page()
    print(f"Nombre total de résultats: {total_results} ({max_pages} pages)")

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(process_and_save_page, page): page
            for page in range(1, max_pages + 1)
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Pages"):
            future.result()
            time.sleep(random.uniform(0.5, 1.5))

    print("\n✅ Extraction terminée. Fichiers générés :")
    print(f"➡ {ATTRIB_FILE}")
    print(f"➡ {INFRUC_FILE}")


if __name__ == "__main__":
    main()

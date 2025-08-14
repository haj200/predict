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
MAX_WORKERS = 8
MAX_NATURE_WORKERS = 4
RETRIES = 5
TIMEOUT = 80
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
    f"&search_consultation_resultats%5BpageSize%5D={PAGE_SIZE}"
)

headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(headers)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def get_max_page_for_nature(nature_id):
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BnaturePrestation%5D={nature_id}"
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
        print(f"[get_max_page_for_nature] Erreur: {e}")

    return 1, 0


def get_natures():
    try:
        res = session.get(SEARCH_URL, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        options = soup.select('#search_consultation_resultats_naturePrestation option')
        return {int(opt['value']): opt.text.strip() for opt in options if opt['value'].isdigit()}
    except Exception as e:
        print(f"[get_natures] Erreur: {e}")
        return {}


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


def fetch_nature_page(nature_id, page):
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BnaturePrestation%5D={nature_id}"
        f"{FIXED_URL_PART_2}"
        f"&page={page}"
    )
    url = f"{SEARCH_URL}?{query}"

    for attempt in range(RETRIES):
        try:
            time.sleep(random.uniform(0.25, 0.35))
            res = session.get(url, timeout=TIMEOUT)
            res.raise_for_status()

            soup = BeautifulSoup(res.text, 'lxml')
            cards = soup.select('.entreprise__card')
            return [extract_card_data(card) for card in cards if card]
        except requests.RequestException as e:
            print(f"[fetch_nature_page] Tentative {attempt+1}/{RETRIES} Nature {nature_id} Page {page} erreur: {e}")
            time.sleep(0.3)
    return []


def save_json_per_nature(nature_name, data):
    safe_name = nature_name.lower().replace(' ', '_').replace('/', '_').replace('-', '_')
    filepath = os.path.join(DATA_DIR, f"{safe_name}.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[save_json_per_nature] Sauvegardé {len(data)} consultations attribuées pour '{nature_name}'")


def save_infructuous_consultations(data):
    filepath = os.path.join(DATA_DIR, "infructueux.json")
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[save_infructuous_consultations] Sauvegardé {len(data)} consultations infructueuses")


def get_max_pages_all_natures():
    natures = get_natures()
    info = {}
    print("[get_max_pages_all_natures] Récupération des pages max pour toutes les natures...")
    for nid, name in natures.items():
        max_pages, total_results = get_max_page_for_nature(nid)
        print(f"Nature '{name}' (ID {nid}) -> Max pages: {max_pages}, Total résultats: {total_results}")
        info[nid] = {
            "name": name,
            "max_pages": max_pages,
            "total_results": total_results
        }
    return info


def process_nature_using_global_info(nid, nature_pages_info):
    nature_name = nature_pages_info[nid]["name"]
    max_pages = nature_pages_info[nid]["max_pages"]

    print(f"[process_nature_using_global_info] Traitement nature: {nature_name} (ID {nid}), {max_pages} pages")

    all_data = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(fetch_nature_page, nid, page): page
            for page in range(1, max_pages + 1)
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc=f"Pages {nature_name}"):
            result = future.result()
            if result:
                all_data.extend(result)

    attributed = [d for d in all_data if d and d['attribue']]
    infructuous = [d for d in all_data if d and not d['attribue']]

    if attributed:
        save_json_per_nature(nature_name, attributed)

    return infructuous


def main():
    print("[main] Début extraction des consultations...")

    nature_pages_info = get_max_pages_all_natures()

    all_infructuous = []

    with ThreadPoolExecutor(max_workers=MAX_NATURE_WORKERS) as executor:
        futures = {
            executor.submit(process_nature_using_global_info, nid, nature_pages_info): nid
            for nid in nature_pages_info.keys()
        }

        for future in tqdm(as_completed(futures), total=len(futures), desc="Traitement global natures"):
            infructuous_data = future.result()
            if infructuous_data:
                all_infructuous.extend(infructuous_data)

    save_infructuous_consultations(all_infructuous)

    print("\n✅ Extraction terminée, voir dossier 'data'")


if __name__ == "__main__":
    main()

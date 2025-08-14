import os
import json
import time
import random
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime

# --- Configuration ---
MAX_WORKERS = 8
MAX_NATURE_WORKERS = 4
RETRIES = 3
TIMEOUT = 50
PAGES_TO_FETCH = 10

BASE_URL = "https://www.marchespublics.gov.ma"
SEARCH_URL = f"{BASE_URL}/bdc/entreprise/consultation/resultat"

FIXED_URL_PART_1 = (
    "search_consultation_resultats%5Bkeyword%5D=&search_consultation_resultats%5Breference%5D="
    "&search_consultation_resultats%5Bobjet%5D=&search_consultation_resultats%5BdateLimitePublicationStart%5D="
    "&search_consultation_resultats%5BdateLimitePublicationEnd%5D=&search_consultation_resultats%5BdateMiseEnLigneStart%5D="
    "&search_consultation_resultats%5BdateMiseEnLigneEnd%5D=&search_consultation_resultats%5Bcategorie%5D="
)
FIXED_URL_PART_2 = (
    "&search_consultation_resultats%5Bacheteur%5D=&search_consultation_resultats%5Bservice%5D="
    "&search_consultation_resultats%5BlieuExecution%5D=&search_consultation_resultats%5BpageSize%5D=50"
)

HEADERS = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(HEADERS)


# --- Fonctions utilitaires ---

def get_natures():
    """Récupère la liste des natures de prestations disponibles."""
    resp = session.get(SEARCH_URL)
    soup = BeautifulSoup(resp.text, 'lxml')
    options = soup.select('#search_consultation_resultats_naturePrestation option')
    return {opt['value']: opt.text.strip() for opt in options if opt['value'].isdigit()}


def fetch_page(nature_id, page):
    """Récupère les résultats d'une page pour une nature spécifique, avec retry."""
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BnaturePrestation%5D={nature_id}"
        f"{FIXED_URL_PART_2}"
        f"&search_consultation_resultats%5Bpage%5D={page}"
    )
    url = f"{SEARCH_URL}?{query}"

    for attempt in range(RETRIES):
        try:
            time.sleep(random.uniform(0.25, 0.35))
            res = session.get(url, timeout=TIMEOUT)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'lxml')
                cards = soup.select('.entreprise__card')
                return [extract_card_data(card) for card in cards if card]
        except Exception as e:
            time.sleep(0.3)
    return []


def extract_card_data(card):
    """Extrait les données d'une carte de résultat."""
    try:
        ref = card.select_one('.font-bold.table__links')
        ref_text = ref.text.strip().replace('Référence :', '').strip() if ref else None

        objet_div = card.select_one('[data-bs-toggle="tooltip"]')
        objet_text = objet_div.text.strip().replace('Objet :', '').strip() if objet_div else None

        acheteur_span = card.find('span', string=lambda s: s and "Acheteur" in s)
        acheteur = acheteur_span.parent.text.replace('Acheteur :', '').strip() if acheteur_span else None

        date_span = card.find('span', string=lambda s: s and "Date de publication" in s)
        date_pub = date_span.parent.text.replace('Date de publication du résultat :', '').strip() if date_span else None

        right_card = card.select_one('.entreprise__rightSubCard--top')
        nombre_devis = entreprise_attributaire = montant_ttc = None
        attribue = False

        if right_card:
            devis_match = right_card.find(string=lambda s: s and "Nombre de devis reçus" in s)
            if devis_match:
                devis_span = right_card.select_one("span span.font-bold")
                nombre_devis = devis_span.text.strip() if devis_span else None

            spans = right_card.find_all('span', recursive=False)
            def get_bold(span):
                bold = span.find('span', class_='font-bold')
                return bold.text.strip() if bold else None

            if len(spans) >= 3:
                entreprise_attributaire = get_bold(spans[1])
                montant_ttc = get_bold(spans[2])
                attribue = entreprise_attributaire is not None

        return {
            "reference": ref_text,
            "objet": objet_text,
            "acheteur": acheteur,
            "date_publication": date_pub,
            "nombre_devis": nombre_devis,
            "attribue": attribue,
            "entreprise_attributaire": entreprise_attributaire if attribue else None,
            "montant": montant_ttc if attribue else None
        }
    except Exception as e:
        print(f"[Erreur carte] {e}")
        return None


def is_today(date_str):
    """Vérifie si la date donnée est aujourd'hui (heure ignorée)."""
    try:
        pub_date = datetime.strptime(date_str, "%d/%m/%Y")
        now = datetime.now()
        today_start = datetime(now.year, now.month, now.day)
        today_end = datetime(now.year, now.month, now.day, 23, 59, 59)
        return today_start <= pub_date <= today_end
    except Exception:
        return False


def process_nature(nature_id, nature_label):
    """Récupère et filtre les données d'une nature pour les pages spécifiées."""
    data = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(fetch_page, nature_id, page) for page in range(1, PAGES_TO_FETCH + 1)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                for entry in result:
                    if entry and entry["reference"] and is_today(entry["date_publication"]):
                        data.append(entry)
    return nature_label, data


def save_daily_data(nature_label, entries):
    """Sauvegarde les données extraites dans un fichier JSON, mise à jour ou ajout."""
    safe_name = nature_label.replace(" ", "").replace("/", "_").lower()
    data_dir = os.path.join("data")
    os.makedirs(data_dir, exist_ok=True)

    data_path = os.path.join(data_dir, f"{safe_name}.json")

    existing = {}
    if os.path.exists(data_path):
        with open(data_path, 'r', encoding='utf-8') as f:
            existing = {entry["reference"]: entry for entry in json.load(f)}

    new_entries_count = 0
    for entry in entries:
        if entry["reference"] not in existing:
            new_entries_count += 1
        existing[entry["reference"]] = entry

    with open(data_path, 'w', encoding='utf-8') as f:
        json.dump(list(existing.values()), f, ensure_ascii=False, indent=2)

    return new_entries_count


# --- Programme principal ---

def main():
    natures = get_natures()
    total_new_entries = 0

    with ThreadPoolExecutor(max_workers=MAX_NATURE_WORKERS) as executor:
        futures = {executor.submit(process_nature, nid, label): label for nid, label in natures.items()}

        for future in tqdm(as_completed(futures), total=len(futures), desc="Extraction journalière complète"):
            label, entries = future.result()
            new_count = save_daily_data(label, entries)
            total_new_entries += new_count

    print("\n📊 Statistiques du scraping quotidien:")
    print(f"📈 Total des nouveaux éléments récupérés: {total_new_entries}")
    print("\n✨ Extraction journalière complète terminée.")


if __name__ == "__main__":
    main()

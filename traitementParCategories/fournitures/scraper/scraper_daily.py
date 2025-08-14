import requests
from bs4 import BeautifulSoup
import time
import random
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from datetime import datetime, timedelta

# --- Configuration ---
NATURE_ID = 1
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
)
FIXED_URL_PART_2 = (
    "&search_consultation_resultats%5BdateMiseEnLigneStart%5D="
    "&search_consultation_resultats%5BdateMiseEnLigneEnd%5D="
    "&search_consultation_resultats%5Bcategorie%5D=2"
)
FIXED_URL_PART_3 = (
    "&search_consultation_resultats%5Bacheteur%5D="
    "&search_consultation_resultats%5Bservice%5D="
    "&search_consultation_resultats%5BlieuExecution%5D="
    f"&search_consultation_resultats%5BpageSize%5D={PAGE_SIZE}"
)

# Dossiers de sauvegarde
DAILY_DIR = "data_daily"
os.makedirs(DAILY_DIR, exist_ok=True)

headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(headers)


def convert_montant(montant_str):
    """Convertit une chaîne de montant en nombre flottant."""
    if not montant_str:
        return None
    
    # Supprimer les espaces et remplacer la virgule par un point
    montant_str = montant_str.replace(' ', '').replace(',', '.')
    
    # Extraire uniquement les chiffres et le point décimal
    match = re.search(r'([\d.]+)', montant_str)
    if not match:
        return None
        
    try:
        return float(match.group(1))
    except ValueError:
        return None

def clean_data(data):
    """Nettoie les données en gardant uniquement les champs requis et en convertissant le montant."""
    cleaned = []
    for item in data:
        if not item:
            continue
            
        cleaned_item = {
            "reference": item.get("reference"),
            "objet": item.get("objet"),
            "acheteur": item.get("acheteur"),
            "montant": convert_montant(item.get("montant"))
        }
        cleaned.append(cleaned_item)
    return cleaned


def get_max_page(date_str):
    """Retourne le nombre de pages et de résultats pour une date donnée."""
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    date_formattee = date_obj.strftime("%Y-%m-%d")
    print(date_formattee)
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BdateLimitePublicationStart%5D={date_formattee}&"
        f"search_consultation_resultats%5BdateLimitePublicationEnd%5D="
        f"{FIXED_URL_PART_2}"
        f"&search_consultation_resultats%5BnaturePrestation%5D="
        f"{FIXED_URL_PART_3}"
    )
    url = f"{SEARCH_URL}?{query}"
    try:
        res = session.get(url, timeout=TIMEOUT)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')

        div = soup.find('div', class_='content__resultat')
        if div:
            match = re.search(r'Nombre de résultats\s*:\s*(\d+)', div.get_text(strip=True))
            if match:
                total = int(match.group(1))
                pages = (total + PAGE_SIZE - 1) // PAGE_SIZE
                return pages, total
    except Exception as e:
        print(f"[get_max_page] Erreur: {e}")

    return 1, 0

def extract_card_data(card):
    """Extrait les données d'une carte de consultation."""
    try:
        ref = card.select_one('.font-bold.table__links')
        objet = card.select_one('[data-bs-toggle="tooltip"]')
        buyer = card.find('span', string=lambda s: s and "Acheteur" in s)
        pub_date = card.find('span', string=lambda s: s and "Date de publication" in s)

        reference = ref.text.strip().replace('Référence :', '') if ref else None
        obj = objet.text.strip().replace('Objet :', '') if objet else None
        acheteur = buyer.parent.text.replace('Acheteur :', '').strip() if buyer else None
        date_pub = pub_date.parent.text.replace('Date de publication du résultat :', '').strip() if pub_date else None

        # Bloc à droite de la carte
        right = card.select_one('.entreprise__rightSubCard--top')
        if right:
            devis = right.find(string=lambda s: "Nombre de devis reçus" in s)
            nombre_devis = right.select_one("span span.font-bold").text.strip() if devis else None

            spans = right.find_all('span', recursive=False)
            attribue = False
            entreprise = montant = None

            if len(spans) >= 3:
                entreprise = spans[1].find('span', class_='font-bold')
                montant = spans[2].find('span', class_='font-bold')
                entreprise = entreprise.text.strip() if entreprise else None
                montant = montant.text.strip() if montant else None
                attribue = entreprise is not None

            return {
                "reference": reference,
                "objet": obj,
                "acheteur": acheteur,
                "date_publication": date_pub,
                "nombre_devis": nombre_devis,
                "attribue": attribue,
                "entreprise_attributaire": entreprise if attribue else None,
                "montant": montant if attribue else None
            }
    except Exception as e:
        print(f"[extract_card_data] Erreur: {e}")
    return None

def fetch_page(page, date_str):
    """Récupère une page de résultats pour une date donnée."""
    date_obj = datetime.strptime(date_str, "%d/%m/%Y")
    date_formattee = date_obj.strftime("%Y-%m-%d")
    query = (
        f"{FIXED_URL_PART_1}"
        f"&search_consultation_resultats%5BdateLimitePublicationStart%5D={date_formattee}&"
        f"search_consultation_resultats%5BdateLimitePublicationEnd%5D="
        f"{FIXED_URL_PART_2}"
        f"&search_consultation_resultats%5BnaturePrestation%5D"
        f"{FIXED_URL_PART_3}"
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
            print(f"[fetch_page] Tentative {attempt+1}/{RETRIES} - Erreur page {page}: {e}")
            time.sleep(0.3)
    return []

def save_results(data, date_str):
    """Sauvegarde les résultats par type (attribués ou infructueux) et les données nettoyées."""
    
    attribues = [d for d in data if d and d['attribue']]
    
    # Sauvegarder les données brutes
    if attribues:
        path = os.path.join(DAILY_DIR, f"attributed_day_{date_str.replace('/', '-')}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(attribues, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(attribues)} consultations attribuées sauvegardées dans {path}")
    
    # Nettoyer et sauvegarder les données nettoyées
    if attribues:
        cleaned_data = clean_data(attribues)
        cleaned_path = os.path.join(DAILY_DIR, f"attributed_cleaned_day_{date_str.replace('/', '-')}.json")
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        print(f"🧹 {len(cleaned_data)} données nettoyées sauvegardées dans {cleaned_path}")

def main():
    today = datetime.now()
    # Calculate last Wednesday's date
    days_since_wednesday = (today.weekday() - 2 + 7) % 7 # Monday is 0, Wednesday is 2
    last_wednesday = today - timedelta(days=days_since_wednesday)
    
    current_date = last_wednesday

    while current_date <= today:
        date_str = current_date.strftime('%d/%m/%Y')
        print(f"\n📅 Scraping pour la date : {date_str}")
        print(f"📂 Nature de prestation : {NATURE_ID}")

        max_pages, total_results = get_max_page(date_str)
        print(f"🔍 {total_results} résultats trouvés sur {max_pages} pages.")

        all_data = []
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {
                executor.submit(fetch_page, page, date_str): page
                for page in range(1, max_pages + 1)
            }

            for future in tqdm(as_completed(futures), total=len(futures), desc=f"📄 Pages ({date_str})"):
                result = future.result()
                if result:
                    all_data.extend(result)
        print(f'📊 Total des données extraites pour {date_str} : {len(all_data)}')
        save_results(all_data, date_str)
        print(f"🎉 Extraction terminée pour {date_str}.")
        current_date += timedelta(days=1)

if __name__ == "__main__":
    main()

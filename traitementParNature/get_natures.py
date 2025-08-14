import requests
from bs4 import BeautifulSoup
import json
import os

# Configuration
BASE_URL = "https://www.marchespublics.gov.ma"
SEARCH_URL = BASE_URL + "/bdc/entreprise/consultation/resultat"

headers = {"User-Agent": "Mozilla/5.0"}
session = requests.Session()
session.headers.update(headers)

def get_natures():
    try:
        res = session.get(SEARCH_URL, timeout=50)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'lxml')
        options = soup.select('#search_consultation_resultats_naturePrestation option')
        return {f"nature_{opt['value']}": opt.text.strip() for opt in options if opt['value'].isdigit()}
    except Exception as e:
        print(f"[get_natures] Erreur: {e}")
        return {}

def save_natures_to_json(natures):
    with open('natures.json', 'w', encoding='utf-8') as f:
        json.dump(natures, f, ensure_ascii=False, indent=2)
    print(f"✅ {len(natures)} natures de prestation sauvegardées dans natures.json")

def main():
    print("Extraction des natures de prestation...")
    natures = get_natures()
    save_natures_to_json(natures)

if __name__ == "__main__":
    main() 
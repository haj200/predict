import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict
from string import punctuation
from nltk.corpus import stopwords

'''Ce script prend le json de la nouvelle data sans split par nature, chaque 
enregistrement contient les champs suivants; reference, nature, montant, text 
 en fait la prédiction et donne les résultats '''
# === PARAMÈTRES ===
DATA_FILE = "combined_data.jsonl"  # Fichier de la nouvelle data à prédire
NATURES_MAP_FILE = "natures.json"  # Mapping nature <-> id
RESULTS_DIR = "resultats_par_nature"  # Dossier des fichiers de mots-clés par nature
OUTPUT_RESULTS = "prediction_results.json"
OUTPUT_STATS = "prediction_stats.json"

STOPWORDS = set(stopwords.words('french'))

def normalize_text(text):
    text = text.lower()
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(rf"[{punctuation}]", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def extract_keywords(text):
    text = normalize_text(text)
    return set(mot for mot in text.split() if mot not in STOPWORDS and len(mot) > 2)

def parse_montant(montant_str):
    if montant_str is None:
        return None
    montant_str = str(montant_str).replace("MAD", "").replace(",", ".").replace(" ", "").strip()
    try:
        return float(montant_str)
    except Exception:
        return None

def interval_contains(interval_str, montant):
    try:
        min_, max_ = map(float, interval_str.split("-"))
        return min_ <= montant < max_
    except Exception:
        return False

# Charger le mapping des natures
with open(NATURES_MAP_FILE, "r", encoding="utf-8") as f:
    natures_map = json.load(f)

# Inverser le mapping id -> nature
id_to_nature = {v["id"]: k for k, v in natures_map.items()}

# Charger la data à prédire
with open(DATA_FILE, "r", encoding="utf-8") as f:
    data = [json.loads(line) for line in f if line.strip()]

detailed_results = []
stats_by_nature = defaultdict(lambda: {"total": 0, "correct": 0})

for elt in data:
    reference = elt.get("reference", "")
    nature = elt.get("nature", "")
    montant = parse_montant(elt.get("montant", ""))
    text = elt.get("text", "")

    # Trouver l'id de la nature
    nature_id = natures_map.get(nature, {}).get("id", None)
    if not nature_id:
        print(f"Nature inconnue : {nature}")
        continue

    # Charger les mots-clés par intervalle pour cette nature
    nature_file = Path(RESULTS_DIR) / f"{nature.replace(' ', '_').replace('/', '_')}.json"
    if not nature_file.exists():
        print(f"Fichier de mots-clés introuvable pour la nature : {nature}")
        continue

    with open(nature_file, "r", encoding="utf-8") as f:
        intervals_keywords = json.load(f)

    elt_keywords = extract_keywords(text)
    best_interval = None
    max_overlap = 0

    for interval, keywords in intervals_keywords.items():
        overlap = len(elt_keywords & set(keywords))
        if overlap > max_overlap:
            max_overlap = overlap
            best_interval = interval

    # Vérifier si la prédiction est correcte
    correct = False
    if best_interval and montant is not None:
        correct = interval_contains(best_interval, montant)

    stats_by_nature[nature]["total"] += 1
    if correct:
        stats_by_nature[nature]["correct"] += 1

    detailed_results.append({
        "reference": reference,
        "nature_id": nature_id,
        "nature": nature,
        "real_montant": montant,
        "predicted_interval": best_interval,
        "correct": correct
    })

# Sauvegarder les résultats détaillés
with open(OUTPUT_RESULTS, "w", encoding="utf-8") as f:
    json.dump(detailed_results, f, ensure_ascii=False, indent=2)

# Statistiques globales
stats = {
    nature: {
        "id": natures_map[nature]["id"],
        "total": vals["total"],
        "correct": vals["correct"],
        "accuracy_pct": round(vals["correct"] / vals["total"] * 100, 2) if vals["total"] else 0
    }
    for nature, vals in stats_by_nature.items()
}

with open(OUTPUT_STATS, "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"Résultats détaillés écrits dans {OUTPUT_RESULTS}")
print(f"Statistiques écrites dans {OUTPUT_STATS}")
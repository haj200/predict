import json
import re
import os
import spacy
from unidecode import unidecode

# Charger le modèle spaCy pour le français
nlp = spacy.load("fr_core_news_sm")
stop_words = set(nlp.Defaults.stop_words)

# 🔍 Fonction de nettoyage et lemmatisation améliorée

def normalize_text(text):
    """Minuscule + suppression des accents"""
    text = text.lower()
    text = unidecode(text)
    return text

def clean_and_lemmatize(text):
    # Supprimer les caractères spéciaux \r, \n, \t
    text = text.replace("\r", " ").replace("\n", " ").replace("\t", " ")

    # Supprimer les dates (comme 09/02/2024) et les années spécifiques (2023, 2024, 2025)
    text = re.sub(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', ' ', text)  # dates
    text = re.sub(r'\b(?:2023|2024|2025)\b', ' ', text)  # années ciblées

    # Supprimer les caractères / et -
    text = text.replace("/", " ").replace("-", " ")

    # Normaliser le texte (minuscule + suppression accents)
    text = normalize_text(text)

    # Traitement NLP avec spaCy
    doc = nlp(text)
    racines = [
        token.lemma_ for token in doc
        if token.lemma_ not in stop_words and token.is_alpha and len(token.lemma_) > 1
    ]
    return racines

# 💰 Fonction pour convertir un montant texte en float
def parse_montant(montant_str):
    montant_str = montant_str.replace("MAD", "").replace(",", ".").replace(" ", "")
    try:
        return float(montant_str)
    except ValueError:
        return None

# 🔢 Charger les intervalles depuis intervals.json
with open("../data/intervals.json", "r", encoding="utf-8") as f:
    interval_specs = json.load(f)

intervals = []
for spec in interval_specs:
    start = spec["min"]
    while start < spec["max"]:
        end = min(start + spec["step"], spec["max"])
        intervals.append((start, end))
        start = end

# 🔍 Trouver dans quel intervalle tombe un montant
def find_interval(montant):
    for min_val, max_val in intervals:
        if min_val <= montant < max_val:
            return (min_val, max_val)
    return None

# 🔁 Nouveau chemin absolu du dossier contenant les fichiers
data_dir = "C:/Users/pc/Desktop/NewData/data/natures"
output_dir = "C:/Users/pc/Desktop/NewData/data/lemmes_par_nature"
os.makedirs(output_dir, exist_ok=True)

# 🔀 Parcours des fichiers dans le bon dossier
for file in os.listdir(data_dir):
    if file.startswith("data_nature_") and file.endswith(".jsonl"):
        full_path = os.path.join(data_dir, file)

        with open(full_path, "r", encoding="utf-8") as f:
            data = [json.loads(line) for line in f if line.strip()]
            print(f"📂 {file} : {len(data)} lignes chargées")

        interval_texts = {}

        for item in data:
            montant = parse_montant(item.get("montant", ""))
            if montant is None:
                continue

            interval = find_interval(montant)
            if not interval:
                continue

            text = item.get("text", "")
            interval_texts.setdefault(interval, []).append(text)

        interval_lemmas = {}
        for interval, texts in interval_texts.items():
            full_text = " ".join(texts)
            lemmas = clean_and_lemmatize(full_text)

            if lemmas:
                key = f"{interval[0]}-{interval[1]}"
                interval_lemmas[key] = sorted(list(set(lemmas)))

        if interval_lemmas:
            out_file = os.path.join(output_dir, file.replace(".jsonl", "_lemmes.json"))
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(interval_lemmas, f, ensure_ascii=False, indent=2)

            print(f"✅ {file} → {len(interval_lemmas)} intervalles sauvegardés")
        else:
            print(f"⚠️ {file} → aucun mot lemmatisé")

import json
import os
from collections import defaultdict
import spacy
from unidecode import unidecode
import pandas as pd
from pathlib import Path

# Charger le modèle français de spaCy
nlp = spacy.load('fr_core_news_sm')

# Mots de liaison français à exclure
stop_words = set(nlp.Defaults.stop_words)

def normalize_text(text):
    # Convertir en minuscules et enlever les accents
    text = text.lower()
    text = unidecode(text)
    return text

def process_json_file(file_path):
    # Lire le fichier JSON
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Collecter tous les textes
    all_words = []
    
    # Traiter chaque objet
    for item in data:
        # Extraire le texte des champs pertinents (ajustez selon votre structure JSON)
        text_fields = []
        if isinstance(item, dict):
            # Récupérer toutes les valeurs textuelles
            for value in item.values():
                if isinstance(value, str):
                    text_fields.append(value)
        
        # Normaliser et traiter chaque texte
        for text in text_fields:
            # Normaliser
            text = normalize_text(text)
            
            # Traiter avec spaCy
            doc = nlp(text)
            
            # Lemmatiser et filtrer
            words = [token.lemma_ for token in doc 
                    if token.lemma_ not in stop_words 
                    and token.is_alpha 
                    and len(token.lemma_) > 1]
            
            all_words.extend(words)
    
    # Retourner les mots uniques de cette catégorie
    return sorted(set(all_words))

def main():
    # Chemin vers le dossier contenant les sous-dossiers de catégories
    data_root = Path('data_categories_5')
    for subdir in data_root.iterdir():
        if not subdir.is_dir():
            continue
        print(f"\nTraitement du dossier {subdir.name}...")
        results = {}
        # Traiter chaque fichier categorie_XX.json
        for file_path in subdir.glob('categorie_*.json'):
            category_name = file_path.stem
            print(f"  - Catégorie: {category_name}")
            words = process_json_file(file_path)
            results[category_name] = words
            print(f"    Nombre de mots: {len(words)}")
        # Sauvegarder les résultats dans le sous-dossier
        output_path = subdir / 'processed_categories.json'
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"  Résultats sauvegardés dans {output_path}")

if __name__ == "__main__":
    main() 
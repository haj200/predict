import json
import spacy
from unidecode import unidecode

# Charger le modèle spaCy français
nlp = spacy.load("fr_core_news_sm")
stop_words = set(nlp.Defaults.stop_words)

# Fonction pour charger les données d'une catégorie spécifique
def load_category_data(folder_number):
    base_path = f"data_categories_{folder_number}/achat_de_matériel_de_transport,_de_citernes_et_d'engins"
    
    # Charger les mots traités
    with open(f"{base_path}/processed_categories.json", "r", encoding="utf-8") as f:
        category_words = json.load(f)
    
    # Charger les marges de prix
    price_margins = {}
    try:
        with open(f"{base_path}/resume_categories.json", "r", encoding="utf-8") as f:
            resume = json.load(f)
            for category, stats in resume.items():
                min_amount = stats["min"]
                max_amount = stats["max"]
                price_margins[category] = f"{min_amount:,.2f} MAD - {max_amount:,.2f} MAD"
    except FileNotFoundError:
        print(f"Le fichier resume_categories.json n'a pas été trouvé pour le dossier {folder_number}")
        price_margins = {}
    
    return category_words, price_margins

# Fonction pour nettoyer et lemmatiser un texte
def preprocess(text):
    text = unidecode(text.lower())
    doc = nlp(text)
    return set([
        token.lemma_ for token in doc
        if token.is_alpha and token.lemma_ not in stop_words
    ])

# Fonction pour prédire la catégorie
def predict_category(new_text, category_words, price_margins):
    processed = preprocess(new_text)

    similarities = {}
    for category, words in category_words.items():
        common = processed.intersection(set(words))
        score = len(common)
        similarities[category] = score

    best_category = max(similarities, key=similarities.get)
    return best_category, similarities[best_category], price_margins.get(best_category)

# Exemple d'utilisation
if __name__ == "__main__":
    # Charger les données pour chaque dossier
    data_25 = load_category_data(25)
    data_30 = load_category_data(30)
    data_50 = load_category_data(50)
    
    print("Pour quitter le programme, tapez 'q' ou 'quit'")
    while True:
        nouveau_projet = input("\nEntrez la description du projet (q pour quitter) :\n> ")
        
        if nouveau_projet.lower() in ['q', 'quit']:
            print("Au revoir!")
            break
            
        if not nouveau_projet.strip():
            print("Veuillez entrer une description valide.")
            continue
        
        print("\nRésultats pour chaque jeu de données :")
        print("\n=== Données 25 ===")
        cat_25, score_25, marge_25 = predict_category(nouveau_projet, *data_25)
        print("Catégorie prédite :", cat_25)
        print("Score de similarité :", score_25)
        print("Marge de prix estimée :", marge_25)
        
        print("\n=== Données 30 ===")
        cat_30, score_30, marge_30 = predict_category(nouveau_projet, *data_30)
        print("Catégorie prédite :", cat_30)
        print("Score de similarité :", score_30)
        print("Marge de prix estimée :", marge_30)
        
        print("\n=== Données 50 ===")
        cat_50, score_50, marge_50 = predict_category(nouveau_projet, *data_50)
        print("Catégorie prédite :", cat_50)
        print("Score de similarité :", score_50)
        print("Marge de prix estimée :", marge_50)

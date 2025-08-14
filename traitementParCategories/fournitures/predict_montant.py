import json
import spacy
from unidecode import unidecode
from collections import Counter

# Charger le modèle spaCy pour le français
try:
    nlp = spacy.load('fr_core_news_sm')
except OSError:
    print("Le modèle spaCy 'fr_core_news_sm' n'est pas téléchargé. Exécutez : python -m spacy download fr_core_news_sm")
    exit()

# Mots vides à exclure
stop_words = set(nlp.Defaults.stop_words)

def normalize_text(text):
    """Minuscule + suppression des accents"""
    text = text.lower()
    text = unidecode(text)
    return text

def process_text(text):
    """Traite un texte avec spaCy et retourne les mots lemmatisés"""
    text = normalize_text(text)
    doc = nlp(text)
    
    # Lemmatisation + filtrage
    words = [token.lemma_ for token in doc
             if token.lemma_ not in stop_words
             and token.is_alpha
             and len(token.lemma_) > 1]
    
    return words

def predict_montant_by_similarity(user_text_words, montants_data):
    list_of_similarities = []

    user_word_count = Counter(user_text_words)
    user_word_set = set(user_text_words)

    for montant_str, details in montants_data.items():
        analysis_words = set(details['mots_uniques'])
        
        # Using Jaccard similarity
        intersection = len(user_word_set.intersection(analysis_words))
        union = len(user_word_set.union(analysis_words))
        
        similarity = 0
        if union > 0:
            similarity = intersection / union
        
        list_of_similarities.append((float(montant_str), similarity))
    
    # Sort by similarity in descending order and get the top 5
    list_of_similarities.sort(key=lambda x: x[1], reverse=True)
    
    return list_of_similarities[:5]

def main():
    montants_analysis_file = "data/montants_analysis.json"

    try:
        with open(montants_analysis_file, 'r', encoding='utf-8') as f:
            montants_data = json.load(f)
    except FileNotFoundError:
        print(f"Erreur: Le fichier '{montants_analysis_file}' n'a pas été trouvé. Assurez-vous qu'il est dans le bon répertoire.")
        return
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le fichier JSON '{montants_analysis_file}'. Vérifiez son format.")
        return

    print("\n--- Prédiction de Montant par Similarité ---")
    print("Entrez 'quit' pour quitter à tout moment.")

    while True:
        objet = input("Objet (ex: achat voiture): ")
        if objet.lower() == 'quit':
            break
        
        acheteur = input("Acheteur (ex: commune de ...): ")
        if acheteur.lower() == 'quit':
            break

        reference = input("Référence (ex: appel d'offre...): ")
        if reference.lower() == 'quit':
            break

        combined_input = f"{objet} {acheteur} {reference}"
        processed_input_words = process_text(combined_input)

        if not processed_input_words:
            print("Aucun mot significatif détecté dans votre entrée. Veuillez réessayer.")
            continue

        top_5_montants = predict_montant_by_similarity(processed_input_words, montants_data)

        if top_5_montants:
            print("\nTop 5 Montants prédits par similarité :")
            for montant, score in top_5_montants:
                print(f"- {montant:,.2f} MAD (Similarité Jaccard: {score:.4f})")
        else:
            print("Impossible de prédire le montant. Aucune correspondance trouvée.")
        print("------------------------------------------\n")

if __name__ == "__main__":
    main() 
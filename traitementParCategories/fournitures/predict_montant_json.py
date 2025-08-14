import json
import spacy
import requests
from unidecode import unidecode
from collections import Counter
import sys

# Charger le modèle spaCy pour le français
try:
    nlp = spacy.load('fr_core_news_sm')
except OSError:
    print("Le modèle spaCy 'fr_core_news_sm' n'est pas téléchargé. Exécutez : python -m spacy download fr_core_news_sm")
    exit()

# Mots vides à exclure
stop_words = set(nlp.Defaults.stop_words)

JSON_URL = "C:/Users/pc/MarchePub/traitementParCategories/fournitures/data_daily/attributed_day_cleaned.json" # REMPLACEZ CETTE URL AVEC VOTRE URL DE FICHIER JSON RÉEL

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
    
    # Sort by similarity in descending order and get the top 10
    list_of_similarities.sort(key=lambda x: x[1], reverse=True)
    
    return list_of_similarities[:10]

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

    print(f"\n--- Prédiction de Montant à partir de l'URL/Fichier: {JSON_URL} ---")
    try:
        if JSON_URL.startswith(('http://', 'https://')):
            response = requests.get(JSON_URL)
            response.raise_for_status() # Lève une exception pour les codes d'état HTTP d'erreur
            new_data = response.json()
        else:
            # Traiter comme un chemin de fichier local
            with open(JSON_URL, 'r', encoding='utf-8') as f:
                new_data = json.load(f)
    except requests.exceptions.RequestException as e:
        print(f"Erreur lors du téléchargement du fichier JSON depuis l'URL: {e}")
        return
    except FileNotFoundError:
        print(f"Erreur: Le fichier local '{JSON_URL}' n'a pas été trouvé.")
        return
    except json.JSONDecodeError:
        print(f"Erreur: Impossible de décoder le fichier JSON depuis '{JSON_URL}'. Vérifiez son format.")
        return

    results = []
    for i, entry in enumerate(new_data):
        objet = entry.get('objet', '')
        acheteur = entry.get('acheteur', '')
        reference = entry.get('reference', '')
        montant_reel = entry.get('montant_reel')
        if montant_reel is None:
            montant_reel = entry.get('montant')

        combined_input = f"{objet} {acheteur} {reference}"
        processed_input_words = process_text(combined_input)

        if not processed_input_words:
            print(f"Skipping entry {i+1}: Aucun mot significatif détecté dans l'entrée: {combined_input}")
            continue

        top_10_montants = predict_montant_by_similarity(processed_input_words, montants_data)

        if top_10_montants:
            predicted_montant = top_10_montants[0][0] # Prendre le meilleur montant prédit
            similarity_score = top_10_montants[0][1]
            result = {
                "objet": objet,
                "acheteur": acheteur,
                "reference": reference,
                "montant_reel": montant_reel,
                "montant_predit": predicted_montant,
                "similarite_jaccard": similarity_score,
                "top_10_predictions": [
                    {"montant": montant, "similarite": score} for montant, score in top_10_montants
                ]
            }
            if montant_reel is not None:
                error = abs(predicted_montant - montant_reel)
                result["erreur_absolue"] = error
                result["erreur_pourcentage"] = (error / montant_reel) * 100 if montant_reel != 0 else float('inf')
            results.append(result)
            print(f"\n--- Entrée {i+1} ---")
            print(f"Objet: {objet}")
            print(f"Acheteur: {acheteur}")
            print(f"Référence: {reference}")
            print(f"Montant Prédit: {predicted_montant:,.2f} MAD (Similarité Jaccard: {similarity_score:.4f})")
            if montant_reel is not None:
                print(f"Montant Réel: {montant_reel:,.2f} MAD")
                print(f"Erreur Absolue: {error:,.2f} MAD")
                if montant_reel != 0:
                    print(f"Erreur Pourcentage: {result['erreur_pourcentage']:.2f}%")
                else:
                    print("Erreur Pourcentage: Infini (Montant Réel est zéro)")
        else:
            print(f"Impossible de prédire le montant pour l'entrée {i+1}: {combined_input}")
    
    output_file_name = "prediction_results.json"
    with open(output_file_name, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=4)
    print(f"\nRésultats des prédictions enregistrés dans '{output_file_name}'")

    with open('prediction_results.json', 'r', encoding='utf-8') as f:
        results = json.load(f)

    total = 0
    bien_predits = 0

    for entry in results:
        montant_reel = entry.get('montant_reel')
        top_10 = entry.get('top_10_predictions', [])
        if montant_reel is not None and isinstance(montant_reel, (int, float)):
            total += 1
            for pred in top_10:
                montant = pred['montant']
                if montant_reel != 0:
                    erreur_pct = abs(montant - montant_reel) / montant_reel * 100
                    if erreur_pct < 50:
                        bien_predits += 1
                        break

    print(f"Nombre total d'éléments traités : {total}")
    print(f"Nombre d'éléments bien prédits (<50% d'erreur sur au moins une des 10 prédictions) : {bien_predits}")
    print(f"Pourcentage de bien prédits : {bien_predits/total*100:.2f}%")

if __name__ == "__main__":
    main() 
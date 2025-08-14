import json
import os
from collections import defaultdict
import spacy
from unidecode import unidecode

# Charger le modèle spaCy pour le français
nlp = spacy.load('fr_core_news_sm')

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

def analyze_montants():
    # Chemin vers le fichier attributed_cleaned.json
    json_file = "data/attributed_cleaned.json"
    output_file = "data/montants_analysis.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Dictionnaire pour stocker les informations par montant
        montants_info = defaultdict(lambda: {'words': set(), 'count': 0})
        
        # Regrouper les informations par montant
        for item in data:
            if 'montant' in item and item['montant'] is not None:
                montant = item['montant']
                
                # Concaténer les champs de texte
                texts = [
                    item.get('objet', ''),
                    item.get('acheteur', ''),
                    item.get('reference', '')
                ]
                combined_text = " ".join(text for text in texts if isinstance(text, str))
                
                # Traiter le texte et ajouter les mots au set
                words = process_text(combined_text)
                montants_info[montant]['words'].update(words)
                montants_info[montant]['count'] += 1
        
        # Convertir en format final pour le JSON
        result = {
            str(montant): {
                'montant': montant,
                'nombre_elements': info['count'],
                'mots_uniques': sorted(list(info['words']))  # Convertir le set en liste triée
            }
            for montant, info in montants_info.items()
        }
        
        # Sauvegarder les résultats dans un fichier JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            
        # Afficher les statistiques
        montants_uniques = sorted(montants_info.keys())
        
        print(f"Analyse des montants pour la nature {os.path.basename(os.getcwd())}")
        print(f"Nombre total de montants : {sum(info['count'] for info in montants_info.values())}")
        print(f"Nombre de montants uniques : {len(montants_uniques)}")
        print(f"Montant minimum : {min(montants_uniques):,.2f} MAD")
        print(f"Montant maximum : {max(montants_uniques):,.2f} MAD")
        
        print("\nListe des montants uniques triés:")
        for montant in montants_uniques:
            info = montants_info[montant]
            print(f"{montant:,.2f} MAD - {info['count']} éléments - {len(info['words'])} mots uniques")
            
        print(f"\nLes résultats détaillés ont été sauvegardés dans {output_file}")
            
    except FileNotFoundError:
        print(f"Le fichier {json_file} n'a pas été trouvé.")
    except json.JSONDecodeError:
        print(f"Erreur lors de la lecture du fichier JSON {json_file}")
    except Exception as e:
        print(f"Une erreur s'est produite : {str(e)}")

if __name__ == "__main__":
    analyze_montants()

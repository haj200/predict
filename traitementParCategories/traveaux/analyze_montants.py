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

def get_montant_range(montant, step=1000):
    start = int(montant // step) * step
    end = start + step - 1
    return f"{start}-{end}"

def analyze_montants():
    # Chemin vers le fichier attributed_cleaned.json
    json_file = "data/attributed_cleaned.json"
    output_file = "data/montants_analysis.json"
    step = 1000  # Taille de la fourchette
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Dictionnaire pour stocker les textes concaténés par fourchette de montant
        ranges_info = defaultdict(lambda: {'texts': [], 'count': 0})
        
        # Regrouper les informations par fourchette de montant
        for item in data:
            if 'montant' in item and item['montant'] is not None:
                montant = item['montant']
                montant_range = get_montant_range(montant, step)
                
                # Concaténer les champs de texte
                texts = [
                    item.get('objet', ''),
                    item.get('acheteur', ''),
                    item.get('reference', '')
                ]
                combined_text = " ".join(text for text in texts if isinstance(text, str))
                
                # Ajouter le texte à la fourchette
                ranges_info[montant_range]['texts'].append(combined_text)
                ranges_info[montant_range]['count'] += 1
        
        # Préparer le résultat final
        result = {}
        for montant_range, info in ranges_info.items():
            full_text = " ".join(info['texts'])
            words = process_text(full_text)
            result[montant_range] = {
                'range': montant_range,
                'nombre_elements': info['count'],
                'mots_uniques': sorted(list(set(words)))
            }
        
        # Sauvegarder les résultats dans un fichier JSON
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        # Afficher les statistiques
        montant_ranges_sorted = sorted(ranges_info.keys(), key=lambda x: int(x.split('-')[0]))
        print(f"Analyse des montants par fourchettes pour la nature {os.path.basename(os.getcwd())}")
        print(f"Nombre total d'éléments : {sum(info['count'] for info in ranges_info.values())}")
        print(f"Nombre de fourchettes uniques : {len(montant_ranges_sorted)}")
        print("\nListe des fourchettes triées:")
        for montant_range in montant_ranges_sorted:
            info = ranges_info[montant_range]
            mots = result[montant_range]['mots_uniques']
            print(f"{montant_range} MAD - {info['count']} éléments - {len(mots)} mots uniques")
        print(f"\nLes résultats détaillés ont été sauvegardés dans {output_file}")
        
    except FileNotFoundError:
        print(f"Le fichier {json_file} n'a pas été trouvé.")
    except json.JSONDecodeError:
        print(f"Erreur lors de la lecture du fichier JSON {json_file}")
    except Exception as e:
        print(f"Une erreur s'est produite : {str(e)}")

if __name__ == "__main__":
    analyze_montants()

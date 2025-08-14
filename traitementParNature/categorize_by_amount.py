

import json
import spacy
from unidecode import unidecode
from pathlib import Path
from collections import defaultdict, Counter
import math

# Charger le modèle spaCy pour le français
try:
    nlp = spacy.load('fr_core_news_sm')
except OSError:
    print("❌ Modèle spaCy 'fr_core_news_sm' non trouvé. Installation requise:")
    print("python -m spacy download fr_core_news_sm")
    exit(1)

# Mots vides à exclure
stop_words = set(nlp.Defaults.stop_words)

def normalize_text(text):
    """Minuscule + suppression des accents"""
    if not text:
        return ""
    text = text.lower()
    text = unidecode(text)
    return text

def process_text(text):
    """Traite un texte avec spaCy et retourne les mots lemmatisés"""
    if not text:
        return []
    text = normalize_text(text)
    doc = nlp(text)
    
    # Lemmatisation + filtrage
    words = [token.lemma_ for token in doc
             if token.lemma_ not in stop_words
             and token.is_alpha
             and len(token.lemma_) > 1]
    
    return words

def categorize_by_amount(nature_id, step=2000):
    """
    Catégorise les données par montant et extrait les mots significatifs
    """
    data_file = Path(f"nature_{nature_id}/data/attributed_cleaned.json")
    
    if not data_file.exists():
        print(f"❌ Fichier non trouvé: {data_file}")
        return None
    
    # Charger les données
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print(f"⚠️  Aucune donnée trouvée pour nature_{nature_id}")
        return None
    
    # Trouver le montant maximum
    max_amount = max(item.get('montant', 0) for item in data)
    
    # Créer les catégories de montant
    categories = defaultdict(list)
    
    for item in data:
        montant = item.get('montant', 0)
        if montant is None:
            continue
            
        # Calculer la catégorie
        category_start = math.floor(montant / step) * step
        category_end = category_start + step
        category_key = f"{category_start}-{category_end}"
        
        # Combiner les champs texte
        combined_text = f"{item.get('acheteur', '')} {item.get('reference', '')} {item.get('objet', '')}"
        
        categories[category_key].append({
            'montant': montant,
            'text': combined_text
        })
    
    # Traiter chaque catégorie
    results = {}
    
    for category, items in categories.items():
        if not items:  # Ignorer les catégories vides
            continue
            
        # Combiner tous les textes de la catégorie
        all_text = " ".join(item['text'] for item in items)
        
        # Extraire les mots significatifs
        words = process_text(all_text)
        
        # Compter les occurrences
        word_counts = Counter(words)
        
        # Prendre les mots les plus fréquents (top 20)
        top_words = word_counts.most_common(20)
        
        results[category] = {
            'count': len(items),
            'min_amount': min(item['montant'] for item in items),
            'max_amount': max(item['montant'] for item in items),
            'words': dict(top_words)
        }
    
    return results

def process_all_natures():
    """
    Traite toutes les natures et sauvegarde les résultats
    """
    base_dir = Path(".")
    all_results = {}
    
    print("🔍 Traitement des données par montant...")
    
    # Parcourir tous les dossiers nature_
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name.replace("nature_", "")
            
            print(f"📁 Traitement de nature_{nature_id}...")
            
            results = categorize_by_amount(nature_id)
            if results:
                all_results[nature_id] = results
                print(f"   ✅ {len(results)} catégories créées")
            else:
                print(f"   ⚠️  Aucun résultat pour nature_{nature_id}")
    
    # Sauvegarder les résultats
    output_file = "categorization_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Résultats sauvegardés dans {output_file}")
    
    # Afficher un résumé
    total_categories = sum(len(results) for results in all_results.values())
    total_natures = len(all_results)
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   📁 Natures traitées: {total_natures}")
    print(f"   📊 Catégories créées: {total_categories}")
    
    return all_results

if __name__ == "__main__":
    process_all_natures() 
import json
import spacy
from unidecode import unidecode
from pathlib import Path
from collections import defaultdict, Counter
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
    
    return " ".join(words)

def load_categorization_results():
    """Charge les résultats de catégorisation"""
    try:
        with open("categorization_results.json", 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Fichier categorization_results.json non trouvé. Exécutez d'abord categorize_by_amount.py")
        return None

def predict_amount_ranges_for_nature(nature_id, categorization_data):
    """
    Prédit les marges de montant pour une nature donnée
    """
    # Charger les données cleaned
    data_file = Path(f"nature_{nature_id}/data_daily/attributed_cleaned_day.json")
    
    if not data_file.exists():
        print(f"❌ Fichier non trouvé: {data_file}")
        return None
    
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if not data:
        print(f"⚠️  Aucune donnée trouvée pour nature_{nature_id}")
        return None
    
    # Récupérer les catégories pour cette nature
    nature_categories = categorization_data.get(nature_id, {})
    if not nature_categories:
        print(f"⚠️  Aucune catégorisation trouvée pour nature_{nature_id}")
        return None
    
    # Préparer les textes des catégories pour TF-IDF
    category_texts = []
    category_ranges = []
    
    for category_range, category_info in nature_categories.items():
        # Créer un texte représentatif de la catégorie basé sur les mots les plus fréquents
        words = list(category_info['words'].keys())
        category_text = " ".join(words * 3)  # Répéter pour plus de poids
        category_texts.append(category_text)
        category_ranges.append(category_range)
    
    # Vectoriser les catégories
    vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
    category_vectors = vectorizer.fit_transform(category_texts)
    
    # Traiter chaque élément
    predictions = []
    
    for item in data:
        montant_reel = item.get('montant', 0)
        if montant_reel is None:
            continue
        
        # Combiner les champs texte
        combined_text = f"{item.get('acheteur', '')} {item.get('reference', '')} {item.get('objet', '')}"
        processed_text = process_text(combined_text)
        
        # Vectoriser le texte de l'élément
        item_vector = vectorizer.transform([processed_text])
        
        # Calculer les similarités
        similarities = cosine_similarity(item_vector, category_vectors).flatten()
        
        # Obtenir les top 5 catégories les plus similaires
        top_indices = np.argsort(similarities)[::-1][:15]
        
        top_predictions = []
        for idx in top_indices:
            top_predictions.append({
                'range': category_ranges[idx],
                'similarity': float(similarities[idx]),
                'count': nature_categories[category_ranges[idx]]['count']
            })
        
        # Déterminer si le montant réel appartient à l'une des top 15 prédictions
        montant_reel_range = f"{math.floor(montant_reel / 2000) * 2000}-{math.floor(montant_reel / 2000) * 2000 + 2000}"
        correct_prediction = any(pred['range'] == montant_reel_range for pred in top_predictions)
        
        predictions.append({
            'reference': item.get('reference', ''),
            'montant_reel': montant_reel,
            'montant_reel_range': montant_reel_range,
            'top_15_predictions': top_predictions,
            'correct_prediction': correct_prediction
        })
    
    return predictions

def process_all_natures():
    """
    Traite toutes les natures et génère les prédictions
    """
    # Charger les résultats de catégorisation
    categorization_data = load_categorization_results()
    if not categorization_data:
        return
    
    base_dir = Path(".")
    all_statistics = {}
    total_processed = 0
    total_correct = 0
    
    print("🔍 Prédiction des marges de montant...")
    
    # Parcourir tous les dossiers nature_
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name.replace("nature_", "")
            
            print(f"📁 Traitement de nature_{nature_id}...")
            
            predictions = predict_amount_ranges_for_nature(nature_id, categorization_data)
            if predictions:
                # Sauvegarder les prédictions pour cette nature
                output_file = Path(f"nature_{nature_id}/predictions.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(predictions, f, ensure_ascii=False, indent=2)
                
                # Calculer les statistiques
                correct_count = sum(1 for pred in predictions if pred['correct_prediction'])
                total_count = len(predictions)
                
                all_statistics[nature_id] = {
                    'total_processed': total_count,
                    'correct_predictions': correct_count,
                    'accuracy': correct_count / total_count if total_count > 0 else 0
                }
                
                total_processed += total_count
                total_correct += correct_count
                
                print(f"   ✅ {total_count} éléments traités, {correct_count} prédictions correctes")
            else:
                print(f"   ⚠️  Aucun résultat pour nature_{nature_id}")
    
    # Sauvegarder les statistiques globales
    global_stats = {
        'total_elements_processed': total_processed,
        'total_correct_predictions': total_correct,
        'global_accuracy': total_correct / total_processed if total_processed > 0 else 0,
        'nature_statistics': all_statistics
    }
    
    with open("prediction_statistics.json", 'w', encoding='utf-8') as f:
        json.dump(global_stats, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Résultats sauvegardés:")
    print(f"   📁 Prédictions par nature: nature_X/predictions.json")
    print(f"   📊 Statistiques globales: prediction_statistics.json")
    
    print(f"\n📊 RÉSUMÉ GLOBAL:")
    print(f"   📈 Éléments traités: {total_processed:,}")
    print(f"   ✅ Prédictions correctes: {total_correct:,}")
    print(f"   🎯 Précision globale: {(total_correct / total_processed * 100):.1f}%" if total_processed > 0 else "   🎯 Précision globale: 0%")
    
    return global_stats

if __name__ == "__main__":
    process_all_natures() 
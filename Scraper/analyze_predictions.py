import json
import spacy
from unidecode import unidecode
import statistics
from pathlib import Path
import numpy as np

# Charger le modèle spaCy français
nlp = spacy.load("fr_core_news_sm")
stop_words = set(nlp.Defaults.stop_words)

def load_price_margins_json(summary_json_path):
    # Charger les marges de prix depuis le fichier de résumé JSON
    with open(summary_json_path, "r", encoding="utf-8") as f:
        summary = json.load(f)
    # Pour chaque catégorie, récupérer min et max
    price_stats = {}
    for cat, stats in summary.items():
        price_stats[cat] = {
            'mean': stats['mean'],
            'min': stats['min'],
            'max': stats['max']
        }
    return price_stats

def preprocess(text):
    text = unidecode(text.lower())
    doc = nlp(text)
    return set([
        token.lemma_ for token in doc
        if token.is_alpha and token.lemma_ not in stop_words
    ])

def predict_category(text, category_words):
    processed = preprocess(text)
    similarities = {}
    for category, words in category_words.items():
        common = processed.intersection(set(words))
        score = len(common)
        similarities[category] = score
    return max(similarities, key=similarities.get)

def analyze_predictions_for_file(cleaned_file, category_dir):
    # Charger les données nécessaires
    print(f"\nAnalyse pour {cleaned_file.name}...")
    with open(cleaned_file, "r", encoding="utf-8") as f:
        avis_attribues = json.load(f)
    processed_categories_path = category_dir / "processed_categories.json"
    with open(processed_categories_path, "r", encoding="utf-8") as f:
        category_words = json.load(f)
    summary_json_path = category_dir / "resume_categories.json"
    price_stats = load_price_margins_json(summary_json_path)
    # Préparer les structures pour l'analyse
    results = []
    errors = []
    error_percentages = []
    total_items = len(avis_attribues)
    # Préparer un tableau des montants pour recherche rapide
    all_amounts = [float(str(avis['montant']).replace(',', '.')) for avis in avis_attribues]
    for i, avis in enumerate(avis_attribues, 1):
        if i % 100 == 0:
            print(f"Progression: {i}/{total_items} ({i/total_items*100:.1f}%)")
        try:
            real_price = float(str(avis['montant']).replace(',', '.'))
            description = avis.get('objet', '') + ' ' + avis.get('description', '')
            predicted_category = predict_category(description, category_words)
            predicted_avg_price = price_stats[predicted_category]['mean']
            min_pred = price_stats[predicted_category]['min']
            max_pred = price_stats[predicted_category]['max']
            price_difference = abs(real_price - predicted_avg_price)
            error_percentage = (price_difference / real_price) * 100 if real_price else 0
            # Compter le nombre d'éléments dont le montant réel appartient à la marge prédite
            count_in_predicted_range = sum(1 for amt in all_amounts if min_pred <= amt <= max_pred)
            result = {
                'id': avis.get('id', 'N/A'),
                'real_price': real_price,
                'predicted_category': predicted_category,
                'predicted_avg_price': predicted_avg_price,
                'price_difference': price_difference,
                'error_percentage': error_percentage,
                'count_in_predicted_range': count_in_predicted_range,
                'predicted_min': min_pred,
                'predicted_max': max_pred
            }
            results.append(result)
            errors.append(price_difference)
            error_percentages.append(error_percentage)
        except (ValueError, KeyError, ZeroDivisionError) as e:
            print(f"Erreur avec l'avis {avis.get('id', 'N/A')}: {str(e)}")
            continue
    # Calculer les statistiques
    avg_error = statistics.mean(errors) if errors else 0
    median_error = statistics.median(errors) if errors else 0
    avg_error_percentage = statistics.mean(error_percentages) if error_percentages else 0
    median_error_percentage = statistics.median(error_percentages) if error_percentages else 0
    report = {
        'statistiques_globales': {
            'nombre_total_avis': len(results),
            'erreur_moyenne_mad': avg_error,
            'erreur_mediane_mad': median_error,
            'erreur_moyenne_pourcentage': avg_error_percentage,
            'erreur_mediane_pourcentage': median_error_percentage
        },
        'predictions_detaillees': results
    }
    output_file = category_dir / "analyse_predictions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  Résultats détaillés sauvegardés dans: {output_file}")
    print(f"  Nombre total d'avis analysés: {len(results)}")
    print(f"  Erreur moyenne: {avg_error:.2f} MAD ({avg_error_percentage:.1f}%)")
    print(f"  Erreur médiane: {median_error:.2f} MAD ({median_error_percentage:.1f}%)")
    return report

def main():
    data_cleaned_dir = Path("data_cleaned")
    data_categories_dir = Path("data_categories")
    global_results = {}
    for cleaned_file in data_cleaned_dir.glob("*.json"):
        base_name = cleaned_file.stem
        category_dir = data_categories_dir / base_name
        if not category_dir.exists():
            print(f"Dossier de catégories non trouvé pour {base_name}, ignoré.")
            continue
        # Vérifier la présence des fichiers nécessaires
        if not (category_dir / "processed_categories.json").exists() or not (category_dir / "resume_categories.json").exists():
            print(f"Fichiers de catégories manquants dans {category_dir}, ignoré.")
            continue
        report = analyze_predictions_for_file(cleaned_file, category_dir)
        global_results[base_name] = report
    # Sauvegarder le fichier global
    global_output_file = data_categories_dir / "analyse_predictions_global.json"
    with open(global_output_file, "w", encoding="utf-8") as f:
        json.dump(global_results, f, ensure_ascii=False, indent=2)
    print(f"\nFichier global sauvegardé dans: {global_output_file}")

if __name__ == "__main__":
    main() 
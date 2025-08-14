import json
import pandas as pd
from pathlib import Path

def analyze_error_percentages():
    data_categories_dir = Path('data_categories')
    global_stats = {}
    for subdir in data_categories_dir.iterdir():
        if not subdir.is_dir():
            continue
        result_file = subdir / 'analyse_predictions.json'
        summary_file = subdir / 'resume_categories.json'
        if not result_file.exists() or not summary_file.exists():
            continue
        print(f"\nAnalyse pour {subdir.name}:")
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            with open(summary_file, 'r', encoding='utf-8') as sf:
                summary = json.load(sf)
        except Exception as e:
            print(f"  Erreur de lecture: {e}")
            continue
        # Convertir la liste predictions_detaillees en DataFrame
        df = pd.DataFrame(data['predictions_detaillees'])
        # S'assurer que error_percentage est un nombre
        df['error_percentage'] = pd.to_numeric(df['error_percentage'], errors='coerce')
        # Calculer le nombre total d'éléments valides (sans les NaN)
        df_valid = df.dropna(subset=['error_percentage'])
        total_elements = len(df_valid)
        if total_elements == 0:
            print("  Aucun élément valide à analyser.")
            continue
        # Calculer le nombre d'éléments dont le montant réel appartient à la marge prédite
        all_amounts = df_valid['real_price'].tolist()
        count_in_predicted_range = 0
        for idx, row in df_valid.iterrows():
            pred_cat = row['predicted_category']
            min_pred = summary[pred_cat]['min']
            max_pred = summary[pred_cat]['max']
            real_price = row['real_price']
            if min_pred <= real_price <= max_pred:
                count_in_predicted_range += 1
        percent_in_predicted_range = (count_in_predicted_range / total_elements) * 100 if total_elements else 0
        # Calculer le nombre d'éléments pour chaque catégorie d'erreur
        less_than_10 = len(df_valid[df_valid['error_percentage'] <= 10])
        between_10_and_50 = len(df_valid[(df_valid['error_percentage'] > 10) & (df_valid['error_percentage'] <= 50)])
        percent_less_than_10 = (less_than_10 / total_elements) * 100
        percent_between_10_and_50 = (between_10_and_50 / total_elements) * 100
        # Afficher les résultats
        print(f"  Nombre total d'éléments valides: {total_elements}")
        print(f"  Nombre d'éléments avec montant réel dans la marge prédite: {count_in_predicted_range} ({percent_in_predicted_range:.2f}%)")
        print(f"  Éléments avec un pourcentage d'erreur ≤ 10%: {less_than_10} ({percent_less_than_10:.2f}%)")
        print(f"  Éléments avec un pourcentage d'erreur entre 10% et 50%: {between_10_and_50} ({percent_between_10_and_50:.2f}%)")
        # Ajouter aux stats globales
        global_stats[subdir.name] = {
            'total_elements': total_elements,
            'count_in_predicted_range': int(count_in_predicted_range),
            'percent_in_predicted_range': round(percent_in_predicted_range, 2),
            'less_than_10': less_than_10,
            'percent_less_than_10': round(percent_less_than_10, 2),
            'between_10_and_50': between_10_and_50,
            'percent_between_10_and_50': round(percent_between_10_and_50, 2)
        }
    # Sauvegarder le fichier global
    global_output_file = data_categories_dir / "analyse_error_percentages_global.json"
    with open(global_output_file, "w", encoding="utf-8") as f:
        json.dump(global_stats, f, ensure_ascii=False, indent=2)
    print(f"\nFichier global sauvegardé dans: {global_output_file}")

if __name__ == "__main__":
    analyze_error_percentages()
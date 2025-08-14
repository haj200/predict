import json
import os
import numpy as np
from pathlib import Path


def categorize_all_data():
    # Chemin vers le dossier data_cleaned
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_cleaned_dir = os.path.join(script_dir, 'data_cleaned')
    output_root_dir = os.path.join(script_dir, 'data_categories')
    os.makedirs(output_root_dir, exist_ok=True)

    # Trouver tous les fichiers JSON du dossier data_cleaned
    files = sorted([f for f in os.listdir(data_cleaned_dir) if f.endswith('.json')])
    if not files:
        print('Aucun fichier JSON trouvé dans data_cleaned.')
        return

    for file_name in files:
        input_file = os.path.join(data_cleaned_dir, file_name)
        print(f"\nTraitement du fichier : {input_file}")

        # Charger les données
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Extraire tous les montants pour calculer les percentiles
        amounts = [item['montant'] for item in data]
        if len(amounts) < 5:
            print(f"Pas assez de données pour 5 catégories dans {file_name} (seulement {len(amounts)} éléments).")
            continue

        # Calculer 19 points de division pour obtenir 20 groupes
        percentiles = [100/20 * i for i in range(1, 20)]  # 19 points de division
        thresholds = np.percentile(amounts, percentiles)

        # Initialiser les catégories
        categories = {}
        for i in range(20):  # 20 catégories
            categories[f'categorie_{i+1:02d}'] = []  # Format à 2 chiffres (01, 02, ...)

        # Catégoriser chaque élément
        for item in data:
            amount = item['montant']
            category_index = 0
            for i, threshold in enumerate(thresholds):
                if amount <= threshold:
                    category_index = i
                    break
                category_index = len(thresholds)  # last category (20th) if greater than all thresholds
            category_name = f'categorie_{category_index+1:02d}'
            categories[category_name].append(item)

        # Créer un sous-dossier de sortie pour ce fichier
        base_name = os.path.splitext(file_name)[0]
        output_dir = os.path.join(output_root_dir, base_name)
        os.makedirs(output_dir, exist_ok=True)

        # Créer un fichier de résumé texte et JSON
        summary_file_txt = os.path.join(output_dir, 'resume_categories.txt')
        summary_file_json = os.path.join(output_dir, 'resume_categories.json')
        summary_json = {}
        total_items = len(data)

        with open(summary_file_txt, 'w', encoding='utf-8') as sf:
            sf.write(f"Résumé de la répartition des données par catégorie pour {file_name}\n")
            sf.write("=" * 5 + "\n\n")
            for category, items in sorted(categories.items()):
                # Sauvegarder les données de la catégorie
                output_file = os.path.join(output_dir, f'{category}.json')
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(items, f, ensure_ascii=False, indent=2)
                percentage = (len(items) / total_items) * 100 if total_items else 0
                min_amount = min((item['montant'] for item in items), default=0)
                max_amount = max((item['montant'] for item in items), default=0)
                avg_amount = sum((item['montant'] for item in items)) / len(items) if items else 0
                print(f"\n{category}:")
                print(f"  - Nombre d'éléments: {len(items)} ({percentage:.1f}%)")
                print(f"  - Montant min: {min_amount:,.2f} MAD")
                print(f"  - Montant max: {max_amount:,.2f} MAD")
                print(f"  - Montant moyen: {avg_amount:,.2f} MAD")
                sf.write(f"{category}:\n")
                sf.write(f"  - Nombre d'éléments: {len(items)} ({percentage:.1f}%)\n")
                sf.write(f"  - Montant min: {min_amount:,.2f} MAD\n")
                sf.write(f"  - Montant max: {max_amount:,.2f} MAD\n")
                sf.write(f"  - Montant moyen: {avg_amount:,.2f} MAD\n")
                sf.write("-" * 5 + "\n\n")
                summary_json[category] = {
                    "count": len(items),
                    "percentage": round(percentage, 2),
                    "min": round(min_amount, 2),
                    "max": round(max_amount, 2),
                    "mean": round(avg_amount, 2)
                }
        with open(summary_file_json, 'w', encoding='utf-8') as jf:
            json.dump(summary_json, jf, ensure_ascii=False, indent=2)
        print(f"\nRésumé détaillé sauvegardé dans: {summary_file_txt}")
        print(f"Résumé JSON sauvegardé dans: {summary_file_json}")

if __name__ == '__main__':
    print("Début de la catégorisation des données...")
    categorize_all_data()
    print("\nCatégorisation terminée pour tous les fichiers!") 
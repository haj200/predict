import json
import sys
from pathlib import Path

def sort_by_predicted_range(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Trie les catégories selon le pourcentage d'éléments dans la range prédite
    sorted_items = sorted(data.items(), key=lambda x: x[1].get('percent_in_predicted_range', 0))
    sorted_dict = {k: v for k, v in sorted_items}
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sorted_dict, f, ensure_ascii=False, indent=2)
    print(f"Fichier trié sauvegardé dans : {output_path}")

if __name__ == "__main__":
    # Chemin par défaut
    default_input = r'C:\Users\pc\MarchePub\Scraper\data_categories\analyse_error_percentages_global.json'
    default_output = str(Path(default_input).with_name('sorted_by_predicted_range.json'))
    # Utilisation : python sort_by_predicted_range.py [input_json] [output_json]
    if len(sys.argv) < 2:
        input_json = default_input
        output_json = default_output
        print(f"Aucun argument fourni, utilisation du chemin par défaut :\n  Entrée : {input_json}\n  Sortie : {output_json}")
    else:
        input_json = sys.argv[1]
        if len(sys.argv) > 2:
            output_json = sys.argv[2]
        else:
            output_json = str(Path(input_json).with_name('sorted_by_predicted_range.json'))
    sort_by_predicted_range(input_json, output_json) 
import os
import json
from collections import defaultdict

nature_element_counts = defaultdict(int)
base_path = '.'  # Current directory

for root, dirs, files in os.walk(base_path):
    if 'attributed_cleaned.json' in files and os.path.basename(root) == 'data':
        # Check if the parent directory is a 'nature_X' directory
        parent_dir = os.path.basename(os.path.dirname(root))
        if parent_dir.startswith('nature_'):
            nature_number = parent_dir.replace('nature_', '')
            file_path = os.path.join(root, 'attributed_cleaned.json')
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        nature_element_counts[nature_number] += len(data)
            except json.JSONDecodeError:
                print(f"Erreur de décodage JSON pour le fichier: {file_path}")
            except Exception as e:
                print(f"Erreur lors du traitement du fichier {file_path}: {e}")

# Trier les natures par le nombre d'éléments en ordre décroissant
sorted_natures = sorted(nature_element_counts.items(), key=lambda item: item[1], reverse=True)

# Filtrer les natures ayant plus de 5 000 éléments
filtered_natures = [(nature, count) for nature, count in sorted_natures if count > 5000]

print("Natures ayant plus de 5 000 éléments dans 'attributed_cleaned.json':")
for i, (nature, count) in enumerate(filtered_natures):
    print(f"{i+1}. Nature {nature}: {count} éléments")

# Optionally, save the results to a JSON file
with open('natures_above_5000_elements.json', 'w', encoding='utf-8') as f:
    json.dump(dict(filtered_natures), f, indent=2, ensure_ascii=False) 
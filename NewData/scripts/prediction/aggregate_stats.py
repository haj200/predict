import os
import json

# Dossier contenant les fichiers de stats
stats_dir = "C:/Users/pc/MarchePub/NewData/data/prediction/prediction_results/new_data"

# Fichier de sortie
output_file = os.path.join(stats_dir, 'stats_globales.json')

# Dictionnaire global
global_stats = {}

# Parcours des fichiers de stats
for fname in os.listdir(stats_dir):
    if fname.startswith('stats_data_nature_') and fname.endswith('.json'):
        fpath = os.path.join(stats_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Chaque fichier a une seule clé : la nature
            for nature, stats in data.items():
                global_stats[nature] = stats

# Sauvegarde du fichier global
with open(output_file, 'w', encoding='utf-8') as f:
    json.dump(global_stats, f, ensure_ascii=False, indent=2)

print(f"✅ Statistiques globales agrégées dans {output_file} ({len(global_stats)} natures)") 
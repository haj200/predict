import json

# Charger les statistiques depuis le fichier JSON
with open('prediction_statistics.json', 'r', encoding='utf-8') as f:
    stats = json.load(f)

nature_stats = stats.get('nature_statistics', {})

# Extraire les natures avec une accuracy >= 0.5
high_accuracy = {
    nature: data
    for nature, data in nature_stats.items()
    if data.get('accuracy', 0) >= 0.5
}

# Afficher les résultats
print(f"Natures avec une accuracy >= 0.5 : {list(high_accuracy.keys())}")

# Sauvegarder dans un nouveau fichier JSON
with open('high_accuracy_natures.json', 'w', encoding='utf-8') as f:
    json.dump(high_accuracy, f, indent=2, ensure_ascii=False) 
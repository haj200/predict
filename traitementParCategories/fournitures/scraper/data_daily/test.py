import json

with open("prediction_results_day_cluster.json", "r", encoding="utf-8") as f:
    data = json.load(f)

results = data["results"]

# Compte des éléments bien prédits par au moins une des marges
count = sum(1 for elt in results if elt.get("in_10_90") or elt.get("in_25_75"))

print(f"Nombre d'éléments bien prédits par au moins une des marges : {count}")
print(f"Sur un total de : {len(results)}")
print(f"Pourcentage : {100*count/len(results):.2f}%")
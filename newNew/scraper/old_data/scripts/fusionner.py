import json
import re

# Fonction de nettoyage
def clean(text):
    if not isinstance(text, str):
        return ""
    # Supprimer espaces, # et :
    text = re.sub(r"^[\s#:]+|[\s#:]+$", "", text)
    # Normaliser la casse (majuscules ou minuscules selon ce que tu préfères)
    return text.strip().lower()


# Étape 1 : charger les doublons
with open("doublons.jsonl", "r", encoding="utf-8") as f:
    doublons_data = [json.loads(line) for line in f]

# Construire l'ensemble des clés de doublons
doublons_keys = {
    (
        d.get("reference", ""),
        d.get("objet", ""),
        d.get("acheteur", "")
    )
    for d in doublons_data
}

# Étape 2 : charger les données sources
with open("data/attributed.jsonl", "r", encoding="utf-8") as f:
    attributed_data = [json.loads(line) for line in f]

with open("data/consultations.ndjson", "r", encoding="utf-8") as f:
    consultations_data = [json.loads(line) for line in f]

# Étape 3 : indexation rapide des consultations
consultation_index = {
    (
        clean(c.get("référence", "")),
        clean(c.get("objet", "")),
        clean(c.get("acheteur", ""))
    ): c
    for c in consultations_data
}
# Étape 4 : fusion uniquement si pas doublon
merged_data = []

for attr in attributed_data:
    key = (
        clean(attr.get("reference", "")),
        clean(attr.get("objet", "")),
        clean(attr.get("acheteur", ""))
    )

    if key in doublons_keys:
        continue  # On saute cet élément car c’est un doublon

    consultation_match = consultation_index.get(key)
    if consultation_match:
        merged_item = {
            "reference": attr["reference"],
            "objet": attr['objet'],
            "acheteur": attr['acheteur'],
            "catégorie principale": consultation_match.get("catégorie", ""),
            "nature": consultation_match.get("nature", ""),
            "lieu": consultation_match.get("lieu", ""),
            "montant": attr.get("montant", ""),
            "articles" : consultation_match.get("articles", "")
        }
        merged_data.append(merged_item)

# Étape 5 : sauvegarde du fichier final
with open("merged_output_strict_montant.jsonl", "w", encoding="utf-8") as f:
    for item in merged_data:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"{len(merged_data)} éléments fusionnés (hors doublons) enregistrés dans merged_output_strict.jsonl")

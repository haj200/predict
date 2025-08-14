import json

# === CONFIGURATION ===
input_file = "cleaned_output.jsonl"   # ou .json
output_file = "donnees_nettoyees_extraites.jsonl"

def filtrer_donnees(donnees):
    extraits = []
    for item in donnees:
        nouveau = {
            "reference": item.get("reference"),
            "objet_nettoye": item.get("objet_nettoye"),
            "acheteur_nettoye": item.get("acheteur_nettoye"),
            "lieu_nettoye": item.get("lieu_nettoye"),
            "montant_num": item.get("montant_num"),
            "nature": item.get("nature"),
            "categorie": item.get("catégorie principale"),  # renommage
        }

        # Extraire les articles nettoyés
        articles = item.get("articles", [])
        articles_extraits = []
        for article in articles:
            titre = article.get("titre_nettoye")
            quantite = article.get("quantité_num")
            if titre is not None or quantite is not None:
                articles_extraits.append({
                    "titre_nettoye": titre,
                    "quantité_num": quantite
                })
        nouveau["articles"] = articles_extraits

        extraits.append(nouveau)
    return extraits

# === CHARGEMENT ===
donnees = []
with open(input_file, "r", encoding="utf-8") as f:
    for line in f:
        donnees.append(json.loads(line))

# === FILTRAGE ===
donnees_filtrees = filtrer_donnees(donnees)

# === SAUVEGARDE ===
with open(output_file, "w", encoding="utf-8") as f:
    for item in donnees_filtrees:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"{len(donnees_filtrees)} enregistrements filtrés écrits dans {output_file}")

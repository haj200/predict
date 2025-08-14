import json

input_file = "data.jsonl"  # à adapter si besoin
output_file = "combined_data.jsonl"

def get_field(d, key):
    # Gère les clés avec ou sans accents, minuscules/majuscules
    for k in d:
        if k.lower().replace("é", "e").replace("è", "e") == key.lower().replace("é", "e").replace("è", "e"):
            return d[k]
    return ""

with open(input_file, "r", encoding="utf-8") as fin, open(output_file, "w", encoding="utf-8") as fout:
    for line in fin:
        if not line.strip():
            continue
        data = json.loads(line)
        reference = get_field(data, "référence")
        objet = get_field(data, "objet")
        acheteur = get_field(data, "acheteur")
        lieu = get_field(data, "lieu")
        categorie = get_field(data, "catégorie")
        nature = get_field(data, "nature")
        montant = get_field(data, "montant")
        articles = data.get("articles", [])

        articles_text = []
        for art in articles:
            titre = get_field(art, "Titre")
            garanties = get_field(art, "Garanties")
            caracteristiques = get_field(art, "Caractéristiques")
            articles_text.append(f"{titre} {garanties} {caracteristiques}")

        text = " ".join([
            str(reference), str(objet), str(acheteur), str(lieu), str(categorie),
            " ".join(articles_text)
        ]).strip()

        out = {
            "reference": reference,
            "nature": nature,
            "montant": montant,
            "text": text
        }
        fout.write(json.dumps(out, ensure_ascii=False) + "\n")

print(f"Fichier écrit : {output_file}")
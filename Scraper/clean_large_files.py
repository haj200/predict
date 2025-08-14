import json
import os

def clean_amount(montant_str):
    if not montant_str:
        return None
    montant_str = montant_str.replace("MAD", "").replace(" ", "").replace(",", ".")
    try:
        return float(montant_str)
    except ValueError:
        return None


def process_large_files():
    data_dir = "data"
    output_dir = "data_cleaned"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(data_dir):
        if not filename.endswith('.json') or 'infructueux' in filename.lower():
            continue

        file_path = os.path.join(data_dir, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if not isinstance(data, list) or len(data) <= 900:
                continue

            cleaned = []
            for item in data:
                if all(k in item for k in ['montant', 'objet', 'acheteur', 'reference']):
                    montant = clean_amount(item['montant'])
                    objet = item['objet']
                    acheteur = item['acheteur']
                    reference = item['reference']

                    cleaned.append({
                        "montant": montant,
                        "objet": objet,
                        "acheteur": acheteur,
                        "reference": reference
                    })

            # Sauvegarde du fichier nettoyé
            output_path = os.path.join(output_dir, filename)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(cleaned, f, ensure_ascii=False, indent=2)

        except Exception:
            continue

if __name__ == "__main__":
    process_large_files()

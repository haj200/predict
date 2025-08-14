import json
import os
import re

def convert_montant(montant_str):
    """Convertit une chaîne de montant en nombre flottant."""
    if not montant_str:
        return None
    
    # Supprimer les espaces et remplacer la virgule par un point
    montant_str = montant_str.replace(' ', '').replace(',', '.')
    
    # Extraire uniquement les chiffres et le point décimal
    match = re.search(r'([\d.]+)', montant_str)
    if not match:
        return None
        
    try:
        return float(match.group(1))
    except ValueError:
        return None

def clean_data(data):
    """Nettoie les données en gardant uniquement les champs requis et en convertissant le montant."""
    cleaned = []
    for item in data:
        if not item:
            continue
            
        cleaned_item = {
            "reference": item.get("reference"),
            "objet": item.get("objet"),
            "acheteur": item.get("acheteur"),
            "montant": convert_montant(item.get("montant"))
        }
        cleaned.append(cleaned_item)
    return cleaned

def main():
    # Chemin vers le dossier data
    data_dir = "data"
    
   
    
    # Fichier source et destination
    source_file = os.path.join(data_dir, f"attributed.json")
    cleaned_file = os.path.join(data_dir, f"attributed_cleaned.json")
    
    if not os.path.exists(source_file):
        print(f"❌ Fichier source {source_file} non trouvé")
        return
        
    try:
        # Charger les données
        with open(source_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Nettoyer les données
        cleaned_data = clean_data(data)
        
        # Sauvegarder les données nettoyées
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            
        print(f"✅ Données nettoyées sauvegardées dans {cleaned_file}")
        print(f"📊 Nombre d'entrées traitées : {len(cleaned_data)}")
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage des données : {e}")

if __name__ == "__main__":
    main()


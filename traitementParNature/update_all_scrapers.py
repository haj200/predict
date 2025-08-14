 

import os
import shutil
from pathlib import Path
import json
import re

def update_scraper_daily(nature_id):
    """
    Met à jour le fichier scraper_daily.py pour une nature donnée
    """
    scraper_file = Path(f"nature_{nature_id}/scraper/scraper_daily.py")
    
    if not scraper_file.exists():
        print(f"⚠️  Fichier non trouvé: {scraper_file}")
        return False
    
    # Lire le contenu actuel
    with open(scraper_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Vérifier si le nettoyage est déjà présent
    if "convert_montant" in content:
        print(f"✅ nature_{nature_id}: Nettoyage déjà présent")
        return True
    
    # Ajouter les fonctions de nettoyage après les imports
    cleaning_functions = '''
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

'''
    
    # Trouver la position après les imports et avant get_max_page
    lines = content.split('\n')
    insert_position = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def get_max_page'):
            insert_position = i
            break
    
    if insert_position is None:
        print(f"❌ nature_{nature_id}: Impossible de trouver la position d'insertion")
        return False
    
    # Insérer les fonctions de nettoyage
    lines.insert(insert_position, cleaning_functions)
    
    # Modifier la fonction save_results
    save_results_start = None
    save_results_end = None
    
    for i, line in enumerate(lines):
        if line.strip().startswith('def save_results'):
            save_results_start = i
        elif save_results_start and line.strip().startswith('def '):
            save_results_end = i
            break
    
    if save_results_start is not None:
        # Nouvelle fonction save_results avec nettoyage
        new_save_results = '''def save_results(data, date_str):
    """Sauvegarde les résultats par type (attribués ou infructueux) et les données nettoyées."""
    
    attribues = [d for d in data if d and d['attribue']]
    
    # Sauvegarder les données brutes
    if attribues:
        path = os.path.join(DAILY_DIR, f"attributed_day.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(attribues, f, ensure_ascii=False, indent=2)
        print(f"✅ {len(attribues)} consultations attribuées sauvegardées dans {path}")
    
    # Nettoyer et sauvegarder les données nettoyées
    if attribues:
        cleaned_data = clean_data(attribues)
        cleaned_path = os.path.join(DAILY_DIR, f"attributed_cleaned_day.json")
        with open(cleaned_path, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        print(f"🧹 {len(cleaned_data)} données nettoyées sauvegardées dans {cleaned_path}")
'''
        
        # Remplacer la fonction save_results
        if save_results_end:
            lines[save_results_start:save_results_end] = new_save_results.split('\n')
        else:
            # Si on ne trouve pas la fin, remplacer jusqu'à la fin
            lines[save_results_start:] = new_save_results.split('\n')
    
    # Modifier la fonction main pour ajouter le message de nettoyage
    for i, line in enumerate(lines):
        if "print('🎉 Extraction terminée.')" in line:
            lines[i] = "    print('🎉 Extraction et nettoyage terminés.')"
        elif "print(all_data)" in line:
            lines[i] = "    print(f'📊 Total des données extraites : {len(all_data)}')"
    
    # Écrire le nouveau contenu
    new_content = '\n'.join(lines)
    
    # Sauvegarder le fichier modifié
    with open(scraper_file, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ nature_{nature_id}: Fichier mis à jour avec succès")
    return True

def main():
    """
    Met à jour tous les scraper_daily.py
    """
    base_dir = Path(".")
    updated_count = 0
    total_count = 0
    
    print("🔄 Mise à jour des scraper_daily.py...")
    
    # Parcourir tous les dossiers nature_
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name.replace("nature_", "")
            total_count += 1
            
            if update_scraper_daily(nature_id):
                updated_count += 1
    
    print(f"\n📊 RÉSUMÉ:")
    print(f"   📁 Total des natures: {total_count}")
    print(f"   ✅ Fichiers mis à jour: {updated_count}")
    print(f"   ⚠️  Fichiers non modifiés: {total_count - updated_count}")

if __name__ == "__main__":
    main() 
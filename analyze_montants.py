import os
import glob
import re

def extract_montants(file_content):
    # Regex pour extraire les montants
    pattern = r"Montant (?:min|max): ([\d,\.]+) MAD"
    montants = re.findall(pattern, file_content)
    # Convertir les montants en float, en gérant les séparateurs
    montants = [float(m.replace(',', '')) for m in montants]
    return montants

def analyze_montants():
    # Chemin vers les fichiers de résumé
    resume_files = glob.glob("Scraper/data_categories_*/*/resume_categories.txt")
    
    all_montants = set()  # Utiliser un set pour les montants uniques
    
    for file_path in resume_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                montants = extract_montants(content)
                all_montants.update(montants)
        except Exception as e:
            print(f"Erreur lors de la lecture de {file_path}: {e}")
    
    # Convertir le set en liste pour le tri
    montants_list = sorted(list(all_montants))
    
    print(f"Nombre total de montants uniques: {len(montants_list)}")
    print(f"Montant minimum: {min(montants_list):,.2f} MAD")
    print(f"Montant maximum: {max(montants_list):,.2f} MAD")
    
    print("\nListe des montants uniques triés:")
    for montant in montants_list:
        print(f"{montant:,.2f} MAD")

if __name__ == "__main__":
    analyze_montants() 
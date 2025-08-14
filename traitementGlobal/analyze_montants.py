import json
import os

def analyze_montants():
    # Chemin vers le fichier attributed_cleaned.json
    json_file = "avis_attribues_nettoyes.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Extraire tous les montants
        montants = [item['montant'] for item in data if 'montant' in item and item['montant'] is not None]
        
        if not montants:
            print("Aucun montant trouvé dans le fichier.")
            return
            
        # Convertir en set pour avoir les montants uniques, puis en liste pour le tri
        montants_uniques = sorted(list(set(montants)))
        
        print(f"Analyse des montants pour la nature {os.path.basename(os.getcwd())}")
        print(f"Nombre total de montants : {len(montants)}")
        print(f"Nombre de montants uniques : {len(montants_uniques)}")
        print(f"Montant minimum : {min(montants_uniques):,.2f} MAD")
        print(f"Montant maximum : {max(montants_uniques):,.2f} MAD")
        
        
        # print("\nListe des montants uniques triés:")
        # for montant in montants_uniques:
        #     print(f"{montant:,.2f} MAD")
            
    except FileNotFoundError:
        print(f"Le fichier {json_file} n'a pas été trouvé.")
    except json.JSONDecodeError:
        print(f"Erreur lors de la lecture du fichier JSON {json_file}")
    except Exception as e:
        print(f"Une erreur s'est produite : {str(e)}")

if __name__ == "__main__":
    analyze_montants()

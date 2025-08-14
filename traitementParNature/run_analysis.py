import os
import subprocess

def create_analysis_script(target_script):
    """Crée le script d'analyse des montants."""
    script_content = '''import json
import os

def analyze_montants():
    # Chemin vers le fichier attributed_cleaned.json
    json_file = "data/attributed_cleaned.json"
    
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
        
        print("\\nListe des montants uniques triés:")
        for montant in montants_uniques:
            print(f"{montant:,.2f} MAD")
            
    except FileNotFoundError:
        print(f"Le fichier {json_file} n'a pas été trouvé.")
    except json.JSONDecodeError:
        print(f"Erreur lors de la lecture du fichier JSON {json_file}")
    except Exception as e:
        print(f"Une erreur s'est produite : {str(e)}")

if __name__ == "__main__":
    analyze_montants()
'''
    with open(target_script, 'w', encoding='utf-8') as f:
        f.write(script_content)

def run_analysis():
    # Obtenir le chemin absolu du répertoire courant
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Parcourir tous les dossiers qui commencent par "nature_"
    for dirname in os.listdir(base_dir):
        if dirname.startswith("nature_"):
            nature_dir = os.path.join(base_dir, dirname)
            if os.path.isdir(nature_dir):
                # Créer le script d'analyse dans le dossier de la nature
                target_script = os.path.join(nature_dir, "analyze_montants.py")
                try:
                    create_analysis_script(target_script)
                    
                    print(f"\nAnalyse pour {dirname}:")
                    print("-" * 50)
                    
                    # Exécuter le script dans le dossier de la nature
                    subprocess.run(["python", target_script], cwd=nature_dir, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Erreur lors de l'exécution du script pour {dirname}: {str(e)}")
                except Exception as e:
                    print(f"Une erreur s'est produite pour {dirname}: {str(e)}")

if __name__ == "__main__":
    run_analysis() 
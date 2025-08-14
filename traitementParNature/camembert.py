import json
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sentence_transformers import SentenceTransformer
import numpy as np
import warnings

# Ignorer les avertissements
warnings.filterwarnings("ignore")

def evaluate_camembert_for_nature(nature_id, data_file):
    """
    Évalue le modèle CamemBERT + RandomForest pour une nature donnée
    """
    try:
        # Charger les données
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if not data:
            print(f"⚠️  Aucune donnée trouvée pour nature_{nature_id}")
            return None
        
        df = pd.DataFrame(data)
        
        # Filtrer les données avec montant valide
        df = df[df['montant'].notna() & (df['montant'] > 0)]
        
        if len(df) < 10:
            print(f"⚠️  Pas assez de données pour nature_{nature_id} (seulement {len(df)} entrées)")
            return None
        
        # Concaténer les champs textuels
        df["text"] = df["reference"].fillna("") + " " + df["objet"].fillna("") + " " + df["acheteur"].fillna("")
        
        # Séparer les variables
        X_text = df["text"].tolist()
        y = df["montant"].tolist()
        
        # Split train/test
        X_train_text, X_test_text, y_train, y_test = train_test_split(X_text, y, test_size=0.3, random_state=42)
        
        print(f"   🔄 Embedding des textes avec CamemBERT pour nature_{nature_id}...")
        
        # Charger CamemBERT depuis sentence-transformers
        model = SentenceTransformer("dangvantuan/sentence-camembert-large")
        
        # Embedding des textes
        X_train_embeddings = model.encode(X_train_text, show_progress_bar=False)
        X_test_embeddings = model.encode(X_test_text, show_progress_bar=False)
        
        # Modèle de régression
        reg = RandomForestRegressor(random_state=42)
        reg.fit(X_train_embeddings, y_train)
        
        # Prédictions
        y_pred = reg.predict(X_test_embeddings)
        
        # Évaluation
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
        
        # Calculer quelques statistiques supplémentaires
        mean_amount = np.mean(y)
        mae_percentage = (mae / mean_amount) * 100 if mean_amount > 0 else 0
        rmse_percentage = (rmse / mean_amount) * 100 if mean_amount > 0 else 0
        
        results = {
            "Nature_ID": nature_id,
            "Total_Data": len(df),
            "Train_Size": len(X_train_text),
            "Test_Size": len(X_test_text),
            "Mean_Amount": round(mean_amount, 2),
            "MAE": round(mae, 2),
            "RMSE": round(rmse, 2),
            "R2_Score": round(r2, 4),
            "MAE_Percentage": round(mae_percentage, 2),
            "RMSE_Percentage": round(rmse_percentage, 2),
            "Model": "CamemBERT + RandomForest"
        }
        
        print(f"   ✅ Résultats pour nature_{nature_id}:")
        print(f"      MAE: {mae:.2f} ({mae_percentage:.1f}%)")
        print(f"      RMSE: {rmse:.2f} ({rmse_percentage:.1f}%)")
        print(f"      R²: {r2:.4f}")
        
        return results
        
    except Exception as e:
        print(f"❌ Erreur pour nature_{nature_id}: {e}")
        return None

def process_all_natures():
    """
    Traite toutes les natures avec CamemBERT et génère les résultats
    """
    base_dir = Path(".")
    all_results = []
    processed_count = 0
    error_count = 0
    
    print("🔍 Évaluation CamemBERT + RandomForest pour toutes les natures...")
    print("⚠️  Cette opération peut prendre du temps à cause des embeddings...")
    
    # Parcourir tous les dossiers nature_
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name.replace("nature_", "")
            
            # Chercher le fichier attributed_cleaned.json
            data_file = item / "data" / "attributed_cleaned.json"
            
            if not data_file.exists():
                print(f"⚠️  Fichier non trouvé pour nature_{nature_id}: {data_file}")
                error_count += 1
                continue
            
            print(f"📁 Traitement de nature_{nature_id}...")
            
            # Évaluer CamemBERT pour cette nature
            results = evaluate_camembert_for_nature(nature_id, data_file)
            
            if results is not None:
                # Sauvegarder les résultats pour cette nature
                output_file = item / "camembert_results.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                
                # Ajouter à la liste globale
                all_results.append(results)
                processed_count += 1
                
                print(f"   💾 Résultats sauvegardés dans {output_file}")
            else:
                error_count += 1
    
    # Créer un résumé global
    if all_results:
        # Sauvegarder tous les résultats
        with open("all_camembert_results.json", 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        
        # Créer un DataFrame pour l'analyse
        results_df = pd.DataFrame(all_results)
        
        # Trier par RMSE (meilleur en premier)
        results_df_sorted = results_df.sort_values('RMSE')
        
        # Sauvegarder le résumé
        results_df_sorted.to_json("camembert_summary.json", orient="records", indent=2, force_ascii=False)
        
        print(f"\n✅ Résultats sauvegardés:")
        print(f"   📁 Résultats par nature: nature_X/camembert_results.json")
        print(f"   📊 Tous les résultats: all_camembert_results.json")
        print(f"   📈 Résumé trié: camembert_summary.json")
        
        print(f"\n📊 RÉSUMÉ GLOBAL:")
        print(f"   📁 Natures traitées: {processed_count}")
        print(f"   ❌ Erreurs: {error_count}")
        
        # Statistiques globales
        avg_mae = results_df['MAE'].mean()
        avg_rmse = results_df['RMSE'].mean()
        avg_r2 = results_df['R2_Score'].mean()
        
        print(f"   📊 Moyennes globales:")
        print(f"      MAE moyen: {avg_mae:.2f}")
        print(f"      RMSE moyen: {avg_rmse:.2f}")
        print(f"      R² moyen: {avg_r2:.4f}")
        
        # Top 5 des meilleures natures
        print(f"\n🏆 TOP 5 DES MEILLEURES NATURES:")
        for i, row in results_df_sorted.head().iterrows():
            print(f"   {i+1}. Nature {row['Nature_ID']}: RMSE={row['RMSE']:.2f}, R²={row['R2_Score']:.4f}, MAE={row['MAE']:.2f}")
        
        # Top 5 des pires natures
        print(f"\n⚠️  TOP 5 DES PIRE NATURES:")
        for i, row in results_df_sorted.tail().iterrows():
            print(f"   {i+1}. Nature {row['Nature_ID']}: RMSE={row['RMSE']:.2f}, R²={row['R2_Score']:.4f}, MAE={row['MAE']:.2f}")
    
    return all_results if all_results else None

if __name__ == "__main__":
    process_all_natures()

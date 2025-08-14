import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sentence_transformers import SentenceTransformer
from tpot import TPOTRegressor
import warnings

warnings.filterwarnings("ignore")

def evaluate_automl_for_nature(nature_id, data_file):
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not data:
            print(f"⚠️  Aucune donnée trouvée pour nature_{nature_id}")
            return None
        df = pd.DataFrame(data)
        df = df[df['montant'].notna() & (df['montant'] > 0)]
        if len(df) < 10:
            print(f"⚠️  Pas assez de données pour nature_{nature_id} (seulement {len(df)} entrées)")
            return None
        df["text"] = df["reference"].fillna("") + " " + df["objet"].fillna("") + " " + df["acheteur"].fillna("")
        X_text = df["text"].tolist()
        y = df["montant"].tolist()
        X_train_text, X_test_text, y_train, y_test = train_test_split(X_text, y, test_size=0.3, random_state=42)
        print(f"   🔄 Génération des embeddings CamemBERT pour nature_{nature_id}...")
        model = SentenceTransformer("dangvantuan/sentence-camembert-large")
        X_train_emb = model.encode(X_train_text, show_progress_bar=False)
        X_test_emb = model.encode(X_test_text, show_progress_bar=False)
        print("   🤖 Lancement de l'AutoML (TPOT)...")
        tpot = TPOTRegressor(generations=5, population_size=20, verbosity=2, random_state=42, max_time_mins=10)
        tpot.fit(X_train_emb, y_train)
        y_pred = tpot.predict(X_test_emb)
        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)
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
            "Model": "CamemBERT + TPOT"
        }
        print(f"   ✅ Résultats pour nature_{nature_id}:")
        print(f"      MAE: {mae:.2f} ({mae_percentage:.1f}%)")
        print(f"      RMSE: {rmse:.2f} ({rmse_percentage:.1f}%)")
        print(f"      R²: {r2:.4f}")
        # Export du meilleur pipeline
        pipeline_file = f"nature_{nature_id}/best_pipeline.py"
        tpot.export(pipeline_file)
        print(f"      💾 Pipeline exporté dans {pipeline_file}")
        return results
    except Exception as e:
        print(f"❌ Erreur pour nature_{nature_id}: {e}")
        return None

def process_all_natures():
    base_dir = Path(".")
    all_results = []
    processed_count = 0
    error_count = 0
    print("🔍 Évaluation AutoML (TPOT + CamemBERT) pour toutes les natures...")
    print("⚠️  Cette opération peut prendre du temps à cause des embeddings et de l'AutoML...")
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name.replace("nature_", "")
            data_file = item / "data" / "attributed_cleaned.json"
            if not data_file.exists():
                print(f"⚠️  Fichier non trouvé pour nature_{nature_id}: {data_file}")
                error_count += 1
                continue
            print(f"📁 Traitement de nature_{nature_id}...")
            results = evaluate_automl_for_nature(nature_id, data_file)
            if results is not None:
                output_file = item / "automl_results.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
                all_results.append(results)
                processed_count += 1
                print(f"   💾 Résultats sauvegardés dans {output_file}")
            else:
                error_count += 1
    if all_results:
        with open("all_automl_results.json", 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        results_df = pd.DataFrame(all_results)
        results_df_sorted = results_df.sort_values('RMSE')
        results_df_sorted.to_json("automl_summary.json", orient="records", indent=2, force_ascii=False)
        print(f"\n✅ Résultats sauvegardés:")
        print(f"   📁 Résultats par nature: nature_X/automl_results.json")
        print(f"   📊 Tous les résultats: all_automl_results.json")
        print(f"   📈 Résumé trié: automl_summary.json")
        print(f"\n📊 RÉSUMÉ GLOBAL:")
        print(f"   📁 Natures traitées: {processed_count}")
        print(f"   ❌ Erreurs: {error_count}")
        avg_mae = results_df['MAE'].mean()
        avg_rmse = results_df['RMSE'].mean()
        avg_r2 = results_df['R2_Score'].mean()
        print(f"   📊 Moyennes globales:")
        print(f"      MAE moyen: {avg_mae:.2f}")
        print(f"      RMSE moyen: {avg_rmse:.2f}")
        print(f"      R² moyen: {avg_r2:.4f}")
        print(f"\n🏆 TOP 5 DES MEILLEURES NATURES:")
        for i, row in results_df_sorted.head().iterrows():
            print(f"   {i+1}. Nature {row['Nature_ID']}: RMSE={row['RMSE']:.2f}, R²={row['R2_Score']:.4f}, MAE={row['MAE']:.2f}")
        print(f"\n⚠️  TOP 5 DES PIRE NATURES:")
        for i, row in results_df_sorted.tail().iterrows():
            print(f"   {i+1}. Nature {row['Nature_ID']}: RMSE={row['RMSE']:.2f}, R²={row['R2_Score']:.4f}, MAE={row['MAE']:.2f}")
    return all_results if all_results else None

if __name__ == "__main__":
    process_all_natures()

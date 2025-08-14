import json
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import warnings

# Ignorer les avertissements
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def evaluate_models_for_nature(nature_id, data_file):
    """
    Évalue tous les modèles de régression pour une nature donnée
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
        
        # Créer le champ textuel combiné
        df["text"] = df["reference"].fillna("") + " " + df["objet"].fillna("") + " " + df["acheteur"].fillna("")
        
        # Définir X et y
        X = df["text"]
        y = df["montant"]
        
        # Séparer les données
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
        
        # Définir les modèles
        models = {
            "Linear Regression": LinearRegression(),
            "Ridge Regression": Ridge(),
            "Lasso Regression": Lasso(),
            "Decision Tree": DecisionTreeRegressor(),
            "Random Forest": RandomForestRegressor(),
            "Gradient Boosting": GradientBoostingRegressor(),
            "Extra Trees": ExtraTreesRegressor(),
            "K-Nearest Neighbors": KNeighborsRegressor(n_neighbors=min(3, len(X_train))),
            "Support Vector Regressor": SVR(),
            "MLP Regressor": MLPRegressor(max_iter=500)
        }
        
        # TF-IDF vectorizer
        vectorizer = TfidfVectorizer(max_features=1000)
        
        # Évaluer chaque modèle
        results = []
        
        for name, model in models.items():
            pipeline = Pipeline([
                ("tfidf", vectorizer),
                ("regressor", model)
            ])
            try:
                pipeline.fit(X_train, y_train)
                y_pred = pipeline.predict(X_test)
                
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                r2 = r2_score(y_test, y_pred)
                
                results.append({
                    "Model": name,
                    "MAE": round(mae, 2),
                    "RMSE": round(rmse, 2),
                    "R² Score": round(r2, 4)
                })
            except Exception as e:
                results.append({
                    "Model": name,
                    "MAE": None,
                    "RMSE": None,
                    "R² Score": None,
                    "Error": str(e)
                })
        
        # Créer le DataFrame des résultats
        results_df = pd.DataFrame(results).sort_values(by="RMSE", na_position="last").reset_index(drop=True)
        
        # Ajouter des métadonnées
        results_df["Nature_ID"] = nature_id
        results_df["Total_Data"] = len(df)
        results_df["Train_Size"] = len(X_train)
        results_df["Test_Size"] = len(X_test)
        
        return results_df
        
    except Exception as e:
        print(f"❌ Erreur pour nature_{nature_id}: {e}")
        return None

def process_all_natures():
    """
    Traite toutes les natures et génère les résultats de régression
    """
    base_dir = Path(".")
    all_results = []
    processed_count = 0
    error_count = 0
    
    print("🔍 Évaluation des modèles de régression pour toutes les natures...")
    
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
            
            # Évaluer les modèles pour cette nature
            results_df = evaluate_models_for_nature(nature_id, data_file)
            
            if results_df is not None:
                # Sauvegarder les résultats pour cette nature
                output_file = item / "regression_results.json"
                results_df.to_json(output_file, orient="records", indent=2, force_ascii=False)
                
                # Ajouter à la liste globale
                all_results.append(results_df)
                processed_count += 1
                
                print(f"   ✅ {len(results_df)} modèles évalués, données sauvegardées")
                
                # Afficher le meilleur modèle
                best_model = results_df.iloc[0]
                print(f"   🏆 Meilleur modèle: {best_model['Model']} (RMSE: {best_model['RMSE']})")
            else:
                error_count += 1
    
    # Combiner tous les résultats
    if all_results:
        combined_results = pd.concat(all_results, ignore_index=True)
        
        # Sauvegarder les résultats combinés
        combined_results.to_json("all_regression_results.json", orient="records", indent=2, force_ascii=False)
        
        # Créer un résumé par nature
        summary = []
        for nature_id in combined_results["Nature_ID"].unique():
            nature_results = combined_results[combined_results["Nature_ID"] == nature_id]
            best_model = nature_results.iloc[0]
            summary.append({
                "Nature_ID": nature_id,
                "Best_Model": best_model["Model"],
                "Best_RMSE": best_model["RMSE"],
                "Best_R2": best_model["R² Score"],
                "Total_Data": best_model["Total_Data"]
            })
        
        summary_df = pd.DataFrame(summary).sort_values(by="Best_RMSE")
        summary_df.to_json("regression_summary.json", orient="records", indent=2, force_ascii=False)
        
        print(f"\n✅ Résultats sauvegardés:")
        print(f"   📁 Résultats par nature: nature_X/regression_results.json")
        print(f"   📊 Résultats combinés: all_regression_results.json")
        print(f"   📈 Résumé: regression_summary.json")
        
        print(f"\n📊 RÉSUMÉ GLOBAL:")
        print(f"   📁 Natures traitées: {processed_count}")
        print(f"   ❌ Erreurs: {error_count}")
        print(f"   🏆 Meilleur modèle global: {summary_df.iloc[0]['Best_Model']} (RMSE: {summary_df.iloc[0]['Best_RMSE']})")
        
        # Afficher le top 5 des meilleures natures
        print(f"\n🏆 TOP 5 DES MEILLEURES NATURES:")
        for i, row in summary_df.head().iterrows():
            print(f"   {i+1}. Nature {row['Nature_ID']}: {row['Best_Model']} (RMSE: {row['Best_RMSE']}, R²: {row['Best_R2']:.4f})")
    
    return combined_results if all_results else None

if __name__ == "__main__":
    process_all_natures()

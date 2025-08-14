import json
import pandas as pd
import numpy as np
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
import os
from datetime import datetime

# Ignorer les avertissements
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

def run_regression_comparison(data_path, category_name):
    """
    Exécute la comparaison de régression pour une catégorie donnée
    """
    print(f"\n=== Traitement de {category_name} ===")
    
    # Charger le JSON
    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"Données chargées: {len(data)} entrées")
    except Exception as e:
        print(f"Erreur lors du chargement de {data_path}: {e}")
        return None
    
    df = pd.DataFrame(data)
    
    # Vérifier que les colonnes nécessaires existent
    required_columns = ["reference", "objet", "acheteur", "montant"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"Colonnes manquantes dans {category_name}: {missing_columns}")
        return None
    
    # Créer le champ textuel combiné
    df["text"] = df["reference"] + " " + df["objet"] + " " + df["acheteur"]
    
    # Définir X et y
    X = df["text"]
    y = df["montant"]
    
    # Vérifier qu'il y a suffisamment de données
    if len(X) < 10:
        print(f"Pas assez de données pour {category_name}: {len(X)} entrées")
        return None
    
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
                "Category": category_name,
                "Model": name,
                "MAE": round(mae, 2),
                "RMSE": round(rmse, 2),
                "R² Score": round(r2, 4),
                "Data_Size": len(X)
            })
            print(f"  {name}: RMSE={round(rmse, 2)}, R²={round(r2, 4)}")
        except Exception as e:
            results.append({
                "Category": category_name,
                "Model": name,
                "MAE": None,
                "RMSE": None,
                "R² Score": None,
                "Data_Size": len(X),
                "Error": str(e)
            })
            print(f"  {name}: Erreur - {str(e)}")
    
    return results

def main():
    # Définir les chemins des fichiers
    data_files = {
        "Fournitures": "fournitures/data/attributed_cleaned.json",
        "Services": "services/data/attributed_cleaned.json", 
        "Travaux": "traveaux/data/attributed_cleaned.json"
    }
    
    all_results = []
    
    # Traiter chaque catégorie
    for category_name, data_path in data_files.items():
        if os.path.exists(data_path):
            results = run_regression_comparison(data_path, category_name)
            if results:
                all_results.extend(results)
        else:
            print(f"Fichier non trouvé: {data_path}")
    
    if all_results:
        # Créer le DataFrame final
        results_df = pd.DataFrame(all_results)
        
        # Trier par catégorie puis par RMSE
        results_df = results_df.sort_values(by=["Category", "RMSE"], na_position="last").reset_index(drop=True)
        
        # Afficher les résultats
        print("\n" + "="*80)
        print("RÉSULTATS COMPLETS DE LA COMPARAISON DE RÉGRESSION")
        print("="*80)
        print(results_df)
        
        # Sauvegarder les résultats
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"regression_comparison_results_{timestamp}.json"
        
        # Sauvegarder en JSON
        results_df.to_json(output_file, orient="records", indent=2, force_ascii=False)
        print(f"\nRésultats sauvegardés dans: {output_file}")
        
        # Sauvegarder en CSV
        csv_file = f"regression_comparison_results_{timestamp}.csv"
        results_df.to_csv(csv_file, index=False, encoding='utf-8')
        print(f"Résultats sauvegardés dans: {csv_file}")
        
        # Afficher un résumé par catégorie
        print("\n" + "="*80)
        print("RÉSUMÉ PAR CATÉGORIE")
        print("="*80)
        
        for category in results_df["Category"].unique():
            cat_results = results_df[results_df["Category"] == category]
            best_model = cat_results.loc[cat_results["RMSE"].idxmin()]
            print(f"\n{category}:")
            print(f"  Meilleur modèle: {best_model['Model']}")
            print(f"  RMSE: {best_model['RMSE']}")
            print(f"  R² Score: {best_model['R² Score']}")
            print(f"  Taille des données: {best_model['Data_Size']}")
    
    else:
        print("Aucun résultat obtenu. Vérifiez les fichiers de données.")

if __name__ == "__main__":
    main() 
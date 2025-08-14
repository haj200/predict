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

# Ignorer les avertissements
from sklearn.exceptions import ConvergenceWarning
warnings.filterwarnings("ignore", category=ConvergenceWarning)
warnings.filterwarnings("ignore", category=UserWarning)

# === Charger le JSON ===
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# === Créer le champ textuel combiné ===
df["text"] = df["reference"] + " " + df["objet"] + " " + df["acheteur"]

# === Définir X et y ===
X = df["text"]
y = df["montant"]

# === Séparer les données ===
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# === Définir les modèles ===
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

# === TF-IDF vectorizer ===
vectorizer = TfidfVectorizer(max_features=1000)

# === Évaluer chaque modèle ===
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

# === Affichage des résultats triés par RMSE ===
results_df = pd.DataFrame(results).sort_values(by="RMSE", na_position="last").reset_index(drop=True)
print(results_df)

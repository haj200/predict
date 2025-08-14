import json
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import numpy as np

# === 1. Charger les données ===
def load_data(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

# === 2. Préparation : fusion texte ===
def prepare(df):
    df = df.dropna(subset=["objet", "acheteur", "montant"])
    df["texte"] = df["objet"].astype(str) + " " + df["acheteur"].astype(str)
    return df

# === 3. TF-IDF ===
def vectorize_text(texts):
    vectorizer = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
    X = vectorizer.fit_transform(texts)
    return X, vectorizer

# === 4. Entraînement modèle et évaluation ===
def train_and_evaluate(name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"\n📈 Résultats pour {name}:")
    print(f"  - MAE  : {mean_absolute_error(y_test, y_pred):.2f}")
    
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print(f"  - RMSE : {rmse:.2f}")

    print(f"  - R²   : {r2_score(y_test, y_pred):.3f}")
    return model

# === 5. Prédire pour un nouvel enregistrement ===
def predict_new(model, vectorizer):
    while True:
        objet = input("\n📝 Entrez l'objet du marché (ou 'quit'): ")
        if objet.lower() == 'quit':
            break
        acheteur = input("🏢 Entrez le nom de l'acheteur : ")
        texte = objet + " " + acheteur
        vect = vectorizer.transform([texte])
        prediction = model.predict(vect)[0]
        print(f"💰 Montant prédit : {prediction:.2f} MAD")

# === 6. Script principal ===
if __name__ == "__main__":
    json_file = "../data/attributed_cleaned.json"  # Ton fichier JSON
    df = load_data(json_file)
    df = prepare(df)

    # Split
    X, vectorizer = vectorize_text(df["texte"])
    y = df["montant"]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Modèles
    xgb_model = XGBRegressor(n_estimators=300, learning_rate=0.1, max_depth=5, random_state=42)
    lgb_model = LGBMRegressor(n_estimators=300, learning_rate=0.1, min_gain_to_split=0.0, max_depth=5, random_state=42)

    # Entraîner et évaluer
    xgb_model = train_and_evaluate("XGBoost", xgb_model, X_train, X_test, y_train, y_test)
    lgb_model = train_and_evaluate("LightGBM", lgb_model, X_train, X_test, y_train, y_test)

    # Sauvegarder le meilleur
    print("\n💾 Sauvegarde des modèles et vectoriseur...")
    joblib.dump(xgb_model, "xgb_model.pkl")
    joblib.dump(lgb_model, "lgb_model.pkl")
    joblib.dump(vectorizer, "tfidf_vectorizer.pkl")
    print("✅ Sauvegarde terminée.")

    # Tester avec un nouveau
    print("\n🔍 Teste un nouvel enregistrement :")
    predict_new(xgb_model, vectorizer)
    predict_new(lgb_model, vectorizer)

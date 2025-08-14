import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sentence_transformers import SentenceTransformer
import joblib

# === 1. Charger les données ===
def load_data(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)

# === 2. Préparation : concatène objet + acheteur ===
def prepare(df):
    df = df.dropna(subset=["objet", "acheteur", "montant"])
    df["texte"] = df["objet"].astype(str) + " " + df["acheteur"].astype(str)
    return df

# === 3. Vectorisation par SentenceTransformer ===
def encode_texts(texts, model_name="paraphrase-multilingual-MiniLM-L12-v2"):
    model = SentenceTransformer(model_name)
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings, model

# === 4. Entraînement et évaluation ===
def train_and_evaluate(name, model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"\n📈 Résultats pour {name}:")
    print(f"  - MAE  : {mae:.2f}")
    print(f"  - RMSE : {rmse:.2f}")
    print(f"  - R²   : {r2:.3f}")
    return model, mae

# === 5. Prédire pour un nouvel enregistrement avec intervalle ===
def predict_new(model, embedder, mae, model_name):
    while True:
        objet = input(f"\n📝 [{model_name}] Entrez l'objet du marché (ou 'quit') : ")
        if objet.lower() == 'quit':
            break
        acheteur = input("🏢 Entrez le nom de l'acheteur : ")
        texte = objet + " " + acheteur
        vect = embedder.encode([texte])
        prediction = model.predict(vect)[0]
        print(f"💰 Montant prédit : {prediction:.2f} MAD")
        print(f"📊 Intervalle estimé : [{prediction - mae:.2f}, {prediction + mae:.2f}] MAD")

# === 6. Main ===
if __name__ == "__main__":
    json_path = "../data/attributed_cleaned.json"
    df = load_data(json_path)
    df = prepare(df)

    # Embedding
    X_embed, embedder = encode_texts(df["texte"])
    y = df["montant"]
    X_train, X_test, y_train, y_test = train_test_split(X_embed, y, test_size=0.2, random_state=42)

    # Modèles
    rf_model = RandomForestRegressor(n_estimators=200, random_state=42)
    gb_model = GradientBoostingRegressor(n_estimators=300, learning_rate=0.1, max_depth=5, random_state=42)

    # Entraînement & évaluation
    rf_model, rf_mae = train_and_evaluate("RandomForest", rf_model, X_train, X_test, y_train, y_test)
    gb_model, gb_mae = train_and_evaluate("GradientBoosting", gb_model, X_train, X_test, y_train, y_test)

    # Sauvegarde
    print("\n💾 Sauvegarde...")
    joblib.dump(rf_model, "rf_model.pkl")
    joblib.dump(gb_model, "gb_model.pkl")
    joblib.dump(embedder, "sentence_transformer.pkl")
    print("✅ Modèles sauvegardés.")

    # Tester
    print("\n🔍 Tester un nouveau texte :")
    predict_new(rf_model, embedder, rf_mae, "RandomForest")
    predict_new(gb_model, embedder, gb_mae, "GradientBoosting")

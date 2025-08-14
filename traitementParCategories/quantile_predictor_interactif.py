import os
import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from scipy.sparse import hstack, csr_matrix
import lightgbm as lgb
import joblib

# === 1. Fichiers à traiter ===
data_files = {
    "fournitures": "fournitures/data/attributed_cleaned.json",
    "services": "services/data/attributed_cleaned.json",
    "traveaux": "traveaux/data/attributed_cleaned.json"
}

MODELS_DIR = "models_lgb_quantile"
os.makedirs(MODELS_DIR, exist_ok=True)
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# === 2. Structures de stockage ===
category_models = {}
category_vectorizers = {}
category_embedder_name = {}

# === 3. Chargement du modèle d'embedding ===
print(f"🔄 Chargement du modèle SentenceTransformer: {EMBED_MODEL_NAME}")
model_embed = SentenceTransformer(EMBED_MODEL_NAME)

# === 4. Entraînement ou chargement des modèles ===
for cat, path in data_files.items():
    print(f"\n📂 Catégorie : {cat}")
    tfidf_path = os.path.join(MODELS_DIR, f"{cat}_tfidf.pkl")
    embed_name_path = os.path.join(MODELS_DIR, f"{cat}_embedder.txt")
    models_paths = {q: os.path.join(MODELS_DIR, f"{cat}_lgb_quantile_{int(q*100)}.pkl") for q in [0.1, 0.5, 0.9]}
    # Si tout existe, on recharge
    if os.path.exists(tfidf_path) and all(os.path.exists(p) for p in models_paths.values()) and os.path.exists(embed_name_path):
        print("  🔁 Chargement des modèles et TF-IDF depuis le disque...")
        tfidf = joblib.load(tfidf_path)
        models = {q: joblib.load(models_paths[q]) for q in models_paths}
        with open(embed_name_path, "r", encoding="utf-8") as f:
            embedder_name = f.read().strip()
        category_models[cat] = models
        category_vectorizers[cat] = tfidf
        category_embedder_name[cat] = embedder_name
        print(f"  ✅ Modèles chargés pour {cat}.")
        continue
    # Sinon, entraîner et sauvegarder
    if not os.path.exists(path):
        print(f"❌ Fichier non trouvé: {path}")
        continue
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    df = pd.DataFrame(data)
    if not all(col in df.columns for col in ["objet", "acheteur", "montant"]):
        print(f"❌ Colonnes manquantes dans {cat}")
        continue
    df["texte_complet"] = df["objet"].astype(str) + " " + df["acheteur"].astype(str)
    # Embeddings batchés
    print("  → Génération des embeddings (batch)...")
    embed_matrix = model_embed.encode(df["texte_complet"].tolist(), batch_size=128, show_progress_bar=True)
    # TF-IDF
    print("  → Vectorisation TF-IDF...")
    tfidf = TfidfVectorizer()
    tfidf_matrix = tfidf.fit_transform(df["texte_complet"])
    # Fusion
    X = hstack([csr_matrix(embed_matrix), tfidf_matrix])
    y = df["montant"].values
    # Découpage train/test (optionnel, ici on entraîne sur tout)
    X_train, y_train = X, y
    # Entraînement des modèles quantiles LightGBM
    print("  ⚙️ Entraînement des modèles LightGBM (quantile)...")
    quantiles = [0.1, 0.5, 0.9]
    models = {}
    for q in quantiles:
        print(f"    ➤ Apprentissage pour quantile {q}...")
        params = {
            "objective": "quantile",
            "alpha": q,
            "n_estimators": 200,
            "learning_rate": 0.05,
            "n_jobs": -1,
            "verbosity": -1
        }
        model = lgb.LGBMRegressor(**params)
        model.fit(X_train, y_train)
        models[q] = model
        joblib.dump(model, models_paths[q])
    # Sauvegarde du vectorizer et du nom du modèle d'embedding
    joblib.dump(tfidf, tfidf_path)
    with open(embed_name_path, "w", encoding="utf-8") as f:
        f.write(EMBED_MODEL_NAME)
    # Stockage en mémoire
    category_models[cat] = models
    category_vectorizers[cat] = tfidf
    category_embedder_name[cat] = EMBED_MODEL_NAME
    print(f"  ✅ Modèles entraînés et sauvegardés pour {cat}.")

# === 5. Prédiction interactive ===
def predict_interval(cat, objet, acheteur):
    tfidf = category_vectorizers[cat]
    models = category_models[cat]
    texte = objet + " " + acheteur
    embed = model_embed.encode([texte])
    tfidf_vec = tfidf.transform([texte])
    input_vec = hstack([csr_matrix(embed), tfidf_vec])
    result = {}
    for q in models:
        result[f"q{int(q*100)}"] = round(models[q].predict(input_vec)[0], 2)
    return result

print("\n=== Prédiction interactive ===")
print("Catégories disponibles :")
for i, cat in enumerate(category_models.keys()):
    print(f"  {i+1}. {cat}")

while True:
    cat_input = input("\nChoisissez la catégorie (nom ou numéro, 'quit' pour sortir) : ").strip()
    if cat_input.lower() == 'quit':
        break
    # Résolution du nom/numéro
    if cat_input.isdigit():
        cat_list = list(category_models.keys())
        idx = int(cat_input) - 1
        if 0 <= idx < len(cat_list):
            cat = cat_list[idx]
        else:
            print("Numéro invalide.")
            continue
    else:
        cat = cat_input
    if cat not in category_models:
        print("Catégorie inconnue.")
        continue
    objet = input("Objet : ").strip()
    if objet.lower() == 'quit':
        break
    acheteur = input("Acheteur : ").strip()
    if acheteur.lower() == 'quit':
        break
    prediction = predict_interval(cat, objet, acheteur)
    print("\n📊 Intervalle prédit (MAD) :")
    print(f"🔻 Min (10%)  : {prediction['q10']}")
    print(f"➖ Médiane    : {prediction['q50']}")
    print(f"🔺 Max (90%)  : {prediction['q90']}")

print("\nFin de la session.") 
import json
import os
import pandas as pd
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.feature_extraction.text import TfidfVectorizer
from sentence_transformers import SentenceTransformer
from scipy.sparse import hstack, csr_matrix
import joblib

# === 1. Définir les chemins de données ===
data_files = {
    "fournitures": "fournitures/data/attributed_cleaned.json",
    "services": "services/data/attributed_cleaned.json",
    "traveaux": "traveaux/data/attributed_cleaned.json"
}

# === 2. Préparer les structures pour stocker modèles et vectorizers ===
category_models = {}
category_vectorizers = {}
category_embedders = {}

# === 2b. Dossier de stockage des modèles ===
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# === 3. Charger et entraîner/recharger pour chaque catégorie ===
print("🔄 Chargement du modèle SentenceTransformer...")
model_embed = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

for cat, path in data_files.items():
    print(f"\n📂 Traitement de {cat}...")
    tfidf_path = os.path.join(MODELS_DIR, f"{cat}_tfidf.pkl")
    models_paths = {q: os.path.join(MODELS_DIR, f"{cat}_quantile_{int(q*100)}.pkl") for q in [0.1, 0.5, 0.9]}
    # Vérifier si tout existe
    if os.path.exists(tfidf_path) and all(os.path.exists(p) for p in models_paths.values()):
        print("  🔁 Chargement des modèles et TF-IDF depuis le disque...")
        tfidf = joblib.load(tfidf_path)
        models = {q: joblib.load(models_paths[q]) for q in models_paths}
        category_models[cat] = models
        category_vectorizers[cat] = tfidf
        category_embedders[cat] = model_embed
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
    # Embedding
    print("  → Embedding sémantique...")
    sentence_vectors = np.vstack(df["texte_complet"].apply(lambda x: model_embed.encode(x)))
    # TF-IDF
    print("  → Vectorisation TF-IDF...")
    tfidf = TfidfVectorizer()
    tfidf_vectors = tfidf.fit_transform(df["texte_complet"])
    # Fusion features
    X = hstack([csr_matrix(sentence_vectors), tfidf_vectors])
    y = df["montant"].values
    # Entraînement modèles quantiles
    def train_quantile_model(q):
        model = GradientBoostingRegressor(loss='quantile', alpha=q, random_state=42)
        model.fit(X.toarray(), y)
        return model
    quantiles = [0.1, 0.5, 0.9]
    models = {q: train_quantile_model(q) for q in quantiles}
    # Sauvegarde
    joblib.dump(tfidf, tfidf_path)
    for q in quantiles:
        joblib.dump(models[q], models_paths[q])
    # Stockage en mémoire
    category_models[cat] = models
    category_vectorizers[cat] = tfidf
    category_embedders[cat] = model_embed
    print(f"  ✅ Modèles entraînés et sauvegardés pour {cat}.")

# === 4. Boucle interactive ===
def predict_interval(cat, objet_input, acheteur_input):
    tfidf = category_vectorizers[cat]
    models = category_models[cat]
    embedder = category_embedders[cat]
    text_input = objet_input + " " + acheteur_input
    embed_vec = embedder.encode(text_input).reshape(1, -1)
    tfidf_vec = tfidf.transform([text_input])
    input_vec = hstack([csr_matrix(embed_vec), tfidf_vec])
    prediction = {
        f"q{int(q*100)}": round(models[q].predict(input_vec.toarray())[0], 2)
        for q in models
    }
    return prediction

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
    resultat = predict_interval(cat, objet, acheteur)
    print("\n📊 Intervalle prédit (en dirhams MAD) :")
    print(f"🔻 Min (10%)  : {resultat['q10']} MAD")
    print(f"➖ Médiane    : {resultat['q50']} MAD")
    print(f"🔺 Max (90%)  : {resultat['q90']} MAD")

print("\nFin de la session.") 
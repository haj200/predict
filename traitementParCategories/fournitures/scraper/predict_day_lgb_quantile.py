import os
import json
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from scipy.sparse import hstack, csr_matrix
import joblib

# === Chemins ===
MODELS_DIR = "models_lgb_quantile"
DATA_PATH = "fournitures/scraper/data_daily/attributed_cleaned_day.json"
RESULTS_PATH = "fournitures/scraper/data_daily/prediction_results_day.json"
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
CATEGORY = "fournitures"

# === Charger modèles et vectorizer ===
tfidf_path = os.path.join(MODELS_DIR, f"{CATEGORY}_tfidf.pkl")
embed_name_path = os.path.join(MODELS_DIR, f"{CATEGORY}_embedder.txt")
models_paths = {q: os.path.join(MODELS_DIR, f"{CATEGORY}_lgb_quantile_{int(q*100)}.pkl") for q in [0.1, 0.5, 0.9]}

assert os.path.exists(tfidf_path), "TF-IDF manquant"
assert all(os.path.exists(p) for p in models_paths.values()), "Un ou plusieurs modèles manquent"
assert os.path.exists(embed_name_path), "Nom du modèle d'embedding manquant"

print("🔄 Chargement du modèle SentenceTransformer...")
with open(embed_name_path, "r", encoding="utf-8") as f:
    embedder_name = f.read().strip()
model_embed = SentenceTransformer(embedder_name)
tfidf = joblib.load(tfidf_path)
models = {q: joblib.load(models_paths[q]) for q in models_paths}
quantiles = [0.1, 0.5, 0.9]

# === Charger la nouvelle data ===
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data)

# === Prédiction ===
results = []
inside_count = 0
for idx, row in df.iterrows():
    texte = str(row["objet"]) + " " + str(row["acheteur"])
    embed = model_embed.encode([texte])
    tfidf_vec = tfidf.transform([texte])
    input_vec = hstack([csr_matrix(embed), tfidf_vec])
    preds = {f"q{int(q*100)}": float(models[q].predict(input_vec)[0]) for q in quantiles}
    montant_reel = float(row["montant"])
    in_interval = preds["q10"] <= montant_reel <= preds["q90"]
    if in_interval:
        inside_count += 1
    results.append({
        "reference": row.get("reference", None),
        "objet": row["objet"],
        "acheteur": row["acheteur"],
        "montant_reel": montant_reel,
        "q10": round(preds["q10"], 2),
        "q50": round(preds["q50"], 2),
        "q90": round(preds["q90"], 2),
        "in_interval": in_interval
    })

pourcentage = 100 * inside_count / len(df) if len(df) > 0 else 0

# === Sauvegarde des résultats ===
with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump({
        "pourcentage_in_interval": round(pourcentage, 2),
        "total": len(df),
        "inside_count": inside_count,
        "results": results
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ Résultats sauvegardés dans {RESULTS_PATH}")
print(f"Pourcentage d'éléments dont le montant réel est dans l'intervalle [q10, q90] : {round(pourcentage, 2)}% ({inside_count}/{len(df)})") 
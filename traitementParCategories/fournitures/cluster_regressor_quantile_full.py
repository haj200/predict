import os
import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
from lightgbm import LGBMRegressor
from concurrent.futures import ThreadPoolExecutor, as_completed
import joblib

# === Chemins ===
DATA_PATH = "data/attributed_cleaned.json"
EMBEDDINGS_PATH = "embeddings_fournitures.npy"
SCALER_PATH = "scaler_fournitures.pkl"
KMEANS_PATH = "kmeans_fournitures.pkl"
MODELS_DIR = "models_cluster_lgbm"
os.makedirs(MODELS_DIR, exist_ok=True)
EMBED_MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

# === Chargement des données JSON ===
with open(DATA_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data).dropna(subset=["objet", "acheteur", "reference", "montant"])

# === Embedding des textes (objet+acheteur+reference) ===
model = SentenceTransformer(EMBED_MODEL_NAME)
texts = (df["objet"].astype(str) + " " + df["acheteur"].astype(str) + " " + df["reference"].astype(str)).tolist()
if os.path.exists(EMBEDDINGS_PATH):
    print("🔁 Chargement des embeddings depuis le disque...")
    embeddings = np.load(EMBEDDINGS_PATH)
else:
    print("🔄 Calcul des embeddings...")
    embeddings = model.encode(texts, show_progress_bar=True, batch_size=128)
    np.save(EMBEDDINGS_PATH, embeddings)

# === Standardisation + Clustering ===
if os.path.exists(SCALER_PATH) and os.path.exists(KMEANS_PATH):
    print("🔁 Chargement du scaler et du kmeans...")
    scaler = joblib.load(SCALER_PATH)
    kmeans = joblib.load(KMEANS_PATH)
    df["cluster"] = kmeans.predict(scaler.transform(embeddings))
else:
    print("🔄 Calcul du scaler et du kmeans...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(embeddings)
    kmeans = KMeans(n_clusters=5, random_state=42)
    df["cluster"] = kmeans.fit_predict(X_scaled)
    joblib.dump(scaler, SCALER_PATH)
    joblib.dump(kmeans, KMEANS_PATH)

# === Entraînement ou chargement des modèles quantile pour chaque cluster (parallélisé) ===
quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]
models_by_cluster = {}

def train_or_load_cluster(cid):
    cluster_models_path = os.path.join(MODELS_DIR, f"models_cluster_{cid}.pkl")
    if os.path.exists(cluster_models_path):
        print(f"🔁 Chargement des modèles du cluster {cid}...")
        return cid, joblib.load(cluster_models_path)
    else:
        print(f"⚙️ Entraînement des modèles pour cluster {cid}...")
        group_df = df[df["cluster"] == cid]
        X = model.encode((group_df["objet"].astype(str) + " " + group_df["acheteur"].astype(str) + " " + group_df["reference"].astype(str)).tolist(), batch_size=128, show_progress_bar=False)
        X = scaler.transform(X)
        y = group_df["montant"].values
        models = {}
        for alpha in quantiles:
            lgbm = LGBMRegressor(objective='quantile', alpha=alpha, n_estimators=100)
            lgbm.fit(X, y)
            models[alpha] = lgbm
        joblib.dump(models, cluster_models_path)
        return cid, models

print("⏳ Entraînement/chargement des modèles par cluster (multi-thread)...")
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(train_or_load_cluster, cid) for cid in sorted(df["cluster"].unique())]
    for future in as_completed(futures):
        cid, models = future.result()
        models_by_cluster[cid] = models

# === Prédiction sur le fichier de test (parallélisé) ===
TEST_PATH = "scraper/data_daily/attributed_cleaned_day.json"
RESULTS_PATH = "scraper/data_daily/prediction_results_day_cluster.json"
with open(TEST_PATH, "r", encoding="utf-8") as f:
    test_data = json.load(f)
df_test = pd.DataFrame(test_data).dropna(subset=["objet", "acheteur", "reference", "montant"])

def predict_row(row):
    text = str(row["objet"]) + " " + str(row["acheteur"]) + " " + str(row["reference"])
    emb = model.encode([text])
    X = scaler.transform(emb)
    cluster = int(kmeans.predict(X)[0])
    models = models_by_cluster[cluster]
    preds = {f"q{int(alpha*100)}": float(models[alpha].predict(X)[0]) for alpha in quantiles}
    montant_reel = float(row["montant"])
    in_10_90 = preds["q10"] <= montant_reel <= preds["q90"]
    in_25_75 = preds["q25"] <= montant_reel <= preds["q75"]
    return {
        "reference": row["reference"],
        "objet": row["objet"],
        "acheteur": row["acheteur"],
        "montant_reel": montant_reel,
        "cluster": cluster,
        "q10": round(preds["q10"], 2),
        "q25": round(preds["q25"], 2),
        "q50": round(preds["q50"], 2),
        "q75": round(preds["q75"], 2),
        "q90": round(preds["q90"], 2),
        "in_10_90": in_10_90,
        "in_25_75": in_25_75
    }

print("⏳ Prédiction sur le fichier de test (multi-thread)...")
results = []
inside_10_90 = 0
inside_25_75 = 0
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(predict_row, row) for idx, row in df_test.iterrows()]
    for future in as_completed(futures):
        res = future.result()
        results.append(res)
        if res["in_10_90"]:
            inside_10_90 += 1
        if res["in_25_75"]:
            inside_25_75 += 1

pourc_10_90 = 100 * inside_10_90 / len(df_test) if len(df_test) > 0 else 0
pourc_25_75 = 100 * inside_25_75 / len(df_test) if len(df_test) > 0 else 0

with open(RESULTS_PATH, "w", encoding="utf-8") as f:
    json.dump({
        "pourcentage_in_10_90": round(pourc_10_90, 2),
        "pourcentage_in_25_75": round(pourc_25_75, 2),
        "total": len(df_test),
        "inside_10_90": inside_10_90,
        "inside_25_75": inside_25_75,
        "results": results
    }, f, ensure_ascii=False, indent=2)

print(f"\n✅ Résultats sauvegardés dans {RESULTS_PATH}")
print(f"Pourcentage d'éléments dans [q10, q90] : {round(pourc_10_90, 2)}% ({inside_10_90}/{len(df_test)})")
print(f"Pourcentage d'éléments dans [q25, q75] : {round(pourc_25_75, 2)}% ({inside_25_75}/{len(df_test)})") 
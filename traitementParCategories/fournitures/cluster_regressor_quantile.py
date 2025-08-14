import json
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer
from lightgbm import LGBMRegressor
from concurrent.futures import ThreadPoolExecutor, as_completed

# === Chargement des données JSON ===
with open("data/attributed_cleaned.json", "r", encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data).dropna(subset=["objet", "montant"])

# === Encodage des textes ===
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
embeddings = model.encode(df["objet"].tolist(), show_progress_bar=True)

# === Standardisation + Clustering ===
scaler = StandardScaler()
X_scaled = scaler.fit_transform(embeddings)
kmeans = KMeans(n_clusters=5, random_state=42)
df["cluster"] = kmeans.fit_predict(X_scaled)

# === Entraînement des modèles quantile pour chaque cluster ===
def train_models(cluster_id, group_df):
    X = model.encode(group_df["objet"].tolist())
    y = group_df["montant"].values
    X = scaler.transform(X)

    quantiles = [0.1, 0.25, 0.5, 0.75, 0.9]
    models = {}
    for alpha in quantiles:
        lgbm = LGBMRegressor(objective='quantile', alpha=alpha, n_estimators=100)
        lgbm.fit(X, y)
        models[alpha] = lgbm
    return cluster_id, models

# === Multi-threaded training ===
models_by_cluster = {}
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(train_models, cid, group) for cid, group in df.groupby("cluster")]
    for future in as_completed(futures):
        cid, models = future.result()
        models_by_cluster[cid] = models

# === Prédiction avec marges ===
def predict_price(objet):
    emb = model.encode([objet])
    X = scaler.transform(emb)
    cluster = kmeans.predict(X)[0]
    models = models_by_cluster[cluster]

    predictions = {f"q{int(alpha*100)}": model.predict(X)[0] for alpha, model in models.items()}
    return {
        "objet": objet,
        "cluster": int(cluster),
        "prediction_median": round(predictions["q50"], 2),
        "interval_q25_q75": (round(predictions["q25"], 2), round(predictions["q75"], 2)),
        "interval_q10_q90": (round(predictions["q10"], 2), round(predictions["q90"], 2)),
    }

# === Exemple sur 5 objets aléatoires ===
test_objets = df["objet"].sample(5, random_state=42).tolist()
for res in [predict_price(obj) for obj in test_objets]:
    print(json.dumps(res, indent=2, ensure_ascii=False))

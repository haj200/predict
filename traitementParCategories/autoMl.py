import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sentence_transformers import SentenceTransformer
from tpot import TPOTRegressor

# === Charger les données JSON ===
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# === Combiner les champs textuels ===
df["text"] = df["reference"] + " " + df["objet"] + " " + df["acheteur"]
X_text = df["text"].tolist()
y = df["montant"].tolist()

# === Split ===
X_train_text, X_test_text, y_train, y_test = train_test_split(X_text, y, test_size=0.3, random_state=42)

# === Embedding avec CamemBERT ===
print("🔄 Génération des embeddings CamemBERT...")
model = SentenceTransformer("dangvantuan/sentence-camembert-large")
X_train_emb = model.encode(X_train_text, show_progress_bar=True)
X_test_emb = model.encode(X_test_text, show_progress_bar=True)

# === AutoML avec TPOT ===
print("\n🤖 Lancement de l'AutoML (TPOT)...")
tpot = TPOTRegressor(generations=5, population_size=20, verbosity=2, random_state=42, max_time_mins=10)
tpot.fit(X_train_emb, y_train)

# === Prédictions et évaluation ===
y_pred = tpot.predict(X_test_emb)

mae = mean_absolute_error(y_test, y_pred)
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)

print("\n📊 Résultats du meilleur modèle AutoML (CamemBERT + TPOT) :")
print(f"MAE       : {mae:.2f}")
print(f"RMSE      : {rmse:.2f}")
print(f"R² Score  : {r2:.4f}")

# === Export du meilleur pipeline (optionnel) ===
tpot.export("best_pipeline.py")

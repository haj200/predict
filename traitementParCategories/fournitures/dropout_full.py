import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sentence_transformers import SentenceTransformer
import tensorflow as tf
from tensorflow.keras import layers, models, backend as K

# === Chargement des données ===
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)
df = pd.DataFrame(data).dropna(subset=["objet", "montant"])

# === Embedding avec SentenceTransformer ===
encoder = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
X = encoder.encode(df["objet"].tolist(), show_progress_bar=True)
y = df["montant"].values

# === Split pour évaluation
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === Construction du modèle avec Dropout actif en inference ===
def build_model(input_dim, dropout_rate=0.3):
    inputs = tf.keras.Input(shape=(input_dim,))
    x = layers.Dense(128, activation="relu")(inputs)
    x = layers.Dropout(dropout_rate)(x, training=True)  # 🧠 Dropout actif pendant prédiction
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(dropout_rate)(x, training=True)
    outputs = layers.Dense(1)(x)
    model = models.Model(inputs, outputs)
    model.compile(optimizer="adam", loss="mse")
    return model

model = build_model(X.shape[1])
model.fit(X_train, y_train, epochs=30, batch_size=32, verbose=1)

# === Prédiction Monte Carlo Dropout
def predict_mc_dropout(text, n_iter=100):
    x_embed = encoder.encode([text])
    preds = np.array([model(x_embed, training=True).numpy().flatten()[0] for _ in range(n_iter)])
    mean = preds.mean()
    std = preds.std()
    return {
        "objet": text,
        "pred_mean": round(mean, 2),
        "pred_std": round(std, 2),
        "interval_95": (round(mean - 2*std, 2), round(mean + 2*std, 2)),
        "note_confiance": f"{round(100 - std*100/mean, 1)}%" if mean > 0 else "N/A"
    }

# === Exemple d’utilisation
for obj in df["objet"].sample(5, random_state=2):
    res = predict_mc_dropout(obj)
    print(json.dumps(res, indent=2, ensure_ascii=False))

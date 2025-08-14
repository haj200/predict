import json
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Charger les résultats de prédiction
with open("prediction_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

df = pd.DataFrame(data)

# Créer un champ textuel combiné pour la similarité
if "objet" in df.columns and "acheteur" in df.columns:
    df["text"] = df["objet"].astype(str) + " " + df["acheteur"].astype(str)
else:
    df["text"] = df["objet"].astype(str)

# Vectorisation TF-IDF
vectorizer = TfidfVectorizer(max_features=1000)
X = vectorizer.fit_transform(df["text"])

# Calcul de la similarité cosinus
similarity_matrix = cosine_similarity(X)

# Stocker les bonnes prédictions
good_predictions = []

for idx, row in df.iterrows():
    # Indices des 15 plus similaires (hors soi-même)
    sim_scores = similarity_matrix[idx]
    similar_indices = np.argsort(sim_scores)[::-1][1:16]
    
    # Pour ces indices, vérifier l'erreur de prédiction
    for sim_idx in similar_indices:
        montant_reel = df.loc[sim_idx, "montant"]
        montant_predit = df.loc[sim_idx, "montant_predit"]
        erreur = abs(montant_reel - montant_predit)
        if erreur <= 2000:
            good_predictions.append({
                "index": int(sim_idx),
                "objet": df.loc[sim_idx, "objet"],
                "acheteur": df.loc[sim_idx, "acheteur"] if "acheteur" in df.columns else None,
                "montant": montant_reel,
                "montant_predit": montant_predit,
                "erreur": round(erreur, 2)
            })

# Sauvegarder les résultats
with open("bonnes_predictions.json", "w", encoding="utf-8") as f:
    json.dump(good_predictions, f, ensure_ascii=False, indent=2)

print(f"Nombre de bonnes prédictions trouvées : {len(good_predictions)}")
print("Exemple :")
for res in good_predictions[:5]:
    print(res) 
import json
import matplotlib.pyplot as plt
import textwrap
import os

def shorten(text, width=40):
    return "\n".join(textwrap.wrap(text, width=width))

def load_and_sort_json(file_path, min_pct=20.0):
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Filtrer par seuil
    filtered = {
        k: v for k, v in data.items()
        if v.get("pct_within_10pct_interval", 0) >= min_pct
    }
    sorted_data = sorted(filtered.items(), key=lambda x: x[1]["pct_within_10pct_interval"], reverse=True)
    return sorted_data

def plot_batches(sorted_data, batch_size=10, save_dir="plots"):
    os.makedirs(save_dir, exist_ok=True)
    total_batches = (len(sorted_data) + batch_size - 1) // batch_size

    for batch_num in range(total_batches):
        batch = sorted_data[batch_num * batch_size:(batch_num + 1) * batch_size]
        labels = [shorten(f"{key} ({value['total']})") for key, value in batch]
        values = [value['pct_within_10pct_interval'] for _, value in batch]

        plt.figure(figsize=(12, 6))
        bars = plt.barh(labels, values, color="#6495ED")
        plt.xlabel("% dans l'intervalle ±10 %")
        plt.title(f"Batch {batch_num + 1} – Précision dans l'intervalle ±10 % (>=20%)")
        plt.gca().invert_yaxis()

        # Annoter les barres
        for bar, val in zip(bars, values):
            plt.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2, f"{val:.2f}%", va='center')

        plt.tight_layout()
        filename = os.path.join(save_dir, f"batch_{batch_num + 1}.png")
        plt.savefig(filename)
        plt.close()
        print(f"[✔] Plot enregistré : {filename}")

if __name__ == "__main__":
    file_path = "C:/Users/pc/MarchePub/NewData/data/prediction/prediction_results/new_data/stats_globales.json"  
    sorted_data = load_and_sort_json(file_path, min_pct=20.0)
    plot_batches(sorted_data)

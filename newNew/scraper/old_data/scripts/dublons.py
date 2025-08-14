import json
from collections import defaultdict

# --- Fichiers source ---
files = ["data/attributed.jsonl", "data/infructuous.jsonl"]

# --- Détection de doublons ---
seen = defaultdict(list)

for filename in files:
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue  # Skip empty lines
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                print(f"[WARN] Invalid JSON in {filename} at line {line_num}: {e}")
                continue
            key = (
                obj["reference"].strip().lower(),
                obj["objet"].strip().lower(),
                obj["acheteur"].strip().lower()
            )
            seen[key].append(obj)

# --- Stockage des doublons ---
with open("doublons.jsonl", "w", encoding="utf-8") as out:
    for key, group in seen.items():
        if len(group) > 1:
            for item in group:
                out.write(json.dumps(item, ensure_ascii=False) + "\n")

print("Doublons extraits dans 'doublons.jsonl'")

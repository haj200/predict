import os
import subprocess

base_dir = os.path.dirname(os.path.abspath(__file__))

for i in range(1, 102):  # adapte la plage si besoin
    scraper_path = os.path.join(base_dir, f"nature_{i}", "scraper", "scraper.py")
    if os.path.exists(scraper_path):
        print(f"--- Running: {scraper_path} ---")
        subprocess.run(["python", scraper_path])
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour calculer le nombre total de données dans les fichiers JSON
attribués et infructueux pour toutes les natures
"""

import os
import json
from pathlib import Path

def count_data_in_json_file(file_path):
    """
    Compte le nombre d'éléments dans un fichier JSON
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            else:
                return 1  # Si c'est un objet unique
    except (FileNotFoundError, json.JSONDecodeError, UnicodeDecodeError) as e:
        return 0

def analyze_nature_data():
    """
    Analyse les données de toutes les natures et compte le total
    """
    base_dir = Path(".")
    total_attributed = 0
    total_infructuous = 0
    total_combined = 0
    
    # Parcourir tous les dossiers qui commencent par "nature_"
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name
            data_dir = item / "data_daily"
            
            if data_dir.exists():
                attributed_file = data_dir / "attributed_cleaned_day.json"
                
                # Compter les données attribuées
                attributed_count = 0
                if attributed_file.exists():
                    attributed_count = count_data_in_json_file(attributed_file)
                
                
                # Calculer le total pour cette nature
                nature_total = attributed_count 
                
                # Ajouter aux totaux globaux
                total_attributed += attributed_count
                total_combined += nature_total
    
    # Afficher seulement le total
    print(f"Total des données: {total_combined:,}")
    print(f"  - Attribuées: {total_attributed:,}")
    
    
    return total_combined

if __name__ == "__main__":
    total_data = analyze_nature_data() 
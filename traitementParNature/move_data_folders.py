#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script pour déplacer le dossier data de chaque nature_x/scraper/data vers nature_x/data
"""

import os
import shutil
from pathlib import Path

def move_data_folders():
    """
    Déplace le dossier data de chaque nature_x/scraper/data vers nature_x/data
    """
    base_dir = Path(".")
    moved_count = 0
    skipped_count = 0
    
    print("🔄 Déplacement des dossiers data...")
    
    # Parcourir tous les dossiers qui commencent par "nature_"
    for item in base_dir.iterdir():
        if item.is_dir() and item.name.startswith("nature_"):
            nature_id = item.name
            source_data_dir = item / "scraper" / "data"
            target_data_dir = item / "data"
            
            # Vérifier si le dossier source existe
            if source_data_dir.exists() and source_data_dir.is_dir():
                # Vérifier si le dossier cible existe déjà
                if target_data_dir.exists():
                    print(f"⚠️  {nature_id}: Le dossier data existe déjà dans {nature_id}/")
                    skipped_count += 1
                    continue
                
                try:
                    # Déplacer le dossier
                    shutil.move(str(source_data_dir), str(target_data_dir))
                    print(f"✅ {nature_id}: Dossier data déplacé avec succès")
                    moved_count += 1
                except Exception as e:
                    print(f"❌ {nature_id}: Erreur lors du déplacement: {e}")
                    skipped_count += 1
            else:
                print(f"⚠️  {nature_id}: Aucun dossier data trouvé dans scraper/")
                skipped_count += 1
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DU DÉPLACEMENT")
    print("=" * 50)
    print(f"✅ Dossiers déplacés: {moved_count}")
    print(f"⚠️  Dossiers ignorés: {skipped_count}")
    print(f"📁 Total traité: {moved_count + skipped_count}")

if __name__ == "__main__":
    move_data_folders() 
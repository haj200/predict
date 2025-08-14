import json
import os
from pathlib import Path

def get_safe_name(text):
    return text.lower().replace(' ', '_').replace('/', '_').replace('-', '_')

def rename_files_and_folders_based_on_nature():
    natures_file_path = "traitementParNature/natures.json"
    
    try:
        with open(natures_file_path, 'r', encoding='utf-8') as f:
            natures_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: natures.json not found at {natures_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not decode natures.json at {natures_file_path}")
        return

    # Create a reverse mapping from descriptive name (in safe format) to nature_X
    reverse_nature_map = {get_safe_name(description): nature_key for nature_key, description in natures_data.items()}

    # Define target directories
    target_base_dirs = [
        "Scraper/data_cleaned"
    ]

    for base_dir_str in target_base_dirs:
        base_dir = Path(base_dir_str)
        if not base_dir.exists():
            print(f"Warning: Directory {base_dir} does not exist. Skipping.")
            continue

        print(f"\nProcessing directory: {base_dir}")

        for item in base_dir.iterdir():
            original_name = item.name
            potential_match_name = original_name

            # For files, remove the .json extension for matching against descriptions
            if item.is_file() and original_name.endswith('.json'):
                potential_match_name = original_name[:-5] # remove '.json'

            new_name_prefix = None
            if potential_match_name in reverse_nature_map:
                new_name_prefix = reverse_nature_map[potential_match_name]
            
            if new_name_prefix:
                new_item_name = new_name_prefix
                if item.is_file() and original_name.endswith('.json'):
                    new_item_name += '.json' # Add back .json for files

                new_item_path = item.parent / new_item_name

                try:
                    if item.exists(): # Check if the item still exists before renaming
                        os.rename(item, new_item_path)
                        print(f"  Renamed '{original_name}' to '{new_item_name}'")
                    else:
                        print(f"  Warning: '{original_name}' no longer exists, skipping rename.")
                except OSError as e:
                    print(f"  Error renaming '{original_name}' to '{new_item_name}': {e}")
            else:
                print(f"  Skipped '{original_name}' (no matching nature found).")

if __name__ == "__main__":
    rename_files_and_folders_based_on_nature() 
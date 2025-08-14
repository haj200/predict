import os
import json

def count_json_items(directory):
    total_items = 0
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        total_items += len(data)
                        print(f"File: {filename}, Items: {len(data)}")
                    elif isinstance(data, dict):
                        total_items += len(data)
                        print(f"File: {filename}, Items: {len(data)}")
                    else:
                        print(f"File: {filename} contains an unsupported JSON structure (not a list or dictionary).")
            except json.JSONDecodeError:
                print(f"Error decoding JSON from {filename}. Skipping.")
            except Exception as e:
                print(f"An error occurred while processing {filename}: {e}")
    return total_items

if __name__ == "__main__":
    data_directory = "Scraper/data"
    total = count_json_items(data_directory)
    print(f"\nTotal items across all JSON files: {total}") 
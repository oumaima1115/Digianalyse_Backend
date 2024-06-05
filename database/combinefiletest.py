import os
import json

def combine_json_files(input_folder, output_file):
    combined_data = []

    json_files = [f for f in os.listdir(input_folder) if f.endswith('.json')]

    if not json_files:
        print("No JSON files found in the input folder.")
        return

    for filename in json_files:
        print("Processing file:", filename)
        file_path = os.path.join(input_folder, filename)
        with open(file_path, 'r', encoding='utf-8') as file:
            try:
                data = json.load(file)
                print(f"Successfully read data from {filename}")
                combined_data.extend(data)
            except json.JSONDecodeError as e:
                print(f"Error reading {filename}: {e}")
                continue

    try:
        with open(output_file, 'w', encoding='utf-8') as output:
            json.dump(combined_data, output, ensure_ascii=False, indent=4)
        print(f"Combined data saved to {output_file}")
    except Exception as e:
        print(f"Error saving combined data: {e}")

# Example usage:
input_folder = 'API'
output_file = 'influencer.json'
combine_json_files(input_folder, output_file)

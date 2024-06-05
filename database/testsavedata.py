import os
import json

def save_to_json(data, filename):
    # Ensure the filename ends with .json
    if not filename.endswith('.json'):
        filename += '.json'
        
    # Define the path for the 'API' folder inside 'database'
    api_folder = os.path.join('database', 'API')
    print(f"API folder path: {api_folder}")

    # Create 'API' folder if it doesn't exist
    if not os.path.exists(api_folder):
        os.makedirs(api_folder)
        print(f"Created API folder at: {api_folder}")
    else:
        print(f"API folder already exists at: {api_folder}")

    # Define the complete file path
    filepath = os.path.join(api_folder, filename)
    print(f"File path to save JSON: {filepath}")

    # Try to save the data to the JSON file
    try:
        with open(filepath, 'w', encoding='utf-8') as json_file:
            json.dump(data, json_file, indent=4)
        print(f"Data has been saved to {filepath}")
    except (TypeError, ValueError) as e:
        print(f"Error saving data to JSON: {e}")

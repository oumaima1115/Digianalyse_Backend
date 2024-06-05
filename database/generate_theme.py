import spacy
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import os
import json

# Get the current working directory
current_directory = os.getcwd()

# Construct the path to the JSON file
file_path = os.path.join(current_directory, 'serialization', 'influencer_data.json')

# Read data from the JSON file
with open(file_path, 'r') as file:
    clusters = json.load(file)

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def extract_keywords(text):
    try:
        doc = nlp(text.lower())
    except UnicodeEncodeError:
        doc = nlp(text.encode('ascii', 'ignore').decode('utf-8').lower())
    keywords = [token.text for token in doc if token.is_alpha and not token.is_stop]
    return keywords

def generate_theme(documents):
    all_keywords = []
    with ThreadPoolExecutor() as executor:
        descriptions = [
            ' '.join(doc['description']) if isinstance(doc['description'], list) else doc['description']
            for doc in documents
        ]
        results = executor.map(extract_keywords, descriptions)
    for keywords in results:
        all_keywords.extend(keywords)
    common_keywords = Counter(all_keywords).most_common(5)
    theme = ' '.join([keyword for keyword, _ in common_keywords])
    return theme

# Generate themes for each cluster
for cluster_id, cluster_data in clusters.items():
    theme = generate_theme(cluster_data['documents'])
    clusters[cluster_id]['theme'] = theme

# Write the updated clusters with generated themes to a new JSON file
output_file_path = os.path.join(current_directory, 'serialization', 'influencer-update.json')
with open(output_file_path, 'w') as output_file:
    json.dump(clusters, output_file, indent=4)

print("Updated data saved to influencer-update.json")

import numpy as np
import hashlib
import matplotlib.pyplot as plt
# from collections import defaultdict
from sklearn.cluster import KMeans
from sklearn.manifold import TSNE
from sentence_transformers import SentenceTransformer
from threading import Timer
import json
import re
import os
import logging

import re
import json
import os


from sklearn.feature_extraction.text import TfidfVectorizer

# Define the directory and file paths
script_dir = os.path.dirname(os.path.realpath(__file__))
json_file_path = os.path.join(script_dir, 'influencer.json')

# Load influencer data from JSON file
with open(json_file_path, 'r', encoding='utf-8') as json_file:
    influencer_data = json.load(json_file)

# Function to remove emojis and symbols from text
def remove_emojis_and_symbols(text):
    text = text.encode('ascii', 'ignore').decode('ascii')  # Remove emojis
    text = re.sub(r'[^\w\s]', '', text)  # Remove symbols
    return text

# Extract and clean texts from influencer data
texts = []
for data in influencer_data:
    text = data.get('text', '')
    cleaned_text = remove_emojis_and_symbols(text) 
    if cleaned_text:
        texts.append(cleaned_text)

# Display the cleaned texts
for i, text in enumerate(texts[:5]):  # Displaying the first 5 cleaned texts
    print(f"Cleaned text {i + 1}:\n{text}\n")


# Vectorize the cleaned text data
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

# Apply K-means clustering
kmeans = KMeans(n_clusters=5, random_state=42)
kmeans.fit(X)

# Get cluster labels
cluster_labels = kmeans.labels_

# Print the cluster labels
print("Cluster labels:", cluster_labels)

# Print texts within each cluster
for cluster_id in range(5):
    cluster_texts = [texts[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
    print(f"Cluster {cluster_id} - Number of texts: {len(cluster_texts)}")
    print("Example texts:")
    for text in cluster_texts[:5]:  # Print first 5 texts in each cluster
        print(text)
    print("\n")

cluster_themes = {}

# Add cluster themes and documents
for cluster_label in range(5):
    theme = "Cluster " + str(cluster_label)
    cluster_docs = []
    for idx, label in enumerate(cluster_labels):
        if label == cluster_label:
            if influencer_data[idx].get('source', '') == 'youtube' or influencer_data[idx].get('source', '') == "reddit":
                document = {
                    'author': influencer_data[idx].get('author', ''),
                    'description': remove_emojis_and_symbols(influencer_data[idx].get('text', '')),
                    'like': influencer_data[idx].get('like', ''),
                    'source': influencer_data[idx].get('source', ''),
                }
            else:
                document = {
                    'author': influencer_data[idx].get('author', ''),
                    'description': influencer_data[idx].get('description', []),
                    'like': influencer_data[idx].get('like', []),
                    'source': influencer_data[idx].get('source', ''),
                }
            cluster_docs.append(document)
    cluster_themes[cluster_label] = {'theme': theme, 'documents': cluster_docs}


# Print cluster themes
for cluster_id, theme_info in cluster_themes.items():
    print(f"Cluster {cluster_id} - Theme: {theme_info['theme']}")
    for doc in theme_info['documents']:
        print(f"  author: {doc['author']}, description: {doc['description']}, like: {doc['like']}, source: {doc['source']}")

script_dir = os.path.dirname(os.path.realpath(__file__))
serialization_dir = os.path.join(script_dir, 'serialization')

# Ensure the Serialization directory exists
os.makedirs(serialization_dir, exist_ok=True)

# Path for the output JSON file
output_file_path = os.path.join(serialization_dir, 'influencer_data.json')

# Save the cluster themes to a JSON file in the Serialization directory
with open(output_file_path, 'w', encoding='utf-8') as json_file:
    json.dump(cluster_themes, json_file, indent=4)


# # Initialize Sentence Transformer model
# model = SentenceTransformer('all-MiniLM-L6-v2')

# # Cache class for storing embeddings
# class Cache:
#     def __init__(self):
#         self.cache_dict = {}

#     def get(self, key):
#         return self.cache_dict.get(key)

#     def set(self, key, value, timeout=None):
#         self.cache_dict[key] = value
#         if timeout:
#             Timer(timeout, self._remove_key, args=(key,)).start()

#     def _remove_key(self, key):
#         if key in self.cache_dict:
#             del self.cache_dict[key]

# # Initialize cache object
# cache = Cache()

# # Get embedding for texts
# def get_embedding(texts, mention):
#     if isinstance(texts, str):
#         texts = [texts]
#     combined_text = " ".join([text.strip() for text in texts if text])
#     cache_key = f"embedding:{mention}:{hashlib.sha256(combined_text.encode('utf-8')).hexdigest()}"

#     # Attempt to retrieve the cached embedding
#     embedding_vector = cache.get(cache_key)
#     if embedding_vector is not None:
#         logging.info("Using cached embedding for mention: %s", mention)
#         return embedding_vector

#     try:
#         embedding_vector = model.encode(texts)
#         cache.set(cache_key, embedding_vector)
#         logging.info("Generated new embedding for mention: %s", mention)
#         return embedding_vector
#     except Exception as e:
#         error_message = f"An error occurred while generating embedding for mention {mention}: {e}"
#         logging.error(error_message)
#         return None


# # Perform clustering on embedded texts
# def clustering(texts_embedded, n_clusters=10, perplexity=5):
#     try:
#         matrix = np.array(texts_embedded)
#         matrix = np.nan_to_num(matrix)
#         kmeans = KMeans(n_clusters=n_clusters, random_state=42)
#         kmeans.fit(matrix)
#         labels = kmeans.labels_

#         tsne = TSNE(n_components=2, perplexity=perplexity, random_state=42)
#         vis_dims2 = tsne.fit_transform(matrix)

#         return labels, vis_dims2
#     except Exception as e:
#         error_message = f"An error occurred while clustering: {e}"
#         logging.error(error_message)
#         return None, None

# # Generate theme based on descriptions
# def generate_theme(descriptions):
#     keywords = ['finance', 'digital currency', 'smart contracts', 'emerging trends', 'blockchain benefits', 'cryptocurrency', 'decentralized finance', 'tokenization', 'security', 'transparency']
#     theme = ""
#     for keyword in keywords:
#         if keyword in descriptions.lower():
#             theme = f'"{keyword.capitalize()}"'
#             break
#     if not theme:
#         theme = '"General Blockchain"'  # Fallback theme
#     return theme

# # Set up logging
# logging.basicConfig(level=logging.INFO)

# # Generate cluster themes for influencer chart
# def influencer_chart(user_id: str, mention: str, recent_market_analysis_date: str) -> dict:
#     logging.info("Generating cluster themes for mention: %s", mention)
#     cluster_themes = {}
#     influencer_chart_dict = defaultdict(list)
#     embeddings = []
#     documents = []
#     mention_cache_key = f"{mention}_embedding_influencer_results"
#     embedding_result = cache.get(mention_cache_key)

#     # Check if embedding_result is None or empty
#     if embedding_result is None or len(embedding_result) == 0:
#         logging.warning("Failed to get or no embeddings found in the cache for mention: %s", mention)
#         return cluster_themes

#     # Continue with the rest of the code
#     for doc in embedding_result:
#         if doc.get('description') == "[removed]":
#             continue
#         embeddingg = get_embedding(doc['description'], mention)
#         if embeddingg is not None:
#             embeddings.append(embeddingg)
#             documents.append(doc)

#     if len(embeddings) == 0:
#         logging.warning("No valid embeddings found for the given mention: %s", mention)
#         return cluster_themes

#     try:
#         # Flatten the list of embeddings if they are not already flattened
#         embeddings = [e for emb in embeddings for e in emb]

#         labels, vis_dims2 = clustering(embeddings)
#         for doc, label in zip(documents, labels):
#             doc['cluster'] = int(label)
#         for doc in documents:
#             cluster = doc['cluster']
#             influencer_chart_dict[cluster].append(doc)
#         for cluster, docs in influencer_chart_dict.items():
#             theme_cache_key = f"{mention}_cluster_theme_{cluster}"
#             cached_theme = cache.get(theme_cache_key)
#             if cached_theme:
#                 cluster_themes[cluster] = cached_theme
#                 continue
#             summaries = " ".join([' '.join(filter(None, doc.get('description', [])))[:50] if isinstance(doc.get('description'), list) else doc.get('description', '')[:50] for doc in docs[:10]])
#             # Generate theme using the language model
#             theme = generate_theme(summaries)
#             document_details = [{"author": doc.get("author", "Unknown"), "title": doc.get("title", "Untitled"), "likes": doc.get("like", 0), "description": doc.get("description", ""), "source": doc.get("source", "Unknown source")} for doc in docs]
#             cache.set(theme_cache_key, {"theme": theme, "documents": document_details}, timeout=86400)
#             cluster_themes[cluster] = {"theme": theme, "documents": document_details}
#         logging.info("Cluster themes generated for mention: %s", mention)
#         return cluster_themes

#     except Exception as e:
#         error_message = f"An error occurred in influencer_chart for mention {mention}: {e}"
#         logging.error(error_message)
#         return cluster_themes


# #
# #
# # Test
# #
# #

# # Test parameters
# user_id = "user_123"
# mention = "blockchain"
# recent_market_analysis_date = "2024-05-01"

# # Get embedding for each text
# embedded_texts = [get_embedding(text, mention) for text in texts]

# # Print out embeddings for inspection
# for i, embedding in enumerate(embedded_texts):
#     print(f"Embedding for text {i + 1}:\n{embedding}")
#     if embedding is not None:
#         print(f"Shape: {embedding.shape}")
#     else:
#         print("Embedding is None")

# # Convert embedded texts to 2D array
# embedded_texts = np.array([e for e in embedded_texts if e is not None])
# if embedded_texts.ndim == 3:
#     nsamples, nx, ny = embedded_texts.shape
#     embedded_texts_2d = embedded_texts.reshape((nsamples, nx * ny))
# else:
#     embedded_texts_2d = embedded_texts

# # Perform clustering on embedded texts
# labels, vis_dims2 = clustering(embedded_texts_2d)

# # Generate cluster themes for influencer chart
# cluster_themes = influencer_chart(user_id, mention, recent_market_analysis_date)
# print("cluster_themes = ", cluster_themes)


import spacy
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

def generate(clusters):
    try:
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception as e:
        print(f"Error loading spaCy model: {e}")
        return clusters

    def extract_keywords(text):
        try:
            doc = nlp(text.lower())
        except Exception as e:
            print(f"Error processing text: {e}")
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
        cluster_data['theme'] = theme  

    return clusters

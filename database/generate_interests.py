import spacy
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

def generate_interests(clusters):
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

    def generate_interests_string(texts):
        all_keywords = []
        with ThreadPoolExecutor() as executor:
            list_texts = [
                ' '.join(doc['text']) if isinstance(doc['text'], list) else doc['text']
                for doc in texts
            ]
            results = executor.map(extract_keywords, list_texts)
        for keywords in results:
            all_keywords.extend(keywords)
        common_keywords = Counter(all_keywords).most_common(10)  # Get top 10 keywords as interests
        interests = ' '.join([keyword for keyword, _ in common_keywords])
        return interests

    # Generate interests for each cluster
    final_clusters = {}
    for cluster_id, cluster_data in clusters.items():
        interests = generate_interests_string(cluster_data['texts'])
        texts = [
            {
                "author": doc['author'],
                "text": doc['text'],
                "source": doc['source'],
                "source_link": doc['source_link']
            }
            for doc in cluster_data['texts']
        ]
        final_clusters[cluster_id] = {
            "interests": interests,
            "texts": texts
        }

    return final_clusters

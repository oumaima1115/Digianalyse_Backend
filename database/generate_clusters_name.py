import spacy
from collections import Counter

nlp = spacy.load('en_core_web_sm')

def generate_cluster_names(domains_per_cluster):
    """Génère des noms descriptifs pour les clusters basés sur les noms de domaine."""
    import spacy
    from collections import Counter
    
    nlp = spacy.load('en_core_web_sm')

    def extract_keywords(text):
        """Extraire les mots-clés en utilisant SpaCy."""
        doc = nlp(text)
        keywords = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        return keywords

    cluster_keywords = {}

    for cluster_label, domain_list in domains_per_cluster.items():
        all_keywords = []
        for domain in domain_list:
            keywords = extract_keywords(domain)
            all_keywords.extend(keywords)
        
        keyword_freq = Counter(all_keywords)
        most_common_keywords = keyword_freq.most_common(3)  # Prendre les 3 mots les plus fréquents
        cluster_name = ' '.join([keyword for keyword, _ in most_common_keywords])
        
        if not cluster_name:
            cluster_name = f"Cluster {cluster_label + 1}"
        
        cluster_keywords[cluster_label] = cluster_name
    
    return cluster_keywords

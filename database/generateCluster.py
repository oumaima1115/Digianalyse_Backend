import spacy
from collections import Counter
import tldextract

def generate_cluster_names(domains_per_cluster):
    """Generate descriptive names for clusters based on domain names."""
    try:
        spacy.cli.download("en_core_web_sm")
        nlp = spacy.load("en_core_web_sm", disable=["parser", "ner"])
    except Exception as e:
        print(f"Error loading spaCy model: {e}")
        return {f"Cluster {cluster_label + 1}" for cluster_label in domains_per_cluster.keys()}

    def extract_keywords_from_domain(domain):
        """Extract meaningful keywords from a domain name."""
        extracted = tldextract.extract(domain)
        components = [extracted.subdomain, extracted.domain]
        keywords = []
        for component in components:
            if component:
                doc = nlp(component)
                keywords.extend([token.lemma_ for token in doc if not token.is_stop and not token.is_punct and token.is_alpha])
        return keywords

    cluster_keywords = {}

    for cluster_label, domain_list in domains_per_cluster.items():
        all_keywords = []
        for domain in domain_list:
            keywords = extract_keywords_from_domain(domain)
            all_keywords.extend(keywords)

        keyword_freq = Counter(all_keywords)
        most_common_keywords = [keyword for keyword, _ in keyword_freq.most_common(3)]
        cluster_name = ' '.join(most_common_keywords).capitalize()

        if not cluster_name or cluster_name.strip() == '':
            cluster_name = f"Cluster {cluster_label + 1}"

        cluster_keywords[cluster_label] = cluster_name.capitalize()

    return cluster_keywords

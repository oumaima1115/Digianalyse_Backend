from transformers import pipeline

def generate_descriptive_names_with_transformers(domains_per_cluster):
    """Generate cluster names using a pre-trained transformer model."""
    generator = pipeline('text-generation', model='gpt2')
    
    cluster_keywords = {}
    
    for cluster_label, domain_list in domains_per_cluster.items():
        combined_text = ' '.join(domain_list)
        prompt = f"Generate a descriptive name for the following cluster: {combined_text}"
        result = generator(prompt, max_length=50, num_return_sequences=1)
        cluster_name = result[0]['generated_text']
        
        cluster_keywords[cluster_label] = cluster_name
    
    return cluster_keywords

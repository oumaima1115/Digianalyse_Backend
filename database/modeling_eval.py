from sklearn.cluster import KMeans, AgglomerativeClustering, SpectralClustering, Birch
from sklearn.metrics import silhouette_score, davies_bouldin_score, calinski_harabasz_score, adjusted_rand_score, \
    normalized_mutual_info_score, homogeneity_score, completeness_score
from sklearn.feature_extraction.text import TfidfVectorizer
import re

def clustering(influencer_data, leads_data):
    
    def clean_description(text):
        # Check if text is a list or a string and handle accordingly
        if isinstance(text, list):
            text = ' '.join(text)
        text = text.encode('ascii', 'ignore').decode('ascii') if isinstance(text, str) else ''
        text = re.sub(r'\n+', ' ', text)  # Remove multiple newlines
        text = re.sub(r'\s+', ' ', text)  # Remove extra whitespaces
        text = re.sub(r'[^\w\s]', '', text)  # Remove non-alphanumeric characters
        return text.strip()

    # Clean the 'description' field from all objects in data
    influencers_texts = [clean_description(d.get('description', '')) for d in influencer_data]
    leads_texts = [clean_description(d.get('description', '')) for d in leads_data]

    # Remove empty texts
    influencers_texts = [text for text in influencers_texts if text.strip()]
    leads_texts = [text for text in leads_texts if text.strip()]

    if not influencers_texts or not leads_texts:
        print("No meaningful texts available after cleaning.")
        return None

    # Vectorize the cleaned text data
    vectorizer = TfidfVectorizer()
    X_influencers = vectorizer.fit_transform(influencers_texts)
    X_leads = vectorizer.fit_transform(leads_texts)

    # Determine the number of clusters
    n_samples_influencers = X_influencers.shape[0]
    n_clusters_influencers = min(5, n_samples_influencers) 
    
    n_samples_leads = X_leads.shape[0]
    n_clusters_leads = min(5, n_samples_leads)

    # Define clustering algorithms
    clustering_algorithms_influencers = {
        'KMeans': KMeans(n_clusters=n_clusters_influencers, random_state=42),
        'Agglomerative': AgglomerativeClustering(n_clusters=n_clusters_influencers),
        'Spectral': SpectralClustering(n_clusters=n_clusters_influencers, random_state=42),
        'Birch': Birch(n_clusters=n_clusters_influencers)
    }

    clustering_algorithms_leads = {
        'KMeans': KMeans(n_clusters=n_clusters_leads, random_state=42),
        'Agglomerative': AgglomerativeClustering(n_clusters=n_clusters_leads),
        'Spectral': SpectralClustering(n_clusters=n_clusters_leads, random_state=42),
        'Birch': Birch(n_clusters=n_clusters_leads)
    }

    # Evaluation metrics
    evaluation_metrics = {
        'Silhouette Score': silhouette_score,
        'Davies-Bouldin Index': davies_bouldin_score,
        'Calinski-Harabasz Index': calinski_harabasz_score,
        'Adjusted Rand Index': adjusted_rand_score,
        'Normalized Mutual Information': normalized_mutual_info_score,
        'Homogeneity Score': homogeneity_score,
        'Completeness Score': completeness_score
    }

    def perform_clustering_influencer(algorithm, X):
        algo_results_influencers = {}
        algo_influencers = clustering_algorithms_influencers[algorithm]

        # Convert sparse matrix to dense array if needed
        X_dense = X.toarray() if hasattr(X, 'toarray') else X
        
        cluster_labels_influencers = algo_influencers.fit_predict(X_dense)
        algo_results_influencers['Cluster labels'] = cluster_labels_influencers.tolist()

        # Print cluster labels
        # print(f"\nResults for {algorithm}:")
        # print("Cluster labels:", cluster_labels_influencers)

        # Collect cluster documents for themes
        cluster_themes_influencers = {}

        for cluster_id in range(n_clusters_influencers):
            cluster_docs = []
            for idx, label in enumerate(cluster_labels_influencers):
                if label == cluster_id:
                    source = influencer_data[idx].get('source', '')
                    document = {
                        'author': influencer_data[idx].get('author', ''),
                        'description': influencer_data[idx].get('description', ''),
                        'like': influencer_data[idx].get('like', ''),
                        'source': source,
                    }
                    cluster_docs.append(document)
            cluster_themes_influencers[cluster_id] = {'theme': f"Cluster {cluster_id}", 'documents': cluster_docs}

        return algo_results_influencers, cluster_themes_influencers

    def perform_clustering_leads(algorithm, X):
        algo_results_leads = {}
        algo_leads = clustering_algorithms_leads[algorithm]

        # Convert sparse matrix to dense array if needed
        X_dense = X.toarray() if hasattr(X, 'toarray') else X

        cluster_labels_leads = algo_leads.fit_predict(X_dense)
        algo_results_leads['Cluster labels'] = cluster_labels_leads.tolist()

        # Print cluster labels
        # print(f"\nResults for {algorithm}:")
        # print("Cluster labels:", cluster_labels_leads)

        # Collect cluster documents for interests
        cluster_interests_leads = {}

        for cluster_id in range(n_clusters_leads):
            cluster_docs = []
            for idx, label in enumerate(cluster_labels_leads):
                if label == cluster_id:
                    source = leads_data[idx].get('source', '')
                    document = {
                        'author': leads_data[idx].get('author', ''),
                        'text': leads_data[idx].get('text', ''),
                        'source': source,
                        'source_link': leads_data[idx].get('source_link', ''),
                    }
                    cluster_docs.append(document)
            cluster_interests_leads[cluster_id] = {'interests': f"Cluster {cluster_id}", 'texts': cluster_docs}

        return algo_results_leads, cluster_interests_leads

    # Dictionary to store results
    results = {}
    cluster_all = {"influencers_charts": {}, "leads_charts": {}}

    # Perform clustering and evaluation for influencers
    for algo_name_influencer, algo in clustering_algorithms_influencers.items():
        algo_results, cluster_themes = perform_clustering_influencer(algo_name_influencer, X_influencers)
        results[algo_name_influencer] = algo_results
        cluster_all["influencers_charts"][algo_name_influencer] = cluster_themes

    # Perform clustering and evaluation for leads
    for algo_name_leads, algo in clustering_algorithms_leads.items():
        algo_results, cluster_interests = perform_clustering_leads(algo_name_leads, X_leads)
        results[algo_name_leads] = algo_results
        cluster_all["leads_charts"][algo_name_leads] = cluster_interests

    # Print evaluation results
    # for algo_name, algo_result in results.items():
    #     print(f"\nResults for {algo_name}:")
    #     for metric_name, score in algo_result.items():
    #         if metric_name != 'Cluster labels':
    #             print(f"{metric_name}: {score}")

    # Choose the best method based on the evaluation metrics
    best_evaluation_metric = 'Silhouette Score'
    best_method = max(results, key=lambda x: results[x].get(best_evaluation_metric, float('-inf')))

    # print(f"\nBest clustering method based on {best_evaluation_metric}: {best_method}")

    # Get the cluster themes and interests for the best method
    best_clusters = {
        "influencers_charts": cluster_all["influencers_charts"][best_method],
        "leads_charts": cluster_all["leads_charts"][best_method]
    }

    return best_clusters
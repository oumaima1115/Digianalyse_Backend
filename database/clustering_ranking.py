from sklearn.cluster import KMeans

def clusteringRanking(data):
    # Filtrer les données par competition_level
    def filter_data_by_competition_level(data, level):
        return [item for item in data if item['competition_level'].upper() == level.upper()]

    # Appliquer le filtrage pour chaque niveau de compétition
    data_levels = {
        'LOW': filter_data_by_competition_level(data, 'LOW'),
        'MEDIUM': filter_data_by_competition_level(data, 'MEDIUM'),
        'HIGH': filter_data_by_competition_level(data, 'HIGH'),
        'UNSPECIFIED': filter_data_by_competition_level(data, 'UNSPECIFIED')
    }

    # Extraire les caractéristiques pour le clustering
    features = ['volume', 'competition_index', 'low_bid', 'high_bid', 'trend']

    # Organiser les données par clusters pour chaque niveau de compétition
    organized_data = {}

    for level, data_level in data_levels.items():
        if not data_level:
            continue

        # Extraire les caractéristiques
        X = [[item[feature] for feature in features] for item in data_level]

        # Appliquer KMeans pour le clustering
        kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(X)

        # Ajouter les étiquettes de clusters aux données
        for i, item in enumerate(data_level):
            item['cluster'] = int(clusters[i])  # Convert cluster to native Python int

        # Organiser les données par cluster et niveau de compétition
        if level not in organized_data:
            organized_data[level] = {}

        for item in data_level:
            cluster_id = item['cluster']
            if cluster_id not in organized_data[level]:
                organized_data[level][cluster_id] = {feature: [] for feature in features}
                organized_data[level][cluster_id]['hashtag'] = []

            # Ajouter les données au cluster
            for feature in features:
                organized_data[level][cluster_id][feature].append(item[feature])
            organized_data[level][cluster_id]['hashtag'].append(item['text'])

    # `organized_data` est maintenant un dictionnaire organisé par niveau de compétition et par cluster.

    return organized_data

import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
from sklearn.model_selection import GridSearchCV
from sklearn_extra.cluster import KMedoids
from sklearn.cluster import AgglomerativeClustering
from sklearn.cluster import DBSCAN
from sklearn.cluster import OPTICS
import seaborn as sns
from .generateCluster import generate_cluster_names

def clustering_domains(data):
    # Fonction pour générer des couleurs dynamiques
    def generate_colors(num_colors):
        """Génère une liste de couleurs distinctes en fonction du nombre d'éléments."""
        # Assurez-vous que num_colors est au moins 1
        num_colors = max(num_colors, 1)
        return sns.color_palette("husl", num_colors).as_hex()

    # Préparation des données
    # Chargement des données dans un DataFrame
    df = pd.DataFrame(data)

    # Conserver les valeurs initiales
    initial_df = df.copy()

    # Remplacement des valeurs manquantes par 0 et conversion en entiers pour spam_score
    df['spam_score'].fillna(0, inplace=True)  # Remplacer NaN par 0
    df['spam_score'] = df['spam_score'].astype(int)  # Convertir en entiers

    # Sélection des caractéristiques à utiliser pour le clustering
    features = ['totalBacklinks', 'domain_authority', 'page_authority', 'spam_score']

    # Normalisation des caractéristiques pour le clustering
    scaler = StandardScaler()
    df[features] = scaler.fit_transform(df[features])

    # Fonction pour calculer le score silhouette avec vérification des clusters
    def silhouette_score_wrapper(estimator, X):
        """Calcule le score silhouette s'il y a plus d'un cluster."""
        labels = estimator.fit_predict(X)
        if len(np.unique(labels)) > 1:
            return silhouette_score(X, labels)
        else:
            return np.nan

    # Définition des grilles de paramètres pour chaque algorithme
    param_grids = {
        'kmeans': {
            'n_clusters': range(2, 11),
        },
        'agglomerative': {
            'n_clusters': range(2, 11),
        },
        'kmedoids': {
            'n_clusters': range(2, 11),
        },
        'dbscan': {
            'eps': np.linspace(0.1, 2.0, 10),
            'min_samples': [2, 3, 4, 5, 6],  # Adaptation de min_samples
        },
        'optics': {
            'min_samples': [2, 3, 4, 5, 6],  # Adaptation de min_samples
            'max_eps': np.linspace(0.1, 2.0, 10),
        }
    }

    # Création des objets de clustering
    kmeans = KMeans(n_init=20, random_state=0)
    agglomerative = AgglomerativeClustering()
    kmedoids = KMedoids(random_state=0)
    dbscan = DBSCAN()
    optics = OPTICS()

    # Configuration de GridSearchCV pour chaque algorithme
    grid_searches = {
        'kmeans': GridSearchCV(estimator=kmeans, param_grid=param_grids['kmeans'],
                            scoring=silhouette_score_wrapper, cv=3, verbose=1),
        'agglomerative': GridSearchCV(estimator=agglomerative, param_grid=param_grids['agglomerative'],
                                    scoring=silhouette_score_wrapper, cv=3, verbose=1),
        'kmedoids': GridSearchCV(estimator=kmedoids, param_grid=param_grids['kmedoids'],
                                scoring=silhouette_score_wrapper, cv=3, verbose=1),
        'dbscan': GridSearchCV(estimator=dbscan, param_grid=param_grids['dbscan'],
                            scoring=silhouette_score_wrapper, cv=3, verbose=1),
        'optics': GridSearchCV(estimator=optics, param_grid=param_grids['optics'],
                            scoring=silhouette_score_wrapper, cv=3, verbose=1),
    }

    # Exécution de GridSearchCV pour chaque algorithme
    results = {}
    for name, grid_search in grid_searches.items():
        print(f"Exécution de GridSearchCV pour {name}...")
        grid_search.fit(df[features])
        results[name] = grid_search.best_params_
        print(f"Meilleurs paramètres pour {name}: {grid_search.best_params_}")

    # Application du meilleur modèle, par exemple KMeans
    best_kmeans_params = results['kmeans']
    kmeans = KMeans(n_clusters=best_kmeans_params['n_clusters'], n_init=20, random_state=0)
    df['cluster'] = kmeans.fit_predict(df[features])

    # Détecter le nombre total d'éléments (lignes dans le DataFrame)
    num_elements = len(df)

    # Génération des couleurs dynamiques pour les éléments
    colors = generate_colors(num_elements)

    initial_df['spam_score'].fillna(0, inplace=True)

    clusters = df['cluster'].tolist()
    domains = initial_df['Site'].tolist()
    domains_per_cluster = {}

    for domain, cluster in zip(domains, clusters):
        if cluster not in domains_per_cluster:
            domains_per_cluster[cluster] = []
        domains_per_cluster[cluster].append(domain)

    cluster_names = generate_cluster_names(domains_per_cluster)
    print("Cluster Names:", cluster_names)
        
    result_json = {
        "domains": initial_df['Site'].tolist(),
        "da_scores_percentages": initial_df['domain_authority'].tolist(),
        "pa_scores_percentages": initial_df['page_authority'].tolist(),
        "spam_scores": initial_df['spam_score'].tolist(),  # Utilisez les valeurs d'origine ici
        "total_backlinks": initial_df['totalBacklinks'].tolist(),
        "colors": colors,  # Couleurs dynamiques pour les éléments
        "clusters": df['cluster'].tolist()
    }
    print(result_json)
    return result_json
    # # Affichage du résultat JSON
    # print("Résultat JSON:")
    # print(json.dumps(result_json, indent=4))

    # # Sauvegarde du résultat JSON dans un fichier
    # with open('final_result.json', 'w') as f:
    #     json.dump(result_json, f, indent=4)


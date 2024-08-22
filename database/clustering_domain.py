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

def clustering_domains():
    # Fonction pour générer des couleurs dynamiques
    def generate_colors(num_colors):
        """Génère une liste de couleurs distinctes en fonction du nombre d'éléments."""
        # Assurez-vous que num_colors est au moins 1
        num_colors = max(num_colors, 1)
        return sns.color_palette("husl", num_colors).as_hex()

    # Préparation des données
    data = {
        'Site': ['facebook.com', 'bing.com', 'twitter.com', 'instagram.com', 'reddit.com',
                'altavista.com', 'github.com', 'linkedin.com', 'tiktok.com', 'canva.com',
                'gmail.com', 'ya.ru', 'yandex.ru', 'ask.com', 'lycos.com', 'duckduckgo.com',
                'tineye.com', 'baidu.com', 'gogle.com', 'yandex.com'],
        'totalBacklinks': [64552488179, 281220262, 55729341025, 37097540229, 1443483817,
                        10873884, 3128579142, 16105957084, 3257148852, 19996063,
                        15818721, 6787120, 1031289097, 8572704, 12576334, 27500918,
                        2558227, 12194099700, 34343, 47640094],
        'domain_authority': [96, 93, 95, 94, 92, 75, 96, 99, 95, 93,
                            93, 77, 93, 87, 92, 88, 75, 79, 45, 93],
        'page_authority': [100, 81, 100, 100, 89, 65, 93, 99, 86, 77,
                        80, 68, 81, 70, 82, 77, 67, 78, 53, 80],
        'spam_score': [1.0, 56.0, 31.0, 1.0, 3.0, None, 1.0, 1.0, 18.0, 13.0,
                    None, 22.0, 3.0, 3.0, 2.0, 9.0, 18.0, 1.0, None, 7.0]
    }

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

    # Créer les listes pour le résultat JSON en utilisant les valeurs initiales
    result_json = {
        "domains": initial_df['Site'].tolist(),
        "da_scores_percentages": initial_df['domain_authority'].tolist(),
        "pa_scores_percentages": initial_df['page_authority'].tolist(),
        "spam_scores": initial_df['spam_score'].tolist(),  # Utilisez les valeurs d'origine ici
        "total_backlinks": initial_df['totalBacklinks'].tolist(),
        "colors": colors,  # Couleurs dynamiques pour les éléments
        "clusters": df['cluster'].tolist()
    }
    return result_json
    # # Affichage du résultat JSON
    # print("Résultat JSON:")
    # print(json.dumps(result_json, indent=4))

    # # Sauvegarde du résultat JSON dans un fichier
    # with open('final_result.json', 'w') as f:
    #     json.dump(result_json, f, indent=4)

import requests
import pandas as pd

# Fonction pour obtenir les sites similaires via SimilarSites API
def get_similar_sites(domain):
    url = "https://similarsites1.p.rapidapi.com/v1/find-similar/"
    querystring = {"domain": domain}
    headers = {
        "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
        "x-rapidapi-host": "similarsites1.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        data = response.json()
        print("Raw API response:", data)  # Debugging: print the raw response

        return [site['Site'] for site in data.get("SimilarSites", [])]

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")

    return []

# Fonction pour obtenir les metrics de Majestic API
def get_majestic_metrics(site):
    try:
        url = "https://majestic1.p.rapidapi.com/url_metrics"
        querystring = {"url": site}
        headers = {
          "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
          "x-rapidapi-host": "majestic1.p.rapidapi.com"
        }
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Majestic metrics for site {site}: {e}")
        return {}  # Return an empty dictionary if there's an error

# Fonction pour obtenir les metrics de Moz API
def get_moz_metrics(site):
    try:
        url = "https://moz-da-pa1.p.rapidapi.com/v1/getDaPa"
        payload = {"q": site}
        headers = {
          "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
          "x-rapidapi-host": "moz-da-pa1.p.rapidapi.com",
          "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Moz metrics for site {site}: {e}")
        return []  # Return an empty list if there's an error

def get_domains_metrics(domain):
    sites = get_similar_sites(domain)
    print("Fetched sites:", sites)  # Debug print to check the sites

    # Initialiser une liste pour stocker les données
    data = []

    # Pour chaque site, obtenir les métriques des API Majestic et Moz
    for site in sites:
        majestic_data = get_majestic_metrics(site)
        print(f"Majestic data for {site}:", majestic_data)  # Debug print to check Majestic data

        moz_data = get_moz_metrics(site)
        print(f"Moz data for {site}:", moz_data)  # Debug print to check Moz data

        # Vérifier si les données sont valides avant de les utiliser
        if majestic_data and moz_data:
            try:
                # Construire un dictionnaire avec les données combinées
                combined_data = {
                    "Site": site,
                    "totalBacklinks": majestic_data.get("extbacklinks"),
                    "domain_authority": moz_data[0].get("domain_authority"),
                    "page_authority": moz_data[0].get("page_authority"),
                    "spam_score": moz_data[0].get("spam_score")
                }
                data.append(combined_data)
            except (KeyError, IndexError) as e:
                print(f"Error processing data for site {site}: {e}")

    # Convertir les données en DataFrame
    df_final = pd.DataFrame(data)

    # Afficher le DataFrame final
    return df_final

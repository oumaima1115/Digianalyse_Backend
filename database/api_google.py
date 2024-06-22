import requests

def search_google_posts(mention):
    url = "https://local-business-data.p.rapidapi.com/search"

    querystring = {
        "query": mention,
        "limit": "30"
    }

    headers = {
        "x-rapidapi-key": "bcf17d2b43msh7b704af227742b6p1f3cd4jsn4622d32cf51d",
        "x-rapidapi-host": "local-business-data.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code != 200:
        print(f"Failed to search posts for mention '{mention}', status code: {response.status_code}")
        return []

    data = response.json()
    media_entries = data.get("data", [])
    profiles = []

    for media in media_entries:
        about_info = media.get("about", {})
        text = about_info.get("summary", "")

        source_link = media.get("website", "")
        author = media.get("name", "")

        # Check if both source and source_link are not null or empty
        if text and source_link:
            profiles.append({
                "author": author,
                "source": "google",
                "text": text,
                "source_link": source_link
            })

    return profiles


def google_scrap(mention):
    profiles = search_google_posts(mention)
    if not profiles:
        print("No profiles found for the given keyword.")
        return []
    else:      
        return profiles

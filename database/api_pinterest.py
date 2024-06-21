from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from .testsavedata import save_to_json

#
#
#
#
# pinterest
#
#
#


def fetch_pinterest_data(profile):
    url = "https://pinterest-scraper.p.rapidapi.com/profile/"
    headers = {
        "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
        "x-rapidapi-host": "pinterest-scraper.p.rapidapi.com"
    }
    querystring = {"username": profile["username"]}
    response = requests.get(url, headers=headers, params=querystring)

    try:
        data = response.json()
        text = data.get("data", {}).get("about", "")
        like = data.get("data", {}).get("follower_count", 0)

        profile["like"] = like
        profile["description"] = text
    except Exception as e:
        print(f"An error occurred while fetching data for {profile['username']}: {e}")

    return profile

# def pinterest_scrap(request):
def pinterest_scrap(mention):
    # mention="nasa"
    items=30
    url_search = "https://pinterest-scraper.p.rapidapi.com/search/"
    headers = {
        "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
        "x-rapidapi-host": "pinterest-scraper.p.rapidapi.com"
    }
    querystring = {"keyword": mention}
    response = requests.get(url_search, headers=headers, params=querystring)

    profiles = []
    try:
        data = response.json()
        search_items = data.get("data", {}).get("items", [])
        
        for item in search_items:
            if len(profiles) >= items:
                break
            if item.get("username", ""):
                username = item.get("username", "")
                author = item.get("full_name", "")
                pinterest_post_source_link = f"https://www.pinterest.fr/{username}/"

                profiles.append({
                    "username": username,
                    "author": author,
                    "source": "pinterest",
                    "source_link": pinterest_post_source_link,
                    "mention": mention,
                    "mentions_texts": mention,
                    "hashtags_texts": mention,
                })
    except Exception as e:
        print(f"An error occurred during the search: {e}")
    
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_pinterest_data, profile) for profile in profiles]
        profiles_with_data = []
        for future in as_completed(futures):
            profile_data = future.result()
            if profile_data.get("like") and profile_data.get("description"):
                profiles_with_data.append(profile_data)
    # if profiles_with_data:
    #     save_to_json(profiles_with_data,"pinterest")
        
    # return JsonResponse(profiles_with_data, safe=False)

    return profiles_with_data
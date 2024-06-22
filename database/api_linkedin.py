import requests
import concurrent.futures

#
#
#
# Linkedin
#
#
#
#


def fetch_linkedin_profile_posts(profile):
    url = "https://linkedin-data-api.p.rapidapi.com/get-profile-posts"
    headers = {
        "x-rapidapi-key": "963b4e78b3msh95db887e195252bp112fd6jsn84e50ea45f6e",
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
    }

    querystring = {"username": profile["username"]}
    response = requests.get(url, headers=headers, params=querystring)
    if response.status_code != 200:
        print(f"Failed to fetch posts for {profile['username']}, status code: {response.status_code}")
        return None

    data = response.json()
    items = data.get("data", [])

    print(f"Fetched {len(items)} posts for profile: {profile['username']}")

    likes = []
    descriptions = []

    # Filter out empty or non-alphabetic descriptions
    for item in items:
        text = item.get("text", "").strip()
        if text and any(char.isalpha() for char in text):  # Check if text contains alphabetic characters
            descriptions.append(text)
            likes.append(item.get("likeCount", 0))

    # Check if descriptions list is empty after processing
    if not descriptions:
        print(f"No meaningful text found in the descriptions for {profile['username']}.")
        return None

    profile["like"] = likes
    profile["description"] = descriptions

    return profile


def search_linkedin_posts(mention):
    url = "https://linkedin-data-api.p.rapidapi.com/search-posts"
    payload = {
        "keyword": mention
    }
    headers = {
        "x-rapidapi-key": "963b4e78b3msh95db887e195252bp112fd6jsn84e50ea45f6e",
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print(f"Failed to search posts for mention '{mention}', status code: {response.status_code}")
        return []

    data = response.json()
    items = data.get("data", {}).get("items", [])

    print(f"Found {len(items)} posts for mention: {mention}")

    profiles = []
    for item in items:
        username = item.get("author", {}).get("username", "")
        author = item.get("author", {}).get("fullName", "")
        linkedin_post_source_link = item.get("url", {})

        profiles.append({
            "username": username,
            "author": author,
            "source": "linkedin",
            "source_link": linkedin_post_source_link,
            "mention": mention,
            "mentions_texts": mention,
            "hashtags_texts": mention,
        })

    return profiles


def linkedin_scrap(mention):
    profiles = search_linkedin_posts(mention)
    if not profiles:
        print("No profiles found for the given keyword.")
        return []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_linkedin_profile_posts, profile) for profile in profiles]
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                result = future.result()
                if result:
                    results.append(result)
                    print("Profile data:", result)
            except Exception as e:
                print(f"An error occurred: {e}")

    return results
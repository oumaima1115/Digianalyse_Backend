import concurrent
import time
import requests
from .testsavedata import save_to_json


#
#
#
# Instagram
#
#
#
#


def fetch_instagram_data(instagram_document):
    headers = {
        "x-rapidapi-key": "bcf17d2b43msh7b704af227742b6p1f3cd4jsn4622d32cf51d",
        "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
    }
    url_posts = "https://instagram-scraper-api2.p.rapidapi.com/v1.2/posts"
    author_id = instagram_document.get("author")
    querystring_2 = {"username_or_id_or_url": author_id}
    response = requests.get(url_posts, headers=headers, params=querystring_2)
    
    try:
        data = response.json()
        data_posts = data.get('data', {}).get('items', [])
        like = []
        description = []
        for data_element in data_posts:
            like_count = data_element.get('like_count')
            caption_text = data_element.get('caption', {}).get('text', "")
            if like_count and caption_text:  # Only add if both like and description are present
                like.append(like_count)
                description.append(caption_text)
        
        if like and description:
            instagram_document["like"] = like
            instagram_document["description"] = description
            return True  # Indicate that this document is valid
        else:
            return False  # Indicate that this document should be discarded
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

# def instagram_scrap(request):
def instagram_scrap(mention):
    # mention = "summer"
    instagram_rapid_api_url = "https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag"
    items = 10
    instagram_source = "instagram_app"
    hashtag_pattern = "#\w+"
    mention_pattern = "@\w+"
    y_m_dTHM_format = "%Y-%m-%dT%H:%M"
    post_type = "video"
    user_id = "12345"

    MAX_RETRIES = 2
    retry_count = 0
    instagram_captions_list = []

    while retry_count <= MAX_RETRIES:
        try:
            next_cursor = None

            while len(instagram_captions_list) < items:
                querystring = {"hashtag": mention, "pagination_token": next_cursor} if next_cursor else {"hashtag": mention}

                headers = {
                    "x-rapidapi-key": "bcf17d2b43msh7b704af227742b6p1f3cd4jsn4622d32cf51d",
                    "x-rapidapi-host": "instagram-scraper-api2.p.rapidapi.com"
                }
                response = requests.get(instagram_rapid_api_url, headers=headers, params=querystring)
                            
                data = response.json()
                pagination_token = data.get("pagination_token")
                if pagination_token:
                    next_cursor = pagination_token
                else:
                    break
                
                media_entries = data.get('data', {}).get('items', [])
                if not media_entries:
                    print("No posts found for Instagram")
                    break 
                
                for media_entry in media_entries:
                    try:
                        caption_text = media_entry.get("caption", {}).get("text", "")
                        hashtags = media_entry.get("caption", {}).get("hashtags", "")
                        mentions = media_entry.get("caption", {}).get("mentions", "")
                        author_id = media_entry.get("user", {}).get("username", "") 
                        instagram_post_source_link = media_entry.get("thumbnail_url")

                        instagram_document = {
                            "user_id": user_id,
                            "text": caption_text,
                            "type": post_type,
                            "source": "instagram",
                            "source_link": instagram_post_source_link,
                            "date": "2024/02/03",
                            "mention": mention,
                            "nbr_mentions": 8, 
                            "nbr_hashtags": 9, 
                            "mentions_texts": mentions, 
                            "hashtags_texts": hashtags, 
                            "author": author_id
                        }

                        instagram_captions_list.append(instagram_document)
                    except KeyError:
                        continue
                
                time.sleep(1)
            
            valid_documents = []
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(fetch_instagram_data, doc): doc for doc in instagram_captions_list}
                for future in concurrent.futures.as_completed(futures):
                    if future.result():  # Check if the document is valid
                        valid_documents.append(futures[future])

            instagram_captions_list = valid_documents

            if not instagram_captions_list:
                print(f"No Instagram posts found for mention {mention}")  
            else:
                print(f"Number of records in instagram_captions_list: {len(instagram_captions_list)}")
            break

        except Exception as e:
            print(f"An error occurred: {e}")
            retry_count += 1
            if retry_count > MAX_RETRIES:
                print("Max retry attempts reached. Exiting.")
                return []
    
    # if instagram_captions_list:
    #     save_to_json(instagram_captions_list, "instagram")

    # return JsonResponse(instagram_captions_list, safe=False)

    return instagram_captions_list
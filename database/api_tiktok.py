import re
import requests
import concurrent.futures
import urllib.parse


def process_tiktok(tiktoks_list, headers):
    tiktok_url = "https://tiktok-video-feature-summary.p.rapidapi.com/user/posts"
    author_data = []

    for tiktok in tiktoks_list:
        user_id = tiktok["user_id"]
        text = tiktok["text"]
        type = tiktok["type"]
        author = tiktok["author"]
        source = tiktok["source"]
        source_link = tiktok["source_link"]
        date = tiktok["date"]
        mention = tiktok["mention"]
        nbr_mentions = tiktok["nbr_mentions"]
        nbr_hashtags = tiktok["nbr_hashtags"]
        mentions_texts = tiktok["mentions_texts"]
        hashtags_texts = tiktok["hashtags_texts"]

        querystring = {"user_id": user_id, "count": 3}
        response = requests.get(tiktok_url, headers=headers, params=querystring)
        print(f"Response Status Code: {response.status_code}")  # Debug print
        print(f"Response Text: {response.text}")  # Debug print

        data_tiktoks = response.json().get('data', {}).get('videos', [])

        likes = []
        descriptions = []

        for data_tiktok in data_tiktoks:
            likes.append(data_tiktok.get("digg_count", 0))
            descriptions.append(data_tiktok.get("title", ""))

        author_data.append({
            "data": data_tiktoks,
            "like": likes,
            "description": descriptions,
            "author": author,
            "user_id": user_id,
            "text": text,
            "type": type,
            "source": source,
            "date":date,
            "source_link": source_link,
            "mention": mention,
            "nbr_mentions": nbr_mentions,
            "nbr_hashtags": nbr_hashtags,
            "mentions_texts": mentions_texts,
            "hashtags_texts": hashtags_texts
        })

    list_best_authors_sorted = author_data

    list_final_tiktok = []

    for author_data in list_best_authors_sorted:
        user_id = author_data["user_id"]
        author = author_data["author"]
        text = author_data["text"]
        type = author_data["type"]
        source = author_data["source"]
        source_link = author_data["source_link"]
        date = author_data["date"]
        mention = author_data["mention"]
        nbr_mentions = author_data["nbr_mentions"]
        nbr_hashtags = author_data["nbr_hashtags"]
        mentions_texts = author_data["mentions_texts"]
        hashtags_texts = author_data["hashtags_texts"]
        likes = author_data["like"]
        descriptions = author_data["description"]

        authors_tiktoks = [{
            "source": source,
            "like": likes,
            "description": descriptions,
            "author": author,
            "user_id": user_id,
            "text": text,
            "type": type,
            "source_link": source_link,
            "date": date,
            "mention": mention,
            "nbr_mentions": nbr_mentions,
            "nbr_hashtags": nbr_hashtags,
            "mentions_texts": mentions_texts,
            "hashtags_texts": hashtags_texts
        }]

        list_final_tiktok.append(authors_tiktoks)

    print("list_final_tiktok =", list_final_tiktok)

    return list_final_tiktok

# def tiktok_scrap(request):
def tiktok_scrap(mention):
#     mention = "Girl"
    tiktok_videos_list = []
    cursor = 0
    hashtag_pattern = "#\\w+"
    mention_pattern = "@\\w+"
    has_more = True
    tiktok_rapid_api_url = "https://tiktok-video-feature-summary.p.rapidapi.com/feed/search"
    tiktok_config_items = 10
    items = 10
    post_type = "video"

    # URL encode the mention keyword
    encoded_mention = urllib.parse.quote(mention)

    while has_more and len(tiktok_videos_list) < items:
        querystring = {"keywords":"Beautiful","count":"10","cursor":"0","region":"US","publish_time":"0","sort_type":"0"}

        headers = {
            "x-rapidapi-key": "bcf17d2b43msh7b704af227742b6p1f3cd4jsn4622d32cf51d",
            "x-rapidapi-host": "tiktok-video-feature-summary.p.rapidapi.com"
        }

        response = requests.get(tiktok_rapid_api_url, headers=headers, params=querystring)
        print(f"Search Response Status Code: {response.status_code}")  # Debug print
        print(f"Search Response Text: {response.text}")  # Debug print
        data = response.json()
        videos = data.get('data', {}).get('videos', [])
        cursor = data.get("cursor", 0)
        has_more = data.get("hasMore", False)

        for video in videos:
            try:
                video_id = video.get("id")
                author_username = video.get("author", {}).get("unique_id", "")
                video_title = video.get("title", "")
                author_id = video.get("author", {}).get("id", "")

                mentions = re.findall(mention_pattern, video_title)
                hashtags = re.findall(hashtag_pattern, video_title)

                tiktok_source_link = f"https://www.tiktok.com/@{author_username}/video/{video_id}"
                tiktok_document = {
                    "user_id": author_id,
                    "text": video_title,
                    "type": post_type,
                    "author": author_username,
                    "source": 'tiktok',
                    "source_link": tiktok_source_link,
                    "date": "03-08-2024",
                    "mention": mention,
                    "nbr_mentions": len(mentions),
                    "nbr_hashtags": len(hashtags),
                    "mentions_texts": mentions,
                    "hashtags_texts": hashtags
                }

                tiktok_videos_list.append(tiktok_document)
            except KeyError:
                continue

    list_tiktok = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_tiktok, tiktok_videos_list, headers)]
        for future in concurrent.futures.as_completed(futures):
            tiktok_profile_data = future.result()
            if tiktok_profile_data:
                list_tiktok.extend(tiktok_profile_data)

    flat_list_tiktok = [item for sublist in list_tiktok for item in sublist]
    print("length of flat_list_tiktok =", len(flat_list_tiktok))

    # if flat_list_tiktok:
    #     save_to_json(flat_list_tiktok, "tiktok")

    # return JsonResponse(flat_list_tiktok, safe=False)
    return flat_list_tiktok
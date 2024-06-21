import datetime
import concurrent
import re
import requests
from .testsavedata import save_to_json

#
#
#
# Twitter
#
#
#
#

def fetch_author_info(tweet_document):
    tweet_url = "https://twitter135.p.rapidapi.com/v2/UserTweets/"
    headers = {
        "x-rapidapi-key": "bcf17d2b43msh7b704af227742b6p1f3cd4jsn4622d32cf51d",
        "x-rapidapi-host": "twitter135.p.rapidapi.com"
    }
    author_id = tweet_document["user_id"]

    querystring = {"id": author_id, "count": "10"}
    response = requests.get(tweet_url, headers=headers, params=querystring).json()

    try:
        instructions_list = response['data']['user']['result']['timeline_v2']['timeline']['instructions']
        entries_data = next((i['entries'] for i in instructions_list if i.get('type') == 'TimelineAddEntries'), [])
        
        likes=[]
        descriptions=[]
        for entry in entries_data:
            try:
                tweet_data = entry['content']['itemContent']['tweet_results']['result']
                likes.append(tweet_data.get("legacy", {}).get("retweet_count", 0))
                descriptions.append(tweet_data.get("legacy", {}).get("full_text", ""))
            except KeyError:
                print("Error: Required keys not found in tweet data.")
                
        tweet_document["like"] = likes
        tweet_document["description"] = descriptions

    except KeyError:
        print("Error: Response structure does not match expectations.")

    return tweet_document

# def twitter_scrap(request):
def twitter_scrap(mention):
    # mention = "nike"
    twitter_rapid_api_url = "https://twitter135.p.rapidapi.com/Search/"
    twitter_source = "twitter_app"
    hashtag_pattern = "#\w+"
    mention_pattern = "@\w+"
    y_m_dTHM_format = "%Y-%m-%dT%H:%M"
    twitter_original_date_format = "%a %b %d %H:%M:%S %z %Y"
    post_type = "video"
    user_id = "12345"
    tweets_list = []
    headers = {
        "x-rapidapi-key": "bcf17d2b43msh7b704af227742b6p1f3cd4jsn4622d32cf51d",
        "x-rapidapi-host": "twitter135.p.rapidapi.com"
    }
    next_cursor = None
    previous_cursor = None
    tweets_collected = 0
    max_tweets = 2
    
    while tweets_collected < max_tweets:

        querystring = {"q":"nike","count":"10","safe_search":"true"}
        if next_cursor:
            querystring["cursor"] = next_cursor

        response = requests.get(twitter_rapid_api_url, headers=headers, params=querystring).json()
        # print("first response : ", response)

        try:
            instructions_list = response['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']
            entries_data = next((i['entries'] for i in instructions_list if i.get('type') == 'TimelineAddEntries'), [])

            for entry in entries_data:
                try:
                    tweet_data = entry['content']['itemContent']['tweet_results']['result']['legacy']
                    author_name = entry['content']['itemContent']['tweet_results']['result']['core']['user_results']['result']['legacy']['name']
                    tweet_id = tweet_data.get("id_str")
                    tweet_full_text = tweet_data.get("full_text")
                    mentions = re.findall(mention_pattern, tweet_full_text)
                    hashtags = re.findall(hashtag_pattern, tweet_full_text)
                    tweet_date = datetime.datetime.strptime(
                        tweet_data.get("created_at"),
                        twitter_original_date_format
                    ).strftime(y_m_dTHM_format)

                    tweet_source_link = f"https://twitter.com/user/status/{tweet_id}"
                    twitter_document = {
                        "user_id": tweet_data.get("user_id_str"),
                        "text": tweet_full_text,
                        "type": post_type,
                        "author": author_name,
                        "source": "twitter",
                        "source_link": tweet_source_link,
                        "date": tweet_date,
                        "mention": mention,
                        "nbr_mentions": len(mentions),
                        "nbr_hashtags": len(hashtags),
                        "mentions_texts": mentions,
                        "hashtags_texts": hashtags
                    }

                    tweets_list.append(twitter_document)
                    tweets_collected += 1                
                except KeyError:
                    continue

            next_cursor = next((e['content'].get('value') for e in entries_data if e['content'].get('entryType') == 'TimelineTimelineCursor'), None)

            if not next_cursor or next_cursor == previous_cursor:
                break
 
            previous_cursor = next_cursor
        except KeyError:
            print("Error: 'data' key not found in response.")
            break
        
    print("Number of tweets collected =", len(tweets_list))
    list_twitter = []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_author_info, tweet_document) for tweet_document in tweets_list]
                
        for future in concurrent.futures.as_completed(futures):
            if future.result().get("like") and future.result().get("description"):
                twitter_profile_data = future.result()
                print("twitter_profile_data = ", twitter_profile_data)

                if twitter_profile_data:
                    list_twitter.append(twitter_profile_data)

    # flat_list_twitter = [item for sublist in list_twitter for item in sublist]
    # print("length of flat_list_twitter = ", len(flat_list_twitter))

    # if list_twitter:
    #     save_to_json(list_twitter, "twitter")

    # return JsonResponse(list_twitter, safe=False)
    return list_twitter
from database.db import find_insert_or_delete_market_charts
from django.http import HttpResponseBadRequest, JsonResponse
from database.db import ElasticsearchConfig
import json
import os
import datetime
from django.views.decorators.csrf import csrf_exempt
from .db import find_insert_or_delete_market_charts
from .market import months_chart, search_total
from elasticsearch_dsl import Search,connections
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent
import re
from datetime import datetime
from django.http import JsonResponse
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import uuid
from .models import ScrapConfig
import time
import praw
import requests
import csv
import os
import aiohttp
import asyncio
from django.views.decorators.csrf import csrf_exempt
import gzip
from elasticsearch_dsl import connections
from elasticsearch.helpers import bulk
from .testsavedata import save_to_json


elasticsearch_instance = ElasticsearchConfig.get_instance() 


@csrf_exempt
def post(request):
    if request.method == 'POST':
        data_path = os.path.join(os.path.dirname(__file__), 'serialization', 'influencer-update.json')

        mention= request.POST.get("mention") 
        with open(data_path, 'r') as f:
            charts = json.load(f)
        
        res = find_insert_or_delete_market_charts(elasticsearch_instance.index_digianalyse, charts, mention)

        return JsonResponse(res, safe=False)
    else:
        return HttpResponseBadRequest("Only POST requests are allowed for this endpoint.")


@csrf_exempt
def get_user_data(request):
    if request.method == 'POST':
        es = connections.get_connection()
        
        mention_request = request.POST.get("mention")

        search = Search(using=es, index="digianalyse").query("match", mention=mention_request)

        response = search.execute()

        if response.hits.total.value > 0:
            user_data = response.hits[0].to_dict()
            mention = user_data.get('mention', "")
            influencer_chart = user_data.get('influencer_chart', {})
            leads_chart = user_data.get('leads_chart', {})
            
            return JsonResponse({
                "mention": mention,
                "influencer_chart": influencer_chart,
                "leads_chart": leads_chart
            })
        else:
            return JsonResponse({
                "message": "No data found for the provided mention"
            }, status=404)
    else:
        return HttpResponseBadRequest("Only POST requests are allowed for this endpoint.")


#
#
#
# Youtube
#
#
#
#

def get_video_details_in_bulk(youtube,
                                youtube_config,
                                video_id_batch,
                                video_ids,
                                document,
                                snippet,
                                hashtag_pattern,
                                mention_pattern,
                                y_m_dTHMSZ_format,
                                y_m_dTHM_format,
                                post_type,
                                youtube_source,
                                user_id,
                                mention,
                                scrap_config):

    video_detail_list = []
    joined_video_ids = ",".join(video_ids)
    video_response = youtube.videos().list(id=joined_video_ids, part=snippet).execute()

    if not video_response.get("items"):
        return []

    if isinstance(video_response, dict):
        for video_item in video_response.get("items", []):
            video_id = video_item.get('id')
            video_info = video_item.get(snippet, {})
            document_text = video_info.get("description")
            source_link = f"https://www.youtube.com/watch?v={video_id}"
            scrap_config.set_mention_pattern(document_text)
            mention_pattern = scrap_config.mention_pattern
            mentions = scrap_config.extract_mentions(document_text, mention_pattern)
            hashtags = re.findall(hashtag_pattern, document_text)
            if mentions or hashtags:
                post_uuid = str(uuid.uuid4())
                document_date = datetime.strptime(video_info.get("publishedAt"), y_m_dTHMSZ_format).strftime(y_m_dTHM_format)
                youtube_document = {
                    "source": youtube_source,
                    "author": video_info.get("channelTitle"),
                    "user_id": user_id,
                    "text": document_text,
                    "type": post_type,
                    "source_link": source_link,
                    "date": document_date,
                    "mention": mention,
                    "nbr_mentions": len(mentions),
                    "nbr_hashtags": len(hashtags),
                    "mentions_texts": mentions,
                    "hashtags_texts": hashtags,
                    "post_uuid": post_uuid
                }

                channel_id = video_info.get("channelId")
                if channel_id in document:
                    channel_details = document[channel_id]
                    youtube_document.update({
                        'description': channel_details.get('description', ''),
                        'like': channel_details.get('viewCount', '')
                    })
                video_detail_list.append(youtube_document)

    sorted_videos = sorted(video_detail_list, key=lambda x: int(x["like"]), reverse=True)[:4]
    
    return sorted_videos


def youtube_scrap(request):

    youtube_config={
        "service_version":"v3", 
        "google_key":"AIzaSyBZdHYAp2WWgm413pasORoGG2nJ179DYVg", 
        "snippet_part":"snippet",
        "type":"any",
        "max_results":10
    }
    start_date = datetime(2024, 2, 1).isoformat() + 'Z'
    end_date = datetime(2024, 2, 28).isoformat() + 'Z'
    hashtag_pattern = "#\w+"
    mention_pattern = "@\w+"
    y_m_dTHM_format = "%Y-%m-%dT%H:%M"
    y_m_dTHMSZ_format = "%Y-%m-%dT%H:%M:%SZ"
    post_type="video"
    youtube_source="youtube"
    mention= "surfing"
    user_id="123456"
    scrap_config = ScrapConfig()
    
    def get_video_ids_based_on_date(youtube, start_date, end_date):
        search_response = youtube.search().list(q=mention,
                                                type=youtube_config["type"],
                                                maxResults=youtube_config["max_results"],
                                                publishedAfter=start_date,
                                                publishedBefore=end_date,
                                                part=youtube_config["snippet_part"]).execute()
        
        #print("search response = ", search_response)
        video_ids = []
        channel_ids = []

        for item in search_response.get('items', []):
            if 'videoId' in item['id']: 
                video_ids.append(item['id']['videoId'])
                channel_ids.append(item['snippet']['channelId'])

        return video_ids, channel_ids

    snippet = youtube_config["snippet_part"]
    youtube = build(youtube_source, youtube_config["service_version"], developerKey=youtube_config["google_key"])
    video_ids, channel_ids = get_video_ids_based_on_date(youtube, start_date, end_date)
    video_id_batches = [video_ids[i:i + 5] for i in range(0, len(video_ids), 5)]

    #print("channel_ids = ", channel_ids)
    request = youtube.channels().list(
        maxResults=3,
        part="snippet,contentDetails,statistics",
        id=",".join(channel_ids)
    )
    response = request.execute()
    document = {}
    for item in response.get('items', []):
        channel_id = item['id']
        description = item['snippet']['description']
        view_count = item['statistics']['viewCount']
        document[channel_id] = {'description': description, 'viewCount': view_count}
    print("Document = ", document)

    def worker_function(video_id_batch):
        local_youtube = build(youtube_source,
                            youtube_config["service_version"], 
                            developerKey=youtube_config["google_key"])
        return get_video_details_in_bulk(local_youtube,
                                        youtube_config,
                                        video_id_batch,
                                        video_ids,
                                        document,
                                        snippet,
                                        hashtag_pattern,
                                        mention_pattern,
                                        y_m_dTHMSZ_format,
                                        y_m_dTHM_format,
                                        post_type,
                                        youtube_source,
                                        user_id,
                                        mention,
                                        scrap_config)

    with ThreadPoolExecutor(max_workers=2) as executor:
        future_to_batch = {executor.submit(worker_function, batch): batch for batch in video_id_batches}
        all_results = [future.result() for future in as_completed(future_to_batch)]

    youtube_posts_comments_list = [item for sublist in all_results for item in sublist]
    
    for i, item in enumerate(youtube_posts_comments_list):
        if isinstance(item, dict):
            for key, value in item.items():
                if isinstance(value, bytes):
                    youtube_posts_comments_list[i][key] = value.decode('utf-8')
        else:
            youtube_posts_comments_list.pop(i)

    if youtube_posts_comments_list:
        save_to_json(youtube_posts_comments_list, "youtube")

    return JsonResponse(youtube_posts_comments_list, safe=False)

#
#
#
# Redite
#
#
#
#

def process_comment(comment,
                    mention,
                    y_m_dTHM_format,
                    user_id,
                    comment_type,
                    reddit_source,
                    mention_pattern,
                    hashtag_pattern,
                    scrap_config):

    document_text = comment.body
    scrap_config.set_mention_pattern(document_text)
    mention_pattern = scrap_config.mention_pattern
    mentions = scrap_config.extract_mentions(document_text, mention_pattern)
    hashtags = re.findall(hashtag_pattern, document_text)
    document_author = comment.author
    comment_id = comment.id 
    post_id = comment.submission.id 
    reddit_comment_source_link = f"https://www.reddit.com/r/{comment.subreddit}/comments/{post_id}/-/{comment_id}"
    
    if (mentions or hashtags) and document_author is not None:
        comment_date = datetime.utcfromtimestamp(comment.created_utc).strftime(y_m_dTHM_format)

        reddit_document = {
            "user_id": user_id,
            "text": document_text,
            "type": comment_type,
            "author": document_author.name,
            "source": reddit_source,
            "source_link": reddit_comment_source_link,
            "date": comment_date,
            "mention": mention,
            "nbr_mentions": len(mentions),
            "nbr_hashtags": len(hashtags),
            "mentions_texts": mentions,
            "hashtags_texts": hashtags
        }
        return reddit_document
    return None
    
def process_profile_reddit(reddit_list,headers):
    reddit_author_data = []

    for reddit in reddit_list:
        user_id = reddit["user_id"]
        text = reddit["text"]
        type = reddit["type"]
        author_id = reddit["author"]
        source = reddit["source"]
        source_link = reddit["source_link"]
        date = reddit["date"]
        mention = reddit["mention"]
        nbr_mentions = reddit["nbr_mentions"]
        nbr_hashtags = reddit["nbr_hashtags"]
        mentions_texts = reddit["mentions_texts"]
        hashtags_texts = reddit["hashtags_texts"]

        profile_url = f"https://api.reddit.com/user/{author_id}/submitted"
        response = requests.get(profile_url, headers=headers)
        
        # if response.status_code == 200:
        try:
            data = response.json()
            
            likes = []
            reddit_post = data['data']['children']
            for post in reddit_post:
                reddit_data = post['data']
                likes.append(reddit_data.get('upvote_ratio', 0) )

            reddit_author_data.append({"data":reddit_post, 
                                "like":sum(likes)/len(likes) if likes else 0, 
                                "author_id":author_id, 
                                "user_id": user_id,
                                "text":text,
                                "type":type,
                                "source":source,
                                "source_link":source_link,
                                "date":date,
                                "mention":mention,
                                "nbr_mentions":nbr_mentions,
                                "nbr_hashtags":nbr_hashtags,
                                "mentions_texts":mentions_texts,
                                "hashtags_texts":hashtags_texts
                                })
        except KeyError:
            print("Error: Response structure does not match expectations.")

    list_best_reddit_authors_sorted = sorted(reddit_author_data, key=lambda x: x["like"], reverse=True)[:4]
    list_final_reddit=[]

    for author_data in list_best_reddit_authors_sorted:
        author_id = author_data["author_id"]
        data_reddits=author_data["data"]
        user_id = author_data["user_id"]
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

        authors_reddit = []
        for data_reddit_posts in data_reddits:
            like = data_reddit_posts['data']['upvote_ratio']
            selftext = data_reddit_posts['data']['selftext']
            title_reddit = data_reddit_posts['data']['title']

            authors_reddit.append({"source": source,
                                        "like": like,
                                        "author": author_id, 
                                        "description": selftext if selftext else title_reddit,
                                        "user_id": user_id,
                                        "text":text,
                                        "type":type,
                                        "source_link":source_link,
                                        "date":date,
                                        "mention":mention,
                                        "nbr_mentions":nbr_mentions,
                                        "nbr_hashtags":nbr_hashtags,
                                        "mentions_texts":mentions_texts,
                                        "hashtags_texts":hashtags_texts})
    list_final_reddit.append(sorted(authors_reddit, key=lambda x: x["like"], reverse=True)[:10])
    print("authors_reddit = ",authors_reddit)
    return list_final_reddit

def reddit_scrap(request):
    REDDIT_HEADERS = {"User-Agent": "MyBot/0.0.1"}
    reddit = praw.Reddit(
                client_id="q7J0g1si5uXJjRJkoMhtjQ",
                client_secret="xb4ag_Wr9iIY7i912LhIt_-LZUbqAA",
                username="oumaima_ayachi",
                password="W8HpJ4E5mT#L$5*",
                user_agent=REDDIT_HEADERS["User-Agent"]
            )
    subreddit=reddit.subreddit("python")
    limit=5
    y_m_dTHMSZ_format = "%Y-%m-%dT%H:%M:%SZ"
    start_date = datetime(2024, 2, 1).isoformat() + 'Z'
    end_date = datetime(2024, 2, 28).isoformat() + 'Z'
    hashtag_pattern = "#\w+"
    mention_pattern = "@\w+"
    y_m_dTHM_format = "%Y-%m-%dT%H:%M"
    post_type="post"
    comment_type="text"
    reddit_source="reddit"
    mention="nike"
    user_id="12345"
    scrap_config= ScrapConfig()
    start_time = time.time()

    initial_start_date = start_date
    initial_end_date = end_date

    start_date = datetime.strptime(initial_start_date, y_m_dTHMSZ_format)
    start_timestamp = int(start_date.timestamp())

    end_date = datetime.strptime(initial_end_date, y_m_dTHMSZ_format)
    end_timestamp = int(end_date.timestamp())

    reddit_posts_comments_list = []
    posts = subreddit.search("python", limit=5)

    post_list = list(posts)
    # print(f"Number of posts found: {len(post_list)}")

    if post_list:
        for post in post_list:
            mentions = ["nike","girl"]
            hashtags = []
            reddit_post_source_link = f"https://www.reddit.com{post.permalink}"
            document_text = post.title + post.selftext
            hashtags = re.findall(hashtag_pattern, document_text)
            document_author = post.author
            if (mentions or hashtags) and document_author is not None:
                document_date = datetime.utcfromtimestamp(post.created_utc).strftime(y_m_dTHM_format)
                reddit_document = {
                    "user_id": user_id,
                    "text": document_text,
                    "type": post_type,
                    "author": document_author.name,
                    "source": reddit_source,
                    "source_link": reddit_post_source_link,
                    "date": document_date,
                    "mention": mention,
                    "nbr_mentions": len(mentions),
                    "nbr_hashtags": len(hashtags),
                    "mentions_texts": mentions,
                    "hashtags_texts": hashtags
                }
                reddit_posts_comments_list.append(reddit_document)
                comments = post.comments
                comments.replace_more(limit=limit)

                with ThreadPoolExecutor() as executor:
                    args_for_comments = [(comment, mention, y_m_dTHM_format, user_id, comment_type, reddit_source, mention_pattern, hashtag_pattern, scrap_config) for comment in comments.list()]
                    results = list(executor.map(lambda args: process_comment(*args), args_for_comments))
                reddit_posts_comments_list.extend(filter(None, results))

    list_reddit = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(process_profile_reddit, reddit_posts_comments_list,REDDIT_HEADERS)]
        for future in concurrent.futures.as_completed(futures):
            reddit_profile_data = future.result()
            if reddit_profile_data:
                list_reddit.extend(reddit_profile_data)
                
    flat_list_reddit = [item for sublist in list_reddit for item in sublist]
    print("length of flat_list_reddit = ", len(flat_list_reddit))

    end_time = time.time()
    duration = end_time - start_time
    print(f"the reddit function took {duration:2f} seconds to complete ")
    # print(f"Number of records in reddit_posts_comments_list: {len(reddit_posts_comments_list)}")

    if flat_list_reddit:
        save_to_json(flat_list_reddit, "reddit")

    return JsonResponse(flat_list_reddit, safe=False)


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
        "X-RapidAPI-Key": "9edcbd1b9fmsha32eed8d12dc817p103628jsn9b4da960ede0",
        "X-RapidAPI-Host": "twitter135.p.rapidapi.com"
    }
    author_id = tweet_document["author"]

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
                likes.append(tweet_data.get("core", {}).get("user_results", {}).get("result", {}).get("legacy", {}).get("media_count", 0))
                descriptions.append(tweet_data.get("legacy", {}).get("full_text", ""))
            except KeyError:
                print("Error: Required keys not found in tweet data.")
                
        tweet_document["like"] = likes
        tweet_document["description"] = descriptions

    except KeyError:
        print("Error: Response structure does not match expectations.")

    return tweet_document

def twitter_scrap(request):
    twitter_rapid_api_url = "https://twitter135.p.rapidapi.com/Search/"
    mention = "nike"
    twitter_source = "twitter_app"
    hashtag_pattern = "#\w+"
    mention_pattern = "@\w+"
    y_m_dTHM_format = "%Y-%m-%dT%H:%M"
    twitter_original_date_format = "%a %b %d %H:%M:%S %z %Y"
    post_type = "video"
    user_id = "12345"
    tweets_list = []
    headers = {
        "X-RapidAPI-Key": "9edcbd1b9fmsha32eed8d12dc817p103628jsn9b4da960ede0",
        "X-RapidAPI-Host": "twitter135.p.rapidapi.com"
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
                    tweet_id = tweet_data.get("id_str")
                    tweet_full_text = tweet_data.get("full_text")
                    mentions = re.findall(mention_pattern, tweet_full_text)
                    hashtags = re.findall(hashtag_pattern, tweet_full_text)
                    tweet_date = datetime.strptime(
                        tweet_data.get("created_at"),
                        twitter_original_date_format
                    ).strftime(y_m_dTHM_format)

                    tweet_source_link = f"https://twitter.com/user/status/{tweet_id}"
                    twitter_document = {
                        "user_id": str(user_id),
                        "text": tweet_full_text,
                        "type": post_type,
                        "author": tweet_data.get("user_id_str"),
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

    save_to_json(list_twitter, "twitter")

    return JsonResponse(list_twitter, safe=False)

#
#
#
#
# Tiktok
#
#
#
#
#


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

def tiktok_scrap(request):
    mention = "Girl"
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
            "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
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

    if flat_list_tiktok:
        save_to_json(flat_list_tiktok, "tiktok")
    return JsonResponse(flat_list_tiktok, safe=False)


#
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
        "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
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

def instagram_scrap(request):
    instagram_rapid_api_url = "https://instagram-scraper-api2.p.rapidapi.com/v1/hashtag"
    mention = "summer"
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
                    "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
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
                        author_id = media_entry.get("user", {}).get("username", "") 
                        instagram_post_source_link = media_entry.get("link_to_post")

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
                            "mentions_texts": mention, 
                            "hashtags_texts": mention, 
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
    
    if instagram_captions_list:
        save_to_json(instagram_captions_list, "instagram")
    return JsonResponse(instagram_captions_list, safe=False)


#
#
#
# Linkedin
#
#
#
#
import requests
import concurrent.futures
import time

def fetch_linkedin_profile_posts(profile):
    url = "https://linkedin-data-api.p.rapidapi.com/get-profile-posts"
    headers = {
        "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com"
    }

    querystring = {"username": profile["username"]}
    response = requests.get(url, headers=headers, params=querystring)
    data = response.json()
    items = data.get("data", [])
    
    likes = []
    descriptions = []
    for item in items:
        descriptions.append(item.get("text", ""))
        likes.append(item.get("likeCount", 0))
    
    profile["like"] = likes
    profile["description"] = descriptions
    
    return profile


def search_linkedin_posts(mention):
    url = "https://linkedin-data-api.p.rapidapi.com/search-posts"
    payload = {
        "keyword": mention
    }
    headers = {
        "x-rapidapi-key": "9e451e62bfmsh238f3eae5164e8ep176494jsn31a69a8b3191",
        "x-rapidapi-host": "linkedin-data-api.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()
    items = data.get("data", {}).get("items", [])

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

def linkedin_scrap(request):
    mention="golang"
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
                results.append(result)
                print("Profile data:", result)
            except Exception as e:
                print(f"An error occurred: {e}")
    if results:
        save_to_json(results,"linkedin")

    return JsonResponse(results, safe=False)

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

def pinterest_scrap(request):
    items=30
    mention="nasa"
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

    save_to_json(profiles_with_data,"pinterest")
    
    return JsonResponse(profiles_with_data, safe=False)

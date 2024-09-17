import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import concurrent
import re
from database.models import ScrapConfig
import time
import praw
import requests

#
#
#
# Reddit
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
        comment_date = datetime.datetime.utcfromtimestamp(comment.created_utc).strftime(y_m_dTHM_format)

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

# def reddit_scrap(request):
def reddit_scrap(mention):
    # mention="nike"
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
    start_date = datetime.datetime(2024, 2, 1).isoformat() + 'Z'
    end_date = datetime.datetime(2024, 2, 28).isoformat() + 'Z'
    hashtag_pattern = "#\w+"
    mention_pattern = "@\w+"
    y_m_dTHM_format = "%Y-%m-%dT%H:%M"
    post_type="post"
    comment_type="text"
    reddit_source="reddit"
    user_id="12345"
    scrap_config= ScrapConfig()
    start_time = time.time()

    initial_start_date = start_date
    initial_end_date = end_date

    start_date = datetime.datetime.strptime(initial_start_date, y_m_dTHMSZ_format)
    start_timestamp = int(start_date.timestamp())

    end_date = datetime.datetime.strptime(initial_end_date, y_m_dTHMSZ_format)
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
                document_date = datetime.datetime.utcfromtimestamp(post.created_utc).strftime(y_m_dTHM_format)
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
    # print(f"Number of records in reddit_posts_comments_list: {len(reddit_posts_comments_list))

    # if flat_list_reddit:
    #     save_to_json(flat_list_reddit, "reddit")

    # return JsonResponse(flat_list_reddit, safe=False)
    return flat_list_reddit

from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from googleapiclient.discovery import build
import uuid
from database.models import ScrapConfig

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


# def youtube_scrap(request):
def youtube_scrap(mention):
    # mention= "surfing"
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

    # if youtube_posts_comments_list:
    #     save_to_json(youtube_posts_comments_list, "youtube")

    # return JsonResponse(youtube_posts_comments_list, safe=False)
    return youtube_posts_comments_list
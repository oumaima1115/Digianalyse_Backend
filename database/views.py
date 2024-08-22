import json
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from django.http import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from elasticsearch_dsl import Search, connections
from .db import find_insert_or_delete_market_charts, find_insert_or_delete_topics_charts,find_insert_or_delete_domain_charts, ElasticsearchConfig
from .combinefiletest import combine_json_files
from .modeling_eval import clustering
from .generate_theme import generate
from .generate_interests import generate_interests
from .api_youtube import youtube_scrap
from .api_instagram import instagram_scrap
from .api_linkedin import linkedin_scrap
from .api_reddit import reddit_scrap
from .api_tiktok import tiktok_scrap
from .api_twitter import twitter_scrap
from .api_google import google_scrap
from .api_best_hashtag import api_besthashtag
from .api_domains import get_domains_metrics
from .classification_hashtag import classificationHashtag
from .clustering_domain import clustering_domains

elasticsearch_instance = ElasticsearchConfig.get_instance()

@csrf_exempt
def bestdomains(request):
    try:
        if request.domain == 'POST':
            domain = request.POST.get("domain")

            if not domain:
                return HttpResponseBadRequest("Domain parameter is missing")

            es_conn = connections.get_connection()
            if not es_conn.ping():
                return HttpResponseBadRequest("Elasticsearch connection failed")
            
            domain_data = get_domain_data(domain)
            if domain_data:
                return domain_data
            else:
                # data = get_domains_metrics(domain)
                domain_data = clustering_domains()
                find_insert_or_delete_domain_charts(elasticsearch_instance.index_domain, domain, domain_data)
                
                if 'error' in domain_data:
                    return HttpResponseBadRequest(f"Error fetching data: {domain_data['error']}")
                
                return JsonResponse(domain_data, safe=False)
        else:
            return HttpResponseBadRequest("Only POST requests are allowed for this endpoint.")
    except Exception as e:
        # Log the exception if needed
        print(f"Exception occurred: {str(e)}")
        return HttpResponseBadRequest(f"An error occurred: {str(e)}")

def get_domain_data(domain):
    try:
        es_conn = connections.get_connection()
        if not es_conn.ping():
            return {"error": "Elasticsearch connection failed"}

        # Perform Elasticsearch search
        search = Search(using=es_conn, index="domain").query("match", domain=domain)
        response = search.execute()

        if response.hits.total.value > 0:
            # Extract user data if found
            domain_data = response.hits[0].to_dict()
            domain = domain_data.get('domain', "")
            domain_chart = domain_data.get('top_competitors', {})

            return {
                "domain": domain,
                "top_competitors": domain_chart,
            }
        else:
            return None
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}
    
@csrf_exempt
def besthashtag(request):
    try:
        # Check Elasticsearch connection
        es_conn = connections.get_connection()
        if not es_conn.ping():
            return HttpResponseBadRequest("Elasticsearch connection failed")
        
        # Process and update Elasticsearch with new data
        data_df = api_besthashtag()
        topics_data = classificationHashtag(data_df)
        find_insert_or_delete_topics_charts(elasticsearch_instance.index_seo, topics_data)
        
        # Fetch the latest topics data
        latest_topics_data = get_topics_data()
        
        if 'error' in latest_topics_data:
            return HttpResponseBadRequest(f"Error fetching data: {latest_topics_data['error']}")
        
        return JsonResponse(latest_topics_data, safe=False)
    
    except Exception as e:
        # Log the exception if needed
        print(f"Exception occurred: {str(e)}")
        return HttpResponseBadRequest(f"An error occurred: {str(e)}")


def get_topics_data():
    try:
        es_conn = connections.get_connection()
        if not es_conn.ping():
            return {"error": "Elasticsearch connection failed"}

        # Perform Elasticsearch search with sorting
        user_id = 123456789
        search = Search(using=es_conn, index="seo") \
            .query("match", user_id=user_id) \
            .sort("-timestamp") 
        response = search.execute()

        if response.hits.total.value > 0:
            # Extract user data if found
            user_data = response.hits[0].to_dict()
            user_id = user_data.get('user_id', "")
            topics_chart = user_data.get('topics_chart', {})

            return {
                "user_id": user_id,
                "topics_chart": topics_chart,
            }
        else:
            return None
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

def get_user_data(mention):
    try:
        es_conn = connections.get_connection()
        if not es_conn.ping():
            return {"error": "Elasticsearch connection failed"}

        # Perform Elasticsearch search
        search = Search(using=es_conn, index="digianalyse").query("match", mention=mention)
        response = search.execute()

        if response.hits.total.value > 0:
            # Extract user data if found
            user_data = response.hits[0].to_dict()
            mention = user_data.get('mention', "")
            influencer_chart = user_data.get('influencer_chart', {})
            leads_chart = user_data.get('leads_chart', {})

            return {
                "mention": mention,
                "influencer_chart": influencer_chart,
                "leads_chart": leads_chart
            }
        else:
            return None
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@csrf_exempt
def post(request):
    if request.method == 'POST':
        mention = request.POST.get("mention")

        if not mention:
            return HttpResponseBadRequest("Mention parameter is missing")

        try:
            es_conn = connections.get_connection()
            if not es_conn.ping():
                return HttpResponseBadRequest("Elasticsearch connection failed")
        except Exception as e:
            return HttpResponseBadRequest(f"Elasticsearch connection error: {str(e)}")

        try:
            data = get_user_data(mention)
            if data:
                res = data
            else:
                youtube_data = youtube_scrap(mention)
                instagram_data = instagram_scrap(mention)
                tiktok_data = tiktok_scrap(mention)
                twitter_data = twitter_scrap(mention)
                reddit_data = reddit_scrap(mention)
                linkedin_data = linkedin_scrap(mention)
                google_data = google_scrap(mention)

                influencer_data = combine_json_files(
                    youtube_data, 
                    instagram_data,
                    tiktok_data, 
                    twitter_data, 
                    reddit_data, 
                    linkedin_data
                )
                leads_data = combine_json_files(
                    google_data,
                    youtube_data, 
                    instagram_data,
                    tiktok_data, 
                    twitter_data, 
                    reddit_data, 
                    linkedin_data
                )
                
                cluster_themes = clustering(influencer_data, leads_data)
                influencer = generate(cluster_themes['influencers_charts'])
                leads = generate_interests(cluster_themes.get("leads_charts"))
                find_insert_or_delete_market_charts(elasticsearch_instance.index_digianalyse, influencer, leads, mention)

                res = {
                    "mention": mention,
                    "influencer_chart": influencer,
                    "leads_chart": leads
                }

            return JsonResponse(res, safe=False)

        except Exception as e:
            return HttpResponseBadRequest(f"An error occurred: {str(e)}")
    else:
        return HttpResponseBadRequest("Only POST requests are allowed for this endpoint.")

# Initialize the VADER sentiment analyzer
nltk.download('vader_lexicon')
sid = SentimentIntensityAnalyzer()

# Function to classify sentiment and return high and low scores
def classify_sentiment(text):
    ss = sid.polarity_scores(text)
    compound_score = ss['compound']
    
    if compound_score >= 0.05:
        return "praise", ss['pos'], ss['neg']
    elif compound_score <= -0.05:
        return "complaint", ss['neg'], ss['pos']
    else:
        return "request", ss['neu'], ss['neu']

@csrf_exempt
def predictclass(request):
    if request.method == 'POST':
        try:
            request_data = json.loads(request.body)

            if not isinstance(request_data, list):
                return JsonResponse({"error": "Expected a list of clusters"}, status=400)

            result = {}

            # Download VADER lexicon if not already downloaded
            nltk.download('vader_lexicon')

            for idx, cluster_data in enumerate(request_data):
                if not isinstance(cluster_data, dict):
                    return JsonResponse({"error": f"Expected a dictionary at index {idx}"}, status=400)

                cluster_texts = cluster_data.get('texts', [])

                cluster_result = {
                    "cluster_name": f"Cluster {idx}",
                    "interests": cluster_data.get("interests", ""),
                    "texts": [],
                    "sources": [],
                    "classes_prediction": []
                }

                for text_info in cluster_texts:
                    if not isinstance(text_info, dict):
                        return JsonResponse({"error": f"Expected a dictionary in texts at index {idx}"}, status=400)

                    text = text_info.get('text', '')
                    source = text_info.get('source', '')

                    # Classify the sentiment of the text using NLTK's Vader and get scores
                    sentiment_class, high_score, low_score = classify_sentiment(text)

                    cluster_result["texts"].append(text)
                    cluster_result["sources"].append(source)

                    # Create a classification prediction dictionary with varied scores
                    if sentiment_class == "praise":
                        prediction = [{"id": 0, "label": "praise", "score": high_score, "color": "#9966ff"},
                                      {"id": 1, "label": "complain", "score": low_score, "color": "#36a2eb"},
                                      {"id": 2, "label": "request", "score": low_score, "color": "#4bc0c0"}]
                    elif sentiment_class == "complaint":
                        prediction = [{"id": 0, "label": "complain", "score": high_score, "color": "#36a2eb"},
                                      {"id": 1, "label": "praise", "score": low_score, "color": "#9966ff"},
                                      {"id": 2, "label": "request", "score": low_score, "color": "#4bc0c0"}]
                    else:
                        prediction = [{"id": 0, "label": "request", "score": high_score, "color": "#4bc0c0"},
                                      {"id": 1, "label": "complain", "score": low_score, "color": "#36a2eb"},
                                      {"id": 2, "label": "praise", "score": low_score, "color": "#9966ff"}]

                    cluster_result["classes_prediction"].append(prediction)

                result[str(idx)] = cluster_result

            return JsonResponse(result, safe=False)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    else:
        return JsonResponse({"error": "Only POST method is allowed"}, status=405)

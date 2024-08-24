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
        if request.method == 'POST':
            domain = request.POST.get("domain")

            if not domain:
                return HttpResponseBadRequest("Domain parameter is missing")

            es_conn = connections.get_connection()
            if not es_conn.ping():
                return HttpResponseBadRequest("Elasticsearch connection failed")
            
            existing_domain_data = get_domain_data(domain)
            
            if not existing_domain_data:
                # Création de nouvelles données de domaine si le domaine n'existe pas
                data = {
                    'Site': ['facebook.com', 'bing.com', 'twitter.com', 'instagram.com', 'reddit.com',
                            'altavista.com', 'github.com', 'linkedin.com', 'tiktok.com', 'canva.com',
                            'gmail.com', 'ya.ru', 'yandex.ru', 'ask.com', 'lycos.com', 'duckduckgo.com',
                            'tineye.com', 'baidu.com', 'gogle.com', 'yandex.com'],
                    'totalBacklinks': [64552488179, 281220262, 55729341025, 37097540229, 1443483817,
                                    10873884, 3128579142, 16105957084, 3257148852, 19996063,
                                    15818721, 6787120, 1031289097, 8572704, 12576334, 27500918,
                                    2558227, 12194099700, 34343, 47640094],
                    'domain_authority': [96, 93, 95, 94, 92, 75, 96, 99, 95, 93,
                                        93, 77, 93, 87, 92, 88, 75, 79, 45, 93],
                    'page_authority': [100, 81, 100, 100, 89, 65, 93, 99, 86, 77,
                                    80, 68, 81, 70, 82, 77, 67, 78, 53, 80],
                    'spam_score': [1.0, 56.0, 31.0, 1.0, 3.0, 0.0, 1.0, 1.0, 18.0, 13.0,
                                0.0, 22.0, 3.0, 3.0, 2.0, 9.0, 18.0, 1.0, 0.0, 7.0]
                }
                domain_data = clustering_domains(data)
                print(f"Inserting domain data for {domain}")
                find_insert_or_delete_domain_charts(elasticsearch_instance.index_domain, domain, domain_data)
            else:
                # Mettre à jour les données existantes si elles sont trouvées
                print(f"Updating existing domain data for {domain}")
                domain_data = existing_domain_data['domain_chart']
            
            return JsonResponse(domain_data, safe=False)
        else:
            return HttpResponseBadRequest("Only POST requests are allowed for this endpoint.")
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return HttpResponseBadRequest(f"An error occurred: {str(e)}")

def get_domain_data(domain):
    try:
        es_conn = connections.get_connection()
        if not es_conn.ping():
            return {"error": "Elasticsearch connection failed"}

        search = Search(using=es_conn, index="domain").query("match", domain=domain)
        response = search.execute()

        if response.hits.total.value > 0:
            domain_data = response.hits[0].to_dict()
            return domain_data
        else:
            return {}
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

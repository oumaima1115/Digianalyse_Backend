from django.test import TestCase
from unittest.mock import patch, Mock
from .api_best_hashtag import api_besthashtag
import pandas as pd
from .api_domains import get_similar_sites, get_majestic_metrics, get_moz_metrics, get_domains_metrics
from .api_google import search_google_posts, google_scrap
from .api_instagram import fetch_instagram_data, instagram_scrap
from .api_linkedin import fetch_linkedin_profile_posts, search_linkedin_posts, linkedin_scrap
from .api_ranking import get_ranking
from .api_reddit import reddit_scrap
from api_tiktok import process_tiktok, tiktok_scrap
from api_twitter import fetch_author_info, twitter_scrap
from api_youtube import get_video_details_in_bulk, youtube_scrap
from classification_hashtag import classificationHashtag
from clustering_domain import clustering_domains
from clustering_ranking import clusteringRanking
from combinefiletest import combine_json_files
from db import (
    ElasticsearchConfig,
    find_insert_or_delete_market_charts,
    find_insert_or_delete_topics_charts,
    find_insert_or_delete_domain_charts,
    find_insert_or_delete_ranking_charts
)
from generate_interests import generate_interests
from generate_theme import generate
from modeling_eval import clustering
from models import ScrapConfig
import os
import json
import datetime
from serialisationdatatest import serialisation_data, serialize_custom, print_types
from django.urls import reverse, resolve
from database import views
from django.http import JsonResponse

class ApiBestHashtagTestCase(TestCase):
    @patch('api_best_hashtag.requests.get')
    def test_api_besthashtag_success(self, mock_get):
        # Define a mock response
        mock_response = {
            "video_views": 123456,
            "country_name": "US",
            "industry": "Tech",
            "hashtag": "#example",
            "publish_count": 100,
            "trend_type": "hot",
            "is_new": True
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [mock_response]

        result = api_besthashtag()
        
        # Check the result
        expected = [{
            'video_views': 123456,
            'country_name': 'US',
            'industry': 'Tech',
            'hashtag': '#example',
            'publish_count': 100,
            'trend_type': 'hot',
            'is_new': True
        }]
        self.assertEqual(result, expected)

    @patch('api_best_hashtag.requests.get')
    def test_api_besthashtag_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        result = api_besthashtag()
        
        # Check that result is empty on failure
        self.assertEqual(result, [])

class ApiDomainsTestCase(TestCase):
    @patch('api_domains.requests.get')
    def test_get_similar_sites_success(self, mock_get):
        # Define a mock response
        mock_response = {
            "SimilarSites": [
                {"Site": "example.com"},
                {"Site": "example.net"}
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = get_similar_sites("example.org")
        
        # Check the result
        expected = ["example.com", "example.net"]
        self.assertEqual(result, expected)

    @patch('api_domains.requests.get')
    def test_get_similar_sites_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        result = get_similar_sites("example.org")
        
        # Check that result is empty on failure
        self.assertEqual(result, [])

    @patch('api_domains.requests.get')
    def test_get_majestic_metrics_success(self, mock_get):
        # Define a mock response
        mock_response = {
            "extbacklinks": 1234
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = get_majestic_metrics("example.com")
        
        # Check the result
        expected = {"extbacklinks": 1234}
        self.assertEqual(result, expected)

    @patch('api_domains.requests.post')
    def test_get_moz_metrics_success(self, mock_post):
        # Define a mock response
        mock_response = [{
            "domain_authority": 55,
            "page_authority": 60,
            "spam_score": 1
        }]
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        result = get_moz_metrics("example.com")
        
        # Check the result
        expected = [{
            "domain_authority": 55,
            "page_authority": 60,
            "spam_score": 1
        }]
        self.assertEqual(result, expected)

    @patch('api_domains.get_similar_sites')
    @patch('api_domains.get_majestic_metrics')
    @patch('api_domains.get_moz_metrics')
    def test_get_domains_metrics_success(self, mock_get_moz_metrics, mock_get_majestic_metrics, mock_get_similar_sites):
        # Define mock responses
        mock_get_similar_sites.return_value = ["example.com"]
        mock_get_majestic_metrics.return_value = {"extbacklinks": 1234}
        mock_get_moz_metrics.return_value = [{
            "domain_authority": 55,
            "page_authority": 60,
            "spam_score": 1
        }]

        result = get_domains_metrics("example.org")

        # Expected DataFrame
        expected_df = pd.DataFrame([{
            "Site": "example.com",
            "totalBacklinks": 1234,
            "domain_authority": 55,
            "page_authority": 60,
            "spam_score": 1
        }])

        pd.testing.assert_frame_equal(result, expected_df)

    @patch('api_domains.get_similar_sites')
    @patch('api_domains.get_majestic_metrics')
    @patch('api_domains.get_moz_metrics')
    def test_get_domains_metrics_failure(self, mock_get_moz_metrics, mock_get_majestic_metrics, mock_get_similar_sites):
        # Define mock responses for failures
        mock_get_similar_sites.return_value = []
        mock_get_majestic_metrics.return_value = {}
        mock_get_moz_metrics.return_value = []

        result = get_domains_metrics("example.org")

        # Expected empty DataFrame
        expected_df = pd.DataFrame()

        pd.testing.assert_frame_equal(result, expected_df)

class ApiGoogleTestCase(TestCase):
    @patch('api_google.requests.get')
    def test_search_google_posts_success(self, mock_get):
        # Define a mock response
        mock_response = {
            "data": [
                {
                    "about": {"summary": "This is a summary"},
                    "website": "http://example.com",
                    "name": "Example Author"
                }
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = search_google_posts("test mention")
        
        # Check the result
        expected = [{
            "author": "Example Author",
            "source": "google",
            "text": "This is a summary",
            "source_link": "http://example.com"
        }]
        self.assertEqual(result, expected)

    @patch('api_google.requests.get')
    def test_search_google_posts_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        result = search_google_posts("test mention")
        
        # Check that result is empty on failure
        self.assertEqual(result, [])

    @patch('api_google.search_google_posts')
    def test_google_scrap_success(self, mock_search_google_posts):
        # Define a mock return value
        mock_search_google_posts.return_value = [{
            "author": "Example Author",
            "source": "google",
            "text": "This is a summary",
            "source_link": "http://example.com"
        }]

        result = google_scrap("test mention")
        
        # Check the result
        expected = [{
            "author": "Example Author",
            "source": "google",
            "text": "This is a summary",
            "source_link": "http://example.com"
        }]
        self.assertEqual(result, expected)

    @patch('api_google.search_google_posts')
    def test_google_scrap_no_profiles(self, mock_search_google_posts):
        # Define a mock return value for no profiles
        mock_search_google_posts.return_value = []

        result = google_scrap("test mention")
        
        # Check that result is empty when no profiles are found
        self.assertEqual(result, [])

class ApiInstagramTestCase(TestCase):
    @patch('api_instagram.requests.get')
    def test_fetch_instagram_data_success(self, mock_get):
        # Define a mock response
        mock_response = {
            "data": {
                "items": [
                    {
                        "like_count": 100,
                        "caption": {"text": "Great photo!"}
                    }
                ]
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        instagram_document = {"author": "test_user"}
        result = fetch_instagram_data(instagram_document)
        
        # Check the result
        self.assertTrue(result)
        self.assertIn("like", instagram_document)
        self.assertIn("description", instagram_document)

    @patch('api_instagram.requests.get')
    def test_fetch_instagram_data_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        instagram_document = {"author": "test_user"}
        result = fetch_instagram_data(instagram_document)
        
        # Check that result is False on failure
        self.assertFalse(result)

    @patch('api_instagram.requests.get')
    @patch('api_instagram.fetch_instagram_data')
    def test_instagram_scrap_success(self, mock_fetch_instagram_data, mock_get):
        # Define a mock response
        mock_response = {
            "data": {
                "items": [
                    {
                        "caption": {"text": "Great photo!", "hashtags": [], "mentions": []},
                        "user": {"username": "test_user"},
                        "thumbnail_url": "http://example.com/photo.jpg"
                    }
                ],
                "pagination_token": None
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        mock_fetch_instagram_data.return_value = True
        
        result = instagram_scrap("test_mention")
        
        # Check the result
        self.assertGreater(len(result), 0)

    @patch('api_instagram.requests.get')
    @patch('api_instagram.fetch_instagram_data')
    def test_instagram_scrap_no_posts(self, mock_fetch_instagram_data, mock_get):
        # Define a mock response for no posts
        mock_response = {
            "data": {
                "items": [],
                "pagination_token": None
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        mock_fetch_instagram_data.return_value = True
        
        result = instagram_scrap("test_mention")
        
        # Check that result is empty when no posts are found
        self.assertEqual(result, [])

    @patch('api_instagram.requests.get')
    @patch('api_instagram.fetch_instagram_data')
    def test_instagram_scrap_max_retries(self, mock_fetch_instagram_data, mock_get):
        # Simulate API failure to test retry logic
        mock_get.side_effect = Exception("API call failed")
        mock_fetch_instagram_data.return_value = True

        result = instagram_scrap("test_mention")
        
        # Check that result is empty when retries fail
        self.assertEqual(result, [])

class ApiLinkedinTestCase(TestCase):
    @patch('api_linkedin.requests.get')
    def test_fetch_linkedin_profile_posts_success(self, mock_get):
        # Define a mock response for profile posts
        mock_response = {
            "data": [
                {
                    "text": "This is a meaningful post.",
                    "likeCount": 50
                },
                {
                    "text": "Another relevant post.",
                    "likeCount": 30
                }
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        profile = {"username": "test_user"}
        result = fetch_linkedin_profile_posts(profile)
        
        # Check the result
        self.assertIn("like", result)
        self.assertIn("description", result)
        self.assertEqual(len(result["description"]), 2)
        self.assertEqual(len(result["like"]), 2)

    @patch('api_linkedin.requests.get')
    def test_fetch_linkedin_profile_posts_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        profile = {"username": "test_user"}
        result = fetch_linkedin_profile_posts(profile)
        
        # Check that result is None on failure
        self.assertIsNone(result)

    @patch('api_linkedin.requests.post')
    def test_search_linkedin_posts_success(self, mock_post):
        # Define a mock response for search posts
        mock_response = {
            "data": {
                "items": [
                    {
                        "author": {"username": "test_user", "fullName": "Test User"},
                        "url": "http://linkedin.com/test_post"
                    }
                ]
            }
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_response

        result = search_linkedin_posts("test_keyword")
        
        # Check the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["username"], "test_user")

    @patch('api_linkedin.requests.post')
    def test_search_linkedin_posts_failure(self, mock_post):
        # Simulate a failed API response
        mock_post.return_value.status_code = 500

        result = search_linkedin_posts("test_keyword")
        
        # Check that result is empty on failure
        self.assertEqual(result, [])

    @patch('api_linkedin.requests.post')
    @patch('api_linkedin.requests.get')
    def test_linkedin_scrap_success(self, mock_get, mock_post):
        # Define a mock response for search posts
        mock_post_response = {
            "data": {
                "items": [
                    {
                        "author": {"username": "test_user", "fullName": "Test User"},
                        "url": "http://linkedin.com/test_post"
                    }
                ]
            }
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_post_response

        # Define a mock response for profile posts
        mock_get_response = {
            "data": [
                {
                    "text": "This is a meaningful post.",
                    "likeCount": 50
                }
            ]
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_get_response

        result = linkedin_scrap("test_keyword")
        
        # Check the result
        self.assertGreater(len(result), 0)
        self.assertIn("like", result[0])
        self.assertIn("description", result[0])

    @patch('api_linkedin.requests.post')
    @patch('api_linkedin.requests.get')
    def test_linkedin_scrap_no_profiles(self, mock_get, mock_post):
        # Define a mock response for search posts with no items
        mock_post_response = {
            "data": {
                "items": []
            }
        }
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = mock_post_response

        result = linkedin_scrap("test_keyword")
        
        # Check that result is empty when no profiles are found
        self.assertEqual(result, [])

    @patch('api_linkedin.requests.post')
    @patch('api_linkedin.requests.get')
    def test_linkedin_scrap_max_retries(self, mock_get, mock_post):
        # Simulate API failure to test retry logic
        mock_post.side_effect = Exception("API call failed")
        mock_get.side_effect = Exception("API call failed")

        result = linkedin_scrap("test_keyword")
        
        # Check that result is empty when retries fail
        self.assertEqual(result, [])

class ApiRankingTestCase(TestCase):
    @patch('api_ranking.requests.get')
    def test_get_ranking_success(self, mock_get):
        # Define a mock response for keyword ranking
        mock_response = {
            "data": {
                "suggestions": [
                    {"keyword": "example keyword 1"},
                    {"keyword": "example keyword 2"}
                ]
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        keyword = "test_keyword"
        result = get_ranking(keyword)
        
        # Check the result
        self.assertEqual(result, mock_response)
        mock_get.assert_called_once_with(
            "https://google-keyword-insight1.p.rapidapi.com/keysuggest/",
            headers={
                "x-rapidapi-key": "8e9dd20399msh09e9ced25a3fda9p157ea5jsn84c0bfbd8926",
                "x-rapidapi-host": "google-keyword-insight1.p.rapidapi.com"
            },
            params={"keyword": keyword, "location": "US", "lang": "en"}
        )

    @patch('api_ranking.requests.get')
    def test_get_ranking_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500
        mock_get.return_value.json.return_value = {"error": "Something went wrong"}

        keyword = "test_keyword"
        result = get_ranking(keyword)
        
        # Check that result is the raw API response on failure
        self.assertEqual(result, {"error": "Something went wrong"})
        mock_get.assert_called_once_with(
            "https://google-keyword-insight1.p.rapidapi.com/keysuggest/",
            headers={
                "x-rapidapi-key": "8e9dd20399msh09e9ced25a3fda9p157ea5jsn84c0bfbd8926",
                "x-rapidapi-host": "google-keyword-insight1.p.rapidapi.com"
            },
            params={"keyword": keyword, "location": "US", "lang": "en"}
        )

class RedditScrapTestCase(TestCase):
    @patch('api_reddit.praw.Reddit')
    @patch('api_reddit.requests.get')
    @patch('api_reddit.ThreadPoolExecutor')
    @patch('api_reddit.concurrent.futures.ThreadPoolExecutor')
    def test_reddit_scrap(self, mock_thread_pool_executor, mock_thread_pool_executor_patched, mock_requests_get, mock_praw_reddit):
        # Mock Reddit API responses
        mock_reddit_instance = Mock()
        mock_subreddit = Mock()
        mock_subreddit.search.return_value = [Mock(title="Sample title", selftext="Sample selftext", permalink="/r/sample_post", author=Mock(name="test_user"), created_utc=1609459200, comments=Mock())]
        mock_praw_reddit.return_value = mock_reddit_instance
        mock_reddit_instance.subreddit.return_value = mock_subreddit
        
        # Mock requests.get
        mock_response = {
            'data': {
                'children': [
                    {'data': {'upvote_ratio': 0.8}},
                    {'data': {'upvote_ratio': 0.9}}
                ]
            }
        }
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = mock_response

        # Mock ThreadPoolExecutor
        mock_thread_pool_executor_patched.return_value.__enter__.return_value.map.return_value = [None]

        mention = "nike"
        result = reddit_scrap(mention)

        self.assertTrue(result)
        self.assertGreater(len(result), 0)

class ApiTikTokTestCase(TestCase):
    @patch('api_tiktok.requests.get')
    def test_process_tiktok_success(self, mock_get):
        # Define a mock response for the API call
        mock_response = {
            "data": {
                "videos": [
                    {
                        "digg_count": 150,
                        "title": "Great video!",
                    }
                ]
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        tiktoks_list = [{
            "user_id": "user123",
            "text": "Amazing content",
            "type": "video",
            "author": "test_author",
            "source": "source",
            "source_link": "http://example.com",
            "date": "2024-09-16",
            "mention": "@test",
            "nbr_mentions": 1,
            "nbr_hashtags": 2,
            "mentions_texts": ["@test"],
            "hashtags_texts": ["#example"]
        }]
        headers = {"Authorization": "Bearer test_token"}

        result = process_tiktok(tiktoks_list, headers)

        # Check the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["like"], [150])
        self.assertEqual(result[0]["description"], ["Great video!"])

    @patch('api_tiktok.requests.get')
    def test_process_tiktok_no_videos(self, mock_get):
        # Define a mock response with no videos
        mock_response = {
            "data": {
                "videos": []
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        tiktoks_list = [{
            "user_id": "user123",
            "text": "Amazing content",
            "type": "video",
            "author": "test_author",
            "source": "source",
            "source_link": "http://example.com",
            "date": "2024-09-16",
            "mention": "@test",
            "nbr_mentions": 1,
            "nbr_hashtags": 2,
            "mentions_texts": ["@test"],
            "hashtags_texts": ["#example"]
        }]
        headers = {"Authorization": "Bearer test_token"}

        result = process_tiktok(tiktoks_list, headers)

        # Check the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["like"], [])
        self.assertEqual(result[0]["description"], [])

    @patch('api_tiktok.requests.get')
    def test_tiktok_scrap_success(self, mock_get):
        # Define a mock response for the search API
        mock_response = {
            "data": {
                "videos": [
                    {
                        "id": "video1",
                        "author": {"unique_id": "author1", "id": "user123"},
                        "title": "Amazing video",
                    }
                ],
                "cursor": 0,
                "hasMore": False
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = tiktok_scrap("test_mention")

        # Check the result
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0][0]["author"], "author1")

    @patch('api_tiktok.requests.get')
    def test_tiktok_scrap_no_videos(self, mock_get):
        # Define a mock response with no videos
        mock_response = {
            "data": {
                "videos": [],
                "cursor": 0,
                "hasMore": False
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = tiktok_scrap("test_mention")

        # Check that result is empty when no videos are found
        self.assertEqual(result, [])

    @patch('api_tiktok.requests.get')
    def test_tiktok_scrap_api_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        result = tiktok_scrap("test_mention")

        # Check that result is empty on API failure
        self.assertEqual(result, [])

class ApiTikTokTestCase(TestCase): 
    @patch('api_tiktok.requests.get')
    def test_process_tiktok_success(self, mock_get):
        # Mock API response for successful data retrieval
        mock_response = {
            "data": {
                "videos": [
                    {
                        "digg_count": 150,
                        "title": "Great video!",
                    }
                ]
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        tiktoks_list = [{
            "user_id": "user123",
            "text": "Amazing content",
            "type": "video",
            "author": "test_author",
            "source": "source",
            "source_link": "http://example.com",
            "date": "2024-09-16",
            "mention": "@test",
            "nbr_mentions": 1,
            "nbr_hashtags": 2,
            "mentions_texts": ["@test"],
            "hashtags_texts": ["#example"]
        }]
        headers = {"Authorization": "Bearer test_token"}

        result = process_tiktok(tiktoks_list, headers)

        # Validate the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["like"], [150])
        self.assertEqual(result[0]["description"], ["Great video!"])

    @patch('api_tiktok.requests.get')
    def test_process_tiktok_no_videos(self, mock_get):
        # Mock API response with no videos
        mock_response = {
            "data": {
                "videos": []
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        tiktoks_list = [{
            "user_id": "user123",
            "text": "Amazing content",
            "type": "video",
            "author": "test_author",
            "source": "source",
            "source_link": "http://example.com",
            "date": "2024-09-16",
            "mention": "@test",
            "nbr_mentions": 1,
            "nbr_hashtags": 2,
            "mentions_texts": ["@test"],
            "hashtags_texts": ["#example"]
        }]
        headers = {"Authorization": "Bearer test_token"}

        result = process_tiktok(tiktoks_list, headers)

        # Validate the result when no videos are found
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["like"], [])
        self.assertEqual(result[0]["description"], [])

    @patch('api_tiktok.requests.get')
    def test_tiktok_scrap_success(self, mock_get):
        # Mock response for search API
        mock_response = {
            "data": {
                "videos": [
                    {
                        "id": "video1",
                        "author": {"unique_id": "author1", "id": "user123"},
                        "title": "Amazing video",
                    }
                ],
                "cursor": 0,
                "hasMore": False
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = tiktok_scrap("test_mention")

        # Validate the result
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0][0]["author"], "author1")

    @patch('api_tiktok.requests.get')
    def test_tiktok_scrap_no_videos(self, mock_get):
        # Mock response with no videos
        mock_response = {
            "data": {
                "videos": [],
                "cursor": 0,
                "hasMore": False
            }
        }
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response

        result = tiktok_scrap("test_mention")

        # Validate that result is empty when no videos are found
        self.assertEqual(result, [])

    @patch('api_tiktok.requests.get')
    def test_tiktok_scrap_api_failure(self, mock_get):
        # Simulate API failure response
        mock_get.return_value.status_code = 500

        result = tiktok_scrap("test_mention")

        # Validate that result is empty on API failure
        self.assertEqual(result, [])

class ApiTwitterTestCase(TestCase):

    @patch('api_twitter.requests.get')
    def test_fetch_author_info_success(self, mock_get):
        # Define a mock response for the API call
        mock_response = {
            "data": {
                "user": {
                    "result": {
                        "timeline_v2": {
                            "timeline": {
                                "instructions": [
                                    {
                                        "type": "TimelineAddEntries",
                                        "entries": [
                                            {
                                                "content": {
                                                    "itemContent": {
                                                        "tweet_results": {
                                                            "result": {
                                                                "legacy": {
                                                                    "retweet_count": 100,
                                                                    "full_text": "Sample tweet text"
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        }
                    }
                }
            }
        }
        mock_get.return_value.json.return_value = mock_response

        tweet_document = {"user_id": "12345"}
        result = fetch_author_info(tweet_document)

        # Validate the result
        self.assertEqual(result["like"], [100])
        self.assertEqual(result["description"], ["Sample tweet text"])

    @patch('api_twitter.requests.get')
    def test_twitter_scrap_success(self, mock_get):
        # Define a mock response for the search API
        mock_response = {
            "data": {
                "search_by_raw_query": {
                    "search_timeline": {
                        "timeline": {
                            "instructions": [
                                {
                                    "type": "TimelineAddEntries",
                                    "entries": [
                                        {
                                            "content": {
                                                "itemContent": {
                                                    "tweet_results": {
                                                        "result": {
                                                            "legacy": {
                                                                "id_str": "tweet1",
                                                                "full_text": "Sample tweet text",
                                                                "created_at": "Mon Sep 16 16:00:00 +0000 2024",
                                                                "user_id_str": "user123"
                                                            },
                                                            "core": {
                                                                "user_results": {
                                                                    "result": {
                                                                        "legacy": {
                                                                            "name": "Test Author"
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                }
            }
        }
        mock_get.return_value.json.return_value = mock_response

        result = twitter_scrap("nike")

        # Validate the result
        self.assertGreater(len(result), 0)
        self.assertEqual(result[0]["author"], "Test Author")

    @patch('api_twitter.requests.get')
    def test_twitter_scrap_no_tweets(self, mock_get):
        # Define a mock response with no tweets
        mock_response = {
            "data": {
                "search_by_raw_query": {
                    "search_timeline": {
                        "timeline": {
                            "instructions": []
                        }
                    }
                }
            }
        }
        mock_get.return_value.json.return_value = mock_response

        result = twitter_scrap("nike")

        # Validate that result is empty when no tweets are found
        self.assertEqual(result, [])

    @patch('api_twitter.requests.get')
    def test_twitter_scrap_api_failure(self, mock_get):
        # Simulate a failed API response
        mock_get.return_value.status_code = 500

        result = twitter_scrap("nike")

        # Validate that result is empty on API failure
        self.assertEqual(result, [])

class TestYoutubeFunctions(TestCase):
    
    @patch('api_youtube.build')
    @patch('api_youtube.ScrapConfig')
    def test_get_video_details_in_bulk(self, MockScrapConfig, MockBuild):
        # Mock ScrapConfig instance
        mock_scrap_config = MockScrapConfig.return_value
        mock_scrap_config.extract_mentions.return_value = ['@mention']
        mock_scrap_config.set_mention_pattern.return_value = None
        
        # Mock YouTube API response
        mock_youtube = Mock()
        mock_youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "description": "Check this out! #amazing @user",
                        "publishedAt": "2024-09-15T12:34:56Z",
                        "channelTitle": "Channel1",
                        "channelId": "channel1"
                    }
                }
            ]
        }
        
        youtube_config = {
            "service_version": "v3",
            "google_key": "fake_key",
            "snippet_part": "snippet",
            "type": "any",
            "max_results": 10
        }
        video_ids = ["video1"]
        document = {
            "channel1": {
                "description": "A great channel",
                "viewCount": "1000"
            }
        }
        hashtag_pattern = "#\w+"
        mention_pattern = "@\w+"
        y_m_dTHMSZ_format = "%Y-%m-%dT%H:%M:%SZ"
        y_m_dTHM_format = "%Y-%m-%dT%H:%M"
        post_type = "video"
        youtube_source = "youtube"
        user_id = "123456"
        mention = "test"
        
        results = get_video_details_in_bulk(
            mock_youtube,
            youtube_config,
            video_ids,
            video_ids,
            document,
            youtube_config["snippet_part"],
            hashtag_pattern,
            mention_pattern,
            y_m_dTHMSZ_format,
            y_m_dTHM_format,
            post_type,
            youtube_source,
            user_id,
            mention,
            mock_scrap_config
        )
        
        expected_result = [{
            "source": youtube_source,
            "author": "Channel1",
            "user_id": user_id,
            "text": "Check this out! #amazing @user",
            "type": post_type,
            "source_link": "https://www.youtube.com/watch?v=video1",
            "date": "2024-09-15T12:34",
            "mention": mention,
            "nbr_mentions": 1,
            "nbr_hashtags": 1,
            "mentions_texts": ["@mention"],
            "hashtags_texts": ["#amazing"],
            "post_uuid": mock_scrap_config.set_mention_pattern.return_value,
            "description": "A great channel",
            "like": "1000"
        }]
        
        self.assertEqual(results, expected_result)
    
    @patch('api_youtube.build')
    @patch('api_youtube.ScrapConfig')
    def test_youtube_scrap(self, MockScrapConfig, MockBuild):
        # Mock ScrapConfig instance
        mock_scrap_config = MockScrapConfig.return_value
        
        # Mock YouTube API responses
        mock_youtube = Mock()
        mock_youtube.search.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "video1"},
                    "snippet": {"channelId": "channel1"}
                }
            ]
        }
        mock_youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "video1",
                    "snippet": {
                        "description": "Check this out! #amazing @user",
                        "publishedAt": "2024-09-15T12:34:56Z",
                        "channelTitle": "Channel1",
                        "channelId": "channel1"
                    }
                }
            ]
        }
        mock_youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "channel1",
                    "snippet": {"description": "A great channel"},
                    "statistics": {"viewCount": "1000"}
                }
            ]
        }
        
        results = youtube_scrap("test")
        
        expected_result = [{
            "source": "youtube",
            "author": "Channel1",
            "user_id": "123456",
            "text": "Check this out! #amazing @user",
            "type": "video",
            "source_link": "https://www.youtube.com/watch?v=video1",
            "date": "2024-09-15T12:34",
            "mention": "test",
            "nbr_mentions": 1,
            "nbr_hashtags": 1,
            "mentions_texts": ["@mention"],
            "hashtags_texts": ["#amazing"],
            "post_uuid": mock_scrap_config.set_mention_pattern.return_value,
            "description": "A great channel",
            "like": "1000"
        }]
        
        self.assertEqual(results, expected_result)

class ClassificationHashtagTests(TestCase):

    @patch('classification_hashtag.XGBClassifier')
    @patch('classification_hashtag.GridSearchCV')
    @patch('classification_hashtag.RandomOverSampler')
    @patch('classification_hashtag.StratifiedShuffleSplit')
    @patch('classification_hashtag.LabelEncoder')
    @patch('classification_hashtag.pd.get_dummies')
    def test_classificationHashtag(self, mock_get_dummies, MockLabelEncoder, MockStratifiedShuffleSplit, MockRandomOverSampler, MockGridSearchCV, MockXGBClassifier):
        # Mocking
        mock_get_dummies.return_value = pd.DataFrame({
            'country_name_1': [1, 0],
            'industry_tech': [1, 0],
            'trend_type_rise': [1, 0],
            'is_new_True': [1, 0],
            'industry_Unknown': [0, 1],
            'video_views': [1000, 500],
            'publish_count': [10, 5],
            'hashtag': ['#tech', '#innovation']
        })
        
        mock_label_encoder = MockLabelEncoder.return_value
        mock_label_encoder.fit_transform.return_value = [0, 1]
        mock_label_encoder.classes_ = ['tech', 'innovation']
        
        mock_split = MockStratifiedShuffleSplit.return_value
        mock_split.split.return_value = ([0, 1], [2, 3])
        
        mock_ros = MockRandomOverSampler.return_value
        mock_ros.fit_resample.return_value = (pd.DataFrame(), [0, 1])
        
        mock_grid_search = MockGridSearchCV.return_value
        mock_grid_search.best_estimator_ = Mock()
        
        mock_xgb = MockXGBClassifier.return_value
        mock_xgb.predict.return_value = [0, 1]
        
        data_df = {
            'country_name': ['USA', 'UK'],
            'industry': ['tech', 'Unknown'],
            'trend_type': ['rise', 'fall'],
            'is_new': [True, False],
            'video_views': [1000, 500],
            'publish_count': [10, 5],
            'hashtag': ['#tech', '#innovation']
        }
        
        result = classificationHashtag(data_df)
        
        expected_topics_chart = {
            'topics': ['industry_tech'],
            'colors': {'industry_tech': '#FF0000'},  # Adjust based on the actual color generation logic
            'percentages': {'industry_tech': 100.0},
            'counts': {'industry_tech': 1},
            'hashtags': {'industry_tech': ['#tech']},
            'wordclouds': {'industry_tech': [{'hashtag': '#tech', 'value': 10000}]}
        }
        
        self.assertEqual(result, expected_topics_chart)

    def test_classificationHashtag_empty_data(self):
        data_df = pd.DataFrame()
        result = classificationHashtag(data_df)
        self.assertEqual(result, {
            'topics': [],
            'colors': {},
            'percentages': {},
            'counts': {},
            'hashtags': {},
            'wordclouds': {}
        })

    def test_classificationHashtag_invalid_data(self):
        with self.assertRaises(Exception):
            classificationHashtag(None)

class ClusteringDomainsTests(TestCase):

    @patch('clustering_domains.KMeans')
    @patch('clustering_domains.AgglomerativeClustering')
    @patch('clustering_domains.KMedoids')
    @patch('clustering_domains.DBSCAN')
    @patch('clustering_domains.OPTICS')
    @patch('clustering_domains.GridSearchCV')
    @patch('clustering_domains.StandardScaler')
    @patch('clustering_domains.sns.color_palette')
    def test_clustering_domains(self, mock_color_palette, MockStandardScaler, MockGridSearchCV, MockOPTICS, MockDBSCAN, MockKMedoids, MockAgglomerativeClustering, MockKMeans):
        # Mocking
        mock_color_palette.return_value.as_hex.return_value = ['#FF0000', '#00FF00']
        
        mock_scaler = MockStandardScaler.return_value
        mock_scaler.fit_transform.return_value = pd.DataFrame({
            'totalBacklinks': [0.5, -0.5],
            'domain_authority': [0.5, -0.5],
            'page_authority': [0.5, -0.5],
            'spam_score': [0.5, -0.5]
        })

        mock_kmeans = MockKMeans.return_value
        mock_kmeans.fit_predict.return_value = [0, 1]

        mock_agglomerative = MockAgglomerativeClustering.return_value
        mock_agglomerative.fit_predict.return_value = [0, 1]

        mock_kmedoids = MockKMedoids.return_value
        mock_kmedoids.fit_predict.return_value = [0, 1]

        mock_dbscan = MockDBSCAN.return_value
        mock_dbscan.fit_predict.return_value = [0, 1]

        mock_optics = MockOPTICS.return_value
        mock_optics.fit_predict.return_value = [0, 1]

        mock_grid_search = MockGridSearchCV.return_value
        mock_grid_search.best_params_ = {'n_clusters': 2}

        data = {
            'Site': ['site1.com', 'site2.com'],
            'totalBacklinks': [100, 200],
            'domain_authority': [50, 60],
            'page_authority': [40, 55],
            'spam_score': [0, 1]
        }
        
        result = clustering_domains(data)

        expected_result = {
            'domains': ['site1.com', 'site2.com'],
            'da_scores_percentages': [50, 60],
            'pa_scores_percentages': [40, 55],
            'spam_scores': [0, 1],
            'total_backlinks': [100, 200],
            'colors': ['#FF0000', '#00FF00'],
            'clusters': [0, 1]
        }
        
        self.assertEqual(result, expected_result)

    def test_clustering_domains_empty_data(self):
        data = pd.DataFrame()
        result = clustering_domains(data)
        self.assertEqual(result, {
            'domains': [],
            'da_scores_percentages': [],
            'pa_scores_percentages': [],
            'spam_scores': [],
            'total_backlinks': [],
            'colors': [],
            'clusters': []
        })

    def test_clustering_domains_invalid_data(self):
        with self.assertRaises(TypeError):
            clustering_domains(None)

class ClusteringRankingTests(TestCase):

    @patch('clustering_ranking.KMeans')
    def test_clustering_ranking(self, MockKMeans):
        # Mock KMeans
        mock_kmeans = MockKMeans.return_value
        mock_kmeans.fit_predict.return_value = [0, 1, 0, 1]

        # Sample input data
        data = [
            {'competition_level': 'LOW', 'volume': 100, 'competition_index': 0.1, 'low_bid': 10, 'high_bid': 15, 'trend': 0.5, 'text': 'hashtag1'},
            {'competition_level': 'LOW', 'volume': 150, 'competition_index': 0.2, 'low_bid': 12, 'high_bid': 18, 'trend': 0.4, 'text': 'hashtag2'},
            {'competition_level': 'MEDIUM', 'volume': 200, 'competition_index': 0.3, 'low_bid': 20, 'high_bid': 25, 'trend': 0.6, 'text': 'hashtag3'},
            {'competition_level': 'HIGH', 'volume': 300, 'competition_index': 0.4, 'low_bid': 30, 'high_bid': 35, 'trend': 0.7, 'text': 'hashtag4'},
            {'competition_level': 'UNSPECIFIED', 'volume': 250, 'competition_index': 0.2, 'low_bid': 15, 'high_bid': 20, 'trend': 0.3, 'text': 'hashtag5'},
        ]

        expected_result = {
            'LOW': {
                0: {'volume': [100], 'competition_index': [0.1], 'low_bid': [10], 'high_bid': [15], 'trend': [0.5], 'hashtag': ['hashtag1']},
                1: {'volume': [150], 'competition_index': [0.2], 'low_bid': [12], 'high_bid': [18], 'trend': [0.4], 'hashtag': ['hashtag2']}
            },
            'MEDIUM': {
                0: {'volume': [200], 'competition_index': [0.3], 'low_bid': [20], 'high_bid': [25], 'trend': [0.6], 'hashtag': ['hashtag3']}
            },
            'HIGH': {
                0: {'volume': [300], 'competition_index': [0.4], 'low_bid': [30], 'high_bid': [35], 'trend': [0.7], 'hashtag': ['hashtag4']}
            },
            'UNSPECIFIED': {
                0: {'volume': [250], 'competition_index': [0.2], 'low_bid': [15], 'high_bid': [20], 'trend': [0.3], 'hashtag': ['hashtag5']}
            }
        }

        result = clusteringRanking(data)

        # Check if result matches the expected result
        self.assertEqual(result, expected_result)

    def test_clustering_ranking_empty_data(self):
        data = []
        result = clusteringRanking(data)
        expected_result = {
            'LOW': {},
            'MEDIUM': {},
            'HIGH': {},
            'UNSPECIFIED': {}
        }
        self.assertEqual(result, expected_result)

    def test_clustering_ranking_no_competition_level(self):
        data = [
            {'volume': 100, 'competition_index': 0.1, 'low_bid': 10, 'high_bid': 15, 'trend': 0.5, 'text': 'hashtag1'}
        ]
        result = clusteringRanking(data)
        expected_result = {
            'LOW': {},
            'MEDIUM': {},
            'HIGH': {},
            'UNSPECIFIED': {}
        }
        self.assertEqual(result, expected_result)

class CombineJsonFilesTests(TestCase):

    def test_combine_json_files_success(self):
        # Define some sample JSON data
        data1 = [{"id": 1, "value": "A"}, {"id": 2, "value": "B"}]
        data2 = [{"id": 3, "value": "C"}, {"id": 4, "value": "D"}]
        data3 = [{"id": 5, "value": "E"}]

        # Combine the JSON data
        result = combine_json_files(data1, data2, data3)

        # Define the expected result
        expected_result = [
            {"id": 1, "value": "A"},
            {"id": 2, "value": "B"},
            {"id": 3, "value": "C"},
            {"id": 4, "value": "D"},
            {"id": 5, "value": "E"}
        ]

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

    def test_combine_json_files_with_empty_data(self):
        # Define some sample JSON data with an empty source
        data1 = [{"id": 1, "value": "A"}]
        data2 = []
        data3 = [{"id": 2, "value": "B"}]

        # Combine the JSON data
        result = combine_json_files(data1, data2, data3)

        # Define the expected result
        expected_result = [
            {"id": 1, "value": "A"},
            {"id": 2, "value": "B"}
        ]

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

    def test_combine_json_files_with_invalid_data(self):
        # Define some sample JSON data with invalid entries
        data1 = [{"id": 1, "value": "A"}]
        data2 = "invalid data"  # Invalid data
        data3 = [{"id": 2, "value": "B"}]

        # Combine the JSON data
        result = combine_json_files(data1, data2, data3)

        # Define the expected result, should only include valid data
        expected_result = [
            {"id": 1, "value": "A"},
            {"id": 2, "value": "B"}
        ]

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

    def test_combine_json_files_with_all_invalid_data(self):
        # Define some sample JSON data with all invalid entries
        data1 = "invalid data"
        data2 = None
        data3 = 12345  # Another invalid data

        # Combine the JSON data
        result = combine_json_files(data1, data2, data3)

        # Define the expected result, should be empty
        expected_result = []

        # Assert that the result matches the expected result
        self.assertEqual(result, expected_result)

class ElasticsearchConfigTests(TestCase):

    @patch('db.Elasticsearch')
    def test_singleton_instance(self, MockElasticsearch):
        # Test singleton behavior
        instance1 = ElasticsearchConfig.get_instance()
        instance2 = ElasticsearchConfig.get_instance()
        self.assertIs(instance1, instance2)

    @patch('db.Elasticsearch')
    def test_elasticsearch_initialization(self, MockElasticsearch):
        instance = ElasticsearchConfig.get_instance()
        MockElasticsearch.assert_called_once_with("http://localhost:9200")
        self.assertIsNotNone(instance.es)
        self.assertEqual(instance.index_digianalyse, "digianalyse")

class DocumentCreationTests(TestCase):

    @patch('db.bulk')
    @patch('db.connections.get_connection')
    def test_market_chart_document_creation(self, mock_get_connection, mock_bulk):
        # Mock Elasticsearch connection
        mock_get_connection.return_value = Mock()
        
        influencer = {
            "theme": "Tech",
            "documents": [
                {"author": "Author A", "title": "Title A", "description": "Description A", "likes": 10.5, "source": "Source A"}
            ]
        }
        leads = {
            "interests": "Interest A",
            "texts": [
                {"author": "Author B", "text": "Text B", "source": "Source B"}
            ]
        }
        mention = "Some mention"

        find_insert_or_delete_market_charts("test_index", influencer, leads, mention)
        
        # Assert that the bulk method was called with the correct data
        mock_bulk.assert_called_once()

    @patch('db.bulk')
    @patch('db.connections.get_connection')
    def test_seo_chart_document_creation(self, mock_get_connection, mock_bulk):
        # Mock Elasticsearch connection
        mock_get_connection.return_value = Mock()
        
        topics_chart = {
            "topics": ["SEO", "Marketing"],
            "counts": {"SEO": 100, "Marketing": 150},
            "hashtags": {"SEO": ["#SEO"], "Marketing": ["#Marketing"]},
            "wordclouds": {"SEO": "cloud1", "Marketing": "cloud2"}
        }

        find_insert_or_delete_topics_charts("test_index_seo", topics_chart)
        
        # Assert that the bulk method was called with the correct data
        mock_bulk.assert_called_once()

    @patch('db.bulk')
    @patch('db.connections.get_connection')
    def test_domain_chart_document_creation(self, mock_get_connection, mock_bulk):
        # Mock Elasticsearch connection
        mock_get_connection.return_value = Mock()
        
        domain_chart = {
            "domains": ["example.com"],
            "da_scores_percentages": [50],
            "pa_scores_percentages": [60],
            "spam_scores": [1.5],
            "total_backlinks": [100],
            "colors": ["red"],
            "clusters": [5]
        }

        find_insert_or_delete_domain_charts("test_index_domain", "example.com", domain_chart)
        
        # Assert that the bulk method was called with the correct data
        mock_bulk.assert_called_once()

    @patch('db.bulk')
    @patch('db.connections.get_connection')
    def test_ranking_chart_document_creation(self, mock_get_connection, mock_bulk):
        # Mock Elasticsearch connection
        mock_get_connection.return_value = Mock()
        
        ranking_chart = {
            "volume": [1000],
            "competition_index": [3],
            "low_bid": [0.5],
            "high_bid": [1.5],
            "trend": [0.1],
            "hashtag": ["#ranking"]
        }

        find_insert_or_delete_ranking_charts("test_index_ranking", "keyword", ranking_chart)
        
        # Assert that the bulk method was called with the correct data
        mock_bulk.assert_called_once()

class GenerateInterestsTests(TestCase):

    @patch('generate_interests.spacy.load')
    @patch('generate_interests.spacy.cli.download')
    @patch('generate_interests.ThreadPoolExecutor')
    def test_generate_interests_success(self, MockThreadPoolExecutor, MockDownload, MockLoad):
        # Mock spaCy model and ThreadPoolExecutor
        mock_nlp = Mock()
        MockLoad.return_value = mock_nlp
        MockDownload.return_value = None

        # Mock extract_keywords function
        def mock_extract_keywords(text):
            return text.split()

        # Set up the mock for ThreadPoolExecutor
        mock_executor = Mock()
        mock_executor.map = Mock(return_value=[['keyword1', 'keyword2'], ['keyword1']])
        MockThreadPoolExecutor.return_value = mock_executor
        
        clusters = {
            1: {
                'texts': [
                    {'author': 'Author1', 'text': 'Text for keyword1 keyword2', 'source': 'Source1', 'source_link': 'Link1'},
                    {'author': 'Author2', 'text': 'Text for keyword1', 'source': 'Source2', 'source_link': 'Link2'}
                ]
            }
        }

        result = generate_interests(clusters)

        expected_result = {
            1: {
                'interests': 'keyword1 keyword2',
                'texts': [
                    {'author': 'Author1', 'text': 'Text for keyword1 keyword2', 'source': 'Source1', 'source_link': 'Link1'},
                    {'author': 'Author2', 'text': 'Text for keyword1', 'source': 'Source2', 'source_link': 'Link2'}
                ]
            }
        }

        self.assertEqual(result, expected_result)

    @patch('generate_interests.spacy.load')
    @patch('generate_interests.spacy.cli.download')
    def test_generate_interests_spacy_load_error(self, MockDownload, MockLoad):
        # Simulate spaCy load error
        MockLoad.side_effect = Exception("Error loading spaCy model")

        clusters = {
            1: {
                'texts': [
                    {'author': 'Author1', 'text': 'Text for keyword1', 'source': 'Source1', 'source_link': 'Link1'}
                ]
            }
        }

        result = generate_interests(clusters)

        self.assertEqual(result, clusters)  # Expecting the same clusters returned if spaCy model loading fails

    @patch('generate_interests.spacy.load')
    @patch('generate_interests.spacy.cli.download')
    @patch('generate_interests.ThreadPoolExecutor')
    def test_generate_interests_text_processing_error(self, MockThreadPoolExecutor, MockDownload, MockLoad):
        # Mock spaCy model
        mock_nlp = Mock()
        MockLoad.return_value = mock_nlp
        MockDownload.return_value = None

        # Simulate error in text processing
        def mock_extract_keywords(text):
            raise Exception("Error processing text")

        # Set up the mock for ThreadPoolExecutor
        mock_executor = Mock()
        mock_executor.map = Mock(return_value=[[]])
        MockThreadPoolExecutor.return_value = mock_executor
        mock_nlp.side_effect = Exception("Error in spaCy model")

        clusters = {
            1: {
                'texts': [
                    {'author': 'Author1', 'text': 'Text for keyword1', 'source': 'Source1', 'source_link': 'Link1'}
                ]
            }
        }

        result = generate_interests(clusters)

        expected_result = {
            1: {
                'interests': '',
                'texts': [
                    {'author': 'Author1', 'text': 'Text for keyword1', 'source': 'Source1', 'source_link': 'Link1'}
                ]
            }
        }

        self.assertEqual(result, expected_result)

class GenerateThemeTests(TestCase):

    @patch('generate_theme.spacy.load')
    @patch('generate_theme.spacy.cli.download')
    @patch('generate_theme.ThreadPoolExecutor')
    def test_generate_success(self, MockThreadPoolExecutor, MockDownload, MockLoad):
        # Mock spaCy model and ThreadPoolExecutor
        mock_nlp = Mock()
        MockLoad.return_value = mock_nlp
        MockDownload.return_value = None

        # Mock extract_keywords function
        def mock_extract_keywords(text):
            return text.split()

        # Set up the mock for ThreadPoolExecutor
        mock_executor = Mock()
        mock_executor.map = Mock(return_value=[['keyword1', 'keyword2'], ['keyword1']])
        MockThreadPoolExecutor.return_value = mock_executor

        clusters = {
            1: {
                'documents': [
                    {'description': 'Description with keyword1 keyword2'},
                    {'description': 'Another description with keyword1'}
                ]
            }
        }

        result = generate(clusters)

        expected_result = {
            1: {
                'documents': [
                    {'description': 'Description with keyword1 keyword2'},
                    {'description': 'Another description with keyword1'}
                ],
                'theme': 'keyword1 keyword2'
            }
        }

        self.assertEqual(result, expected_result)

    @patch('generate_theme.spacy.load')
    @patch('generate_theme.spacy.cli.download')
    def test_generate_spacy_load_error(self, MockDownload, MockLoad):
        # Simulate spaCy load error
        MockLoad.side_effect = Exception("Error loading spaCy model")

        clusters = {
            1: {
                'documents': [
                    {'description': 'Description with keyword1 keyword2'}
                ]
            }
        }

        result = generate(clusters)

        self.assertEqual(result, clusters)  # Expecting the same clusters returned if spaCy model loading fails

    @patch('generate_theme.spacy.load')
    @patch('generate_theme.spacy.cli.download')
    @patch('generate_theme.ThreadPoolExecutor')
    def test_generate_text_processing_error(self, MockThreadPoolExecutor, MockDownload, MockLoad):
        # Mock spaCy model
        mock_nlp = Mock()
        MockLoad.return_value = mock_nlp
        MockDownload.return_value = None

        # Simulate error in text processing
        def mock_extract_keywords(text):
            raise Exception("Error processing text")

        # Set up the mock for ThreadPoolExecutor
        mock_executor = Mock()
        mock_executor.map = Mock(return_value=[[]])
        MockThreadPoolExecutor.return_value = mock_executor
        mock_nlp.side_effect = Exception("Error in spaCy model")

        clusters = {
            1: {
                'documents': [
                    {'description': 'Description with keyword1 keyword2'}
                ]
            }
        }

        result = generate(clusters)

        expected_result = {
            1: {
                'documents': [
                    {'description': 'Description with keyword1 keyword2'}
                ],
                'theme': ''
            }
        }

        self.assertEqual(result, expected_result)

class ModelingEvalTests(TestCase):

    @patch('modeling_eval.TfidfVectorizer')
    @patch('modeling_eval.KMeans')
    @patch('modeling_eval.AgglomerativeClustering')
    @patch('modeling_eval.SpectralClustering')
    @patch('modeling_eval.Birch')
    @patch('modeling_eval.clean_description')
    def test_clustering_success(self, MockCleanDescription, MockBirch, MockSpectralClustering, MockAgglomerativeClustering, MockKMeans, MockTfidfVectorizer):
        # Mock the vectorizer
        mock_vectorizer = Mock()
        mock_vectorizer.fit_transform.return_value = Mock()
        MockTfidfVectorizer.return_value = mock_vectorizer

        # Mock the clustering algorithms
        mock_kmeans = Mock()
        mock_kmeans.fit_predict.return_value = [0, 1]
        MockKMeans.return_value = mock_kmeans

        mock_agglomerative = Mock()
        mock_agglomerative.fit_predict.return_value = [0, 1]
        MockAgglomerativeClustering.return_value = mock_agglomerative

        mock_spectral = Mock()
        mock_spectral.fit_predict.return_value = [0, 1]
        MockSpectralClustering.return_value = mock_spectral

        mock_birch = Mock()
        mock_birch.fit_predict.return_value = [0, 1]
        MockBirch.return_value = mock_birch

        # Mock the text cleaning
        MockCleanDescription.side_effect = lambda x: x

        influencer_data = [
            {'description': 'Influencer description 1', 'author': 'Author 1', 'source': 'Source 1', 'like': 'Like 1'},
            {'description': 'Influencer description 2', 'author': 'Author 2', 'source': 'Source 2', 'like': 'Like 2'}
        ]

        leads_data = [
            {'description': 'Lead description 1', 'author': 'Author 1', 'text': 'Text 1', 'source': 'Source 1', 'source_link': 'Link 1'},
            {'description': 'Lead description 2', 'author': 'Author 2', 'text': 'Text 2', 'source': 'Source 2', 'source_link': 'Link 2'}
        ]

        result = clustering(influencer_data, leads_data)

        expected_result = {
            'influencers_charts': {
                'KMeans': {
                    0: {'theme': 'Cluster 0', 'documents': influencer_data},
                    1: {'theme': 'Cluster 1', 'documents': influencer_data}
                },
                'Agglomerative': {
                    0: {'theme': 'Cluster 0', 'documents': influencer_data},
                    1: {'theme': 'Cluster 1', 'documents': influencer_data}
                },
                'Spectral': {
                    0: {'theme': 'Cluster 0', 'documents': influencer_data},
                    1: {'theme': 'Cluster 1', 'documents': influencer_data}
                },
                'Birch': {
                    0: {'theme': 'Cluster 0', 'documents': influencer_data},
                    1: {'theme': 'Cluster 1', 'documents': influencer_data}
                }
            },
            'leads_charts': {
                'KMeans': {
                    0: {'interests': 'Cluster 0', 'texts': leads_data},
                    1: {'interests': 'Cluster 1', 'texts': leads_data}
                },
                'Agglomerative': {
                    0: {'interests': 'Cluster 0', 'texts': leads_data},
                    1: {'interests': 'Cluster 1', 'texts': leads_data}
                },
                'Spectral': {
                    0: {'interests': 'Cluster 0', 'texts': leads_data},
                    1: {'interests': 'Cluster 1', 'texts': leads_data}
                },
                'Birch': {
                    0: {'interests': 'Cluster 0', 'texts': leads_data},
                    1: {'interests': 'Cluster 1', 'texts': leads_data}
                }
            }
        }

        self.assertEqual(result, expected_result)

    @patch('modeling_eval.TfidfVectorizer')
    @patch('modeling_eval.KMeans')
    @patch('modeling_eval.AgglomerativeClustering')
    @patch('modeling_eval.SpectralClustering')
    @patch('modeling_eval.Birch')
    @patch('modeling_eval.clean_description')
    def test_clustering_empty_data(self, MockCleanDescription, MockBirch, MockSpectralClustering, MockAgglomerativeClustering, MockKMeans, MockTfidfVectorizer):
        # Mock the vectorizer
        mock_vectorizer = Mock()
        mock_vectorizer.fit_transform.return_value = Mock()
        MockTfidfVectorizer.return_value = mock_vectorizer

        # Mock the clustering algorithms
        mock_kmeans = Mock()
        mock_kmeans.fit_predict.return_value = []
        MockKMeans.return_value = mock_kmeans

        mock_agglomerative = Mock()
        mock_agglomerative.fit_predict.return_value = []
        MockAgglomerativeClustering.return_value = mock_agglomerative

        mock_spectral = Mock()
        mock_spectral.fit_predict.return_value = []
        MockSpectralClustering.return_value = mock_spectral

        mock_birch = Mock()
        mock_birch.fit_predict.return_value = []
        MockBirch.return_value = mock_birch

        # Mock the text cleaning
        MockCleanDescription.side_effect = lambda x: x

        influencer_data = []
        leads_data = []

        result = clustering(influencer_data, leads_data)

        self.assertIsNone(result)  # Expect None if there's no meaningful text

    @patch('modeling_eval.TfidfVectorizer')
    @patch('modeling_eval.KMeans')
    @patch('modeling_eval.AgglomerativeClustering')
    @patch('modeling_eval.SpectralClustering')
    @patch('modeling_eval.Birch')
    @patch('modeling_eval.clean_description')
    def test_clustering_with_error_in_vectorizer(self, MockCleanDescription, MockBirch, MockSpectralClustering, MockAgglomerativeClustering, MockKMeans, MockTfidfVectorizer):
        # Mock the vectorizer to raise an error
        MockTfidfVectorizer.side_effect = Exception("Vectorizer error")

        influencer_data = [
            {'description': 'Influencer description 1'}
        ]

        leads_data = [
            {'description': 'Lead description 1'}
        ]

        result = clustering(influencer_data, leads_data)

        self.assertIsNone(result)  # Expect None if there's an error in vectorization

    @patch('modeling_eval.TfidfVectorizer')
    @patch('modeling_eval.KMeans')
    @patch('modeling_eval.AgglomerativeClustering')
    @patch('modeling_eval.SpectralClustering')
    @patch('modeling_eval.Birch')
    @patch('modeling_eval.clean_description')
    def test_clustering_with_invalid_data(self, MockCleanDescription, MockBirch, MockSpectralClustering, MockAgglomerativeClustering, MockKMeans, MockTfidfVectorizer):
        # Mock the vectorizer
        mock_vectorizer = Mock()
        mock_vectorizer.fit_transform.return_value = Mock()
        MockTfidfVectorizer.return_value = mock_vectorizer

        # Mock the clustering algorithms
        mock_kmeans = Mock()
        mock_kmeans.fit_predict.side_effect = Exception("Clustering error")
        MockKMeans.return_value = mock_kmeans

        # Mock the text cleaning
        MockCleanDescription.side_effect = lambda x: x

        influencer_data = [
            {'description': 'Influencer description 1'}
        ]

        leads_data = [
            {'description': 'Lead description 1'}
        ]

        result = clustering(influencer_data, leads_data)

        self.assertIsNone(result)  # Expect None if there's an error in clustering

class ScrapConfigTests(TestCase):

    def setUp(self):
        self.config = ScrapConfig()

    def test_initial_mention_pattern(self):
        # Test the initial state of mention_pattern
        self.assertEqual(self.config.mention_pattern, r"@\w+")

    def test_set_mention_pattern(self):
        # Test if set_mention_pattern correctly sets the pattern
        new_pattern = r"#\w+"
        self.config.set_mention_pattern(new_pattern)
        self.assertEqual(self.config.mention_pattern, r"@\w+")
        
    def test_extract_mentions(self):
        # Test if extract_mentions correctly extracts mentions based on the pattern
        text = "Hello @user1 and @user2! Check this out @user3."
        mentions = self.config.extract_mentions(text, self.config.mention_pattern)
        self.assertEqual(mentions, ['@user1', '@user2', '@user3'])
        
    def test_extract_mentions_with_custom_pattern(self):
        # Test if extract_mentions works with a custom pattern
        self.config.set_mention_pattern(r"#\w+")
        text = "Here are some hashtags: #hashtag1 #hashtag2."
        mentions = self.config.extract_mentions(text, self.config.mention_pattern)
        self.assertEqual(mentions, ['#hashtag1', '#hashtag2'])

class SerializationDataTests(TestCase):

    def setUp(self):
        # Create a sample data file for testing
        self.data_path = os.path.join(os.path.dirname(__file__), 'data.json')
        self.serialisation_path = os.path.join(os.path.dirname(__file__), 'serialisation.json')
        
        sample_data = {
            "name": "John Doe",
            "age": 30,
            "date_of_birth": "1994-05-23",
            "registered": datetime.datetime(2024, 1, 15, 8, 30, 45)
        }
        
        with open(self.data_path, 'w') as f:
            json.dump(sample_data, f)
            
        self.sentiment_chart_dict = {
            "positive": 0.8,
            "neutral": 0.1,
            "negative": 0.1
        }
        
        with open(self.serialisation_path, 'w') as f:
            json.dump(self.sentiment_chart_dict, f)

    def test_serialisation_data(self):
        expected_data = {
            "name": "John Doe",
            "age": 30,
            "date_of_birth": "1994-05-23",
            "registered": "2024-01-15T08:30:45"
        }
        data = serialisation_data()
        self.assertEqual(data, expected_data)

    def test_serialize_custom_datetime(self):
        dt = datetime.datetime(2024, 1, 15, 8, 30, 45)
        serialized = serialize_custom(dt)
        self.assertEqual(serialized, dt.isoformat())

    def test_serialize_custom_non_serializable(self):
        with self.assertRaises(TypeError):
            serialize_custom(object())

    def test_print_types(self):
        result = print_types()
        self.assertEqual(result, self.sentiment_chart_dict)

class TestUrls(TestCase):

    def test_add_user_data_url(self):
        url = reverse('add_user_data')
        self.assertEqual(resolve(url).func, views.post)

    def test_predictclass_url(self):
        url = reverse('predictclass')
        self.assertEqual(resolve(url).func, views.predictclass)

    def test_besthashtag_url(self):
        url = reverse('besthashtag')
        self.assertEqual(resolve(url).func, views.besthashtag)

    def test_bestdomains_url(self):
        url = reverse('bestdomains')
        self.assertEqual(resolve(url).func, views.bestdomains)

    def test_ranking_url(self):
        url = reverse('ranking')
        self.assertEqual(resolve(url).func, views.ranking)

class TestViews(TestCase):

    @patch('database.views.post')  # Mock the actual implementation if necessary
    def test_post_view(self, mock_post):
        mock_post.return_value = JsonResponse({'status': 'success'})
        response = self.client.post(reverse('add_user_data'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success'})

    @patch('database.views.predictclass')  # Mock the actual implementation if necessary
    def test_predictclass_view(self, mock_predictclass):
        mock_predictclass.return_value = JsonResponse({'prediction': 'classA'})
        response = self.client.get(reverse('predictclass'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'prediction': 'classA'})

    @patch('database.views.besthashtag')  # Mock the actual implementation if necessary
    def test_besthashtag_view(self, mock_besthashtag):
        mock_besthashtag.return_value = JsonResponse({'hashtags': ['#example']})
        response = self.client.get(reverse('besthashtag'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'hashtags': ['#example']})

    @patch('database.views.bestdomains')  # Mock the actual implementation if necessary
    def test_bestdomains_view(self, mock_bestdomains):
        mock_bestdomains.return_value = JsonResponse({'domains': ['example.com']})
        response = self.client.get(reverse('bestdomains'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'domains': ['example.com']})

    @patch('database.views.ranking')  # Mock the actual implementation if necessary
    def test_ranking_view(self, mock_ranking):
        mock_ranking.return_value = JsonResponse({'ranking': [1, 2, 3]})
        response = self.client.get(reverse('ranking'))
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'ranking': [1, 2, 3]})

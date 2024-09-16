from django.test import TestCase
from unittest.mock import patch
from django.urls import reverse, resolve
from database import views
from django.http import JsonResponse


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

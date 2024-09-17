from django.test import TestCase
from django.urls import reverse, resolve
from database import views


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

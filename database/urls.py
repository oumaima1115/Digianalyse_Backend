from django.urls import path
from . import views

urlpatterns = [
    path('add_user_data/', views.post, name='add_user_data'),
    path('get_user_data/', views.get_user_data, name='get_user_data'),  
    path('youtube_scrap/', views.youtube_scrap, name='youtube_scrap'),
    path('twitter_scrap/', views.twitter_scrap, name='twitter_scrap'),
    path('reddit_scrap/', views.reddit_scrap, name='reddit_scrap'),
    path('tiktok_scrap/', views.tiktok_scrap, name='tiktok_scrap'),
    path('instagram_scrap/', views.instagram_scrap, name='instagram_scrap'),
    path('linkedin_scrap/', views.linkedin_scrap, name='linkedin_scrap'),
    path('pinterest_scrap/', views.pinterest_scrap, name='pinterest_scrap')
]

from django.urls import path
from . import views

urlpatterns = [
    path('add_user_data/', views.post, name='add_user_data'),
    path('user/predictclass/', views.predictclass, name='predictclass'),
    path('seo/besthashtag/', views.besthashtag, name='besthashtag'),
    path('seo/bestdomains/', views.bestdomains, name='bestdomains'),
]

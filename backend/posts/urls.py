from django.urls import path
from posts import views
from .views import api_trending_cuisines

urlpatterns = [
    path("api/trending-cuisines", api_trending_cuisines),
    path("api/trends/", views.api_trends),
    path("api/search/", views.api_search),
    path("api/posts/", views.api_posts),
]
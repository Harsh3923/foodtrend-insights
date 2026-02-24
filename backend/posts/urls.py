from django.urls import path
from posts import views

urlpatterns = [
    path("api/trends/", views.api_trends),
    path("api/search/", views.api_search),
    path("api/posts/", views.api_posts),
]
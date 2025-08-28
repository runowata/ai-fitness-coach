from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path("health/", views.health, name="content_health"),
    path("media/<path:key>", views.media_proxy, name="media_proxy"),
    path("stories/", views.health, name="stories"),  # Temporary stub
]
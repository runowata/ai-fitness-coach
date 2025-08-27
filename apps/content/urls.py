from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path("health/", views.health, name="content_health"),
]
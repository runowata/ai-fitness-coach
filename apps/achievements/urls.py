from django.urls import path
from django.views.decorators.cache import cache_page
from . import views

urlpatterns = [
    path("", cache_page(60 * 5)(views.achievements_list), name="achievements_list"),
]
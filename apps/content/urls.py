from django.urls import path
from django.views.decorators.cache import cache_page
from . import views

app_name = 'content'

urlpatterns = [
    path('stories/', cache_page(60 * 5)(views.stories_list), name='stories'),
    path('stories/<slug:story_slug>/', views.story_detail, name='story_detail'),
    path('stories/<slug:story_slug>/chapter/<int:chapter_number>/', views.read_chapter, name='read_chapter'),
    path('unlock-preview/<int:chapter_id>/', views.unlock_preview, name='unlock_preview'),
]
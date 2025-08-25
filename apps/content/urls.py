from django.urls import path

from . import views

app_name = 'content'

urlpatterns = [
    path('stories/', views.stories_list, name='stories'),
    path('stories/<slug:story_slug>/', views.story_detail, name='story_detail'),
    path('stories/<slug:story_slug>/chapter/<int:chapter_number>/', views.read_chapter, name='read_chapter'),
    path('unlock-preview/<int:chapter_id>/', views.unlock_preview, name='unlock_preview'),
    path('api/next-chapter/', views.get_next_chapter, name='api_next_chapter'),
]
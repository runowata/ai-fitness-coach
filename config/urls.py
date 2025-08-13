"""URL Configuration for AI Fitness Coach"""
import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

# API Views
from apps.users.views import ArchetypeView, UserProfileView
from apps.workouts.views import (
    ExplainerVideoView,
    WeeklyCurrentView,
    WeeklyLessonHealthView,
    WeeklyLessonView,
    WeeklyUnreadView,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('workouts/', include('apps.workouts.urls')),
    path('onboarding/', include('apps.onboarding.urls')),
    path('content/', include('apps.content.urls')),
    path('achievements/', include('apps.achievements.urls')),
    path('', include('apps.notifications.urls')),
    path('', include('apps.analytics.urls')),
    
    # API endpoints
    path('api/profile/', UserProfileView.as_view(), name='api_profile'),
    path('api/archetype/', ArchetypeView.as_view(), name='api_archetype'),
    path('api/exercise/<str:exercise_id>/video/', ExplainerVideoView.as_view(), name='api_exercise_video'),
    path('api/weekly/current/', WeeklyCurrentView.as_view(), name='api_weekly_current'),
    path('api/weekly/unread/', WeeklyUnreadView.as_view(), name='api_weekly_unread'),
    path('api/weekly/<int:week>/', WeeklyLessonView.as_view(), name='api_weekly_lesson'),
    path('api/weekly/health/', WeeklyLessonHealthView.as_view(), name='api_weekly_health'),
    
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# Media files: в проде (R2/S3 storage) медиа не раздаём через Django
if settings.DEBUG and getattr(settings, 'MEDIA_ROOT', None):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
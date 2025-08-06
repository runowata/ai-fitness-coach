"""URL Configuration for AI Fitness Coach"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

# API Views
from apps.users.views import ArchetypeView
from apps.workouts.views import ExplainerVideoView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('workouts/', include('apps.workouts.urls')),
    path('onboarding/', include('apps.onboarding.urls')),
    path('content/', include('apps.content.urls')),
    path('achievements/', include('apps.achievements.urls')),
    
    # API endpoints
    path('api/archetype/', ArchetypeView.as_view(), name='api_archetype'),
    path('api/exercise/<str:exercise_id>/video/', ExplainerVideoView.as_view(), name='api_exercise_video'),
    
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# Media files serving
# Serve media files in DEBUG mode or when RENDER variable is set (production deployment on Render)
if settings.DEBUG or os.getenv('RENDER'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
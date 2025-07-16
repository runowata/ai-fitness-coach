"""URL Configuration for AI Fitness Coach"""
import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('users/', include('apps.users.urls')),
    path('workouts/', include('apps.workouts.urls')),
    path('onboarding/', include('apps.onboarding.urls')),
    path('content/', include('apps.content.urls')),
    path('achievements/', include('apps.achievements.urls')),
    
    # Auth URLs
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Password reset
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]

# Serve media files in development and on Render
if settings.DEBUG or os.getenv('RENDER'):
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development only (WhiteNoise handles them in production)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Debug endpoints only in development
    from apps.users.views import debug_auth
    urlpatterns += [
        path('debug-auth/', debug_auth, name='debug_auth_global'),
    ]
    
    import debug_toolbar
    urlpatterns += [
        path('__debug__/', include(debug_toolbar.urls)),
    ]
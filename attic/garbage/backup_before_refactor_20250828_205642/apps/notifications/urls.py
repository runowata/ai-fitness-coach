from django.urls import path

from .views import FCMWebhookView, OneSignalWebhookView, PushSubscriptionView, push_stats_view

app_name = 'notifications'

urlpatterns = [
    # API endpoints
    path('api/push/subscribe/', PushSubscriptionView.as_view(), name='push_subscribe'),
    path('api/push/unsubscribe/', PushSubscriptionView.as_view(), name='push_unsubscribe'),
    path('api/push/stats/', push_stats_view, name='push_stats'),
    
    # Webhook endpoints
    path('webhooks/onesignal/', OneSignalWebhookView.as_view(), name='onesignal_webhook'),
    path('webhooks/fcm/', FCMWebhookView.as_view(), name='fcm_webhook'),
]
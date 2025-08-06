from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class PushSubscription(models.Model):
    """Store push notification subscription details for users"""
    
    PROVIDER_CHOICES = [
        ('onesignal', 'OneSignal'),
        ('fcm', 'Firebase Cloud Messaging'),
    ]
    
    PLATFORM_CHOICES = [
        ('web', 'Web Browser'),
        ('ios', 'iOS App'),
        ('android', 'Android App'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default='onesignal')
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES, default='web')
    
    # Subscription identifiers
    subscription_id = models.CharField(max_length=200, unique=True)  # OneSignal Player ID or FCM token
    endpoint = models.URLField(blank=True)  # Web Push endpoint
    
    # Subscription metadata
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'push_subscriptions'
        unique_together = [('user', 'subscription_id')]
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['subscription_id']),
            models.Index(fields=['provider', 'platform']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.provider} ({self.platform})"


class PushNotificationLog(models.Model):
    """Log all push notification attempts"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent Successfully'), 
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
        ('clicked', 'Clicked'),
    ]
    
    subscription = models.ForeignKey(PushSubscription, on_delete=models.CASCADE, related_name='notification_logs')
    
    # Notification content
    title = models.CharField(max_length=100)
    body = models.TextField()
    data = models.JSONField(default=dict)  # Custom data payload
    
    # Delivery tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    provider_message_id = models.CharField(max_length=200, blank=True)  # OneSignal notification ID
    error_message = models.TextField(blank=True)
    
    # Timestamps
    sent_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'push_notification_logs'
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['subscription', 'status']),
            models.Index(fields=['sent_at']),
            models.Index(fields=['provider_message_id']),
        ]
    
    def __str__(self):
        return f"{self.subscription.user.username}: {self.title} [{self.status}]"
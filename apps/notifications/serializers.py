from rest_framework import serializers
from .models import PushSubscription, PushNotificationLog


class PushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for push notification subscriptions"""
    
    class Meta:
        model = PushSubscription
        fields = [
            'provider', 'platform', 'subscription_id', 'endpoint',
            'user_agent', 'is_active', 'created_at'
        ]
        read_only_fields = ['created_at']
        
    def validate_subscription_id(self, value):
        """Validate subscription_id is unique for this user"""
        user = self.context['request'].user
        existing = PushSubscription.objects.filter(
            user=user,
            subscription_id=value
        ).exclude(id=self.instance.id if self.instance else None)
        
        if existing.exists():
            # If subscription already exists, just update it
            existing.update(is_active=True)
            raise serializers.ValidationError("Subscription already exists and has been reactivated")
            
        return value
    
    def create(self, validated_data):
        # Get client IP and user agent from request
        request = self.context.get('request')
        if request:
            validated_data['ip_address'] = self._get_client_ip(request)
            validated_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')
        
        return super().create(validated_data)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class PushNotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for push notification logs"""
    
    subscription_user = serializers.CharField(source='subscription.user.username', read_only=True)
    subscription_provider = serializers.CharField(source='subscription.provider', read_only=True)
    
    class Meta:
        model = PushNotificationLog
        fields = [
            'id', 'title', 'body', 'data', 'status', 
            'provider_message_id', 'error_message',
            'sent_at', 'delivered_at', 'clicked_at',
            'subscription_user', 'subscription_provider'
        ]
        read_only_fields = ['id', 'sent_at', 'delivered_at', 'clicked_at']
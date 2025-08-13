from django.contrib import admin
from django.utils.html import format_html

from .models import PushNotificationLog, PushSubscription


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'provider', 'platform', 'subscription_id_short', 
        'is_active', 'created_at', 'last_used_at'
    ]
    list_filter = ['provider', 'platform', 'is_active', 'created_at']
    search_fields = ['user__username', 'user__email', 'subscription_id']
    readonly_fields = ['created_at', 'updated_at', 'last_used_at']
    
    def subscription_id_short(self, obj):
        """Show shortened subscription ID for readability"""
        if len(obj.subscription_id) > 20:
            return f"{obj.subscription_id[:20]}..."
        return obj.subscription_id
    subscription_id_short.short_description = 'Subscription ID'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['deactivate_subscriptions', 'reactivate_subscriptions']
    
    def deactivate_subscriptions(self, request, queryset):
        """Deactivate selected subscriptions"""
        count = queryset.update(is_active=False)
        self.message_user(request, f"Deactivated {count} subscriptions.")
    deactivate_subscriptions.short_description = "Deactivate selected subscriptions"
    
    def reactivate_subscriptions(self, request, queryset):
        """Reactivate selected subscriptions"""
        count = queryset.update(is_active=True)
        self.message_user(request, f"Reactivated {count} subscriptions.")
    reactivate_subscriptions.short_description = "Reactivate selected subscriptions"


@admin.register(PushNotificationLog)
class PushNotificationLogAdmin(admin.ModelAdmin):
    list_display = [
        'subscription_user', 'subscription_provider', 'title', 
        'status', 'sent_at', 'delivered_at', 'clicked_at'
    ]
    list_filter = [
        'status', 'subscription__provider', 'subscription__platform', 
        'sent_at', 'delivered_at'
    ]
    search_fields = [
        'subscription__user__username', 'subscription__user__email',
        'title', 'body', 'provider_message_id'
    ]
    readonly_fields = [
        'subscription', 'title', 'body', 'data', 'provider_message_id',
        'sent_at', 'delivered_at', 'clicked_at', 'error_message'
    ]
    
    def subscription_user(self, obj):
        """Show subscription user"""
        return obj.subscription.user.username
    subscription_user.short_description = 'User'
    
    def subscription_provider(self, obj):
        """Show subscription provider"""
        return obj.subscription.provider
    subscription_provider.short_description = 'Provider'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('subscription__user')
    
    # Custom view permissions
    def has_add_permission(self, request):
        """Don't allow manual creation of notification logs"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Allow viewing but not editing"""
        return request.user.is_superuser
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete logs"""
        return request.user.is_superuser


# Custom admin site sections
admin.site.site_header = "AI Fitness Coach Admin"
admin.site.site_title = "AI Fitness Coach Admin"
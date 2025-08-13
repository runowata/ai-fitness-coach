from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html

from .models import AnalyticsEvent, AnalyticsMetrics, UserSession


@admin.register(AnalyticsEvent)
class AnalyticsEventAdmin(admin.ModelAdmin):
    list_display = [
        'event_name', 'user_display', 'event_type', 'platform', 
        'event_time', 'amplitude_status'
    ]
    list_filter = [
        'event_type', 'platform', 'amplitude_sent', 'event_time', 
        'language', 'country'
    ]
    search_fields = [
        'event_name', 'event_type', 'user__username', 'user__email',
        'user_id_external', 'properties', 'device_id', 'session_id'
    ]
    readonly_fields = [
        'event_id', 'event_time', 'amplitude_sent_at', 
        'insert_id', 'ip_address', 'user_agent'
    ]
    
    date_hierarchy = 'event_time'
    ordering = ['-event_time']
    
    def user_display(self, obj):
        """Display user information"""
        if obj.user:
            return f"{obj.user.username} ({obj.user.id})"
        elif obj.user_id_external:
            return f"External: {obj.user_id_external}"
        else:
            return "Anonymous"
    user_display.short_description = 'User'
    
    def amplitude_status(self, obj):
        """Display Amplitude sync status"""
        if obj.amplitude_sent:
            return format_html('<span style="color: green;">✓ Sent</span>')
        elif obj.amplitude_error:
            return format_html('<span style="color: red;">✗ Error</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    amplitude_status.short_description = 'Amplitude'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_id', 'event_type', 'event_name', 'event_time')
        }),
        ('User Context', {
            'fields': ('user', 'user_id_external', 'session_id', 'device_id')
        }),
        ('Event Data', {
            'fields': ('properties', 'user_properties'),
            'classes': ('collapse',)
        }),
        ('Platform Information', {
            'fields': ('platform', 'os_name', 'os_version', 'device_type', 'language'),
            'classes': ('collapse',)
        }),
        ('Location & Network', {
            'fields': ('country', 'region', 'city', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Amplitude Integration', {
            'fields': ('amplitude_sent', 'amplitude_sent_at', 'amplitude_error', 'insert_id'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['resend_to_amplitude', 'mark_amplitude_sent']
    
    def resend_to_amplitude(self, request, queryset):
        """Resend selected events to Amplitude"""
        from .tasks import send_event_to_amplitude_task
        
        count = 0
        for event in queryset:
            # Reset amplitude status
            event.amplitude_sent = False
            event.amplitude_error = ''
            event.save()
            
            # Queue for resending
            send_event_to_amplitude_task.delay(event.id)
            count += 1
        
        self.message_user(request, f"Queued {count} events for resending to Amplitude.")
    resend_to_amplitude.short_description = "Resend to Amplitude"
    
    def mark_amplitude_sent(self, request, queryset):
        """Mark selected events as sent to Amplitude"""
        count = queryset.update(amplitude_sent=True, amplitude_error='')
        self.message_user(request, f"Marked {count} events as sent to Amplitude.")
    mark_amplitude_sent.short_description = "Mark as sent to Amplitude"


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = [
        'session_id_short', 'user_display', 'platform',
        'started_at', 'duration_display', 'events_count'
    ]
    list_filter = ['platform', 'started_at']
    search_fields = ['session_id', 'user__username', 'user__email', 'ip_address']
    readonly_fields = ['session_id', 'started_at', 'ended_at', 'duration_seconds']
    
    date_hierarchy = 'started_at'
    ordering = ['-started_at']
    
    def session_id_short(self, obj):
        """Display shortened session ID"""
        return f"{obj.session_id[:8]}..."
    session_id_short.short_description = 'Session ID'
    
    def user_display(self, obj):
        """Display user information"""
        if obj.user:
            return f"{obj.user.username}"
        else:
            return "Anonymous"
    user_display.short_description = 'User'
    
    def duration_display(self, obj):
        """Display session duration in human readable format"""
        if obj.duration_seconds:
            minutes = obj.duration_seconds // 60
            seconds = obj.duration_seconds % 60
            return f"{minutes}m {seconds}s"
        else:
            return "Active" if not obj.ended_at else "Unknown"
    duration_display.short_description = 'Duration'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
    
    actions = ['end_sessions']
    
    def end_sessions(self, request, queryset):
        """End selected active sessions"""
        count = 0
        for session in queryset.filter(ended_at__isnull=True):
            session.end_session()
            count += 1
        
        self.message_user(request, f"Ended {count} active sessions.")
    end_sessions.short_description = "End active sessions"


@admin.register(AnalyticsMetrics)
class AnalyticsMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'metric_type', 'metric_date', 'metric_value_display', 
        'dimension_display', 'calculated_at'
    ]
    list_filter = ['metric_type', 'metric_date', 'calculated_at']
    search_fields = ['metric_type', 'dimension_filters']
    readonly_fields = ['calculated_at']
    
    date_hierarchy = 'metric_date'
    ordering = ['-metric_date', 'metric_type']
    
    def metric_value_display(self, obj):
        """Display metric value with appropriate formatting"""
        if obj.metric_type in ['daily_active_users', 'weekly_active_users', 'monthly_active_users']:
            return f"{int(obj.metric_value)}"
        elif 'rate' in obj.metric_type:
            return f"{obj.metric_value:.1f}%"
        elif 'duration' in obj.metric_type:
            return f"{obj.metric_value:.1f} min"
        else:
            return f"{obj.metric_value:.2f}"
    metric_value_display.short_description = 'Value'
    
    def dimension_display(self, obj):
        """Display dimension filters"""
        if obj.dimension_filters:
            return ", ".join([f"{k}={v}" for k, v in obj.dimension_filters.items()])
        return "All users"
    dimension_display.short_description = 'Dimensions'
    
    actions = ['recalculate_metrics']
    
    def recalculate_metrics(self, request, queryset):
        """Recalculate selected metrics"""
        from .tasks import calculate_daily_metrics_task
        
        dates = set(queryset.values_list('metric_date', flat=True))
        count = 0
        
        for date in dates:
            calculate_daily_metrics_task.delay(date.isoformat())
            count += 1
        
        self.message_user(request, f"Queued recalculation for {count} dates.")
    recalculate_metrics.short_description = "Recalculate metrics"


# Customize admin site
admin.site.site_title = "AI Fitness Coach Analytics"
admin.site.index_title = "Analytics Dashboard"
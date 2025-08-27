import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class AnalyticsEvent(models.Model):
    """
    Store analytics events for tracking user behavior.
    Compatible with Amplitude event structure for seamless integration.
    """
    
    EVENT_TYPES = [
        # User lifecycle events
        ('user_signup', 'User Signup'),
        ('user_login', 'User Login'),
        ('user_logout', 'User Logout'),
        ('onboarding_started', 'Onboarding Started'),
        ('onboarding_completed', 'Onboarding Completed'),
        
        # Workout events
        ('workout_started', 'Workout Started'),
        ('workout_completed', 'Workout Completed'),
        ('workout_skipped', 'Workout Skipped'),
        ('exercise_substituted', 'Exercise Substituted'),
        ('workout_feedback', 'Workout Feedback'),
        
        # Content consumption
        ('weekly_lesson_viewed', 'Weekly Lesson Viewed'),
        ('weekly_lesson_completed', 'Weekly Lesson Completed'),
        # story events removed - functionality deprecated
        ('video_played', 'Video Played'),
        ('video_completed', 'Video Completed'),
        
        # Gamification events
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('level_up', 'Level Up'),
        ('streak_milestone', 'Streak Milestone'),
        ('xp_earned', 'XP Earned'),
        
        # App interaction events
        ('screen_view', 'Screen View'),
        ('button_click', 'Button Click'),
        ('feature_used', 'Feature Used'),
        ('coach_archetype_selected', 'Coach Archetype Selected'),
        ('settings_changed', 'Settings Changed'),
        
        # Push notification events
        ('push_notification_sent', 'Push Notification Sent'),
        ('push_notification_opened', 'Push Notification Opened'),
        ('push_notification_dismissed', 'Push Notification Dismissed'),
        
        # Custom events
        ('custom_event', 'Custom Event'),
    ]
    
    # Event identification
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    event_name = models.CharField(max_length=100)  # Human-readable event name
    
    # User context
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    user_id_external = models.CharField(max_length=100, blank=True)  # For anonymous tracking
    session_id = models.CharField(max_length=100, blank=True)
    device_id = models.CharField(max_length=100, blank=True)
    
    # Event properties (JSON field for flexible event data)
    properties = models.JSONField(default=dict)
    
    # User properties at time of event
    user_properties = models.JSONField(default=dict)
    
    # Device/platform information
    platform = models.CharField(max_length=20, blank=True)  # web, ios, android
    os_name = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=50, blank=True)
    device_type = models.CharField(max_length=50, blank=True)
    
    # App context
    app_version = models.CharField(max_length=20, blank=True)
    language = models.CharField(max_length=10, default='ru')
    country = models.CharField(max_length=10, blank=True)
    region = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Network context
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamps
    event_time = models.DateTimeField(default=timezone.now)
    insert_id = models.CharField(max_length=100, blank=True)  # Deduplication
    
    # Amplitude integration
    amplitude_sent = models.BooleanField(default=False)
    amplitude_sent_at = models.DateTimeField(null=True, blank=True)
    amplitude_error = models.TextField(blank=True)
    
    class Meta:
        db_table = 'analytics_events'
        indexes = [
            models.Index(fields=['user', 'event_time']),
            models.Index(fields=['event_type', 'event_time']),
            models.Index(fields=['event_time']),
            models.Index(fields=['session_id']),
            models.Index(fields=['device_id']),
            models.Index(fields=['amplitude_sent']),
        ]
        ordering = ['-event_time']
    
    def __str__(self):
        user_str = self.user.username if self.user else self.user_id_external or 'anonymous'
        return f"{user_str}: {self.event_name} ({self.event_time.strftime('%Y-%m-%d %H:%M')})"
    
    def to_amplitude_format(self):
        """Convert to Amplitude event format"""
        amplitude_event = {
            'event_type': self.event_name,
            'time': int(self.event_time.timestamp() * 1000),  # Amplitude expects milliseconds
            'event_properties': self.properties,
            'user_properties': self.user_properties,
            'platform': self.platform,
            'os_name': self.os_name,
            'os_version': self.os_version,
            'device_type': self.device_type,
            'language': self.language,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'ip': str(self.ip_address) if self.ip_address else None,
        }
        
        # Add user ID
        if self.user:
            amplitude_event['user_id'] = str(self.user.id)
        elif self.user_id_external:
            amplitude_event['user_id'] = self.user_id_external
        
        # Add device ID if available
        if self.device_id:
            amplitude_event['device_id'] = self.device_id
        
        # Add session ID if available
        if self.session_id:
            amplitude_event['session_id'] = int(self.session_id) if self.session_id.isdigit() else -1
        
        # Add insert_id for deduplication
        if self.insert_id:
            amplitude_event['insert_id'] = self.insert_id
        else:
            amplitude_event['insert_id'] = str(self.event_id)
        
        # Remove None values
        return {k: v for k, v in amplitude_event.items() if v is not None}


class UserSession(models.Model):
    """
    Track user sessions for analytics
    """
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    
    # Session metadata
    started_at = models.DateTimeField(default=timezone.now)
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    
    # Device/platform info
    platform = models.CharField(max_length=20, blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Session statistics
    events_count = models.PositiveIntegerField(default=0)
    screens_viewed = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'user_sessions'
        indexes = [
            models.Index(fields=['user', 'started_at']),
            models.Index(fields=['session_id']),
            models.Index(fields=['started_at']),
        ]
        ordering = ['-started_at']
    
    def __str__(self):
        user_str = self.user.username if self.user else 'anonymous'
        return f"{user_str} session ({self.session_id[:8]}...)"
    
    def end_session(self):
        """End the session and calculate duration"""
        if not self.ended_at:
            self.ended_at = timezone.now()
            self.duration_seconds = (self.ended_at - self.started_at).total_seconds()
            self.save(update_fields=['ended_at', 'duration_seconds'])
    
    def update_stats(self):
        """Update session statistics"""
        self.events_count = AnalyticsEvent.objects.filter(session_id=self.session_id).count()
        self.screens_viewed = AnalyticsEvent.objects.filter(
            session_id=self.session_id,
            event_type='screen_view'
        ).count()
        self.save(update_fields=['events_count', 'screens_viewed'])


class AnalyticsMetrics(models.Model):
    """
    Store pre-calculated analytics metrics for faster dashboards
    """
    
    METRIC_TYPES = [
        ('daily_active_users', 'Daily Active Users'),
        ('weekly_active_users', 'Weekly Active Users'),
        ('monthly_active_users', 'Monthly Active Users'),
        ('workout_completion_rate', 'Workout Completion Rate'),
        ('retention_rate', 'Retention Rate'),
        ('feature_adoption_rate', 'Feature Adoption Rate'),
        ('average_session_duration', 'Average Session Duration'),
    ]
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    metric_date = models.DateField()
    metric_value = models.FloatField()
    
    # Optional dimension filters
    dimension_filters = models.JSONField(default=dict)  # e.g., {"archetype": "111", "platform": "web"}
    
    # Metadata
    calculated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'analytics_metrics'
        unique_together = [('metric_type', 'metric_date', 'dimension_filters')]
        indexes = [
            models.Index(fields=['metric_type', 'metric_date']),
            models.Index(fields=['metric_date']),
        ]
        ordering = ['-metric_date']
    
    def __str__(self):
        return f"{self.get_metric_type_display()} - {self.metric_date}: {self.metric_value}"
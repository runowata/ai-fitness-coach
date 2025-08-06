from rest_framework import serializers
from .models import AnalyticsEvent, UserSession


class AnalyticsEventSerializer(serializers.ModelSerializer):
    """Serializer for analytics events"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AnalyticsEvent
        fields = [
            'event_id', 'event_type', 'event_name', 'event_time',
            'user', 'user_username', 'user_id_external', 
            'properties', 'user_properties',
            'platform', 'session_id', 'device_id',
            'amplitude_sent'
        ]
        read_only_fields = ['event_id', 'event_time', 'user_username', 'amplitude_sent']


class TrackEventSerializer(serializers.Serializer):
    """Serializer for tracking new events"""
    
    EVENT_TYPE_CHOICES = [
        ('user_signup', 'User Signup'),
        ('user_login', 'User Login'), 
        ('onboarding_started', 'Onboarding Started'),
        ('onboarding_completed', 'Onboarding Completed'),
        ('workout_started', 'Workout Started'),
        ('workout_completed', 'Workout Completed'),
        ('workout_skipped', 'Workout Skipped'),
        ('exercise_substituted', 'Exercise Substituted'),
        ('workout_feedback', 'Workout Feedback'),
        ('weekly_lesson_viewed', 'Weekly Lesson Viewed'),
        ('weekly_lesson_completed', 'Weekly Lesson Completed'),
        ('story_chapter_read', 'Story Chapter Read'),
        ('video_played', 'Video Played'),
        ('video_completed', 'Video Completed'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('level_up', 'Level Up'),
        ('screen_view', 'Screen View'),
        ('button_click', 'Button Click'),
        ('feature_used', 'Feature Used'),
        ('coach_archetype_selected', 'Coach Archetype Selected'),
        ('settings_changed', 'Settings Changed'),
        ('push_notification_opened', 'Push Notification Opened'),
        ('custom_event', 'Custom Event'),
    ]
    
    event_type = serializers.ChoiceField(choices=EVENT_TYPE_CHOICES)
    event_name = serializers.CharField(max_length=100, required=False)
    properties = serializers.JSONField(required=False, default=dict)
    user_properties = serializers.JSONField(required=False, default=dict)
    device_id = serializers.CharField(max_length=100, required=False)
    
    def validate_event_type(self, value):
        """Validate event type is supported"""
        valid_types = [choice[0] for choice in self.EVENT_TYPE_CHOICES]
        if value not in valid_types:
            raise serializers.ValidationError(f"Event type '{value}' is not supported.")
        return value
    
    def validate_properties(self, value):
        """Validate properties is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Properties must be a dictionary.")
        return value
    
    def validate_user_properties(self, value):
        """Validate user_properties is a dictionary"""
        if not isinstance(value, dict):
            raise serializers.ValidationError("User properties must be a dictionary.")
        return value


class UserSessionSerializer(serializers.ModelSerializer):
    """Serializer for user sessions"""
    
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = UserSession
        fields = [
            'session_id', 'user', 'user_username',
            'started_at', 'ended_at', 'duration_seconds',
            'platform', 'events_count', 'screens_viewed'
        ]
        read_only_fields = [
            'session_id', 'user_username', 'started_at', 
            'ended_at', 'duration_seconds', 'events_count', 'screens_viewed'
        ]


class AmplitudeEventSerializer(serializers.Serializer):
    """Serializer for Amplitude-compatible event format"""
    
    event_type = serializers.CharField()
    user_id = serializers.CharField(required=False)
    device_id = serializers.CharField(required=False)
    time = serializers.IntegerField()  # Unix timestamp in milliseconds
    event_properties = serializers.JSONField(required=False, default=dict)
    user_properties = serializers.JSONField(required=False, default=dict)
    platform = serializers.CharField(required=False)
    os_name = serializers.CharField(required=False)
    os_version = serializers.CharField(required=False)
    device_type = serializers.CharField(required=False)
    language = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    region = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    ip = serializers.IPAddressField(required=False)
    session_id = serializers.IntegerField(required=False)
    insert_id = serializers.CharField(required=False)
    
    def validate_time(self, value):
        """Validate timestamp is reasonable"""
        import time
        current_time_ms = int(time.time() * 1000)
        one_year_ms = 365 * 24 * 60 * 60 * 1000
        
        if value > current_time_ms + one_year_ms:
            raise serializers.ValidationError("Timestamp is too far in the future.")
        if value < current_time_ms - one_year_ms:
            raise serializers.ValidationError("Timestamp is too far in the past.")
        
        return value
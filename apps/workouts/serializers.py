from rest_framework import serializers

from .models import WeeklyLesson, WeeklyNotification


class WeeklyNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyNotification
        fields = [
            'id', 'week', 'archetype', 'lesson_title', 'lesson_script',
            'created_at', 'read_at', 'is_read'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'is_read']


class WeeklyLessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyLesson
        fields = ['week', 'archetype', 'title', 'script', 'locale', 'duration_sec']
        read_only_fields = ['week', 'archetype', 'title', 'script', 'locale', 'duration_sec']
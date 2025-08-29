from rest_framework import serializers

from .models import WeeklyNotification


class WeeklyNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyNotification
        fields = [
            'id', 'week', 'archetype', 'lesson_title', 'lesson_script',
            'created_at', 'read_at', 'is_read'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'is_read']


# УДАЛЕНО: WeeklyLessonSerializer - WeeklyLesson заменен на R2Video с category='weekly'
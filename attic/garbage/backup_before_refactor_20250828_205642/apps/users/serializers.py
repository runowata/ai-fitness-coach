from rest_framework import serializers

from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile data"""
    
    archetype_display = serializers.CharField(source='get_archetype_display', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'archetype', 'archetype_display',
            'age', 'height', 'weight',
            'level', 'experience_points', 'current_streak', 
            'longest_streak', 'total_workouts_completed'
        ]
        read_only_fields = [
            'level', 'experience_points', 'current_streak',
            'longest_streak', 'total_workouts_completed'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data with profile"""
    
    profile = UserProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'timezone', 'measurement_system', 
            'completed_onboarding', 'created_at', 'profile'
        ]
        read_only_fields = [
            'id', 'created_at', 'completed_onboarding'
        ]


class ArchetypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("archetype",)
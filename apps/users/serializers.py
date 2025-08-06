from rest_framework import serializers
from .models import UserProfile


class ArchetypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ("archetype",)
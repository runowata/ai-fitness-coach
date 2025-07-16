from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'completed_onboarding', 'is_adult_confirmed', 'is_2fa_enabled', 'created_at')
    list_filter = ('completed_onboarding', 'is_adult_confirmed', 'is_2fa_enabled', 'is_staff', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('timezone', 'measurement_system', 'is_adult_confirmed', 'is_2fa_enabled')}),
        ('Profile Info', {'fields': ('archetype', 'age', 'height', 'weight', 'experience_points', 'level', 'current_streak')}),
        ('Onboarding', {'fields': ('completed_onboarding', 'onboarding_completed_at')}),
    )


# UserProfile admin removed - profile data now part of User model
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'is_adult_confirmed', 'is_2fa_enabled', 'created_at')
    list_filter = ('is_adult_confirmed', 'is_2fa_enabled', 'is_staf', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('timezone', 'measurement_system', 'is_adult_confirmed', 'is_2fa_enabled')}),
    )
    
    inlines = [UserProfileInline]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'archetype', 'level', 'experience_points', 'current_streak', 'total_workouts_completed')
    list_filter = ('archetype', 'level')
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('experience_points', 'level', 'total_workouts_completed')
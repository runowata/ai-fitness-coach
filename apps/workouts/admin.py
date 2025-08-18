from django.contrib import admin
from .models import Exercise, WorkoutPlan, DailyWorkout


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['exercise_slug']
    search_fields = ['exercise_slug']
    ordering = ['exercise_slug']


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'duration_weeks', 'created_at', 'is_active']
    list_filter = ['is_active', 'duration_weeks']
    search_fields = ['user__email']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


@admin.register(DailyWorkout)
class DailyWorkoutAdmin(admin.ModelAdmin):
    list_display = ['plan', 'day_number', 'completed', 'completed_at']
    list_filter = ['completed']
    search_fields = ['plan__user__email']
    ordering = ['plan', 'day_number']
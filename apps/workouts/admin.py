from django.contrib import admin
from django.utils.html import format_html

from .models import CSVExercise, DailyWorkout, R2Video, R2Image, WorkoutPlan


# ExerciseAdmin REMOVED in Phase 5.6 - Exercise model deleted


@admin.register(CSVExercise)
class CSVExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_ru', 'get_video_type')
    search_fields = ('id', 'name_ru', 'description')
    readonly_fields = ('id', 'get_video_type')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name_ru', 'description', 'get_video_type')
        }),
    )
    
    def get_video_type(self, obj):
        return obj.video_type
    get_video_type.short_description = 'Тип видео'


@admin.register(R2Video)
class R2VideoAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'archetype', 'is_featured', 'get_exercise_type')
    list_filter = ('category', 'archetype', 'is_featured')
    search_fields = ('code', 'name', 'description', 'display_title')
    readonly_fields = ('get_exercise_type', 'r2_url')
    
    fieldsets = (
        ('Video Information', {
            'fields': ('code', 'name', 'description', 'category', 'archetype')
        }),
        ('Landing Page Display', {
            'fields': ('display_title', 'display_description', 'is_featured', 'sort_order'),
            'classes': ('collapse',)
        }),
        ('R2 Storage', {
            'fields': ('get_exercise_type', 'r2_url'),
            'classes': ('collapse',)
        }),
    )
    
    def get_exercise_type(self, obj):
        return obj.exercise_type
    get_exercise_type.short_description = 'Тип упражнения'


@admin.register(R2Image)
class R2ImageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'category', 'archetype', 'is_hero_image', 'is_featured')
    list_filter = ('category', 'archetype', 'is_hero_image', 'is_featured')
    search_fields = ('code', 'name', 'description', 'alt_text')
    readonly_fields = ('r2_url',)
    
    fieldsets = (
        ('Image Information', {
            'fields': ('code', 'name', 'description', 'category', 'archetype')
        }),
        ('Landing Page Display', {
            'fields': ('alt_text', 'is_hero_image', 'is_featured', 'sort_order'),
            'classes': ('collapse',)
        }),
        ('R2 Storage', {
            'fields': ('r2_url',),
            'classes': ('collapse',)
        }),
    )
    


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'duration_weeks', 'created_at', 'is_active')
    list_filter = ('is_active', 'duration_weeks', 'created_at')
    search_fields = ('name', 'user__email')
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'get_current_week')
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('user', 'name', 'duration_weeks')
        }),
        ('Plan Data', {
            'fields': ('plan_data',),
            'classes': ('collapse',)
        }),
        ('Progress', {
            'fields': ('started_at', 'completed_at', 'get_current_week', 'is_active')
        }),
        ('Adaptation', {
            'fields': ('last_adaptation_date', 'adaptation_count')
        })
    )
    
    def get_current_week(self, obj):
        return obj.get_current_week()
    get_current_week.short_description = 'Current Week'


@admin.register(DailyWorkout)
class DailyWorkoutAdmin(admin.ModelAdmin):
    list_display = ('plan', 'day_number', 'week_number', 'name', 'is_rest_day', 'completed_at', 'feedback_rating')
    list_filter = ('is_rest_day', 'feedback_rating', 'week_number')
    search_fields = ('name', 'plan__user__email')
    readonly_fields = ('started_at', 'completed_at')
    
    fieldsets = (
        ('Workout Information', {
            'fields': ('plan', 'day_number', 'week_number', 'name', 'is_rest_day')
        }),
        ('Exercises', {
            'fields': ('exercises',),
            'classes': ('collapse',)
        }),
        ('Confidence Task', {
            'fields': ('confidence_task',)
        }),
        ('Completion', {
            'fields': ('started_at', 'completed_at', 'feedback_rating', 'feedback_note')
        }),
        ('Substitutions', {
            'fields': ('substitutions',),
            'classes': ('collapse',)
        })
    )
from django.contrib import admin
from django.utils.html import format_html
from .models import Exercise, VideoClip, WorkoutPlan, DailyWorkout


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'difficulty', 'muscle_groups', 'equipment')
    list_filter = ('difficulty',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('id',)  # Make ID readonly since it's manually set
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name', 'slug', 'description')
        }),
        ('Classification', {
            'fields': ('difficulty', 'muscle_groups', 'equipment')
        })
    )


@admin.register(VideoClip)
class VideoClipAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'type', 'archetype', 'model_name', 'duration_seconds', 'is_active')
    list_filter = ('type', 'archetype', 'model_name', 'is_active')
    search_fields = ('exercise__name', 'reminder_text')
    autocomplete_fields = ['exercise']
    
    fieldsets = (
        ('Video Information', {
            'fields': ('exercise', 'type', 'archetype', 'model_name')
        }),
        ('Content', {
            'fields': ('url', 'duration_seconds', 'reminder_text')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exercise')


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'duration_weeks', 'goal', 'created_at', 'is_active')
    list_filter = ('is_active', 'duration_weeks', 'created_at')
    search_fields = ('name', 'user__email', 'goal')
    readonly_fields = ('created_at', 'started_at', 'completed_at', 'get_current_week')
    
    fieldsets = (
        ('Plan Information', {
            'fields': ('user', 'name', 'duration_weeks', 'goal')
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
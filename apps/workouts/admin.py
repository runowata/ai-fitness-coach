from django.contrib import admin
from django.utils.html import format_html

from .models import CSVExercise, DailyWorkout, Exercise, VideoClip, WorkoutPlan
from .video_storage import get_storage


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'difficulty', 'is_active')
    list_filter = ('difficulty', 'is_active')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Classification', {
            'fields': ('difficulty',)
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )
    
    # Equipment display removed - field no longer exists


@admin.register(CSVExercise)
class CSVExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name_ru', 'name_en', 'level', 'muscle_group', 'exercise_type', 'is_active')
    list_filter = ('level', 'muscle_group', 'exercise_type', 'is_active')
    search_fields = ('id', 'name_ru', 'name_en', 'description')
    readonly_fields = ('id',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'name_ru', 'name_en', 'description')
        }),
        ('Classification', {
            'fields': ('level', 'muscle_group', 'exercise_type', 'ai_tags')
        }),
        ('Status', {
            'fields': ('is_active',)
        })
    )


@admin.register(VideoClip)
class VideoClipAdmin(admin.ModelAdmin):
    list_display = ('exercise', 'r2_kind', 'provider', 'storage_status', 'archetype', 'model_name', 'duration_seconds', 'is_active')
    list_filter = ('r2_kind', 'provider', 'archetype', 'model_name', 'is_active')
    search_fields = ('exercise__name_ru', 'exercise__name_en', 'reminder_text', 'stream_uid', 'playback_id')
    autocomplete_fields = ['exercise']
    readonly_fields = ('storage_status', 'playback_url_display')
    
    fieldsets = (
        ('Video Information', {
            'fields': ('exercise', 'r2_kind', 'archetype', 'model_name')
        }),
        ('Storage Provider', {
            'fields': ('provider', 'storage_status', 'playback_url_display'),
            'description': 'Video storage configuration and validation status'
        }),
        ('R2 Storage (Cloudflare R2)', {
            'fields': ('r2_file', 'r2_archetype'),
            'classes': ('collapse',),
            'description': 'Fields for R2-hosted videos'
        }),
        ('Stream Storage (Cloudflare Stream)', {
            'fields': ('stream_uid', 'playback_id'),
            'classes': ('collapse',),
            'description': 'Fields for Stream-hosted videos'
        }),
        ('Content', {
            'fields': ('duration_seconds', 'script_text', 'reminder_text')
        }),
        ('Status', {
            'fields': ('is_active', 'is_placeholder')
        })
    )
    
    def storage_status(self, obj):
        """Display storage status with color coding"""
        try:
            storage = get_storage(obj)
            exists = storage.exists(obj)
            
            if exists:
                return format_html('<span style="color: green; font-weight: bold;">✓ Available</span>')
            else:
                return format_html('<span style="color: red; font-weight: bold;">✗ Missing</span>')
        except Exception as e:
            return format_html('<span style="color: orange; font-weight: bold;">⚠ Error: {}</span>', str(e))
    storage_status.short_description = 'Storage Status'
    
    def playback_url_display(self, obj):
        """Display playback URL for testing"""
        try:
            storage = get_storage(obj)
            url = storage.playback_url(obj)
            
            if url:
                # Truncate very long URLs for display
                display_url = url if len(url) <= 80 else f"{url[:77]}..."
                return format_html('<a href="{}" target="_blank" title="{}">{}</a>', url, url, display_url)
            else:
                return format_html('<span style="color: gray;">No URL</span>')
        except Exception as e:
            return format_html('<span style="color: red;">Error: {}</span>', str(e))
    playback_url_display.short_description = 'Playback URL'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('exercise')


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
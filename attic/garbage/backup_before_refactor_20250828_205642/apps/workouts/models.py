from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone

from .constants import Archetype, VideoKind

User = get_user_model()


class VideoProvider(models.TextChoices):
    R2 = "r2", "Cloudflare R2"
    STREAM = "stream", "Cloudflare Stream"
    EXTERNAL = "external", "External URL"


# Exercise model COMPLETELY REMOVED in Phase 5.6
# Replaced by CSVExercise model for cleaner structure


class VideoClip(models.Model):
    # Use centralized constants
    R2_KIND_CHOICES = VideoKind.choices()
    ARCHETYPE_CHOICES = Archetype.choices()
    
    exercise = models.ForeignKey(
        'CSVExercise', 
        on_delete=models.CASCADE, 
        related_name='video_clips',
        null=True,
        blank=True
    )
    archetype = models.CharField(
        max_length=20, 
        choices=ARCHETYPE_CHOICES
    )
    model_name = models.CharField(max_length=50)  # mod1, mod2, mod3
    duration_seconds = models.PositiveIntegerField()
    
    # R2 Storage fields (required in v2)
    r2_file = models.FileField(
        upload_to='videos/',
        blank=True,
        null=True,
        help_text='Video file in R2 storage'
    )
    r2_key = models.CharField(
        max_length=500,
        blank=True,
        help_text='R2 storage key/path for direct access'
    )
    r2_kind = models.CharField(
        max_length=20,
        choices=R2_KIND_CHOICES,
        default=VideoKind.INSTRUCTION,
        help_text='Video type for R2 organization'
    )
    r2_archetype = models.CharField(
        max_length=20,
        choices=ARCHETYPE_CHOICES,
        blank=True,
        help_text='Archetype for R2 videos'
    )
    
    # Video provider abstraction
    provider = models.CharField(
        max_length=16,
        choices=VideoProvider.choices,
        default=VideoProvider.R2,
        help_text='Video storage provider'
    )
    
    # Stream provider fields (for future use)
    stream_uid = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        help_text='Cloudflare Stream UID'
    )
    playback_id = models.CharField(
        max_length=64, 
        blank=True, 
        null=True,
        help_text='Stream playback ID'
    )
    
    # Script/content
    script_text = models.TextField(blank=True, help_text='Video script or content')
    
    # For reminder clips
    reminder_text = models.CharField(max_length=200, blank=True)
    
    # Rich contextual fields for expanded video system
    mood_type = models.CharField(
        max_length=20,
        choices=[
            ('energetic', 'Энергичное'),
            ('philosophical', 'Философское'), 
            ('business', 'Деловое'),
            ('encouraging', 'Ободряющее'),
            ('calm', 'Спокойное')
        ],
        blank=True,
        help_text='Настроение/тон видео'
    )
    
    content_theme = models.CharField(
        max_length=30, 
        choices=[
            ('week_start', 'Начало недели'),
            ('overcoming', 'Преодоление'),
            ('gratitude', 'Благодарность'),
            ('motivation', 'Мотивация'),
            ('recovery', 'Восстановление'),
            ('achievement', 'Достижение'),
            ('consistency', 'Постоянство'),
            ('challenge', 'Вызов')
        ],
        blank=True,
        help_text='Тематика контента'
    )
    
    position_in_workout = models.CharField(
        max_length=15,
        choices=[
            ('intro', 'Вступление'),
            ('mid', 'Середина'),
            ('outro', 'Завершение')
        ],
        blank=True,
        help_text='Позиция в тренировке'
    )
    
    week_context = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        help_text='Номер недели курса (1-8)'
    )
    
    variation_number = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
        help_text='Номер вариации (для множественных intro/outro)'
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False)  # True for dev placeholders
    
    class Meta:
        db_table = 'video_clips'
        indexes = [
            models.Index(fields=['exercise', 'r2_kind', 'archetype']),
            models.Index(fields=['r2_kind', 'archetype']),  # For playlist queries
            models.Index(fields=['is_active', 'r2_kind']),  # For filtering active clips
        ]
        unique_together = [
            ['exercise', 'r2_kind', 'archetype', 'model_name', 'reminder_text']
        ]
    
    def __str__(self):
        return f"{self.exercise.name_ru if self.exercise else 'General'} - {self.r2_kind} - {self.archetype}"
    
    @property
    def signed_url(self):
        """Get signed URL for video from R2 storage"""
        if self.r2_file:
            from apps.core.services.media import MediaService
            return MediaService.get_signed_url(self.r2_file)
        elif self.r2_key:
            # Direct R2 key access for synced videos
            from apps.core.services.media import MediaService
            return MediaService.get_signed_url_from_key(self.r2_key)
        return ''
    
    @property
    def has_video(self) -> bool:
        """Check if video clip has available video content"""
        if self.provider == VideoProvider.R2:
            return bool(self.r2_file or self.r2_key)
        if self.provider == VideoProvider.STREAM:
            return bool(self.stream_uid or self.playback_id)
        if self.provider == VideoProvider.EXTERNAL:
            # Future: check external_url field
            return False
        return False


class WeeklyTheme(models.Model):
    """Weekly themes for structured course progression"""
    
    week_number = models.PositiveIntegerField(
        unique=True,
        validators=[MinValueValidator(1), MaxValueValidator(8)],
        help_text='Week number in the course (1-8)'
    )
    
    theme_title = models.CharField(
        max_length=100,
        help_text='Title of the weekly theme'
    )
    
    focus_area = models.CharField(
        max_length=200,
        help_text='Main focus area for the week'
    )
    
    description = models.TextField(
        blank=True,
        help_text='Detailed description of weekly objectives'
    )
    
    # Archetype-specific content variations
    mentor_content = models.TextField(
        blank=True,
        help_text='Content adapted for mentor archetype'
    )
    
    professional_content = models.TextField(
        blank=True,
        help_text='Content adapted for professional archetype'
    )
    
    peer_content = models.TextField(
        blank=True,
        help_text='Content adapted for peer archetype'
    )
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'weekly_themes'
        ordering = ['week_number']
        
    def __str__(self):
        return f"Week {self.week_number}: {self.theme_title}"
    
    def get_content_for_archetype(self, archetype: str) -> str:
        """Get content adapted for specific archetype"""
        content_map = {
            'mentor': self.mentor_content,
            'professional': self.professional_content, 
            'peer': self.peer_content
        }
        return content_map.get(archetype, self.description)


class WorkoutPlan(models.Model):
    STATUS_CHOICES = [
        ('DRAFT', 'Draft - awaiting confirmation'),
        ('CONFIRMED', 'Confirmed - ready to start'),
        ('ACTIVE', 'Active - in progress'),
        ('COMPLETED', 'Completed'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    
    # Plan details  
    name = models.CharField(max_length=200)
    duration_weeks = models.PositiveIntegerField(validators=[MinValueValidator(4), MaxValueValidator(8)])
    # goal field removed - data stored in plan_data JSON and user onboarding data
    
    # AI-generated plan data
    plan_data = models.JSONField()  # Complete plan structure with report
    ai_analysis = models.JSONField(blank=True, null=True)  # AI analysis data (deprecated)
    
    # Status tracking
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    
    # Weekly adaptation
    last_adaptation_date = models.DateTimeField(null=True, blank=True)
    adaptation_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=False)  # Legacy, use status instead
    
    class Meta:
        db_table = 'workout_plans'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
        
    def get_current_week(self):
        if not self.started_at:
            return 0
        days_passed = (timezone.now() - self.started_at).days
        return min((days_passed // 7) + 1, self.duration_weeks)


class DailyWorkout(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='daily_workouts')
    day_number = models.PositiveIntegerField()
    week_number = models.PositiveIntegerField()
    
    # Workout details
    name = models.CharField(max_length=200)
    exercises = models.JSONField()  # List of exercise data with sets, reps, rest
    is_rest_day = models.BooleanField(default=False)
    
    # Confidence task
    confidence_task = models.TextField(blank=True)
    
    # Completion tracking
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Micro-feedback
    feedback_rating = models.CharField(
        max_length=10,
        choices=[
            ('fire', '🔥 Great'),
            ('smile', '🙂 Good'),
            ('neutral', '😐 OK'),
            ('tired', '🤕 Hard'),
        ],
        blank=True
    )
    feedback_note = models.TextField(blank=True)
    
    # Exercise substitutions made
    substitutions = models.JSONField(default=dict)  # {original_exercise_id: substitute_exercise_id}
    
    class Meta:
        db_table = 'daily_workouts'
        unique_together = [['plan', 'day_number']]
        ordering = ['day_number']


class WorkoutExecution(models.Model):
    workout = models.ForeignKey(DailyWorkout, on_delete=models.CASCADE, related_name='executions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_executions')
    
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Detailed execution data
    exercise_data = models.JSONField()  # Actual sets, reps, weights performed
    calories_burned = models.PositiveIntegerField(null=True, blank=True)
    
    # XP earned
    xp_earned = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'workout_executions'
        ordering = ['-started_at']


# ===== New CSV-based models =====

class CSVExercise(models.Model):
    """
    Базовое упражнение, импортируется из data/clean/exercises_complete_r2.csv
    Обновлено под реальную структуру R2 (271 упражнение)
    """
    # Primary fields matching R2 structure
    id = models.CharField(primary_key=True, max_length=20)          # warmup_01, main_001, endurance_01, relaxation_01
    name_ru = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    
    # Classification fields
    level = models.CharField(max_length=20, default='beginner')     # beginner / intermediate / advanced
    muscle_group = models.CharField(max_length=120, blank=True)     # Все тело / Грудь / Спина / Ноги / и т.д.
    exercise_type = models.CharField(max_length=120, blank=True)    # strength / mobility / cardio / flexibility
    
    # AI integration fields
    ai_tags = models.JSONField(blank=True, default=list)
    
    # R2 structure support 
    r2_slug = models.CharField(max_length=50, blank=True, help_text='Original R2 slug format')
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Упражнение CSV"
        verbose_name_plural = "Упражнения CSV"
        db_table = 'csv_exercises'

    def __str__(self):
        return f"{self.id} – {self.name_ru}"


class ExplainerVideo(models.Model):
    """
    Скрипт или ссылка на видео-объяснение; 1:* к упражнению,
    разделено по архетипу тренера.
    """
    ARCHETYPE_CHOICES = [
        ("111", "Наставник"),
        ("222", "Профессионал"),
        ("333", "Ровесник"),
    ]

    exercise = models.ForeignKey(CSVExercise, on_delete=models.CASCADE, related_name="videos")
    archetype = models.CharField(max_length=3, choices=ARCHETYPE_CHOICES)
    script = models.TextField()                      # пока хранит текст; позже можно добавить video_url
    locale = models.CharField(max_length=5, default="ru")  # ru / en …

    class Meta:
        unique_together = ("exercise", "archetype", "locale")
        verbose_name = "Видео-объяснение"
        verbose_name_plural = "Видео-объяснения"
        db_table = 'explainer_videos'

    def __str__(self):
        return f"{self.exercise_id} – {self.get_archetype_display()}"

    @classmethod
    def from_row(cls, row: dict, archetype: str, locale: str = "ru"):
        return cls(
            exercise_id=row["exercise_id"],
            archetype=archetype,
            script=row[f"script_{locale}"],
            locale=locale,
        )


class WeeklyLesson(models.Model):
    """
    Текст «бонус-урока недели», 1 запись = 1 неделя × архетип × язык
    """
    week = models.PositiveSmallIntegerField()
    archetype = models.CharField(max_length=3, choices=[("111","Н"),("222","П"),("333","Р")])
    locale = models.CharField(max_length=5, default="ru")
    title = models.CharField(max_length=120)
    script = models.TextField()
    duration_sec = models.PositiveIntegerField(default=180, help_text="Estimated reading time in seconds")

    class Meta:
        unique_together = ("week", "archetype", "locale")
        ordering = ["week"]
        db_table = 'weekly_lessons'

    def __str__(self):
        return f"Week {self.week} - {self.get_archetype_display()}"


class FinalVideo(models.Model):
    arch = models.CharField(max_length=3, choices=[("111","Н"),("222","П"),("333","Р")], primary_key=True)
    locale = models.CharField(max_length=5, default="ru")
    script = models.TextField()

    class Meta:
        db_table = 'final_videos'

    def __str__(self):
        return f"Final - {self.get_arch_display()}"


class WeeklyNotification(models.Model):
    """
    Персональное уведомление о еженедельном уроке для каждого пользователя.
    Создается Celery beat task и потребляется фронтендом.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_notifications')
    week = models.PositiveSmallIntegerField()
    archetype = models.CharField(max_length=3, choices=[("111","Н"),("222","П"),("333","Р")])
    lesson_title = models.CharField(max_length=120)
    lesson_script = models.TextField()
    
    # Status tracking
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'weekly_notifications'
        unique_together = [('user', 'week')]
        ordering = ['-week', '-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['week']),
        ]
    
    def __str__(self):
        return f"Week {self.week} for {self.user.email} ({'read' if self.is_read else 'unread'})"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class DailyPlaylistItem(models.Model):
    """
    Плейлист дня - последовательность медиа-клипов из R2 для конкретной тренировки
    """
    ROLE_CHOICES = [
        ("intro", "Intro"),
        ("warmup", "Warm-up"),
        ("main", "Main Exercise Clip"),
        ("transition", "Transition"),
        ("cooldown", "Cooldown / Stretch"),
        ("timer", "Timer"),
        ("motivation", "Motivation"),
        ("breathing", "Breathing"),
    ]

    day = models.ForeignKey("DailyWorkout", on_delete=models.CASCADE, related_name="playlist_items")
    order = models.PositiveIntegerField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    media = models.ForeignKey("content.MediaAsset", on_delete=models.PROTECT, related_name="used_in_playlist")
    duration_seconds = models.PositiveIntegerField(null=True, blank=True)
    overlay = models.JSONField(default=dict, blank=True)  # подписи/подсказки/инструкции (опционально)

    class Meta:
        db_table = "daily_playlist_items"
        ordering = ["day_id", "order"]
        indexes = [
            models.Index(fields=["day", "order"]),
            models.Index(fields=["role"]),
        ]
        unique_together = [("day", "order")]

    def __str__(self):
        return f"Day {self.day.day_number} - #{self.order} {self.role}"
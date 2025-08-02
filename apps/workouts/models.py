from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone

User = get_user_model()


class Exercise(models.Model):
    DIFFICULTY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]
    
    MUSCLE_GROUP_CHOICES = [
        ('chest', 'Chest'),
        ('back', 'Back'),
        ('shoulders', 'Shoulders'),
        ('arms', 'Arms'),
        ('legs', 'Legs'),
        ('core', 'Core'),
        ('full_body', 'Full Body'),
    ]
    
    id = models.CharField(primary_key=True, max_length=36)
    slug = models.SlugField(unique=True, max_length=100)
    name = models.CharField(max_length=200)
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    muscle_groups = models.JSONField(default=list)  # List of muscle groups
    equipment_needed = models.JSONField(default=list)  # List of equipment
    equipment = models.CharField(
        max_length=50,
        default="bodyweight",
        help_text="Основной инвентарь: bodyweight | dumbbell | barbell …",
    )
    
    # Exercise alternatives (for substitution feature)
    alternatives = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    # Video references
    technique_video_url = models.URLField(blank=True, default='')
    mistake_video_url = models.URLField(blank=True, default='')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'exercises'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['difficulty']),
        ]
    
    def __str__(self):
        return self.name


class VideoClip(models.Model):
    TYPE_CHOICES = [
        ('technique', 'Technique'),
        ('mistake', 'Common Mistake'),
        ('intro', 'Introduction'),
        ('outro', 'Outro'),
        ('support', 'Support/Motivation'),
    ]
    
    exercise = models.ForeignKey(
        Exercise, 
        on_delete=models.CASCADE, 
        related_name='video_clips',
        null=True,
        blank=True
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    archetype = models.CharField(
        max_length=20, 
        choices=[
            ('bro', 'Бро'),
            ('sergeant', 'Сержант'),
            ('intellectual', 'Интеллектуал'),
        ]
    )
    model_name = models.CharField(max_length=50)  # mod1, mod2, mod3
    url = models.URLField()
    duration_seconds = models.PositiveIntegerField()
    
    # For reminder clips
    reminder_text = models.CharField(max_length=200, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_placeholder = models.BooleanField(default=False)  # True for dev placeholders
    
    class Meta:
        db_table = 'video_clips'
        indexes = [
            models.Index(fields=['exercise', 'type', 'archetype']),
        ]
        unique_together = [
            ['exercise', 'type', 'archetype', 'model_name', 'reminder_text']
        ]


class WorkoutPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    
    # Plan details
    name = models.CharField(max_length=200)
    duration_weeks = models.PositiveIntegerField(validators=[MinValueValidator(4), MaxValueValidator(8)])
    goal = models.CharField(max_length=100)
    
    # AI-generated plan data
    plan_data = models.JSONField()  # Complete plan structure
    ai_analysis = models.JSONField(blank=True, null=True)  # AI analysis data
    
    # Weekly adaptation
    last_adaptation_date = models.DateTimeField(null=True, blank=True)
    adaptation_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=False)  # User confirmed the plan
    
    class Meta:
        db_table = 'workout_plans'
        ordering = ['-created_at']
        
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
    Базовое упражнение, импортируется из data/clean/exercises.csv
    """
    id = models.CharField(primary_key=True, max_length=20)          # EX027_v2
    name_ru = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True)
    level = models.CharField(max_length=20)                         # beginner / intermediate / advanced
    description = models.TextField(blank=True)
    muscle_group = models.CharField(max_length=50, blank=True)
    exercise_type = models.CharField(max_length=50, blank=True)     # strength / stretch / cardio
    ai_tags = models.JSONField(blank=True, default=list)

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
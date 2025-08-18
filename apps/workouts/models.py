from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
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
    
    # Exercise alternatives (for substitution feature)
    alternatives = models.ManyToManyField('self', blank=True, symmetrical=True)
    
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
        ('instruction', 'Instruction'),
        ('reminder', 'Reminder'),
        ('intro', 'Daily Intro'),
        ('weekly', 'Weekly Motivation'),
        ('progress', 'Progress Milestone'),
        ('final', 'Final Congratulation'),
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
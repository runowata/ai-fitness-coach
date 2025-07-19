from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, Q

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
    
    # Use CharField to match existing table structure
    id = models.CharField(primary_key=True, max_length=36)
    slug = models.SlugField(unique=True, max_length=100)
    name = models.CharField(max_length=100)  # Match existing table
    description = models.TextField()
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES)
    muscle_groups = models.TextField()  # Match existing table
    equipment = models.CharField(max_length=50)  # Match existing table name
    
    # Alternatives for exercises
    alternatives = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="alternative_for",
        help_text="Упражнения-замены"
    )
    # technique_video_url = models.URLField(blank=True)
    # mistake_video_url = models.URLField(blank=True)
    # created_at = models.DateTimeField(auto_now_add=True)
    # updated_at = models.DateTimeField(auto_now=True)
    # is_active = models.BooleanField(default=True)
    
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
        ('weekly', 'Weekly Motivation'),
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
        ],
        blank=True,
        null=True
    )
    model_name = models.CharField(max_length=50, blank=True, null=True)  # mod1, mod2, mod3
    url = models.URLField(unique=True)
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
        """Get current week with caching for performance"""
        if not self.started_at:
            return 0
        
        # Cache key based on plan ID and current date
        cache_key = f"workout_plan_{self.id}_current_week_{timezone.now().date()}"
        current_week = cache.get(cache_key)
        
        if current_week is None:
            days_passed = (timezone.now() - self.started_at).days
            current_week = min((days_passed // 7) + 1, self.duration_weeks)
            # Cache for 1 hour
            cache.set(cache_key, current_week, 3600)
        
        return current_week
    
    def is_6_weeks_completed(self):
        """Check if user has completed all workouts for 6 weeks"""
        if self.duration_weeks < 6:
            return False
            
        # Count completed workouts in first 6 weeks
        completed_workouts = self.daily_workouts.filter(
            week_number__lte=6,
            completed_at__isnull=False
        ).count()
        
        # Count total workouts in first 6 weeks (excluding rest days)
        total_workouts = self.daily_workouts.filter(
            week_number__lte=6,
            is_rest_day=False
        ).count()
        
        # Consider completed if 80% or more workouts are done
        completion_rate = completed_workouts / total_workouts if total_workouts > 0 else 0
        return completion_rate >= 0.8
    
    def get_program_completion_stats(self):
        """Get detailed completion statistics for the program with optimized queries"""
        cache_key = f"workout_plan_{self.id}_completion_stats"
        stats = cache.get(cache_key)
        
        if stats is None:
            # Single optimized query for all workouts
            workouts_summary = self.daily_workouts.aggregate(
                total_completed=Count('id', filter=Q(completed_at__isnull=False)),
                total_workouts=Count('id', filter=Q(is_rest_day=False))
            )
            
            # Weekly breakdown with optimized query
            weekly_data = self.daily_workouts.filter(
                week_number__lte=min(6, self.duration_weeks)
            ).values('week_number').annotate(
                completed=Count('id', filter=Q(completed_at__isnull=False)),
                total=Count('id', filter=Q(is_rest_day=False))
            ).order_by('week_number')
            
            weekly_stats = []
            for week_data in weekly_data:
                completion_rate = (week_data['completed'] / week_data['total'] * 100) if week_data['total'] > 0 else 0
                weekly_stats.append({
                    'week': week_data['week_number'],
                    'completed': week_data['completed'],
                    'total': week_data['total'],
                    'completion_rate': completion_rate
                })
            
            stats = {
                'total_completed': workouts_summary['total_completed'],
                'total_workouts': workouts_summary['total_workouts'],
                'overall_completion_rate': (workouts_summary['total_completed'] / workouts_summary['total_workouts'] * 100) if workouts_summary['total_workouts'] > 0 else 0,
                'weekly_stats': weekly_stats,
                'is_6_weeks_completed': self.is_6_weeks_completed()
            }
            
            # Cache for 30 minutes
            cache.set(cache_key, stats, 1800)
        
        return stats
    
    def clear_cache(self):
        """Clear all cached data for this workout plan"""
        cache_keys = [
            f"workout_plan_{self.id}_current_week_{timezone.now().date()}",
            f"workout_plan_{self.id}_completion_stats"
        ]
        cache.delete_many(cache_keys)
    
    def save(self, *args, **kwargs):
        """Override save to clear cache when plan is updated"""
        super().save(*args, **kwargs)
        self.clear_cache()


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


class WeeklyFeedback(models.Model):
    """User feedback for a completed week"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_feedbacks')
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='weekly_feedbacks')
    week_number = models.PositiveIntegerField()
    
    # Overall week assessment
    overall_difficulty = models.CharField(
        max_length=20,
        choices=[
            ('too_easy', 'Слишком легко'),
            ('just_right', 'В самый раз'),
            ('too_hard', 'Слишком тяжело'),
            ('varied', 'По-разному')
        ],
        default='just_right'
    )
    
    energy_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Низкий'),
            ('medium', 'Средний'),
            ('high', 'Высокий')
        ],
        default='medium'
    )
    
    motivation_level = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Низкая'),
            ('medium', 'Средняя'),
            ('high', 'Высокая')
        ],
        default='medium'
    )
    
    # Specific feedback
    most_challenging_exercises = models.JSONField(default=list)  # List of exercise slugs
    favorite_exercises = models.JSONField(default=list)  # List of exercise slugs
    
    # Progress perception
    strength_progress = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )  # 1-10 scale
    
    confidence_progress = models.IntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(10)]
    )  # 1-10 scale
    
    # Suggestions
    wants_more_cardio = models.BooleanField(default=False)
    wants_more_strength = models.BooleanField(default=False)
    wants_shorter_workouts = models.BooleanField(default=False)
    wants_longer_workouts = models.BooleanField(default=False)
    
    # Free text feedback
    what_worked_well = models.TextField(blank=True)
    what_needs_improvement = models.TextField(blank=True)
    additional_notes = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'weekly_feedbacks'
        unique_together = ['user', 'plan', 'week_number']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Week {self.week_number} feedback for {self.user.email}"
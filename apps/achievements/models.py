from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Achievement(models.Model):
    TRIGGER_TYPE_CHOICES = [
        ('workout_count', 'Total Workouts'),
        ('streak_days', 'Consecutive Days'),
        ('xp_earned', 'Experience Points'),
        ('plan_completed', 'Plan Completion'),
        ('perfect_week', 'Perfect Week'),
        ('confidence_tasks', 'Confidence Tasks Completed'),
    ]
    
    slug = models.SlugField(unique=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    # Achievement trigger
    trigger_type = models.CharField(max_length=30, choices=TRIGGER_TYPE_CHOICES)
    trigger_value = models.PositiveIntegerField()  # e.g., 7 for 7-day streak
    
    # Rewards
    xp_reward = models.PositiveIntegerField(default=0)
    unlocks_story_chapter = models.ForeignKey(
        'content.StoryChapter',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Display
    icon_url = models.URLField(blank=True)
    order = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'achievements'
        ordering = ['order']
    
    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    
    unlocked_at = models.DateTimeField(auto_now_add=True)
    notified = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'user_achievements'
        unique_together = [['user', 'achievement']]
        ordering = ['-unlocked_at']


class XPTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('workout_completed', 'Workout Completed'),
        ('achievement_unlocked', 'Achievement Unlocked'),
        ('perfect_week', 'Perfect Week Bonus'),
        ('confidence_task', 'Confidence Task Completed'),
        ('daily_login', 'Daily Login Bonus'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_transactions')
    amount = models.PositiveIntegerField()
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPE_CHOICES)
    description = models.CharField(max_length=200)
    
    # Related objects
    workout_execution = models.ForeignKey(
        'workouts.WorkoutExecution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'xp_transactions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
        ]


class DailyProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_progress')
    date = models.DateField()
    
    # Daily metrics
    workouts_completed = models.PositiveIntegerField(default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    confidence_tasks_completed = models.PositiveIntegerField(default=0)
    
    # Streak tracking
    is_streak_day = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'daily_progress'
        unique_together = [['user', 'date']]
        ordering = ['-date']
        indexes = [
            models.Index(fields=['user', '-date']),
        ]
        
    @classmethod
    def update_for_user(cls, user, date=None):
        if date is None:
            date = timezone.now().date()
            
        progress, created = cls.objects.get_or_create(
            user=user,
            date=date
        )
        
        # Update streak
        yesterday = date - timezone.timedelta(days=1)
        yesterday_progress = cls.objects.filter(user=user, date=yesterday).first()
        
        if progress.workouts_completed > 0:
            progress.is_streak_day = True
            profile = user.profile
            
            if yesterday_progress and yesterday_progress.is_streak_day:
                profile.current_streak += 1
            else:
                profile.current_streak = 1
                
            profile.longest_streak = max(profile.longest_streak, profile.current_streak)
            profile.save(update_fields=['current_streak', 'longest_streak'])
            
        progress.save()
        return progress
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import pytz


class User(AbstractUser):
    MEASUREMENT_CHOICES = [
        ('metric', 'Metric (kg/cm)'),
        ('imperial', 'Imperial (lbs/in)'),
    ]
    
    email = models.EmailField(unique=True)
    timezone = models.CharField(
        max_length=50,
        default='Europe/Zurich',
        choices=[(tz, tz) for tz in pytz.all_timezones]
    )
    measurement_system = models.CharField(
        max_length=10,
        choices=MEASUREMENT_CHOICES,
        default='metric'
    )
    is_adult_confirmed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # 2FA
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=32, blank=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
        ]


class UserProfile(models.Model):
    ARCHETYPE_CHOICES = [
        ('bro', 'Бро'),
        ('sergeant', 'Сержант'),
        ('intellectual', 'Интеллектуал'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    archetype = models.CharField(max_length=20, choices=ARCHETYPE_CHOICES, blank=True)
    
    # Physical data
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)  # in cm or inches
    weight = models.PositiveIntegerField(null=True, blank=True)  # in kg or lbs
    
    # Goals
    goals = models.JSONField(default=dict)
    limitations = models.JSONField(default=dict)
    
    # XP System
    experience_points = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    
    # Preferences
    notification_time = models.TimeField(default='08:00')
    push_notifications_enabled = models.BooleanField(default=True)
    email_notifications_enabled = models.BooleanField(default=True)
    
    # Tracking
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    last_workout_at = models.DateTimeField(null=True, blank=True)
    total_workouts_completed = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    longest_streak = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'user_profiles'
        
    def add_xp(self, points):
        self.experience_points += points
        # Simple level calculation: 100 XP per level
        self.level = (self.experience_points // 100) + 1
        self.save(update_fields=['experience_points', 'level'])
        
    def get_local_time(self):
        tz = pytz.timezone(self.user.timezone)
        return timezone.now().astimezone(tz)
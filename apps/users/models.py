import pytz
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


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
    completed_onboarding = models.BooleanField(default=False)  # Critical for dashboard redirect logic
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
        ('mentor', 'Мудрый наставник'),
        ('professional', 'Успешный профессионал'),
        ('peer', 'Ровесник'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    archetype = models.CharField(max_length=20, choices=ARCHETYPE_CHOICES, default='mentor')
    
    # Physical data
    age = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)  # in cm or inches
    weight = models.PositiveIntegerField(null=True, blank=True)  # in kg or lbs
    
    # Goals
    goals = models.JSONField(default=dict)
    limitations = models.JSONField(default=dict)
    
    # Health data from onboarding
    health_conditions = models.JSONField(default=dict)  # Cardiovascular, diabetes, etc.
    chronic_pain_areas = models.JSONField(default=dict)  # Body map data
    flexibility_level = models.IntegerField(null=True, blank=True)  # 1-5 scale
    injuries_surgeries = models.TextField(blank=True)
    hiv_status_disclosed = models.BooleanField(default=False)
    medications = models.TextField(blank=True)
    exercise_limitations = models.JSONField(default=dict)
    is_smoker = models.BooleanField(default=False)
    
    # Lifestyle data
    work_activity_level = models.CharField(max_length=20, blank=True)  # sedentary/moderate/active
    sleep_hours = models.IntegerField(null=True, blank=True)
    sleep_quality = models.IntegerField(null=True, blank=True)  # 1-5 scale
    stress_level = models.IntegerField(null=True, blank=True)  # 1-5 scale
    meal_frequency = models.IntegerField(null=True, blank=True)
    water_intake = models.CharField(max_length=20, blank=True)
    alcohol_consumption = models.CharField(max_length=20, blank=True)
    
    # Sexual health preferences
    sexual_health_goals = models.JSONField(default=dict)
    sexual_stamina_rating = models.IntegerField(null=True, blank=True)  # 1-5 scale
    flexibility_importance = models.IntegerField(null=True, blank=True)  # 1-5 scale
    kegel_exercises_interest = models.BooleanField(default=False)
    sexual_role = models.CharField(max_length=20, blank=True)
    intimacy_confidence = models.IntegerField(null=True, blank=True)  # 1-5 scale
    
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
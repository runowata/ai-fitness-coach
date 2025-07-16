"""Models for AI integration tracking and configuration"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class AIProviderConfig(models.Model):
    """Configuration for AI providers"""
    
    PROVIDER_CHOICES = [
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
    ]
    
    name = models.CharField(max_length=50, choices=PROVIDER_CHOICES, unique=True)
    api_key = models.CharField(max_length=255, blank=True)
    model_name = models.CharField(max_length=100, default='gpt-4o-mini')
    max_tokens = models.IntegerField(default=2000)
    temperature = models.FloatField(default=0.7, validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_provider_configs'
        verbose_name = 'AI Provider Configuration'
        verbose_name_plural = 'AI Provider Configurations'
    
    def __str__(self):
        return f"{self.get_name_display()} - {self.model_name}"


class AIRequestLog(models.Model):
    """Log of AI API requests for monitoring and debugging"""
    
    REQUEST_TYPES = [
        ('plan_generation', 'Plan Generation'),
        ('weekly_adaptation', 'Weekly Adaptation'),
        ('evolution_plan', 'Evolution Plan'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_requests')
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPES)
    provider = models.CharField(max_length=50)
    model_name = models.CharField(max_length=100)
    
    # Request details
    prompt_length = models.IntegerField()
    max_tokens = models.IntegerField()
    temperature = models.FloatField()
    
    # Response details
    response_length = models.IntegerField(null=True, blank=True)
    tokens_used = models.IntegerField(null=True, blank=True)
    processing_time_ms = models.IntegerField(null=True, blank=True)
    
    # Status
    success = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ai_request_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'request_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.get_request_type_display()} - {self.created_at}"


class AIPromptTemplate(models.Model):
    """Store and manage AI prompt templates"""
    
    TEMPLATE_TYPES = [
        ('workout_plan_bro', 'Workout Plan - Bro'),
        ('workout_plan_sergeant', 'Workout Plan - Sergeant'),
        ('workout_plan_intellectual', 'Workout Plan - Intellectual'),
        ('weekly_adaptation', 'Weekly Adaptation'),
        ('evolution_plan', 'Evolution Plan'),
    ]
    
    name = models.CharField(max_length=100, choices=TEMPLATE_TYPES, unique=True)
    content = models.TextField()
    variables = models.JSONField(default=list)  # List of expected variables
    
    # Metadata
    version = models.CharField(max_length=20, default='1.0')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ai_prompt_templates'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.get_name_display()} v{self.version}"


class PlanGenerationMetrics(models.Model):
    """Metrics for plan generation performance"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='plan_metrics')
    
    # Generation details
    archetype = models.CharField(max_length=20)
    generation_time_ms = models.IntegerField()
    tokens_used = models.IntegerField()
    
    # Plan characteristics
    total_exercises = models.IntegerField()
    total_workouts = models.IntegerField()
    duration_weeks = models.IntegerField()
    
    # Quality metrics
    plan_complexity_score = models.FloatField(null=True, blank=True)  # 1-10 scale
    exercise_variety_score = models.FloatField(null=True, blank=True)  # 1-10 scale
    
    # User feedback
    user_satisfaction = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'plan_generation_metrics'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'archetype']),
            models.Index(fields=['created_at']),
        ]
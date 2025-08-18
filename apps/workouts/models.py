from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Exercise(models.Model):
    """
    Минимальная модель упражнения.
    Все данные о видео хранятся в SYSTEM_616_VIDEOS.json на Cloudflare.
    """
    # Только exercise_slug из промпта (high_knees, push_ups и т.д.)
    exercise_slug = models.CharField(primary_key=True, max_length=100)
    
    class Meta:
        db_table = 'exercises'
        ordering = ['exercise_slug']
    
    def __str__(self):
        return self.exercise_slug


class WorkoutPlan(models.Model):
    """
    AI-сгенерированный план тренировок.
    Содержит JSON с exercise_slug для каждого дня.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_plans')
    
    # План от AI в формате JSON
    # Содержит exercise_slug для каждого дня согласно схеме плейлиста
    plan_data = models.JSONField()
    
    # AI анализ пользователя (отдельно от плана)
    ai_analysis = models.JSONField(null=True, blank=True)
    
    # Длительность плана
    duration_weeks = models.IntegerField(default=6)
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    is_confirmed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'workout_plans'
        ordering = ['-created_at']


class DailyWorkout(models.Model):
    """
    Ежедневная тренировка с плейлистом из 16 видео.
    """
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='daily_workouts')
    day_number = models.IntegerField()
    week_number = models.IntegerField()
    name = models.CharField(max_length=200)
    
    # Список упражнений для дня
    exercises = models.JSONField()
    
    # Плейлист на день (16 видео в строгой последовательности)
    # Формат: [
    #   {"type": "motivational", "category": "intro"},
    #   {"type": "exercise", "category": "warmup", "exercise_slug": "high_knees"},
    #   ...
    # ]
    playlist = models.JSONField(default=list)
    
    # Статус выполнения и даты
    is_rest_day = models.BooleanField(default=False)
    completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    
    # Задания на уверенность
    confidence_task = models.TextField(blank=True)
    
    # Обратная связь
    feedback_rating = models.IntegerField(null=True, blank=True)  # 1-5 звезд
    feedback_note = models.TextField(blank=True)
    
    # Замены упражнений
    substitutions = models.JSONField(default=dict)
    
    class Meta:
        db_table = 'daily_workouts'
        unique_together = [['plan', 'day_number']]
        ordering = ['day_number']


# Удаляем все старые модели VideoClip, WorkoutExecution и т.д.
# Они не нужны для новой структуры с 616 видео на Cloudflare
from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
import re

from .constants import Archetype, VideoKind

User = get_user_model()


class VideoProvider(models.TextChoices):
    R2 = "r2", "Cloudflare R2"
    STREAM = "stream", "Cloudflare Stream"
    EXTERNAL = "external", "External URL"


# Exercise model COMPLETELY REMOVED in Phase 5.6
# Replaced by CSVExercise model for cleaner structure


class R2Video(models.Model):
    """
    Видео из Cloudflare R2 хранилища - ТОЛЬКО необходимые поля
    Основано на реальной структуре R2 (616 видео в 5 категориях)
    """
    # Код = имя файла без расширения
    code = models.CharField(max_length=150, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Категория определяется по папке в R2
    CATEGORY_CHOICES = [
        ('exercises', 'Упражнения'),         # videos/exercises/ - 271 файл
        ('motivation', 'Мотивация'),         # videos/motivation/ - 315 файлов
        ('final', 'Финальные'),              # videos/final/ - 3 файла
        ('progress', 'Прогресс'),            # videos/progress/ - 9 файлов  
        ('weekly', 'Еженедельные'),          # videos/weekly/ - 18 файлов
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Landing page support - дополнительные поля для отображения на сайте
    display_title = models.CharField(max_length=200, blank=True, help_text="Заголовок для отображения на landing page")
    display_description = models.TextField(blank=True, help_text="Описание для отображения на landing page")
    is_featured = models.BooleanField(default=False, help_text="Показывать на главной странице")
    sort_order = models.PositiveIntegerField(default=0, help_text="Порядок сортировки для отображения")
    
    # Archetype support - для архетипных видео
    ARCHETYPE_CHOICES = [
        ('mentor', 'Мудрый наставник'),
        ('professional', 'Профессиональный тренер'), 
        ('peer', 'Лучший друг'),
    ]
    archetype = models.CharField(max_length=20, choices=ARCHETYPE_CHOICES, blank=True, help_text="Архетип тренера для видео")
    
    class Meta:
        db_table = 'r2_videos'
        verbose_name = 'R2 Видео'
        verbose_name_plural = 'R2 Видео'
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Валидация R2Video модели"""
        super().clean()
        
        # Проверяем код на валидные символы (без пробелов и спецсимволов)
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.code):
            raise ValidationError({
                'code': 'Код должен содержать только буквы, цифры, _ и -'
            })
        
        # Проверяем длину кода
        if len(self.code) < 3:
            raise ValidationError({
                'code': 'Код должен содержать минимум 3 символа'
            })
        
        # Проверяем соответствие кода категории для exercises
        if self.category == 'exercises':
            valid_prefixes = ['warmup_', 'main_', 'endurance_', 'relaxation_']
            if not any(self.code.startswith(prefix) for prefix in valid_prefixes):
                raise ValidationError({
                    'code': f'Для категории exercises код должен начинаться с: {", ".join(valid_prefixes)}'
                })
        
        # Проверяем, что название не пустое
        if not self.name.strip():
            raise ValidationError({
                'name': 'Название не может быть пустым'
            })
    
    @property
    def r2_url(self):
        """Генерирует публичный URL в R2"""
        if not self.code or not self.category:
            return None
        # Use R2 public URL from settings if available
        from django.conf import settings
        base_url = getattr(settings, 'R2_PUBLIC_BASE_URL', None)
        if not base_url:
            # Fallback to hardcoded URL
            base_url = "https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev"
        # Ensure no trailing slash
        base_url = base_url.rstrip('/')
        return f"{base_url}/videos/{self.category}/{self.code}.mp4"
    
    @property 
    def exercise_type(self):
        """Определяет тип упражнения для категории exercises"""
        if self.category == 'exercises':
            if self.code.startswith('warmup_'):
                return 'warmup'
            elif self.code.startswith('main_') or self.code.startswith('endurance_') or self.code.startswith('relaxation_'):
                # Разбираем из названия файла: main_01_technique_m01.mp4
                parts = self.code.split('_')
                if len(parts) >= 2:
                    return parts[0]  # main, endurance, relaxation  
            return 'main'  # По умолчанию основное упражнение
        return self.category
    
    def save(self, *args, **kwargs):
        """Сохранение с валидацией"""
        self.full_clean()  # Запускаем валидацию перед сохранением
        super().save(*args, **kwargs)


class R2Image(models.Model):
    """
    Изображения из R2 хранилища для мотивационных карточек
    Основано на реальной структуре R2 (2009 изображений в 4 категориях)
    """
    # Код = имя файла без расширения  
    code = models.CharField(max_length=150, unique=True, primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Категория по папкам в R2
    CATEGORY_CHOICES = [
        ('avatars', 'Аватары'),              # images/avatars/ - 9 файлов
        ('quotes', 'Цитаты'),                # photos/quotes/ - 1000 файлов
        ('progress', 'Прогресс'),            # photos/progress/ - 500 файлов
        ('workout', 'Тренировки'),           # photos/workout/ - 500 файлов
    ]
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Landing page support - дополнительные поля для отображения
    alt_text = models.CharField(max_length=200, blank=True, help_text="Альтернативный текст для изображения")
    is_hero_image = models.BooleanField(default=False, help_text="Главное изображение на landing page")
    is_featured = models.BooleanField(default=False, help_text="Показывать в featured галерее")
    sort_order = models.PositiveIntegerField(default=0, help_text="Порядок сортировки для отображения")
    
    # Archetype support - для архетипных изображений (аватары)
    ARCHETYPE_CHOICES = [
        ('mentor', 'Мудрый наставник'),
        ('professional', 'Профессиональный тренер'), 
        ('peer', 'Лучший друг'),
    ]
    archetype = models.CharField(max_length=20, choices=ARCHETYPE_CHOICES, blank=True, help_text="Архетип для аватаров")
    
    class Meta:
        db_table = 'r2_images'
        verbose_name = 'R2 Изображение'
        verbose_name_plural = 'R2 Изображения'
        
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def clean(self):
        """Валидация R2Image модели"""
        super().clean()
        
        # Проверяем код на валидные символы
        if not re.match(r'^[a-zA-Z0-9_-]+$', self.code):
            raise ValidationError({
                'code': 'Код должен содержать только буквы, цифры, _ и -'
            })
        
        # Проверяем длину кода
        if len(self.code) < 3:
            raise ValidationError({
                'code': 'Код должен содержать минимум 3 символа'
            })
        
        # Проверяем, что название не пустое
        if not self.name.strip():
            raise ValidationError({
                'name': 'Название не может быть пустым'
            })
        
        # Специфические проверки для категорий
        if self.category == 'quotes' and not self.code.startswith('card_'):
            raise ValidationError({
                'code': 'Для категории quotes код должен начинаться с "card_"'
            })
    
    @property
    def r2_url(self):
        """Генерирует публичный URL в R2"""
        if not self.code or not self.category:
            return None
        # Use R2 public URL from settings if available
        from django.conf import settings
        base_url = getattr(settings, 'R2_PUBLIC_BASE_URL', None)
        if not base_url:
            # Fallback to hardcoded URL
            base_url = "https://pub-d620683e68bf49abb422f1bc95810ff7.r2.dev"
        # Ensure no trailing slash
        base_url = base_url.rstrip('/')
        if self.category == 'avatars':
            return f"{base_url}/images/avatars/{self.code}.jpg"
        else:
            return f"{base_url}/photos/{self.category}/{self.code}.jpg"
    
    def save(self, *args, **kwargs):
        """Сохранение с валидацией"""
        self.full_clean()  # Запускаем валидацию перед сохранением
        super().save(*args, **kwargs)


# УДАЛЕНО: VideoClip alias - все ссылки обновлены на R2Video


# УДАЛЕНО: WeeklyTheme - дублировал R2Video(weekly), пустая модель


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
    duration_weeks = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(12)])  # Changed: allow 1 week for demo plans
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
        unique_together = [['plan', 'week_number', 'day_number']]
        ordering = ['week_number', 'day_number']


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
    Упрощенная модель упражнения - только необходимые поля
    Тип определяется по префиксу id (warmup_, main_, endurance_, relaxation_)
    """
    # Только необходимые поля
    id = models.CharField(primary_key=True, max_length=20)  # warmup_01, main_001, etc
    name_ru = models.CharField(max_length=120)  # Название упражнения
    description = models.TextField(blank=True)  # Описание упражнения
    
    class Meta:
        verbose_name = "Упражнение"
        verbose_name_plural = "Упражнения"
        db_table = 'csv_exercises'

    def __str__(self):
        return f"{self.id} – {self.name_ru}"
    
    @property
    def video_type(self):
        """Определяет тип видео по префиксу id"""
        if self.id.startswith('warmup_'):
            return 'warmup'
        elif self.id.startswith('main_'):
            return 'main'
        elif self.id.startswith('endurance_'):
            return 'endurance'
        elif self.id.startswith('relaxation_'):
            return 'relaxation'
        return 'unknown'


# УДАЛЕНО: ExplainerVideo - дублировал R2Video(exercises), использовать R2Video с category='exercises'


# УДАЛЕНО: WeeklyLesson - дублировал R2Video(weekly), использовать R2Video с category='weekly'


# УДАЛЕНО: FinalVideo - дублировал R2Video(final), использовать R2Video с category='final'


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
    Плейлист дня - последовательность видео из R2 для конкретной тренировки
    Обновлено для использования R2Video вместо MediaAsset
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
    # ОБНОВЛЕНО: используем R2Video вместо MediaAsset
    # Это поле заменяет старое media поле
    video = models.ForeignKey("R2Video", on_delete=models.PROTECT, related_name="used_in_playlist")
    # Старое поле media будет удалено в миграции
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
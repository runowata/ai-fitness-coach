"""
Упрощенные модели для системы видеоплейлистов
Только необходимые поля для воспроизведения видео по плейлисту на 3 недели
"""
from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class VideoType(models.TextChoices):
    """Типы видео согласно структуре в R2"""
    # Упражнения (модель)
    WARMUP = "warmup", "Разминка"
    MAIN = "main", "Основные упражнения" 
    ENDURANCE = "endurance", "Сексуальная выносливость"
    RELAXATION = "relaxation", "Расслабление"
    
    # Мотивационные (тренер)
    INTRO = "intro", "Вступление и приветствие"
    WARMUP_MOTIVATION = "warmup_motivation", "Мотивация после разминки"
    MAIN_MOTIVATION = "main_motivation", "Мотивация после основных"
    TRAINER_SPEECH = "trainer_speech", "Мотивирующий ролик тренера"  
    CLOSING = "closing", "Напутственное слово"


class ArchetypeType(models.TextChoices):
    """Типы тренеров"""
    BRO = "bro", "Best Mate (peer/333)"
    INTELLECTUAL = "intellectual", "Wise Mentor (mentor/111)"
    SERGEANT = "sergeant", "Pro Coach (professional/222)"


class Video(models.Model):
    """Упрощенная модель видео - только необходимые поля"""
    # Основные поля
    code = models.CharField(max_length=100, unique=True, help_text="Код видео в R2 (имя файла без .mp4)")
    name = models.CharField(max_length=200, help_text="Название упражнения/мотивации")
    description = models.TextField(blank=True, help_text="Описание упражнения")
    video_type = models.CharField(max_length=20, choices=VideoType.choices, help_text="Тип видео")
    
    # Для тренеров - архетип, для упражнений - пустое
    archetype = models.CharField(max_length=20, choices=ArchetypeType.choices, blank=True, help_text="Архетип тренера (только для мотивационных)")
    
    # Для упражнений - номер по порядку, для тренеров - день (1-21)
    sequence_number = models.PositiveIntegerField(help_text="Номер упражнения или день тренировки")
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'simple_videos'
        ordering = ['video_type', 'sequence_number']
        indexes = [
            models.Index(fields=['video_type', 'archetype']),
            models.Index(fields=['video_type', 'sequence_number']),
        ]
    
    def __str__(self):
        if self.archetype:
            return f"{self.get_video_type_display()} - {self.get_archetype_display()} - День {self.sequence_number}"
        else:
            return f"{self.get_video_type_display()} #{self.sequence_number} - {self.name}"
    
    @property
    def r2_url(self):
        """Генерирует URL для видео в R2"""
        base_url = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
        if self.video_type in ['warmup', 'main', 'endurance', 'relaxation']:
            # Упражнения: /videos/exercises/{code}.mp4
            return f"{base_url}/videos/exercises/{self.code}.mp4"
        else:
            # Мотивационные: /videos/motivation/{code}.mp4
            return f"{base_url}/videos/motivation/{self.code}.mp4"


class WorkoutDay(models.Model):
    """Упрощенная модель дня тренировки"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_days')
    day_number = models.PositiveIntegerField(validators=[models.validators.MinValueValidator(1), models.validators.MaxValueValidator(21)])
    archetype = models.CharField(max_length=20, choices=ArchetypeType.choices)
    
    # Статус
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'simple_workout_days'
        unique_together = ('user', 'day_number')
        ordering = ['day_number']
    
    def __str__(self):
        return f"День {self.day_number} - {self.user.email} ({self.get_archetype_display()})"
    
    @property
    def week_number(self):
        """Номер недели (1-3)"""
        return ((self.day_number - 1) // 7) + 1
    
    def get_playlist(self):
        """Генерирует плейлист из 16 видео согласно идеальной структуре"""
        # Идеальный плейлист:
        playlist = []
        
        # 1. Вступление и приветствие (Тренер)
        playlist.append(self._get_trainer_video('intro'))
        
        # 2-3. Разминка упражнение 1-2 (Модель)
        playlist.extend(self._get_exercise_videos('warmup', 2))
        
        # 4. Мотивация после разминки (Тренер)
        playlist.append(self._get_trainer_video('warmup_motivation'))
        
        # 5-9. Основные упражнения 1-5 (Модель)
        playlist.extend(self._get_exercise_videos('main', 5))
        
        # 10. Мотивация после основных (Тренер)
        playlist.append(self._get_trainer_video('main_motivation'))
        
        # 11-12. Секс. выносливость упр. 1-2 (Модель)
        playlist.extend(self._get_exercise_videos('endurance', 2))
        
        # 13. Мотивирующий ролик тренера (Тренер)
        playlist.append(self._get_trainer_video('trainer_speech'))
        
        # 14-15. Расслабление упражнения 1-2 (Модель)
        playlist.extend(self._get_exercise_videos('relaxation', 2))
        
        # 16. Напутственное слово (Тренер)
        playlist.append(self._get_trainer_video('closing'))
        
        return playlist
    
    def _get_trainer_video(self, video_type):
        """Получает мотивационное видео тренера для данного дня"""
        try:
            return Video.objects.get(
                video_type=video_type,
                archetype=self.archetype,
                sequence_number=self.day_number
            )
        except Video.DoesNotExist:
            return None
    
    def _get_exercise_videos(self, exercise_type, count):
        """Получает упражнения, не повторяющиеся в течение 3 недель"""
        # Простая логика: равномерно распределяем упражнения по дням
        start_idx = ((self.day_number - 1) * count) % Video.objects.filter(video_type=exercise_type, is_active=True).count()
        
        videos = list(Video.objects.filter(
            video_type=exercise_type,
            is_active=True
        ).order_by('sequence_number')[start_idx:start_idx + count])
        
        # Если не хватает в конце, берем с начала
        if len(videos) < count:
            remaining = count - len(videos)
            videos.extend(list(Video.objects.filter(
                video_type=exercise_type,
                is_active=True
            ).order_by('sequence_number')[:remaining]))
        
        return videos


class UserProfile(models.Model):
    """Упрощенный профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='simple_profile')
    archetype = models.CharField(max_length=20, choices=ArchetypeType.choices)
    current_day = models.PositiveIntegerField(default=1, validators=[models.validators.MinValueValidator(1), models.validators.MaxValueValidator(21)])
    
    # Метаданные
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'simple_user_profiles'
    
    def __str__(self):
        return f"{self.user.email} - {self.get_archetype_display()} - День {self.current_day}"
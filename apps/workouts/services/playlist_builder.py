from typing import List
from django.db import transaction
from apps.workouts.models import DailyWorkout, R2Video
from apps.core.services.unified_media import UnifiedMediaService

# Обновленный шаблон плейлиста под R2 структуру
IDEAL_TEMPLATE = [
    ("motivation", 1),   # Мотивационное открытие
    ("exercises", 1),    # Разминка (warmup_*)
    ("exercises", 4),    # Основные упражнения (main_*, endurance_*, relaxation_*)
    ("motivation", 1),   # Завершающая мотивация
]

class R2PlaylistBuilder:
    """
    Строит плейлист дня из R2Video через UnifiedMediaService
    Заменяет дублирующую логику MediaAsset
    """
    def __init__(self, day: DailyWorkout, archetype: str = None):
        self.day = day
        self.archetype = archetype or 'mentor'  # По умолчанию наставник

    def _pick_videos(self, category: str, exercise_type: str = None, count: int = 1) -> List[R2Video]:
        """Выбирает видео для категории через UnifiedMediaService"""
        if category == "exercises" and exercise_type:
            # Для упражнений используем специфический тип
            videos = UnifiedMediaService.get_workout_videos_for_exercise(
                exercise_type=exercise_type, 
                archetype=self.archetype
            )
        else:
            # Для остальных категорий
            videos = UnifiedMediaService.get_video_by_category_and_archetype(
                category=category,
                archetype=self.archetype
            )
        
        # Берем нужное количество
        video_list = list(videos[:count])
        
        # Если не хватает видео, дополняем последним
        if len(video_list) < count and video_list:
            while len(video_list) < count:
                video_list.append(video_list[-1])
        
        return video_list[:count]

    @transaction.atomic
    def build(self) -> int:
        """Строит плейлист для дня тренировки"""
        from apps.workouts.models import DailyPlaylistItem
        
        # Чистим старые позиции
        DailyPlaylistItem.objects.filter(day=self.day).delete()

        order = 1
        total = 0
        
        # Обновленный алгоритм для R2 структуры
        playlist_steps = [
            ("motivation", "motivation", 1),      # Открывающая мотивация
            ("exercises", "warmup", 1),          # Разминка
            ("exercises", "main", 3),            # Основные упражнения
            ("exercises", "endurance", 1),       # Выносливость или расслабление
            ("motivation", "motivation", 1),     # Закрывающая мотивация
        ]
        
        for category, exercise_type, count in playlist_steps:
            videos = self._pick_videos(category, exercise_type, count)
            role = "main" if exercise_type in ["main", "endurance"] else exercise_type
            
            for video in videos:
                DailyPlaylistItem.objects.create(
                    day=self.day, 
                    order=order, 
                    role=role, 
                    video=video,  # ОБНОВЛЕНО: используем video вместо media
                    duration_seconds=video.duration if hasattr(video, 'duration') else None,
                    overlay={}
                )
                order += 1
                total += 1
                
        return total

    def get_playlist_summary(self) -> dict:
        """Возвращает сводку по плейлисту"""
        from apps.workouts.models import DailyPlaylistItem
        
        items = DailyPlaylistItem.objects.filter(day=self.day).select_related('video')
        
        summary = {
            'total_items': items.count(),
            'by_role': {},
            'by_category': {},
            'total_duration': 0
        }
        
        for item in items:
            role = item.role
            if role not in summary['by_role']:
                summary['by_role'][role] = 0
            summary['by_role'][role] += 1
            
            # Статистика по категориям R2Video
            if item.video:
                category = item.video.category
                if category not in summary['by_category']:
                    summary['by_category'][category] = 0
                summary['by_category'][category] += 1
            
            if item.duration_seconds:
                summary['total_duration'] += item.duration_seconds
        
        return summary
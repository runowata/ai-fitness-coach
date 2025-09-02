from typing import List
from django.db import transaction
from apps.content.models import MediaAsset
from apps.workouts.models import DailyWorkout, DailyPlaylistItem

# Минимальный шаблон «идеального плейлиста»
# Подстройте порядок и роли под ваш документ:
IDEAL_TEMPLATE = [
    ("intro", 1),
    ("warmup", 1),
    ("main_block", 4),   # 4 основных клипа
    ("transition", 1),
    ("cooldown", 1),
    ("motivation", 1),
]

class R2PlaylistBuilder:
    """
    Строит плейлист дня из MediaAsset без использования AI
    """
    def __init__(self, day: DailyWorkout, archetype: str | None = None):
        self.day = day
        self.archetype = archetype or ""

    def _pick_assets(self, category: str, count: int) -> List[MediaAsset]:
        """Выбирает медиа-ассеты для категории"""
        qs = MediaAsset.objects.filter(is_active=True, category=category)
        
        # Если у вас есть аватары/голос тренера под archetype — можно фильтровать тут:
        if self.archetype:
            # Сначала пробуем найти для конкретного архетипа
            archetype_qs = qs.filter(archetype=self.archetype)
            if archetype_qs.exists():
                qs = archetype_qs
            else:
                # Fallback на универсальные (пустой archetype)
                qs = qs.filter(archetype="")
        
        items = list(qs.order_by("id")[:count])
        
        if len(items) < count:
            # Если не хватает — дублируем последние (или меняем стратегию)
            while len(items) < count and items:
                items.append(items[-1])
        
        return items[:count]

    @transaction.atomic
    def build(self) -> int:
        """Строит плейлист для дня тренировки"""
        # Чистим старые позиции
        DailyPlaylistItem.objects.filter(day=self.day).delete()

        order = 1
        total = 0
        
        for category, cnt in IDEAL_TEMPLATE:
            assets = self._pick_assets(category, cnt)
            role = "main" if category == "main_block" else category
            
            for media in assets:
                DailyPlaylistItem.objects.create(
                    day=self.day, 
                    order=order, 
                    role=role, 
                    media=media,
                    duration_seconds=None,  # Можно вычислить из медиа
                    overlay={}
                )
                order += 1
                total += 1
                
        return total

    def get_playlist_summary(self) -> dict:
        """Возвращает сводку по плейлисту"""
        items = DailyPlaylistItem.objects.filter(day=self.day).select_related('media')
        
        summary = {
            'total_items': items.count(),
            'by_role': {},
            'total_duration': 0
        }
        
        for item in items:
            role = item.role
            if role not in summary['by_role']:
                summary['by_role'][role] = 0
            summary['by_role'][role] += 1
            
            if item.duration_seconds:
                summary['total_duration'] += item.duration_seconds
        
        return summary
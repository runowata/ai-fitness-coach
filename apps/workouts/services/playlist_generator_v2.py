"""
Playlist Generator V2 - R2-driven video playlist generation
Generates 16-video playlists for 21-day workout program
"""
import random
from typing import List, Dict, Optional
from django.db import models
from apps.workouts.models import R2Video, DailyWorkout, DailyPlaylistItem


class PlaylistGeneratorV2:
    """
    Generates daily workout playlists with 16 videos per day.
    Ensures no exercise repetition across 21 days.
    """
    
    # Playlist structure: (position, video_type, category, count)
    PLAYLIST_STRUCTURE = [
        (1, 'opening', 'motivation', 1),           # Вступление
        (2, 'warmup', 'exercises', 2),             # Разминка x2
        (4, 'warmup_motivation', 'motivation', 1),  # Мотивация после разминки
        (5, 'main', 'exercises', 5),               # Основные x5
        (10, 'main_motivation', 'motivation', 1),   # Мотивация после основных
        (11, 'endurance', 'exercises', 2),         # Выносливость x2
        (13, 'endurance_motivation', 'motivation', 1), # Мотивация
        (14, 'cooldown', 'exercises', 2),          # Расслабление x2
        (16, 'closing', 'motivation', 1),          # Напутствие
    ]
    
    def __init__(self, user, archetype: str):
        """
        Initialize generator for specific user and archetype
        
        Args:
            user: User object
            archetype: 'mentor', 'professional', or 'peer'
        """
        self.user = user
        self.archetype = self._normalize_archetype(archetype)
        self.used_exercises = self._get_used_exercises()
        
    def _normalize_archetype(self, archetype: str) -> str:
        """Normalize archetype names to match video naming"""
        mapping = {
            'mentor': 'intellectual',  # в видео используется intellectual
            'professional': 'sergeant',  # в видео используется sergeant
            'peer': 'bro',  # в видео используется bro
        }
        return mapping.get(archetype, 'bro')
    
    def _get_used_exercises(self) -> set:
        """Get list of exercises already used by this user"""
        # Получаем все использованные упражнения из предыдущих плейлистов
        used = DailyPlaylistItem.objects.filter(
            workout__plan__user=self.user,
            video_type__in=['warmup', 'main', 'endurance', 'cooldown']
        ).values_list('video_code', flat=True)
        return set(used)
    
    def generate_playlist_for_day(self, day_number: int, workout: DailyWorkout) -> List[DailyPlaylistItem]:
        """
        Generate 16-video playlist for specific day
        
        Args:
            day_number: Day number (1-21)
            workout: DailyWorkout object to attach playlist to
            
        Returns:
            List of created DailyPlaylistItem objects
        """
        playlist_items = []
        position = 0
        
        # 1. Opening video
        opening = self._get_motivation_video('opening', day_number)
        if opening:
            playlist_items.append(self._create_playlist_item(
                workout, position, opening, 'opening'
            ))
            position += 1
        
        # 2-3. Warmup exercises (2)
        warmups = self._get_exercise_videos('warmup', 2)
        for video in warmups:
            playlist_items.append(self._create_playlist_item(
                workout, position, video, 'warmup'
            ))
            position += 1
        
        # 4. Warmup motivation
        warmup_mot = self._get_motivation_video('warmup', day_number)
        if warmup_mot:
            playlist_items.append(self._create_playlist_item(
                workout, position, warmup_mot, 'warmup_motivation'
            ))
            position += 1
        
        # 5-9. Main exercises (5)
        mains = self._get_exercise_videos('main', 5)
        for video in mains:
            playlist_items.append(self._create_playlist_item(
                workout, position, video, 'main'
            ))
            position += 1
        
        # 10. Main motivation
        main_mot = self._get_motivation_video('middle', day_number)
        if main_mot:
            playlist_items.append(self._create_playlist_item(
                workout, position, main_mot, 'main_motivation'
            ))
            position += 1
        
        # 11-12. Endurance exercises (2)
        endurances = self._get_exercise_videos('endurance', 2)
        for video in endurances:
            playlist_items.append(self._create_playlist_item(
                workout, position, video, 'endurance'
            ))
            position += 1
        
        # 13. Endurance motivation
        endurance_mot = self._get_motivation_video('endurance', day_number)
        if endurance_mot:
            playlist_items.append(self._create_playlist_item(
                workout, position, endurance_mot, 'endurance_motivation'
            ))
            position += 1
        
        # 14-15. Cooldown exercises (2)
        cooldowns = self._get_exercise_videos('relaxation', 2)
        for video in cooldowns:
            playlist_items.append(self._create_playlist_item(
                workout, position, video, 'cooldown'
            ))
            position += 1
        
        # 16. Closing video
        closing = self._get_motivation_video('closing', day_number)
        if closing:
            playlist_items.append(self._create_playlist_item(
                workout, position, closing, 'closing'
            ))
            position += 1
        
        return playlist_items
    
    def _get_exercise_videos(self, exercise_type: str, count: int) -> List[R2Video]:
        """
        Get unused exercise videos of specific type
        
        Args:
            exercise_type: 'warmup', 'main', 'endurance', 'relaxation'
            count: Number of videos needed
            
        Returns:
            List of R2Video objects
        """
        # Получаем все доступные видео этого типа
        available = R2Video.objects.filter(
            category='exercises',
            code__icontains=exercise_type
        ).exclude(
            code__in=self.used_exercises
        )
        
        # Если недостаточно неиспользованных, берем любые
        if available.count() < count:
            available = R2Video.objects.filter(
                category='exercises',
                code__icontains=exercise_type
            )
        
        # Выбираем случайные
        videos = list(available.order_by('?')[:count])
        
        # Добавляем в использованные
        for video in videos:
            self.used_exercises.add(video.code)
        
        return videos
    
    def _get_motivation_video(self, video_type: str, day_number: int) -> Optional[R2Video]:
        """
        Get motivation video for specific type and day
        
        Args:
            video_type: 'opening', 'warmup', 'middle', 'endurance', 'closing'
            day_number: Day number (1-21)
            
        Returns:
            R2Video object or None
        """
        # Ищем видео с нужным типом и архетипом
        pattern = f"{video_type}_{self.archetype}_day{day_number:02d}"
        
        video = R2Video.objects.filter(
            category='motivation',
            code__icontains=pattern
        ).first()
        
        # Если нет для конкретного дня, берем любое этого типа
        if not video:
            video = R2Video.objects.filter(
                category='motivation',
                code__icontains=f"{video_type}_{self.archetype}"
            ).order_by('?').first()
        
        # Если все еще нет, берем любое мотивационное для архетипа
        if not video:
            video = R2Video.objects.filter(
                category='motivation',
                code__icontains=self.archetype
            ).order_by('?').first()
        
        return video
    
    def _create_playlist_item(self, workout: DailyWorkout, order: int, 
                             video: R2Video, video_type: str) -> DailyPlaylistItem:
        """
        Create and save playlist item
        
        Args:
            workout: DailyWorkout to attach to
            order: Position in playlist
            video: R2Video object
            video_type: Type of video for tracking
            
        Returns:
            Created DailyPlaylistItem
        """
        return DailyPlaylistItem.objects.create(
            workout=workout,
            order=order,
            video_code=video.code,
            video_type=video_type,
            duration_seconds=30,  # Default duration, можно обновить позже
            metadata={
                'category': video.category,
                'archetype': self.archetype,
                'original_archetype': video.archetype
            }
        )
    
    def generate_full_program(self, plan) -> Dict:
        """
        Generate complete 21-day program with playlists
        
        Args:
            plan: WorkoutPlan object
            
        Returns:
            Dictionary with statistics
        """
        stats = {
            'days_created': 0,
            'videos_total': 0,
            'unique_exercises': len(self.used_exercises),
            'errors': []
        }
        
        # Создаем плейлисты для каждого дня
        for day in range(1, 22):
            try:
                # Получаем или создаем DailyWorkout
                workout, created = DailyWorkout.objects.get_or_create(
                    plan=plan,
                    day_number=day,
                    week_number=(day - 1) // 7 + 1,
                    defaults={
                        'name': f'День {day}',
                        'exercises': [],
                        'is_rest_day': False
                    }
                )
                
                # Удаляем старые плейлисты если есть
                DailyPlaylistItem.objects.filter(workout=workout).delete()
                
                # Генерируем новый плейлист
                playlist = self.generate_playlist_for_day(day, workout)
                
                stats['days_created'] += 1
                stats['videos_total'] += len(playlist)
                
            except Exception as e:
                stats['errors'].append(f"Day {day}: {str(e)}")
        
        stats['unique_exercises'] = len(self.used_exercises)
        return stats
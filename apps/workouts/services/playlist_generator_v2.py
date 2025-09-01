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
        """Convert NEW archetype names to OLD R2 file names"""
        # R2 files use OLD names: bro, sergeant, intellectual
        # Convert NEW names to match R2 files
        if archetype in ['peer', 'friend']:
            return 'bro'  # peer → bro (R2 files)
        elif archetype in ['professional', 'coach']:
            return 'sergeant'  # professional → sergeant (R2 files)
        elif archetype in ['mentor', 'wise']:
            return 'intellectual'  # mentor → intellectual (R2 files)
        # Handle legacy cases
        elif archetype in ['bro', 'sergeant', 'intellectual']:
            return archetype  # Already correct R2 names
        else:
            return 'intellectual'  # Default fallback to match R2
    
    def _get_used_exercises(self) -> set:
        """Get list of exercises already used by this user"""
        # Получаем все использованные упражнения из предыдущих плейлистов
        used = DailyPlaylistItem.objects.filter(
            day__plan__user=self.user,
            role__in=['warmup', 'main', 'endurance', 'cooldown']
        ).values_list('video__code', flat=True)
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
        
        # 1. Opening video (use 'intro' in R2)
        opening = self._get_motivation_video('intro', day_number)
        if opening:
            playlist_items.append(self._create_playlist_item(
                workout, position, opening, 'motivation'
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
        warmup_mot = self._get_motivation_video('warmup_motivation', day_number)
        if warmup_mot:
            playlist_items.append(self._create_playlist_item(
                workout, position, warmup_mot, 'motivation'
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
        main_mot = self._get_motivation_video('main_motivation', day_number)
        if main_mot:
            playlist_items.append(self._create_playlist_item(
                workout, position, main_mot, 'motivation'
            ))
            position += 1
        
        # 11-12. Endurance exercises (2)
        endurances = self._get_exercise_videos('endurance', 2)
        for video in endurances:
            playlist_items.append(self._create_playlist_item(
                workout, position, video, 'main'
            ))
            position += 1
        
        # 13. Endurance motivation (use main_motivation)
        endurance_mot = self._get_motivation_video('main_motivation', day_number)
        if endurance_mot:
            playlist_items.append(self._create_playlist_item(
                workout, position, endurance_mot, 'motivation'
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
                workout, position, closing, 'motivation'
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
            video_type: 'intro', 'warmup_motivation', 'main_motivation', 'closing'
            day_number: Day number (1-21)
            
        Returns:
            R2Video object or None
        """
        # R2 motivation videos have patterns like: intro_bro_day01, warmup_motivation_bro_day01
        if video_type == 'warmup_motivation' or video_type == 'main_motivation':
            pattern = f"{video_type}_{self.archetype}_day{day_number:02d}"
        else:  # intro, closing
            pattern = f"{video_type}_{self.archetype}_day{day_number:02d}"
        
        video = R2Video.objects.filter(
            category='motivation',
            code=pattern
        ).first()
        
        # If not found for specific day, try without day
        if not video:
            if video_type == 'warmup_motivation' or video_type == 'main_motivation':
                video = R2Video.objects.filter(
                    category='motivation',
                    code__startswith=f"{video_type}_{self.archetype}_"
                ).order_by('?').first()
            else:
                video = R2Video.objects.filter(
                    category='motivation',
                    code__startswith=f"{video_type}_{self.archetype}_"
                ).order_by('?').first()
        
        # Final fallback: any motivation video for this archetype
        if not video:
            video = R2Video.objects.filter(
                category='motivation',
                code__icontains=self.archetype
            ).order_by('?').first()
        
        return video
    
    def _create_playlist_item(self, workout: DailyWorkout, order: int, 
                             video: R2Video, role: str) -> DailyPlaylistItem:
        """
        Create and save playlist item
        
        Args:
            workout: DailyWorkout to attach to
            order: Position in playlist
            video: R2Video object
            role: Type of video for role field
            
        Returns:
            Created DailyPlaylistItem
        """
        return DailyPlaylistItem.objects.create(
            day=workout,
            order=order,
            video=video,  # ForeignKey to R2Video
            role=role,
            duration_seconds=30,  # Default duration, можно обновить позже
            overlay={
                'category': video.category,
                'archetype': self.archetype,
                'original_archetype': getattr(video, 'archetype', '')
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
                DailyPlaylistItem.objects.filter(day=workout).delete()
                
                # Генерируем новый плейлист
                playlist = self.generate_playlist_for_day(day, workout)
                
                stats['days_created'] += 1
                stats['videos_total'] += len(playlist)
                
            except Exception as e:
                stats['errors'].append(f"Day {day}: {str(e)}")
        
        stats['unique_exercises'] = len(self.used_exercises)
        return stats
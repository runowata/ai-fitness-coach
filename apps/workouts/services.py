import random
from typing import List, Dict
from django.db.models import Q
from .models import Exercise, VideoClip, DailyWorkout


class VideoPlaylistBuilder:
    """Service to build video playlist for a workout"""
    
    def build_workout_playlist(self, workout: DailyWorkout, user_archetype: str) -> List[Dict]:
        """
        Build complete video playlist for a workout
        Returns list of video items in order of playback
        """
        playlist = []
        
        # If it's a rest day, return motivational video only
        if workout.is_rest_day:
            rest_day_video = self._get_rest_day_video(workout.week_number, user_archetype)
            if rest_day_video:
                playlist.append(rest_day_video)
            return playlist
        
        # Add intro video at the beginning (prefer non-placeholder)
        intro_video = VideoClip.objects.filter(
            exercise=None,
            type='intro',
            archetype=user_archetype,
            is_active=True
        ).order_by('?').first()
        
        if intro_video:
            playlist.append({
                'type': 'intro',
                'url': intro_video.url,
                'duration': intro_video.duration_seconds,
                'title': 'Добро пожаловать на тренировку!'
            })
        
        # Build playlist for each exercise
        for exercise_data in workout.exercises:
            exercise_slug = exercise_data.get('exercise_slug')
            exercise_playlist = self._build_exercise_playlist(
                exercise_slug, 
                user_archetype,
                exercise_data
            )
            playlist.extend(exercise_playlist)
        
        # Add weekly motivational video at the end
        if workout.day_number == 7:  # Last day of week
            weekly_video = self._get_weekly_motivation_video(workout.week_number, user_archetype)
            if weekly_video:
                playlist.append(weekly_video)
        
        return playlist
    
    def _build_exercise_playlist(self, exercise_slug: str, archetype: str, exercise_data: Dict) -> List[Dict]:
        """Build video sequence for a single exercise"""
        playlist = []
        
        # Handle both slug formats: 'ex005' (from AI) and 'push-ups' (human readable)
        slug_or_code = exercise_slug
        
        # If this looks like an exercise code (ex###), normalize to uppercase and search by PK
        if slug_or_code.lower().startswith("ex") and len(slug_or_code) == 5:
            exercise_lookup = {"pk": slug_or_code.upper()}
        else:
            exercise_lookup = {"slug": slug_or_code}
        
        try:
            exercise = Exercise.objects.get(**exercise_lookup)
        except Exercise.DoesNotExist:
            return playlist
        
        # 1. Technique video (mod1)
        technique_video = VideoClip.objects.filter(
            exercise=exercise,
            type='technique',
            model_name='mod1',
            is_active=True
        ).first()
        
        if technique_video:
            playlist.append({
                'type': 'technique',
                'url': technique_video.url,
                'duration': technique_video.duration_seconds,
                'title': f'{exercise.name} - Техника выполнения',
                'exercise_name': exercise.name,
                'model': 'mod1'
            })
        
        # 2. Support video (motivation based on archetype) - only real videos
        support_video = VideoClip.objects.filter(
            exercise=None,  # Trainer videos have no specific exercise
            type='support',
            archetype=archetype,
            is_active=True
        ).order_by('?').first()
        
        if support_video:
            playlist.append({
                'type': 'support',
                'url': support_video.url,
                'duration': support_video.duration_seconds,
                'title': f'Мотивация - {exercise.name}',
                'exercise_name': exercise.name,
                'sets': exercise_data.get('sets'),
                'reps': exercise_data.get('reps'),
                'rest': exercise_data.get('rest_seconds')
            })
        
        # 3. Maybe add another support video (30% chance)
        if random.random() < 0.3:
            extra_support = VideoClip.objects.filter(
                exercise=None,
                type='support',
                archetype=archetype, 
                is_active=True,
                  # Only real videos
            ).exclude(id=support_video.id if support_video else 0).order_by('?').first()
            
            if extra_support:
                playlist.append({
                    'type': 'support',
                    'url': extra_support.url,
                    'duration': extra_support.duration_seconds,
                    'title': 'Дополнительная мотивация',
                    'exercise_name': exercise.name
                })
        
        # 4. Common mistakes video (optional, show occasionally)
        if random.random() < 0.3:  # 30% chance to show mistakes video
            mistake_video = VideoClip.objects.filter(
                exercise=exercise,
                type='mistake',
                model_name='mod1',
                is_active=True,
                  # Only real videos
            ).first()
            
            if mistake_video:
                playlist.append({
                    'type': 'mistake',
                    'url': mistake_video.url,
                    'duration': mistake_video.duration_seconds,
                    'title': f'{exercise.name} - Частые ошибки',
                    'exercise_name': exercise.name,
                    'model': 'mod1'
                })
        
        return playlist
    
    def _get_rest_day_video(self, week_number: int, archetype: str) -> Dict:
        """Get motivational video for rest day - only real videos"""
        video = VideoClip.objects.filter(
            type='support',
            archetype=archetype,
            is_active=True
        ).order_by('?').first()
        
        if video:
            return {
                'type': 'rest_day',
                'url': video.url,
                'duration': video.duration_seconds,
                'title': 'День отдыха - Восстановление и мотивация'
            }
        return None
    
    def _get_weekly_motivation_video(self, week_number: int, archetype: str) -> Dict:
        """Get weekly motivational video - only real videos"""
        # Use outro video for weekly completion
        video = VideoClip.objects.filter(
            type='outro',
            archetype=archetype,
            is_active=True
        ).order_by('?').first()
        
        if video:
            return {
                'type': 'weekly_motivation',
                'url': video.url,
                'duration': video.duration_seconds,
                'title': f'Поздравляем с завершением недели {week_number}!'
            }
        return None
    
    def get_substitution_options(self, exercise_slug: str, user_equipment: List[str]) -> List[Exercise]:
        """Get possible exercise substitutions based on user's equipment"""
        try:
            exercise = Exercise.objects.get(slug=exercise_slug)
            
            # Get alternatives that match user's equipment
            alternatives = exercise.alternatives.filter(
                is_active=True
            ).all()
            
            # Filter by equipment availability
            suitable_alternatives = []
            for alt in alternatives:
                required_equipment = set(alt.equipment_needed)
                user_equipment_set = set(user_equipment)
                
                # Check if user has all required equipment
                if required_equipment.issubset(user_equipment_set) or not required_equipment:
                    suitable_alternatives.append(alt)
            
            return suitable_alternatives
            
        except Exercise.DoesNotExist:
            return []
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
        
        try:
            exercise = Exercise.objects.get(slug=exercise_slug)
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
        
        # 2. Instruction video (based on archetype)
        # Randomly select between mod1, mod2, mod3 for variety
        model_choice = random.choice(['mod1', 'mod2', 'mod3'])
        instruction_video = VideoClip.objects.filter(
            exercise=exercise,
            type='instruction',
            archetype=archetype,
            model_name=model_choice,
            is_active=True
        ).first()
        
        if instruction_video:
            playlist.append({
                'type': 'instruction',
                'url': instruction_video.url,
                'duration': instruction_video.duration_seconds,
                'title': f'{exercise.name} - Инструктаж',
                'exercise_name': exercise.name,
                'model': model_choice,
                'sets': exercise_data.get('sets'),
                'reps': exercise_data.get('reps'),
                'rest': exercise_data.get('rest_seconds')
            })
        
        # 3. Reminder videos (2-3 random reminders)
        reminders = VideoClip.objects.filter(
            exercise=exercise,
            type='reminder',
            archetype=archetype,
            is_active=True
        ).order_by('?')[:random.randint(2, 3)]
        
        for reminder in reminders:
            playlist.append({
                'type': 'reminder',
                'url': reminder.url,
                'duration': reminder.duration_seconds,
                'title': reminder.reminder_text or f'{exercise.name} - Напоминание',
                'exercise_name': exercise.name
            })
        
        # 4. Common mistakes video (optional, show occasionally)
        if random.random() < 0.3:  # 30% chance to show mistakes video
            mistake_video = VideoClip.objects.filter(
                exercise=exercise,
                type='mistake',
                model_name='mod1',
                is_active=True
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
        """Get motivational video for rest day"""
        video = VideoClip.objects.filter(
            type='weekly',
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
        """Get weekly motivational video"""
        video = VideoClip.objects.filter(
            Q(type='weekly') & Q(reminder_text__icontains=f'week{week_number}'),
            archetype=archetype,
            is_active=True
        ).first()
        
        # Fallback to any weekly video
        if not video:
            video = VideoClip.objects.filter(
                type='weekly',
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
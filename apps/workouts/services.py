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
        
        # 1. Add daily intro video at the beginning
        intro_video = self._get_intro_video(workout.day_number, user_archetype)
        if intro_video:
            playlist.append(intro_video)
        
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
        if workout.day_number % 7 == 0:  # Last day of week
            weekly_video = self._get_weekly_motivation_video(workout.week_number, user_archetype)
            if weekly_video:
                playlist.append(weekly_video)
        
        # Add progress video every 2 weeks (days 14, 28, 42, etc.)
        if workout.day_number % 14 == 0:
            progress_video = self._get_progress_video(workout.week_number, user_archetype)
            if progress_video:
                playlist.append(progress_video)
        
        # Add final video if this is the last day of the plan
        if self._is_final_day(workout):
            final_video = self._get_final_video(user_archetype)
            if final_video:
                playlist.append(final_video)
        
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
    
    def _get_intro_video(self, day_number: int, archetype: str) -> Dict:
        """Get daily intro video"""
        video = VideoClip.objects.filter(
            type='intro',
            archetype=archetype,
            reminder_text=f'day_{day_number}',
            is_active=True
        ).first()
        
        if video:
            return {
                'type': 'daily_intro',
                'url': video.url,
                'duration': video.duration_seconds,
                'title': f'Добро пожаловать в день {day_number}!'
            }
        return None
    
    def _get_progress_video(self, week_number: int, archetype: str) -> Dict:
        """Get bi-weekly progress video"""
        # Calculate which progress milestone (1, 2, or 3)
        progress_num = min((week_number // 2) + 1, 3)
        
        video = VideoClip.objects.filter(
            type='progress',
            archetype=archetype,
            reminder_text=f'progress_{progress_num}',
            is_active=True
        ).first()
        
        if video:
            return {
                'type': 'progress_milestone',
                'url': video.url,
                'duration': video.duration_seconds,
                'title': f'Прогресс - Этап {progress_num}'
            }
        return None
    
    def _get_final_video(self, archetype: str) -> Dict:
        """Get final completion video"""
        video = VideoClip.objects.filter(
            type='final',
            archetype=archetype,
            reminder_text='completion',
            is_active=True
        ).first()
        
        if video:
            return {
                'type': 'program_completion',
                'url': video.url,
                'duration': video.duration_seconds,
                'title': 'Поздравляем с завершением программы!'
            }
        return None
    
    def _is_final_day(self, workout: DailyWorkout) -> bool:
        """Check if this is the last day of the workout plan"""
        plan = workout.plan
        total_days = plan.duration_weeks * 7
        return workout.day_number == total_days
    
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
import random
from typing import List, Dict
from django.db.models import Q
from django.conf import settings
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
    
    def get_final_video(self, workout: DailyWorkout, user_archetype: str) -> Dict:
        """
        Get 'see you tomorrow' final video after workout completion
        Returns video item for end of workout
        """
        # Get next workout to determine message
        next_workout = DailyWorkout.objects.filter(
            plan=workout.plan,
            week_number=workout.week_number,
            day_number=workout.day_number + 1
        ).first()
        
        # If no next workout in same week, check next week
        if not next_workout:
            next_workout = DailyWorkout.objects.filter(
                plan=workout.plan,
                week_number=workout.week_number + 1,
                day_number=1
            ).first()
        
        # Try to get archetype-specific final video
        final_video = VideoClip.objects.filter(
            type='final',
            archetype=user_archetype,
            is_active=True
        ).order_by('?').first()
        
        # Fallback to any final video
        if not final_video:
            final_video = VideoClip.objects.filter(
                type='final',
                is_active=True
            ).order_by('?').first()
        
        if final_video:
            # Customize message based on what's next
            if next_workout:
                if next_workout.is_rest_day:
                    title = "Отличная работа! Завтра у вас день отдыха."
                else:
                    title = f"Отличная работа! Увидимся завтра для тренировки: {next_workout.name}"
            else:
                title = "Поздравляем! Вы завершили всю программу!"
            
            return {
                'type': 'final',
                'url': final_video.url,
                'duration': final_video.duration_seconds,
                'title': title,
                'archetype': user_archetype,
                'next_workout': next_workout.name if next_workout else None,
                'is_program_complete': next_workout is None
            }
        
        # Fallback message if no video available
        return {
            'type': 'final',
            'url': None,
            'duration': 0,
            'title': "Отличная работа! Увидимся завтра!" if next_workout else "Поздравляем с завершением программы!",
            'archetype': user_archetype,
            'next_workout': next_workout.name if next_workout else None,
            'is_program_complete': next_workout is None
        }
    
    def get_cycle_completion_video(self, plan, user_archetype: str, completion_stats: Dict) -> Dict:
        """
        Get special congratulations video for completing a full 6-week cycle
        """
        # Try to get archetype-specific cycle completion video
        cycle_video = VideoClip.objects.filter(
            type='final',
            archetype=user_archetype,
            reminder_text__icontains='cycle_complete',
            is_active=True
        ).first()
        
        # Fallback to general cycle completion video
        if not cycle_video:
            cycle_video = VideoClip.objects.filter(
                type='final',
                reminder_text__icontains='cycle_complete',
                is_active=True
            ).first()
        
        # Final fallback to any congratulatory video
        if not cycle_video:
            cycle_video = VideoClip.objects.filter(
                type='final',
                archetype=user_archetype,
                is_active=True
            ).order_by('?').first()
        
        # Archetype-specific congratulations
        congratulations = {
            'bro': {
                'title': '🔥 Братан, ты сделал это!',
                'message': f'6 недель позади! {completion_stats["total_completed"]} тренировок завершено. Ты показал что такое настоящая сила воли!',
                'celebration': 'Время праздновать твой успех!'
            },
            'sergeant': {
                'title': '🎖️ Миссия выполнена!',
                'message': f'6 недель интенсивной подготовки завершены! {completion_stats["total_completed"]} тренировок в активе. Дисциплина и упорство - твои главные достижения!',
                'celebration': 'Ты заслужил это признание, боец!'
            },
            'intellectual': {
                'title': '📊 Цикл успешно завершен!',
                'message': f'Статистика впечатляет: {completion_stats["total_completed"]} тренировок, {completion_stats["overall_completion_rate"]:.1f}% завершение. Данные показывают отличную готовность к следующему этапу!',
                'celebration': 'Методичный подход принес отличные результаты!'
            }
        }
        
        archetype_data = congratulations.get(user_archetype, congratulations['bro'])
        
        if cycle_video:
            return {
                'type': 'cycle_completion',
                'url': cycle_video.url,
                'duration': cycle_video.duration_seconds,
                'title': archetype_data['title'],
                'message': archetype_data['message'],
                'celebration': archetype_data['celebration'],
                'archetype': user_archetype,
                'completion_stats': completion_stats,
                'plan_name': plan.name,
                'weeks_completed': 6
            }
        
        # Text-only fallback if no video
        return {
            'type': 'cycle_completion',
            'url': None,
            'duration': 0,
            'title': archetype_data['title'],
            'message': archetype_data['message'],
            'celebration': archetype_data['celebration'],
            'archetype': user_archetype,
            'completion_stats': completion_stats,
            'plan_name': plan.name,
            'weeks_completed': 6
        }
    
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
        else:
            # Fallback to static placeholder video
            fallback_url = f"{settings.STATIC_URL}videos/exercises/{exercise_slug}_technique_{archetype}_1.mp4"
            playlist.append({
                'type': 'technique',
                'url': fallback_url,
                'duration': 60,  # Default duration
                'title': f'{exercise.name} - Техника выполнения',
                'exercise_name': exercise.name,
                'model': 'fallback'
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
        else:
            # Fallback to static placeholder video
            fallback_url = f"{settings.STATIC_URL}videos/placeholder.mp4"
            playlist.append({
                'type': 'instruction',
                'url': fallback_url,
                'duration': 45,  # Default duration
                'title': f'{exercise.name} - Инструктаж',
                'exercise_name': exercise.name,
                'model': 'fallback',
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
        
        # Fallback if no reminders found
        if not reminders:
            fallback_url = f"{settings.STATIC_URL}videos/placeholder.mp4"
            playlist.append({
                'type': 'reminder',
                'url': fallback_url,
                'duration': 30,
                'title': f'{exercise.name} - Напоминание',
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
        
        # Fallback to placeholder video
        fallback_url = f"{settings.STATIC_URL}videos/placeholder.mp4"
        return {
            'type': 'rest_day',
            'url': fallback_url,
            'duration': 120,
            'title': 'День отдыха - Восстановление и мотивация'
        }
    
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
        
        # Fallback to placeholder video
        fallback_url = f"{settings.STATIC_URL}videos/placeholder.mp4"
        return {
            'type': 'weekly_motivation',
            'url': fallback_url,
            'duration': 90,
            'title': f'Поздравляем с завершением недели {week_number}!'
        }
    
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
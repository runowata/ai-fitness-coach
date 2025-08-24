import hashlib
import logging
import random
import time
from typing import Dict, List, Optional


from apps.core.metrics import MetricNames, incr, timing
from apps.core.services.exercise_validation import ExerciseValidationService

from .constants import (
    ARCHETYPE_FALLBACK_ORDER,
    MID_WORKOUT_INSERTION_FREQUENCY,
    OPTIONAL_VIDEO_KINDS_PLAYLIST,
    REQUIRED_VIDEO_KINDS_PLAYLIST,
    VideoKind,
)
from .models import CSVExercise, DailyWorkout
from .video_storage import get_storage

logger = logging.getLogger(__name__)


class VideoPlaylistBuilder:
    """Service to build video playlist for a workout"""
    
    def __init__(self, archetype: str, locale: str = "ru", rng: Optional[random.Random] = None):
        self.archetype = archetype
        self.locale = locale
        self.rng = rng or random.Random()  # Use provided RNG or default
        self._candidates = {}  # Candidate cache: (exercise_id, kind, archetype) -> [VideoClip]
    
    def build_playlist(self, exercises) -> List[Dict]:
        """Build playlist from ExplainerVideo scripts for given exercises"""
        from apps.workouts.models import CSVExercise, ExplainerVideo
        
        videos = []
        for ex in exercises:
            # Get exercise object if we have ID string
            if isinstance(ex, str):
                exercise = CSVExercise.objects.filter(id=ex).first()
            else:
                exercise = ex
                
            if not exercise:
                continue
                
            # Get video script for this exercise/archetype/locale
            available_videos = list(ExplainerVideo.objects.filter(
                exercise=exercise,
                archetype=self.archetype,
                locale=self.locale
            ).values_list('id', flat=True))
            
            video = None
            if available_videos:
                # Use RNG instead of order_by('?') for better distribution
                random_id = self.rng.choice(available_videos)
                video = ExplainerVideo.objects.get(id=random_id)
            
            if video:
                videos.append({
                    "exercise_id": exercise.id,
                    "script": video.script
                })
        
        return videos
    
    def build_workout_playlist(self, workout: DailyWorkout, user_archetype: str) -> List[Dict]:
        """
        Build complete video playlist for a workout using storage adapters
        Returns list of video items in order of playback
        """
        start_time = time.monotonic()
        
        # Create deterministic seed based on workout data for reproducible playlists
        self._seed_rng_for_workout(workout, user_archetype)
        
        playlist = []
        
        # If it's a rest day, return motivational video only
        if workout.is_rest_day:
            rest_day_video = self._get_rest_day_video(workout.week_number, user_archetype)
            if rest_day_video:
                playlist.append(rest_day_video)
            return playlist
        
        # Prefetch video candidates for all exercises in this workout
        exercise_ids = [ex.get('exercise_slug') for ex in workout.exercises if ex.get('exercise_slug')]
        if exercise_ids:
            self._prefetch_candidates(exercise_ids, user_archetype)
        
        # Add contextual intro video at the beginning (if not rest day)
        intro_video = self._get_contextual_intro_video(workout, user_archetype)
        
        if intro_video:
            playlist.append({
                'type': 'intro',
                'url': intro_video['url'],
                'duration': intro_video['duration'],
                'title': 'Добро пожаловать на тренировку!',
                'clip_id': intro_video['clip_id'],
                'provider': intro_video['provider'],
                'kind': intro_video.get('kind', 'intro')
            })
            logger.info(f"Added intro video: clip_id={intro_video['clip_id']}")
        
        # Process each exercise in the workout with mid-workout motivation
        for i, exercise_data in enumerate(workout.exercises):
            exercise_slug = exercise_data.get('exercise_slug')
            exercise_playlist = self._build_exercise_playlist(
                exercise_slug, 
                user_archetype,
                exercise_data
            )
            playlist.extend(exercise_playlist)
            
            # Add mid-workout motivation every 3rd exercise
            if (i + 1) % MID_WORKOUT_INSERTION_FREQUENCY == 0 and (i + 1) < len(workout.exercises):
                mid_workout_video = self._get_mid_workout_motivation(workout, user_archetype)
                if mid_workout_video:
                    playlist.append(mid_workout_video)
        
        # Add weekly theme-based video at the end
        if workout.day_number == 7:  # Last day of week
            weekly_video = self._get_weekly_theme_video(workout.week_number, user_archetype)
            if weekly_video:
                playlist.append(weekly_video)
        
        # Add contextual outro video
        outro_video = self._get_contextual_outro_video(workout, user_archetype)
        if outro_video:
            playlist.append(outro_video)
        
        # Track metrics
        build_time_ms = (time.monotonic() - start_time) * 1000
        timing(MetricNames.VIDEO_PLAYLIST_BUILD_TIME, build_time_ms)
        
        # Count video providers used
        for item in playlist:
            if 'provider' in item:
                if item['provider'] == 'r2':
                    incr(MetricNames.VIDEO_PROVIDER_R2)
                elif item['provider'] == 'stream':
                    incr(MetricNames.VIDEO_PROVIDER_STREAM)
        
        logger.info(f"Built playlist with {len(playlist)} items in {build_time_ms:.2f}ms")
        
        return playlist
    
    def _seed_rng_for_workout(self, workout: DailyWorkout, archetype: str):
        """Create reproducible seed for workout playlist generation"""
        # Combine workout identifiers to create consistent seed
        seed_data = f"workout_{workout.id}_{workout.week_number}_{workout.day_number}_{archetype}"
        seed = int(hashlib.md5(seed_data.encode()).hexdigest()[:8], 16)
        self.rng.seed(seed)
        logger.debug(f"Seeded RNG with {seed} for workout {workout.id}")
    
    def _prefetch_candidates(self, exercise_ids: List[str], archetype: str):
        """
        Prefetch video clip candidates for all exercises to avoid N+1 queries
        
        Args:
            exercise_ids: List of exercise slugs/IDs for the workout
            archetype: Primary archetype for this workout
        """
        from django.conf import settings

        # Clear existing cache
        self._candidates.clear()
        
        # Get all relevant video kinds
        all_kinds = REQUIRED_VIDEO_KINDS_PLAYLIST + OPTIONAL_VIDEO_KINDS_PLAYLIST
        
        # Get all archetypes in fallback order
        archetype_order = ARCHETYPE_FALLBACK_ORDER.get(archetype, [archetype])
        
        # Build query for all possible combinations
        query = ExerciseValidationService.get_clips_with_video().filter(
            exercise__id__in=exercise_ids,
            r2_kind__in=all_kinds,
            r2_archetype__in=archetype_order
        ).select_related('exercise').order_by('id')
        
        # Execute single query and group results
        clips = list(query)
        logger.debug(f"Prefetched {len(clips)} video clips for {len(exercise_ids)} exercises")
        
        # Group by (exercise_slug, kind, archetype)
        for clip in clips:
            exercise_slug = clip.exercise.id if clip.exercise else None
            if exercise_slug:
                key = (exercise_slug, clip.r2_kind, clip.r2_archetype)
                
                if key not in self._candidates:
                    self._candidates[key] = []
                
                # Limit candidates per key to avoid memory bloat
                if len(self._candidates[key]) < settings.PLAYLIST_FALLBACK_MAX_CANDIDATES:
                    self._candidates[key].append(clip)
        
        # Track prefetch metrics
        incr(MetricNames.VIDEO_PLAYLIST_CANDIDATES, len(clips))
    
    def _get_video_with_storage(self, exercise=None, r2_kind=None, archetype=None, exclude_id=None):
        """
        Get video clip with storage availability check using deterministic selection
        Uses multi-level fallback strategy for better reliability
        """

        # For global videos (intro, closing, weekly) use legacy logic
        if exercise is None:
            return self._get_global_video_legacy(r2_kind, archetype, exclude_id)
        
        # For exercise-specific videos, use prefetch cache and fallback levels
        exercise_slug = exercise.id if hasattr(exercise, 'id') else str(exercise)
        
        # Determine if this is a required or optional video kind
        is_required = r2_kind in REQUIRED_VIDEO_KINDS_PLAYLIST
        
        # Level 1: Exact match (exercise + kind + archetype)
        candidates = self._get_candidates_for_level(exercise_slug, r2_kind, archetype, level=1)
        selected_clip = self._choose_with_storage_retry(candidates, exclude_id)
        
        if selected_clip:
            logger.debug(f"Level 1: Selected clip {selected_clip.id} for {exercise_slug}:{r2_kind}:{archetype}")
            return self._format_video_response(selected_clip, r2_kind)
        
        # Level 2: Same exercise + kind, different archetype (fallback order)
        archetype_fallbacks = ARCHETYPE_FALLBACK_ORDER.get(archetype, [archetype])[1:]  # Skip primary
        
        for fallback_archetype in archetype_fallbacks:
            candidates = self._get_candidates_for_level(exercise_slug, r2_kind, fallback_archetype, level=2)
            selected_clip = self._choose_with_storage_retry(candidates, exclude_id)
            
            if selected_clip:
                incr(MetricNames.VIDEO_PLAYLIST_FALLBACK_HIT, level=2, kind=r2_kind)
                logger.info(f"Level 2: Fallback to {fallback_archetype} for {exercise_slug}:{r2_kind}")
                return self._format_video_response(selected_clip, r2_kind)
        
        # Level 3: Only for optional videos - skip for required ones
        if not is_required:
            # Could add similar exercise lookup here, but for now just fail gracefully
            pass
        
        # No video found
        if is_required:
            logger.error(f"REQUIRED video not found: {exercise_slug}:{r2_kind}:{archetype}")
            incr(MetricNames.VIDEO_PLAYLIST_FALLBACK_MISSED, required='true', kind=r2_kind)
        else:
            logger.debug(f"Optional video not found: {exercise_slug}:{r2_kind}:{archetype}")
            incr(MetricNames.VIDEO_PLAYLIST_FALLBACK_MISSED, required='false', kind=r2_kind)
        
        return None
    
    def _get_candidates_for_level(self, exercise_slug: str, r2_kind: str, archetype: str, level: int) -> List:
        """Get candidate clips for specific fallback level"""
        key = (exercise_slug, r2_kind, archetype)
        candidates = self._candidates.get(key, [])
        
        if candidates:
            logger.debug(f"Level {level}: Found {len(candidates)} candidates for {key}")
        
        return candidates
    
    def _choose_with_storage_retry(self, candidates: List, exclude_id: Optional[int] = None) -> Optional:
        """
        Choose clip from candidates with storage availability retry
        Uses deterministic RNG and retries up to PLAYLIST_STORAGE_RETRY times
        """
        from django.conf import settings
        
        if not candidates:
            return None
        
        # Filter out excluded clips
        if exclude_id:
            candidates = [c for c in candidates if c.id != exclude_id]
            if not candidates:
                return None
        
        # Try up to PLAYLIST_STORAGE_RETRY times
        max_retries = min(settings.PLAYLIST_STORAGE_RETRY, len(candidates))
        
        for attempt in range(max_retries):
            # Deterministic selection
            clip = self.rng.choice(candidates)
            
            # Check storage availability
            storage = get_storage(clip)
            if storage.exists(clip):
                return clip
            
            # Remove failed clip from candidates for next attempt
            candidates = [c for c in candidates if c.id != clip.id]
            if not candidates:
                break
            
            logger.debug(f"Storage retry {attempt + 1}/{max_retries}: clip {clip.id} not available")
        
        return None
    
    def _format_video_response(self, clip, r2_kind: str) -> Dict:
        """Format clip into response dict with all required fields"""
        storage = get_storage(clip)
        
        return {
            'url': storage.playback_url(clip),
            'duration': clip.duration_seconds or 0,
            'clip_id': clip.id,
            'provider': clip.provider,
            'kind': r2_kind
        }
    
    def _get_global_video_legacy(self, r2_kind: str, archetype: str, exclude_id: Optional[int] = None):
        """Legacy method for global videos (intro, closing, weekly) that don't use prefetch"""
        query = ExerciseValidationService.get_clips_with_video()
        
        if r2_kind:
            query = query.filter(r2_kind=r2_kind)
        if archetype:
            query = query.filter(r2_archetype=archetype)
        if exclude_id:
            query = query.exclude(id=exclude_id)
        
        # Get clips ordered by ID for deterministic results
        clips = list(query.order_by('id')[:20])
        
        if not clips:
            return None
        
        selected_clip = self._choose_with_storage_retry(clips, exclude_id)
        if selected_clip:
            return self._format_video_response(selected_clip, r2_kind)
        
        return None
    
    def _build_exercise_playlist(self, exercise_slug: str, archetype: str, exercise_data: Dict) -> List[Dict]:
        """Build video sequence for a single exercise using storage adapters"""
        playlist = []
        
        # Handle both slug formats: 'ex005' (from AI) and 'push-ups' (human readable)
        slug_or_code = exercise_slug
        
        # If this looks like an exercise code (ex###), normalize to uppercase and search by PK
        if slug_or_code.lower().startswith("ex") and len(slug_or_code) == 5:
            exercise_lookup = {"pk": slug_or_code.upper()}
        else:
            exercise_lookup = {"id": slug_or_code}
        
        try:
            exercise = CSVExercise.objects.get(**exercise_lookup)
        except CSVExercise.DoesNotExist:
            return playlist
        
        # 1. Technique video
        technique_video = self._get_video_with_storage(
            exercise=exercise,
            r2_kind=VideoKind.TECHNIQUE,
            archetype=archetype
        )
        
        if technique_video:
            playlist.append({
                'type': 'technique',
                'url': technique_video['url'],
                'duration': technique_video['duration'],
                'title': f'{exercise.name} - Техника выполнения',
                'exercise_name': exercise.name,
                'exercise_slug': exercise_slug,
                'clip_id': technique_video['clip_id'],
                'provider': technique_video['provider'],
                'kind': technique_video['kind']
            })
            logger.info(f"Added technique video for {exercise_slug}: clip_id={technique_video['clip_id']}")
        
        # 2. Instruction video (motivation based on archetype)
        instruction_video = self._get_video_with_storage(
            exercise=exercise,
            r2_kind=VideoKind.INSTRUCTION,
            archetype=archetype
        )
        
        if instruction_video:
            playlist.append({
                'type': 'instruction',
                'url': instruction_video['url'],
                'duration': instruction_video['duration'],
                'title': f'Инструкция - {exercise.name}',
                'exercise_name': exercise.name,
                'exercise_slug': exercise_slug,
                'sets': exercise_data.get('sets'),
                'reps': exercise_data.get('reps'),
                'rest': exercise_data.get('rest_seconds'),
                'clip_id': instruction_video['clip_id'],
                'provider': instruction_video['provider'],
                'kind': instruction_video['kind']
            })
            logger.info(f"Added instruction video for {exercise_slug}: clip_id={instruction_video['clip_id']}")
        
        # 3. Common mistakes video (probabilistic, optional)
        from django.conf import settings
        if self.rng.random() < settings.PLAYLIST_MISTAKE_PROB:
            mistake_video = self._get_video_with_storage(
                exercise=exercise,
                r2_kind=VideoKind.MISTAKE,
                archetype=archetype
            )
            
            if mistake_video:
                playlist.append({
                    'type': 'mistake',
                    'url': mistake_video['url'],
                    'duration': mistake_video['duration'],
                    'title': f'{exercise.name} - Частые ошибки',
                    'exercise_name': exercise.name,
                    'exercise_slug': exercise_slug,
                    'clip_id': mistake_video['clip_id'],
                    'provider': mistake_video['provider'],
                    'kind': mistake_video['kind']
                })
                logger.info(f"Added mistake video for {exercise_slug}: clip_id={mistake_video['clip_id']}")
        
        return playlist
    
    def _get_rest_day_video(self, week_number: int, archetype: str) -> Dict:
        """Get motivational video for rest day using storage adapters"""
        video = self._get_video_with_storage(
            exercise=None,
            r2_kind=VideoKind.WEEKLY,
            archetype=archetype
        )
        
        if video:
            logger.info(f"Added rest day video: clip_id={video['clip_id']}")
            return {
                'type': 'rest_day',
                'url': video['url'],
                'duration': video['duration'],
                'title': 'День отдыха - Восстановление и мотивация',
                'clip_id': video['clip_id']
            }
        return None
    
    def _get_weekly_motivation_video(self, week_number: int, archetype: str) -> Dict:
        """Get weekly motivational video using storage adapters"""
        video = self._get_video_with_storage(
            exercise=None,
            r2_kind=VideoKind.CLOSING,
            archetype=archetype
        )
        
        if video:
            logger.info(f"Added weekly motivation video for week {week_number}: clip_id={video['clip_id']}")
            return {
                'type': 'weekly_motivation',
                'url': video['url'],
                'duration': video['duration'],
                'title': f'Поздравляем с завершением недели {week_number}!',
                'clip_id': video['clip_id']
            }
        return None
    
    def get_substitution_options(self, exercise_slug: str, user_equipment: List[str]) -> List[CSVExercise]:
        """Get possible exercise substitutions (equipment checking removed)"""
        try:
            exercise = CSVExercise.objects.get(id=exercise_slug)
            
            # Get all active alternatives (equipment filtering removed)
            alternatives = exercise.alternatives.filter(
                is_active=True
            ).all()
            
            return list(alternatives)
            
        except CSVExercise.DoesNotExist:
            return []
    
    # Contextual Video Selection Methods
    
    def _get_contextual_intro_video(self, workout: DailyWorkout, archetype: str) -> Optional[Dict]:
        """Get contextual intro video based on workout context"""

        # Determine context factors
        context_factors = {
            'week_context': workout.week_number,
            'day_number': workout.day_number
        }
        
        # Try to get contextual intro first
        contextual_video = self._get_contextual_video_by_factors(
            VideoKind.CONTEXTUAL_INTRO,
            archetype,
            context_factors
        )
        
        if contextual_video:
            logger.info(f"Selected contextual intro for week {workout.week_number}, day {workout.day_number}")
            return self._format_video_response(contextual_video, VideoKind.CONTEXTUAL_INTRO)
        
        # Fallback to regular intro
        regular_intro = self._get_video_with_storage(
            exercise=None,
            r2_kind=VideoKind.INTRO,
            archetype=archetype
        )
        
        if regular_intro:
            logger.debug("Fallback to regular intro video")
            return regular_intro
        
        return None
    
    def _get_contextual_outro_video(self, workout: DailyWorkout, archetype: str) -> Optional[Dict]:
        """Get contextual outro video matching the intro style"""
        context_factors = {
            'week_context': workout.week_number,
            'day_number': workout.day_number
        }
        
        # Try contextual outro first
        contextual_outro = self._get_contextual_video_by_factors(
            VideoKind.CONTEXTUAL_OUTRO,
            archetype,
            context_factors
        )
        
        if contextual_outro:
            return self._format_video_response(contextual_outro, VideoKind.CONTEXTUAL_OUTRO)
        
        # Fallback to regular closing
        return self._get_video_with_storage(
            exercise=None,
            r2_kind=VideoKind.CLOSING,
            archetype=archetype
        )
    
    def _get_mid_workout_motivation(self, workout: DailyWorkout, archetype: str) -> Optional[Dict]:
        """Get mid-workout motivational video"""
        mid_workout_video = self._get_video_with_storage(
            exercise=None,
            r2_kind=VideoKind.MID_WORKOUT,
            archetype=archetype
        )
        
        if mid_workout_video:
            logger.info(f"Added mid-workout motivation video: clip_id={mid_workout_video['clip_id']}")
            return {
                'type': 'mid_workout_motivation',
                'url': mid_workout_video['url'],
                'duration': mid_workout_video['duration'],
                'title': 'Мотивация посреди тренировки',
                'clip_id': mid_workout_video['clip_id'],
                'provider': mid_workout_video['provider'],
                'kind': mid_workout_video['kind']
            }
        
        return None
    
    def _get_weekly_theme_video(self, week_number: int, archetype: str) -> Optional[Dict]:
        """Get weekly theme-based lesson video"""
        from .models import WeeklyTheme
        
        try:
            # Get the weekly theme
            theme = WeeklyTheme.objects.get(week_number=week_number, is_active=True)
            
            # Try to get theme-based video first
            theme_video = self._get_contextual_video_by_factors(
                VideoKind.THEME_BASED,
                archetype,
                {'week_context': week_number}
            )
            
            if theme_video:
                logger.info(f"Found theme-based video for week {week_number}: {theme.theme_title}")
                return {
                    'type': 'weekly_theme',
                    'url': self._format_video_response(theme_video, VideoKind.THEME_BASED)['url'],
                    'duration': theme_video.duration_seconds,
                    'title': f'Урок недели {week_number}: {theme.theme_title}',
                    'theme_content': theme.get_content_for_archetype(archetype),
                    'clip_id': theme_video.id,
                    'provider': theme_video.provider,
                    'kind': VideoKind.THEME_BASED
                }
                
        except WeeklyTheme.DoesNotExist:
            logger.warning(f"No weekly theme found for week {week_number}")
        
        # Fallback to regular weekly video
        return self._get_weekly_motivation_video(week_number, archetype)
    
    def _get_contextual_video_by_factors(self, video_kind: str, archetype: str, factors: Dict) -> Optional:
        """
        Get video based on contextual factors like week, mood, theme
        
        Args:
            video_kind: Type of video (CONTEXTUAL_INTRO, etc.)
            archetype: User archetype
            factors: Dict with context factors (week_context, mood_type, etc.)
        """
        from django.db.models import Q

        # Build query with contextual factors
        query = ExerciseValidationService.get_clips_with_video().filter(
            r2_kind=video_kind,
            r2_archetype=archetype,
            is_active=True
        )
        
        # Apply context filters
        context_filters = Q()
        
        if 'week_context' in factors:
            context_filters |= Q(week_context=factors['week_context']) | Q(week_context__isnull=True)
        
        if 'mood_type' in factors:
            context_filters |= Q(mood_type=factors['mood_type']) | Q(mood_type='')
        
        if 'content_theme' in factors:
            context_filters |= Q(content_theme=factors['content_theme']) | Q(content_theme='')
        
        # Apply filters and get candidates
        candidates = list(query.filter(context_filters).order_by('id')[:10])
        
        if not candidates:
            # Fallback: get any video of this kind for this archetype
            candidates = list(query.order_by('id')[:5])
        
        if candidates:
            # Prefer videos with more specific context matches
            prioritized_candidates = []
            fallback_candidates = []
            
            for candidate in candidates:
                has_specific_context = any([
                    candidate.week_context == factors.get('week_context'),
                    candidate.mood_type == factors.get('mood_type'),
                    candidate.content_theme == factors.get('content_theme')
                ])
                
                if has_specific_context:
                    prioritized_candidates.append(candidate)
                else:
                    fallback_candidates.append(candidate)
            
            # Choose from prioritized first, then fallback
            final_candidates = prioritized_candidates or fallback_candidates
            
            if final_candidates:
                return self._choose_with_storage_retry(final_candidates)
        
        return None
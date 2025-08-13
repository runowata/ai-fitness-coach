"""
Test factories using factory_boy for consistent test data generation
"""

import random

import factory
from factory.django import DjangoModelFactory

from apps.users.models import User
from apps.workouts.constants import Archetype, VideoKind
from apps.workouts.models import CSVExercise, DailyWorkout, VideoClip, VideoProvider, WorkoutPlan


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    completed_onboarding = False


class CSVExerciseFactory(DjangoModelFactory):
    class Meta:
        model = CSVExercise
    
    id = factory.Sequence(lambda n: f"EX{n:03d}_v2")
    name_ru = factory.Faker('sentence', nb_words=3)
    name_en = factory.Faker('sentence', nb_words=3)
    level = factory.Faker('random_element', elements=['beginner', 'intermediate', 'advanced'])
    muscle_group = factory.Faker('random_element', elements=['chest', 'legs', 'back', 'shoulders', 'arms'])
    exercise_type = factory.Faker('random_element', elements=['strength', 'stretch', 'cardio'])
    description = factory.Faker('text', max_nb_chars=200)
    ai_tags = factory.LazyFunction(lambda: [])


class VideoClipFactory(DjangoModelFactory):
    class Meta:
        model = VideoClip
    
    exercise = factory.SubFactory(CSVExerciseFactory)
    r2_archetype = factory.Faker('random_element', elements=['professional', 'mentor', 'peer'])
    model_name = factory.Faker('random_element', elements=['mod1', 'mod2', 'mod3'])
    duration_seconds = factory.Faker('random_int', min=15, max=120)
    provider = VideoProvider.R2
    r2_kind = factory.Faker('random_element', elements=list(VideoKind))
    
    # R2 fields
    r2_file = factory.LazyAttribute(
        lambda obj: f"videos/{obj.exercise.id}_{obj.r2_kind}_{obj.r2_archetype}_{obj.model_name}.mp4"
    )
    
    @factory.post_generation
    def setup_provider_fields(obj, create, extracted, **kwargs):
        """Setup provider-specific fields based on provider type"""
        if obj.provider == VideoProvider.R2:
            if not obj.r2_file:
                obj.r2_file = f"videos/{obj.exercise.id}_{obj.r2_kind}.mp4"
        elif obj.provider == VideoProvider.STREAM:
            obj.stream_uid = factory.Faker('uuid4').generate()
            obj.playback_id = factory.Faker('uuid4').generate()
            obj.r2_file = None


class StreamVideoClipFactory(VideoClipFactory):
    """Factory for Stream-based video clips"""
    provider = VideoProvider.STREAM
    r2_file = None
    stream_uid = factory.Faker('uuid4')
    playback_id = factory.Faker('uuid4')


class WorkoutPlanFactory(DjangoModelFactory):
    class Meta:
        model = WorkoutPlan
    
    user = factory.SubFactory(UserFactory)
    plan_name = factory.Faker('sentence', nb_words=3)
    duration_weeks = factory.Faker('random_int', min=4, max=12)
    weekly_frequency = factory.Faker('random_int', min=3, max=5)
    session_duration = factory.Faker('random_int', min=30, max=90)
    is_active = True


class DailyWorkoutFactory(DjangoModelFactory):
    class Meta:
        model = DailyWorkout
    
    workout_plan = factory.SubFactory(WorkoutPlanFactory)
    week_number = factory.Faker('random_int', min=1, max=8)
    day_number = factory.Faker('random_int', min=1, max=7)
    is_rest_day = False
    exercises = factory.LazyFunction(lambda: [
        {
            'exercise_slug': 'push-ups',
            'sets': 3,
            'reps': 12,
            'rest_seconds': 60
        },
        {
            'exercise_slug': 'squats', 
            'sets': 3,
            'reps': 15,
            'rest_seconds': 90
        }
    ])


# Specialized factories for complete video coverage
class CompleteExerciseFactory(CSVExerciseFactory):
    """Exercise with complete video coverage for all required kinds"""
    
    @factory.post_generation
    def create_video_clips(obj, create, extracted, **kwargs):
        """Create video clips for all required kinds and archetypes"""
        if not create:
            return
        
        required_kinds = [VideoKind.TECHNIQUE, VideoKind.INSTRUCTION]
        archetypes = ['professional', 'mentor', 'peer']
        
        for kind in required_kinds:
            for archetype in archetypes:
                VideoClipFactory(
                    exercise=obj,
                    r2_kind=kind,
                    r2_archetype=archetype
                )
        
        # Optional mistake videos for some archetypes
        if random.random() < 0.7:  # 70% chance
            VideoClipFactory(
                exercise=obj,
                r2_kind=VideoKind.MISTAKE,
                r2_archetype='professional'
            )


class SeededExerciseSetFactory:
    """Factory to create a consistent set of exercises for deterministic tests"""
    
    @staticmethod
    def create_standard_set():
        """Create standard exercise set with predictable slugs and coverage"""
        exercises = []
        
        # Core exercises with full coverage
        core_exercises = [
            ('push-ups', 'chest', 'strength', 'beginner'),
            ('squats', 'legs', 'strength', 'beginner'), 
            ('pull-ups', 'back', 'strength', 'intermediate'),
            ('bench-press', 'chest', 'strength', 'intermediate'),
            ('deadlifts', 'back', 'strength', 'advanced'),
        ]
        
        for i, (name_base, muscle, ex_type, difficulty) in enumerate(core_exercises):
            exercise = CSVExerciseFactory(
                id=f"EX{i+1:03d}_test",
                name_ru=name_base.replace('-', ' ').title(),
                name_en=name_base.replace('-', ' ').title(),
                muscle_group=muscle,
                exercise_type=ex_type,
                level=difficulty
            )
            
            # Create full video coverage
            for archetype in ['professional', 'mentor', 'peer']:
                for kind in [VideoKind.TECHNIQUE, VideoKind.INSTRUCTION]:
                    VideoClipFactory(
                        exercise=exercise,
                        r2_kind=kind,
                        r2_archetype=archetype,
                        duration_seconds=45
                    )
                
                # Mistake videos for some
                if slug in ['push-ups', 'squats', 'bench-press']:
                    VideoClipFactory(
                        exercise=exercise,
                        r2_kind=VideoKind.MISTAKE,
                        r2_archetype=archetype,
                        duration_seconds=30
                    )
            
            exercises.append(exercise)
        
        return exercises
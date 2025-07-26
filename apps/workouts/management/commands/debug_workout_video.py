from django.core.management.base import BaseCommand
from apps.workouts.models import DailyWorkout, VideoClip, Exercise
from apps.workouts.services import VideoPlaylistBuilder


class Command(BaseCommand):
    help = 'Debug video playlist for a specific workout'

    def add_arguments(self, parser):
        parser.add_argument('workout_id', type=int, help='Workout ID to debug')

    def handle(self, *args, **options):
        workout_id = options['workout_id']
        
        try:
            workout = DailyWorkout.objects.get(id=workout_id)
            self.stdout.write(f"🔍 Debugging workout {workout_id}: {workout.name}")
            self.stdout.write(f"   User: {workout.plan.user.username}")
            self.stdout.write(f"   Archetype: {workout.plan.user.profile.archetype}")
            self.stdout.write(f"   Is rest day: {workout.is_rest_day}")
            self.stdout.write(f"   Exercises: {len(workout.exercises) if workout.exercises else 0}")
            
            # Check VideoClip records
            total_clips = VideoClip.objects.count()
            real_clips = VideoClip.objects.filter(is_placeholder=False).count()
            placeholder_clips = VideoClip.objects.filter(is_placeholder=True).count()
            
            self.stdout.write(f"\n📹 VideoClip database status:")
            self.stdout.write(f"   Total clips: {total_clips}")
            self.stdout.write(f"   Real clips: {real_clips}")
            self.stdout.write(f"   Placeholder clips: {placeholder_clips}")
            
            # Check specific archetype videos
            archetype = workout.plan.user.profile.archetype
            archetype_clips = VideoClip.objects.filter(archetype=archetype).count()
            intro_clips = VideoClip.objects.filter(
                exercise=None, 
                type='intro', 
                archetype=archetype,
                is_active=True
            ).count()
            
            self.stdout.write(f"\n🎯 Archetype '{archetype}' videos:")
            self.stdout.write(f"   Total for archetype: {archetype_clips}")
            self.stdout.write(f"   Intro videos: {intro_clips}")
            
            # Test playlist builder
            builder = VideoPlaylistBuilder()
            playlist = builder.build_workout_playlist(workout, archetype)
            
            self.stdout.write(f"\n🎵 Generated playlist:")
            self.stdout.write(f"   Items: {len(playlist)}")
            
            for i, item in enumerate(playlist):
                self.stdout.write(f"   {i+1}. {item.get('type', 'unknown')} - {item.get('title', 'No title')}")
                self.stdout.write(f"      URL: {item.get('url', 'No URL')}")
                self.stdout.write(f"      Duration: {item.get('duration', 'Unknown')} sec")
            
            # Check exercises exist
            if not workout.is_rest_day and workout.exercises:
                self.stdout.write(f"\n🏋️ Exercise check:")
                for exercise_data in workout.exercises:
                    slug = exercise_data.get('exercise_slug')
                    try:
                        exercise = Exercise.objects.get(slug=slug)
                        exercise_clips = VideoClip.objects.filter(exercise=exercise).count()
                        self.stdout.write(f"   {slug}: ✓ (clips: {exercise_clips})")
                    except Exercise.DoesNotExist:
                        self.stdout.write(f"   {slug}: ❌ Exercise not found!")
            
            # Sample video URLs
            sample_clips = VideoClip.objects.all()[:5]
            if sample_clips:
                self.stdout.write(f"\n🔗 Sample video URLs:")
                for clip in sample_clips:
                    self.stdout.write(f"   {clip.type}/{clip.archetype}: {clip.url}")
            
            self.stdout.write(self.style.SUCCESS(f"\n✅ Debug complete for workout {workout_id}"))
            
        except DailyWorkout.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Workout {workout_id} not found"))
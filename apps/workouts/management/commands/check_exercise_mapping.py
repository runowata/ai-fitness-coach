from django.core.management.base import BaseCommand

from apps.core.services.exercise_validation import ExerciseValidationService
from apps.workouts.models import CSVExercise, VideoClip


class Command(BaseCommand):
    help = "Check exercise to video mapping for comprehensive plans"

    def add_arguments(self, parser):
        parser.add_argument('--archetype', type=str, choices=['mentor', 'professional', 'peer'], 
                          default='mentor', help='Trainer archetype to check')
        parser.add_argument('--verbose', action='store_true', help='Verbose output')

    def handle(self, *args, **options):
        archetype = options['archetype']
        verbose = options['verbose']
        
        self.stdout.write("🧪 Checking exercise to video mapping...")
        
        # Get available exercises
        total_exercises = CSVExercise.objects.count()
        self.stdout.write(f"📊 Total exercises in database: {total_exercises}")
        
        if total_exercises == 0:
            self.stdout.write(self.style.WARNING("⚠️  No exercises found in database"))
            return
        
        # Get allowed exercises for archetype  
        try:
            allowed_slugs = ExerciseValidationService.get_allowed_exercise_slugs(archetype=archetype)
            self.stdout.write(f"📊 Allowed exercises for {archetype}: {len(allowed_slugs)}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error getting allowed exercises: {str(e)}"))
            return
        
        if verbose:
            self.stdout.write(f"📋 First 10 allowed exercises: {list(allowed_slugs)[:10]}")
        
        # Check exercises that would be used in comprehensive plans
        sample_exercises = ['push_ups', 'squats', 'plank', 'mountain_climbers', 'burpees']
        
        self.stdout.write(f"\n🎯 Checking common exercises used in plans:")
        for exercise_slug in sample_exercises:
            try:
                exercise = CSVExercise.objects.get(id=exercise_slug)
                self.stdout.write(f"✅ {exercise_slug}: {exercise.name}")
                
                # Check if it's in allowed list
                if exercise_slug in allowed_slugs:
                    self.stdout.write(f"   ✓ Allowed for {archetype}")
                else:
                    self.stdout.write(f"   ❌ Not allowed for {archetype}")
                    
            except CSVExercise.DoesNotExist:
                self.stdout.write(f"❌ {exercise_slug}: Not found in database")
        
        # Check video clips availability
        total_clips = VideoClip.objects.count()
        self.stdout.write(f"\n📊 Total video clips: {total_clips}")
        
        if total_clips == 0:
            self.stdout.write(self.style.WARNING("⚠️  No video clips found - playlists will be empty"))
        else:
            archetype_clips = VideoClip.objects.filter(r2_archetype=archetype).count()
            self.stdout.write(f"📊 Video clips for {archetype}: {archetype_clips}")
        
        # Test exercise resolution in VideoPlaylistBuilder format
        self.stdout.write(f"\n🔧 Testing exercise resolution for VideoPlaylistBuilder:")
        for exercise_slug in sample_exercises[:3]:  # Test first 3
            try:
                # This is how VideoPlaylistBuilder looks up exercises
                if exercise_slug.lower().startswith("ex") and len(exercise_slug) == 5:
                    exercise_lookup = {"pk": exercise_slug.upper()}
                else:
                    exercise_lookup = {"id": exercise_slug}
                
                exercise = CSVExercise.objects.get(**exercise_lookup)
                self.stdout.write(f"✅ VideoPlaylistBuilder can resolve: {exercise_slug} -> {exercise.name}")
            except CSVExercise.DoesNotExist:
                self.stdout.write(f"❌ VideoPlaylistBuilder cannot resolve: {exercise_slug}")
        
        # Summary
        self.stdout.write(f"\n📋 SUMMARY:")
        self.stdout.write(f"   • Total exercises: {total_exercises}")
        self.stdout.write(f"   • Allowed for {archetype}: {len(allowed_slugs)}")
        self.stdout.write(f"   • Total video clips: {total_clips}")
        
        if total_exercises > 0 and len(allowed_slugs) > 0:
            self.stdout.write(self.style.SUCCESS("✅ Exercise system ready for comprehensive plans"))
        else:
            self.stdout.write(self.style.ERROR("❌ Exercise system not ready - missing data"))
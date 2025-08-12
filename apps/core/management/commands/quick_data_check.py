"""
Quick data check command for deployment verification
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from apps.workouts.models import CSVExercise, VideoClip
from apps.users.models import User


class Command(BaseCommand):
    help = 'Quick check of database data for deployment verification'
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 60)
        self.stdout.write("📊 QUICK DATA CHECK")
        self.stdout.write("=" * 60)
        
        # Check exercises
        exercise_count = CSVExercise.objects.count()
        active_exercises = CSVExercise.objects.filter(is_active=True).count()
        
        if exercise_count == 0:
            self.stdout.write(self.style.ERROR(f"❌ NO EXERCISES in database!"))
            self.stdout.write(self.style.WARNING("  Run: python manage.py import_exercises_v2 --data-dir ./data/clean"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Exercises: {exercise_count} total, {active_exercises} active"))
            
            # Show first 5 exercises
            first_5 = CSVExercise.objects.all()[:5]
            self.stdout.write("  First 5 exercises:")
            for ex in first_5:
                self.stdout.write(f"    - {ex.id}: {ex.name_ru} ({ex.level})")
        
        # Check video clips
        video_count = VideoClip.objects.count()
        videos_with_files = VideoClip.objects.filter(r2_file__isnull=False).count()
        
        if video_count > 0:
            self.stdout.write(self.style.SUCCESS(f"✅ Video clips: {video_count} total, {videos_with_files} with R2 files"))
        else:
            self.stdout.write(self.style.WARNING(f"⚠️  No video clips in database"))
        
        # Check users
        user_count = User.objects.count()
        self.stdout.write(f"👥 Users: {user_count}")
        
        # Summary
        self.stdout.write("=" * 60)
        if exercise_count > 0:
            self.stdout.write(self.style.SUCCESS("✅ READY FOR AI TESTING"))
            self.stdout.write("  Run: python manage.py test_ai_generation")
        else:
            self.stdout.write(self.style.ERROR("❌ NOT READY - Import exercises first!"))
            self.stdout.write("  1. python manage.py import_exercises_v2 --data-dir ./data/clean")
            self.stdout.write("  2. python manage.py test_ai_generation")
        self.stdout.write("=" * 60)
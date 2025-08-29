"""
Management command to verify sync between database and R2 storage
"""
import requests
from django.core.management.base import BaseCommand
from apps.workouts.models import CSVExercise
from collections import defaultdict


class Command(BaseCommand):
    help = 'Verify that database exercises match R2 storage structure'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verifying sync between database and R2 storage...")
        
        # Expected R2 structure from documentation
        r2_structure = {
            'warmup': 20,      # warmup_01 to warmup_20
            'main': 100,       # main_001 to main_100
            'endurance': 30,   # endurance_01 to endurance_30
            'relaxation': 30,  # relaxation_01 to relaxation_30
        }
        
        # Count exercises in database by type
        db_counts = defaultdict(int)
        all_exercises = CSVExercise.objects.all()
        
        for exercise in all_exercises:
            video_type = exercise.video_type
            if video_type != 'unknown':
                db_counts[video_type] += 1
        
        # Compare counts
        self.stdout.write("\n📊 Comparison Results:")
        self.stdout.write("-" * 50)
        
        all_match = True
        for video_type, expected_count in r2_structure.items():
            db_count = db_counts.get(video_type, 0)
            
            if db_count == expected_count:
                status = "✅"
            else:
                status = "❌"
                all_match = False
            
            self.stdout.write(
                f"{status} {video_type.capitalize():12} - "
                f"Expected: {expected_count:3}, "
                f"Database: {db_count:3}"
            )
        
        # Check for unexpected types
        for video_type, count in db_counts.items():
            if video_type not in r2_structure and video_type != 'unknown':
                self.stdout.write(
                    self.style.WARNING(
                        f"⚠️  Unexpected type '{video_type}' with {count} exercises"
                    )
                )
                all_match = False
        
        # List missing exercises
        self.stdout.write("\n🔍 Checking for missing exercises...")
        missing_exercises = []
        
        # Check warmup
        for i in range(1, 21):
            exercise_id = f"warmup_{i:02d}"
            if not CSVExercise.objects.filter(id=exercise_id).exists():
                missing_exercises.append(exercise_id)
        
        # Check main
        for i in range(1, 101):
            exercise_id = f"main_{i:03d}"
            if not CSVExercise.objects.filter(id=exercise_id).exists():
                missing_exercises.append(exercise_id)
        
        # Check endurance
        for i in range(1, 31):
            exercise_id = f"endurance_{i:02d}"
            if not CSVExercise.objects.filter(id=exercise_id).exists():
                missing_exercises.append(exercise_id)
        
        # Check relaxation
        for i in range(1, 31):
            exercise_id = f"relaxation_{i:02d}"
            if not CSVExercise.objects.filter(id=exercise_id).exists():
                missing_exercises.append(exercise_id)
        
        if missing_exercises:
            self.stdout.write(
                self.style.ERROR(
                    f"\n❌ Missing {len(missing_exercises)} exercises:"
                )
            )
            for exercise_id in missing_exercises[:10]:  # Show first 10
                self.stdout.write(f"   - {exercise_id}")
            if len(missing_exercises) > 10:
                self.stdout.write(f"   ... and {len(missing_exercises) - 10} more")
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ All expected exercises found in database")
            )
        
        # Test R2 accessibility
        self.stdout.write("\n🌐 Testing R2 storage accessibility...")
        base_url = "https://pub-92568f8b8a15c68a9ece5fe08c66485b.r2.dev"
        
        test_files = [
            f"{base_url}/videos/exercises/warmup_01.mp4",
            f"{base_url}/videos/exercises/main_001.mp4",
            f"{base_url}/videos/motivation/intro_bro_day01.mp4",
        ]
        
        for url in test_files:
            try:
                response = requests.head(url, timeout=5)
                if response.status_code == 200:
                    self.stdout.write(f"✅ Accessible: {url.split('/')[-1]}")
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            f"⚠️  Status {response.status_code}: {url.split('/')[-1]}"
                        )
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Error accessing: {url.split('/')[-1]} - {e}")
                )
        
        # Final summary
        self.stdout.write("\n" + "=" * 50)
        if all_match and not missing_exercises:
            self.stdout.write(
                self.style.SUCCESS(
                    "✅ Database and R2 structure are in sync!"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    "❌ Database and R2 structure have discrepancies!"
                )
            )
            self.stdout.write(
                "Run 'python manage.py sync_simple_videos' to fix"
            )
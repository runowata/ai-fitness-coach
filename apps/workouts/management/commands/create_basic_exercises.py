
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.workouts.models import Exercise


class Command(BaseCommand):
    help = 'Create basic exercises without video files - ensures AI prompts work'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true',
                          help='Show what would be created without saving')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write("🚀 CREATING BASIC EXERCISES FOR AI PROMPTS")
        self.stdout.write("=" * 60)
        
        # Exercise data mapping - matches the AI prompts exactly
        exercises_data = [
            # Basic exercises
            {'id': 'ex001', 'name': 'Push-ups', 'difficulty': 'beginner'},
            {'id': 'ex002', 'name': 'Squats', 'difficulty': 'beginner'},
            {'id': 'ex004', 'name': 'Lunges', 'difficulty': 'beginner'},
            {'id': 'ex005', 'name': 'Plank', 'difficulty': 'beginner'},
            {'id': 'ex009', 'name': 'Burpees', 'difficulty': 'intermediate'},
            {'id': 'ex010', 'name': 'Mountain Climbers', 'difficulty': 'beginner'},
            {'id': 'ex011', 'name': 'Jumping Jacks', 'difficulty': 'beginner'},
            
            # Chest exercises
            {'id': 'ex007', 'name': 'Bench Press', 'difficulty': 'intermediate'},
            {'id': 'ex026', 'name': 'Chest Flyes', 'difficulty': 'intermediate'},
            {'id': 'ex042', 'name': 'Diamond Push-ups', 'difficulty': 'intermediate'},
            {'id': 'ex043', 'name': 'Wide Push-ups', 'difficulty': 'beginner'},
            {'id': 'ex045', 'name': 'Incline Push-ups', 'difficulty': 'beginner'},
            
            # Back exercises
            {'id': 'ex003', 'name': 'Pull-ups', 'difficulty': 'intermediate'},
            {'id': 'ex008', 'name': 'Rows', 'difficulty': 'beginner'},
            {'id': 'ex085', 'name': 'Lat Pulldowns', 'difficulty': 'intermediate'},
            {'id': 'ex090', 'name': 'Bent Over Rows', 'difficulty': 'intermediate'},
            {'id': 'ex084', 'name': 'Cable Rows', 'difficulty': 'intermediate'},
            
            # Leg exercises
            {'id': 'ex050', 'name': 'Bulgarian Split Squats', 'difficulty': 'intermediate'},
            {'id': 'ex051', 'name': 'Goblet Squats', 'difficulty': 'beginner'},
            {'id': 'ex052', 'name': 'Jump Squats', 'difficulty': 'intermediate'},
            {'id': 'ex062', 'name': 'Hip Thrusts', 'difficulty': 'beginner'},
            {'id': 'ex064', 'name': 'Calf Raises', 'difficulty': 'beginner'},
            {'id': 'ex067', 'name': 'Leg Curls', 'difficulty': 'intermediate'},
            
            # Shoulder exercises
            {'id': 'ex025', 'name': 'Shoulder Press', 'difficulty': 'beginner'},
            {'id': 'ex022', 'name': 'Lateral Raises', 'difficulty': 'beginner'},
            {'id': 'ex038', 'name': 'Front Raises', 'difficulty': 'beginner'},
            {'id': 'ex039', 'name': 'Rear Delt Flyes', 'difficulty': 'intermediate'},
            {'id': 'ex036', 'name': 'Arnold Press', 'difficulty': 'intermediate'},
            
            # Arm exercises
            {'id': 'ex023', 'name': 'Bicep Curls', 'difficulty': 'beginner'},
            {'id': 'ex024', 'name': 'Tricep Extensions', 'difficulty': 'beginner'},
            {'id': 'ex031', 'name': 'Hammer Curls', 'difficulty': 'beginner'},
            {'id': 'ex012', 'name': 'Dips', 'difficulty': 'intermediate'},
            
            # Core exercises
            {'id': 'ex014', 'name': 'Crunches', 'difficulty': 'beginner'},
            {'id': 'ex015', 'name': 'Russian Twists', 'difficulty': 'beginner'},
            {'id': 'ex013', 'name': 'Leg Raises', 'difficulty': 'intermediate'},
            
            # Cardio exercises
            {'id': 'ex017', 'name': 'High Knees', 'difficulty': 'beginner'},
            {'id': 'ex018', 'name': 'Butt Kicks', 'difficulty': 'beginner'},
            {'id': 'ex019', 'name': 'Jump Rope', 'difficulty': 'beginner'},
            {'id': 'ex020', 'name': 'Box Jumps', 'difficulty': 'intermediate'},
            {'id': 'ex021', 'name': 'Step-ups', 'difficulty': 'beginner'},
        ]
        
        self.stdout.write(f"📊 Will create {len(exercises_data)} exercises")
        
        if dry_run:
            self.stdout.write("\n🔍 DRY RUN - Would create:")
            for ex in exercises_data[:5]:  # Show first 5
                self.stdout.write(f"   {ex['id']}: {ex['name']} ({ex['difficulty']})")
            if len(exercises_data) > 5:
                self.stdout.write(f"   ... and {len(exercises_data) - 5} more")
            return
        
        # Create exercises
        with transaction.atomic():
            # Clear existing exercises
            self.stdout.write("🗑️ Clearing existing exercises...")
            Exercise.objects.all().delete()
            
            # Create new exercises
            self.stdout.write(f"💪 Creating {len(exercises_data)} exercises...")
            created_count = 0
            
            for ex_data in exercises_data:
                exercise = Exercise.objects.create(
                    id=ex_data['id'],
                    slug=ex_data['id'],  # Use same as ID for consistency
                    name=ex_data['name'],
                    description=f"{ex_data['name']} - proper form and technique",
                    difficulty=ex_data['difficulty'],
                    is_active=True
                )
                created_count += 1
                
                if created_count % 10 == 0:
                    self.stdout.write(f"   Created {created_count}/{len(exercises_data)} exercises...")
        
        # Final verification
        final_count = Exercise.objects.count()
        self.stdout.write("\n🎉 SUCCESS!")
        self.stdout.write(f"   💪 Total exercises created: {final_count}")
        self.stdout.write("   🤖 AI prompts can now generate workout plans!")
        
        # Show some examples
        self.stdout.write("\n📋 Sample exercises created:")
        sample_exercises = Exercise.objects.all()[:5]
        for ex in sample_exercises:
            self.stdout.write(f"   {ex.id}: {ex.name} ({ex.difficulty})")
        
        return f"Created {final_count} basic exercises"
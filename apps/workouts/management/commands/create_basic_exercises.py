
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
            {'id': 'ex001', 'name': 'Push-ups', 'muscle_groups': ['chest', 'arms'], 'difficulty': 'beginner'},
            {'id': 'ex002', 'name': 'Squats', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex004', 'name': 'Lunges', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex005', 'name': 'Plank', 'muscle_groups': ['core'], 'difficulty': 'beginner'},
            {'id': 'ex009', 'name': 'Burpees', 'muscle_groups': ['full_body'], 'difficulty': 'intermediate'},
            {'id': 'ex010', 'name': 'Mountain Climbers', 'muscle_groups': ['core', 'legs'], 'difficulty': 'beginner'},
            {'id': 'ex011', 'name': 'Jumping Jacks', 'muscle_groups': ['full_body'], 'difficulty': 'beginner'},
            
            # Chest exercises
            {'id': 'ex007', 'name': 'Bench Press', 'muscle_groups': ['chest', 'arms'], 'difficulty': 'intermediate'},
            {'id': 'ex026', 'name': 'Chest Flyes', 'muscle_groups': ['chest'], 'difficulty': 'intermediate'},
            {'id': 'ex042', 'name': 'Diamond Push-ups', 'muscle_groups': ['chest', 'arms'], 'difficulty': 'intermediate'},
            {'id': 'ex043', 'name': 'Wide Push-ups', 'muscle_groups': ['chest'], 'difficulty': 'beginner'},
            {'id': 'ex045', 'name': 'Incline Push-ups', 'muscle_groups': ['chest'], 'difficulty': 'beginner'},
            
            # Back exercises
            {'id': 'ex003', 'name': 'Pull-ups', 'muscle_groups': ['back', 'arms'], 'difficulty': 'intermediate'},
            {'id': 'ex008', 'name': 'Rows', 'muscle_groups': ['back', 'arms'], 'difficulty': 'beginner'},
            {'id': 'ex085', 'name': 'Lat Pulldowns', 'muscle_groups': ['back'], 'difficulty': 'intermediate'},
            {'id': 'ex090', 'name': 'Bent Over Rows', 'muscle_groups': ['back'], 'difficulty': 'intermediate'},
            {'id': 'ex084', 'name': 'Cable Rows', 'muscle_groups': ['back'], 'difficulty': 'intermediate'},
            
            # Leg exercises
            {'id': 'ex050', 'name': 'Bulgarian Split Squats', 'muscle_groups': ['legs'], 'difficulty': 'intermediate'},
            {'id': 'ex051', 'name': 'Goblet Squats', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex052', 'name': 'Jump Squats', 'muscle_groups': ['legs'], 'difficulty': 'intermediate'},
            {'id': 'ex062', 'name': 'Hip Thrusts', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex064', 'name': 'Calf Raises', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex067', 'name': 'Leg Curls', 'muscle_groups': ['legs'], 'difficulty': 'intermediate'},
            
            # Shoulder exercises
            {'id': 'ex025', 'name': 'Shoulder Press', 'muscle_groups': ['shoulders'], 'difficulty': 'beginner'},
            {'id': 'ex022', 'name': 'Lateral Raises', 'muscle_groups': ['shoulders'], 'difficulty': 'beginner'},
            {'id': 'ex038', 'name': 'Front Raises', 'muscle_groups': ['shoulders'], 'difficulty': 'beginner'},
            {'id': 'ex039', 'name': 'Rear Delt Flyes', 'muscle_groups': ['shoulders'], 'difficulty': 'intermediate'},
            {'id': 'ex036', 'name': 'Arnold Press', 'muscle_groups': ['shoulders'], 'difficulty': 'intermediate'},
            
            # Arm exercises
            {'id': 'ex023', 'name': 'Bicep Curls', 'muscle_groups': ['arms'], 'difficulty': 'beginner'},
            {'id': 'ex024', 'name': 'Tricep Extensions', 'muscle_groups': ['arms'], 'difficulty': 'beginner'},
            {'id': 'ex031', 'name': 'Hammer Curls', 'muscle_groups': ['arms'], 'difficulty': 'beginner'},
            {'id': 'ex012', 'name': 'Dips', 'muscle_groups': ['chest', 'arms'], 'difficulty': 'intermediate'},
            
            # Core exercises
            {'id': 'ex014', 'name': 'Crunches', 'muscle_groups': ['core'], 'difficulty': 'beginner'},
            {'id': 'ex015', 'name': 'Russian Twists', 'muscle_groups': ['core'], 'difficulty': 'beginner'},
            {'id': 'ex013', 'name': 'Leg Raises', 'muscle_groups': ['core'], 'difficulty': 'intermediate'},
            
            # Cardio exercises
            {'id': 'ex017', 'name': 'High Knees', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex018', 'name': 'Butt Kicks', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
            {'id': 'ex019', 'name': 'Jump Rope', 'muscle_groups': ['full_body'], 'difficulty': 'beginner'},
            {'id': 'ex020', 'name': 'Box Jumps', 'muscle_groups': ['legs'], 'difficulty': 'intermediate'},
            {'id': 'ex021', 'name': 'Step-ups', 'muscle_groups': ['legs'], 'difficulty': 'beginner'},
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
                    muscle_groups=ex_data['muscle_groups'],
                    equipment_needed=[],  # Default empty
                    is_active=True,
                    technique_video_url='',  # Default empty
                    mistake_video_url=''     # Default empty
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
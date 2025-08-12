from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.workouts.models import CSVExercise, VideoClip
from apps.ai_integration.services import WorkoutPlanGenerator

R2_CLIPS = {
    "pushup": {
        "instruction": "videos/exercises/instruction/pushup_mentor.mp4",
        "technique": "videos/exercises/technique/pushup_mentor.mp4", 
        "mistake": "videos/exercises/mistake/pushup_common.mp4",
    },
    "bodyweight_squat": {
        "instruction": "videos/exercises/instruction/squat_mentor.mp4",
        "technique": "videos/exercises/technique/squat_mentor.mp4",
        "mistake": "videos/exercises/mistake/squat_common.mp4", 
    },
    "plank": {
        "instruction": "videos/exercises/instruction/plank_mentor.mp4",
        "technique": "videos/exercises/technique/plank_mentor.mp4",
        "mistake": "videos/exercises/mistake/plank_common.mp4",
    }
}

class Command(BaseCommand):
    help = "Minimal v2 bootstrap: a few exercises/clips and one plan"

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting minimal v2 bootstrap...")
        
        # 1) Create exercises
        for slug, clips in R2_CLIPS.items():
            # CSVExercise uses 'id' field, not 'slug'
            exercise, created = CSVExercise.objects.get_or_create(
                id=slug, 
                defaults={
                    "name_ru": slug.replace("_", " ").title(),
                    "name_en": slug.replace("_", " ").title(),
                    "level": "beginner",
                    "muscle_group": "core" if slug == "plank" else "chest" if slug == "pushup" else "legs",
                    "exercise_type": "strength",
                    "is_active": True
                }
            )
            if created:
                self.stdout.write(f"  ✅ Created exercise: {exercise.name_ru}")
            
            # 2) Create video clips for each exercise
            for kind, r2_path in clips.items():
                clip, created = VideoClip.objects.get_or_create(
                    exercise=exercise,
                    r2_kind=kind,
                    archetype="mentor", 
                    model_name="default",
                    reminder_text="",
                    defaults={
                        "is_active": True,
                        "duration_seconds": 60,
                    }
                )
                # Set R2 file path (simulates uploaded file)
                clip.r2_file.name = r2_path
                clip.save()
                
                if created:
                    self.stdout.write(f"    ✅ Created clip: {exercise.id} - {kind}")

        # 3) Create test user and plan (optional)
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username="smoke_test",
            defaults={
                "email": "smoke@example.com",
                "first_name": "Smoke",
                "last_name": "Test"
            }
        )
        
        if hasattr(user, "profile"):
            user.profile.archetype = "mentor" 
            user.profile.age = 25
            user.profile.height = 175
            user.profile.weight = 70
            user.profile.save()
        
        # Generate a workout plan
        try:
            generator = WorkoutPlanGenerator()
            user_data = {
                "archetype": "mentor",
                "age": 25,
                "height": 175,
                "weight": 70,
                "goal": "general_fitness",
                "experience_level": "beginner",
                "available_days": 3,
                "duration_weeks": 4
            }
            
            plan = generator.create_plan(user=user, user_data=user_data)
            self.stdout.write(self.style.SUCCESS(f"✅ Created workout plan: {plan.id}"))
            
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Could not create plan: {e}"))
        
        # 4) Summary
        exercises_count = CSVExercise.objects.filter(is_active=True).count()
        clips_count = VideoClip.objects.filter(is_active=True, r2_file__isnull=False).count()
        
        self.stdout.write(self.style.SUCCESS("\n🎉 Bootstrap complete!"))
        self.stdout.write(f"  📊 {exercises_count} active exercises")
        self.stdout.write(f"  🎥 {clips_count} video clips")
        self.stdout.write(f"  👤 Test user: {user.username}")
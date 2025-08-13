"""
Generate a test workout plan using v2 system after import
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.ai_integration.services import WorkoutPlanGenerator
from apps.onboarding.services import OnboardingDataProcessor


class Command(BaseCommand):
    help = "Generate a test workout plan using imported exercises (v2)"
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--archetype',
            type=str,
            choices=['peer', 'professional', 'mentor'],
            default='mentor',
            help='Archetype for test plan'
        )
        parser.add_argument(
            '--username',
            type=str,
            default='test_user_v2',
            help='Username for test user'
        )

    def handle(self, *args, **options):
        archetype = options['archetype']
        username = options['username']
        
        self.stdout.write(f"🤖 Generating test plan for {archetype}...")
        
        # 1. Create or get test user
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'first_name': 'Test',
                'last_name': 'User'
            }
        )
        
        # 2. Set up user profile
        if hasattr(user, 'profile'):
            user.profile.archetype = archetype
            user.profile.age = 28
            user.profile.height = 175
            user.profile.weight = 70
            user.profile.fitness_level = 'beginner'
            user.profile.available_days = 3
            user.profile.duration_weeks = 6
            user.profile.save()
            self.stdout.write(f"  👤 Updated user profile: {archetype}")
        
        # 3. Collect user data for AI
        processor = OnboardingDataProcessor()
        user_data = processor.collect_user_data(user)
        
        self.stdout.write(f"  📊 Collected user data: {len(user_data)} fields")
        
        # 4. Generate workout plan
        try:
            generator = WorkoutPlanGenerator()
            plan = generator.create_plan(user=user, user_data=user_data)
            
            if plan:
                weeks_count = len(plan.plan_data.get('weeks', []))
                self.stdout.write(self.style.SUCCESS(f"  ✅ Generated plan {plan.id} ({weeks_count} weeks)"))
                
                # 5. Test playlist generation
                from apps.workouts.services.playlist_v2 import build_playlist
                playlist = build_playlist(plan.plan_data, archetype)
                
                video_items = [item for item in playlist if item.get('clip_id')]
                text_items = [item for item in playlist if item.get('text')]
                
                self.stdout.write(f"  🎬 Generated playlist: {len(video_items)} videos, {len(text_items)} texts")
                
                # Show sample exercises
                if weeks_count > 0:
                    first_week = plan.plan_data['weeks'][0]
                    if 'days' in first_week and len(first_week['days']) > 0:
                        first_day = first_week['days'][0]
                        exercises = first_day.get('exercises', [])
                        exercise_names = [ex.get('name', 'Unknown') for ex in exercises[:3]]
                        self.stdout.write(f"  🏋️  Sample exercises: {', '.join(exercise_names)}")
                
                return plan.id
            else:
                self.stdout.write(self.style.ERROR("  ❌ Plan generation failed"))
                return None
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ Error generating plan: {e}"))
            import traceback
            self.stdout.write(traceback.format_exc())
            return None
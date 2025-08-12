"""
Management command to test AI generation directly
Usage: python manage.py test_ai_generation
"""
import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.ai_integration.services import WorkoutPlanGenerator

User = get_user_model()


class Command(BaseCommand):
    help = 'Test AI workout plan generation with real API key'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--create-user',
            action='store_true',
            help='Create a test user',
        )
        parser.add_argument(
            '--username',
            type=str,
            default='ai_test_user',
            help='Username for test user',
        )
    
    def handle(self, *args, **options):
        # Ensure exercises are imported before testing
        from django.core.management import call_command
        try:
            self.stdout.write("🔄 Ensuring exercises are imported...")
            call_command("import_exercises_v2", "--data-dir", "./data/raw")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"⚠️  Exercise import failed: {e}"))
        self.stdout.write("🚀 Testing AI Generation...")
        self.stdout.write("=" * 50)
        
        # Test 1: Check OpenAI API key
        self.test_api_key()
        
        # Test 2: Test AI generation
        self.test_plan_generation()
        
        # Test 3: Create test user if requested
        if options['create_user']:
            self.create_test_user(options['username'])
    
    def test_api_key(self):
        """Test OpenAI API key configuration"""
        from django.conf import settings
        
        self.stdout.write("\n🔑 Testing OpenAI API Key...")
        
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        if not api_key:
            self.stdout.write(self.style.ERROR("❌ OPENAI_API_KEY not set"))
            return False
        
        if api_key == 'dummy':
            self.stdout.write(self.style.ERROR("❌ OPENAI_API_KEY is set to 'dummy'"))
            return False
        
        if not api_key.startswith('sk-'):
            self.stdout.write(self.style.ERROR("❌ OPENAI_API_KEY doesn't look valid (should start with 'sk-')"))
            return False
        
        self.stdout.write(self.style.SUCCESS(f"✅ API Key configured: {api_key[:10]}...{api_key[-4:]}"))
        self.stdout.write(f"📊 Model: {getattr(settings, 'OPENAI_MODEL', 'not set')}")
        self.stdout.write(f"🎛️  Max Tokens: {getattr(settings, 'OPENAI_MAX_TOKENS', 'not set')}")
        return True
    
    def test_plan_generation(self):
        """Test actual AI plan generation"""
        self.stdout.write("\n🤖 Testing AI Plan Generation...")
        
        # Sample user data for testing
        test_user_data = {
            'archetype': 'mentor',
            'age': 25,
            'height': 175,
            'weight': 70,
            'duration_weeks': 4,  # Shorter for testing
            'workout_duration': 45,
            'days_per_week': 3,
            'primary_goal': 'muscle_gain',
            'experience_level': 'beginner',
            'recent_activity_level': 'light_activity',
            'available_equipment': 'bodyweight_only',
            'preferred_workout_time': 'evening',
            'health_limitations': 'none',
            'preferred_exercise_types': 'strength_training',
            'gym_comfort_level': 'neutral',
            'motivation_style': 'wellbeing'
        }
        
        try:
            generator = WorkoutPlanGenerator()
            self.stdout.write("📤 Sending request to OpenAI...")
            
            plan_data = generator.generate_plan(test_user_data)
            
            self.stdout.write(self.style.SUCCESS("✅ AI Generation Successful!"))
            self.stdout.write(f"📋 Plan Name: {plan_data.get('plan_name', 'N/A')}")
            self.stdout.write(f"📅 Duration: {plan_data.get('duration_weeks', 'N/A')} weeks")
            self.stdout.write(f"🗓️  Total Weeks: {len(plan_data.get('weeks', []))}")
            
            # Show first week summary
            weeks = plan_data.get('weeks', [])
            if weeks:
                first_week = weeks[0]
                self.stdout.write(f"🎯 Week 1 Focus: {first_week.get('focus', 'N/A')}")
                self.stdout.write(f"📊 Days in Week 1: {len(first_week.get('days', []))}")
            
            # Save sample to file for inspection
            sample_file = 'ai_test_sample.json'
            with open(sample_file, 'w', encoding='utf-8') as f:
                json.dump(plan_data, f, indent=2, ensure_ascii=False, default=str)
            self.stdout.write(f"💾 Sample saved to: {sample_file}")
            
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ AI Generation Failed: {str(e)}"))
            
            # Print more detailed error info
            import traceback
            self.stdout.write(self.style.ERROR("🔍 Full error traceback:"))
            self.stdout.write(traceback.format_exc())
            return False
    
    def create_test_user(self, username):
        """Create a test user for manual testing"""
        self.stdout.write(f"\n👤 Creating test user: {username}")
        
        try:
            # Check if user already exists
            if User.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f"⚠️  User {username} already exists"))
                return
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@test.local",
                password='test123456'
            )
            
            self.stdout.write(self.style.SUCCESS(f"✅ Test user created: {username}"))
            self.stdout.write(f"📧 Email: {user.email}")
            self.stdout.write(f"🔑 Password: test123456")
            self.stdout.write(f"🌐 Login URL: https://ai-fitness-coach-ttzf.onrender.com/users/login/")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create user: {str(e)}"))
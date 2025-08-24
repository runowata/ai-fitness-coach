#!/usr/bin/env python
"""
Quick test script for AI workout plan generation
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append('/Users/alexbel/Desktop/Проекты/AI Fitness Coach')
django.setup()

from django.contrib.auth import get_user_model
from apps.onboarding.services import OnboardingDataProcessor
from apps.ai_integration.services import WorkoutPlanGenerator

User = get_user_model()

def main():
    try:
        # Get the test user
        user = User.objects.get(email='test@test.com')
        print(f"✅ Found user: {user.email}")
        print(f"📋 User archetype: {user.profile.archetype}")
        
        # Check responses count
        responses_count = user.onboarding_responses.count()
        print(f"📝 Onboarding responses: {responses_count}")
        
        if responses_count < 10:
            print("❌ Not enough onboarding responses. Run: python manage.py complete_onboarding_auto --archetype mentor")
            return
        
        # Process onboarding data
        processed_data = OnboardingDataProcessor.collect_user_data(user)
        print(f"🔄 Processed onboarding data: {len(processed_data)} fields")
        
        # Generate workout plan
        generator = WorkoutPlanGenerator()
        print("🤖 Generating AI workout plan...")
        
        result = generator.generate_plan(
            user_data=processed_data,
            use_comprehensive=True
        )
        
        print(f"✅ AI Plan generated successfully!")
        print(f"🎯 Goal: {result.get('goal', 'Unknown')}")
        print(f"📝 Description length: {len(result.get('description', ''))} characters")
        
        # Get plan data
        plan_data = result.get('training_program', {})
        total_exercises = 0
        for week in plan_data.get('weeks', []):
            for day in week.get('days', []):
                total_exercises += len(day.get('exercises', []))
        
        print(f"💪 Total exercises in plan: {total_exercises}")
        print("\nFirst few exercises:")
        for i, week in enumerate(plan_data.get('weeks', [])[:1]):
            for j, day in enumerate(week.get('days', [])[:3]):
                print(f"  Week {i+1}, Day {j+1}: {len(day.get('exercises', []))} exercises")
                for k, ex in enumerate(day.get('exercises', [])[:2]):
                    print(f"    - {ex.get('exercise_slug', 'Unknown')}: {ex.get('sets', 0)}x{ex.get('reps', 0)}")
        
    except User.DoesNotExist:
        print("❌ Test user not found. Run: python manage.py complete_onboarding_auto --archetype mentor")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
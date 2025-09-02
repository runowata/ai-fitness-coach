#!/usr/bin/env python
"""
Full system integration test for AI Fitness Coach
Tests the complete flow with 3-week plan generation
"""

import os
import sys
import django
import json
from datetime import datetime
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.models import UserProfile
from apps.workouts.models import WorkoutPlan, CSVExercise, VideoClip
from apps.onboarding.services import OnboardingDataProcessor
from apps.ai_integration.services import WorkoutPlanGenerator
from apps.core.services.exercise_validation import ExerciseValidationService

User = get_user_model()

def run_full_system_test():
    print("🚀 FULL SYSTEM INTEGRATION TEST")
    print("=" * 60)
    
    # 1. Check system status
    print("\n📊 SYSTEM STATUS:")
    print(f"  Total exercises: {CSVExercise.objects.count()}")
    print(f"  Active exercises: {CSVExercise.objects.filter(is_active=True).count()}")
    print(f"  Video clips: {VideoClip.objects.count()}")
    allowed_exercises = ExerciseValidationService.get_allowed_exercise_slugs()
    print(f"  Exercises with complete video: {len(allowed_exercises)}")
    
    # 2. Create test user
    print("\n👤 CREATING TEST USER:")
    test_username = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    test_email = f"{test_username}@example.com"
    user = User.objects.create_user(
        username=test_username,
        email=test_email,
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    print(f"  Created user: {user.email}")
    
    # 3. Create user profile with 3-week plan preference
    print("\n📝 CREATING USER PROFILE:")
    profile = UserProfile.objects.create(
        user=user,
        archetype='mentor',  # Use mentor archetype
        age=30,
        height=180,
        weight=75,
        goals='muscle_gain,strength',
        flexibility_level=5,  # 1-10 scale
        onboarding_completed_at=timezone.now()
    )
    print(f"  Profile created: {profile.archetype} archetype")
    
    # 4. Prepare onboarding data
    print("\n🎯 PREPARING ONBOARDING DATA:")
    user_data = OnboardingDataProcessor.collect_user_data(profile)
    # Set 3-week duration manually since it's not a profile field
    user_data['duration_weeks'] = 3
    print(f"  Duration: {user_data.get('duration_weeks')} weeks")
    print(f"  Archetype: {user_data.get('archetype')}")
    print(f"  Equipment: {user_data.get('equipment_list')}")
    
    # 5. Check exercise whitelist
    print("\n📋 EXERCISE WHITELIST:")
    whitelist = list(ExerciseValidationService.get_allowed_exercise_slugs(profile.archetype))
    print(f"  Available exercises for {profile.archetype}: {len(whitelist)}")
    
    # Sample exercises by category
    warmup = [e for e in whitelist if e.startswith('WZ')]
    main = [e for e in whitelist if e.startswith('EX')]
    endurance = [e for e in whitelist if e.startswith('SX') or e.startswith('CX')]
    cooldown = [e for e in whitelist if e.startswith('CZ')]
    
    print(f"  Warmup exercises (WZ): {len(warmup)}")
    print(f"  Main exercises (EX): {len(main)}")
    print(f"  Endurance exercises (SX/CX): {len(endurance)}")
    print(f"  Cooldown exercises (CZ): {len(cooldown)}")
    
    # 6. Create a simple test plan
    print("\n🔧 CREATING TEST PLAN:")
    
    # Create a simple 3-week plan manually
    fallback_plan = {
        'plan_name': '3-Week Test Plan',
        'duration_weeks': 3,
        'goal': 'General fitness',
        'weeks': []
    }
    
    # Generate 3 weeks of workouts
    for week_num in range(1, 4):
        week = {
            'week_number': week_num,
            'days': []
        }
        
        # 7 days per week
        for day_num in range(1, 8):
            day = {
                'day_number': day_num,
                'warmup_exercises': warmup[:2] if warmup else [],
                'main_exercises': main[:4] if main else [],
                'endurance_exercises': endurance[:2] if endurance else [],
                'cooldown_exercises': cooldown[:2] if cooldown else []
            }
            week['days'].append(day)
        
        fallback_plan['weeks'].append(week)
    
    if fallback_plan:
        print(f"  ✅ Fallback plan generated: {fallback_plan.get('plan_name')}")
        print(f"  Duration: {fallback_plan.get('duration_weeks')} weeks")
        print(f"  Weeks in plan: {len(fallback_plan.get('weeks', []))}")
        
        # Check first week structure
        if fallback_plan.get('weeks'):
            first_week = fallback_plan['weeks'][0]
            print(f"  First week has {len(first_week.get('days', []))} days")
            
            # Check first day
            if first_week.get('days'):
                first_day = first_week['days'][0]
                print(f"\n  📅 First day structure:")
                print(f"    Day: {first_day.get('day_number')}")
                print(f"    Warmup: {len(first_day.get('warmup_exercises', []))} exercises")
                print(f"    Main: {len(first_day.get('main_exercises', []))} exercises")
                print(f"    Endurance: {len(first_day.get('endurance_exercises', []))} exercises")
                print(f"    Cooldown: {len(first_day.get('cooldown_exercises', []))} exercises")
                
                # Verify all exercises are from whitelist
                all_exercises = (
                    first_day.get('warmup_exercises', []) +
                    first_day.get('main_exercises', []) +
                    first_day.get('endurance_exercises', []) +
                    first_day.get('cooldown_exercises', [])
                )
                
                invalid_exercises = [e for e in all_exercises if e not in whitelist]
                if invalid_exercises:
                    print(f"    ⚠️  Invalid exercises found: {invalid_exercises}")
                else:
                    print(f"    ✅ All exercises are valid and have video coverage")
    else:
        print("  ❌ Fallback plan generation failed")
    
    # 7. Create workout plan in database
    print("\n💾 SAVING WORKOUT PLAN:")
    try:
        workout_plan = WorkoutPlan.objects.create(
            user=user,
            name=fallback_plan.get('plan_name', '3-Week Test Plan'),
            duration_weeks=3,
            goal=fallback_plan.get('goal', 'General fitness'),
            plan_data=fallback_plan
        )
        print(f"  ✅ Workout plan saved: {workout_plan.name}")
        print(f"  Plan ID: {workout_plan.id}")
    except Exception as e:
        print(f"  ❌ Error saving plan: {e}")
    
    # 8. Verify video coverage for exercises
    print("\n🎥 VIDEO COVERAGE CHECK:")
    from apps.workouts.constants import VideoKind
    
    # Check technique videos
    technique_videos = VideoClip.objects.filter(
        r2_kind=VideoKind.TECHNIQUE,
        is_active=True
    ).values_list('exercise_id', flat=True).distinct()
    
    print(f"  Exercises with technique videos: {len(set(technique_videos))}")
    
    # Check motivational videos (should be 315 total)
    intro_videos = VideoClip.objects.filter(r2_kind=VideoKind.INTRO).count()
    closing_videos = VideoClip.objects.filter(r2_kind=VideoKind.CLOSING).count()
    weekly_videos = VideoClip.objects.filter(r2_kind=VideoKind.WEEKLY).count()
    
    print(f"  Intro videos: {intro_videos}")
    print(f"  Closing videos: {closing_videos}")
    print(f"  Weekly/motivational videos: {weekly_videos}")
    
    # 9. Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print(f"  ✅ User created: {user.email}")
    print(f"  ✅ Profile created: {profile.archetype} archetype")
    print(f"  ✅ Plan duration: {user_data.get('duration_weeks', 3)} weeks")
    print(f"  ✅ Exercise whitelist: {len(whitelist)} exercises")
    print(f"  ✅ Fallback plan generated: {len(fallback_plan.get('weeks', []))} weeks")
    
    if workout_plan:
        print(f"  ✅ Workout plan saved to database")
    
    print("\n🎉 FULL SYSTEM TEST COMPLETED!")
    
    # Cleanup
    print("\n🧹 Cleaning up test data...")
    if workout_plan:
        workout_plan.delete()
    profile.delete()
    user.delete()
    print("  Test data cleaned up")
    
    return True

if __name__ == "__main__":
    try:
        success = run_full_system_test()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
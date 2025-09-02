"""
Management command to test the complete user journey from registration to day 21
Usage: python manage.py test_full_user_journey
"""
import json
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.urls import reverse
from django.utils import timezone

from apps.onboarding.views import create_demo_plan_for_user
from apps.workouts.models import WorkoutPlan, DailyWorkout, DailyPlaylistItem
# from apps.workouts.services.playlist_generator_v2 import PlaylistGeneratorV2  # Not needed anymore

User = get_user_model()


class Command(BaseCommand):
    help = 'Test complete user journey from registration to day 21'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='journey_test_user',
            help='Username for test user',
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Cleanup test user after completion',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🚀 Testing Complete User Journey...")
        self.stdout.write("=" * 60)
        
        username = options['username']
        
        try:
            # Stage 1: Create Test User
            user = self.create_test_user(username)
            if not user:
                return
                
            # Stage 2: Create Demo Plan
            plan = self.create_demo_plan(user)
            if not plan:
                return
                
            # Stage 3: Validate 21-Day Plan
            self.validate_21_day_plan(plan)
            
            # Stage 4: Test Playlist Generation
            self.test_playlist_generation(user, plan)
            
            # Stage 5: Test Day 21 Access
            self.test_final_day_access(plan)
            
            # Stage 6: Final Journey Summary
            self.journey_summary(user, plan)
            
            # Cleanup if requested
            if options['cleanup']:
                self.cleanup_test_user(user)
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Journey test failed: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
    
    def create_test_user(self, username):
        """Stage 1: Create and setup test user"""
        self.stdout.write(f"\n👤 STAGE 1: Creating test user '{username}'...")
        
        try:
            # Delete existing test user if exists
            User.objects.filter(username=username).delete()
            
            user = User.objects.create_user(
                username=username,
                email=f"{username}@journey-test.local",
                password='test123456',
                is_adult_confirmed=True,
                completed_onboarding=False
            )
            
            # Create profile
            if hasattr(user, 'profile'):
                profile = user.profile
            else:
                from apps.users.models import UserProfile
                profile = UserProfile.objects.create(user=user)
            
            self.stdout.write(self.style.SUCCESS(f"✅ Test user created: {username}"))
            self.stdout.write(f"📧 Email: {user.email}")
            self.stdout.write(f"🔑 Password: test123456")
            
            return user
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Failed to create user: {str(e)}"))
            return None
    
    def create_demo_plan(self, user):
        """Stage 2: Create demo plan using the same logic as onboarding"""
        self.stdout.write(f"\n📋 STAGE 2: Creating demo plan for user...")
        
        try:
            plan = create_demo_plan_for_user(user)
            
            if plan:
                # Mark onboarding as completed (as per fixed logic)
                user.completed_onboarding = True
                user.save()
                
                if hasattr(user, 'profile'):
                    user.profile.onboarding_completed_at = timezone.now()
                    user.profile.save()
                
                self.stdout.write(self.style.SUCCESS(f"✅ Demo plan created: {plan.name}"))
                self.stdout.write(f"📅 Duration: {plan.duration_weeks} weeks")
                self.stdout.write(f"🎯 Status: {plan.status}")
                
                return plan
            else:
                self.stdout.write(self.style.ERROR("❌ Failed to create demo plan"))
                return None
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Demo plan creation failed: {str(e)}"))
            return None
    
    def validate_21_day_plan(self, plan):
        """Stage 3: Validate that the plan has 21 days"""
        self.stdout.write(f"\n✅ STAGE 3: Validating 21-day plan structure...")
        
        daily_workouts = DailyWorkout.objects.filter(plan=plan).order_by('day_number')
        
        self.stdout.write(f"📊 Total days created: {daily_workouts.count()}")
        
        if daily_workouts.count() != 21:
            self.stdout.write(self.style.ERROR(f"❌ Expected 21 days, got {daily_workouts.count()}"))
            return False
        
        # Check week distribution
        for week in range(1, 4):  # Weeks 1, 2, 3
            week_days = daily_workouts.filter(week_number=week)
            self.stdout.write(f"📅 Week {week}: {week_days.count()} days")
        
        # Check specific days
        day_1 = daily_workouts.filter(day_number=1).first()
        day_21 = daily_workouts.filter(day_number=21).first()
        
        if day_1:
            self.stdout.write(f"🎯 Day 1: {day_1.name} (Week {day_1.week_number})")
        if day_21:
            self.stdout.write(f"🏁 Day 21: {day_21.name} (Week {day_21.week_number})")
        
        self.stdout.write(self.style.SUCCESS("✅ 21-day plan structure validated"))
        return True
    
    def test_playlist_generation(self, user, plan):
        """Stage 4: Test playlist generation for key days"""
        self.stdout.write(f"\n🎵 STAGE 4: Testing playlist generation...")
        
        try:
            # FIXED: Don't generate new playlists - just check existing ones
            # Demo plan already creates all playlists, no need to regenerate
            
            # Check playlist for Day 1
            day_1_workout = DailyWorkout.objects.filter(plan=plan, day_number=1).first()
            if day_1_workout:
                playlist_1 = DailyPlaylistItem.objects.filter(day=day_1_workout).order_by('order')
                self.stdout.write(f"🎬 Day 1 playlist: {len(playlist_1)} videos")
            
            # Check playlist for Day 21
            day_21_workout = DailyWorkout.objects.filter(plan=plan, day_number=21).first()
            if day_21_workout:
                playlist_21 = DailyPlaylistItem.objects.filter(day=day_21_workout).order_by('order')
                self.stdout.write(f"🏁 Day 21 playlist: {len(playlist_21)} videos")
                
                # Check the last video
                if playlist_21:
                    last_video = playlist_21.last()
                    self.stdout.write(f"📺 Last video (position {last_video.order + 1}): {last_video.video.name if last_video.video else 'No video'}")
                    self.stdout.write(f"🎭 Role: {last_video.role}")
            
            self.stdout.write(self.style.SUCCESS("✅ Playlist generation tested"))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Playlist generation failed: {str(e)}"))
            return False
    
    def test_final_day_access(self, plan):
        """Stage 5: Test accessing day 21"""
        self.stdout.write(f"\n🏁 STAGE 5: Testing Day 21 access...")
        
        try:
            day_21 = DailyWorkout.objects.filter(plan=plan, day_number=21).first()
            
            if not day_21:
                self.stdout.write(self.style.ERROR("❌ Day 21 not found"))
                return False
            
            # Check playlist items for day 21
            playlist_items = DailyPlaylistItem.objects.filter(day=day_21).order_by('order')
            
            self.stdout.write(f"📺 Day 21 playlist items: {playlist_items.count()}")
            
            if playlist_items.count() > 0:
                self.stdout.write(f"🎬 First video: {playlist_items.first().video.name if playlist_items.first().video else 'No video'}")
                self.stdout.write(f"🎭 Last video: {playlist_items.last().video.name if playlist_items.last().video else 'No video'}")
                
                # Check if this is position 16 (the expected last video)
                last_item = playlist_items.last()
                expected_position = 15  # 0-based indexing, so position 15 = video 16
                if last_item.order == expected_position:
                    self.stdout.write(self.style.SUCCESS(f"✅ Last video is at position {last_item.order + 1} as expected"))
                else:
                    self.stdout.write(f"⚠️  Last video is at position {last_item.order + 1}, expected 16")
            
            # Test URL generation
            workout_day_url = reverse('workouts:workout_day', kwargs={'day_id': day_21.id})
            self.stdout.write(f"🌐 Day 21 URL: {workout_day_url}")
            
            self.stdout.write(self.style.SUCCESS("✅ Day 21 access tested"))
            return True
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Day 21 access test failed: {str(e)}"))
            return False
    
    def journey_summary(self, user, plan):
        """Stage 6: Final summary"""
        self.stdout.write(f"\n📋 STAGE 6: Journey Summary")
        self.stdout.write("=" * 40)
        
        self.stdout.write(f"👤 User: {user.username} ({user.email})")
        self.stdout.write(f"✅ Onboarding completed: {user.completed_onboarding}")
        self.stdout.write(f"📋 Plan: {plan.name}")
        self.stdout.write(f"📅 Duration: {plan.duration_weeks} weeks")
        self.stdout.write(f"🎯 Status: {plan.status}")
        
        total_days = DailyWorkout.objects.filter(plan=plan).count()
        total_videos = DailyPlaylistItem.objects.filter(day__plan=plan).count()
        
        self.stdout.write(f"📊 Total days: {total_days}")
        self.stdout.write(f"🎬 Total videos: {total_videos}")
        
        # Test URLs for manual verification
        self.stdout.write(f"\n🌐 Test URLs:")
        self.stdout.write(f"Login: https://ai-fitness-coach-ttzf.onrender.com/users/login/")
        self.stdout.write(f"Dashboard: https://ai-fitness-coach-ttzf.onrender.com/users/dashboard/")
        self.stdout.write(f"My Plan: https://ai-fitness-coach-ttzf.onrender.com/workouts/my-plan/")
        
        if total_days >= 21:
            day_21 = DailyWorkout.objects.filter(plan=plan, day_number=21).first()
            if day_21:
                self.stdout.write(f"Day 21: https://ai-fitness-coach-ttzf.onrender.com/workouts/day/{day_21.id}/")
        
        self.stdout.write(self.style.SUCCESS("🎉 COMPLETE USER JOURNEY TEST FINISHED!"))
    
    def cleanup_test_user(self, user):
        """Clean up test user"""
        self.stdout.write(f"\n🧹 Cleaning up test user...")
        try:
            user.delete()
            self.stdout.write(self.style.SUCCESS("✅ Test user cleaned up"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Cleanup failed: {str(e)}"))
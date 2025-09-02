"""
Management command to test all workout-related pages for 500 errors
Usage: python manage.py test_workout_pages
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.test import Client, RequestFactory
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

from apps.workouts.models import WorkoutPlan, DailyWorkout
from apps.workouts import views

User = get_user_model()


class Command(BaseCommand):
    help = 'Test all workout-related pages for errors'
    
    def handle(self, *args, **options):
        self.stdout.write("🧪 Testing Workout Pages for Errors...")
        self.stdout.write("=" * 50)
        
        # Get or create test user with plan
        user = self.get_test_user()
        if not user:
            return
            
        plan = self.get_test_plan(user)
        if not plan:
            return
            
        # Test all workout pages
        self.test_workout_pages(user, plan)
        
        self.stdout.write(self.style.SUCCESS("🎉 All workout pages tested!"))
    
    def get_test_user(self):
        """Get existing test user or create new one"""
        try:
            # Try to find existing test user with plan
            user = User.objects.filter(
                username__startswith='journey21_test'
            ).first()
            
            if user:
                self.stdout.write(f"✅ Using existing test user: {user.username}")
                return user
            else:
                self.stdout.write("❌ No test user found. Run 'test_full_user_journey' first.")
                return None
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error getting test user: {str(e)}"))
            return None
    
    def get_test_plan(self, user):
        """Get test plan for user"""
        try:
            plan = WorkoutPlan.objects.filter(user=user).first()
            if plan:
                self.stdout.write(f"✅ Found test plan: {plan.name}")
                self.stdout.write(f"📅 Duration: {plan.duration_weeks} weeks")
                
                total_days = DailyWorkout.objects.filter(plan=plan).count()
                self.stdout.write(f"📊 Total days: {total_days}")
                
                return plan
            else:
                self.stdout.write("❌ No workout plan found for test user")
                return None
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error getting test plan: {str(e)}"))
            return None
    
    def test_workout_pages(self, user, plan):
        """Test all workout-related pages"""
        client = Client()
        client.force_login(user)
        
        self.stdout.write(f"\n📋 Testing workout pages...")
        
        # Test 1: My Plan page
        self.test_page(client, "workouts:my_plan", "My Plan")
        
        # Test 2: Plan Overview (if it exists)
        try:
            self.test_page(client, "workouts:plan_overview", "Plan Overview")
        except:
            self.stdout.write("⏭️  Plan Overview URL not found, skipping")
        
        # Test 3: History page
        try:
            self.test_page(client, "workouts:history", "History")
        except:
            self.stdout.write("⏭️  History URL not found, skipping")
        
        # Test 4: Daily workout pages - test first few days and last day
        days_to_test = [1, 2, 3, 21]  # First few and last day
        
        for day_num in days_to_test:
            daily_workout = DailyWorkout.objects.filter(
                plan=plan, 
                day_number=day_num
            ).first()
            
            if daily_workout:
                self.test_day_page(client, daily_workout, f"Day {day_num}")
            else:
                self.stdout.write(f"⚠️  Day {day_num} not found in plan")
        
        # Test 5: Test a few random days
        random_days = DailyWorkout.objects.filter(plan=plan)[5:8]  # Days 6-8
        for daily_workout in random_days:
            self.test_day_page(client, daily_workout, f"Day {daily_workout.day_number} (Random)")
    
    def test_page(self, client, url_name, page_name, **kwargs):
        """Test a specific page"""
        try:
            if kwargs:
                url = reverse(url_name, kwargs=kwargs)
            else:
                url = reverse(url_name)
                
            response = client.get(url)
            
            if response.status_code == 200:
                self.stdout.write(f"✅ {page_name}: OK (200)")
                
                # Check for template errors in content
                content = response.content.decode('utf-8')
                if 'TemplateSyntaxError' in content or 'TemplateDoesNotExist' in content:
                    self.stdout.write(f"⚠️  {page_name}: Template error found in content")
                
            elif response.status_code == 404:
                self.stdout.write(f"❌ {page_name}: Not Found (404) - URL: {url}")
            elif response.status_code == 500:
                self.stdout.write(f"❌ {page_name}: Server Error (500) - URL: {url}")
                # Try to get more error details
                try:
                    content = response.content.decode('utf-8')
                    if 'does not exist' in content:
                        self.stdout.write(f"   💡 Likely missing field/filter error")
                except:
                    pass
            else:
                self.stdout.write(f"⚠️  {page_name}: Status {response.status_code} - URL: {url}")
                
        except Exception as e:
            self.stdout.write(f"❌ {page_name}: Exception - {str(e)}")
    
    def test_day_page(self, client, daily_workout, page_name):
        """Test a specific workout day page"""
        try:
            url = reverse('workouts:workout_day', kwargs={'day_id': daily_workout.id})
            response = client.get(url)
            
            if response.status_code == 200:
                self.stdout.write(f"✅ {page_name}: OK (200)")
                
                # Check for specific content
                content = response.content.decode('utf-8')
                
                # Check for playlist content
                if 'Видео-плейлист дня' in content:
                    self.stdout.write(f"   📺 Playlist section found")
                elif 'Плейлист готовится' in content:
                    self.stdout.write(f"   ⏳ Playlist preparing message found")
                else:
                    self.stdout.write(f"   ⚠️  No playlist content found")
                
                # Check for template errors
                if 'TemplateSyntaxError' in content:
                    self.stdout.write(f"   ❌ Template syntax error found!")
                elif 'does not exist' in content and 'filter' in content:
                    self.stdout.write(f"   ❌ Template filter error found!")
                    
            elif response.status_code == 404:
                self.stdout.write(f"❌ {page_name}: Not Found (404)")
            elif response.status_code == 500:
                self.stdout.write(f"❌ {page_name}: Server Error (500)")
            else:
                self.stdout.write(f"⚠️  {page_name}: Status {response.status_code}")
                
        except Exception as e:
            self.stdout.write(f"❌ {page_name}: Exception - {str(e)}")
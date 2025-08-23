import logging

from django.conf import settings
from django.core.management import call_command
from django.db import connection
from django.shortcuts import redirect
from django.urls import reverse

logger = logging.getLogger(__name__)

# Safe paths that don't require strict validation
SAFE_PATHS = ("/", "/healthz/", "/onboarding/", "/accounts/", "/admin/", "/static/", "/media/")


class StrictAccessMiddleware:
    """
    Middleware that blocks access to protected pages until user is ready
    
    Protects workout-related pages until user has:
    - Completed onboarding
    - Has an active workout plan
    - Plan has valid data and exercises
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.enabled = getattr(settings, 'STRICT_ACCESS_MIDDLEWARE_ENABLED', True)
    
    def __call__(self, request):
        # Skip middleware if disabled
        if not self.enabled:
            return self.get_response(request)
        
        path = request.path or "/"
        
        # Check if this is a protected path and user is not ready
        if self._is_protected_path(path) and not self._user_is_ready(request):
            return redirect(self._get_onboarding_url())
        
        return self.get_response(request)
    
    def _is_protected_path(self, path: str) -> bool:
        """
        Check if path requires strict validation
        
        Args:
            path: Request path
            
        Returns:
            True if path is protected
        """
        # Allow safe paths
        if any(path.startswith(safe_path) for safe_path in SAFE_PATHS):
            return False
        
        # Protect workout-related paths
        protected_prefixes = ["/workouts/", "/api/workout/", "/dashboard/"]
        return any(path.startswith(prefix) for prefix in protected_prefixes)
    
    def _user_is_ready(self, request) -> bool:
        """
        Check if user has completed setup and is ready for protected pages
        
        Args:
            request: Django request object
            
        Returns:
            True if user is ready for protected content
        """
        user = getattr(request, "user", None)
        
        # Anonymous users are not ready
        if not (user and user.is_authenticated):
            return False
        
        try:
            # Check if user has an active workout plan
            plans = user.workout_plans.filter(is_active=True)
            if not plans.exists():
                return False
            
            plan = plans.first()
            
            # Check if plan has valid data
            plan_data_ok = bool(getattr(plan, "plan_data", None))
            if not plan_data_ok:
                return False
            
            # Check if plan has exercises (non-rest days)
            has_exercises = plan.daily_workouts.filter(
                is_rest_day=False
            ).exclude(
                exercises__isnull=True
            ).exclude(
                exercises=[]
            ).exists()
            
            return has_exercises
            
        except Exception as e:
            logger.warning(f"Error checking user readiness: {e}")
            return False
    
    def _get_onboarding_url(self) -> str:
        """
        Get URL for onboarding start
        
        Returns:
            Onboarding start URL
        """
        try:
            return reverse("onboarding:start")
        except Exception:
            return "/onboarding/"

class DatabaseSetupMiddleware:
    """
    Middleware to automatically setup database on first request in production.
    This is a workaround for Render.com ignoring our startCommand.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.setup_completed = False
        
    def __call__(self, request):
        # Only run setup once and only in production
        if not self.setup_completed and getattr(settings, 'RENDER', False):
            try:
                self.setup_database()
                self.setup_completed = True
            except Exception as e:
                logger.error(f"Database setup failed: {e}")
                # Continue anyway - don't break the app
        
        response = self.get_response(request)
        return response
    
    def setup_database(self):
        """Setup database if needed"""
        logger.info("🚀 Database Setup Middleware - checking database...")
        
        try:
            # Check if basic tables exist
            with connection.cursor() as cursor:
                # Check for user_profiles table
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'user_profiles'
                    );
                """)
                user_profiles_exists = cursor.fetchone()[0]
                
                # Check if exercises table has equipment_needed column
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns
                        WHERE table_schema = 'public' 
                        AND table_name = 'exercises'
                        AND column_name = 'equipment_needed'
                    );
                """)
                equipment_column_exists = cursor.fetchone()[0]
                
            if not user_profiles_exists or not equipment_column_exists:
                logger.info("Database setup needed...")
                logger.info(f"user_profiles exists: {user_profiles_exists}")
                logger.info(f"equipment_needed column exists: {equipment_column_exists}")
                
                # Force run migrations (they might be marked as applied but not actually applied)
                logger.info("Running migrations with fake rollback first...")
                try:
                    call_command('migrate', 'workouts', '0001', '--fake', verbosity=0)
                    call_command('migrate', 'workouts', verbosity=0)
                except Exception as migrate_error:
                    logger.info(f"Migration rollback failed (expected): {migrate_error}")
                    
                # Just run all migrations
                call_command('migrate', '--noinput', verbosity=1)
                logger.info("✓ Migrations complete")
                
                # Verify the column exists now
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT EXISTS (
                            SELECT FROM information_schema.columns
                            WHERE table_schema = 'public' 
                            AND table_name = 'exercises'
                            AND column_name = 'equipment_needed'
                        );
                    """)
                    equipment_column_exists = cursor.fetchone()[0]
                
                if equipment_column_exists:
                    logger.info("✓ equipment_needed column confirmed")
                    # Bootstrap from videos
                    call_command('bootstrap_from_videos')
                    logger.info("✓ Bootstrap from videos complete")
                    logger.info("🎉 Database setup complete - AI Fitness Coach ready!")
                else:
                    logger.error("❌ equipment_needed column still missing after migrations")
            else:
                # Check if we need to bootstrap exercises
                from apps.workouts.models import Exercise
                if Exercise.objects.count() == 0:
                    logger.info("No exercises found - running bootstrap...")
                    call_command('bootstrap_from_videos')
                    logger.info("✓ Bootstrap from videos complete")
                else:
                    logger.info("✓ Database already set up")
                
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            # Don't raise - let the app continue
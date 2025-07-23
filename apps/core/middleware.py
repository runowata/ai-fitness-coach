import os
import logging
from django.core.management import call_command
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)

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
                logger.info("✓ Database already set up")
                
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            # Don't raise - let the app continue
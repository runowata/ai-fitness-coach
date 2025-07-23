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
            # Check if user_profiles table exists
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'user_profiles'
                    );
                """)
                table_exists = cursor.fetchone()[0]
                
            if not table_exists:
                logger.info("user_profiles table not found. Running setup...")
                
                # Run migrations
                call_command('migrate', '--noinput', verbosity=0)
                logger.info("✓ Migrations complete")
                
                # Bootstrap from videos
                call_command('bootstrap_from_videos')
                logger.info("✓ Bootstrap from videos complete")
                
                logger.info("🎉 Database setup complete - AI Fitness Coach ready\!")
            else:
                logger.info("✓ Database already set up")
                
        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise
EOF < /dev/null
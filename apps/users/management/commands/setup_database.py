import logging
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup database with migrations and fixtures if needed'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== Database Setup Command ==='))
        
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
                self.stdout.write(self.style.WARNING('user_profiles table not found. Running migrations...'))
                
                # Run migrations
                call_command('migrate', '--noinput', verbosity=2)
                
                # CLEAN START - Bootstrap everything from video files
                try:
                    self.stdout.write('🚀 Bootstrapping complete application from video files...')
                    call_command('bootstrap_from_videos')
                    self.stdout.write(self.style.SUCCESS('✓ Bootstrap complete - AI Fitness Coach ready!'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠ Bootstrap failed: {e}'))
                    self.stderr.write(traceback.format_exc())
                    # Don't fail deployment - let startCommand handle it
                        
                self.stdout.write(self.style.SUCCESS('=== Database setup complete ==='))
            else:
                self.stdout.write(self.style.SUCCESS('=== Database already set up ==='))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database setup failed: {e}'))
            raise
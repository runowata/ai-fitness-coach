from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
import logging

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
                
                # Load fixtures
                fixtures = [
                    'fixtures/exercises.json',
                    'fixtures/onboarding_questions.json', 
                    'fixtures/motivational_cards.json',
                    'fixtures/stories.json',
                    'fixtures/video_clips.json',
                    'fixtures/achievements.json'
                ]
                
                for fixture in fixtures:
                    try:
                        self.stdout.write(f'Loading {fixture}...')
                        call_command('loaddata', fixture)
                        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {fixture}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'⚠ Failed to load {fixture}: {e}'))
                        # Continue with other fixtures - some may succeed
                        
                self.stdout.write(self.style.SUCCESS('=== Database setup complete ==='))
            else:
                self.stdout.write(self.style.SUCCESS('=== Database already set up ==='))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Database setup failed: {e}'))
            raise
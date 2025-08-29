"""
Management command to fix CSV exercises table issues
Ensures table exists properly through Django migrations
"""
from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fix csv_exercises table to work with Django migrations'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'csv_exercises'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if table_exists:
                # Check if it has Django migration tracking
                cursor.execute("""
                    SELECT COUNT(*) FROM django_migrations 
                    WHERE app = 'workouts' AND name = '0001_initial';
                """)
                migration_recorded = cursor.fetchone()[0] > 0
                
                if not migration_recorded:
                    # Table exists but migration not recorded - this is the problem!
                    self.stdout.write(
                        self.style.WARNING(
                            'Table csv_exercises exists but migration not recorded. '
                            'Recording migration as applied...'
                        )
                    )
                    
                    # Mark migration as applied without running it
                    cursor.execute("""
                        INSERT INTO django_migrations (app, name, applied) 
                        VALUES ('workouts', '0001_initial', NOW())
                        ON CONFLICT (app, name) DO NOTHING;
                    """)
                    
                    self.stdout.write(
                        self.style.SUCCESS('✅ Migration tracking fixed')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS('✅ Table and migrations are in sync')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        'Table does not exist. Run migrations to create it.'
                    )
                )
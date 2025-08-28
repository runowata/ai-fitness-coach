"""
Management command to safely drop only workouts app tables.
Used for clean reset when migration conflicts occur.

Usage:
    python manage.py drop_workouts_tables [--dry-run]
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Safely drop all tables belonging to workouts app'
    
    # Tables that belong to workouts app (from migrations)
    WORKOUTS_TABLES = [
        'daily_workouts',
        'video_clips', 
        'csv_exercises',
        'explainer_videos',
        'final_videos',
        'weekly_lessons',
        'weekly_notifications',
        'weekly_themes',
        'workout_plans',
        'workout_executions',
        'exercises',  # legacy table from 0001_initial
    ]
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what tables would be dropped without actually dropping them'
        )
        parser.add_argument(
            '--force',
            action='store_true', 
            help='Skip confirmation prompt (use with caution)'
        )
    
    def handle(self, *args, **options):
        if settings.DEBUG:
            self.stdout.write(
                self.style.WARNING("Running in DEBUG mode - this is safe for development")
            )
        else:
            self.stdout.write(
                self.style.WARNING("WARNING: This will DROP TABLES in production!")
            )
            if not options['force']:
                confirm = input("Are you sure? Type 'yes' to continue: ")
                if confirm != 'yes':
                    self.stdout.write("Aborted.")
                    return
        
        with connection.cursor() as cursor:
            # Check which tables actually exist
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = CURRENT_SCHEMA() 
                AND table_name = ANY(%s)
                ORDER BY table_name
            """, [self.WORKOUTS_TABLES])
            
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            if not existing_tables:
                self.stdout.write(self.style.SUCCESS("No workouts tables found to drop."))
                return
            
            self.stdout.write(f"Found {len(existing_tables)} workouts tables:")
            for table in existing_tables:
                self.stdout.write(f"  - {table}")
            
            if options['dry_run']:
                self.stdout.write(self.style.WARNING("DRY RUN - would drop these tables:"))
                for table in existing_tables:
                    self.stdout.write(f"  DROP TABLE IF EXISTS {table} CASCADE;")
                return
            
            # Drop tables with CASCADE to handle foreign keys
            dropped_count = 0
            for table in existing_tables:
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
                    self.stdout.write(f"✓ Dropped table: {table}")
                    dropped_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"✗ Failed to drop {table}: {e}")
                    )
            
            # Clean up sequences that might remain
            cursor.execute("""
                SELECT sequence_name 
                FROM information_schema.sequences 
                WHERE sequence_schema = CURRENT_SCHEMA() 
                AND sequence_name LIKE ANY(ARRAY['%video_clips%', '%csv_exercises%', '%daily_workouts%', '%workout_%'])
            """)
            
            sequences = [row[0] for row in cursor.fetchall()]
            for seq in sequences:
                try:
                    cursor.execute(f"DROP SEQUENCE IF EXISTS {seq} CASCADE")
                    self.stdout.write(f"✓ Dropped sequence: {seq}")
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"Could not drop sequence {seq}: {e}")
                    )
            
            self.stdout.write(
                self.style.SUCCESS(f"\n🎉 Successfully dropped {dropped_count} workouts tables")
            )
            self.stdout.write(
                self.style.SUCCESS("Next steps:")
            )
            self.stdout.write("1. python manage.py migrate workouts --noinput")
            self.stdout.write("2. python manage.py setup_v2_production --force-download")
            self.stdout.write("3. python manage.py audit_video_clips --summary")
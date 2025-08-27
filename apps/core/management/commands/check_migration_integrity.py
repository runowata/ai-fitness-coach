"""
Migration integrity checker - detects fake migrations without actual database tables.
Prevents deployment with broken migration state.

Usage:
    python manage.py check_migration_integrity [--app workouts]
    
Exit codes:
    0 - All migrations integrity OK
    1 - Found integrity issues (fake migrations without tables)
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.apps import apps
from django.conf import settings


class Command(BaseCommand):
    help = 'Check migration integrity - detect fake migrations without actual tables'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--app',
            help='Check specific app only (e.g. workouts)',
            default=None
        )
        parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='Exit on first integrity issue found'
        )
    
    def handle(self, *args, **options):
        loader = MigrationLoader(connection)
        issues_found = 0
        
        # Get apps to check
        if options['app']:
            apps_to_check = [options['app']]
        else:
            apps_to_check = ['workouts', 'users', 'onboarding', 'achievements']
        
        self.stdout.write("🔍 Checking migration integrity...\n")
        
        for app_name in apps_to_check:
            if app_name not in loader.migrated_apps:
                self.stdout.write(f"⚠️  App {app_name} has no migrations recorded")
                continue
                
            issues = self.check_app_integrity(app_name, loader)
            if issues:
                issues_found += len(issues)
                self.stdout.write(
                    self.style.ERROR(f"\n❌ Found {len(issues)} integrity issues in {app_name}:")
                )
                for issue in issues:
                    self.stdout.write(f"   • {issue}")
                    
                if options['fail_fast']:
                    raise CommandError(f"Migration integrity check failed for {app_name}")
            else:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ {app_name}: migration integrity OK")
                )
        
        if issues_found:
            self.stdout.write(
                self.style.ERROR(f"\n🚨 Found {issues_found} total integrity issues!")
            )
            self.stdout.write("\nRecommended fix:")
            self.stdout.write("1. python manage.py drop_workouts_tables --dry-run")
            self.stdout.write("2. python manage.py drop_workouts_tables")  
            self.stdout.write("3. python manage.py migrate workouts --noinput")
            self.stdout.write("4. python manage.py setup_v2_production")
            
            raise CommandError("Migration integrity check FAILED - deployment blocked")
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 All migration integrity checks passed!")
        )
    
    def check_app_integrity(self, app_name, loader):
        """Check integrity for specific app"""
        issues = []
        
        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            return [f"App {app_name} not found"]
        
        # Get applied migrations for this app
        applied_migrations = loader.applied_migrations
        app_applied = {key for key in applied_migrations if key[0] == app_name}
        
        if not app_applied:
            return []  # No migrations applied, nothing to check
        
        # Get models that should have been created by migrations
        models = app_config.get_models()
        expected_tables = set()
        
        for model in models:
            if hasattr(model._meta, 'db_table'):
                expected_tables.add(model._meta.db_table)
            else:
                # Default Django table naming
                expected_tables.add(f"{app_name}_{model._meta.model_name}")
        
        # Check if these tables actually exist
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = CURRENT_SCHEMA()
                AND table_name = ANY(%s)
            """, [list(expected_tables)])
            
            existing_tables = {row[0] for row in cursor.fetchall()}
        
        # Find missing tables
        missing_tables = expected_tables - existing_tables
        
        if missing_tables:
            issues.append(
                f"Missing tables: {', '.join(sorted(missing_tables))} "
                f"(migrations applied: {len(app_applied)}, but tables missing)"
            )
            
            # Special check for workouts app video_clips table
            if app_name == 'workouts' and 'video_clips' in missing_tables:
                issues.append(
                    "video_clips table missing - likely caused by --fake migrations. "
                    "Use drop_workouts_tables command to fix."
                )
        
        return issues
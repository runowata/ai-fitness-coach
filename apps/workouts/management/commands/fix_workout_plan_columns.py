"""
Management command to fix missing workout_plans columns in production
"""
from django.core.management.base import BaseCommand
from django.db import connection, transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Fix missing columns in workout_plans table'
    
    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
        parser.add_argument('--force', action='store_true', help='Force execution even if columns exist')
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        # Get database-specific SQL commands
        db_vendor = connection.vendor
        
        if db_vendor == 'postgresql':
            sql_commands = [
                # Add goal column if missing
                """
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='workout_plans' AND column_name='goal') THEN
                        ALTER TABLE workout_plans ADD COLUMN goal VARCHAR(200) DEFAULT 'Персональный план тренировок';
                        UPDATE workout_plans SET goal = 'Персональный план тренировок' WHERE goal IS NULL;
                        ALTER TABLE workout_plans ALTER COLUMN goal SET NOT NULL;
                    END IF;
                END $$;
                """,
                
                # Add description column if missing
                """
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='workout_plans' AND column_name='description') THEN
                        ALTER TABLE workout_plans ADD COLUMN description TEXT DEFAULT '';
                        ALTER TABLE workout_plans ALTER COLUMN description SET NOT NULL;
                    END IF;
                END $$;
                """,
                
                # Add motivation_text column if missing
                """
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='workout_plans' AND column_name='motivation_text') THEN
                        ALTER TABLE workout_plans ADD COLUMN motivation_text TEXT DEFAULT '';
                        ALTER TABLE workout_plans ALTER COLUMN motivation_text SET NOT NULL;
                    END IF;
                END $$;
                """,
                
                # Add user_analysis column if missing
                """
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='workout_plans' AND column_name='user_analysis') THEN
                        ALTER TABLE workout_plans ADD COLUMN user_analysis JSONB DEFAULT '{}';
                        ALTER TABLE workout_plans ALTER COLUMN user_analysis SET NOT NULL;
                    END IF;
                END $$;
                """,
                
                # Add long_term_strategy column if missing
                """
                DO $$ 
                BEGIN 
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                  WHERE table_name='workout_plans' AND column_name='long_term_strategy') THEN
                        ALTER TABLE workout_plans ADD COLUMN long_term_strategy JSONB DEFAULT '{}';
                        ALTER TABLE workout_plans ALTER COLUMN long_term_strategy SET NOT NULL;
                    END IF;
                END $$;
                """,
            ]
        else:
            # SQLite - simpler approach, just try to add columns (will fail silently if exists)
            sql_commands = [
                "ALTER TABLE workout_plans ADD COLUMN goal VARCHAR(200) DEFAULT 'Персональный план тренировок';",
                "ALTER TABLE workout_plans ADD COLUMN description TEXT DEFAULT '';",
                "ALTER TABLE workout_plans ADD COLUMN motivation_text TEXT DEFAULT '';",
                "ALTER TABLE workout_plans ADD COLUMN user_analysis TEXT DEFAULT '{}';",  # SQLite uses TEXT instead of JSONB
                "ALTER TABLE workout_plans ADD COLUMN long_term_strategy TEXT DEFAULT '{}';",
            ]
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            
        # Check current table schema (database agnostic)
        db_vendor = connection.vendor
        self.stdout.write(f'Database vendor: {db_vendor}')
        
        if db_vendor == 'postgresql':
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = 'workout_plans'
                    ORDER BY ordinal_position
                """)
                
                current_columns = cursor.fetchall()
                self.stdout.write('Current workout_plans table structure:')
                for col_name, data_type, is_nullable, default in current_columns:
                    self.stdout.write(f'  - {col_name}: {data_type} (nullable: {is_nullable}, default: {default})')
        else:
            # For SQLite, use PRAGMA
            with connection.cursor() as cursor:
                cursor.execute("PRAGMA table_info(workout_plans)")
                current_columns = cursor.fetchall()
                self.stdout.write('Current workout_plans table structure:')
                for cid, name, type_name, notnull, default_value, pk in current_columns:
                    nullable = "NO" if notnull else "YES"
                    self.stdout.write(f'  - {name}: {type_name} (nullable: {nullable}, default: {default_value})')
        
        # Execute SQL commands
        if not dry_run:
            try:
                with connection.cursor() as cursor:
                    for i, sql_command in enumerate(sql_commands, 1):
                        self.stdout.write(f'Executing SQL command {i}/{len(sql_commands)}...')
                        try:
                            cursor.execute(sql_command)
                            self.stdout.write(self.style.SUCCESS(f'✓ Command {i} executed successfully'))
                        except Exception as cmd_error:
                            if "duplicate column name" in str(cmd_error).lower() or "already exists" in str(cmd_error).lower():
                                self.stdout.write(self.style.WARNING(f'⚠ Command {i}: Column already exists (skipping)'))
                            else:
                                raise cmd_error
                
                self.stdout.write(self.style.SUCCESS('All database schema fixes applied successfully!'))
                
                # Verify changes (database specific)
                if db_vendor == 'postgresql':
                    with connection.cursor() as cursor:
                        cursor.execute("""
                            SELECT column_name, data_type, is_nullable, column_default
                            FROM information_schema.columns 
                            WHERE table_name = 'workout_plans'
                            AND column_name IN ('goal', 'description', 'motivation_text', 'user_analysis', 'long_term_strategy')
                            ORDER BY column_name
                        """)
                        
                        new_columns = cursor.fetchall()
                        if new_columns:
                            self.stdout.write('\nVerification - Added columns:')
                            for col_name, data_type, is_nullable, default in new_columns:
                                self.stdout.write(f'  ✓ {col_name}: {data_type} (nullable: {is_nullable})')
                else:
                    # SQLite verification
                    with connection.cursor() as cursor:
                        cursor.execute("PRAGMA table_info(workout_plans)")
                        all_columns = cursor.fetchall()
                        target_columns = {'goal', 'description', 'motivation_text', 'user_analysis', 'long_term_strategy'}
                        found_columns = []
                        
                        for cid, name, type_name, notnull, default_value, pk in all_columns:
                            if name in target_columns:
                                found_columns.append((name, type_name, not notnull, default_value))
                        
                        if found_columns:
                            self.stdout.write('\nVerification - Added columns:')
                            for col_name, data_type, is_nullable, default in found_columns:
                                self.stdout.write(f'  ✓ {col_name}: {data_type} (nullable: {is_nullable})')
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error applying database fixes: {str(e)}'))
                raise
        else:
            self.stdout.write('SQL commands that would be executed:')
            for i, sql_command in enumerate(sql_commands, 1):
                self.stdout.write(f'\n--- Command {i} ---')
                self.stdout.write(sql_command.strip())
        
        self.stdout.write(
            self.style.SUCCESS(
                '\n🎯 Next steps:\n'
                '1. Run: python manage.py complete_onboarding_auto --archetype mentor\n'
                '2. Test: /onboarding/generate/ endpoint\n'
                '3. Verify: Full user journey from registration to workout completion'
            )
        )
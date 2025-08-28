#!/usr/bin/env python3
"""
Management command to create csv_exercises table
"""
from django.core.management.base import BaseCommand
from django.db import connection
from apps.workouts.models import CSVExercise


class Command(BaseCommand):
    help = 'Create csv_exercises table if it does not exist'

    def handle(self, *args, **options):
        cursor = connection.cursor()
        
        try:
            # Check if table exists
            tables = connection.introspection.table_names()
            
            if 'csv_exercises' not in tables:
                self.stdout.write('Creating csv_exercises table...')
                
                # Use Django ORM to create the table
                with connection.schema_editor() as schema_editor:
                    schema_editor.create_model(CSVExercise)
                
                self.stdout.write(
                    self.style.SUCCESS('✅ csv_exercises table created successfully')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('csv_exercises table already exists')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'ORM creation failed: {e}')
            )
            
            # Fallback to raw SQL
            try:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS csv_exercises (
                        id VARCHAR(20) PRIMARY KEY,
                        name_ru VARCHAR(120) NOT NULL,
                        name_en VARCHAR(120) DEFAULT '',
                        description TEXT DEFAULT '',
                        level VARCHAR(20) DEFAULT 'beginner',
                        muscle_group VARCHAR(120) DEFAULT '',
                        exercise_type VARCHAR(120) DEFAULT '',
                        ai_tags JSONB DEFAULT '[]'::jsonb,
                        r2_slug VARCHAR(50) DEFAULT '',
                        is_active BOOLEAN DEFAULT true,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
                    );
                ''')
                
                self.stdout.write(
                    self.style.SUCCESS('✅ csv_exercises table created via SQL')
                )
                
            except Exception as sql_error:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create table: {sql_error}')
                )
                raise
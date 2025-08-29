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
        
        # First, try to create table with IF NOT EXISTS via SQL
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS csv_exercises (
                    id VARCHAR(20) PRIMARY KEY,
                    name_ru VARCHAR(120) NOT NULL,
                    description TEXT DEFAULT ''
                );
            ''')
            
            # Check if table was created or already existed
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'csv_exercises'
                );
            """)
            exists = cursor.fetchone()[0]
            
            if exists:
                self.stdout.write(
                    self.style.SUCCESS('✅ csv_exercises table is ready')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to verify csv_exercises table')
                )
                
        except Exception as e:
            # If the error is about table already existing, that's fine
            if 'already exists' in str(e).lower():
                self.stdout.write(
                    self.style.SUCCESS('✅ csv_exercises table already exists')
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f'Failed to create table: {e}')
                )
                raise
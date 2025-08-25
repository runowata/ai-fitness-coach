#!/usr/bin/env python3
"""
Management command to import exercises from R2 structure CSV
"""
import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.workouts.models import CSVExercise, VideoClip


class Command(BaseCommand):
    help = 'Import exercises from exercises_complete_r2.csv and create video clips'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='data/clean/exercises_complete_r2.csv',
            help='CSV file to import (default: data/clean/exercises_complete_r2.csv)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing CSVExercise records before import'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )

    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.verbose = options['verbose']
        csv_file = options['csv_file']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        # Check if CSV file exists
        csv_path = Path(csv_file)
        if not csv_path.exists():
            raise CommandError(f'CSV file not found: {csv_file}')
        
        try:
            with transaction.atomic():
                if options['clear_existing']:
                    self._clear_existing_data()
                
                self._import_exercises(csv_path)
            
            self.stdout.write(self.style.SUCCESS('✅ R2 exercise import completed successfully'))
            
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'❌ Import failed: {e}'))
            raise CommandError(f'Import failed: {e}')

    def _clear_existing_data(self):
        """Clear existing CSVExercise records"""
        if not self.dry_run:
            self.stdout.write('🗑️  Clearing existing CSVExercise records...')
            count = CSVExercise.objects.count()
            CSVExercise.objects.all().delete()
            self.stdout.write(f'   Deleted {count} existing records')
        else:
            count = CSVExercise.objects.count()
            self.stdout.write(f'🗑️  Would delete {count} existing CSVExercise records')

    def _import_exercises(self, csv_path: Path):
        """Import exercises from CSV file"""
        self.stdout.write(f'📋 Reading exercises from: {csv_path}')
        
        created_count = 0
        updated_count = 0
        error_count = 0
        
        with open(csv_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    exercise_data = self._parse_csv_row(row)
                    
                    if self.dry_run:
                        self.stdout.write(f"   Would create: {exercise_data['id']}")
                        created_count += 1
                    else:
                        exercise, created = CSVExercise.objects.update_or_create(
                            id=exercise_data['id'],
                            defaults=exercise_data
                        )
                        
                        if created:
                            created_count += 1
                            if self.verbose:
                                self.stdout.write(f"✅ Created: {exercise.id} - {exercise.name_ru}")
                        else:
                            updated_count += 1
                            if self.verbose:
                                self.stdout.write(f"🔄 Updated: {exercise.id} - {exercise.name_ru}")
                
                except Exception as e:
                    error_count += 1
                    self.stderr.write(f"❌ Error in row {row_num}: {e}")
                    if self.verbose:
                        self.stderr.write(f"   Row data: {row}")
        
        # Summary
        self.stdout.write(f'\n📊 IMPORT SUMMARY:')
        self.stdout.write(f'   Created: {created_count} exercises')
        self.stdout.write(f'   Updated: {updated_count} exercises')
        self.stdout.write(f'   Errors: {error_count} rows')
        
        # Show breakdown by category
        if not self.dry_run and created_count > 0:
            self._show_category_breakdown()

    def _parse_csv_row(self, row: dict) -> dict:
        """Parse CSV row into exercise data"""
        
        # Parse AI tags from JSON string
        ai_tags = []
        if row.get('ai_tags'):
            try:
                ai_tags = json.loads(row['ai_tags'])
                if not isinstance(ai_tags, list):
                    ai_tags = [str(ai_tags)]
            except (json.JSONDecodeError, TypeError):
                # If parsing fails, treat as single tag
                ai_tags = [row['ai_tags']]
        
        # Determine category from ID pattern
        exercise_id = row['id']
        category = 'unknown'
        if exercise_id.startswith('warmup_'):
            category = 'warmup'
        elif exercise_id.startswith('main_'):
            category = 'main'
        elif exercise_id.startswith('endurance_'):
            category = 'endurance'
        elif exercise_id.startswith('relaxation_'):
            category = 'relaxation'
        
        return {
            'id': exercise_id,
            'name_ru': row.get('name_ru', '').strip(),
            'name_en': row.get('name_en', '').strip(),
            'description': row.get('description', '').strip(),
            'level': row.get('level', 'intermediate').strip(),
            'muscle_group': row.get('muscle_group', '').strip(),
            'exercise_type': row.get('exercise_type', 'strength').strip(),
            'category': category,
            'ai_tags': ai_tags,
            'r2_slug': exercise_id,  # Store original R2 slug
            'is_active': True
        }

    def _show_category_breakdown(self):
        """Show breakdown of exercises by category"""
        from django.db.models import Count
        
        self.stdout.write(f'\n📊 CATEGORY BREAKDOWN:')
        
        breakdown = CSVExercise.objects.values('category').annotate(
            count=Count('id')
        ).order_by('category')
        
        total = 0
        for item in breakdown:
            category = item['category'] or 'unknown'
            count = item['count']
            total += count
            self.stdout.write(f'   {category}: {count} exercises')
        
        self.stdout.write(f'   TOTAL: {total} exercises')
        
        # Show exercise type breakdown too
        self.stdout.write(f'\n📊 EXERCISE TYPE BREAKDOWN:')
        
        type_breakdown = CSVExercise.objects.values('exercise_type').annotate(
            count=Count('id')
        ).order_by('exercise_type')
        
        for item in type_breakdown:
            exercise_type = item['exercise_type'] or 'unknown'
            count = item['count']
            self.stdout.write(f'   {exercise_type}: {count} exercises')
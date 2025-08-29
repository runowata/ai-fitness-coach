"""
Management command to load exercises with R2-compatible IDs
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import CSVExercise
import pandas as pd
import os


class Command(BaseCommand):
    help = 'Load exercises with R2-compatible IDs (warmup_01, main_001, etc)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing exercises before loading',
        )

    def handle(self, *args, **options):
        if options['clear']:
            CSVExercise.objects.all().delete()
            self.stdout.write("🗑️ Cleared all existing exercises")
        
        self.stdout.write("📥 Loading exercises with R2-compatible IDs...")
        
        # Load Excel file
        excel_path = 'data/raw/base_exercises.xlsx'
        if not os.path.exists(excel_path):
            self.stdout.write(
                self.style.ERROR(f"File not found: {excel_path}")
            )
            return
        
        df = pd.read_excel(excel_path)
        
        # Mapping from Excel IDs to R2 format
        id_mapping = {
            'WZ': 'warmup',      # WZ001 -> warmup_01
            'MN': 'main',        # MN001 -> main_001
            'EN': 'endurance',   # EN001 -> endurance_01
            'RL': 'relaxation',  # RL001 -> relaxation_01
        }
        
        created_count = 0
        skipped_count = 0
        
        with transaction.atomic():
            for _, row in df.iterrows():
                old_id = str(row['ID']).strip()
                
                # Convert ID to R2 format
                prefix = old_id[:2]
                if prefix in id_mapping:
                    number = old_id[2:].lstrip('0') or '0'
                    number_int = int(number)
                    
                    if prefix == 'WZ':  # warmup_01 to warmup_20
                        if number_int > 20:
                            skipped_count += 1
                            continue
                        new_id = f"warmup_{number_int:02d}"
                    elif prefix == 'MN':  # main_001 to main_100
                        if number_int > 100:
                            skipped_count += 1
                            continue
                        new_id = f"main_{number_int:03d}"
                    elif prefix == 'EN':  # endurance_01 to endurance_30
                        if number_int > 30:
                            skipped_count += 1
                            continue
                        new_id = f"endurance_{number_int:02d}"
                    elif prefix == 'RL':  # relaxation_01 to relaxation_30
                        if number_int > 30:
                            skipped_count += 1
                            continue
                        new_id = f"relaxation_{number_int:02d}"
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Unknown prefix for ID: {old_id}")
                    )
                    skipped_count += 1
                    continue
                
                # Create or update exercise
                exercise, created = CSVExercise.objects.update_or_create(
                    id=new_id,
                    defaults={
                        'name_ru': str(row.get('Название (RU)', '')).strip(),
                        'description': str(row.get('Краткое описание', '')).strip() or '',
                    }
                )
                
                if created:
                    created_count += 1
                    self.stdout.write(f"✅ Created: {new_id} - {exercise.name_ru}")
        
        # Add missing exercises with placeholder data
        self.stdout.write("\n📝 Adding missing exercises with placeholders...")
        placeholder_count = 0
        
        with transaction.atomic():
            # Warmup (20 exercises)
            for i in range(1, 21):
                exercise_id = f"warmup_{i:02d}"
                if not CSVExercise.objects.filter(id=exercise_id).exists():
                    CSVExercise.objects.create(
                        id=exercise_id,
                        name_ru=f"Разминка {i}",
                        description=f"Упражнение для разминки #{i}"
                    )
                    placeholder_count += 1
            
            # Main (100 exercises)
            for i in range(1, 101):
                exercise_id = f"main_{i:03d}"
                if not CSVExercise.objects.filter(id=exercise_id).exists():
                    CSVExercise.objects.create(
                        id=exercise_id,
                        name_ru=f"Основное упражнение {i}",
                        description=f"Основное упражнение #{i}"
                    )
                    placeholder_count += 1
            
            # Endurance (30 exercises)
            for i in range(1, 31):
                exercise_id = f"endurance_{i:02d}"
                if not CSVExercise.objects.filter(id=exercise_id).exists():
                    CSVExercise.objects.create(
                        id=exercise_id,
                        name_ru=f"Выносливость {i}",
                        description=f"Упражнение на выносливость #{i}"
                    )
                    placeholder_count += 1
            
            # Relaxation (30 exercises)
            for i in range(1, 31):
                exercise_id = f"relaxation_{i:02d}"
                if not CSVExercise.objects.filter(id=exercise_id).exists():
                    CSVExercise.objects.create(
                        id=exercise_id,
                        name_ru=f"Расслабление {i}",
                        description=f"Упражнение для расслабления #{i}"
                    )
                    placeholder_count += 1
        
        # Summary
        total = CSVExercise.objects.count()
        self.stdout.write("\n" + "="*50)
        self.stdout.write(f"✅ Created from Excel: {created_count}")
        self.stdout.write(f"✅ Created placeholders: {placeholder_count}")
        self.stdout.write(f"⚠️ Skipped: {skipped_count}")
        self.stdout.write(f"📊 Total exercises in DB: {total}")
        
        # Verify
        self.stdout.write("\n🔍 Verification:")
        for video_type in ['warmup', 'main', 'endurance', 'relaxation']:
            count = CSVExercise.objects.filter(id__startswith=f"{video_type}_").count()
            self.stdout.write(f"  {video_type}: {count} exercises")
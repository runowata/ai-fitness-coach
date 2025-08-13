"""
V2 Import command for exercises and video clips from Excel files
Supports new archetype naming: peer/professional/mentor
Maps Excel exercise IDs to R2 technical names
"""
import json
import os
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction

# Import archetype mapping from core constants
from apps.core.constants import ARCHETYPE_MAPPING
from apps.workouts.models import CSVExercise, VideoClip

# R2 video kind mapping
VIDEO_KIND_MAPPING = {
    'instruction': 'instruction',
    'technique': 'technique', 
    'mistake': 'mistake',
    'reminder': 'reminder',
    'motivation': 'motivation'
}

class Command(BaseCommand):
    help = "Import exercises and video clips from Excel files (v2 compatible)"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.excel_r2_mapping = self._load_excel_r2_mapping()
    
    def _load_excel_r2_mapping(self):
        """Load mapping between Excel IDs and R2 technical names"""
        mapping_path = os.path.join(os.path.dirname(__file__), '../../../../excel_r2_mapping.json')
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r') as f:
                return json.load(f)
        return {}
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--data-dir',
            type=str,
            default='./data/raw',
            help='Directory containing Excel files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without making changes'
        )
        parser.add_argument(
            '--force',
            action='store_true', 
            help='Overwrite existing exercises and clips'
        )

    def handle(self, *args, **options):
        data_dir = Path(options['data_dir'])
        dry_run = options['dry_run']
        force = options['force']
        
        if not data_dir.exists():
            self.stdout.write(self.style.ERROR(f"Data directory not found: {data_dir}"))
            return
            
        self.stdout.write(f"🔍 Scanning {data_dir} for Excel files...")
        
        # Step 1: Import base exercises
        base_exercises_file = data_dir / 'base_exercises.xlsx'
        if base_exercises_file.exists():
            self.import_base_exercises(base_exercises_file, dry_run, force)
        else:
            self.stdout.write(self.style.WARNING("⚠️  base_exercises.xlsx not found"))
            
        # Step 2: Import video clips for each archetype
        video_files = list(data_dir.glob('explainer_videos_*.xlsx'))
        for video_file in video_files:
            self.import_video_clips(video_file, dry_run, force)
            
        # Step 2.5: Create placeholder clips for R2 exercises with mapping
        if not dry_run:
            self.create_r2_placeholder_clips(force)
            
        # Step 3: Summary
        if not dry_run:
            exercises_count = CSVExercise.objects.filter(is_active=True).count()
            clips_count = VideoClip.objects.filter(is_active=True, r2_file__isnull=False).count()
            
            self.stdout.write(self.style.SUCCESS(f"\n🎉 Import complete!"))
            self.stdout.write(f"  📊 {exercises_count} exercises imported")
            self.stdout.write(f"  🎥 {clips_count} video clips imported")

    def import_base_exercises(self, file_path, dry_run, force):
        """Import exercises from base_exercises.xlsx"""
        self.stdout.write(f"\n📋 Importing exercises from {file_path.name}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Map actual Excel columns to our expected fields
            required_excel_cols = ['ID', 'Название (RU)', 'Название (EN)']
            missing_cols = [col for col in required_excel_cols if col not in df.columns]
            if missing_cols:
                self.stdout.write(self.style.ERROR(f"Missing columns: {missing_cols}. Available: {list(df.columns)}"))
                return
                
            created_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                if pd.isna(row['ID']) or pd.isna(row['Название (RU)']):
                    continue
                    
                # Map difficulty level from Russian to English
                difficulty_map = {
                    'Начальный': 'beginner',
                    'Средний': 'intermediate', 
                    'Продвинутый': 'advanced'
                }
                
                level = str(row.get('Сложность', 'Начальный')).strip()
                level_en = difficulty_map.get(level, 'beginner')
                
                exercise_id = str(row['ID']).strip()
                
                # Get R2 technical name if mapping exists
                r2_technical_name = self.excel_r2_mapping.get(exercise_id, '')
                
                exercise_data = {
                    'name_ru': str(row['Название (RU)']).strip(),
                    'name_en': str(row['Название (EN)']).strip(),
                    'muscle_group': str(row.get('Основная мышечная группа', '')).strip(),
                    'exercise_type': str(row.get('Тип упражнения', '')).strip(),
                    'level': level_en,
                    'duration_seconds': 30,  # Default duration
                    'is_active': True
                }
                
                if dry_run:
                    r2_info = f" -> R2: {r2_technical_name}" if r2_technical_name else " (no R2 mapping)"
                    self.stdout.write(f"  Would create/update: {exercise_id} - {exercise_data['name_ru']}{r2_info}")
                    continue
                    
                with transaction.atomic():
                    exercise, created = CSVExercise.objects.update_or_create(
                        id=exercise_id,
                        defaults=exercise_data
                    )
                    
                    if created:
                        created_count += 1
                        r2_info = f" -> R2: {r2_technical_name}" if r2_technical_name else " (no R2 mapping)"
                        self.stdout.write(f"  ✅ Created: {exercise_id} - {exercise_data['name_ru']}{r2_info}")
                    else:
                        updated_count += 1
                        if force:
                            self.stdout.write(f"  🔄 Updated: {exercise_id}")
                        else:
                            self.stdout.write(f"  ⏭️  Skipped existing: {exercise_id}")
                            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f"Exercises: {created_count} created, {updated_count} updated"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing exercises: {e}"))

    def import_video_clips(self, file_path, dry_run, force):
        """Import video clips from explainer_videos_*.xlsx"""
        # Extract archetype from filename
        archetype_key = None
        for key in ARCHETYPE_MAPPING.keys():
            if key in file_path.name:
                archetype_key = key
                break
                
        if not archetype_key:
            self.stdout.write(self.style.WARNING(f"⚠️  Unknown archetype in {file_path.name}"))
            return
            
        archetype = ARCHETYPE_MAPPING[archetype_key]
        self.stdout.write(f"\n🎥 Importing {archetype} videos from {file_path.name}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Expected columns (adjust based on your Excel structure)
            required_cols = ['exercise_slug', 'video_kind', 'r2_path']  
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.stdout.write(self.style.ERROR(f"Missing columns: {missing_cols}. Available: {list(df.columns)}"))
                return
                
            created_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                if pd.isna(row['ID']):
                    continue
                    
                exercise_id = str(row['ID']).strip()
                
                # For instruction videos, we create instruction type clips
                video_kind = 'instruction'
                
                # Find the exercise
                try:
                    exercise = CSVExercise.objects.get(id=exercise_id)
                except CSVExercise.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Exercise not found: {exercise_id}"))
                    continue
                
                # Get instruction script from Excel
                script_column = [col for col in df.columns if 'Скрипт' in col]
                instruction_script = ''
                if script_column:
                    instruction_script = str(row.get(script_column[0], '')).strip()
                
                clip_data = {
                    'archetype': archetype,
                    'r2_kind': video_kind,
                    'model_name': 'default',
                    'reminder_text': instruction_script[:500],  # Limit text length
                    'duration_seconds': 60,
                    'is_active': True,
                    'is_placeholder': True  # Mark as placeholder since no R2 files yet
                }
                
                if dry_run:
                    self.stdout.write(f"  Would create: {exercise_id} - {video_kind} - {archetype}")
                    continue
                    
                with transaction.atomic():
                    clip, created = VideoClip.objects.update_or_create(
                        exercise=exercise,
                        r2_kind=video_kind,
                        archetype=archetype,
                        model_name=clip_data['model_name'],
                        defaults=clip_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"  ✅ Created: {exercise_id} - {video_kind} - {archetype}")
                    else:
                        updated_count += 1
                        if force:
                            self.stdout.write(f"  🔄 Updated: {exercise_id} - {video_kind}")
                        else:
                            self.stdout.write(f"  ⏭️  Skipped existing: {exercise_id} - {video_kind}")
                            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f"Video clips ({archetype}): {created_count} created, {updated_count} updated"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing video clips: {e}"))

    def create_r2_placeholder_clips(self, force):
        """Create placeholder video clips for exercises with R2 mapping"""
        self.stdout.write(f"\n🎥 Creating R2 placeholder clips...")
        
        created_count = 0
        
        # For each exercise with R2 mapping, create basic video clips
        for excel_id, r2_name in self.excel_r2_mapping.items():
            try:
                exercise = CSVExercise.objects.get(id=excel_id)
            except CSVExercise.DoesNotExist:
                continue
                
            # Create technique and instruction clips for each archetype
            archetypes = ['mentor', 'professional', 'peer']
            video_kinds = ['technique', 'instruction']
            
            for archetype in archetypes:
                for video_kind in video_kinds:
                    clip_data = {
                        'archetype': archetype,
                        'r2_kind': video_kind,
                        'model_name': 'default',
                        'reminder_text': f'{video_kind} for {exercise.name_en}',
                        'duration_seconds': 60,
                        'is_active': True,
                        'is_placeholder': True
                    }
                    
                    with transaction.atomic():
                        clip, created = VideoClip.objects.update_or_create(
                            exercise=exercise,
                            r2_kind=video_kind,
                            archetype=archetype,
                            model_name='default',
                            defaults=clip_data
                        )
                        
                        if created:
                            created_count += 1
                            # Construct R2 path based on mapping and pattern
                            r2_path = f"videos/exercises/{r2_name}_{video_kind}_m01.mp4"
                            clip.r2_file.name = r2_path
                            clip.save()
        
        self.stdout.write(self.style.SUCCESS(f"Created {created_count} R2 placeholder clips"))

    def _parse_muscle_groups(self, muscle_groups_str):
        """Parse muscle groups from string to JSON array"""
        if pd.isna(muscle_groups_str) or not muscle_groups_str:
            return []
        try:
            # If already JSON, return as-is
            if isinstance(muscle_groups_str, list):
                return muscle_groups_str
            # If string with commas, split
            if ',' in str(muscle_groups_str):
                return [g.strip() for g in str(muscle_groups_str).split(',')]
            # Single muscle group
            return [str(muscle_groups_str).strip()]
        except:
            return []
    
    def _parse_equipment(self, equipment_str):
        """Parse equipment from string to JSON array"""
        if pd.isna(equipment_str) or not equipment_str:
            return []
        try:
            if isinstance(equipment_str, list):
                return equipment_str
            if ',' in str(equipment_str):
                return [e.strip() for e in str(equipment_str).split(',')]
            return [str(equipment_str).strip()]
        except:
            return []
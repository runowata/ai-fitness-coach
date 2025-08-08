"""
V2 Import command for exercises and video clips from Excel files
Supports new archetype naming: peer/professional/mentor
"""
import pandas as pd
from django.core.management.base import BaseCommand
from django.db import transaction
from pathlib import Path
from apps.workouts.models import Exercise, VideoClip
import json

# New archetype mapping from Excel file names to v2 names
ARCHETYPE_MAPPING = {
    '111_nastavnik': 'mentor',      # Мудрый наставник
    '222_professional': 'professional',  # Успешный профессионал  
    '333_rovesnik': 'peer'          # Ровесник
}

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
            
        # Step 3: Summary
        if not dry_run:
            exercises_count = Exercise.objects.filter(is_active=True).count()
            clips_count = VideoClip.objects.filter(is_active=True, r2_file__isnull=False).count()
            
            self.stdout.write(self.style.SUCCESS(f"\n🎉 Import complete!"))
            self.stdout.write(f"  📊 {exercises_count} exercises imported")
            self.stdout.write(f"  🎥 {clips_count} video clips imported")

    def import_base_exercises(self, file_path, dry_run, force):
        """Import exercises from base_exercises.xlsx"""
        self.stdout.write(f"\n📋 Importing exercises from {file_path.name}")
        
        try:
            df = pd.read_excel(file_path)
            
            # Expected columns (adjust based on your actual Excel structure)
            required_cols = ['slug', 'name']
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                self.stdout.write(self.style.ERROR(f"Missing columns: {missing_cols}"))
                return
                
            created_count = 0
            updated_count = 0
            
            for _, row in df.iterrows():
                if pd.isna(row['slug']) or pd.isna(row['name']):
                    continue
                    
                exercise_data = {
                    'name': str(row['name']).strip(),
                    'muscle_groups': self._parse_muscle_groups(row.get('muscle_groups', '')),
                    'equipment_needed': self._parse_equipment(row.get('equipment', '')),
                    'difficulty': int(row.get('difficulty', 2)),
                    'duration_seconds': int(row.get('duration_seconds', 30)),
                    'is_active': True
                }
                
                slug = str(row['slug']).strip()
                
                if dry_run:
                    self.stdout.write(f"  Would create/update: {slug} - {exercise_data['name']}")
                    continue
                    
                with transaction.atomic():
                    exercise, created = Exercise.objects.update_or_create(
                        slug=slug,
                        defaults=exercise_data
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"  ✅ Created: {slug}")
                    else:
                        updated_count += 1
                        if force:
                            self.stdout.write(f"  🔄 Updated: {slug}")
                        else:
                            self.stdout.write(f"  ⏭️  Skipped existing: {slug}")
                            
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
                if pd.isna(row['exercise_slug']) or pd.isna(row['video_kind']):
                    continue
                    
                exercise_slug = str(row['exercise_slug']).strip()
                video_kind = str(row['video_kind']).strip().lower()
                r2_path = str(row.get('r2_path', '')).strip()
                
                # Map video kind to v2 format
                r2_kind = VIDEO_KIND_MAPPING.get(video_kind, video_kind)
                
                # Find the exercise
                try:
                    exercise = Exercise.objects.get(slug=exercise_slug)
                except Exercise.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f"  ⚠️  Exercise not found: {exercise_slug}"))
                    continue
                
                clip_data = {
                    'archetype': archetype,
                    'r2_kind': r2_kind,
                    'model_name': str(row.get('model_name', 'default')).strip(),
                    'reminder_text': str(row.get('reminder_text', '')).strip(),
                    'duration_seconds': int(row.get('duration_seconds', 60)),
                    'is_active': True,
                    'is_placeholder': False
                }
                
                if dry_run:
                    self.stdout.write(f"  Would create: {exercise_slug} - {r2_kind} - {archetype}")
                    continue
                    
                with transaction.atomic():
                    clip, created = VideoClip.objects.update_or_create(
                        exercise=exercise,
                        r2_kind=r2_kind,
                        archetype=archetype,
                        model_name=clip_data['model_name'],
                        reminder_text=clip_data['reminder_text'],
                        defaults=clip_data
                    )
                    
                    # Set R2 file path if provided
                    if r2_path and r2_path != 'nan':
                        clip.r2_file.name = r2_path
                        clip.save()
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f"  ✅ Created: {exercise_slug} - {r2_kind}")
                    else:
                        updated_count += 1
                        if force:
                            self.stdout.write(f"  🔄 Updated: {exercise_slug} - {r2_kind}")
                        else:
                            self.stdout.write(f"  ⏭️  Skipped existing: {exercise_slug} - {r2_kind}")
                            
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f"Video clips ({archetype}): {created_count} created, {updated_count} updated"))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error importing video clips: {e}"))

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
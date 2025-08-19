import os
import mimetypes
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from django.conf import settings

from apps.content.models import MediaAsset
from apps.workouts.models import Exercise


class Command(BaseCommand):
    help = 'Import media files from a local directory to cloud storage'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'source_dir',
            type=str,
            help='Path to directory containing media files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without actually importing'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Category for imported files',
            choices=[choice[0] for choice in MediaAsset.CATEGORY_CHOICES]
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing media assets before importing'
        )
    
    def handle(self, *args, **options):
        source_dir = Path(options['source_dir'])
        dry_run = options['dry_run']
        category = options.get('category')
        
        if not source_dir.exists():
            raise CommandError(f'Source directory does not exist: {source_dir}')
        
        if options['clear'] and not dry_run:
            self.stdout.write('Clearing existing media assets...')
            MediaAsset.objects.all().delete()
        
        self.stdout.write(f'{"[DRY RUN] " if dry_run else ""}Importing media from {source_dir}')
        
        imported = 0
        errors = 0
        
        for file_path in source_dir.rglob('*'):
            if file_path.is_file():
                try:
                    self._import_file(file_path, category, dry_run)
                    imported += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error importing {file_path}: {e}'))
                    errors += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'{"[DRY RUN] Would import" if dry_run else "Imported"} '
                f'{imported} files with {errors} errors'
            )
        )
    
    def _import_file(self, file_path, category, dry_run):
        """Import a single file"""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        if not mime_type:
            if dry_run:
                self.stdout.write(f'Skipping {file_path.name}: unknown file type')
            return
        
        # Determine asset type from mime type
        if mime_type.startswith('video/'):
            asset_type = 'video'
        elif mime_type.startswith('image/'):
            asset_type = 'image'
        elif mime_type.startswith('audio/'):
            asset_type = 'audio'
        else:
            if dry_run:
                self.stdout.write(f'Skipping {file_path.name}: unsupported type {mime_type}')
            return
        
        # Parse file name for metadata
        file_name = file_path.name
        parts = file_path.stem.split('_')
        
        # Try to determine category from path if not provided
        if not category:
            category = self._guess_category(file_path)
        
        # Extract metadata from filename
        metadata = self._parse_filename_metadata(file_path, category)
        
        if dry_run:
            self.stdout.write(
                f'Would import: {file_name} as {asset_type} in {category}'
                f'{f" (exercise: {metadata.get("exercise_slug")})" if metadata.get("exercise_slug") else ""}'
                f'{f" (archetype: {metadata.get("archetype")})" if metadata.get("archetype") else ""}'
            )
            return
        
        # Check if file already exists
        if MediaAsset.objects.filter(file_name=file_name).exists():
            self.stdout.write(f'Skipping {file_name}: already exists')
            return
        
        # Upload to storage
        try:
            with open(file_path, 'rb') as f:
                storage_path = f'{category}/{file_name}'  # Path without media/ prefix
                stored_path = default_storage.save(storage_path, f)
                
                # Store only the path, URL will be generated via media_service
                file_url = stored_path
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Upload failed for {file_name}: {e}'))
            return
        
        # Create MediaAsset record with path, not full URL
        asset = MediaAsset.objects.create(
            file_name=file_name,
            file_url=file_url,  # This is now a path, not a full URL
            file_size=file_path.stat().st_size,
            asset_type=asset_type,
            category=category,
            archetype=metadata.get('archetype', ''),
            tags=metadata.get('tags', [])
        )
        
        # Try to link to exercise if applicable
        if category.startswith('exercise_') and metadata.get('exercise_slug'):
            try:
                exercise = Exercise.objects.get(slug=metadata['exercise_slug'])
                asset.exercise = exercise
                asset.save()
            except Exercise.DoesNotExist:
                self.stdout.write(f'Warning: Exercise {metadata["exercise_slug"]} not found for {file_name}')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Imported: {file_name}'))
    
    def _guess_category(self, file_path):
        """Guess category from file path"""
        path_str = str(file_path).lower()
        
        if 'technique' in path_str:
            return 'exercise_technique'
        elif 'mistake' in path_str or 'error' in path_str:
            return 'exercise_mistake'
        elif 'instruction' in path_str:
            return 'exercise_instruction'
        elif 'reminder' in path_str:
            return 'exercise_reminder'
        elif 'weekly' in path_str:
            return 'motivation_weekly'
        elif 'final' in path_str or 'congratulation' in path_str:
            return 'motivation_final'
        elif 'card' in path_str:
            return 'card_background'
        elif 'avatar' in path_str:
            return 'avatar'
        elif 'story' in path_str and 'cover' in path_str:
            return 'story_cover'
        else:
            return 'exercise_technique'  # Default
    
    def _parse_filename_metadata(self, file_path, category):
        """Parse metadata from filename based on naming convention"""
        file_stem = file_path.stem
        parts = file_stem.split('_')
        metadata = {'tags': []}
        
        if category.startswith('exercise_'):
            # Format: {exercise_slug}_{type}_{archetype}_{model}.ext
            # Example: push-up_technique_mod1.mp4, push-up_instruction_bro_mod1.mp4
            if len(parts) >= 2:
                metadata['exercise_slug'] = parts[0]
                metadata['tags'].append(parts[1])  # technique, instruction, etc.
                
                # Look for archetype
                archetypes = ['bro', 'sergeant', 'intellectual']
                for part in parts:
                    if part in archetypes:
                        metadata['archetype'] = part
                        break
                        
        elif category == 'motivation_weekly':
            # Format: weekly_{archetype}_week{number}.mp4
            archetypes = ['bro', 'sergeant', 'intellectual']
            for part in parts:
                if part in archetypes:
                    metadata['archetype'] = part
                    break
            
        elif category == 'motivation_final':
            # Format: final_{archetype}.mp4
            archetypes = ['bro', 'sergeant', 'intellectual']
            for part in parts:
                if part in archetypes:
                    metadata['archetype'] = part
                    break
                    
        elif category == 'avatar':
            # Format: {archetype}_avatar_{number}.jpg
            archetypes = ['bro', 'sergeant', 'intellectual']
            for part in parts:
                if part in archetypes:
                    metadata['archetype'] = part
                    break
        
        return metadata
    
    def _extract_exercise_slug(self, file_path):
        """Try to extract exercise slug from file name"""
        # Expected format: {exercise_slug}_{type}_{archetype}.mp4
        parts = file_path.stem.split('_')
        if len(parts) >= 1:
            return parts[0]
        return None
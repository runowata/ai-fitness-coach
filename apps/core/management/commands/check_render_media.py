"""
Management command to check media files in Render storage and create VideoClip records
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import VideoClip, Exercise


class Command(BaseCommand):
    help = 'Check media files in Render storage and create VideoClip records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--media-path',
            type=str,
            default='/opt/render/project/src/media',
            help='Path to media directory on Render (default: /opt/render/project/src/media)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        media_path = Path(options['media_path'])
        
        self.stdout.write(f'Checking media files in: {media_path}')
        
        # Check if media directory exists
        if not media_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Media directory does not exist: {media_path}')
            )
            return
        
        # Check disk usage
        self.check_disk_usage(media_path)
        
        # List video files
        self.list_video_files(media_path)
        
        # Create VideoClip records for found files
        created_count = self.create_video_clips_from_files(media_path, dry_run)
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would create {created_count} VideoClip records'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {created_count} VideoClip records'
                )
            )

    def check_disk_usage(self, media_path):
        """Check disk usage of media directory"""
        try:
            # Get directory size (equivalent to du -sh)
            total_size = sum(
                os.path.getsize(os.path.join(dirpath, filename))
                for dirpath, dirnames, filenames in os.walk(media_path)
                for filename in filenames
            )
            
            # Convert to human readable format
            for unit in ['B', 'KB', 'MB', 'GB']:
                if total_size < 1024.0:
                    size_str = f"{total_size:.1f}{unit}"
                    break
                total_size /= 1024.0
            else:
                size_str = f"{total_size:.1f}TB"
            
            self.stdout.write(f'Media directory size: {size_str}')
            
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Could not check disk usage: {e}')
            )

    def list_video_files(self, media_path):
        """List all video files in media directory"""
        self.stdout.write('\nVideo files found:')
        
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        video_count = 0
        
        for root, dirs, files in os.walk(media_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    rel_path = os.path.relpath(os.path.join(root, file), media_path)
                    file_size = os.path.getsize(os.path.join(root, file))
                    
                    # Convert size to human readable
                    for unit in ['B', 'KB', 'MB', 'GB']:
                        if file_size < 1024.0:
                            size_str = f"{file_size:.1f}{unit}"
                            break
                        file_size /= 1024.0
                    else:
                        size_str = f"{file_size:.1f}TB"
                    
                    self.stdout.write(f'  {rel_path} ({size_str})')
                    video_count += 1
        
        self.stdout.write(f'\nTotal video files: {video_count}')

    def create_video_clips_from_files(self, media_path, dry_run):
        """Create VideoClip records for found video files"""
        created_count = 0
        
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        
        for root, dirs, files in os.walk(media_path):
            for file in files:
                if any(file.lower().endswith(ext) for ext in video_extensions):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, media_path)
                    
                    # Parse file path to determine video type and metadata
                    video_info = self.parse_video_path(rel_path)
                    
                    if video_info:
                        if not dry_run:
                            try:
                                video_clip, created = VideoClip.objects.get_or_create(
                                    exercise=video_info.get('exercise'),
                                    type=video_info['type'],
                                    archetype=video_info.get('archetype'),
                                    model_name=video_info.get('model_name'),
                                    defaults={
                                        'url': f'/media/{rel_path}',
                                        'duration_seconds': video_info.get('duration', 45),
                                        'is_active': True,
                                    }
                                )
                                
                                if created:
                                    created_count += 1
                                    self.stdout.write(f'  ✓ Created: {rel_path}')
                                else:
                                    self.stdout.write(f'  → Already exists: {rel_path}')
                                    
                            except Exception as e:
                                self.stdout.write(
                                    self.style.WARNING(f'Error creating VideoClip for {rel_path}: {e}')
                                )
                        else:
                            self.stdout.write(f'  → Would create: {rel_path}')
                            created_count += 1
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Could not parse video path: {rel_path}')
                        )
        
        return created_count

    def parse_video_path(self, rel_path):
        """Parse video file path to extract metadata"""
        path_parts = rel_path.split('/')
        filename = path_parts[-1]
        
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Default values
        video_info = {
            'type': 'instruction',
            'archetype': None,
            'model_name': None,
            'exercise': None,
            'duration': 45
        }
        
        # Exercise videos: videos/exercises/...
        if 'exercises' in path_parts:
            # Try to find exercise by looking for exercise slug in path or filename
            for exercise in Exercise.objects.all():
                if exercise.slug in name_without_ext or exercise.id in name_without_ext:
                    video_info['exercise'] = exercise
                    break
            
            # Determine video type from filename
            if 'technique' in name_without_ext:
                video_info['type'] = 'technique'
                video_info['model_name'] = 'mod1'
            elif 'mistake' in name_without_ext:
                video_info['type'] = 'mistake'
                video_info['model_name'] = 'mod1'
            elif 'instruction' in name_without_ext:
                video_info['type'] = 'instruction'
                video_info['model_name'] = 'mod1'
            elif 'reminder' in name_without_ext:
                video_info['type'] = 'reminder'
            
            # Determine archetype
            for archetype in ['bro', 'sergeant', 'intellectual']:
                if archetype in name_without_ext:
                    video_info['archetype'] = archetype
                    break
        
        # Trainer videos: videos/trainers/...
        elif 'trainers' in path_parts:
            # Determine archetype from path or filename
            for archetype in ['bro', 'sergeant', 'intellectual']:
                if archetype in rel_path:
                    video_info['archetype'] = archetype
                    break
            
            # Determine video type
            if 'intro' in name_without_ext:
                video_info['type'] = 'instruction'
                video_info['duration'] = 60
            elif 'weekly' in name_without_ext:
                video_info['type'] = 'weekly'
                video_info['duration'] = 90
            elif 'final' in name_without_ext:
                video_info['type'] = 'final'
                video_info['duration'] = 30
        
        # Motivation videos: videos/motivation/...
        elif 'motivation' in path_parts:
            video_info['type'] = 'motivation'
            video_info['duration'] = 30
            
            # Determine archetype
            for archetype in ['bro', 'sergeant', 'intellectual']:
                if archetype in name_without_ext:
                    video_info['archetype'] = archetype
                    break
        
        return video_info
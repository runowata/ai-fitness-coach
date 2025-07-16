"""
Management command to populate VideoClip records from uploaded video files
"""
import os
import re
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.workouts.models import VideoClip, Exercise


class Command(BaseCommand):
    help = 'Populate VideoClip records from uploaded video files'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating records',
        )
        parser.add_argument(
            '--video-path',
            type=str,
            default='media/videos',
            help='Path to video directory (default: media/videos)',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        video_path = Path(options['video_path'])
        
        if not video_path.exists():
            self.stdout.write(
                self.style.ERROR(f'Video directory does not exist: {video_path}')
            )
            return
        
        self.stdout.write(f'Looking for videos in: {video_path.absolute()}')
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            # Process exercise videos
            exercises_dir = video_path / 'exercises'
            if exercises_dir.exists():
                created, updated = self.process_exercise_videos(
                    exercises_dir, dry_run
                )
                created_count += created
                updated_count += updated
            
            # Process trainer videos
            trainers_dir = video_path / 'trainers'
            if trainers_dir.exists():
                created, updated = self.process_trainer_videos(
                    trainers_dir, dry_run
                )
                created_count += created
                updated_count += updated
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would create {created_count} VideoClips '
                    f'and update {updated_count} VideoClips'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Created {created_count} VideoClips and '
                    f'updated {updated_count} VideoClips'
                )
            )
            
            # Show final statistics
            total_clips = VideoClip.objects.count()
            self.stdout.write(f'Total VideoClips in database: {total_clips}')
    
    def process_exercise_videos(self, exercises_dir, dry_run):
        """Process videos in exercises directory"""
        created_count = 0
        updated_count = 0
        
        for exercise_dir in exercises_dir.iterdir():
            if not exercise_dir.is_dir():
                continue
                
            exercise_slug = exercise_dir.name  # EX001, EX002, etc.
            
            # Get or create exercise
            try:
                exercise = Exercise.objects.get(slug=exercise_slug)
                self.stdout.write(f'Found exercise: {exercise_slug}')
            except Exercise.DoesNotExist:
                if not dry_run:
                    exercise = Exercise.objects.create(
                        id=exercise_slug,  # Use slug as ID since it's UUID field
                        slug=exercise_slug,
                        name=f'Exercise {exercise_slug}',
                        description=f'Description for exercise {exercise_slug}',
                        muscle_groups='general',  # Text field, not list
                        difficulty='intermediate',
                        equipment=''  # Updated field name
                    )
                    self.stdout.write(f'Created exercise: {exercise_slug}')
                else:
                    self.stdout.write(f'Would create exercise: {exercise_slug}')
                    exercise = None
            
            # Process video files in this exercise directory
            for video_file in exercise_dir.glob('*.mp4'):
                video_info = self.parse_exercise_video_filename(
                    video_file.name, exercise_slug
                )
                
                if not video_info:
                    self.stdout.write(
                        self.style.WARNING(f'Skipping unknown video: {video_file.name}')
                    )
                    continue
                
                # Create video URL (relative to media root)
                video_url = f'/media/videos/exercises/{exercise_slug}/{video_file.name}'
                
                if not dry_run and exercise:
                    video_clip, created = VideoClip.objects.update_or_create(
                        exercise=exercise,
                        type=video_info['type'],
                        archetype=video_info.get('archetype'),
                        model_name=video_info.get('model_name'),
                        defaults={
                            'url': video_url,
                            'duration_seconds': 30,  # Default duration
                            'is_active': True,
                        }
                    )
                    
                    if created:
                        created_count += 1
                        self.stdout.write(f'  ✓ Created: {video_file.name}')
                    else:
                        updated_count += 1
                        self.stdout.write(f'  ↻ Updated: {video_file.name}')
                else:
                    self.stdout.write(f'  → Would process: {video_file.name}')
        
        return created_count, updated_count
    
    def process_trainer_videos(self, trainers_dir, dry_run):
        """Process videos in trainers directory"""
        created_count = 0
        updated_count = 0
        
        # Mapping trainer video types to VideoClip types
        type_mapping = {
            'intro': 'instruction',
            'support': 'reminder', 
            'outro': 'weekly'
        }
        
        for archetype_dir in trainers_dir.iterdir():
            if not archetype_dir.is_dir():
                continue
                
            archetype = archetype_dir.name  # bro, sergeant, intellectual
            
            for type_dir in archetype_dir.iterdir():
                if not type_dir.is_dir():
                    continue
                    
                trainer_type = type_dir.name  # intro, support, outro
                video_type = type_mapping.get(trainer_type, trainer_type)
                
                for video_file in type_dir.glob('*.mp4'):
                    video_url = f'/media/videos/trainers/{archetype}/{trainer_type}/{video_file.name}'
                    
                    if not dry_run:
                        video_clip, created = VideoClip.objects.update_or_create(
                            exercise=None,  # Trainer videos not linked to specific exercise
                            type=video_type,
                            archetype=archetype,
                            url=video_url,
                            defaults={
                                'duration_seconds': 30,
                                'is_active': True,
                            }
                        )
                        
                        if created:
                            created_count += 1
                            self.stdout.write(f'  ✓ Created trainer: {video_file.name}')
                        else:
                            updated_count += 1
                            self.stdout.write(f'  ↻ Updated trainer: {video_file.name}')
                    else:
                        self.stdout.write(f'  → Would process trainer: {video_file.name}')
        
        return created_count, updated_count
    
    def parse_exercise_video_filename(self, filename, exercise_slug):
        """Parse exercise video filename to extract type, archetype, model"""
        
        # Remove file extension
        name = filename.replace('.mp4', '')
        
        # Technique videos: technique_mod1.mp4
        if 'technique' in name:
            return {
                'type': 'technique',
                'archetype': None,
                'model_name': 'mod1'
            }
        
        # Mistake videos: mistake_mod1.mp4
        elif 'mistake' in name:
            return {
                'type': 'mistake', 
                'archetype': None,
                'model_name': 'mod1'
            }
        
        # Instruction videos: instruction_{archetype}_mod1.mp4
        elif 'instruction' in name:
            archetype = None
            for arch in ['bro', 'sergeant', 'intellectual']:
                if arch in name:
                    archetype = arch
                    break
            
            return {
                'type': 'instruction',
                'archetype': archetype or 'bro',
                'model_name': 'mod1'
            }
        
        # Reminder videos: reminder_{archetype}_1.mp4
        elif 'reminder' in name:
            archetype = None
            for arch in ['bro', 'sergeant', 'intellectual']:
                if arch in name:
                    archetype = arch
                    break
            
            return {
                'type': 'reminder',
                'archetype': archetype or 'bro',
                'model_name': None
            }
        
        return None